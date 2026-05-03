"""initial governance schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-03
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("tenant_id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "api_keys",
        sa.Column("key_id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.tenant_id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("key_hash", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="app"),
        sa.Column("scopes", sa.JSON(), nullable=False),
        sa.Column("revoked", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"], unique=True)
    op.create_index("ix_api_keys_tenant_id", "api_keys", ["tenant_id"])

    op.create_table(
        "ai_features",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.tenant_id"), nullable=False),
        sa.Column("feature_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_email", sa.String(), nullable=True),
        sa.Column("team", sa.String(), nullable=True),
        sa.Column("use_case", sa.String(), nullable=True),
        sa.Column("decision_impact", sa.String(), nullable=True),
        sa.Column("affected_user_groups", sa.JSON(), nullable=False),
        sa.Column("risk_level_current", sa.String(), nullable=False, server_default="unknown"),
        sa.Column("compliance_status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("fria_likely_required", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("approved_providers", sa.JSON(), nullable=False),
        sa.Column("approved_models", sa.JSON(), nullable=False),
        sa.Column("current_feature_version_id", sa.String(), nullable=True),
        sa.Column("current_prompt_hash", sa.String(), nullable=True),
        sa.Column("current_fingerprint", sa.String(), nullable=True),
        sa.Column("policy_bundle_version", sa.String(), nullable=False, server_default="default_v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "feature_id", name="uq_tenant_feature_id"),
    )
    op.create_index("ix_ai_features_tenant_id", "ai_features", ["tenant_id"])
    op.create_index("ix_ai_features_feature_id", "ai_features", ["feature_id"])

    op.create_table(
        "feature_versions",
        sa.Column("feature_version_id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.tenant_id"), nullable=False),
        sa.Column("feature_pk", sa.String(), sa.ForeignKey("ai_features.id"), nullable=False),
        sa.Column("feature_id", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("prompt_hash", sa.String(), nullable=False),
        sa.Column("fingerprint", sa.String(), nullable=False),
        sa.Column("policy_bundle_version", sa.String(), nullable=False),
        sa.Column("change_reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="candidate"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "feature_pk", "version", name="uq_feature_version_number"),
        sa.UniqueConstraint("tenant_id", "feature_pk", "fingerprint", name="uq_feature_version_fingerprint"),
    )
    op.create_index("ix_feature_versions_tenant_id", "feature_versions", ["tenant_id"])
    op.create_index("ix_feature_versions_feature_pk", "feature_versions", ["feature_pk"])
    op.create_index("ix_feature_versions_feature_id", "feature_versions", ["feature_id"])
    op.create_index("ix_feature_versions_fingerprint", "feature_versions", ["fingerprint"])

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.create_foreign_key(
            "fk_ai_features_current_feature_version_id",
            "ai_features",
            "feature_versions",
            ["current_feature_version_id"],
            ["feature_version_id"],
        )

    op.create_table(
        "evidence_logs",
        sa.Column("event_id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.tenant_id"), nullable=False),
        sa.Column("feature_pk", sa.String(), sa.ForeignKey("ai_features.id"), nullable=True),
        sa.Column("feature_id", sa.String(), nullable=True),
        sa.Column("feature_version_id", sa.String(), sa.ForeignKey("feature_versions.feature_version_id"), nullable=True),
        sa.Column("policy_bundle_version", sa.String(), nullable=True),
        sa.Column("request_id", sa.String(), nullable=False),
        sa.Column("trace_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("provider_response_id", sa.String(), nullable=True),
        sa.Column("finish_reason", sa.String(), nullable=True),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("risk_level", sa.String(), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("triggered_rule_results", sa.JSON(), nullable=False),
        sa.Column("request_hash", sa.String(), nullable=True),
        sa.Column("prompt_hash", sa.String(), nullable=True),
        sa.Column("response_hash", sa.String(), nullable=True),
        sa.Column("previous_event_hash", sa.String(), nullable=True),
        sa.Column("event_hash", sa.String(), nullable=False),
        sa.Column("hmac_signature", sa.String(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("token_counts", sa.JSON(), nullable=False),
        sa.Column("metadata_warnings", sa.JSON(), nullable=False),
        sa.Column("policy_context", sa.JSON(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("redacted_input_text", sa.Text(), nullable=True),
        sa.Column("redacted_output_text", sa.Text(), nullable=True),
        sa.Column("evidence_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    for col in ["tenant_id", "feature_pk", "feature_id", "feature_version_id", "request_id", "trace_id", "created_at"]:
        op.create_index(f"ix_evidence_logs_{col}", "evidence_logs", [col])

    op.create_table(
        "review_tasks",
        sa.Column("review_task_id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.tenant_id"), nullable=False),
        sa.Column("feature_pk", sa.String(), sa.ForeignKey("ai_features.id"), nullable=True),
        sa.Column("feature_id", sa.String(), nullable=True),
        sa.Column("feature_version_id", sa.String(), sa.ForeignKey("feature_versions.feature_version_id"), nullable=True),
        sa.Column("review_type", sa.String(), nullable=False),
        sa.Column("trigger_reason", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(), nullable=False, server_default="open"),
        sa.Column("occurrence_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("findings_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_review_tasks_tenant_id", "review_tasks", ["tenant_id"])
    op.create_index("ix_review_tasks_feature_pk", "review_tasks", ["feature_pk"])
    op.create_index("ix_review_tasks_feature_id", "review_tasks", ["feature_id"])
    op.create_index("ix_review_tasks_feature_version_id", "review_tasks", ["feature_version_id"])
    op.create_index(
        "ix_review_dedupe_lookup",
        "review_tasks",
        ["tenant_id", "feature_id", "feature_version_id", "review_type", "trigger_reason", "status"],
    )


def downgrade() -> None:
    op.drop_table("review_tasks")
    op.drop_table("evidence_logs")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.drop_constraint("fk_ai_features_current_feature_version_id", "ai_features", type_="foreignkey")

    op.drop_table("feature_versions")
    op.drop_table("ai_features")
    op.drop_table("api_keys")
    op.drop_table("tenants")
