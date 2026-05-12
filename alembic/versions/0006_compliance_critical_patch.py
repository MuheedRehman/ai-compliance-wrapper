"""compliance critical patch

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-12 00:00:00.000000

"""
from typing import Optional, Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0006"
down_revision: Optional[str] = "0005"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    op.add_column("intake_assessments", sa.Column("obligation_graph_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))
    op.add_column("intake_assessments", sa.Column("legal_basis_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))
    op.add_column("intake_assessments", sa.Column("evidence_requirements_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))

    op.add_column("fria_records", sa.Column("legal_basis_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))
    op.add_column("fria_records", sa.Column("dpia_link_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
    op.add_column("fria_records", sa.Column("signoff_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))

    op.add_column("oversight_assignments", sa.Column("competence_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))

    op.add_column("incident_records", sa.Column("incident_type", sa.String(), nullable=False, server_default="standard"))
    op.add_column("incident_records", sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("incident_records", sa.Column("reported_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("incident_records", sa.Column("escalation_status", sa.String(), nullable=False, server_default="open"))
    op.add_column("incident_records", sa.Column("authority_notification_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))

    op.create_table(
        "reports",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("report_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="completed"),
        sa.Column("report_json", sa.JSON(), nullable=False),
        sa.Column("source_refs_json", sa.JSON(), nullable=False),
        sa.Column("artifact_metadata", sa.JSON(), nullable=False),
        sa.Column("legal_basis_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("generation_manifest_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("ai_system_id", sa.String(), nullable=True),
        sa.Column("feature_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
        sa.ForeignKeyConstraint(["ai_system_id"], ["ai_systems.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reports_id"), "reports", ["id"], unique=False)
    op.create_index(op.f("ix_reports_tenant_id"), "reports", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_reports_ai_system_id"), "reports", ["ai_system_id"], unique=False)
    op.create_index(op.f("ix_reports_feature_id"), "reports", ["feature_id"], unique=False)

    op.create_table(
        "compliance_controls",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("ai_system_id", sa.String(), nullable=True),
        sa.Column("control_key", sa.String(), nullable=False),
        sa.Column("article", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("owner_email", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="not_started"),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence_domain", sa.String(), nullable=False),
        sa.Column("details_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
        sa.ForeignKeyConstraint(["ai_system_id"], ["ai_systems.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "ai_system_id", "control_key", name="uq_control_system_key"),
    )
    op.create_index(op.f("ix_compliance_controls_id"), "compliance_controls", ["id"], unique=False)
    op.create_index(op.f("ix_compliance_controls_tenant_id"), "compliance_controls", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_compliance_controls_ai_system_id"), "compliance_controls", ["ai_system_id"], unique=False)
    op.create_index(op.f("ix_compliance_controls_control_key"), "compliance_controls", ["control_key"], unique=False)
    op.create_index(op.f("ix_compliance_controls_article"), "compliance_controls", ["article"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_compliance_controls_article"), table_name="compliance_controls")
    op.drop_index(op.f("ix_compliance_controls_control_key"), table_name="compliance_controls")
    op.drop_index(op.f("ix_compliance_controls_ai_system_id"), table_name="compliance_controls")
    op.drop_index(op.f("ix_compliance_controls_tenant_id"), table_name="compliance_controls")
    op.drop_index(op.f("ix_compliance_controls_id"), table_name="compliance_controls")
    op.drop_table("compliance_controls")

    op.drop_index(op.f("ix_reports_feature_id"), table_name="reports")
    op.drop_index(op.f("ix_reports_ai_system_id"), table_name="reports")
    op.drop_index(op.f("ix_reports_tenant_id"), table_name="reports")
    op.drop_index(op.f("ix_reports_id"), table_name="reports")
    op.drop_table("reports")

    op.drop_column("incident_records", "authority_notification_json")
    op.drop_column("incident_records", "escalation_status")
    op.drop_column("incident_records", "reported_at")
    op.drop_column("incident_records", "deadline_at")
    op.drop_column("incident_records", "incident_type")

    op.drop_column("oversight_assignments", "competence_json")

    op.drop_column("fria_records", "signoff_json")
    op.drop_column("fria_records", "dpia_link_json")
    op.drop_column("fria_records", "legal_basis_json")

    op.drop_column("intake_assessments", "evidence_requirements_json")
    op.drop_column("intake_assessments", "legal_basis_json")
    op.drop_column("intake_assessments", "obligation_graph_json")
