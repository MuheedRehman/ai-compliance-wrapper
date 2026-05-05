from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Any, Dict, List, Optional, Literal


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


class AiSystemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    deployment_status: Optional[Literal["draft", "deployed", "retired"]] = None
    registration_status: Optional[Literal["draft", "registered", "rejected"]] = None


class AiSystemResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: Optional[str] = None
    deployment_status: str
    registration_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
