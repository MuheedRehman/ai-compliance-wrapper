"""evidence artifacts

Revision ID: 0012
Revises: 0011
Create Date: 2026-05-21 00:00:00.000000

"""
from typing import Optional, Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0012"
down_revision: Optional[str] = "0011"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    op.create_table(
        "evidence_artifacts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("evidence_item_id", sa.String(), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False, server_default="application/octet-stream"),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("artifact_hash", sa.String(), nullable=False),
        sa.Column("hmac_signature", sa.String(), nullable=False),
        sa.Column("storage_backend", sa.String(), nullable=False, server_default="database"),
        sa.Column("storage_key", sa.String(), nullable=False),
        sa.Column("content_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["evidence_item_id"], ["evidence_items.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evidence_artifacts_id"), "evidence_artifacts", ["id"], unique=False)
    op.create_index(op.f("ix_evidence_artifacts_tenant_id"), "evidence_artifacts", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_evidence_artifacts_evidence_item_id"), "evidence_artifacts", ["evidence_item_id"], unique=False)
    op.create_index(op.f("ix_evidence_artifacts_artifact_hash"), "evidence_artifacts", ["artifact_hash"], unique=False)
    op.create_index(op.f("ix_evidence_artifacts_storage_backend"), "evidence_artifacts", ["storage_backend"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_evidence_artifacts_storage_backend"), table_name="evidence_artifacts")
    op.drop_index(op.f("ix_evidence_artifacts_artifact_hash"), table_name="evidence_artifacts")
    op.drop_index(op.f("ix_evidence_artifacts_evidence_item_id"), table_name="evidence_artifacts")
    op.drop_index(op.f("ix_evidence_artifacts_tenant_id"), table_name="evidence_artifacts")
    op.drop_index(op.f("ix_evidence_artifacts_id"), table_name="evidence_artifacts")
    op.drop_table("evidence_artifacts")
