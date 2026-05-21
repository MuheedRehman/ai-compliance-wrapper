from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base


class Tenant(Base):
    __tablename__ = "tenants"

    tenant_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ApiKey(Base):
    __tablename__ = "api_keys"

    key_id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    key_hash = Column(String, nullable=False, unique=True, index=True)
    role = Column(String, nullable=False, default="app")
    scopes = Column(JSON, nullable=False, default=list)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)


class TenantAuthPolicy(Base):
    __tablename__ = "tenant_auth_policies"

    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), primary_key=True)
    google_login_enabled = Column(Boolean, nullable=False, default=True)
    password_login_enabled = Column(Boolean, nullable=False, default=True)
    allowed_domains_json = Column(JSON, nullable=False, default=list)
    allowed_emails_json = Column(JSON, nullable=False, default=list)
    auto_provision_google_users = Column(Boolean, nullable=False, default=True)
    default_role = Column(String, nullable=False, default="viewer")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TenantUser(Base):
    __tablename__ = "tenant_users"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    email = Column(String, nullable=False, index=True)
    name = Column(String, nullable=True)
    role = Column(String, nullable=False, default="viewer")
    status = Column(String, nullable=False, default="active", index=True)
    auth_provider = Column(String, nullable=False, default="google")
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_tenant_user_email"),
    )


class TenantInvitation(Base):
    __tablename__ = "tenant_invitations"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    email = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False, default="viewer")
    status = Column(String, nullable=False, default="pending", index=True)
    invited_by_email = Column(String, nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_tenant_invitation_lookup", "tenant_id", "email", "status"),
    )


class TenantLoginAudit(Base):
    __tablename__ = "tenant_login_audit"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=True, index=True)
    email = Column(String, nullable=True, index=True)
    provider = Column(String, nullable=False)
    outcome = Column(String, nullable=False, index=True)
    reason = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class TenantActionAudit(Base):
    __tablename__ = "tenant_action_audit"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    actor_user_id = Column(String, nullable=True, index=True)
    actor_email = Column(String, nullable=True, index=True)
    actor_role = Column(String, nullable=True)
    action = Column(String, nullable=False, index=True)
    target_type = Column(String, nullable=False, index=True)
    target_id = Column(String, nullable=True, index=True)
    target_email = Column(String, nullable=True, index=True)
    before_json = Column(JSON, nullable=True)
    after_json = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class AiSystem(Base):
    __tablename__ = "ai_systems"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    deployment_status = Column(String, nullable=False, server_default="draft", default="draft")
    registration_status = Column(String, nullable=False, server_default="draft", default="draft")
    owner_email = Column(String, nullable=True, index=True)
    technical_owner_email = Column(String, nullable=True)
    legal_owner_email = Column(String, nullable=True)
    review_status = Column(String, nullable=False, server_default="not_started", default="not_started")
    next_review_at = Column(DateTime(timezone=True), nullable=True, index=True)
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    lifecycle_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AiSystemReviewEvent(Base):
    __tablename__ = "ai_system_review_events"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    ai_system_id = Column(String, ForeignKey("ai_systems.id"), nullable=False, index=True)
    reviewer_email = Column(String, nullable=True, index=True)
    review_type = Column(String, nullable=False, default="lifecycle_review", index=True)
    status = Column(String, nullable=False, default="completed", index=True)
    notes = Column(Text, nullable=True)
    findings_json = Column(JSON, nullable=False, default=list)
    actions_json = Column(JSON, nullable=False, default=list)
    next_review_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class AiFeature(Base):
    __tablename__ = "ai_features"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    ai_system_id = Column(String, ForeignKey("ai_systems.id"), nullable=True, index=True)
    feature_id = Column(String, nullable=False, index=True)

    name = Column(String, nullable=False)
    slug = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    owner_email = Column(String, nullable=True)
    team = Column(String, nullable=True)
    use_case = Column(String, nullable=True)
    decision_impact = Column(String, nullable=True)
    affected_user_groups = Column(JSON, nullable=False, default=list)

    risk_level_current = Column(String, nullable=False, default="unknown")
    compliance_status = Column(String, nullable=False, default="draft")
    fria_likely_required = Column(Boolean, default=False)

    approved_providers = Column(JSON, nullable=False, default=list)
    approved_models = Column(JSON, nullable=False, default=list)

    current_feature_version_id = Column(
        String,
        ForeignKey(
            "feature_versions.feature_version_id",
            name="fk_ai_features_current_feature_version_id",
            use_alter=True,
        ),
        nullable=True,
    )
    current_prompt_hash = Column(String, nullable=True)
    current_fingerprint = Column(String, nullable=True)
    policy_bundle_version = Column(String, nullable=False, default="default_v1")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("tenant_id", "feature_id", name="uq_tenant_feature_id"),
    )


class FeatureVersion(Base):
    __tablename__ = "feature_versions"

    feature_version_id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    feature_pk = Column(String, ForeignKey("ai_features.id"), nullable=False, index=True)
    feature_id = Column(String, nullable=False, index=True)

    version = Column(Integer, nullable=False)
    provider = Column(String, nullable=False)
    model = Column(String, nullable=False)
    prompt_hash = Column(String, nullable=False)
    fingerprint = Column(String, nullable=False, index=True)
    policy_bundle_version = Column(String, nullable=False)
    change_reason = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="candidate")  # candidate/approved/superseded/rejected

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    superseded_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "feature_pk", "version", name="uq_feature_version_number"),
        UniqueConstraint("tenant_id", "feature_pk", "fingerprint", name="uq_feature_version_fingerprint"),
    )


class EvidenceLog(Base):
    __tablename__ = "evidence_logs"

    event_id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    ai_system_id = Column(String, ForeignKey("ai_systems.id"), nullable=True, index=True)
    feature_pk = Column(String, ForeignKey("ai_features.id"), nullable=True, index=True)
    feature_id = Column(String, nullable=True, index=True)
    feature_version_id = Column(String, ForeignKey("feature_versions.feature_version_id"), nullable=True, index=True)
    policy_bundle_version = Column(String, nullable=True, index=True)
    evidence_domain = Column(String, nullable=True, index=True)

    request_id = Column(String, nullable=False, index=True)
    trace_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)

    provider = Column(String, nullable=True)
    model = Column(String, nullable=True)
    provider_response_id = Column(String, nullable=True)
    finish_reason = Column(String, nullable=True)

    decision = Column(String, nullable=False)
    status = Column(String, nullable=False)

    risk_level = Column(String, nullable=False)
    risk_score = Column(Integer, nullable=False)
    triggered_rule_results = Column(JSON, nullable=False, default=list)

    request_hash = Column(String, nullable=True)
    prompt_hash = Column(String, nullable=True)
    response_hash = Column(String, nullable=True)

    previous_event_hash = Column(String, nullable=True)
    event_hash = Column(String, nullable=False)
    hmac_signature = Column(String, nullable=False)

    latency_ms = Column(Integer, nullable=True)
    token_counts = Column(JSON, nullable=False, default=dict)
    metadata_warnings = Column(JSON, nullable=False, default=list)
    policy_context = Column(JSON, nullable=False, default=dict)
    request_metadata = Column("metadata", JSON, nullable=False, default=dict)

    redacted_input_text = Column(Text, nullable=True)
    redacted_output_text = Column(Text, nullable=True)
    evidence_json = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class ReviewTask(Base):
    __tablename__ = "review_tasks"

    review_task_id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    ai_system_id = Column(String, ForeignKey("ai_systems.id"), nullable=True, index=True)
    feature_pk = Column(String, ForeignKey("ai_features.id"), nullable=True, index=True)
    feature_id = Column(String, nullable=True, index=True)
    feature_version_id = Column(String, ForeignKey("feature_versions.feature_version_id"), nullable=True, index=True)

    review_type = Column(String, nullable=False)
    trigger_reason = Column(String, nullable=False)
    severity = Column(String, nullable=False, default="medium")
    status = Column(String, nullable=False, default="open")
    occurrence_count = Column(Integer, nullable=False, default=1)
    findings_json = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        # Backup constraint only. Code-level dedupe is the primary guarantee because NULL semantics differ by DB.
        Index("ix_review_dedupe_lookup", "tenant_id", "feature_id", "feature_version_id", "review_type", "trigger_reason", "status"),
    )


class FRIARecord(Base):
    __tablename__ = "fria_records"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    ai_system_id = Column(String, ForeignKey("ai_systems.id"), nullable=False, index=True)
    
    status = Column(String, nullable=False, default="draft")
    assessment_json = Column(JSON, nullable=False, default=dict)
    legal_basis_json = Column(JSON, nullable=False, default=list)
    dpia_link_json = Column(JSON, nullable=False, default=dict)
    signoff_json = Column(JSON, nullable=False, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OversightAssignment(Base):
    __tablename__ = "oversight_assignments"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    ai_system_id = Column(String, ForeignKey("ai_systems.id"), nullable=False, index=True)
    
    reviewer_email = Column(String, nullable=False)
    role = Column(String, nullable=False)
    competence_json = Column(JSON, nullable=False, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class IncidentRecord(Base):
    __tablename__ = "incident_records"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    ai_system_id = Column(String, ForeignKey("ai_systems.id"), nullable=False, index=True)
    
    severity = Column(String, nullable=False)
    incident_type = Column(String, nullable=False, default="standard")
    description = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="open")
    deadline_at = Column(DateTime(timezone=True), nullable=True)
    reported_at = Column(DateTime(timezone=True), nullable=True)
    escalation_status = Column(String, nullable=False, default="open")
    authority_notification_json = Column(JSON, nullable=False, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class EvidenceBundle(Base):
    __tablename__ = "evidence_bundles"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    ai_system_id = Column(String, ForeignKey("ai_systems.id"), nullable=True, index=True)
    
    bundle_hash = Column(String, nullable=False)
    bundle_url = Column(String, nullable=True)  # Link to Cloud Storage
    status = Column(String, nullable=False, default="pending")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    ai_system_id = Column(String, ForeignKey("ai_systems.id"), nullable=True, index=True)
    control_id = Column(String, ForeignKey("compliance_controls.id"), nullable=True, index=True)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    evidence_type = Column(String, nullable=False, default="policy", index=True)
    source = Column(String, nullable=False)
    source_url = Column(String, nullable=True)
    owner_email = Column(String, nullable=True, index=True)
    status = Column(String, nullable=False, default="active", index=True)

    collected_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    review_at = Column(DateTime(timezone=True), nullable=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)

    evidence_hash = Column(String, nullable=False)
    hmac_signature = Column(String, nullable=False)
    metadata_json = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    artifacts = relationship(
        "EvidenceArtifact",
        back_populates="evidence_item",
        cascade="all, delete-orphan",
    )


class EvidenceArtifact(Base):
    __tablename__ = "evidence_artifacts"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    evidence_item_id = Column(String, ForeignKey("evidence_items.id"), nullable=False, index=True)

    file_name = Column(String, nullable=False)
    content_type = Column(String, nullable=False, default="application/octet-stream")
    size_bytes = Column(Integer, nullable=False)
    artifact_hash = Column(String, nullable=False, index=True)
    hmac_signature = Column(String, nullable=False)
    storage_backend = Column(String, nullable=False, default="database", index=True)
    storage_key = Column(String, nullable=False)
    content_bytes = Column(LargeBinary, nullable=False)
    metadata_json = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    evidence_item = relationship("EvidenceItem", back_populates="artifacts")


class TenantSubscription(Base):
    __tablename__ = "tenant_subscriptions"
    
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), primary_key=True)
    stripe_customer_id = Column(String, nullable=True, index=True)
    stripe_subscription_id = Column(String, nullable=True, index=True)
    plan_id = Column(String, nullable=False, default="free")
    status = Column(String, nullable=False, default="active")
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Entitlement(Base):
    __tablename__ = "entitlements"
    
    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    feature_key = Column(String, nullable=False)
    is_enabled = Column(Boolean, default=False)
    limit_value = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UsageMeter(Base):
    __tablename__ = "usage_meters"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    event_type = Column(String, nullable=False)
    count = Column(Integer, nullable=False, default=1)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class IntakeAssessment(Base):
    __tablename__ = "intake_assessments"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    
    title = Column(String, nullable=False)
    answers_json = Column(JSON, nullable=False, default=dict)
    
    actor_role = Column(String, nullable=False)
    system_classification = Column(String, nullable=False)
    obligation_path = Column(String, nullable=False)
    obligation_graph_json = Column(JSON, nullable=False, default=list)
    legal_basis_json = Column(JSON, nullable=False, default=list)
    evidence_requirements_json = Column(JSON, nullable=False, default=list)
    rationale = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ReportRecord(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    
    report_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    status = Column(String, nullable=False, default="completed")
    
    report_json = Column(JSON, nullable=False, default=dict)
    source_refs_json = Column(JSON, nullable=False, default=list)
    artifact_metadata = Column(JSON, nullable=False, default=dict)
    legal_basis_json = Column(JSON, nullable=False, default=list)
    generation_manifest_json = Column(JSON, nullable=False, default=dict)
    
    ai_system_id = Column(String, ForeignKey("ai_systems.id"), nullable=True, index=True)
    feature_id = Column(String, nullable=True, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ComplianceControl(Base):
    __tablename__ = "compliance_controls"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    ai_system_id = Column(String, ForeignKey("ai_systems.id"), nullable=True, index=True)

    control_key = Column(String, nullable=False, index=True)
    article = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    owner_email = Column(String, nullable=True)
    status = Column(String, nullable=False, default="not_started")
    due_at = Column(DateTime(timezone=True), nullable=True)
    evidence_domain = Column(String, nullable=False)
    details_json = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("tenant_id", "ai_system_id", "control_key", name="uq_control_system_key"),
    )


class WebsiteScan(Base):
    __tablename__ = "website_scans"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)

    url = Column(String, nullable=False)
    normalized_url = Column(String, nullable=False)
    status = Column(String, nullable=False, default="completed", index=True)
    title = Column(String, nullable=True)
    summary = Column(Text, nullable=True)

    detected_signals_json = Column(JSON, nullable=False, default=list)
    evidence_refs_json = Column(JSON, nullable=False, default=list)
    gap_findings_json = Column(JSON, nullable=False, default=list)
    classification_json = Column(JSON, nullable=False, default=dict)
    suggested_actions_json = Column(JSON, nullable=False, default=list)
    source_pages_json = Column(JSON, nullable=False, default=list)
    confidence_score = Column(Integer, nullable=False, default=0)

    ai_system_id = Column(String, ForeignKey("ai_systems.id"), nullable=True, index=True)
    intake_id = Column(String, ForeignKey("intake_assessments.id"), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
