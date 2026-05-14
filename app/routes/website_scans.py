from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import ReportCreate, WebsiteScanConvertResponse, WebsiteScanCreate, WebsiteScanReportResponse, WebsiteScanResponse
from app.services.auth_service import authenticate_api_key
from app.services.entitlement_service import check_entitlement
from app.services.report_service import ReportService
from app.services.website_scanner_service import WebsiteScannerService

router = APIRouter(prefix="/v1/website-scans", tags=["Website Compliance Scanner"])


@router.post("", response_model=WebsiteScanResponse)
async def create_website_scan(
    payload: WebsiteScanCreate,
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="scanner:write")
    return await WebsiteScannerService.create_scan(db, auth["tenant_id"], payload)


@router.get("", response_model=List[WebsiteScanResponse])
def list_website_scans(
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="scanner:read")
    return WebsiteScannerService.list_scans(db, auth["tenant_id"])


@router.get("/{scan_id}", response_model=WebsiteScanResponse)
def get_website_scan(
    scan_id: str,
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="scanner:read")
    return WebsiteScannerService.get_scan(db, auth["tenant_id"], scan_id)


@router.post("/{scan_id}/convert", response_model=WebsiteScanConvertResponse)
def convert_website_scan(
    scan_id: str,
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="scanner:write")
    scan, system, intake, controls, evidence_event_id = WebsiteScannerService.convert_scan(db, auth["tenant_id"], scan_id)
    return {
        "scan": scan,
        "ai_system": system,
        "intake": intake,
        "controls": controls,
        "evidence_event_id": evidence_event_id,
    }


@router.post("/{scan_id}/report", response_model=WebsiteScanReportResponse)
def generate_website_scan_report(
    scan_id: str,
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="reports:write")
    if not check_entitlement(db, auth["tenant_id"], "report_generation"):
        raise HTTPException(status_code=403, detail="Report generation not entitled for this tenant")
    scan, system, intake, controls, evidence_event_id = WebsiteScannerService.convert_scan(db, auth["tenant_id"], scan_id)
    report = ReportService.generate_report(
        db,
        auth["tenant_id"],
        ReportCreate(
            report_type="compliance_readiness_summary",
            title=f"{system.name} Website Compliance Readiness Report",
            ai_system_id=system.id,
            source_refs=[
                {"type": "website_scan", "id": scan.id, "url": scan.normalized_url},
                {"type": "intake", "id": intake.id, "classification": intake.system_classification},
                {"type": "evidence_log", "id": evidence_event_id, "domain": "website_scan"},
            ],
        ),
    )
    return {
        "scan": scan,
        "ai_system": system,
        "intake": intake,
        "controls": controls,
        "evidence_event_id": evidence_event_id,
        "report": report,
    }
