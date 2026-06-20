from fastapi import APIRouter, Depends, Header, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas import (
    AnnexIIICategoryResponse,
    ComplianceDimensionResponse,
    FRIACreate, FRIAUpdate, FRIAResponse,
    FRIASectionsUpdate, FRIASubmitRequest, FRIAReviewRequest,
    OversightCreate, OversightUpdate, OversightResponse,
    IncidentCreate, IncidentUpdate, IncidentResponse,
    ObligationExplanationResponse,
    PenaltyExposureResponse,
)
from app.services.auth_service import authenticate_api_key, DashboardPermission
from app.services.classification_service import ClassificationService
from app.services.obligation_service import ObligationService
from app.services.regulatory_knowledge import list_annex_iii_categories, list_compliance_dimensions, list_penalty_exposures
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


@router.get("/penalties", response_model=List[PenaltyExposureResponse])
def list_penalties(x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    authenticate_api_key(db, x_api_key, required_scope="compliance:read")
    return list_penalty_exposures()


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
    return ObligationService.get_fria_response(db, auth["tenant_id"], fria_id)

@router.post("/fria", response_model=FRIAResponse, dependencies=[DashboardPermission("governance:write")])
def create_fria(payload: FRIACreate, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="fria:write")
    return ObligationService.create_fria(db, auth["tenant_id"], payload)

@router.patch("/fria/{fria_id}", response_model=FRIAResponse, dependencies=[DashboardPermission("governance:write")])
def update_fria(fria_id: str, payload: FRIAUpdate, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="fria:write")
    return ObligationService.update_fria(db, auth["tenant_id"], fria_id, payload)

@router.delete("/fria/{fria_id}", dependencies=[DashboardPermission("governance:write")])
def delete_fria(fria_id: str, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="fria:write")
    return ObligationService.delete_fria(db, auth["tenant_id"], fria_id)

@router.patch("/fria/{fria_id}/sections", response_model=FRIAResponse, dependencies=[DashboardPermission("governance:write")])
def update_fria_sections(fria_id: str, payload: FRIASectionsUpdate, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="fria:write")
    return ObligationService.update_fria_sections(db, auth["tenant_id"], fria_id, payload)

@router.post("/fria/{fria_id}/submit", response_model=FRIAResponse, dependencies=[DashboardPermission("governance:write")])
def submit_fria(fria_id: str, payload: FRIASubmitRequest, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="fria:write")
    return ObligationService.submit_fria(db, auth["tenant_id"], fria_id, payload)

@router.post("/fria/{fria_id}/review", response_model=FRIAResponse, dependencies=[DashboardPermission("governance:write")])
def review_fria(fria_id: str, payload: FRIAReviewRequest, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="fria:write")
    return ObligationService.review_fria(db, auth["tenant_id"], fria_id, payload)

@router.get("/fria/{fria_id}/export", response_class=PlainTextResponse)
def export_fria(fria_id: str, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="fria:read")
    markdown = ObligationService.export_fria_markdown(db, auth["tenant_id"], fria_id)
    return PlainTextResponse(
        content=markdown,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="fria-{fria_id}.md"'},
    )


# --- Oversight ---
@router.get("/oversight", response_model=List[OversightResponse])
def list_oversight(x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="oversight:read")
    return ObligationService.list_oversight(db, auth["tenant_id"])

@router.post("/oversight", response_model=OversightResponse, dependencies=[DashboardPermission("governance:write")])
def create_oversight(payload: OversightCreate, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="oversight:write")
    return ObligationService.create_oversight(db, auth["tenant_id"], payload)

@router.patch("/oversight/{assignment_id}", response_model=OversightResponse, dependencies=[DashboardPermission("governance:write")])
def update_oversight(assignment_id: str, payload: OversightUpdate, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="oversight:write")
    return ObligationService.update_oversight(db, auth["tenant_id"], assignment_id, payload)

@router.delete("/oversight/{assignment_id}", dependencies=[DashboardPermission("governance:write")])
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

@router.post("/incidents", response_model=IncidentResponse, dependencies=[DashboardPermission("governance:write")])
def create_incident(payload: IncidentCreate, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="incidents:write")
    return ObligationService.create_incident(db, auth["tenant_id"], payload)

@router.patch("/incidents/{incident_id}", response_model=IncidentResponse, dependencies=[DashboardPermission("governance:write")])
def update_incident(incident_id: str, payload: IncidentUpdate, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="incidents:write")
    return ObligationService.update_incident(db, auth["tenant_id"], incident_id, payload)

@router.delete("/incidents/{incident_id}", dependencies=[DashboardPermission("governance:write")])
def delete_incident(incident_id: str, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="incidents:write")
    return ObligationService.delete_incident(db, auth["tenant_id"], incident_id)
