from typing import List, Optional

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import (
    ComplianceControlCreate,
    ComplianceControlResponse,
    ComplianceControlUpdate,
    ReadinessScorecardResponse,
)
from app.services.auth_service import authenticate_api_key
from app.services.compliance_control_service import ComplianceControlService


router = APIRouter(prefix="/v1/compliance", tags=["Compliance Controls"])


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


@router.patch("/controls/{control_id}", response_model=ComplianceControlResponse)
def update_control(
    control_id: str,
    payload: ComplianceControlUpdate,
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="compliance:write")
    return ComplianceControlService.update_control(db, auth["tenant_id"], control_id, payload)


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
