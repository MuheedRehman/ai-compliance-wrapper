from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import ReviewTask
from app.schemas import ReviewClose
from app.services.auth_service import authenticate_api_key

router = APIRouter()


@router.get("/v1/review-tasks")
def list_review_tasks(status: str | None = Query(default=None), feature_id: str | None = Query(default=None), x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="reviews:read")
    query = db.query(ReviewTask).filter(ReviewTask.tenant_id == auth["tenant_id"])
    if status:
        query = query.filter(ReviewTask.status == status)
    if feature_id:
        query = query.filter(ReviewTask.feature_id == feature_id)
    tasks = query.order_by(ReviewTask.created_at.desc()).all()
    db.commit()
    return {"tenant_id": auth["tenant_id"], "review_tasks": tasks}


@router.patch("/v1/review-tasks/{task_id}/close")
def close_review_task(task_id: str, payload: ReviewClose, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="reviews:write")
    task = db.query(ReviewTask).filter(ReviewTask.tenant_id == auth["tenant_id"], ReviewTask.review_task_id == task_id).first()
    if not task:
        db.rollback()
        raise HTTPException(status_code=404, detail="Review task not found")
    task.status = "closed"
    task.completed_at = datetime.now(timezone.utc)
    if payload.resolution_note:
        task.findings_json = {**(task.findings_json or {}), "resolution_note": payload.resolution_note}
    db.commit()
    db.refresh(task)
    return task
