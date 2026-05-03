import pytest
from sqlalchemy import text

from app.db import engine


pytestmark = pytest.mark.skipif(
    engine.dialect.name != "postgresql",
    reason="PostgreSQL-only migration/index tests",
)


def test_postgres_partial_indexes_exist():
    with engine.connect() as conn:
        result = conn.execute(text(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND indexname IN (
                'uq_one_approved_version_per_feature',
                'uq_open_review_task_no_version',
                'uq_open_review_task_with_version'
              )
            """
        ))
        indexes = {row[0] for row in result}

    assert "uq_one_approved_version_per_feature" in indexes
    assert "uq_open_review_task_no_version" in indexes
    assert "uq_open_review_task_with_version" in indexes
