from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas import ChatRequest
from app.services.auth_service import authenticate_api_key
from app.services.pipeline import run_chat_pipeline

router = APIRouter()


@router.post("/v1/chat/completions")
def chat_completions(request: ChatRequest, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth_context = authenticate_api_key(db, x_api_key, required_scope="invoke_ai")
    return run_chat_pipeline(db, request, auth_context)
