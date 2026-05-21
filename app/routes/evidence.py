from typing import List, Optional

from fastapi import APIRouter, Depends, File, Header, Query, Response, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import (
    EvidenceArtifactResponse,
    EvidenceItemCreate,
    EvidenceItemResponse,
    EvidenceItemUpdate,
    EvidenceVaultSummaryResponse,
)
from app.services.auth_service import authenticate_api_key
from app.services.evidence_vault_service import EvidenceVaultService


router = APIRouter(prefix="/v1/evidence", tags=["Evidence Vault"])


@router.get("/items", response_model=List[EvidenceItemResponse])
def list_evidence_items(
    ai_system_id: Optional[str] = Query(default=None),
    control_id: Optional[str] = Query(default=None),
    evidence_type: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    owner_email: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="evidence:read")
    return EvidenceVaultService.list_items(
        db,
        auth["tenant_id"],
        ai_system_id=ai_system_id,
        control_id=control_id,
        evidence_type=evidence_type,
        status=status,
        owner_email=owner_email,
        limit=limit,
    )


@router.get("/summary", response_model=EvidenceVaultSummaryResponse)
def get_evidence_summary(
    ai_system_id: Optional[str] = Query(default=None),
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="evidence:read")
    return EvidenceVaultService.summary(db, auth["tenant_id"], ai_system_id)


@router.post("/items", response_model=EvidenceItemResponse)
def create_evidence_item(
    payload: EvidenceItemCreate,
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="evidence:write")
    return EvidenceVaultService.create_item(db, auth["tenant_id"], payload)


@router.patch("/items/{item_id}", response_model=EvidenceItemResponse)
def update_evidence_item(
    item_id: str,
    payload: EvidenceItemUpdate,
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="evidence:write")
    return EvidenceVaultService.update_item(db, auth["tenant_id"], item_id, payload)


@router.post("/items/{item_id}/artifacts", response_model=EvidenceArtifactResponse)
async def upload_evidence_artifact(
    item_id: str,
    file: UploadFile = File(...),
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="evidence:write")
    content = await file.read()
    return EvidenceVaultService.attach_artifact(
        db,
        auth["tenant_id"],
        item_id,
        file_name=file.filename or "evidence-artifact",
        content_type=file.content_type,
        content=content,
    )


@router.get("/items/{item_id}/artifacts/{artifact_id}/download")
def download_evidence_artifact(
    item_id: str,
    artifact_id: str,
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="evidence:read")
    artifact = EvidenceVaultService.get_artifact(db, auth["tenant_id"], item_id, artifact_id)
    return Response(
        content=artifact.content_bytes,
        media_type=artifact.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{artifact.file_name}"',
            "X-Evidence-Artifact-Hash": artifact.artifact_hash,
            "X-Evidence-Artifact-Signature": artifact.hmac_signature,
        },
    )
