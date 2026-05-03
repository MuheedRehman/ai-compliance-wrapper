# Sprint 6B — Alembic Migrations + PostgreSQL Test DB + CI Release Gate

## Added files

```text
alembic.ini
alembic/env.py
alembic/versions/0001_initial_governance_schema.py
alembic/versions/0002_postgres_partial_indexes.py
docker-compose.test.yml
scripts/release_check.py
scripts/release_check.ps1
.github/workflows/ci.yml
tests/test_postgres_indexes.py
```

## Goal

Make schema changes reproducible and block unsafe code from shipping.

## Local SQLite sanity check

```powershell
pytest
```

## Local PostgreSQL check with Docker Desktop

Start Postgres:

```powershell
docker compose -f docker-compose.test.yml up -d
```

Set environment variables:

```powershell
$env:DATABASE_URL="postgresql+psycopg2://ai_test:ai_test@localhost:5433/ai_compliance_test"
$env:OPENAI_API_KEY="dummy_test_key"
$env:DEFAULT_MODEL="gpt-4.1-nano"
$env:APP_ENV="testing"
$env:FEATURE_ID_ENFORCEMENT="warn"
$env:CANDIDATE_VERSION_POLICY="allow_with_warning"
$env:EVIDENCE_CHAIN_MODE="best_effort_tenant_chain"
$env:EVIDENCE_HMAC_SECRET="test_secret_123456789"
```

Run migrations:

```powershell
alembic upgrade head
```

Run tests:

```powershell
pytest
```

Run release gate:

```powershell
python scripts\release_check.py
```

or:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\release_check.ps1
```

Stop Postgres:

```powershell
docker compose -f docker-compose.test.yml down
```

## Release gate

```text
pytest passes
alembic upgrade head passes
alembic downgrade -1 passes
alembic upgrade head passes again
PostgreSQL partial indexes exist
```

## Notes

- SQLite local tests remain useful for speed.
- PostgreSQL CI is the real target for schema/concurrency behavior.
- `0002_postgres_partial_indexes.py` is skipped on non-Postgres DBs.
