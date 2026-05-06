# Sprint 5 — Tenancy + Version Integrity Patch

This patch fixes the must-change issues from Sprint 4.

## Fixes included

- `feature_id` is no longer globally unique.
- `AiFeature` uses surrogate `id` primary key.
- Tenant-scoped feature identity: `UniqueConstraint(tenant_id, feature_id)`.
- Review-task dedupe no longer depends on nullable unique constraint alone.
- Review-task creation uses `db.begin_nested()` savepoints.
- Rejected/superseded feature versions are blocked.
- Candidate versions are governed by `CANDIDATE_VERSION_POLICY`.
- Active approved/current version cannot be rejected accidentally.
- Missing feature_id + block mode now writes durable evidence before rejecting.
- Evidence chain mode is explicitly documented as best-effort tenant-local.
- Added code-level dedupe as primary guarantee; DB constraints are backup only.

## Important

This is still using `Base.metadata.create_all()` for speed. Before production, add Alembic migrations.

## Dev keys

App key:

```text
aigw_dev_app_key_123
```

Admin key:

```text
aigw_dev_admin_key_123
```


## Sprint 5.1 Patch

The `pipeline.py` final decision logic has been rewritten into explicit `if/elif/else` branches for correctness and audit readability.


## Sprint 5.2 Patch

This patch clarifies feature-version state semantics:

- Approving a version clears stale `superseded_at` and `rejected_at`.
- Rejecting a version clears stale `approved_at` and `superseded_at`.
- Status timestamps are treated as current-state indicators.
- PostgreSQL partial unique index examples are included in `migrations_notes/`.


## Sprint 5.3 Patch

This patch fixes feature-version state transitions:

- Rejecting the current approved version now moves feature pointers to an existing approved replacement.
- Superseded versions now clear stale `approved_at` and `rejected_at`.
- The codebase consistently uses current-state timestamp semantics.


## Sprint 6A Testing Foundation

This package adds a dedicated `tests/` folder with pytest-based tests for:

- Pipeline happy path
- Missing/unknown feature handling
- Provider failure evidence
- Feature-version lifecycle
- Review task dedupe

Run:

```powershell
pytest
```


## SQLAlchemy metadata fix

`EvidenceLog.metadata` was renamed to the Python attribute `request_metadata` because `metadata` is reserved by SQLAlchemy Declarative API. The database column name remains `metadata`.


## Sprint 6A SQLite Lock Fix

Provider-error evidence is written independently so it survives rollback.
For SQLite local tests, the main request transaction is rolled back before the independent evidence writer runs, avoiding `database is locked`.


## Sprint 6B

Adds Alembic migrations, PostgreSQL test support, Docker test DB, release gate scripts, and GitHub Actions CI.

## Phase 0A: Cloud Foundation

This phase prepares the AI Compliance Backend for Google Cloud Platform staging and production deployment.

- `Dockerfile` and `cloudbuild.yaml` for containerization and CI/CD.
- GCP Secret Manager integration for robust configuration handling.
- Documentation for Cloud Run and Cloud SQL deployment in the `infra/` folder.

## Firecrawl Foundation (Phase 0A Additive Extension)

Added Firecrawl wrapper to enable asynchronous and single-page scraping without heavy internal dependencies. This foundation must abide by these strict infrastructure constraints to keep costs near zero during the build phase:
- **Low-Cost GCP Usage**: Maintain low-cost architecture during the pre-revenue build phase.
- **No Always-On Workers**: Avoid background worker infrastructure; run processes synchronously where possible.
- **No Queueing System**: Do not use Pub/Sub or Celery unless clearly required in later phases.
- **Same-Region Deployment**: Keep all components in the same GCP region to eliminate cross-region network egress costs.
- **Max Instance Caps & Budgets**: Set `max-instances` tight caps (e.g., 2) on Cloud Run, use GCP budgets, and apply resource labels.
- **Helper Layer**: Firecrawl is purely a helper layer for data acquisition. The database (app.db or Cloud SQL Postgres) remains the ultimate compliance source of truth, not Firecrawl's outputs.

