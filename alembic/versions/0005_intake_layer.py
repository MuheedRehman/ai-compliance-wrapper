"""intake layer

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-10 16:05:00.000000

"""
from typing import Sequence, Optional
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0005'
down_revision: Optional[str] = '0004'
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    op.create_table(
        'intake_assessments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('answers_json', sa.JSON(), nullable=False),
        sa.Column('actor_role', sa.String(), nullable=False),
        sa.Column('system_classification', sa.String(), nullable=False),
        sa.Column('obligation_path', sa.String(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_intake_assessments_id'), 'intake_assessments', ['id'], unique=False)
    op.create_index(op.f('ix_intake_assessments_tenant_id'), 'intake_assessments', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_intake_assessments_tenant_id'), table_name='intake_assessments')
    op.drop_index(op.f('ix_intake_assessments_id'), table_name='intake_assessments')
    op.drop_table('intake_assessments')
