# 🚀 Quick Deployment Guide

**Last Updated:** May 25, 2026 | **Status:** Ready for Deployment

---

## 📌 What's Been Done

✅ **Frontend**
- Moved system status to admin-only dashboard
- Backend connection status only visible to admins
- Clean user dashboard (no system info)
- Admin panel with user management

✅ **Backend**  
- Admin endpoints implemented (`/auth/admin/users`)
- SMTP email verification ready
- JWT authentication with admin roles
- User management endpoints (toggle admin, toggle active)

✅ **Setup Scripts**
- `setup_admin.py` - Create default admin account
- `deploy-complete.ps1` - Automated deployment
- `verify-deployment.ps1` - Test verification

✅ **Configuration**
- `.env.development` - Development configuration template
- `env.example` - Updated with SMTP instructions
- `DEPLOYMENT_ADMIN_SETUP.md` - Detailed guide

---

## 🎯 Quick Start (5 Steps)

### Step 1: Configure SMTP

Edit `.env` file:

```bash
cp env.example .env
nano .env  # or use your editor
```

**Gmail Setup** (easiest):
1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification
3. Go to https://myaccount.google.com/apppasswords
4. Select Mail → Windows Computer
5. Copy the 16-char password
6. Paste into `.env` as `SMTP_PASSWORD`

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx
SMTP_FROM_EMAIL=noreply@yourdomain.com
```

### Step 2: Create Admin Account

```bash
python setup_admin.py
# Follow prompts to create admin user
```

Example output:
```
✅ Admin Account Setup Complete!
📧 Email:    admin@example.com
👤 Name:     Admin User
🔐 Role:     Administrator
✓ Status:    Active & Verified
```

### Step 3: Deploy Backend to Cloud Run

```bash
# Option A: Use automated script
./deploy-complete.ps1

# Option B: Manual deployment
cd scripts/gcp
./deploy-backend.ps1 -ProjectId "project-987f80c5-14e3-450d-9b0" -Region "asia-south1"
```

Backend URL: `https://presentation-api-558900038680.asia-south1.run.app`

### Step 4: Deploy Frontend to Vercel

```bash
# Using Firebase Hosting
firebase deploy --only hosting --project project-987f80c5-14e3-450d-9b0

# OR using Vercel CLI
vercel deploy --prod
```

Frontend URL: `https://project-987f80c5-14e3-450d-9b0.web.app`

### Step 5: Verify Deployment

```bash
# Run verification script
./verify-deployment.ps1 -AdminEmail "admin@example.com" -AdminPassword "your-password"

# Or manually test:
curl https://presentation-api-558900038680.asia-south1.run.app/health
# Should return: {"status":"healthy"}
```

---

## 🔐 Admin Dashboard Features

Once signed in as admin, you'll see:

### System Status (Admin Only)
```
✓ Backend Connection: Connected
✓ GET /health: OK
✓ GET /: OK
```

### User Management (Admin Only)
- View all registered users
- Toggle admin access (make admin / revoke admin)
- Toggle user status (enable / disable)
- View statistics (total, verified, admins)

### Not Visible to Regular Users
- System status indicators
- Backend connection status
- Admin panel
- User management

---

## 📋 Environment Variables

**Required:**
```env
BACKEND_URL=https://presentation-api-558900038680.asia-south1.run.app
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx
SMTP_FROM_EMAIL=noreply@yourdomain.com
ADMIN_EMAIL=admin@example.com
```

**Optional:**
```env
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
ANTHROPIC_API_KEY=...
ELEVENLABS_API_KEY=...
```

---

## ✅ Deployment Checklist

- [ ] SMTP configured in `.env`
- [ ] Admin account created via `setup_admin.py`
- [ ] Backend deployed to Cloud Run
- [ ] Frontend deployed to Firebase Hosting
- [ ] Verification script passes all tests
- [ ] Can sign in with admin account
- [ ] Admin panel visible after sign-in
- [ ] System status shows "Connected"
- [ ] User management works

---

## 🧪 Testing the Admin Panel

1. **Sign In:**
   - Go to frontend URL
   - Click "Sign In / Sign Up"
   - Enter admin email and password
   - Or use Google OAuth

2. **See Admin Dashboard:**
   - Admin panel appears at bottom of page
   - Shows system status and user management

3. **Test System Status:**
   - Click "↻ Refresh system status"
   - Should show Backend Connection: Connected (green dot)
   - GET /health and GET / should show OK

4. **Test User Management:**
   - Click "Refresh users"
   - Should list your admin account
   - Statistics show: Total: 1, Verified: 1, Admins: 1
   - Can click "Make admin" or "Disable" (though you can't disable yourself)

---

## 🐛 Troubleshooting

### SMTP Not Working
```bash
# Check .env has SMTP configured
cat .env | grep SMTP

# Test locally (Python)
python -c "
import smtplib
from dotenv import load_dotenv
import os
load_dotenv()
try:
    server = smtplib.SMTP(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT')))
    server.starttls()
    server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
    print('✓ SMTP working')
except Exception as e:
    print(f'✗ SMTP error: {e}')
"
```

### Admin Panel Not Visible
1. Verify you're signed in: Check username in header
2. Verify account is admin:
   ```sql
   SELECT email, is_admin FROM users WHERE email='admin@example.com';
   ```
3. Clear browser cache and refresh
4. Re-run setup script if needed

### Backend Not Connecting
1. Verify backend URL in frontend config
2. Check CORS in backend is configured correctly
3. Verify backend is running: `curl BACKEND_URL/health`

---

## 📚 Related Documentation

- [Full Deployment Guide](DEPLOYMENT_ADMIN_SETUP.md)
- [System Architecture](AGENTS.md)
- [API Reference](docs/API.md)
- [Troubleshooting](DEPLOYMENT_ADMIN_SETUP.md#-troubleshooting)

---

## 🎉 You're Ready!

Everything is set up for deployment. Follow the 5 steps above and you'll be live!

**Questions?** Check [DEPLOYMENT_ADMIN_SETUP.md](DEPLOYMENT_ADMIN_SETUP.md) for detailed instructions.

**Need help?** Review error messages carefully - most issues are config-related (SMTP, BACKEND_URL, admin account).
