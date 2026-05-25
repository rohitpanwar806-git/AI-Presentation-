# Firebase Deployment with OAuth Token

## ⚠️ Token Format Issue

The token you provided (`4/0AeoWuM-...`) is a Google OAuth authorization code, not a Firebase authentication token. Firebase CLI requires a different token format.

## 🔧 Solutions

### Option 1: Complete the Firebase Login Flow (Recommended - 2 minutes)

Since you have a valid Google authorization code, we can use it to complete the login:

```powershell
cd c:\Users\rohit\Downloads\AI-Presentation-
firebase login
```

This will:
1. Open a browser window
2. You should already be authenticated (since you have the auth code)
3. Copy the authorization code provided
4. Paste it when prompted in the terminal

Then deploy:
```powershell
firebase deploy --only hosting --project project-987f80c5-14e3-450d-9b0
```

---

### Option 2: Deploy via Firebase Web Console (3-5 minutes)

1. Go to: https://console.firebase.google.com/
2. Select project: `project-987f80c5-14e3-450d-9b0`
3. Click **Hosting** in left sidebar
4. Click **Get Started** or **Add Hosting**
5. Upload the contents of `frontend/web/` folder:
   - `index.html`
   - `app.js`
   - `config.js`
6. Click Deploy

---

### Option 3: Use Service Account (Most Secure - 5-10 minutes)

```powershell
# Create service account
gcloud iam service-accounts create firebase-deployer \
  --display-name="Firebase Deployer" \
  --project=project-987f80c5-14e3-450d-9b0

# Grant permissions
gcloud projects add-iam-policy-binding project-987f80c5-14e3-450d-9b0 \
  --member=serviceAccount:firebase-deployer@project-987f80c5-14e3-450d-9b0.iam.gserviceaccount.com \
  --role=roles/firebase.admin

# Create and download key
gcloud iam service-accounts keys create firebase-sa-key.json \
  --iam-account=firebase-deployer@project-987f80c5-14e3-450d-9b0.iam.gserviceaccount.com

# Set credentials and deploy
$env:GOOGLE_APPLICATION_CREDENTIALS = "$PWD/firebase-sa-key.json"
firebase deploy --only hosting --project project-987f80c5-14e3-450d-9b0
```

---

### Option 4: Use gcloud CLI if Already Authenticated

If gcloud is properly set up:

```powershell
gcloud auth login
gcloud config set project project-987f80c5-14e3-450d-9b0
firebase deploy --only hosting
```

---

## ✅ Verification After Deployment

Once deployed successfully, you should see:

```
✨ Deployment complete!

Project Console: https://console.firebase.google.com/project/project-987f80c5-14e3-450d-9b0
Hosting URL: https://project-987f80c5-14e3-450d-9b0.web.app
```

Then verify:
1. Visit: https://project-987f80c5-14e3-450d-9b0.web.app
2. Check "Backend: Connected" indicator (should be green)
3. Verify health checks show ✅

---

## 📋 Troubleshooting

| Error | Solution |
|-------|----------|
| "Failed to authenticate" | Try `firebase login` again |
| "Permission denied" | Service account needs `roles/firebase.admin` |
| "Site not found" | Check .firebaserc has correct project ID |
| Backend shows "Disconnected" | Verify backend is running, check CORS |

---

## 📝 Your Token Information

The token you provided:
- **Format**: Google OAuth Authorization Code
- **Status**: Valid but needs to be exchanged for access token
- **Use**: Complete the `firebase login` flow

To use it:
1. Run: `firebase login`
2. Follow browser prompts
3. When asked for code, paste: `4/0AeoWuM-kQ-KLl32pEG4R9Y1kgEaP6y1wFbhOhIaLMZn-1OlVJD31S8-wAsiDTHtErCSMKw`

---

## 🚀 Quick Deploy Commands

**After authenticating (firebase login):**

```powershell
cd c:\Users\rohit\Downloads\AI-Presentation-
firebase deploy --only hosting --project project-987f80c5-14e3-450d-9b0
```

**Or use the automated script:**

```powershell
node deploy.js
```

---

## 📱 Your Deployment Details

| Item | Value |
|------|-------|
| **Project ID** | project-987f80c5-14e3-450d-9b0 |
| **Firebase URL** | https://project-987f80c5-14e3-450d-9b0.web.app |
| **Backend URL** | https://presentation-api-558900038680.asia-south1.run.app |
| **Files to Deploy** | frontend/web/ (23.5 KB) |
| **Cost** | FREE (within quota) |

---

**Next Step**: Choose one of the 4 options above and complete the deployment! 🎉
