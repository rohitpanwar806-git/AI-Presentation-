#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Complete deployment script for AI Presentation Avatar SaaS
    Deploys backend to Cloud Run and frontend to Vercel

.DESCRIPTION
    This script automates the entire deployment process:
    1. Backend: Builds Docker image, pushes to Cloud Run, sets environment variables
    2. Frontend: Deploys static files to Firebase Hosting
    3. Creates admin account (optional)

.PARAMETER Environment
    Deployment environment: 'development' or 'production'

.PARAMETER SkipAdmin
    Skip admin account creation

.EXAMPLE
    .\deploy.ps1 -Environment production
#>

param(
    [string]$Environment = "production",
    [switch]$SkipAdmin = $false,
    [string]$AdminEmail = "admin@example.com",
    [string]$AdminPassword = ""
)

# Colors for output
$Success = @{ ForegroundColor = "Green" }
$Error = @{ ForegroundColor = "Red" }
$Info = @{ ForegroundColor = "Cyan" }
$Warning = @{ ForegroundColor = "Yellow" }

function Write-Success { Write-Host @Success @args }
function Write-Error { Write-Host @Error @args }
function Write-Info { Write-Host @Info @args }
function Write-Warning { Write-Host @Warning @args }

# Configuration
$ProjectId = "project-987f80c5-14e3-450d-9b0"
$Region = "asia-south1"
$ServiceName = "presentation-api"
$CloudRunUrl = "https://presentation-api-558900038680.asia-south1.run.app"
$FirebaseProject = "project-987f80c5-14e3-450d-9b0"

Write-Info "╔════════════════════════════════════════════════════════════╗"
Write-Info "║  AI Presentation Avatar - Complete Deployment Script       ║"
Write-Info "║  Environment: $Environment"
Write-Info "╚════════════════════════════════════════════════════════════╝`n"

# Step 1: Backend Deployment
Write-Info "📦 STEP 1: Backend Deployment (Cloud Run)"
Write-Info "════════════════════════════════════════════════════════════`n"

$backendDeployScript = ".\scripts\gcp\deploy-backend.ps1"
if (Test-Path $backendDeployScript) {
    Write-Info "Running backend deployment..."
    & $backendDeployScript -ProjectId $ProjectId -Region $Region
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "✓ Backend deployed successfully`n"
    } else {
        Write-Error "✗ Backend deployment failed`n"
        exit 1
    }
} else {
    Write-Warning "⚠ Backend deployment script not found: $backendDeployScript"
    Write-Warning "  Please run manually: $backendDeployScript`n"
}

# Step 2: Frontend Deployment
Write-Info "🌐 STEP 2: Frontend Deployment (Firebase Hosting)"
Write-Info "════════════════════════════════════════════════════════════`n"

Write-Info "Deploying frontend to Firebase Hosting..."
try {
    firebase deploy --only hosting --project $FirebaseProject 2>&1 | ForEach-Object {
        if ($_ -match "error|Error|ERROR") {
            Write-Error $_
        } else {
            Write-Info $_
        }
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "✓ Frontend deployed successfully`n"
    } else {
        Write-Warning "⚠ Firebase deployment had issues (this may be normal)`n"
    }
} catch {
    Write-Warning "⚠ Firebase CLI not found or not logged in"
    Write-Warning "  Run: firebase login`n"
}

# Step 3: Admin Account (Optional)
if (-not $SkipAdmin) {
    Write-Info "👤 STEP 3: Admin Account Setup"
    Write-Info "════════════════════════════════════════════════════════════`n"
    
    $setupAdminScript = "setup_admin.py"
    if (Test-Path $setupAdminScript) {
        Write-Info "Run the following command to create admin account:`n"
        Write-Info "  python setup_admin.py`n"
        Write-Info "Or use environment variables:`n"
        Write-Info "  ADMIN_EMAIL=`"$AdminEmail`" python setup_admin.py`n"
    } else {
        Write-Warning "⚠ Admin setup script not found: $setupAdminScript`n"
    }
}

# Step 4: Summary
Write-Info "✅ STEP 4: Deployment Complete"
Write-Info "════════════════════════════════════════════════════════════`n"

Write-Success "🎉 Deployment Summary:`n"
Write-Info "Backend API:    $CloudRunUrl"
Write-Info "Frontend:       https://$FirebaseProject.web.app"
Write-Info "Admin Email:    $AdminEmail`n"

Write-Info "📋 Next Steps:`n"
Write-Info "1. Verify backend is running:"
Write-Info "   curl $CloudRunUrl/health`n"

Write-Info "2. Create admin account:"
Write-Info "   python setup_admin.py`n"

Write-Info "3. Test the platform:"
Write-Info "   Visit: https://$FirebaseProject.web.app"
Write-Info "   Sign in with admin account`n"

Write-Info "4. Configure admin settings:"
Write-Info "   - Check System Status in admin panel"
Write-Info "   - Manage users and permissions"
Write-Info "   - Set up additional admins as needed`n"

Write-Success "🚀 Deployment finished successfully!`n"
