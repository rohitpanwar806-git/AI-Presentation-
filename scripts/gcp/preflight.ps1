param(
  [Parameter(Mandatory=$true)][string]$ProjectId
)

$ErrorActionPreference = "Stop"

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

Write-Host "Checking active account..."
$account = (Invoke-Gcloud config get-value account).Trim()
if ([string]::IsNullOrWhiteSpace($account) -or $account -eq "(unset)") {
  throw "No active gcloud account. Run: gcloud auth login"
}
Write-Host "Active account: $account"

Write-Host "Checking project access..."
Invoke-Gcloud config set project $ProjectId | Out-Null

Write-Host "Checking billing status..."
$billingJson = Invoke-Gcloud billing projects describe $ProjectId --format=json | ConvertFrom-Json
if (-not $billingJson.billingEnabled) {
  throw "Billing is not enabled on project $ProjectId"
}

$billingAccountId = ($billingJson.billingAccountName -split "/")[-1]
$billingAccount = Invoke-Gcloud billing accounts describe $billingAccountId --format=json | ConvertFrom-Json
if (-not $billingAccount.open) {
  throw "Billing account $billingAccountId is closed. Reopen it or link another open billing account."
}

Write-Host "Checking required APIs..."
$required = @(
  "run.googleapis.com",
  "cloudbuild.googleapis.com",
  "artifactregistry.googleapis.com",
  "sqladmin.googleapis.com",
  "secretmanager.googleapis.com"
)

$enabled = Invoke-Gcloud services list --enabled --format="value(config.name)"
$missing = @()
foreach ($svc in $required) {
  if ($enabled -notcontains $svc) {
    $missing += $svc
  }
}

if ($missing.Count -gt 0) {
  Write-Host "Missing APIs: $($missing -join ', ')"
  Write-Host "Run bootstrap script to enable them."
} else {
  Write-Host "All required APIs are enabled."
}

Write-Host "Preflight passed. You can run bootstrap/deploy scripts."
