"""fria builder sections and approval workflow

Revision ID: 0013
Revises: 0012
Create Date: 2026-06-04 00:00:00.000000

"""
from typing import Optional, Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0013"
down_revision: Optional[str] = "0012"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    op.add_column("fria_records", sa.Column("sections_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
    op.add_column("fria_records", sa.Column("approval_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
    op.add_column("fria_records", sa.Column("completion_percent", sa.Integer(), nullable=False, server_default=sa.text("0")))


def downgrade() -> None:
    op.drop_column("fria_records", "completion_percent")
    op.drop_column("fria_records", "approval_json")
    op.drop_column("fria_records", "sections_json")
