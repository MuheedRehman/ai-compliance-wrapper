-- Sprint 5.2 migration note: PostgreSQL review-task dedupe support
--
-- Service-layer dedupe remains the primary portable safeguard.
-- These partial unique indexes are recommended for PostgreSQL deployments
-- to reduce duplicate open review tasks under concurrency.
--
-- Run only after reviewing table/column names in your deployed schema.

-- Case 1: feature_version_id IS NULL
CREATE UNIQUE INDEX IF NOT EXISTS uq_open_review_task_no_version
ON review_tasks (
    tenant_id,
    COALESCE(feature_pk, ''),
    COALESCE(feature_id, ''),
    review_type,
    trigger_reason,
    status
)
WHERE status = 'open'
  AND feature_version_id IS NULL;

-- Case 2: feature_version_id IS NOT NULL
CREATE UNIQUE INDEX IF NOT EXISTS uq_open_review_task_with_version
ON review_tasks (
    tenant_id,
    COALESCE(feature_pk, ''),
    COALESCE(feature_id, ''),
    feature_version_id,
    review_type,
    trigger_reason,
    status
)
WHERE status = 'open'
  AND feature_version_id IS NOT NULL;

-- Optional feature-version lifecycle support:
-- This prevents multiple approved versions for the same feature in PostgreSQL.
-- The application already supersedes older approved versions on approval.
CREATE UNIQUE INDEX IF NOT EXISTS uq_one_approved_version_per_feature
ON feature_versions (
    tenant_id,
    feature_pk
)
WHERE status = 'approved';
