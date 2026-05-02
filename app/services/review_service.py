from datetime import datetime, timezone
import uuid
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models import ReviewTask


def get_or_create_open_review_task(
    db: Session,
    tenant_id: str,
    feature_id: str | None,
    review_type: str,
    trigger_reason: str,
    severity: str = "medium",
    findings: dict | None = None,
    feature_pk: str | None = None,
    feature_version_id: str | None = None,
) -> ReviewTask:
    # Code-level dedupe is primary because nullable unique constraints behave differently across DBs.
    task = (
        db.query(ReviewTask)
        .filter(
            ReviewTask.tenant_id == tenant_id,
            ReviewTask.feature_id == feature_id,
            ReviewTask.feature_pk == feature_pk,
            ReviewTask.feature_version_id == feature_version_id,
            ReviewTask.review_type == review_type,
            ReviewTask.trigger_reason == trigger_reason,
            ReviewTask.status == "open",
        )
        .first()
    )

    if task:
        task.occurrence_count += 1
        task.last_seen_at = datetime.now(timezone.utc)
        task.findings_json = {
            **(task.findings_json or {}),
            "latest": findings or {},
        }
        db.flush()
        return task

    # Savepoint: failed insert does not poison the surrounding transaction.
    try:
        with db.begin_nested():
            task = ReviewTask(
                review_task_id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                feature_id=feature_id,
                feature_pk=feature_pk,
                feature_version_id=feature_version_id,
                review_type=review_type,
                trigger_reason=trigger_reason,
                severity=severity,
                status="open",
                occurrence_count=1,
                findings_json=findings or {},
                last_seen_at=datetime.now(timezone.utc),
            )
            db.add(task)
            db.flush()
    except IntegrityError:
        task = (
            db.query(ReviewTask)
            .filter(
                ReviewTask.tenant_id == tenant_id,
                ReviewTask.feature_id == feature_id,
                ReviewTask.feature_pk == feature_pk,
                ReviewTask.feature_version_id == feature_version_id,
                ReviewTask.review_type == review_type,
                ReviewTask.trigger_reason == trigger_reason,
                ReviewTask.status == "open",
            )
            .first()
        )
        if not task:
            raise
        task.occurrence_count += 1
        task.last_seen_at = datetime.now(timezone.utc)
        task.findings_json = {
            **(task.findings_json or {}),
            "latest": findings or {},
        }
        db.flush()

    return task
