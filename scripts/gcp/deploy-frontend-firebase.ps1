param(
  [Parameter(Mandatory=$true)][string]$ProjectId,
  [Parameter(Mandatory=$false)][string]$BackendUrl = "https://presentation-api-558900038680.asia-south1.run.app",
  [Parameter(Mandatory=$false)][switch]$SkipLogin = $false
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Deploying Cost-Optimized Frontend on Firebase Hosting"
Write-Host "   Project: $ProjectId"
Write-Host "   Region: asia-south1"
Write-Host "   Backend: $BackendUrl"
Write-Host ""

# Check Firebase CLI
if (-not (Get-Command firebase -ErrorAction SilentlyContinue)) {
  Write-Host "📦 Installing Firebase CLI..."
  npm install -g firebase-tools
  if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install Firebase CLI"
    exit 1
  }
}

# Ensure frontend/web directory exists
if (-not (Test-Path "frontend/web")) {
  Write-Host "📁 Creating frontend/web directory..."
  New-Item -ItemType Directory -Path "frontend/web" | Out-Null
}

# Create config file with backend URL injected
Write-Host "⚙️  Configuring frontend with backend URL..."
$configScript = @"
(function() {
  // Inject backend URL from deployment
  window.BACKEND_URL = '$BackendUrl';
  
  // Fallback logic if window.BACKEND_URL not set
  if (!window.BACKEND_URL || window.BACKEND_URL === 'null') {
    // Try to auto-detect for development
    if (window.location.hostname === 'localhost') {
      window.BACKEND_URL = 'http://localhost:8000';
    } else {
      window.BACKEND_URL = '$BackendUrl';
    }
  }
  
  // Store in localStorage for persistence
  localStorage.setItem('backendUrl', window.BACKEND_URL);
  console.log('Backend URL configured:', window.BACKEND_URL);
})();
"@

# Create config.js to inject the backend URL
$configScript | Set-Content -Path "frontend/web/config.js"

# Verify frontend files exist (they should have been created earlier)
if (-not (Test-Path "frontend/web/index.html")) {
  Write-Host "❌ Error: frontend/web/index.html not found"
  Write-Host "   Make sure HTML, CSS, and JS files are in frontend/web/ directory"
  exit 1
}

if (-not (Test-Path "frontend/web/app.js")) {
  Write-Host "❌ Error: frontend/web/app.js not found"
  exit 1
}

# Update index.html to load config.js first
Write-Host "📝 Injecting config into HTML..."
$htmlContent = Get-Content "frontend/web/index.html" -Raw

# Add config.js reference if not present
if ($htmlContent -notmatch '<script src="config.js"') {
  # Insert config.js before app.js
  $htmlContent = $htmlContent -replace 
    '(<script src="app.js"></script>)',
    '<script src="config.js"></script>
  <script src="app.js"></script>'
  
  Set-Content -Path "frontend/web/index.html" -Value $htmlContent
}

# Configure firebase.json for cost-optimized hosting
Write-Host "🔧 Configuring Firebase settings..."
@"
{
  "hosting": {
    "public": "frontend/web",
    "ignore": ["firebase.json", ".firebaserc", "**/.*", "**/node_modules/**"],
    "cleanUrls": true,
    "trailingSlash": false,
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(js|css|gif|jpg|jpeg|png|svg|webp|woff|woff2)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "public, max-age=31536000"
          }
        ]
      },
      {
        "source": "**/*.html",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "public, max-age=3600, must-revalidate"
          }
        ]
      }
    ]
  }
}
"@ | Set-Content -Path "firebase.json"

# Configure .firebaserc
@"
{
  "projects": {
    "default": "$ProjectId"
  }
}
"@ | Set-Content -Path ".firebaserc"

# Login to Firebase if not skipped
if (-not $SkipLogin) {
  Write-Host "🔐 Logging into Firebase (opens browser)..."
  firebase login
}

# Set project
Write-Host "📌 Setting Firebase project..."
firebase use $ProjectId

# Deploy
Write-Host "🚀 Deploying to Firebase Hosting..."
firebase deploy --only hosting

if ($LASTEXITCODE -eq 0) {
  Write-Host ""
  Write-Host "✅ Frontend deployed successfully!"
  Write-Host ""
  Write-Host "📱 Access your frontend at:"
  Write-Host "   https://$ProjectId.web.app"
  Write-Host ""
  Write-Host "📊 Configuration:"
  Write-Host "   Backend URL: $BackendUrl"
  Write-Host "   Project ID: $ProjectId"
  Write-Host "   Hosting: Firebase (Free tier: 1GB storage, 10GB/month bandwidth)"
  Write-Host ""
  Write-Host "🔍 Next Steps:"
  Write-Host "   1. Visit https://$ProjectId.web.app to verify deployment"
  Write-Host "   2. Check that backend status shows 'Connected'"
  Write-Host "   3. Monitor costs in GCP Console > Billing"
} else {
  Write-Host ""
  Write-Host "❌ Deployment failed. Check errors above."
  exit 1
}
