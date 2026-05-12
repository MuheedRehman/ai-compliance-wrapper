# Phase 0A Terraform Foundation

This directory contains the minimal, low-cost staging infrastructure required to run the AI Compliance Backend on Google Cloud.

## Architecture & Tradeoffs

- **Artifact Registry**: Docker repository for backend containers.
- **Secret Manager**: Secure configuration containers (OpenAI, HMAC, Firecrawl, DB URL). 
- **Cloud SQL (PostgreSQL)**: Single-zone `db-f1-micro`. *Note: `db-f1-micro` is the intended low-cost starting tier, but it must be validated by `terraform plan/apply` in `europe-west3` as regional availability can occasionally vary.*
- **Cloud Run**: Scales to 0, attaches to Cloud SQL via unix socket. By default, it allows `allUsers` (unauthenticated) access. This is an explicit, temporary staging/testing tradeoff enabled by the `allow_unauthenticated` variable.

## Terraform State Caveats

- **External Secret Values**: Real secret payloads (OpenAI key, etc.) are **not managed by Terraform**. Terraform strictly provisions empty Secret Manager containers.
- **Generated Passwords**: The auto-generated database password assigned to `appuser` **is stored in the Terraform state file** (`terraform.tfstate`). Secure this state file appropriately.

## Deployment Flow (Two-Step Process)

Cloud Run will fail to deploy if Secret Manager versions are completely empty. We use a strictly ordered, two-step deployment process to prevent failure loops.

### Step 1: Provision Base Infra & Secrets

Run Terraform with `deploy_cloud_run = false` (the default). This creates the database, service accounts, Artifact Registry, and empty Secret Manager containers.

```bash
terraform apply
```

### Step 2: Manual Secret Injection

After Step 1 completes, manually populate the secrets using the Google Cloud CLI. You will need to construct your `DATABASE_URL` using the generated password and connection name outputted by Terraform.

```bash
# Add OpenAI key
echo -n "sk-proj-YOUR-REAL-KEY" | gcloud secrets versions add OPENAI_API_KEY --data-file=-

# Add Firecrawl key
echo -n "fc-YOUR-REAL-KEY" | gcloud secrets versions add FIRECRAWL_API_KEY --data-file=-

# Add a secure random HMAC secret
echo -n "your-super-secret-hmac-string" | gcloud secrets versions add EVIDENCE_HMAC_SECRET --data-file=-

# Add the real database URL (replace <PASSWORD> with the terraform output)
echo -n "postgresql+psycopg2://appuser:<PASSWORD>@/aicompliance?host=/cloudsql/eu-ai-act-platform-staging:europe-west3:aicompliance-db-staging" | gcloud secrets versions add DATABASE_URL --data-file=-
```

### Step 3: Image Push

Build and push your real backend container image to the Artifact Registry repository created in Step 1.

```bash
docker build -t europe-west3-docker.pkg.dev/eu-ai-act-platform-staging/backend-repo/ai-compliance-backend:latest .
docker push europe-west3-docker.pkg.dev/eu-ai-act-platform-staging/backend-repo/ai-compliance-backend:latest
```

### Step 4: Cloud Run Deployment

Once the container image is in the Artifact Registry and secret values exist, deploy Cloud Run by toggling the deployment flag:

```bash
terraform apply -var="deploy_cloud_run=true" -var="container_image=europe-west3-docker.pkg.dev/eu-ai-act-platform-staging/backend-repo/ai-compliance-backend:latest"
```

## Final Caveats
- If `db-f1-micro` fails deployment validation inside `europe-west3` due to unpredictable Google regional capacity limits, bump it to a supported higher tier if validation fails (e.g. `db-g1-small` or `db-custom-1-3840`).
- Remember that `terraform.tfstate` tracks the raw PostgreSQL password; never commit this state file to git.
- The Cloud Run service remains universally reachable (`allUsers`) until you explicitly apply `-var="allow_unauthenticated=false"` after staging passes regression.
