import ipaddress
import re
from urllib.parse import urlparse

from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Any, Dict, List, Optional, Literal

# Private/reserved address ranges that must never be fetched via the scanner
_SSRF_BLOCKED = re.compile(
    r"^(localhost|.*\.local)$"
    r"|^(127\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|169\.254\.)",
    re.IGNORECASE,
)


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: Optional[str] = None
    max_tokens: int = Field(default=300, ge=1, le=1000)
    messages: List[Message]
    feature_id: Optional[str] = None
    policy_context: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FeatureCreate(BaseModel):
    feature_id: str
    name: str
    description: Optional[str] = None
    owner_email: Optional[str] = None
    team: Optional[str] = None
    use_case: Optional[str] = None
    decision_impact: Optional[str] = None
    affected_user_groups: List[str] = Field(default_factory=list)
    risk_level_current: str = "unknown"
    compliance_status: str = "draft"
    fria_likely_required: bool = False
    approved_providers: List[str] = Field(default_factory=lambda: ["openai"])
    approved_models: List[str] = Field(default_factory=list)
    ai_system_id: Optional[str] = None


class FeatureUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    owner_email: Optional[str] = None
    team: Optional[str] = None
    use_case: Optional[str] = None
    decision_impact: Optional[str] = None
    affected_user_groups: Optional[List[str]] = None
    risk_level_current: Optional[str] = None
    compliance_status: Optional[str] = None
    fria_likely_required: Optional[bool] = None
    approved_providers: Optional[List[str]] = None
    approved_models: Optional[List[str]] = None
    ai_system_id: Optional[str] = None


class ReviewClose(BaseModel):
    resolution_note: Optional[str] = None


class VersionDecision(BaseModel):
    note: Optional[str] = None


class AiSystemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    owner_email: Optional[str] = None
    technical_owner_email: Optional[str] = None
    legal_owner_email: Optional[str] = None
    review_status: Literal["not_started", "scheduled", "in_review", "completed", "overdue"] = "not_started"
    next_review_at: Optional[datetime] = None
    lifecycle_notes: Optional[str] = None


class AiSystemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    deployment_status: Optional[Literal["draft", "deployed", "retired"]] = None
    registration_status: Optional[Literal["draft", "registered", "rejected"]] = None
    owner_email: Optional[str] = None
    technical_owner_email: Optional[str] = None
    legal_owner_email: Optional[str] = None
    review_status: Optional[Literal["not_started", "scheduled", "in_review", "completed", "overdue"]] = None
    next_review_at: Optional[datetime] = None
    last_reviewed_at: Optional[datetime] = None
    lifecycle_notes: Optional[str] = None


class AiSystemReviewCreate(BaseModel):
    reviewer_email: Optional[str] = None
    review_type: Literal["lifecycle_review", "classification_review", "control_review", "evidence_review", "incident_review"] = "lifecycle_review"
    status: Literal["scheduled", "in_review", "completed", "needs_follow_up"] = "completed"
    notes: Optional[str] = None
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    next_review_at: Optional[datetime] = None


class AiSystemResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: Optional[str] = None
    deployment_status: str
    registration_status: str
    owner_email: Optional[str] = None
    technical_owner_email: Optional[str] = None
    legal_owner_email: Optional[str] = None
    review_status: str
    next_review_at: Optional[datetime] = None
    last_reviewed_at: Optional[datetime] = None
    lifecycle_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AiSystemReviewResponse(BaseModel):
    id: str
    tenant_id: str
    ai_system_id: str
    reviewer_email: Optional[str] = None
    review_type: str
    status: str
    notes: Optional[str] = None
    findings_json: List[Dict[str, Any]] = Field(default_factory=list)
    actions_json: List[Dict[str, Any]] = Field(default_factory=list)
    next_review_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AiSystemWorkspaceResponse(BaseModel):
    system: AiSystemResponse
    metrics: Dict[str, Any]
    governance_summary: Dict[str, Any] = Field(default_factory=dict)
    drill_down_actions: Dict[str, Any] = Field(default_factory=dict)
    readiness_scorecard: Dict[str, Any]
    latest_classification: Optional[Dict[str, Any]] = None
    features: List[Dict[str, Any]] = Field(default_factory=list)
    controls: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_items: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_logs: List[Dict[str, Any]] = Field(default_factory=list)
    website_scans: List[Dict[str, Any]] = Field(default_factory=list)
    intakes: List[Dict[str, Any]] = Field(default_factory=list)
    fria_records: List[Dict[str, Any]] = Field(default_factory=list)
    oversight_assignments: List[Dict[str, Any]] = Field(default_factory=list)
    incidents: List[Dict[str, Any]] = Field(default_factory=list)
    reports: List[Dict[str, Any]] = Field(default_factory=list)
    review_events: List[Dict[str, Any]] = Field(default_factory=list)
    follow_up_tasks: List[Dict[str, Any]] = Field(default_factory=list)


class SubscriptionStatusResponse(BaseModel):
    tenant_id: str
    plan_id: str
    status: str
    current_period_end: Optional[datetime] = None


class CheckoutSessionRequest(BaseModel):
    plan_id: str


class CheckoutSessionResponse(BaseModel):
    checkout_url: str


class PortalSessionResponse(BaseModel):
    portal_url: str


class EntitlementResponse(BaseModel):
    feature_key: str
    is_enabled: bool
    limit_value: Optional[int] = None


class IntakeCreate(BaseModel):
    title: str
    answers: Dict[str, Any]



class IntakeResponse(BaseModel):
    id: str
    tenant_id: str
    title: str
    answers_json: Dict[str, Any]
    actor_role: str
    system_classification: str
    obligation_path: str
    obligation_graph_json: List[Dict[str, Any]] = Field(default_factory=list)
    legal_basis_json: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_requirements_json: List[Dict[str, Any]] = Field(default_factory=list)
    rationale: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComplianceDimensionResponse(BaseModel):
    dimension_id: str
    pillar: str
    chapter: str
    articles: List[Dict[str, Any]]
    article: str
    annex_refs: List[str] = Field(default_factory=list)
    actor_roles: List[str] = Field(default_factory=list)
    risk_tiers: List[str] = Field(default_factory=list)
    trigger_conditions: List[str] = Field(default_factory=list)
    required_controls: List[Dict[str, Any]] = Field(default_factory=list)
    required_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    scanner_signals: List[str] = Field(default_factory=list)
    effective_dates: Dict[str, str] = Field(default_factory=dict)
    confidence_policy: str
    status: str
    evidence_domain: str
    summary: str
    penalty_exposure: Dict[str, Any] = Field(default_factory=dict)


class AnnexIIICategoryResponse(BaseModel):
    category_id: str
    area_number: int
    area: str
    subcategory_id: str
    subcategory: str
    annex_ref: str
    article: str
    source: str
    source_url: str
    summary: str
    scanner_terms: List[str] = Field(default_factory=list)


class PenaltyExposureResponse(BaseModel):
    band_id: str
    title: str
    enforcement_article: str
    max_eur: Optional[int] = None
    turnover_percent: Optional[float] = None
    comparison_rule: str
    maximum_text: str
    applies_to: List[str] = Field(default_factory=list)
    source: str
    source_url: str
    sme_rule: Optional[str] = None
    notes: str


class ObligationExplanationResponse(BaseModel):
    actor_role: str
    system_classification: str
    obligation_path: str
    applicable_dimensions: List[Dict[str, Any]] = Field(default_factory=list)
    legal_basis: List[Dict[str, Any]] = Field(default_factory=list)
    controls_to_create: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    explanations: List[str] = Field(default_factory=list)
    manual_review_required: bool = False


# --- Phase 4: Obligation Workflows ---

# FRIA
class FRIACreate(BaseModel):
    ai_system_id: str
    assessment_json: Dict[str, Any] = Field(default_factory=dict)
    dpia_link_json: Dict[str, Any] = Field(default_factory=dict)
    signoff_json: Dict[str, Any] = Field(default_factory=dict)
    status: str = "draft"

class FRIAUpdate(BaseModel):
    assessment_json: Optional[Dict[str, Any]] = None
    dpia_link_json: Optional[Dict[str, Any]] = None
    signoff_json: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class FRIASectionsUpdate(BaseModel):
    """Update one or more FRIA builder sections. Omit a key to leave that section unchanged."""
    intended_purpose: Optional[Dict[str, Any]] = None
    affected_persons: Optional[Dict[str, Any]] = None
    fundamental_rights_risks: Optional[Dict[str, Any]] = None
    mitigation_measures: Optional[Dict[str, Any]] = None
    human_oversight: Optional[Dict[str, Any]] = None
    residual_risk: Optional[Dict[str, Any]] = None

class FRIASubmitRequest(BaseModel):
    submitted_by: str  # email of the submitter

class FRIAReviewRequest(BaseModel):
    reviewer_email: str
    outcome: str  # "approved" | "rejected"
    notes: Optional[str] = None

class FRIAResponse(BaseModel):
    id: str
    tenant_id: str
    ai_system_id: str
    ai_system_name: Optional[str] = None
    status: str
    assessment_json: Dict[str, Any]
    legal_basis_json: List[Dict[str, Any]] = Field(default_factory=list)
    dpia_link_json: Dict[str, Any] = Field(default_factory=dict)
    signoff_json: Dict[str, Any] = Field(default_factory=dict)
    sections_json: Dict[str, Any] = Field(default_factory=dict)
    approval_json: Dict[str, Any] = Field(default_factory=dict)
    completion_percent: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Oversight
class OversightCreate(BaseModel):
    ai_system_id: str
    reviewer_email: str
    role: str
    competence_json: Dict[str, Any] = Field(default_factory=dict)

class OversightUpdate(BaseModel):
    reviewer_email: Optional[str] = None
    role: Optional[str] = None
    competence_json: Optional[Dict[str, Any]] = None

class OversightResponse(BaseModel):
    id: str
    tenant_id: str
    ai_system_id: str
    reviewer_email: str
    role: str
    competence_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Incidents
class IncidentCreate(BaseModel):
    ai_system_id: str
    severity: str
    description: str
    incident_type: Literal["standard", "widespread_infringement", "death"] = "standard"
    authority_notification_json: Dict[str, Any] = Field(default_factory=dict)
    status: str = "open"

class IncidentUpdate(BaseModel):
    severity: Optional[str] = None
    incident_type: Optional[Literal["standard", "widespread_infringement", "death"]] = None
    description: Optional[str] = None
    status: Optional[str] = None
    reported_at: Optional[datetime] = None
    escalation_status: Optional[str] = None
    authority_notification_json: Optional[Dict[str, Any]] = None

class IncidentResponse(BaseModel):
    id: str
    tenant_id: str
    ai_system_id: str
    severity: str
    incident_type: str
    description: str
    status: str
    deadline_at: Optional[datetime] = None
    reported_at: Optional[datetime] = None
    escalation_status: str
    authority_notification_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Phase 4.5: Assessment & Report Engine ---

class ReportCreate(BaseModel):
    report_type: Literal["assessment_summary", "test_session_summary", "compliance_readiness_summary", "incident_summary", "ai_system_factsheet"]
    title: Optional[str] = None
    ai_system_id: Optional[str] = None
    feature_id: Optional[str] = None
    source_refs: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

class ReportResponse(BaseModel):
    id: str
    tenant_id: str
    report_type: str
    title: str
    status: str
    report_json: Dict[str, Any]
    source_refs_json: List[Dict[str, Any]]
    artifact_metadata: Dict[str, Any]
    legal_basis_json: List[Dict[str, Any]] = Field(default_factory=list)
    generation_manifest_json: Dict[str, Any] = Field(default_factory=dict)
    ai_system_id: Optional[str] = None
    feature_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Compliance Control Register ---

ControlSeverity = Literal["low", "medium", "high", "critical"]


class ComplianceControlCreate(BaseModel):
    control_key: str
    article: str
    title: str
    ai_system_id: Optional[str] = None
    owner_email: Optional[str] = None
    status: str = "not_started"
    due_at: Optional[datetime] = None
    evidence_domain: str
    severity: ControlSeverity = "medium"
    review_cycle_days: Optional[int] = Field(default=None, ge=1, le=730)
    next_review_at: Optional[datetime] = None
    details_json: Dict[str, Any] = Field(default_factory=dict)


class ComplianceControlUpdate(BaseModel):
    owner_email: Optional[str] = None
    status: Optional[str] = None
    due_at: Optional[datetime] = None
    severity: Optional[ControlSeverity] = None
    review_cycle_days: Optional[int] = Field(default=None, ge=1, le=730)
    next_review_at: Optional[datetime] = None
    details_json: Optional[Dict[str, Any]] = None


class ComplianceControlReviewCreate(BaseModel):
    reviewer_email: Optional[str] = None
    note: Optional[str] = None
    outcome: Literal["reviewed", "needs_follow_up", "accepted", "rejected"] = "reviewed"
    status: Optional[str] = None
    severity: Optional[ControlSeverity] = None
    review_cycle_days: Optional[int] = Field(default=None, ge=1, le=730)
    next_review_at: Optional[datetime] = None


class ComplianceControlTemplateResponse(BaseModel):
    template_key: str
    article: str
    title: str
    evidence_domain: str
    default_severity: ControlSeverity
    default_review_cycle_days: int
    description: str
    suggested_evidence: List[str] = Field(default_factory=list)
    actor_roles: List[str] = Field(default_factory=list)
    risk_tiers: List[str] = Field(default_factory=list)
    applied: bool = False
    existing_control_id: Optional[str] = None


class ComplianceControlTemplateApplyRequest(BaseModel):
    template_keys: List[str] = Field(default_factory=list)
    ai_system_id: Optional[str] = None
    owner_email: Optional[str] = None
    due_at: Optional[datetime] = None


class ComplianceControlResponse(BaseModel):
    id: str
    tenant_id: str
    ai_system_id: Optional[str] = None
    control_key: str
    article: str
    title: str
    owner_email: Optional[str] = None
    status: str
    due_at: Optional[datetime] = None
    evidence_domain: str
    details_json: Dict[str, Any]
    evidence_item_count: int = 0
    active_evidence_count: int = 0
    needs_review_evidence_count: int = 0
    latest_evidence_at: Optional[datetime] = None
    evidence_status_counts: Dict[str, int] = Field(default_factory=dict)
    evidence_required: bool = True
    evidence_complete: bool = False
    severity: str = "medium"
    review_cycle_days: Optional[int] = None
    last_reviewed_at: Optional[datetime] = None
    next_review_at: Optional[datetime] = None
    review_overdue: bool = False
    last_review_note: Optional[str] = None
    review_history: List[Dict[str, Any]] = Field(default_factory=list)
    comment_count: int = 0
    latest_comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReadinessScorecardResponse(BaseModel):
    tenant_id: str
    ai_system_id: Optional[str] = None
    total_controls: int
    completed_controls: int
    overdue_controls: int
    readiness_score: int
    controls_by_status: Dict[str, int]


class ComplianceAuditStatusResponse(BaseModel):
    tenant_id: str
    ai_system_id: Optional[str] = None
    generated_at: datetime
    summary: Dict[str, Any]
    controls: List[Dict[str, Any]]
    markdown: str


# --- Evidence Vault ---

EvidenceItemStatus = Literal["draft", "active", "needs_review", "expired", "archived"]


class EvidenceItemCreate(BaseModel):
    title: str = Field(..., min_length=1)
    evidence_type: str = "policy"
    source: str = Field(..., min_length=1)
    description: Optional[str] = None
    source_url: Optional[str] = None
    owner_email: Optional[str] = None
    status: EvidenceItemStatus = "active"
    ai_system_id: Optional[str] = None
    control_id: Optional[str] = None
    collected_at: Optional[datetime] = None
    review_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class EvidenceItemUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1)
    evidence_type: Optional[str] = None
    source: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None
    source_url: Optional[str] = None
    owner_email: Optional[str] = None
    status: Optional[EvidenceItemStatus] = None
    ai_system_id: Optional[str] = None
    control_id: Optional[str] = None
    collected_at: Optional[datetime] = None
    review_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata_json: Optional[Dict[str, Any]] = None


class EvidenceArtifactResponse(BaseModel):
    id: str
    tenant_id: str
    evidence_item_id: str
    file_name: str
    content_type: str
    size_bytes: int
    artifact_hash: str
    hmac_signature: str
    storage_backend: str
    storage_key: str
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvidenceItemResponse(BaseModel):
    id: str
    tenant_id: str
    ai_system_id: Optional[str] = None
    control_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    evidence_type: str
    source: str
    source_url: Optional[str] = None
    owner_email: Optional[str] = None
    status: str
    collected_at: datetime
    review_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    evidence_hash: str
    hmac_signature: str
    metadata_json: Dict[str, Any]
    artifacts: List[EvidenceArtifactResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvidenceVaultSummaryResponse(BaseModel):
    tenant_id: str
    ai_system_id: Optional[str] = None
    total_items: int
    linked_system_count: int
    due_for_review_count: int
    expiring_soon_count: int
    items_by_status: Dict[str, int]
    items_by_type: Dict[str, int]


# --- Website / SaaS Compliance Scanner ---

class WebsiteScanCreate(BaseModel):
    url: str
    max_pages: int = Field(default=6, ge=1, le=12)

    @field_validator("url")
    @classmethod
    def validate_no_ssrf(cls, v: str) -> str:
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("URL must use http or https scheme")
        host = (parsed.hostname or "").lower()
        if not host:
            raise ValueError("URL must include a valid hostname")
        if _SSRF_BLOCKED.match(host):
            raise ValueError("URL resolves to a private or reserved address")
        try:
            addr = ipaddress.ip_address(host)
            if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
                raise ValueError("URL resolves to a private or reserved address")
        except ValueError as exc:
            if "private" in str(exc) or "reserved" in str(exc) or "loopback" in str(exc):
                raise
        return v


class WebsiteScanConvertRequest(BaseModel):
    actor_role: Optional[Literal["Provider", "Deployer", "Importer/Distributor"]] = None


class WebsiteScanResponse(BaseModel):
    id: str
    tenant_id: str
    url: str
    normalized_url: str
    status: str
    title: Optional[str] = None
    summary: Optional[str] = None
    detected_signals_json: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_refs_json: List[Dict[str, Any]] = Field(default_factory=list)
    gap_findings_json: List[Dict[str, Any]] = Field(default_factory=list)
    classification_json: Dict[str, Any] = Field(default_factory=dict)
    suggested_actions_json: List[Dict[str, Any]] = Field(default_factory=list)
    source_pages_json: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_score: int
    ai_system_id: Optional[str] = None
    intake_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebsiteScanConvertResponse(BaseModel):
    scan: WebsiteScanResponse
    ai_system: AiSystemResponse
    intake: IntakeResponse
    controls: List[ComplianceControlResponse] = Field(default_factory=list)
    evidence_event_id: Optional[str] = None


class WebsiteScanReportResponse(WebsiteScanConvertResponse):
    report: ReportResponse


# --- Tenant / User Administration ---

TenantRole = Literal["owner", "admin", "reviewer", "auditor", "viewer"]
TenantUserStatus = Literal["active", "invited", "disabled"]
TenantInvitationStatus = Literal["pending", "accepted", "revoked", "expired"]


class TenantAuthPolicyResponse(BaseModel):
    tenant_id: str
    google_login_enabled: bool
    password_login_enabled: bool
    allowed_domains: List[str] = Field(default_factory=list)
    allowed_emails: List[str] = Field(default_factory=list)
    auto_provision_google_users: bool
    default_role: TenantRole
    created_at: datetime
    updated_at: datetime


class TenantAuthPolicyUpdate(BaseModel):
    google_login_enabled: Optional[bool] = None
    password_login_enabled: Optional[bool] = None
    allowed_domains: Optional[List[str]] = None
    allowed_emails: Optional[List[str]] = None
    auto_provision_google_users: Optional[bool] = None
    default_role: Optional[TenantRole] = None


class TenantUserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    name: Optional[str] = None
    role: TenantRole = "viewer"
    status: TenantUserStatus = "active"


class TenantUserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[TenantRole] = None
    status: Optional[TenantUserStatus] = None


class TenantUserResponse(BaseModel):
    id: str
    tenant_id: str
    email: str
    name: Optional[str] = None
    role: TenantRole
    status: TenantUserStatus
    auth_provider: str
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenantInvitationCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    role: TenantRole = "viewer"


class TenantInvitationResponse(BaseModel):
    id: str
    tenant_id: str
    email: str
    role: TenantRole
    status: TenantInvitationStatus
    invited_by_email: Optional[str] = None
    accepted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenantLoginAuditResponse(BaseModel):
    id: str
    tenant_id: Optional[str] = None
    email: Optional[str] = None
    provider: str
    outcome: Literal["success", "failure"]
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenantActionAuditResponse(BaseModel):
    id: str
    tenant_id: str
    actor_user_id: Optional[str] = None
    actor_email: Optional[str] = None
    actor_role: Optional[str] = None
    action: str
    target_type: str
    target_id: Optional[str] = None
    target_email: Optional[str] = None
    before_json: Optional[Dict[str, Any]] = None
    after_json: Optional[Dict[str, Any]] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenantLoginResolveRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    name: Optional[str] = None
    provider: Literal["google", "password"] = "google"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class TenantLoginResolveResponse(BaseModel):
    allowed: bool
    reason: Optional[str] = None
    tenant_id: str
    user: Optional[TenantUserResponse] = None
    permissions: List[str] = Field(default_factory=list)


class TenantAdminSummaryResponse(BaseModel):
    users: List[TenantUserResponse] = Field(default_factory=list)
    invitations: List[TenantInvitationResponse] = Field(default_factory=list)
    auth_policy: TenantAuthPolicyResponse
    login_events: List[TenantLoginAuditResponse] = Field(default_factory=list)
    action_events: List[TenantActionAuditResponse] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Runtime Governance SDK
# ---------------------------------------------------------------------------

class PolicyCheckRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=32000)
    feature_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class PolicyCheckResponse(BaseModel):
    check_id: str
    decision: Literal["allow", "block", "review"]
    reason: str
    feature_id: Optional[str] = None
    feature_name: Optional[str] = None
    ai_system_id: Optional[str] = None
    risk_level: Optional[str] = None
    policy_refs: List[str] = Field(default_factory=list)
    latency_ms: int


class DeveloperKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=300)


class DeveloperKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key_id: str
    name: str
    description: Optional[str] = None
    role: str
    scopes: List[str]
    revoked: bool
    created_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    raw_key: Optional[str] = None  # populated only on creation


class RuntimeUsageDayStat(BaseModel):
    date: str
    total: int
    allow: int
    block: int
    review: int


class RuntimeUsageResponse(BaseModel):
    tenant_id: str
    period_days: int
    total_checks: int
    allow_count: int
    block_count: int
    review_count: int
    top_features: List[Dict[str, Any]]
    daily: List[RuntimeUsageDayStat]
