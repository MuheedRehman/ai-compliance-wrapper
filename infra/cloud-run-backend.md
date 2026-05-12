# Cloud Run Backend Deployment Guide

This guide covers deploying the AI Compliance Backend to Google Cloud Run.

## Prerequisites
1. Ensure the Dockerfile is in the root of the `backend` directory.
2. Ensure you have provisioned Cloud SQL and Secrets (see `cloud-sql.md` and `secrets.md`).
3. Ensure the `cloudbuild.yaml` file exists in the repository root.

## Deployment Method A: Cloud Build (Recommended)
You can trigger a deployment using the `cloudbuild.yaml` file.

```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_CLOUD_SQL_INSTANCE="<PROJECT_ID>:<REGION>:<INSTANCE_NAME>" .
```

This will:
1. Run tests.
2. Build the Docker image.
3. Push to GCR/Artifact Registry.
4. Deploy to Cloud Run, exposing the latest versions of secrets as environment variables and attaching the Cloud SQL instance with a max-instances cap.


## Deployment Method B: Manual gcloud Deploy
If you want to deploy directly from source:

```bash
cd backend
gcloud run deploy ai-compliance-backend \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars APP_ENV=staging \
  --set-secrets="DATABASE_URL=DATABASE_URL:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,EVIDENCE_HMAC_SECRET=EVIDENCE_HMAC_SECRET:latest" \
  --add-cloudsql-instances="<PROJECT_ID>:<REGION>:<INSTANCE_NAME>" \
  --max-instances=10
```

## Post-Deployment Verification
Once deployed, hit the root URL of your Cloud Run service to check the health endpoint:
```
GET https://ai-compliance-backend-...run.app/
```
You should see:
```json
{
  "status": "ok",
  "service": "AI Compliance & Governance Wrapper",
  "version": "0.5.0",
  "sprint": "Phase 3 Registry Endpoints",
  "evidence_chain": "best_effort_tenant_chain"
}
```
