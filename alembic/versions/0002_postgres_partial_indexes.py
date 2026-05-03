"""postgres partial indexes for governance invariants

Revision ID: 0002_pg_indexes
Revises: 0001_initial
Create Date: 2026-05-03
"""

from alembic import op

revision = "0002_pg_indexes"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_one_approved_version_per_feature
        ON feature_versions (tenant_id, feature_pk)
        WHERE status = 'approved';
        """
    )

    op.execute(
        """
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
        """
    )

    op.execute(
        """
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
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute("DROP INDEX IF EXISTS uq_open_review_task_with_version;")
    op.execute("DROP INDEX IF EXISTS uq_open_review_task_no_version;")
    op.execute("DROP INDEX IF EXISTS uq_one_approved_version_per_feature;")
