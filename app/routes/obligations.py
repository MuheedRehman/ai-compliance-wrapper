from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas import (
    AnnexIIICategoryResponse,
    ComplianceDimensionResponse,
    FRIACreate, FRIAUpdate, FRIAResponse,
    OversightCreate, OversightUpdate, OversightResponse,
    IncidentCreate, IncidentUpdate, IncidentResponse,
    ObligationExplanationResponse,
)
from app.services.auth_service import authenticate_api_key
from app.services.classification_service import ClassificationService
from app.services.obligation_service import ObligationService
from app.services.regulatory_knowledge import list_annex_iii_categories, list_compliance_dimensions
from typing import List

router = APIRouter(prefix="/v1/obligations", tags=["Obligation Workflows"])


# --- Obligation Engine 2.0 ---
@router.get("/dimensions", response_model=List[ComplianceDimensionResponse])
def list_dimensions(x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    authenticate_api_key(db, x_api_key, required_scope="compliance:read")
    return list_compliance_dimensions()


@router.get("/annex-iii", response_model=List[AnnexIIICategoryResponse])
def list_annex_iii(x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    authenticate_api_key(db, x_api_key, required_scope="compliance:read")
    return list_annex_iii_categories()


@router.get("/explain/intake/{intake_id}", response_model=ObligationExplanationResponse)
def explain_intake_obligations(intake_id: str, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="intake:read")
    return ClassificationService.explain_intake(db, auth["tenant_id"], intake_id)


# --- FRIA ---
@router.get("/fria", response_model=List[FRIAResponse])
def list_frias(x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="fria:read")
    return ObligationService.list_frias(db, auth["tenant_id"])

@router.get("/fria/{fria_id}", response_model=FRIAResponse)
def get_fria(fria_id: str, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="fria:read")
    return ObligationService.get_fria(db, auth["tenant_id"], fria_id)

@router.post("/fria", response_model=FRIAResponse)
def create_fria(payload: FRIACreate, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="fria:write")
    return ObligationService.create_fria(db, auth["tenant_id"], payload)

@router.patch("/fria/{fria_id}", response_model=FRIAResponse)
def update_fria(fria_id: str, payload: FRIAUpdate, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="fria:write")
    return ObligationService.update_fria(db, auth["tenant_id"], fria_id, payload)

@router.delete("/fria/{fria_id}")
def delete_fria(fria_id: str, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="fria:write")
    return ObligationService.delete_fria(db, auth["tenant_id"], fria_id)


# --- Oversight ---
@router.get("/oversight", response_model=List[OversightResponse])
def list_oversight(x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="oversight:read")
    return ObligationService.list_oversight(db, auth["tenant_id"])

@router.post("/oversight", response_model=OversightResponse)
def create_oversight(payload: OversightCreate, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="oversight:write")
    return ObligationService.create_oversight(db, auth["tenant_id"], payload)

@router.patch("/oversight/{assignment_id}", response_model=OversightResponse)
def update_oversight(assignment_id: str, payload: OversightUpdate, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="oversight:write")
    return ObligationService.update_oversight(db, auth["tenant_id"], assignment_id, payload)

@router.delete("/oversight/{assignment_id}")
def delete_oversight(assignment_id: str, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="oversight:write")
    return ObligationService.delete_oversight(db, auth["tenant_id"], assignment_id)


# --- Incidents ---
@router.get("/incidents", response_model=List[IncidentResponse])
def list_incidents(x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="incidents:read")
    return ObligationService.list_incidents(db, auth["tenant_id"])

@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: str, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="incidents:read")
    return ObligationService.get_incident(db, auth["tenant_id"], incident_id)

@router.post("/incidents", response_model=IncidentResponse)
def create_incident(payload: IncidentCreate, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="incidents:write")
    return ObligationService.create_incident(db, auth["tenant_id"], payload)

@router.patch("/incidents/{incident_id}", response_model=IncidentResponse)
def update_incident(incident_id: str, payload: IncidentUpdate, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="incidents:write")
    return ObligationService.update_incident(db, auth["tenant_id"], incident_id, payload)

@router.delete("/incidents/{incident_id}")
def delete_incident(incident_id: str, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="incidents:write")
    return ObligationService.delete_incident(db, auth["tenant_id"], incident_id)
