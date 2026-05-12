# Cloud SQL Setup Guide

This guide details how to set up PostgreSQL on Google Cloud SQL for the AI Compliance Backend.

## 1. Create the Instance
1. Go to **Cloud SQL** in the GCP Console.
2. Click **Create Instance** > **PostgreSQL**.
3. Choose PostgreSQL 16 (or latest supported).
4. For staging, a `db-f1-micro` or small custom instance is sufficient.
5. Set the root password and store it securely.

## 2. Create the Database & User
1. In the Cloud SQL instance details, go to **Databases** and click **Create Database**. Name it `ai_compliance`.
2. Go to **Users** and click **Add User Account**.
3. Create a dedicated user: `ai_admin` with a strong password.

> **Warning: Connection Limits**
> A `db-f1-micro` instance has a maximum of roughly 100 connections. Since the backend configures `pool_size=5` and `max_overflow=10` per instance, a single Cloud Run container could use up to 15 connections. You **must** cap Cloud Run at `--max-instances=10` or lower to prevent database connection exhaustion, or upgrade the Cloud SQL instance size.

## 3. Configure Connection
When connecting from Cloud Run, use the `postgresql+psycopg2` driver with the Cloud SQL unix socket:

```
DATABASE_URL=postgresql+psycopg2://ai_admin:<PASSWORD>@/ai_compliance?host=/cloudsql/<PROJECT_ID>:<REGION>:<INSTANCE_NAME>
```

Add this URL to Google Secret Manager (see `secrets.md`).

## 4. Run Migrations
Before the application can be used, run Alembic migrations. This can be done locally via Cloud SQL Auth Proxy:
```bash
cloud_sql_proxy -instances=<PROJECT_ID>:<REGION>:<INSTANCE_NAME>=tcp:5432
```
Then run:
```bash
DATABASE_URL=postgresql+psycopg2://ai_admin:<PASSWORD>@localhost:5432/ai_compliance alembic upgrade head
```
