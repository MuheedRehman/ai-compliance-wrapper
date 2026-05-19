"""ai system lifecycle reviews

Revision ID: 0011
Revises: 0010
Create Date: 2026-05-19 00:00:00.000000

"""
from typing import Optional, Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0011"
down_revision: Optional[str] = "0010"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    op.add_column("ai_systems", sa.Column("owner_email", sa.String(), nullable=True))
    op.add_column("ai_systems", sa.Column("technical_owner_email", sa.String(), nullable=True))
    op.add_column("ai_systems", sa.Column("legal_owner_email", sa.String(), nullable=True))
    op.add_column(
        "ai_systems",
        sa.Column("review_status", sa.String(), nullable=False, server_default="not_started"),
    )
    op.add_column("ai_systems", sa.Column("next_review_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("ai_systems", sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("ai_systems", sa.Column("lifecycle_notes", sa.Text(), nullable=True))
    op.create_index(op.f("ix_ai_systems_owner_email"), "ai_systems", ["owner_email"], unique=False)
    op.create_index(op.f("ix_ai_systems_next_review_at"), "ai_systems", ["next_review_at"], unique=False)

    op.create_table(
        "ai_system_review_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("ai_system_id", sa.String(), nullable=False),
        sa.Column("reviewer_email", sa.String(), nullable=True),
        sa.Column("review_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("findings_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("actions_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("next_review_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["ai_system_id"], ["ai_systems.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_system_review_events_id"), "ai_system_review_events", ["id"], unique=False)
    op.create_index(op.f("ix_ai_system_review_events_tenant_id"), "ai_system_review_events", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_ai_system_review_events_ai_system_id"), "ai_system_review_events", ["ai_system_id"], unique=False)
    op.create_index(op.f("ix_ai_system_review_events_reviewer_email"), "ai_system_review_events", ["reviewer_email"], unique=False)
    op.create_index(op.f("ix_ai_system_review_events_review_type"), "ai_system_review_events", ["review_type"], unique=False)
    op.create_index(op.f("ix_ai_system_review_events_status"), "ai_system_review_events", ["status"], unique=False)
    op.create_index(op.f("ix_ai_system_review_events_created_at"), "ai_system_review_events", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_system_review_events_created_at"), table_name="ai_system_review_events")
    op.drop_index(op.f("ix_ai_system_review_events_status"), table_name="ai_system_review_events")
    op.drop_index(op.f("ix_ai_system_review_events_review_type"), table_name="ai_system_review_events")
    op.drop_index(op.f("ix_ai_system_review_events_reviewer_email"), table_name="ai_system_review_events")
    op.drop_index(op.f("ix_ai_system_review_events_ai_system_id"), table_name="ai_system_review_events")
    op.drop_index(op.f("ix_ai_system_review_events_tenant_id"), table_name="ai_system_review_events")
    op.drop_index(op.f("ix_ai_system_review_events_id"), table_name="ai_system_review_events")
    op.drop_table("ai_system_review_events")

    op.drop_index(op.f("ix_ai_systems_next_review_at"), table_name="ai_systems")
    op.drop_index(op.f("ix_ai_systems_owner_email"), table_name="ai_systems")
    op.drop_column("ai_systems", "lifecycle_notes")
    op.drop_column("ai_systems", "last_reviewed_at")
    op.drop_column("ai_systems", "next_review_at")
    op.drop_column("ai_systems", "review_status")
    op.drop_column("ai_systems", "legal_owner_email")
    op.drop_column("ai_systems", "technical_owner_email")
    op.drop_column("ai_systems", "owner_email")
