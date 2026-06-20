import hashlib
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import AiSystem, ComplianceControl, EvidenceArtifact, EvidenceItem
from app.schemas import EvidenceItemCreate, EvidenceItemUpdate
from app.services.hashing import hash_object, hmac_signature
from app.services import gcs_storage


MAX_ARTIFACT_BYTES = 5 * 1024 * 1024
PREVIEWABLE_EXACT_CONTENT_TYPES = {
    "application/json",
    "application/pdf",
    "application/xml",
    "text/csv",
    "text/markdown",
    "text/plain",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _seal_item(item: EvidenceItem) -> None:
    fingerprint = {
        "id": item.id,
        "tenant_id": item.tenant_id,
        "ai_system_id": item.ai_system_id,
        "control_id": item.control_id,
        "title": item.title,
        "description": item.description,
        "evidence_type": item.evidence_type,
        "source": item.source,
        "source_url": item.source_url,
        "owner_email": item.owner_email,
        "status": item.status,
        "collected_at": _aware(item.collected_at).isoformat() if item.collected_at else None,
        "review_at": _aware(item.review_at).isoformat() if item.review_at else None,
        "expires_at": _aware(item.expires_at).isoformat() if item.expires_at else None,
        "metadata_json": item.metadata_json or {},
    }
    item.evidence_hash = hash_object(fingerprint)
    item.hmac_signature = hmac_signature({
        "evidence_item_id": item.id,
        "tenant_id": item.tenant_id,
        "evidence_hash": item.evidence_hash,
    })


def _clean_file_name(file_name: str | None) -> str:
    cleaned = (file_name or "evidence-artifact").replace("\\", "/").split("/")[-1].strip()
    cleaned = cleaned.replace("\r", "").replace("\n", "")
    cleaned = cleaned.replace('"', "")
    return cleaned[:180] or "evidence-artifact"


def _artifact_summary(artifact: EvidenceArtifact) -> dict:
    return {
        "id": artifact.id,
        "file_name": artifact.file_name,
        "content_type": artifact.content_type,
        "size_bytes": artifact.size_bytes,
        "artifact_hash": artifact.artifact_hash,
        "storage_backend": artifact.storage_backend,
        "storage_key": artifact.storage_key,
        "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
    }


def _base_content_type(content_type: str | None) -> str:
    return (content_type or "application/octet-stream").split(";", 1)[0].strip().lower()


class EvidenceVaultService:
    @staticmethod
    def _resolve_links(
        db: Session,
        tenant_id: str,
        ai_system_id: Optional[str],
        control_id: Optional[str],
    ) -> tuple[Optional[str], Optional[str]]:
        if ai_system_id:
            system = db.query(AiSystem).filter(
                AiSystem.tenant_id == tenant_id,
                AiSystem.id == ai_system_id,
            ).first()
            if not system:
                raise HTTPException(status_code=404, detail="AI system not found")

        if control_id:
            control = db.query(ComplianceControl).filter(
                ComplianceControl.tenant_id == tenant_id,
                ComplianceControl.id == control_id,
            ).first()
            if not control:
                raise HTTPException(status_code=404, detail="Compliance control not found")
            if control.ai_system_id and ai_system_id and control.ai_system_id != ai_system_id:
                raise HTTPException(status_code=400, detail="Control belongs to a different AI system")
            if control.ai_system_id and not ai_system_id:
                ai_system_id = control.ai_system_id

        return ai_system_id, control_id

    @staticmethod
    def create_item(db: Session, tenant_id: str, payload: EvidenceItemCreate) -> EvidenceItem:
        ai_system_id, control_id = EvidenceVaultService._resolve_links(
            db,
            tenant_id,
            payload.ai_system_id,
            payload.control_id,
        )

        item = EvidenceItem(
            id=f"evi-{uuid.uuid4().hex[:10]}",
            tenant_id=tenant_id,
            ai_system_id=ai_system_id,
            control_id=control_id,
            title=payload.title,
            description=payload.description,
            evidence_type=payload.evidence_type,
            source=payload.source,
            source_url=payload.source_url,
            owner_email=payload.owner_email,
            status=payload.status,
            collected_at=payload.collected_at or _now(),
            review_at=payload.review_at,
            expires_at=payload.expires_at,
            metadata_json=payload.metadata_json,
            evidence_hash="pending",
            hmac_signature="pending",
        )
        _seal_item(item)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def list_items(
        db: Session,
        tenant_id: str,
        ai_system_id: Optional[str] = None,
        control_id: Optional[str] = None,
        evidence_type: Optional[str] = None,
        status: Optional[str] = None,
        owner_email: Optional[str] = None,
        limit: int = 100,
    ) -> list[EvidenceItem]:
        query = db.query(EvidenceItem).filter(EvidenceItem.tenant_id == tenant_id)
        if ai_system_id:
            query = query.filter(EvidenceItem.ai_system_id == ai_system_id)
        if control_id:
            query = query.filter(EvidenceItem.control_id == control_id)
        if evidence_type:
            query = query.filter(EvidenceItem.evidence_type == evidence_type)
        if status:
            query = query.filter(EvidenceItem.status == status)
        if owner_email:
            query = query.filter(EvidenceItem.owner_email == owner_email)

        return (
            query.order_by(EvidenceItem.created_at.desc(), EvidenceItem.id.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_item(db: Session, tenant_id: str, item_id: str) -> EvidenceItem:
        item = db.query(EvidenceItem).filter(
            EvidenceItem.tenant_id == tenant_id,
            EvidenceItem.id == item_id,
        ).first()
        if not item:
            raise HTTPException(status_code=404, detail="Evidence item not found")
        return item

    @staticmethod
    def attach_item_to_control(
        db: Session,
        tenant_id: str,
        item_id: str,
        control_id: str,
    ) -> EvidenceItem:
        control = db.query(ComplianceControl).filter(
            ComplianceControl.tenant_id == tenant_id,
            ComplianceControl.id == control_id,
        ).first()
        if not control:
            raise HTTPException(status_code=404, detail="Compliance control not found")

        item = EvidenceVaultService.get_item(db, tenant_id, item_id)
        if item.ai_system_id and control.ai_system_id and item.ai_system_id != control.ai_system_id:
            raise HTTPException(status_code=400, detail="Evidence item belongs to a different AI system")

        previous_control_id = item.control_id
        if control.ai_system_id and not item.ai_system_id:
            item.ai_system_id = control.ai_system_id
        item.control_id = control.id

        metadata_json = dict(item.metadata_json or {})
        attachment_event = {
            "control_id": control.id,
            "previous_control_id": previous_control_id,
            "ai_system_id": item.ai_system_id,
            "attached_at": _now().isoformat(),
            "source": "control_evidence_attachment",
        }
        history = [
            entry for entry in metadata_json.get("control_attachment_history", [])
            if isinstance(entry, dict)
        ]
        metadata_json["control_attachment_history"] = [attachment_event, *history][:10]
        metadata_json["latest_control_attachment"] = attachment_event
        item.metadata_json = metadata_json

        _seal_item(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def update_item(db: Session, tenant_id: str, item_id: str, payload: EvidenceItemUpdate) -> EvidenceItem:
        item = EvidenceVaultService.get_item(db, tenant_id, item_id)
        update_data = payload.model_dump(exclude_unset=True)

        next_ai_system_id = update_data.get("ai_system_id", item.ai_system_id)
        next_control_id = update_data.get("control_id", item.control_id)
        next_ai_system_id, next_control_id = EvidenceVaultService._resolve_links(
            db,
            tenant_id,
            next_ai_system_id,
            next_control_id,
        )
        update_data["ai_system_id"] = next_ai_system_id
        update_data["control_id"] = next_control_id

        for key, value in update_data.items():
            setattr(item, key, value)

        _seal_item(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def attach_artifact(
        db: Session,
        tenant_id: str,
        item_id: str,
        *,
        file_name: str,
        content_type: str | None,
        content: bytes,
        metadata: Optional[dict] = None,
    ) -> EvidenceArtifact:
        item = EvidenceVaultService.get_item(db, tenant_id, item_id)
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded evidence artifact is empty")
        if len(content) > MAX_ARTIFACT_BYTES:
            raise HTTPException(status_code=413, detail="Evidence artifacts are limited to 5 MB in this staging upload flow")

        artifact_id = f"art-{uuid.uuid4().hex[:10]}"
        artifact_hash = hashlib.sha256(content).hexdigest()
        storage_key = f"evidence/{tenant_id}/{item_id}/{artifact_id}/{_clean_file_name(file_name)}"
        resolved_content_type = content_type or "application/octet-stream"
        use_gcs = gcs_storage.is_configured()
        if use_gcs:
            gcs_storage.upload(storage_key, content, resolved_content_type)

        artifact = EvidenceArtifact(
            id=artifact_id,
            tenant_id=tenant_id,
            evidence_item_id=item_id,
            file_name=_clean_file_name(file_name),
            content_type=resolved_content_type,
            size_bytes=len(content),
            artifact_hash=artifact_hash,
            hmac_signature=hmac_signature({
                "evidence_artifact_id": artifact_id,
                "tenant_id": tenant_id,
                "evidence_item_id": item_id,
                "artifact_hash": artifact_hash,
            }),
            storage_backend="gcs" if use_gcs else "database",
            storage_key=storage_key,
            content_bytes=None if use_gcs else content,
            metadata_json=metadata or {"source": "evidence_vault_upload"},
        )
        db.add(artifact)
        db.flush()

        metadata_json = dict(item.metadata_json or {})
        existing_artifacts = [
            entry for entry in metadata_json.get("artifacts", [])
            if isinstance(entry, dict) and entry.get("id") != artifact.id
        ]
        metadata_json["artifacts"] = [_artifact_summary(artifact), *existing_artifacts]
        metadata_json["artifact_count"] = len(metadata_json["artifacts"])
        metadata_json["latest_artifact_hash"] = artifact_hash
        item.metadata_json = metadata_json
        _seal_item(item)

        db.commit()
        db.refresh(artifact)
        db.refresh(item)
        return artifact

    @staticmethod
    def get_artifact(
        db: Session,
        tenant_id: str,
        item_id: str,
        artifact_id: str,
    ) -> EvidenceArtifact:
        artifact = (
            db.query(EvidenceArtifact)
            .filter(
                EvidenceArtifact.tenant_id == tenant_id,
                EvidenceArtifact.evidence_item_id == item_id,
                EvidenceArtifact.id == artifact_id,
            )
            .first()
        )
        if not artifact:
            raise HTTPException(status_code=404, detail="Evidence artifact not found")
        return artifact

    @staticmethod
    def get_previewable_artifact(
        db: Session,
        tenant_id: str,
        item_id: str,
        artifact_id: str,
    ) -> EvidenceArtifact:
        artifact = EvidenceVaultService.get_artifact(db, tenant_id, item_id, artifact_id)
        base_type = _base_content_type(artifact.content_type)
        if not (
            base_type.startswith("image/")
            or base_type.startswith("text/")
            or base_type in PREVIEWABLE_EXACT_CONTENT_TYPES
        ):
            raise HTTPException(status_code=415, detail="Evidence artifact type is not previewable")
        return artifact

    @staticmethod
    def read_artifact_content(artifact: EvidenceArtifact) -> bytes:
        if artifact.storage_backend == "gcs":
            return gcs_storage.download(artifact.storage_key)
        return artifact.content_bytes or b""

    @staticmethod
    def download_artifact_bytes(
        db: Session,
        tenant_id: str,
        item_id: str,
        artifact_id: str,
    ) -> bytes:
        artifact = EvidenceVaultService.get_artifact(db, tenant_id, item_id, artifact_id)
        return EvidenceVaultService.read_artifact_content(artifact)

    @staticmethod
    def get_artifact_signed_url(
        db: Session,
        tenant_id: str,
        item_id: str,
        artifact_id: str,
        expiry_seconds: int = 3600,
    ) -> str | None:
        artifact = EvidenceVaultService.get_artifact(db, tenant_id, item_id, artifact_id)
        if artifact.storage_backend != "gcs":
            return None
        return gcs_storage.signed_url(artifact.storage_key, expiry_seconds)

    @staticmethod
    def summary(db: Session, tenant_id: str, ai_system_id: Optional[str] = None) -> dict:
        items = EvidenceVaultService.list_items(db, tenant_id, ai_system_id=ai_system_id, limit=500)
        now = _now()
        soon = now + timedelta(days=30)
        status_counts = Counter(item.status for item in items)
        type_counts = Counter(item.evidence_type for item in items)

        return {
            "tenant_id": tenant_id,
            "ai_system_id": ai_system_id,
            "total_items": len(items),
            "linked_system_count": len({item.ai_system_id for item in items if item.ai_system_id}),
            "due_for_review_count": sum(
                1 for item in items if item.review_at and _aware(item.review_at) <= now
            ),
            "expiring_soon_count": sum(
                1 for item in items if item.expires_at and now <= _aware(item.expires_at) <= soon
            ),
            "items_by_status": dict(status_counts),
            "items_by_type": dict(type_counts),
        }
