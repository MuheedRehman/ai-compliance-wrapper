from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import ApiKey
from app.services.hashing import hash_api_key


def authenticate_api_key(db: Session, api_key: str | None, required_scope: str) -> dict:
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    key_hash = hash_api_key(api_key)
    record = db.query(ApiKey).filter(ApiKey.key_hash == key_hash).first()

    if not record or record.revoked:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key")

    scopes = record.scopes or []

    if required_scope not in scopes and "admin" not in scopes:
        raise HTTPException(status_code=403, detail=f"Missing required scope: {required_scope}")

    record.last_used_at = datetime.now(timezone.utc)
    db.flush()

    return {
        "key_id": record.key_id,
        "tenant_id": record.tenant_id,
        "role": record.role,
        "scopes": scopes,
        "key_hash": key_hash,
        "key_name": record.name,
    }
