# Sprint 5.2 — State Semantics Patch

## Fixed

### 1. Approval timestamp consistency

In `approve_feature_version()`, approving a version now clears both:

```python
version.superseded_at = None
version.rejected_at = None
```

This prevents contradictory states such as:

```text
status = approved
superseded_at = non-null
```

### 2. Rejection timestamp consistency

In `reject_feature_version()`, this patch adopts **current-state timestamp semantics**.

When a version is rejected, it now clears:

```python
version.approved_at = None
version.superseded_at = None
```

So the current status timestamp aligns with the current version state.

## Intentional decision

This codebase now treats status timestamps as **current-state indicators**, not cumulative historical markers.

If you later want full lifecycle history, add a separate `feature_version_events` table instead of overloading status timestamp columns.

## Added

### PostgreSQL migration notes

Added:

```text
backend/migrations_notes/postgres_review_task_dedupe_indexes.sql
```

This includes recommended PostgreSQL partial unique indexes for:

- open review tasks with `feature_version_id IS NULL`
- open review tasks with `feature_version_id IS NOT NULL`
- one approved version per feature

These are not auto-applied yet. Before production, add Alembic and convert these into real migrations.

## Still true

- Service-layer review-task dedupe is still the portable primary safeguard.
- PostgreSQL partial unique indexes are recommended for stronger race protection.
- Evidence chain remains best-effort tenant-local.
- Provider layer remains OpenAI-only.
