param(
  [Parameter(Mandatory=$true)][string]$ProjectId,
  [string]$Region = "asia-south1",
  [string]$SqlInstance = "presentation-db",
  [string]$DbName = "presentation_saas",
  [string]$DbUser = "app_user",
  [string]$ArtifactRepo = "presentation-artifacts",
  [string]$ServiceName = "presentation-api"
)

$ErrorActionPreference = "Stop"

# Prevent local Python env vars from breaking gcloud's embedded runtime.
Remove-Item Env:PYTHONHOME -ErrorAction SilentlyContinue
Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
Remove-Item Env:CLOUDSDK_PYTHON -ErrorAction SilentlyContinue

$gcloudCmd = Get-Command gcloud.cmd -ErrorAction SilentlyContinue
if (-not $gcloudCmd) {
  throw "gcloud CLI not found in PATH. Install Google Cloud SDK first."
}

$gcloudExe = $gcloudCmd.Source

function Invoke-Gcloud {
  param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
  & $gcloudExe @Args
  if ($LASTEXITCODE -ne 0) {
    throw "gcloud failed: gcloud $($Args -join ' ')"
  }
}

$gcloudRoot = Resolve-Path (Join-Path (Split-Path $gcloudExe -Parent) "..")
  $bundledPython = Join-Path $gcloudRoot "platform\bundledpython\python.exe"
  if (Test-Path $bundledPython) {
    $env:CLOUDSDK_PYTHON = $bundledPython
  }

Write-Host "Setting gcloud project: $ProjectId"
Invoke-Gcloud config set project $ProjectId | Out-Null

Write-Host "Checking billing account state..."
$billingJson = Invoke-Gcloud billing projects describe $ProjectId --format=json | ConvertFrom-Json
if (-not $billingJson.billingEnabled) {
  throw "Billing is not enabled on project $ProjectId"
}
$billingAccountId = ($billingJson.billingAccountName -split "/")[-1]
$billingAccount = Invoke-Gcloud billing accounts describe $billingAccountId --format=json | ConvertFrom-Json
if (-not $billingAccount.open) {
  throw "Billing account $billingAccountId is closed. Reopen it or link another open billing account."
}

Write-Host "Enabling required APIs..."
Invoke-Gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com firebase.googleapis.com --project $ProjectId | Out-Null

Write-Host "Creating Artifact Registry repo if missing..."
$repoExists = Invoke-Gcloud artifacts repositories list --location=$Region --project=$ProjectId --format="value(name)" | Select-String $ArtifactRepo
if (-not $repoExists) {
  Invoke-Gcloud artifacts repositories create $ArtifactRepo --repository-format=docker --location=$Region --description="Docker images for AI Presentation SaaS" --project=$ProjectId | Out-Null
}

Write-Host "Creating Cloud SQL Postgres instance (db-f1-micro) if missing..."
$sqlExists = Invoke-Gcloud sql instances list --project=$ProjectId --format="value(name)" | Select-String $SqlInstance
if (-not $sqlExists) {
  Invoke-Gcloud sql instances create $SqlInstance `
    --database-version=POSTGRES_15 `
    --tier=db-f1-micro `
    --region=$Region `
    --storage-size=10GB `
    --storage-type=SSD `
    --backup-start-time=03:00 `
    --project=$ProjectId | Out-Null
}

Write-Host "Creating database if missing..."
$dbExists = Invoke-Gcloud sql databases list --instance=$SqlInstance --project=$ProjectId --format="value(name)" | Select-String $DbName
if (-not $dbExists) {
  Invoke-Gcloud sql databases create $DbName --instance=$SqlInstance --project=$ProjectId | Out-Null
}

Write-Host "Bootstrap complete."
Write-Host "Next: run scripts/gcp/create-secrets.ps1 and scripts/gcp/deploy-backend.ps1"
