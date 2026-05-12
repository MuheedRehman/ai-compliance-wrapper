# Secrets Management Guide

The backend relies on sensitive environment variables. In GCP, these should be managed using **Google Secret Manager**.

## Required Secrets

1. `DATABASE_URL`
   - Description: The PostgreSQL connection string.
   - Value format for Cloud Run: `postgresql+psycopg2://USER:PASS@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE`
2. `OPENAI_API_KEY`
   - Description: The API key for LLM evaluations.
3. `EVIDENCE_HMAC_SECRET`
   - Description: A 64-character hex string used for signing evidence logs.
   - Generation: `openssl rand -hex 32`

## Setting Up Secrets

Using gcloud CLI:

```bash
# Create the secrets
gcloud secrets create DATABASE_URL --replication-policy="automatic"
gcloud secrets create OPENAI_API_KEY --replication-policy="automatic"
gcloud secrets create EVIDENCE_HMAC_SECRET --replication-policy="automatic"

# Add versions (it will prompt for the value)
echo -n "postgresql+psycopg2://..." | gcloud secrets versions add DATABASE_URL --data-file=-
echo -n "sk-..." | gcloud secrets versions add OPENAI_API_KEY --data-file=-
echo -n "my-64-char-hex-secret" | gcloud secrets versions add EVIDENCE_HMAC_SECRET --data-file=-
```

## IAM Permissions
Ensure the Cloud Run service account has the **Secret Manager Secret Accessor** role:
```bash
gcloud projects add-iam-policy-binding <PROJECT_ID> \
    --member="serviceAccount:<CLOUD_RUN_SERVICE_ACCOUNT>" \
    --role="roles/secretmanager.secretAccessor"
```
