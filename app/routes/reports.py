from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas import ReportCreate, ReportResponse
from app.services.auth_service import authenticate_api_key, DashboardPermission
from app.services.report_service import ReportService
from typing import List

router = APIRouter(prefix="/v1/reports", tags=["Assessment & Reporting"])

@router.get("", response_model=List[ReportResponse])
def list_reports(x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="reports:read")
    return ReportService.list_reports(db, auth["tenant_id"])

@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: str, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="reports:read")
    return ReportService.get_report(db, auth["tenant_id"], report_id)

@router.post("", response_model=ReportResponse, dependencies=[DashboardPermission("reports:write")])
def generate_report(payload: ReportCreate, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    auth = authenticate_api_key(db, x_api_key, required_scope="reports:write")
    return ReportService.generate_report(db, auth["tenant_id"], payload)

@router.get("/{report_id}/artifacts/{artifact_name}")
def download_artifact(
    report_id: str, 
    artifact_name: str, 
    x_api_key: str | None = Header(default=None), 
    db: Session = Depends(get_db)
):
    auth = authenticate_api_key(db, x_api_key, required_scope="reports:read")
    report = ReportService.get_report(db, auth["tenant_id"], report_id)
    content = ReportService.get_artifact(report, artifact_name)
    
    media_type = "application/json" if artifact_name.endswith(".json") else "text/markdown"
    return Response(content=content, media_type=media_type)
