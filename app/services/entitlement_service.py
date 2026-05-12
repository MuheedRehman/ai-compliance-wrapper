import uuid
from sqlalchemy.orm import Session
from app.models import Entitlement

def get_entitlements(db: Session, tenant_id: str):
    return db.query(Entitlement).filter(Entitlement.tenant_id == tenant_id).all()

def check_entitlement(db: Session, tenant_id: str, feature_key: str) -> bool:
    ent = db.query(Entitlement).filter(
        Entitlement.tenant_id == tenant_id,
        Entitlement.feature_key == feature_key
    ).first()
    
    if ent and ent.is_enabled:
        return True
    return False

def grant_entitlement(db: Session, tenant_id: str, feature_key: str, limit_value: int = None):
    ent = db.query(Entitlement).filter(
        Entitlement.tenant_id == tenant_id,
        Entitlement.feature_key == feature_key
    ).first()
    
    if not ent:
        ent = Entitlement(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            feature_key=feature_key,
            is_enabled=True,
            limit_value=limit_value
        )
        db.add(ent)
    else:
        ent.is_enabled = True
        if limit_value is not None:
            ent.limit_value = limit_value
            
    db.commit()
    return ent

def revoke_entitlement(db: Session, tenant_id: str, feature_key: str):
    ent = db.query(Entitlement).filter(
        Entitlement.tenant_id == tenant_id,
        Entitlement.feature_key == feature_key
    ).first()
    
    if ent:
        ent.is_enabled = False
        db.commit()
    return ent
