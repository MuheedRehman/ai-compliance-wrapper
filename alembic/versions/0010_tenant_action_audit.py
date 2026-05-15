"""tenant action audit

Revision ID: 0010
Revises: 0009
Create Date: 2026-05-15 00:00:00.000000

"""
from typing import Optional, Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0010"
down_revision: Optional[str] = "0009"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    op.create_table(
        "tenant_action_audit",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("actor_user_id", sa.String(), nullable=True),
        sa.Column("actor_email", sa.String(), nullable=True),
        sa.Column("actor_role", sa.String(), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("target_type", sa.String(), nullable=False),
        sa.Column("target_id", sa.String(), nullable=True),
        sa.Column("target_email", sa.String(), nullable=True),
        sa.Column("before_json", sa.JSON(), nullable=True),
        sa.Column("after_json", sa.JSON(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tenant_action_audit_id"), "tenant_action_audit", ["id"], unique=False)
    op.create_index(op.f("ix_tenant_action_audit_tenant_id"), "tenant_action_audit", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_tenant_action_audit_actor_user_id"), "tenant_action_audit", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_tenant_action_audit_actor_email"), "tenant_action_audit", ["actor_email"], unique=False)
    op.create_index(op.f("ix_tenant_action_audit_action"), "tenant_action_audit", ["action"], unique=False)
    op.create_index(op.f("ix_tenant_action_audit_target_type"), "tenant_action_audit", ["target_type"], unique=False)
    op.create_index(op.f("ix_tenant_action_audit_target_id"), "tenant_action_audit", ["target_id"], unique=False)
    op.create_index(op.f("ix_tenant_action_audit_target_email"), "tenant_action_audit", ["target_email"], unique=False)
    op.create_index(op.f("ix_tenant_action_audit_created_at"), "tenant_action_audit", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_tenant_action_audit_created_at"), table_name="tenant_action_audit")
    op.drop_index(op.f("ix_tenant_action_audit_target_email"), table_name="tenant_action_audit")
    op.drop_index(op.f("ix_tenant_action_audit_target_id"), table_name="tenant_action_audit")
    op.drop_index(op.f("ix_tenant_action_audit_target_type"), table_name="tenant_action_audit")
    op.drop_index(op.f("ix_tenant_action_audit_action"), table_name="tenant_action_audit")
    op.drop_index(op.f("ix_tenant_action_audit_actor_email"), table_name="tenant_action_audit")
    op.drop_index(op.f("ix_tenant_action_audit_actor_user_id"), table_name="tenant_action_audit")
    op.drop_index(op.f("ix_tenant_action_audit_tenant_id"), table_name="tenant_action_audit")
    op.drop_index(op.f("ix_tenant_action_audit_id"), table_name="tenant_action_audit")
    op.drop_table("tenant_action_audit")
