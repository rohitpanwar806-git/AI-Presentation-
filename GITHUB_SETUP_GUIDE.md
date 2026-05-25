# GitHub Integration & Deployment Setup

This guide explains how to connect your GitHub repository with GCP Cloud Run and Vercel for automatic deployments.

## Prerequisites

- GitHub account with repository access
- GCP Project ID: `project-987f80c5-14e3-450d-9b0`
- Vercel account (for frontend deployment)
- GCP Service Account with Cloud Run permissions

## Step 1: Set Up GitHub Repository

```bash
# Clone the repository (if not already done)
git clone https://github.com/rohitpanwar806-git/AI-Presentation-.git
cd AI-Presentation-

# Create main branch if needed
git checkout -b main

# Make sure all code is committed
git add .
git commit -m "Initial commit: Avatar & Voice selection with Agentic AI"

# Push to main branch
git push origin main
```

## Step 2: Configure GCP Workload Identity (Recommended for Security)

### Create Service Account in GCP

```bash
# Set variables
export PROJECT_ID="project-987f80c5-14e3-450d-9b0"
export SERVICE_ACCOUNT="github-actions-deploy"
export WORKLOAD_IDENTITY_POOL="github-actions-pool"
export WORKLOAD_IDENTITY_PROVIDER="github-actions-provider"

# Create service account
gcloud iam service-accounts create $SERVICE_ACCOUNT \
  --project=$PROJECT_ID \
  --display-name="GitHub Actions Deployment Account"

# Grant necessary roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

### Set Up Workload Identity Federation

```bash
# Enable required APIs
gcloud services enable iamcredentials.googleapis.com \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com \
  sts.googleapis.com \
  --project=$PROJECT_ID

# Create workload identity pool
gcloud iam workload-identity-pools create $WORKLOAD_IDENTITY_POOL \
  --project=$PROJECT_ID \
  --location=global \
  --display-name="GitHub Actions Pool"

# Create workload identity provider
gcloud iam workload-identity-pools providers create-oidc $WORKLOAD_IDENTITY_PROVIDER \
  --project=$PROJECT_ID \
  --location=global \
  --workload-identity-pool=$WORKLOAD_IDENTITY_POOL \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.actor=assertion.actor" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-condition="assertion.repository == 'rohitpanwar806-git/AI-Presentation-'"

# Get the workload identity provider resource name
export WORKLOAD_IDENTITY_PROVIDER_RESOURCE=$(gcloud iam workload-identity-pools providers describe $WORKLOAD_IDENTITY_PROVIDER \
  --project=$PROJECT_ID \
  --location=global \
  --workload-identity-pool=$WORKLOAD_IDENTITY_POOL \
  --format='value(name)')

echo "Workload Identity Provider: $WORKLOAD_IDENTITY_PROVIDER_RESOURCE"

# Grant the GitHub Actions workflow access to the service account
gcloud iam service-accounts add-iam-policy-binding \
  "${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --project=$PROJECT_ID \
  --role="roles/iam.workloadIdentityUser" \
  --condition='resource.name == "projects/-/serviceAccounts/'${SERVICE_ACCOUNT}'@'${PROJECT_ID}'.iam.gserviceaccount.com"'
```

## Step 3: Add GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

### Required GCP Secrets

1. **GCP_WORKLOAD_IDENTITY_PROVIDER**
   ```
   Value: projects/[PROJECT_NUMBER]/locations/global/workloadIdentityPools/github-actions-pool/providers/github-actions-provider
   ```
   Get PROJECT_NUMBER: `gcloud projects describe project-987f80c5-14e3-450d-9b0 --format='value(projectNumber)'`

2. **GCP_SERVICE_ACCOUNT**
   ```
   Value: github-actions-deploy@project-987f80c5-14e3-450d-9b0.iam.gserviceaccount.com
   ```

### Required Application Secrets

3. **ANTHROPIC_API_KEY**
   - Get from https://console.anthropic.com/
   - Value: `sk-ant-...`

4. **SMTP_USERNAME**
   - Value: `gravey199@gmail.com`

5. **SMTP_PASSWORD**
   - App-specific password from Gmail
   - Value: `Iphone@99292023` (or your app password)

6. **SMTP_FROM_EMAIL**
   - Value: `gravey199@gmail.com`

### Required Vercel Secrets

7. **VERCEL_TOKEN**
   - Get from https://vercel.com/account/tokens
   - Click "Create" → Give it name → Copy token

8. **VERCEL_ORG_ID**
   - From Vercel dashboard → Settings → Team ID
   - Or: `vercel whoami --token [YOUR_TOKEN]` (optional)

9. **VERCEL_PROJECT_ID**
   - From Vercel project settings
   - Or: `vercel projects ls --token [YOUR_TOKEN]`

### Optional Secrets

10. **CORS_ORIGINS**
    - Comma-separated list of allowed origins
    - Value: `http://localhost:3000,https://web-seven-swart-96tyghlog6.vercel.app`

## Step 4: Verify GitHub Secrets

```bash
# List secrets (doesn't show values)
gh secret list --repo rohitpanwar806-git/AI-Presentation-
```

Expected output:
```
ANTHROPIC_API_KEY
CORS_ORIGINS
GCP_SERVICE_ACCOUNT
GCP_WORKLOAD_IDENTITY_PROVIDER
SMTP_FROM_EMAIL
SMTP_PASSWORD
SMTP_USERNAME
VERCEL_ORG_ID
VERCEL_PROJECT_ID
VERCEL_TOKEN
```

## Step 5: Enable GitHub Actions

1. Go to your repository → Actions tab
2. Verify workflows are enabled
3. You should see:
   - `Build & Deploy to Cloud Run & Vercel` (deploy.yml)
   - `Test PR` (test-pr.yml)

## Step 6: Push to Main and Deploy

```bash
# Make sure everything is committed
git status

# Push to main
git push origin main

# Watch the deployment
# Go to: GitHub → Actions → Workflows → "Build & Deploy to Cloud Run & Vercel"
```

## Verify Deployment

### Check Cloud Run
```bash
gcloud run services list --region asia-south1 --project project-987f80c5-14e3-450d-9b0

# Test the health endpoint
curl https://presentation-api-558900038680.asia-south1.run.app/health
```

### Check Vercel
```bash
# Visit your Vercel deployment URL
# Typically: https://[your-project-name].vercel.app
```

## Troubleshooting

### Deployment Failed
1. Check GitHub Actions logs: Repository → Actions → Latest workflow run
2. Look for error messages in the "Logs" section
3. Common issues:
   - Missing GitHub secrets
   - Invalid GCP credentials
   - Vercel token expired
   - Port binding issue in Cloud Run

### Cloud Run Container Won't Start
```bash
# Check Cloud Run logs
gcloud run services describe presentation-api \
  --region asia-south1 \
  --project project-987f80c5-14e3-450d-9b0

# View recent logs
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=presentation-api" \
  --limit 50 \
  --format=json \
  --project project-987f80c5-14e3-450d-9b0
```

### Vercel Deployment Failed
```bash
# Check Vercel deployment logs
vercel logs --token [YOUR_TOKEN] [DEPLOYMENT_ID]

# Or check Vercel dashboard → Deployments tab
```

## Future Updates

After initial setup, every push to main will:
1. ✅ Run Python tests
2. ✅ Build Docker image
3. ✅ Push to Google Artifact Registry
4. ✅ Deploy to Cloud Run (auto-scales to 0 when idle)
5. ✅ Deploy frontend to Vercel (instant static hosting)

## Rollback Strategy

If a deployment breaks production:

```bash
# Revert to previous commit
git revert HEAD

# Push to main to trigger automatic rollback deployment
git push origin main

# Or manually deploy previous revision
gcloud run deploy presentation-api \
  --image asia-south1-docker.pkg.dev/project-987f80c5-14e3-450d-9b0/presentation-artifacts/presentation-api:[PREVIOUS_SHA] \
  --region asia-south1 \
  --project project-987f80c5-14e3-450d-9b0
```

## Costs

- **Cloud Run**: ~$0.0000042 per request + ~$0.00002500 per vCPU-second (first 2M requests free)
- **Vercel**: Free tier includes up to 50 GB bandwidth/month
- **Google Artifact Registry**: ~$0.10 per GB stored (first 0.5 GB free)

## Support

For issues:
1. Check GitHub Actions logs
2. Check Cloud Run logs: `gcloud logging read ...`
3. Check Vercel dashboard
4. Review this setup guide

---

**Setup Completed:** [Date]
**Next:** Run `git push origin main` to trigger first deployment
