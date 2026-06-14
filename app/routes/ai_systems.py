from fastapi import APIRouter, Depends, Header
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas import (
    AiSystemCreate,
    AiSystemReviewCreate,
    AiSystemReviewResponse,
    AiSystemUpdate,
    AiSystemResponse,
    AiSystemWorkspaceResponse,
)
from app.services.auth_service import authenticate_api_key, DashboardPermission
from app.services import ai_system_service
from typing import List

router = APIRouter(prefix="/v1/ai-systems", tags=["AI Systems"])

@router.post("", response_model=AiSystemResponse, dependencies=[DashboardPermission("governance:write")])
def create_ai_system(
    payload: AiSystemCreate,
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="systems:write")
    return ai_system_service.create_ai_system(db, auth["tenant_id"], payload)

@router.get("", response_model=List[AiSystemResponse])
def list_ai_systems(x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="systems:read")
    return ai_system_service.list_ai_systems(db, auth["tenant_id"])

@router.get("/{ai_system_id}", response_model=AiSystemResponse)
def get_ai_system(ai_system_id: str, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="systems:read")
    return ai_system_service.get_ai_system(db, auth["tenant_id"], ai_system_id)

@router.get("/{ai_system_id}/workspace", response_model=AiSystemWorkspaceResponse)
def get_ai_system_workspace(ai_system_id: str, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="systems:read")
    return jsonable_encoder(ai_system_service.get_ai_system_workspace(db, auth["tenant_id"], ai_system_id))

@router.get("/{ai_system_id}/reviews", response_model=List[AiSystemReviewResponse])
def list_ai_system_reviews(ai_system_id: str, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="systems:read")
    return ai_system_service.list_ai_system_reviews(db, auth["tenant_id"], ai_system_id)

@router.post("/{ai_system_id}/reviews", response_model=AiSystemReviewResponse, dependencies=[DashboardPermission("governance:write")])
def record_ai_system_review(
    ai_system_id: str,
    payload: AiSystemReviewCreate,
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="systems:write")
    return ai_system_service.record_ai_system_review(db, auth["tenant_id"], ai_system_id, payload)

@router.patch("/{ai_system_id}", response_model=AiSystemResponse, dependencies=[DashboardPermission("governance:write")])
def update_ai_system(
    ai_system_id: str,
    payload: AiSystemUpdate,
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="systems:write")
    return ai_system_service.update_ai_system(db, auth["tenant_id"], ai_system_id, payload)
