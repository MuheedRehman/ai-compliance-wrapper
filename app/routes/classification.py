from fastapi import APIRouter, Depends, Header
from fastapi import Query
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas import ComplianceControlResponse, IntakeCreate, IntakeResponse
from app.services.auth_service import authenticate_api_key
from app.services.classification_service import ClassificationService
from typing import List

router = APIRouter(prefix="/v1/intake", tags=["Classification & Intake"])

@router.post("", response_model=IntakeResponse)
def create_intake(
    payload: IntakeCreate, 
    x_api_key: str | None = Header(default=None), 
    db: Session = Depends(get_db)
):
    auth = authenticate_api_key(db, x_api_key, required_scope="intake:write")
    return ClassificationService.create_intake(db, auth["tenant_id"], payload)

@router.get("", response_model=List[IntakeResponse])
def list_intakes(
    x_api_key: str | None = Header(default=None), 
    db: Session = Depends(get_db)
):
    auth = authenticate_api_key(db, x_api_key, required_scope="intake:read")
    return ClassificationService.list_intakes(db, auth["tenant_id"])

@router.get("/{intake_id}", response_model=IntakeResponse)
def get_intake(
    intake_id: str, 
    x_api_key: str | None = Header(default=None), 
    db: Session = Depends(get_db)
):
    auth = authenticate_api_key(db, x_api_key, required_scope="intake:read")
    return ClassificationService.get_intake(db, auth["tenant_id"], intake_id)


@router.post("/{intake_id}/control-plan", response_model=List[ComplianceControlResponse])
def materialize_intake_control_plan(
    intake_id: str,
    ai_system_id: str | None = Query(default=None),
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="compliance:write")
    return ClassificationService.materialize_control_plan(db, auth["tenant_id"], intake_id, ai_system_id)
