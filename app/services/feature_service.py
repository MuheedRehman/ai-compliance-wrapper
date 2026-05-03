from datetime import datetime, timezone
import uuid
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import AiFeature, FeatureVersion
from app.services.hashing import hash_object
from app.services.review_service import get_or_create_open_review_task


def get_feature(db: Session, tenant_id: str, feature_id: str) -> AiFeature | None:
    return db.query(AiFeature).filter(AiFeature.tenant_id == tenant_id, AiFeature.feature_id == feature_id).first()


def compute_feature_fingerprint(feature_id: str, provider: str, model: str, prompt_hash: str, policy_bundle_version: str) -> str:
    return hash_object({
        "feature_id": feature_id,
        "provider": provider,
        "model": model,
        "prompt_hash": prompt_hash,
        "policy_bundle_version": policy_bundle_version,
    })


def ensure_feature_version_candidate(db: Session, tenant_id: str, feature: AiFeature, provider: str, model: str, prompt_hash: str) -> dict:
    fingerprint = compute_feature_fingerprint(feature.feature_id, provider, model, prompt_hash, feature.policy_bundle_version)

    version = db.query(FeatureVersion).filter(
        FeatureVersion.tenant_id == tenant_id,
        FeatureVersion.feature_pk == feature.id,
        FeatureVersion.fingerprint == fingerprint,
    ).first()

    if version:
        changed = bool(feature.current_fingerprint and feature.current_fingerprint != fingerprint)
        if changed and version.status == "candidate":
            get_or_create_open_review_task(
                db=db,
                tenant_id=tenant_id,
                feature_id=feature.feature_id,
                feature_pk=feature.id,
                feature_version_id=version.feature_version_id,
                review_type="change_triggered",
                trigger_reason="feature_fingerprint_changed",
                severity="medium",
                findings={"old_fingerprint": feature.current_fingerprint, "new_fingerprint": fingerprint, "model": model, "provider": provider},
            )
        return {
            "feature_version_id": version.feature_version_id,
            "fingerprint": fingerprint,
            "changed": changed,
            "version_status": version.status,
        }

    latest = db.query(FeatureVersion).filter(
        FeatureVersion.tenant_id == tenant_id,
        FeatureVersion.feature_pk == feature.id,
    ).order_by(FeatureVersion.version.desc()).first()

    version_number = 1 if latest is None else latest.version + 1
    changed = bool(feature.current_fingerprint and feature.current_fingerprint != fingerprint)
    status = "candidate" if changed else "approved"

    version = FeatureVersion(
        feature_version_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        feature_pk=feature.id,
        feature_id=feature.feature_id,
        version=version_number,
        provider=provider,
        model=model,
        prompt_hash=prompt_hash,
        fingerprint=fingerprint,
        policy_bundle_version=feature.policy_bundle_version,
        change_reason="fingerprint_changed" if changed else "initial_version",
        status=status,
        approved_at=datetime.now(timezone.utc) if status == "approved" else None,
    )
    db.add(version)
    db.flush()

    if feature.current_fingerprint is None:
        feature.current_fingerprint = fingerprint
        feature.current_prompt_hash = prompt_hash
        feature.current_feature_version_id = version.feature_version_id
        db.flush()

    if changed:
        get_or_create_open_review_task(
            db=db,
            tenant_id=tenant_id,
            feature_id=feature.feature_id,
            feature_pk=feature.id,
            feature_version_id=version.feature_version_id,
            review_type="change_triggered",
            trigger_reason="feature_fingerprint_changed",
            severity="medium",
            findings={"old_fingerprint": feature.current_fingerprint, "new_fingerprint": fingerprint, "model": model, "provider": provider},
        )

    return {"feature_version_id": version.feature_version_id, "fingerprint": fingerprint, "changed": changed, "version_status": status}


def validate_registered_feature(db: Session, tenant_id: str, feature_id: str, provider: str, model: str, prompt_hash: str) -> dict:
    feature = get_feature(db, tenant_id, feature_id)

    if feature is None:
        return {"allowed": False, "feature": None, "reason": "feature_not_registered", "message": "feature_id is not registered"}

    if feature.compliance_status in {"blocked", "inactive"}:
        return {"allowed": False, "feature": feature, "reason": "feature_not_active", "message": f"Feature compliance_status is {feature.compliance_status}"}

    if feature.approved_providers and provider not in feature.approved_providers:
        return {"allowed": False, "feature": feature, "reason": "provider_not_approved", "message": f"Provider {provider} is not approved for this feature"}

    if feature.approved_models and model not in feature.approved_models:
        return {"allowed": False, "feature": feature, "reason": "model_not_approved", "message": f"Model {model} is not approved for this feature"}

    version_result = ensure_feature_version_candidate(db, tenant_id, feature, provider, model, prompt_hash)

    if version_result["version_status"] in {"rejected", "superseded"}:
        return {
            "allowed": False,
            "feature": feature,
            "reason": f"version_{version_result['version_status']}",
            "message": f"Feature version is {version_result['version_status']} and cannot execute",
            "policy_bundle_version": feature.policy_bundle_version,
            **version_result,
        }

    return {"allowed": True, "feature": feature, "reason": "ok", "message": None, "policy_bundle_version": feature.policy_bundle_version, **version_result}


def approve_feature_version(db: Session, tenant_id: str, feature_id: str, feature_version_id: str):
    feature = get_feature(db, tenant_id, feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")

    version = db.query(FeatureVersion).filter(
        FeatureVersion.tenant_id == tenant_id,
        FeatureVersion.feature_pk == feature.id,
        FeatureVersion.feature_version_id == feature_version_id,
    ).first()

    if not version:
        raise HTTPException(status_code=404, detail="Feature version not found")

    old_approved_versions = db.query(FeatureVersion).filter(
        FeatureVersion.tenant_id == tenant_id,
        FeatureVersion.feature_pk == feature.id,
        FeatureVersion.status == "approved",
        FeatureVersion.feature_version_id != feature_version_id,
    ).all()

    for old_version in old_approved_versions:
        old_version.status = "superseded"
        old_version.superseded_at = datetime.now(timezone.utc)
        old_version.approved_at = None
        old_version.rejected_at = None

    version.status = "approved"
    version.approved_at = datetime.now(timezone.utc)
    version.superseded_at = None
    version.rejected_at = None

    feature.current_fingerprint = version.fingerprint
    feature.current_prompt_hash = version.prompt_hash
    feature.current_feature_version_id = version.feature_version_id
    db.flush()
    return version


def reject_feature_version(db: Session, tenant_id: str, feature_id: str, feature_version_id: str):
    feature = get_feature(db, tenant_id, feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")

    version = db.query(FeatureVersion).filter(
        FeatureVersion.tenant_id == tenant_id,
        FeatureVersion.feature_pk == feature.id,
        FeatureVersion.feature_version_id == feature_version_id,
    ).first()

    if not version:
        raise HTTPException(status_code=404, detail="Feature version not found")

    rejecting_current_approved = (
        feature.current_feature_version_id == feature_version_id
        and version.status == "approved"
    )

    replacement = None

    if rejecting_current_approved:
        replacement = db.query(FeatureVersion).filter(
            FeatureVersion.tenant_id == tenant_id,
            FeatureVersion.feature_pk == feature.id,
            FeatureVersion.status == "approved",
            FeatureVersion.feature_version_id != feature_version_id,
        ).first()

        if not replacement:
            raise HTTPException(
                status_code=409,
                detail="Cannot reject current approved version without approving a replacement first",
            )

    # Current-state timestamp semantics:
    # only the timestamp matching the active status should be populated.
    version.status = "rejected"
    version.rejected_at = datetime.now(timezone.utc)
    version.approved_at = None
    version.superseded_at = None

    if replacement:
        feature.current_feature_version_id = replacement.feature_version_id
        feature.current_fingerprint = replacement.fingerprint
        feature.current_prompt_hash = replacement.prompt_hash

    db.flush()
    return version
