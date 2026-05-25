param(
  [Parameter(Mandatory=$true)][string]$ProjectId
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

function Upsert-Secret {
  param([string]$Name, [string]$Value)

  if ([string]::IsNullOrWhiteSpace($Value)) {
    Write-Host "Skipping empty secret: $Name"
    return
  }

  $exists = Invoke-Gcloud secrets list --project=$ProjectId --format="value(name)" | Select-String "^$Name$"
  if (-not $exists) {
    Invoke-Gcloud secrets create $Name --replication-policy=automatic --project=$ProjectId | Out-Null
  }

  $tmp = New-TemporaryFile
  Set-Content -Path $tmp -Value $Value -NoNewline
  Invoke-Gcloud secrets versions add $Name --data-file=$tmp --project=$ProjectId | Out-Null
  Remove-Item $tmp -Force
  Write-Host "Updated secret: $Name"
}

function Read-SecretValue {
  param([string]$Prompt)
  $secure = Read-Host $Prompt -AsSecureString
  $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try {
    return [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
  }
  finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
  }
}

$secretKey = Read-SecretValue "Enter SECRET_KEY"
$supabaseUrl = Read-Host "Enter SUPABASE_URL"
$supabaseKey = Read-SecretValue "Enter SUPABASE_KEY"
$anthropicKey = Read-SecretValue "Enter ANTHROPIC_API_KEY"
$elevenKey = Read-SecretValue "Enter ELEVENLABS_API_KEY"
$pineconeKey = Read-SecretValue "Enter PINECONE_API_KEY"
$googleClientId = Read-Host "Enter GOOGLE_CLIENT_ID"
$googleClientSecret = Read-SecretValue "Enter GOOGLE_CLIENT_SECRET"
$dbPassword = Read-SecretValue "Enter DB_PASSWORD"
$smtpUsername = Read-Host "Enter SMTP_USERNAME"
$smtpPassword = Read-SecretValue "Enter SMTP_PASSWORD"

Upsert-Secret -Name "presentation-secret-key" -Value $secretKey
Upsert-Secret -Name "presentation-supabase-url" -Value $supabaseUrl
Upsert-Secret -Name "presentation-supabase-key" -Value $supabaseKey
Upsert-Secret -Name "presentation-anthropic-key" -Value $anthropicKey
Upsert-Secret -Name "presentation-elevenlabs-key" -Value $elevenKey
Upsert-Secret -Name "presentation-pinecone-key" -Value $pineconeKey
Upsert-Secret -Name "presentation-google-client-id" -Value $googleClientId
Upsert-Secret -Name "presentation-google-client-secret" -Value $googleClientSecret
Upsert-Secret -Name "presentation-db-password" -Value $dbPassword
Upsert-Secret -Name "presentation-smtp-username" -Value $smtpUsername
Upsert-Secret -Name "presentation-smtp-password" -Value $smtpPassword

Write-Host "All available secrets upserted successfully."
