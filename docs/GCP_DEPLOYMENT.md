# GCP Deployment Guide (Cost Optimized)

This guide deploys:
- Backend: Cloud Run (min instances = 0)
- Database: Cloud SQL PostgreSQL (db-f1-micro)
- Container registry: Artifact Registry
- Frontend: Firebase Hosting (static starter)
- Secrets: Secret Manager

## Selected Configuration
- Project: project-987f80c5-14e3-450d-9b0
- Region: asia-south1 (Mumbai)
- Auth: Supabase Auth + Google OAuth
- Database tier: db-f1-micro
- Frontend mode: Firebase Hosting

## Estimated Monthly Cost (early stage)
- Cloud Run: often within free tier for low traffic
- Cloud SQL db-f1-micro + 10 GB SSD: roughly low cost baseline
- Artifact Registry + Secret Manager: minimal at low usage
- Firebase Hosting: typically low or free at starter usage

Note: Cloud SQL is usually the main fixed cost driver.

## Prerequisites
1. Install and login gcloud CLI.
2. Ensure billing enabled on the GCP project.
3. Ensure Python and Docker are installed locally.
4. Optional for frontend deploy: Node.js and firebase-tools.

## 1) Bootstrap Core Resources
Run from repository root:

```powershell
./scripts/gcp/preflight.ps1 -ProjectId "project-987f80c5-14e3-450d-9b0"
./scripts/gcp/bootstrap.ps1 -ProjectId "project-987f80c5-14e3-450d-9b0" -Region "asia-south1"
```

Current blocker detected in this environment:
- Project billing is attached but billing account is closed.
- Reopen billing account `013F74-EA0BA7-0642BA` or link a different open billing account.

What this creates:
- APIs enabled
- Artifact Registry repo
- Cloud SQL instance
- Postgres database

## 2) Create Cloud SQL User
Create app database user manually (one-time):

```powershell
gcloud sql users create app_user --instance presentation-db --project project-987f80c5-14e3-450d-9b0 --password "<strong-password>"
```

## 3) Store Secrets in Secret Manager

```powershell
./scripts/gcp/create-secrets.ps1 -ProjectId "project-987f80c5-14e3-450d-9b0"
```

Provide these values when prompted:
- SECRET_KEY
- SUPABASE_URL
- SUPABASE_KEY
- ANTHROPIC_API_KEY
- ELEVENLABS_API_KEY
- PINECONE_API_KEY
- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET
- DB_PASSWORD

## 4) Deploy Backend to Cloud Run

```powershell
./scripts/gcp/deploy-backend.ps1 -ProjectId "project-987f80c5-14e3-450d-9b0" -Region "asia-south1"
```

The script:
- Builds image with Cloud Build
- Deploys Cloud Run service with low-cost settings
- Connects Cloud SQL via Unix socket
- Sets GOOGLE_REDIRECT_URI automatically

## 5) Deploy Frontend (Firebase Hosting)

```powershell
./scripts/gcp/deploy-frontend-firebase.ps1 -ProjectId "project-987f80c5-14e3-450d-9b0"
```

This currently deploys a static placeholder in frontend/web.

## Cost-Optimization Settings Already Applied
- Cloud Run min instances = 0
- Cloud Run max instances = 3
- Memory = 512Mi, CPU = 1
- Concurrency = 80
- Cloud SQL smallest managed tier
- Single region deployment

## Next Optimization Steps
1. Add Cloud CDN only after traffic increases.
2. Move high-volume media files to Cloud Storage.
3. Keep logs retention short in Logging if needed.
4. Consider Supabase Postgres if Cloud SQL base cost becomes too high.
