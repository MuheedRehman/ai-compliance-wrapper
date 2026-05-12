# Cloud Run Frontend Deployment Guide

*Note: As of Phase 0A, the frontend/dashboard has not yet been developed. This document serves as a placeholder for the future deployment strategy.*

## Planned Strategy

When the frontend is developed (e.g., using Next.js, React, or Vue), it will be deployed to **Cloud Run** to keep the infrastructure consistent and leverage the same scaling and IAM principles as the backend.

### Expected Steps
1. Create a `Dockerfile` in the `frontend` directory (multi-stage build for Node.js).
2. Add a new step to `cloudbuild.yaml` to build and deploy the frontend service.
3. Configure the frontend to point to the Cloud Run Backend URL via environment variables (e.g., `NEXT_PUBLIC_API_URL`).
4. Set up a Load Balancer or Firebase Hosting in front of Cloud Run if custom domains or CDN caching are required.
