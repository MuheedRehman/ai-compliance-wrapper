from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas import AiSystemCreate, AiSystemUpdate, AiSystemResponse
from app.services.auth_service import authenticate_api_key
from app.services import ai_system_service
from typing import List

router = APIRouter(prefix="/v1/ai-systems", tags=["AI Systems"])

@router.post("", response_model=AiSystemResponse)
def create_ai_system(
    payload: AiSystemCreate, 
    x_api_key: str | None = Header(default=None), 
    db: Session = Depends(get_db)
):
    auth = authenticate_api_key(db, x_api_key, required_scope="systems:write")
    system = ai_system_service.create_ai_system(db, auth["tenant_id"], payload)
    return system

@router.get("", response_model=List[AiSystemResponse])
def list_ai_systems(
    x_api_key: str | None = Header(default=None), 
    db: Session = Depends(get_db)
):
    auth = authenticate_api_key(db, x_api_key, required_scope="systems:read")
    systems = ai_system_service.list_ai_systems(db, auth["tenant_id"])
    return systems

@router.get("/{ai_system_id}", response_model=AiSystemResponse)
def get_ai_system(
    ai_system_id: str, 
    x_api_key: str | None = Header(default=None), 
    db: Session = Depends(get_db)
):
    auth = authenticate_api_key(db, x_api_key, required_scope="systems:read")
    system = ai_system_service.get_ai_system(db, auth["tenant_id"], ai_system_id)
    return system

@router.patch("/{ai_system_id}", response_model=AiSystemResponse)
def update_ai_system(
    ai_system_id: str, 
    payload: AiSystemUpdate, 
    x_api_key: str | None = Header(default=None), 
    db: Session = Depends(get_db)
):
    auth = authenticate_api_key(db, x_api_key, required_scope="systems:write")
    system = ai_system_service.update_ai_system(db, auth["tenant_id"], ai_system_id, payload)
    return system
