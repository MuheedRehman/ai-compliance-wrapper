from fastapi import APIRouter, Depends, Header, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import EvidenceLog
from app.services.auth_service import authenticate_api_key

router = APIRouter()


@router.get("/v1/logs")
def get_logs(
    limit: int = Query(default=50, ge=1, le=500),
    feature_id: str | None = None,
    risk_level: str | None = None,
    decision: str | None = None,
    ai_system_id: str | None = None,
    evidence_domain: str | None = None,
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db)
):
    auth = authenticate_api_key(db, x_api_key, required_scope="logs:read")
    query = db.query(EvidenceLog).filter(EvidenceLog.tenant_id == auth["tenant_id"])
    if feature_id:
        query = query.filter(EvidenceLog.feature_id == feature_id)
    if risk_level:
        query = query.filter(EvidenceLog.risk_level == risk_level)
    if decision:
        query = query.filter(EvidenceLog.decision == decision)
    if ai_system_id:
        query = query.filter(EvidenceLog.ai_system_id == ai_system_id)
    if evidence_domain:
        query = query.filter(EvidenceLog.evidence_domain == evidence_domain)
    logs = query.order_by(EvidenceLog.created_at.desc()).limit(limit).all()
    return {"tenant_id": auth["tenant_id"], "logs": jsonable_encoder(logs)}
