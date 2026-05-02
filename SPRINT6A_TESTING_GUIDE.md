# Sprint 6A — Testing Foundation Guide

## Goal

Sprint 6A adds automated tests for the highest-risk governance paths:

- Feature binding
- Missing/unknown feature handling
- Candidate feature-version behavior
- Version approval/rejection transitions
- Review task deduplication
- Provider failure evidence persistence

## Folder structure

```text
backend/
  app/
    ...
  tests/
    conftest.py
    test_pipeline.py
    test_feature_versions.py
    test_review_tasks.py
  pytest.ini
```

Yes, tests should live in a dedicated `tests/` folder at the backend root.

## Important

These tests default to SQLite for local speed and simplicity. The next hardening step should run the same tests against real PostgreSQL because partial indexes, transaction behavior, and concurrency semantics are PostgreSQL-specific.

For Sprint 6A, this gives you fast local confidence before Sprint 6B migrations/CI/Postgres.

## Windows commands

From the backend folder:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
notepad .env
```

Set:

```env
OPENAI_API_KEY=dummy_test_key
DEFAULT_MODEL=gpt-4.1-nano
DATABASE_URL=sqlite:///./app/data/app.db
APP_ENV=testing
FEATURE_ID_ENFORCEMENT=warn
CANDIDATE_VERSION_POLICY=allow_with_warning
EVIDENCE_HMAC_SECRET=test_secret_123456789
```

Run all tests:

```powershell
pytest
```

Run one file:

```powershell
pytest tests\test_pipeline.py
```

Run one test:

```powershell
pytest tests\test_feature_versions.py::test_reject_current_approved_with_replacement_repoints_feature
```

## What passing means

Passing Sprint 6A means your current governance path has a basic safety net. It does not mean the product is production-ready yet.

Before production, add:

- Alembic migrations
- PostgreSQL test DB
- CI
- partial unique indexes
- standardized error responses
