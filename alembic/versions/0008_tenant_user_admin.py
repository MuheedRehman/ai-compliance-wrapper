"""tenant user administration

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-14 00:00:00.000000

"""
from typing import Optional, Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0008"
down_revision: Optional[str] = "0007"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    op.create_table(
        "tenant_auth_policies",
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("google_login_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("password_login_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("allowed_domains_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("allowed_emails_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("auto_provision_google_users", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("default_role", sa.String(), nullable=False, server_default="viewer"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
        sa.PrimaryKeyConstraint("tenant_id"),
    )

    op.create_table(
        "tenant_users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("role", sa.String(), nullable=False, server_default="viewer"),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("auth_provider", sa.String(), nullable=False, server_default="google"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "email", name="uq_tenant_user_email"),
    )
    op.create_index(op.f("ix_tenant_users_id"), "tenant_users", ["id"], unique=False)
    op.create_index(op.f("ix_tenant_users_tenant_id"), "tenant_users", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_tenant_users_email"), "tenant_users", ["email"], unique=False)
    op.create_index(op.f("ix_tenant_users_status"), "tenant_users", ["status"], unique=False)

    op.create_table(
        "tenant_invitations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="viewer"),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("invited_by_email", sa.String(), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tenant_invitations_id"), "tenant_invitations", ["id"], unique=False)
    op.create_index(op.f("ix_tenant_invitations_tenant_id"), "tenant_invitations", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_tenant_invitations_email"), "tenant_invitations", ["email"], unique=False)
    op.create_index(op.f("ix_tenant_invitations_status"), "tenant_invitations", ["status"], unique=False)
    op.create_index(
        "ix_tenant_invitation_lookup",
        "tenant_invitations",
        ["tenant_id", "email", "status"],
        unique=False,
    )

    op.create_table(
        "tenant_login_audit",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("outcome", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tenant_login_audit_id"), "tenant_login_audit", ["id"], unique=False)
    op.create_index(op.f("ix_tenant_login_audit_tenant_id"), "tenant_login_audit", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_tenant_login_audit_email"), "tenant_login_audit", ["email"], unique=False)
    op.create_index(op.f("ix_tenant_login_audit_outcome"), "tenant_login_audit", ["outcome"], unique=False)
    op.create_index(op.f("ix_tenant_login_audit_created_at"), "tenant_login_audit", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_tenant_login_audit_created_at"), table_name="tenant_login_audit")
    op.drop_index(op.f("ix_tenant_login_audit_outcome"), table_name="tenant_login_audit")
    op.drop_index(op.f("ix_tenant_login_audit_email"), table_name="tenant_login_audit")
    op.drop_index(op.f("ix_tenant_login_audit_tenant_id"), table_name="tenant_login_audit")
    op.drop_index(op.f("ix_tenant_login_audit_id"), table_name="tenant_login_audit")
    op.drop_table("tenant_login_audit")

    op.drop_index("ix_tenant_invitation_lookup", table_name="tenant_invitations")
    op.drop_index(op.f("ix_tenant_invitations_status"), table_name="tenant_invitations")
    op.drop_index(op.f("ix_tenant_invitations_email"), table_name="tenant_invitations")
    op.drop_index(op.f("ix_tenant_invitations_tenant_id"), table_name="tenant_invitations")
    op.drop_index(op.f("ix_tenant_invitations_id"), table_name="tenant_invitations")
    op.drop_table("tenant_invitations")

    op.drop_index(op.f("ix_tenant_users_status"), table_name="tenant_users")
    op.drop_index(op.f("ix_tenant_users_email"), table_name="tenant_users")
    op.drop_index(op.f("ix_tenant_users_tenant_id"), table_name="tenant_users")
    op.drop_index(op.f("ix_tenant_users_id"), table_name="tenant_users")
    op.drop_table("tenant_users")

    op.drop_table("tenant_auth_policies")
