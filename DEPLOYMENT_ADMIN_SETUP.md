# Deployment & Admin Setup Guide

**Last Updated:** May 25, 2026

## 📋 Quick Deployment Checklist

### Phase 1: Backend Setup (Cloud Run)

```bash
# 1. Create .env from template
cp env.example .env

# 2. Edit .env with your credentials (SMTP, DATABASE_URL, etc.)
nano .env  # or your editor

# 3. Create admin account
python setup_admin.py
# Enter admin email and password when prompted

# 4. Deploy to Cloud Run
cd scripts/gcp
./deploy-backend.ps1 -ProjectId "project-987f80c5-14e3-450d-9b0" -Region "asia-south1"
```

### Phase 2: Frontend Deployment (Vercel)

```bash
# 1. Configure backend URL
export BACKEND_URL="https://presentation-api-558900038680.asia-south1.run.app"

# 2. Deploy to Vercel
firebase deploy --only hosting --project project-987f80c5-14e3-450d-9b0

# OR use Vercel CLI:
vercel deploy --prod
```

---

## 🔐 SMTP Configuration (Email Verification)

### Gmail Setup (Recommended for Development)

1. **Enable 2-Factor Authentication**
   - Visit: https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Create App Password**
   - Go to: https://myaccount.google.com/apppasswords
   - Select: Mail → Windows Computer
   - Copy the 16-character password

3. **Update .env**
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx  # 16-char app password
   SMTP_FROM_EMAIL=noreply@yourdomain.com
   SMTP_USE_TLS=true
   ```

### Testing SMTP

```bash
# Test email sending (after starting backend)
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Test",
    "last_name": "User",
    "email": "test@example.com",
    "password": "TestPass123",
    "gender": "male"
  }'
# Check your email inbox for verification code
```

---

## 👤 Admin Account Setup

### Creating the Default Admin

```bash
# Run the setup script
python setup_admin.py

# You'll be prompted for:
# - Admin email address
# - Admin password (min 8 characters)
# - Confirmation

# Output example:
# ✅ Admin Account Setup Complete!
# 📧 Email: admin@yourdomain.com
# 🔐 Role: Administrator
# ✓ Status: Active & Verified
```

### Admin Features

Once logged in as admin, you can:

- **View System Status**: Backend connection, health checks, request logs
- **Manage Users**: 
  - View all registered users
  - Verify email status
  - Grant/revoke admin access
  - Enable/disable accounts
- **View Statistics**: Total users, verified users, admin count

### Admin Dashboard Access

The admin panel is visible **ONLY** to admin users:

1. Sign in with admin account
2. Scroll to bottom of the page
3. Admin Panel section shows:
   - System Status (backend connection, API endpoints)
   - User Management (user list, actions)
   - Statistics (total, verified, admins)

---

## 🚀 Cloud Run Deployment

### Environment Variables for Cloud Run

```env
# Database
DATABASE_URL=postgresql+asyncpg://app_user:PASSWORD@/db_name?host=/cloudsql/PROJECT:REGION:INSTANCE
DB_SOCKET=/cloudsql/PROJECT:REGION:INSTANCE

# SMTP (from Gmail setup above)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_USE_TLS=true

# Admin
ADMIN_EMAIL=admin@yourdomain.com

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=https://project-987f80c5-14e3-450d-9b0.web.app,https://yourdomain.com

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://presentation-api-558900038680.asia-south1.run.app/auth/callback/google
```

### Deployment Script (PowerShell)

```powershell
# scripts/gcp/deploy-backend.ps1
./deploy-backend.ps1 -ProjectId "project-987f80c5-14e3-450d-9b0" -Region "asia-south1"
```

The script will:
1. Check GCP configuration
2. Build Docker image
3. Push to Cloud Run
4. Set environment variables from Secret Manager
5. Deploy service
6. Output backend URL

---

## 🌐 Vercel Deployment

### Environment Variables for Vercel

```env
# Frontend (frontend/web/config.js)
BACKEND_URL=https://presentation-api-558900038680.asia-south1.run.app
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
```

### Deployment Steps

```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Login to Vercel
vercel login

# 3. Deploy
vercel deploy --prod

# OR use Firebase Hosting:
firebase deploy --only hosting --project project-987f80c5-14e3-450d-9b0
```

---

## ✅ Verification Checklist

### After Backend Deployment

- [ ] Health check passes: `https://backend-url/health`
- [ ] API info available: `https://backend-url/` 
- [ ] SMTP configured (test email sending)
- [ ] Database connected
- [ ] Admin account created: `python setup_admin.py`

### After Frontend Deployment

- [ ] Frontend loads without errors
- [ ] Sign in page appears
- [ ] Backend status shown (for admins only)
- [ ] Email verification works
- [ ] Admin can sign in

### Admin Dashboard Testing

1. Sign in with admin account
2. Verify admin panel is visible (bottom of page)
3. Check System Status:
   - Backend Connection shows "Connected" (green dot)
   - GET /health shows "OK"
   - GET / shows "OK"
4. Check User Management:
   - Your account listed as Admin
   - Can view user statistics
5. Test admin actions:
   - Create test user account (sign up)
   - Admin can toggle user's admin status
   - Admin can disable/enable user accounts

---

## 🔍 Troubleshooting

### "SMTP configuration is not valid"

**Issue**: Email verification not sending

**Solution**:
1. Verify SMTP credentials in .env
2. Check if Gmail 2FA is enabled
3. Verify app password is 16 characters
4. Check SMTP_FROM_EMAIL is set correctly

```bash
# Test locally
python -c "
from backend.api.auth import _send_verification_email
result = _send_verification_email('test@example.com', '123456')
print('SMTP OK' if result else 'SMTP Failed')
"
```

### "Database connection refused"

**Issue**: Can't connect to Cloud SQL

**Solution**:
1. Verify DATABASE_URL format:
   ```env
   # Should include /cloudsql/ for Cloud Run
   DATABASE_URL=postgresql+asyncpg://user:pass@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE
   ```
2. Check Cloud SQL Proxy is running
3. Verify Cloud Run service account has Cloud SQL Client role

### "Admin panel not visible"

**Issue**: Admin features not showing even after sign-in

**Solution**:
1. Verify account is_admin flag:
   ```bash
   # Run this in database:
   SELECT email, is_admin FROM users WHERE email='admin@example.com';
   ```
2. Re-run setup script to update account
3. Clear browser cache and re-login

---

## 📚 Related Documentation

- [API Reference](docs/API.md)
- [GCP Deployment Guide](docs/GCP_DEPLOYMENT.md)
- [Firebase Setup](FIREBASE_DEPLOYMENT_GUIDE.md)
- [System Architecture](AGENTS.md)

---

**Need help?** Check the AGENTS.md file for detailed architecture information or review error logs:

```bash
# View backend logs (Cloud Run)
gcloud run logs read presentation-api --limit 50

# View frontend build logs (Vercel)
vercel logs
```
