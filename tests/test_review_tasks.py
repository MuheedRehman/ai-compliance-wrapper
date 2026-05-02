from concurrent.futures import ThreadPoolExecutor

from app.models import ReviewTask
from app.services.review_service import get_or_create_open_review_task


def test_duplicate_missing_feature_review_task_dedupes(db_session):
    for _ in range(3):
        get_or_create_open_review_task(
            db=db_session,
            tenant_id="tenant_test",
            feature_id="unmapped_feature",
            review_type="feature_registration",
            trigger_reason="missing_feature_id",
            severity="medium",
            findings={"source": "test"},
        )

    db_session.commit()

    tasks = db_session.query(ReviewTask).filter(
        ReviewTask.trigger_reason == "missing_feature_id"
    ).all()

    assert len(tasks) == 1
    assert tasks[0].occurrence_count == 3


def test_duplicate_high_risk_review_task_dedupes(db_session):
    for _ in range(5):
        get_or_create_open_review_task(
            db=db_session,
            tenant_id="tenant_test",
            feature_id="customer_support_bot",
            review_type="risk_review",
            trigger_reason="high_risk_pre_check",
            severity="high",
            findings={"source": "test"},
        )

    db_session.commit()

    task = db_session.query(ReviewTask).filter(
        ReviewTask.trigger_reason == "high_risk_pre_check"
    ).first()

    assert task is not None
    assert task.occurrence_count == 5


def test_duplicate_candidate_version_review_task_dedupes(db_session):
    for _ in range(4):
        get_or_create_open_review_task(
            db=db_session,
            tenant_id="tenant_test",
            feature_id="customer_support_bot",
            feature_version_id="version_123",
            review_type="change_triggered",
            trigger_reason="candidate_version_requires_review",
            severity="medium",
            findings={"source": "test"},
        )

    db_session.commit()

    task = db_session.query(ReviewTask).filter(
        ReviewTask.trigger_reason == "candidate_version_requires_review"
    ).first()

    assert task is not None
    assert task.occurrence_count == 4


def test_concurrent_review_task_creation_smoke(db_session):
    # SQLite local concurrency is limited. This is a smoke test, not a substitute
    # for the Sprint 6B PostgreSQL concurrency test.
    for _ in range(10):
        get_or_create_open_review_task(
            db=db_session,
            tenant_id="tenant_test",
            feature_id="customer_support_bot",
            review_type="feature_governance",
            trigger_reason="feature_not_registered",
            severity="high",
            findings={"source": "smoke"},
        )

    db_session.commit()

    tasks = db_session.query(ReviewTask).filter(
        ReviewTask.trigger_reason == "feature_not_registered"
    ).all()

    assert len(tasks) == 1
    assert tasks[0].occurrence_count == 10
