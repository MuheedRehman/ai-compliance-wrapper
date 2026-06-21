"""Runtime Governance SDK — policy check log + developer key description

Revision ID: 0016
Revises: 0015
Create Date: 2026-06-21 00:00:00.000000

Changes:
- runtime_policy_checks table: immutable log of every policy-check API call
- api_keys.description: optional human-readable description for developer keys
"""
from typing import Optional, Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "0016"
down_revision: Optional[str] = "0015"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    op.create_table(
        "runtime_policy_checks",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("api_key_id", sa.String(), nullable=True),
        sa.Column("feature_id", sa.String(), nullable=True),
        sa.Column("ai_system_id", sa.String(), nullable=True),
        sa.Column("prompt_hash", sa.String(), nullable=True),
        sa.Column("prompt_length", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("policy_refs", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_runtime_policy_checks_id", "runtime_policy_checks", ["id"])
    op.create_index("ix_runtime_policy_checks_tenant_id", "runtime_policy_checks", ["tenant_id"])
    op.create_index("ix_runtime_policy_checks_api_key_id", "runtime_policy_checks", ["api_key_id"])
    op.create_index("ix_runtime_policy_checks_feature_id", "runtime_policy_checks", ["feature_id"])
    op.create_index("ix_runtime_policy_checks_decision", "runtime_policy_checks", ["decision"])
    op.create_index("ix_runtime_policy_checks_created_at", "runtime_policy_checks", ["created_at"])

    op.add_column("api_keys", sa.Column("description", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("api_keys", "description")
    op.drop_index("ix_runtime_policy_checks_created_at", table_name="runtime_policy_checks")
    op.drop_index("ix_runtime_policy_checks_decision", table_name="runtime_policy_checks")
    op.drop_index("ix_runtime_policy_checks_feature_id", table_name="runtime_policy_checks")
    op.drop_index("ix_runtime_policy_checks_api_key_id", table_name="runtime_policy_checks")
    op.drop_index("ix_runtime_policy_checks_tenant_id", table_name="runtime_policy_checks")
    op.drop_index("ix_runtime_policy_checks_id", table_name="runtime_policy_checks")
    op.drop_table("runtime_policy_checks")
