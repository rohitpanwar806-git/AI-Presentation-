#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Verify AI Presentation Avatar deployment and admin setup

.DESCRIPTION
    Comprehensive test suite to verify:
    - Backend API endpoints
    - Frontend connectivity
    - Admin account access
    - SMTP configuration
    - System status indicators
#>

param(
    [string]$BackendUrl = "http://localhost:8000",
    [string]$FrontendUrl = "http://localhost:8080",
    [string]$AdminEmail = "admin@example.com",
    [string]$AdminPassword = ""
)

# Colors
$Success = @{ ForegroundColor = "Green" }
$Error = @{ ForegroundColor = "Red" }
$Info = @{ ForegroundColor = "Cyan" }
$Warning = @{ ForegroundColor = "Yellow" }

function Write-Success { Write-Host @Success @args }
function Write-Error { Write-Host @Error @args }
function Write-Info { Write-Host @Info @args }
function Write-Warning { Write-Host @Warning @args }

# Test results
$tests = @()

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        [hashtable]$Headers = @{},
        [string]$Body = $null
    )
    
    try {
        $params = @{
            Method = $Method
            Uri = $Url
            Headers = $Headers
            TimeoutSec = 10
        }
        
        if ($Body) {
            $params["Body"] = $Body
        }
        
        $response = Invoke-WebRequest @params -ErrorAction Stop
        
        return @{
            Name = $Name
            Status = "✓ PASS"
            StatusCode = $response.StatusCode
            Message = "Success"
        }
    } catch {
        return @{
            Name = $Name
            Status = "✗ FAIL"
            StatusCode = $_.Exception.Response.StatusCode
            Message = $_.Exception.Message
        }
    }
}

Write-Info "╔════════════════════════════════════════════════════════════╗"
Write-Info "║  AI Presentation Avatar - Deployment Verification         ║"
Write-Info "╚════════════════════════════════════════════════════════════╝`n"

# ============================================================================
# STEP 1: Backend API Tests
# ============================================================================

Write-Info "🔧 STEP 1: Backend API Verification"
Write-Info "════════════════════════════════════════════════════════════"
Write-Info "Backend URL: $BackendUrl`n"

# Test health endpoint
Write-Info "Testing health endpoint..."
$test1 = Test-Endpoint -Name "GET /health" -Url "$BackendUrl/health"
$tests += $test1
if ($test1.Status -like "✓*") {
    Write-Success $test1.Status
} else {
    Write-Error "$($test1.Status) - $($test1.Message)"
}

# Test info endpoint
Write-Info "Testing info endpoint..."
$test2 = Test-Endpoint -Name "GET /" -Url "$BackendUrl/"
$tests += $test2
if ($test2.Status -like "✓*") {
    Write-Success $test2.Status
} else {
    Write-Error "$($test2.Status) - $($test2.Message)"
}

# Test admin users endpoint (no auth - should fail)
Write-Info "Testing admin endpoint (should require auth)..."
$test3 = Test-Endpoint -Name "GET /auth/admin/users (no auth)" -Url "$BackendUrl/auth/admin/users"
$tests += $test3
if ($test3.StatusCode -eq 401) {
    Write-Success "✓ PASS (correctly requires authentication)"
} else {
    Write-Warning "⚠ Unexpected response: $($test3.StatusCode)"
}

# ============================================================================
# STEP 2: Frontend Tests
# ============================================================================

Write-Info "`n🌐 STEP 2: Frontend Verification"
Write-Info "════════════════════════════════════════════════════════════"
Write-Info "Frontend URL: $FrontendUrl`n"

# Test frontend loads
Write-Info "Testing frontend availability..."
try {
    $response = Invoke-WebRequest -Uri $FrontendUrl -TimeoutSec 10 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Success "✓ PASS - Frontend responds with 200"
        $tests += @{
            Name = "Frontend loads"
            Status = "✓ PASS"
            StatusCode = 200
            Message = "Success"
        }
    }
} catch {
    Write-Warning "⚠ Frontend not accessible at $FrontendUrl"
    Write-Warning "  Make sure to run: npx http-server -p 8080 -c-1 (in frontend/web)"
}

# ============================================================================
# STEP 3: Admin Account Testing
# ============================================================================

Write-Info "`n👤 STEP 3: Admin Account Setup"
Write-Info "════════════════════════════════════════════════════════════`n"

if ([string]::IsNullOrEmpty($AdminPassword)) {
    Write-Warning "⚠ Admin password not provided"
    Write-Info "To test admin account, run:"
    Write-Info "  .\verify-deployment.ps1 -AdminPassword `"your-password`"`n"
} else {
    Write-Info "Testing admin account..."
    
    # Try to login
    try {
        $loginBody = @{
            email = $AdminEmail
            password = $AdminPassword
        } | ConvertTo-Json
        
        $loginTest = Test-Endpoint `
            -Name "Admin Login" `
            -Url "$BackendUrl/auth/login" `
            -Method "POST" `
            -Headers @{"Content-Type"="application/json"} `
            -Body $loginBody
        
        if ($loginTest.Status -like "✓*") {
            Write-Success $loginTest.Status
            Write-Info "✓ Admin account is accessible`n"
        } else {
            Write-Warning "$($loginTest.Status)"
            Write-Info "  Admin account may not exist yet"
            Write-Info "  Create it with: python setup_admin.py`n"
        }
    } catch {
        Write-Warning "Could not test admin login"
    }
}

# ============================================================================
# STEP 4: SMTP Configuration
# ============================================================================

Write-Info "📧 STEP 4: SMTP Configuration"
Write-Info "════════════════════════════════════════════════════════════`n"

Write-Info "Checking .env file for SMTP configuration..."

if (Test-Path ".env") {
    $envContent = Get-Content ".env" | Select-String "SMTP"
    if ($envContent) {
        Write-Success "✓ SMTP configuration found in .env"
        
        $smtpHost = (Get-Content ".env" | Select-String "SMTP_HOST" | ForEach-Object { $_ -split "=" | Select-Object -Last 1 }).Trim()
        $smtpUser = (Get-Content ".env" | Select-String "SMTP_USERNAME" | ForEach-Object { $_ -split "=" | Select-Object -Last 1 }).Trim()
        
        Write-Info "  SMTP Host: $smtpHost"
        Write-Info "  SMTP User: $smtpUser"
        Write-Info "  Status: Ready for email verification`n"
    } else {
        Write-Error "✗ SMTP not configured in .env"
        Write-Warning "  Configure SMTP for email verification"
        Write-Info "  See env.example for Gmail setup instructions`n"
    }
} else {
    Write-Error "✗ .env file not found"
    Write-Info "  Copy env.example to .env and configure SMTP`n"
}

# ============================================================================
# STEP 5: System Status Features
# ============================================================================

Write-Info "⚙️  STEP 5: Admin-Only Features"
Write-Info "════════════════════════════════════════════════════════════`n"

Write-Info "The following features are admin-only:`n"

Write-Info "✓ System Status Panel"
Write-Info "  - Backend connection status"
Write-Info "  - Health check results"
Write-Info "  - API endpoint status`n"

Write-Info "✓ User Management"
Write-Info "  - View all registered users"
Write-Info "  - Grant/revoke admin access"
Write-Info "  - Enable/disable accounts"
Write-Info "  - View user statistics`n"

Write-Info "✓ Admin Dashboard (visible only to admin users)"
Write-Info "  - Hidden from normal users"
Write-Info "  - Hidden from default page`n"

# ============================================================================
# Summary
# ============================================================================

Write-Info "`n✅ Verification Complete"
Write-Info "════════════════════════════════════════════════════════════`n"

$passCount = ($tests | Where-Object { $_.Status -like "✓*" }).Count
$totalCount = $tests.Count

Write-Info "Test Results: $passCount / $totalCount passed`n"

# Print all tests
Write-Info "Test Summary:"
$tests | ForEach-Object {
    if ($_.Status -like "✓*") {
        Write-Success "  $($_.Name): $($_.Status)"
    } else {
        Write-Error "  $($_.Name): $($_.Status)"
    }
}

Write-Info "`n📋 Next Steps:`n"
Write-Info "1. Backend deployment:"
Write-Info "   .\deploy-complete.ps1`n"

Write-Info "2. Create admin account:"
Write-Info "   python setup_admin.py`n"

Write-Info "3. Sign in to admin dashboard:"
Write-Info "   Email: $AdminEmail"
Write-Info "   Check System Status and User Management tabs`n"

Write-Info "4. Deploy to production:"
Write-Info "   Push to GitHub and deploy via CI/CD`n"

Write-Success "🎉 Verification finished!`n"
