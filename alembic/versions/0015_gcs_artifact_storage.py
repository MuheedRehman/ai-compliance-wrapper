"""GCS artifact storage: make content_bytes nullable for external storage backends

Revision ID: 0015
Revises: 0014
Create Date: 2026-06-20 00:00:00.000000

Changes:
- evidence_artifacts.content_bytes becomes nullable so GCS-backed artifacts
  don't duplicate bytes in the database.
- storage_backend='gcs' rows will have content_bytes=NULL; 'database' rows keep
  their bytes unchanged (backward compatible).
"""
from typing import Optional, Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0015"
down_revision: Optional[str] = "0014"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    op.alter_column(
        "evidence_artifacts",
        "content_bytes",
        existing_type=sa.LargeBinary(),
        nullable=True,
    )


def downgrade() -> None:
    # Back-fill NULL bytes before flipping nullable=False to avoid integrity errors.
    op.execute(
        "UPDATE evidence_artifacts SET content_bytes = '' WHERE content_bytes IS NULL"
    )
    op.alter_column(
        "evidence_artifacts",
        "content_bytes",
        existing_type=sa.LargeBinary(),
        nullable=False,
    )
