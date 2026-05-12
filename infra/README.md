# Infrastructure Documentation

This directory contains deployment guides and infrastructure documentation for the AI Governance Platform on Google Cloud Platform (GCP).

## Phase 0A: Cloud Foundation
This phase establishes the foundational cloud infrastructure for staging and production, without moving into dashboard or UI development yet.

### Guides Available
1. **[Cloud SQL Setup](cloud-sql.md)** - Provisioning and configuring the PostgreSQL database.
2. **[Secrets Management](secrets.md)** - Setting up Google Secret Manager for sensitive configuration.
3. **[Cloud Run Backend](cloud-run-backend.md)** - Deploying the FastAPI backend to Cloud Run.
4. **[Cloud Run Frontend](cloud-run-frontend.md)** - Placeholder for future UI deployments.

### General Rollout Checklist
1. Enable necessary GCP APIs (Cloud Run, Cloud SQL, Secret Manager, Cloud Build).
2. Provision Cloud SQL instance and create `ai_compliance` database.
3. Add secrets to Secret Manager (`DATABASE_URL`, `OPENAI_API_KEY`, `EVIDENCE_HMAC_SECRET`).
4. Give Cloud Run service account permissions to access Secret Manager and Cloud SQL.
5. Deploy backend via Cloud Build or direct gcloud command.
6. Verify migrations and test endpoints.
