"""website scanner

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-13 00:00:00.000000

"""
from typing import Optional, Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0007"
down_revision: Optional[str] = "0006"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    op.create_table(
        "website_scans",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("normalized_url", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="completed"),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("detected_signals_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("evidence_refs_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("gap_findings_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("classification_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("suggested_actions_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("source_pages_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("confidence_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ai_system_id", sa.String(), nullable=True),
        sa.Column("intake_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
        sa.ForeignKeyConstraint(["ai_system_id"], ["ai_systems.id"]),
        sa.ForeignKeyConstraint(["intake_id"], ["intake_assessments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_website_scans_id"), "website_scans", ["id"], unique=False)
    op.create_index(op.f("ix_website_scans_tenant_id"), "website_scans", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_website_scans_status"), "website_scans", ["status"], unique=False)
    op.create_index(op.f("ix_website_scans_ai_system_id"), "website_scans", ["ai_system_id"], unique=False)
    op.create_index(op.f("ix_website_scans_intake_id"), "website_scans", ["intake_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_website_scans_intake_id"), table_name="website_scans")
    op.drop_index(op.f("ix_website_scans_ai_system_id"), table_name="website_scans")
    op.drop_index(op.f("ix_website_scans_status"), table_name="website_scans")
    op.drop_index(op.f("ix_website_scans_tenant_id"), table_name="website_scans")
    op.drop_index(op.f("ix_website_scans_id"), table_name="website_scans")
    op.drop_table("website_scans")
