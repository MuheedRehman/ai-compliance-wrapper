from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import AiFeature, FeatureVersion
from app.schemas import FeatureCreate, FeatureUpdate, VersionDecision
from app.services.auth_service import authenticate_api_key, DashboardPermission
from app.services.feature_service import approve_feature_version, reject_feature_version, create_feature as service_create_feature, update_feature as service_update_feature

router = APIRouter()


@router.post("/v1/features", dependencies=[DashboardPermission("governance:write")])
def create_feature(payload: FeatureCreate, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="features:write")
    feature = service_create_feature(db, auth["tenant_id"], payload)
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


@router.patch("/v1/features/{feature_id}", dependencies=[DashboardPermission("governance:write")])
def update_feature(feature_id: str, payload: FeatureUpdate, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="features:write")
    feature = service_update_feature(db, auth["tenant_id"], feature_id, payload)
    return jsonable_encoder(feature)


@router.get("/v1/features/{feature_id}/versions")
def list_feature_versions(feature_id: str, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="features:read")
    feature = db.query(AiFeature).filter(AiFeature.tenant_id == auth["tenant_id"], AiFeature.feature_id == feature_id).first()
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    versions = db.query(FeatureVersion).filter(FeatureVersion.tenant_id == auth["tenant_id"], FeatureVersion.feature_pk == feature.id).order_by(FeatureVersion.version.desc()).all()
    return {"feature_id": feature_id, "versions": jsonable_encoder(versions)}


@router.post("/v1/features/{feature_id}/versions/{feature_version_id}/approve", dependencies=[DashboardPermission("governance:write")])
def approve_version(feature_id: str, feature_version_id: str, payload: VersionDecision, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="features:write")
    version = approve_feature_version(db, auth["tenant_id"], feature_id, feature_version_id)
    db.commit()
    db.refresh(version)
    return jsonable_encoder(version)


@router.post("/v1/features/{feature_id}/versions/{feature_version_id}/reject", dependencies=[DashboardPermission("governance:write")])
def reject_version(feature_id: str, feature_version_id: str, payload: VersionDecision, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="features:write")
    version = reject_feature_version(db, auth["tenant_id"], feature_id, feature_version_id)
    db.commit()
    db.refresh(version)
    return jsonable_encoder(version)
