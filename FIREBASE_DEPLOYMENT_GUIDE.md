# Firebase Hosting Deployment Guide

## Status

✅ **Frontend Created**: Static SPA with backend integration
✅ **Configuration Files Generated**: `firebase.json` and `.firebaserc`
✅ **Backend URL Wired**: `https://presentation-api-558900038680.asia-south1.run.app`
⏳ **Pending**: Firebase CLI Authentication

## Frontend Files Ready

```
frontend/web/
├── index.html          # Main SPA with cost-optimized design
├── app.js              # Backend connectivity tests & API client
└── config.js           # Backend URL injection & configuration
```

## Authentication Options

### Option 1: Firebase Login (Recommended)

```powershell
cd c:\Users\rohit\Downloads\AI-Presentation-
firebase login
# Paste authorization code when prompted
firebase deploy --only hosting --project project-987f80c5-14e3-450d-9b0
```

### Option 2: Service Account Authentication

1. **Create Service Account** (One-time setup):
```bash
gcloud iam service-accounts create firebase-deployer \
  --display-name="Firebase Deployer" \
  --project=project-987f80c5-14e3-450d-9b0
```

2. **Grant Permissions**:
```bash
gcloud projects add-iam-policy-binding project-987f80c5-14e3-450d-9b0 \
  --member=serviceAccount:firebase-deployer@project-987f80c5-14e3-450d-9b0.iam.gserviceaccount.com \
  --role=roles/firebase.admin
```

3. **Create Key**:
```bash
gcloud iam service-accounts keys create firebase-sa-key.json \
  --iam-account=firebase-deployer@project-987f80c5-14e3-450d-9b0.iam.gserviceaccount.com
```

4. **Deploy Using Key**:
```bash
$env:GOOGLE_APPLICATION_CREDENTIALS = "$PWD/firebase-sa-key.json"
firebase deploy --only hosting --project project-987f80c5-14e3-450d-9b0
```

### Option 3: GCP Console Web Upload

1. Go to: https://console.firebase.google.com
2. Select project `project-987f80c5-14e3-450d-9b0`
3. Navigate to Hosting
4. Upload files from `frontend/web/` directory manually

## Cost Optimization

| Component | Cost | Status |
|-----------|------|--------|
| Firebase Hosting Static | FREE | ✅ |
| Cloud Run Backend | ~FREE (early stage) | ✅ |
| Cloud SQL Database | ~$15-20/mo | ✅ |
| **Total Monthly** | **~$15-20** | Using GCP Credits |

**Free Tier Benefits**:
- 1GB storage on Firebase Hosting
- 10GB/month bandwidth (exceeding = $0.18/GB)
- Cloud Run: 2M requests/month free

## End-to-End Testing

Once deployed, access at: `https://project-987f80c5-14e3-450d-9b0.web.app`

### Frontend Health Checks
- ✅ Page loads
- ✅ Backend URL displays: `https://presentation-api-558900038680.asia-south1.run.app`
- ✅ Backend connectivity test passes
- ✅ /health endpoint responds (green indicator)

### API Connectivity Test
The frontend will automatically test:
```
GET https://presentation-api-558900038680.asia-south1.run.app/health
GET https://presentation-api-558900038680.asia-south1.run.app/
```

## Deployment Progress

| Step | Status | Details |
|------|--------|---------|
| 1. Create frontend files | ✅ Complete | HTML/CSS/JS ready |
| 2. Configure backend URL | ✅ Complete | Injected via `config.js` |
| 3. Generate configs | ✅ Complete | `firebase.json`, `.firebaserc` |
| 4. Authenticate Firebase CLI | ⏳ Pending | Requires user interaction |
| 5. Deploy to Firebase | ⏳ Pending | After authentication |
| 6. Verify E2E access | ⏳ Pending | Test frontend → backend → database |

## Next Steps

1. **Authenticate Firebase CLI**:
   - Run: `firebase login`
   - Follow browser prompts
   - Paste authorization code in terminal

2. **Deploy Frontend**:
   ```powershell
   firebase deploy --only hosting --project project-987f80c5-14e3-450d-9b0
   ```

3. **Access Frontend**:
   ```
   https://project-987f80c5-14e3-450d-9b0.web.app
   ```

4. **Verify Connectivity**:
   - Frontend should show "Backend: Connected" status
   - Health check endpoint responds with green indicator
   - Click "Refresh Status" to manually test

## Cost Monitoring

GCP Dashboard: https://console.cloud.google.com/billing/project-987f80c5-14e3-450d-9b0

Watch for:
- Cloud SQL usage (main cost)
- Firebase Hosting bandwidth
- Cloud Run invocations

## Troubleshooting

### "Failed to authenticate"
→ Run `firebase login` first

### "CORS error when testing backend"
→ Verify CORS_ORIGINS in backend includes Firebase domain
→ Add to `.env`: `CORS_ORIGINS="https://project-987f80c5-14e3-450d-9b0.web.app"`

### Backend shows "Disconnected"
→ Check Cloud Run service is running: `gcloud run services list --project project-987f80c5-14e3-450d-9b0`
→ Verify CORS middleware enabled in `backend/main.py`

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                     End User Browser                         │
└────────┬─────────────────────────────────────────────────────┘
         │ HTTPS
         ▼
┌─────────────────────────────────────────────────────────────┐
│            Firebase Hosting (Static SPA)                     │
│  URL: https://project-987f80c5-14e3-450d-9b0.web.app       │
│  Files: index.html, app.js, config.js                       │
│  Cost: FREE (within quota)                                   │
│  Region: Global CDN                                          │
└────────┬─────────────────────────────────────────────────────┘
         │ HTTPS (CORS enabled)
         ▼
┌─────────────────────────────────────────────────────────────┐
│           Google Cloud Run (FastAPI Backend)                 │
│  URL: https://presentation-api-558900038680.asia-south1...  │
│  Min Instances: 0 (no idle cost)                             │
│  Memory: 512MB, CPU: 1 core                                  │
│  Cost: ~FREE (within 2M requests/month)                      │
└────────┬─────────────────────────────────────────────────────┘
         │ TCP/IP
         ▼
┌─────────────────────────────────────────────────────────────┐
│         Google Cloud SQL (PostgreSQL Database)               │
│  Instance: presentation-db (db-f1-micro)                     │
│  Region: asia-south1                                         │
│  Cost: ~$15-20/month (smallest tier)                         │
└─────────────────────────────────────────────────────────────┘
```

## Files Modified/Created

- ✅ `frontend/web/index.html` - Main page
- ✅ `frontend/web/app.js` - JavaScript app logic
- ✅ `frontend/web/config.js` - Backend URL configuration
- ✅ `firebase.json` - Firebase Hosting config
- ✅ `.firebaserc` - Firebase project config
- ✅ `scripts/gcp/deploy-frontend-firebase.ps1` - Updated deployment script
- ✅ `deploy-firebase.js` - Node.js deployment helper

---

**Last Updated**: May 25, 2026  
**Project**: AI Presentation Avatar SaaS  
**Status**: Ready for Firebase deployment (pending authentication)
