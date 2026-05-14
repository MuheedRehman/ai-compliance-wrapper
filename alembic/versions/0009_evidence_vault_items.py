"""evidence vault items

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-14 00:00:00.000000

"""
from typing import Optional, Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0009"
down_revision: Optional[str] = "0008"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    op.create_table(
        "evidence_items",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("ai_system_id", sa.String(), nullable=True),
        sa.Column("control_id", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("evidence_type", sa.String(), nullable=False, server_default="policy"),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("owner_email", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("review_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence_hash", sa.String(), nullable=False),
        sa.Column("hmac_signature", sa.String(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["ai_system_id"], ["ai_systems.id"]),
        sa.ForeignKeyConstraint(["control_id"], ["compliance_controls.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evidence_items_id"), "evidence_items", ["id"], unique=False)
    op.create_index(op.f("ix_evidence_items_tenant_id"), "evidence_items", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_evidence_items_ai_system_id"), "evidence_items", ["ai_system_id"], unique=False)
    op.create_index(op.f("ix_evidence_items_control_id"), "evidence_items", ["control_id"], unique=False)
    op.create_index(op.f("ix_evidence_items_evidence_type"), "evidence_items", ["evidence_type"], unique=False)
    op.create_index(op.f("ix_evidence_items_owner_email"), "evidence_items", ["owner_email"], unique=False)
    op.create_index(op.f("ix_evidence_items_status"), "evidence_items", ["status"], unique=False)
    op.create_index(op.f("ix_evidence_items_collected_at"), "evidence_items", ["collected_at"], unique=False)
    op.create_index(op.f("ix_evidence_items_review_at"), "evidence_items", ["review_at"], unique=False)
    op.create_index(op.f("ix_evidence_items_expires_at"), "evidence_items", ["expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_evidence_items_expires_at"), table_name="evidence_items")
    op.drop_index(op.f("ix_evidence_items_review_at"), table_name="evidence_items")
    op.drop_index(op.f("ix_evidence_items_collected_at"), table_name="evidence_items")
    op.drop_index(op.f("ix_evidence_items_status"), table_name="evidence_items")
    op.drop_index(op.f("ix_evidence_items_owner_email"), table_name="evidence_items")
    op.drop_index(op.f("ix_evidence_items_evidence_type"), table_name="evidence_items")
    op.drop_index(op.f("ix_evidence_items_control_id"), table_name="evidence_items")
    op.drop_index(op.f("ix_evidence_items_ai_system_id"), table_name="evidence_items")
    op.drop_index(op.f("ix_evidence_items_tenant_id"), table_name="evidence_items")
    op.drop_index(op.f("ix_evidence_items_id"), table_name="evidence_items")
    op.drop_table("evidence_items")
