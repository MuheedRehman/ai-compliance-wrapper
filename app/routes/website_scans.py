from typing import List

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import WebsiteScanConvertResponse, WebsiteScanCreate, WebsiteScanResponse
from app.services.auth_service import authenticate_api_key
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
    scan, system, intake = WebsiteScannerService.convert_scan(db, auth["tenant_id"], scan_id)
    return {
        "scan": scan,
        "ai_system": system,
        "intake": intake,
    }
