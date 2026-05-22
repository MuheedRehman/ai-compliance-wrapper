from typing import List, Optional

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import (
    ComplianceAuditStatusResponse,
    ComplianceControlCreate,
    ComplianceControlReviewCreate,
    ComplianceControlResponse,
    ComplianceControlTemplateApplyRequest,
    ComplianceControlTemplateResponse,
    ComplianceControlUpdate,
    EvidenceItemResponse,
    ReadinessScorecardResponse,
)
from app.services.auth_service import authenticate_api_key
from app.services.compliance_control_service import ComplianceControlService
from app.services.evidence_vault_service import EvidenceVaultService


router = APIRouter(prefix="/v1/compliance", tags=["Compliance Controls"])


@router.get("/control-templates", response_model=List[ComplianceControlTemplateResponse])
def list_control_templates(
    ai_system_id: Optional[str] = Query(default=None),
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="compliance:read")
    return ComplianceControlService.list_templates(db, auth["tenant_id"], ai_system_id)


@router.get("/controls", response_model=List[ComplianceControlResponse])
def list_controls(
    ai_system_id: Optional[str] = Query(default=None),
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="compliance:read")
    return ComplianceControlService.list_controls(db, auth["tenant_id"], ai_system_id)


@router.post("/controls", response_model=ComplianceControlResponse)
def create_control(
    payload: ComplianceControlCreate,
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="compliance:write")
    return ComplianceControlService.create_control(db, auth["tenant_id"], payload)


@router.post("/controls/apply-templates", response_model=List[ComplianceControlResponse])
def apply_control_templates(
    payload: ComplianceControlTemplateApplyRequest,
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="compliance:write")
    return ComplianceControlService.apply_templates(db, auth["tenant_id"], payload)


@router.patch("/controls/{control_id}", response_model=ComplianceControlResponse)
def update_control(
    control_id: str,
    payload: ComplianceControlUpdate,
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="compliance:write")
    return ComplianceControlService.update_control(db, auth["tenant_id"], control_id, payload)


@router.post("/controls/{control_id}/reviews", response_model=ComplianceControlResponse)
def record_control_review(
    control_id: str,
    payload: ComplianceControlReviewCreate,
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="compliance:write")
    return ComplianceControlService.record_review(db, auth["tenant_id"], control_id, payload)


@router.get("/controls/{control_id}/evidence", response_model=List[EvidenceItemResponse])
def list_control_evidence(
    control_id: str,
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="compliance:read")
    ComplianceControlService.get_control(db, auth["tenant_id"], control_id)
    return EvidenceVaultService.list_items(db, auth["tenant_id"], control_id=control_id, limit=500)


@router.post("/controls/{control_id}/evidence/{item_id}", response_model=EvidenceItemResponse)
def attach_evidence_to_control(
    control_id: str,
    item_id: str,
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="compliance:write")
    return EvidenceVaultService.attach_item_to_control(db, auth["tenant_id"], item_id, control_id)


@router.post("/controls/seed-baseline", response_model=List[ComplianceControlResponse])
def seed_baseline_controls(
    ai_system_id: Optional[str] = Query(default=None),
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="compliance:write")
    return ComplianceControlService.seed_baseline(db, auth["tenant_id"], ai_system_id)


@router.get("/scorecard", response_model=ReadinessScorecardResponse)
def get_scorecard(
    ai_system_id: Optional[str] = Query(default=None),
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="compliance:read")
    return ComplianceControlService.scorecard(db, auth["tenant_id"], ai_system_id)


@router.get("/audit-status", response_model=ComplianceAuditStatusResponse)
def get_audit_status(
    ai_system_id: Optional[str] = Query(default=None),
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="compliance:read")
    return ComplianceControlService.audit_status(db, auth["tenant_id"], ai_system_id)
