param(
  [Parameter(Mandatory=$true)][string]$ProjectId,
  [string]$Region = "asia-south1",
  [string]$ServiceName = "presentation-api",
  [string]$SqlInstance = "presentation-db",
  [string]$DbName = "presentation_saas",
  [string]$DbUser = "app_user",
  [string]$ArtifactRepo = "presentation-artifacts",
  [string]$AdminEmail = "rohitpanwar806@gmail.com",
  [string]$AuthDatabaseUrl = "",
  [string]$SmtpHost = "",
  [string]$SmtpPort = "587",
  [string]$SmtpFromEmail = "",
  [string]$SmtpUseTls = "true"
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

$Image = "$Region-docker.pkg.dev/$ProjectId/$ArtifactRepo/$ServiceName`:latest"
$SqlConnection = "${ProjectId}:${Region}:${SqlInstance}"

$secretMap = @{
  "presentation-secret-key" = "SECRET_KEY"
  "presentation-supabase-url" = "SUPABASE_URL"
  "presentation-supabase-key" = "SUPABASE_KEY"
  "presentation-anthropic-key" = "ANTHROPIC_API_KEY"
  "presentation-elevenlabs-key" = "ELEVENLABS_API_KEY"
  "presentation-pinecone-key" = "PINECONE_API_KEY"
  "presentation-google-client-id" = "GOOGLE_CLIENT_ID"
  "presentation-google-client-secret" = "GOOGLE_CLIENT_SECRET"
  "presentation-db-password" = "DB_PASSWORD"
  "presentation-smtp-username" = "SMTP_USERNAME"
  "presentation-smtp-password" = "SMTP_PASSWORD"
}

$existingSecrets = Invoke-Gcloud secrets list --project $ProjectId --format="value(name)"
$secretBindings = @()
foreach ($secretName in $secretMap.Keys) {
  if ($existingSecrets -contains $secretName) {
    $secretBindings += "$($secretMap[$secretName])=$secretName`:latest"
  }
}

if (-not ($secretBindings -contains "DB_PASSWORD=presentation-db-password:latest")) {
  throw "Required secret missing: presentation-db-password"
}

if (-not ($secretBindings -contains "SECRET_KEY=presentation-secret-key:latest")) {
  throw "Required secret missing: presentation-secret-key"
}

$secretBindingsArg = $secretBindings -join ","

Write-Host "Configuring project..."
Invoke-Gcloud config set project $ProjectId | Out-Null

Write-Host "Building backend image with Cloud Build..."
Invoke-Gcloud builds submit --tag $Image --project $ProjectId .

Write-Host "Deploying Cloud Run service (cost-optimized settings)..."
  $smtpEnvParts = @()
  if ($SmtpHost) {
    $smtpEnvParts += "SMTP_HOST=$SmtpHost"
  }
  if ($SmtpFromEmail) {
    $smtpEnvParts += "SMTP_FROM_EMAIL=$SmtpFromEmail"
  }
  if ($SmtpPort) {
    $smtpEnvParts += "SMTP_PORT=$SmtpPort"
  }
  if ($SmtpUseTls) {
    $smtpEnvParts += "SMTP_USE_TLS=$SmtpUseTls"
  }

  $envVarParts = @(
    "ENVIRONMENT=production",
    "ALGORITHM=HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES=30",
    "PINECONE_INDEX_NAME=presentations",
    "RATE_LIMIT_PER_MINUTE=60",
    "DB_USER=$DbUser",
    "DB_NAME=$DbName",
    "DB_SOCKET=/cloudsql/$SqlConnection",
    "ADMIN_EMAIL=$AdminEmail",
    "VERIFICATION_CODE_EXPIRE_MINUTES=10"
  )

  if ($AuthDatabaseUrl) {
    $envVarParts += "AUTH_DATABASE_URL=$AuthDatabaseUrl"
  }

  $envVarBase = $envVarParts -join ","
  if ($smtpEnvParts.Count -gt 0) {
    $envVarBase = "$envVarBase,$($smtpEnvParts -join ',')"
  }

Invoke-Gcloud run deploy $ServiceName `
  --image $Image `
  --region $Region `
  --platform managed `
  --allow-unauthenticated `
  --port 8080 `
  --cpu 1 `
  --memory 512Mi `
  --min-instances 0 `
  --max-instances 3 `
  --concurrency 80 `
  --timeout 120 `
  --set-env-vars $envVarBase `
  --set-secrets $secretBindingsArg `
  --add-cloudsql-instances $SqlConnection `
  --project $ProjectId

$serviceUrl = (Invoke-Gcloud run services describe $ServiceName --region $Region --project $ProjectId --format="value(status.url)").Trim()
Invoke-Gcloud run services update $ServiceName --region $Region --project $ProjectId --update-env-vars "GOOGLE_REDIRECT_URI=$serviceUrl/auth/callback/google" | Out-Null
Write-Host "Backend deployed at: $serviceUrl"
Write-Host "GOOGLE_REDIRECT_URI set to: $serviceUrl/auth/callback/google"
