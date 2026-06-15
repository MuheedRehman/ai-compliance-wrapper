"""Security hardening: audit immutability, performance indexes, stripe idempotency

Revision ID: 0014
Revises: 0013
Create Date: 2026-06-15 00:00:00.000000

Changes:
- processed_stripe_events table (Stripe webhook idempotency guard)
- Composite performance indexes on evidence_items, compliance_controls,
  fria_records, evidence_logs
- Postgres-only: immutability rules on tenant_action_audit (INSERT-only)
"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    # --- Stripe webhook idempotency table ---
    op.create_table(
        "processed_stripe_events",
        sa.Column("stripe_event_id", sa.String(), primary_key=True, nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # --- Performance: composite indexes on high-traffic query patterns ---
    op.create_index(
        "ix_evidence_items_tenant_type_status",
        "evidence_items",
        ["tenant_id", "evidence_type", "status"],
    )
    op.create_index(
        "ix_evidence_items_tenant_ai_system",
        "evidence_items",
        ["tenant_id", "ai_system_id"],
    )
    op.create_index(
        "ix_compliance_controls_tenant_status",
        "compliance_controls",
        ["tenant_id", "status"],
    )
    op.create_index(
        "ix_fria_records_tenant_status",
        "fria_records",
        ["tenant_id", "status"],
    )
    op.create_index(
        "ix_evidence_logs_tenant_feature",
        "evidence_logs",
        ["tenant_id", "feature_id"],
    )

    # --- Postgres-only: audit log immutability (INSERT-only via rules) ---
    if _is_postgres():
        op.execute(
            "CREATE RULE no_update_audit AS ON UPDATE TO tenant_action_audit DO INSTEAD NOTHING"
        )
        op.execute(
            "CREATE RULE no_delete_audit AS ON DELETE TO tenant_action_audit DO INSTEAD NOTHING"
        )


def downgrade() -> None:
    if _is_postgres():
        op.execute("DROP RULE IF EXISTS no_delete_audit ON tenant_action_audit")
        op.execute("DROP RULE IF EXISTS no_update_audit ON tenant_action_audit")

    op.drop_index("ix_evidence_logs_tenant_feature", table_name="evidence_logs")
    op.drop_index("ix_fria_records_tenant_status", table_name="fria_records")
    op.drop_index("ix_compliance_controls_tenant_status", table_name="compliance_controls")
    op.drop_index("ix_evidence_items_tenant_ai_system", table_name="evidence_items")
    op.drop_index("ix_evidence_items_tenant_type_status", table_name="evidence_items")

    op.drop_table("processed_stripe_events")
