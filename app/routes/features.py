import uuid
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import AiFeature, FeatureVersion
from app.schemas import FeatureCreate, FeatureUpdate, VersionDecision
from app.services.auth_service import authenticate_api_key
from app.services.feature_service import approve_feature_version, reject_feature_version

router = APIRouter()


@router.post("/v1/features")
def create_feature(payload: FeatureCreate, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="features:write")
    existing = db.query(AiFeature).filter(AiFeature.tenant_id == auth["tenant_id"], AiFeature.feature_id == payload.feature_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Feature already exists for this tenant")

    feature = AiFeature(
        id=str(uuid.uuid4()),
        tenant_id=auth["tenant_id"],
        feature_id=payload.feature_id,
        name=payload.name,
        slug=payload.feature_id,
        description=payload.description,
        owner_email=payload.owner_email,
        team=payload.team,
        use_case=payload.use_case,
        decision_impact=payload.decision_impact,
        affected_user_groups=payload.affected_user_groups,
        risk_level_current=payload.risk_level_current,
        compliance_status=payload.compliance_status,
        fria_likely_required=payload.fria_likely_required,
        approved_providers=payload.approved_providers,
        approved_models=payload.approved_models,
    )
    db.add(feature)
    db.commit()
    db.refresh(feature)
    return jsonable_encoder(feature)


@router.get("/v1/features")
def list_features(x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="features:read")
    features = db.query(AiFeature).filter(AiFeature.tenant_id == auth["tenant_id"]).order_by(AiFeature.created_at.desc()).all()
    return {"tenant_id": auth["tenant_id"], "features": jsonable_encoder(features)}


@router.get("/v1/features/{feature_id}")
def get_feature(feature_id: str, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="features:read")
    feature = db.query(AiFeature).filter(AiFeature.tenant_id == auth["tenant_id"], AiFeature.feature_id == feature_id).first()
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    return jsonable_encoder(feature)


@router.patch("/v1/features/{feature_id}")
def update_feature(feature_id: str, payload: FeatureUpdate, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="features:write")
    feature = db.query(AiFeature).filter(AiFeature.tenant_id == auth["tenant_id"], AiFeature.feature_id == feature_id).first()
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(feature, key, value)
    db.commit()
    db.refresh(feature)
    return jsonable_encoder(feature)


@router.get("/v1/features/{feature_id}/versions")
def list_feature_versions(feature_id: str, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="features:read")
    feature = db.query(AiFeature).filter(AiFeature.tenant_id == auth["tenant_id"], AiFeature.feature_id == feature_id).first()
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    versions = db.query(FeatureVersion).filter(FeatureVersion.tenant_id == auth["tenant_id"], FeatureVersion.feature_pk == feature.id).order_by(FeatureVersion.version.desc()).all()
    return {"feature_id": feature_id, "versions": jsonable_encoder(versions)}


@router.post("/v1/features/{feature_id}/versions/{feature_version_id}/approve")
def approve_version(feature_id: str, feature_version_id: str, payload: VersionDecision, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="features:write")
    version = approve_feature_version(db, auth["tenant_id"], feature_id, feature_version_id)
    db.commit()
    db.refresh(version)
    return jsonable_encoder(version)


@router.post("/v1/features/{feature_id}/versions/{feature_version_id}/reject")
def reject_version(feature_id: str, feature_version_id: str, payload: VersionDecision, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="features:write")
    version = reject_feature_version(db, auth["tenant_id"], feature_id, feature_version_id)
    db.commit()
    db.refresh(version)
    return jsonable_encoder(version)
