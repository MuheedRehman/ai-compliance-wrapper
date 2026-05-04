from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Index,
)
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


class AiSystem(Base):
    __tablename__ = "ai_systems"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    deployment_status = Column(String, nullable=False, server_default="draft", default="draft")
    registration_status = Column(String, nullable=False, server_default="draft", default="draft")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


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

    current_feature_version_id = Column(String, ForeignKey("feature_versions.feature_version_id"), nullable=True)
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
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OversightAssignment(Base):
    __tablename__ = "oversight_assignments"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    ai_system_id = Column(String, ForeignKey("ai_systems.id"), nullable=False, index=True)
    
    reviewer_email = Column(String, nullable=False)
    role = Column(String, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class IncidentRecord(Base):
    __tablename__ = "incident_records"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    ai_system_id = Column(String, ForeignKey("ai_systems.id"), nullable=False, index=True)
    
    severity = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="open")
    
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
