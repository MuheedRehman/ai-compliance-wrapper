import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import AiSystem
from app.schemas import AiSystemCreate, AiSystemUpdate

def create_ai_system(db: Session, tenant_id: str, payload: AiSystemCreate) -> AiSystem:
    ai_system = AiSystem(
        id=f"sys-{uuid.uuid4().hex[:8]}",
        tenant_id=tenant_id,
        name=payload.name,
        description=payload.description,
        # DB defaults will handle deployment_status and registration_status if not provided
    )
    db.add(ai_system)
    db.commit()
    db.refresh(ai_system)
    return ai_system

def list_ai_systems(db: Session, tenant_id: str):
    return db.query(AiSystem).filter(AiSystem.tenant_id == tenant_id).order_by(AiSystem.created_at.desc()).all()

def get_ai_system(db: Session, tenant_id: str, ai_system_id: str) -> AiSystem:
    ai_system = db.query(AiSystem).filter(AiSystem.tenant_id == tenant_id, AiSystem.id == ai_system_id).first()
    if not ai_system:
        raise HTTPException(status_code=404, detail="AI System not found")
    return ai_system

def update_ai_system(db: Session, tenant_id: str, ai_system_id: str, payload: AiSystemUpdate) -> AiSystem:
    ai_system = get_ai_system(db, tenant_id, ai_system_id)
    
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ai_system, key, value)
    
    db.commit()
    db.refresh(ai_system)
    return ai_system
