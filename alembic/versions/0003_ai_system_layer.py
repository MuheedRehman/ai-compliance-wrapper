"""ai_system_layer

Revision ID: 0003
Revises: 0002_pg_indexes
Create Date: 2026-05-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, None] = '0002_pg_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"
    # 1. Create ai_systems table
    op.create_table(
        'ai_systems',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('deployment_status', sa.String(), server_default='draft', nullable=False),
        sa.Column('registration_status', sa.String(), server_default='draft', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_systems_id'), 'ai_systems', ['id'], unique=False)
    op.create_index(op.f('ix_ai_systems_tenant_id'), 'ai_systems', ['tenant_id'], unique=False)

    # 2. Create fria_records table
    op.create_table(
        'fria_records',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('ai_system_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='draft'),
        sa.Column('assessment_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['ai_system_id'], ['ai_systems.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fria_records_id'), 'fria_records', ['id'], unique=False)
    op.create_index(op.f('ix_fria_records_tenant_id'), 'fria_records', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_fria_records_ai_system_id'), 'fria_records', ['ai_system_id'], unique=False)

    # 3. Create oversight_assignments table
    op.create_table(
        'oversight_assignments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('ai_system_id', sa.String(), nullable=False),
        sa.Column('reviewer_email', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['ai_system_id'], ['ai_systems.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_oversight_assignments_id'), 'oversight_assignments', ['id'], unique=False)
    op.create_index(op.f('ix_oversight_assignments_tenant_id'), 'oversight_assignments', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_oversight_assignments_ai_system_id'), 'oversight_assignments', ['ai_system_id'], unique=False)

    # 4. Create incident_records table
    op.create_table(
        'incident_records',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('ai_system_id', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='open'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['ai_system_id'], ['ai_systems.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_incident_records_id'), 'incident_records', ['id'], unique=False)
    op.create_index(op.f('ix_incident_records_tenant_id'), 'incident_records', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_incident_records_ai_system_id'), 'incident_records', ['ai_system_id'], unique=False)

    # 5. Create evidence_bundles table
    op.create_table(
        'evidence_bundles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('ai_system_id', sa.String(), nullable=True),
        sa.Column('bundle_hash', sa.String(), nullable=False),
        sa.Column('bundle_url', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['ai_system_id'], ['ai_systems.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evidence_bundles_id'), 'evidence_bundles', ['id'], unique=False)
    op.create_index(op.f('ix_evidence_bundles_tenant_id'), 'evidence_bundles', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_evidence_bundles_ai_system_id'), 'evidence_bundles', ['ai_system_id'], unique=False)

    # 6. Add columns to existing tables
    op.add_column('ai_features', sa.Column('ai_system_id', sa.String(), nullable=True))
    op.create_index(op.f('ix_ai_features_ai_system_id'), 'ai_features', ['ai_system_id'], unique=False)
    if not is_sqlite:
        op.create_foreign_key('fk_ai_features_ai_system_id', 'ai_features', 'ai_systems', ['ai_system_id'], ['id'])

    op.add_column('evidence_logs', sa.Column('ai_system_id', sa.String(), nullable=True))
    op.add_column('evidence_logs', sa.Column('evidence_domain', sa.String(), nullable=True))
    op.create_index(op.f('ix_evidence_logs_ai_system_id'), 'evidence_logs', ['ai_system_id'], unique=False)
    op.create_index(op.f('ix_evidence_logs_evidence_domain'), 'evidence_logs', ['evidence_domain'], unique=False)
    if not is_sqlite:
        op.create_foreign_key('fk_evidence_logs_ai_system_id', 'evidence_logs', 'ai_systems', ['ai_system_id'], ['id'])

    op.add_column('review_tasks', sa.Column('ai_system_id', sa.String(), nullable=True))
    op.create_index(op.f('ix_review_tasks_ai_system_id'), 'review_tasks', ['ai_system_id'], unique=False)
    if not is_sqlite:
        op.create_foreign_key('fk_review_tasks_ai_system_id', 'review_tasks', 'ai_systems', ['ai_system_id'], ['id'])


def downgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"

    if not is_sqlite:
        op.drop_constraint('fk_review_tasks_ai_system_id', 'review_tasks', type_='foreignkey')
    op.drop_index(op.f('ix_review_tasks_ai_system_id'), table_name='review_tasks')
    op.drop_column('review_tasks', 'ai_system_id')

    if not is_sqlite:
        op.drop_constraint('fk_evidence_logs_ai_system_id', 'evidence_logs', type_='foreignkey')
    op.drop_index(op.f('ix_evidence_logs_evidence_domain'), table_name='evidence_logs')
    op.drop_index(op.f('ix_evidence_logs_ai_system_id'), table_name='evidence_logs')
    op.drop_column('evidence_logs', 'evidence_domain')
    op.drop_column('evidence_logs', 'ai_system_id')

    if not is_sqlite:
        op.drop_constraint('fk_ai_features_ai_system_id', 'ai_features', type_='foreignkey')
    op.drop_index(op.f('ix_ai_features_ai_system_id'), table_name='ai_features')
    op.drop_column('ai_features', 'ai_system_id')

    op.drop_table('evidence_bundles')
    op.drop_table('incident_records')
    op.drop_table('oversight_assignments')
    op.drop_table('fria_records')
    op.drop_table('ai_systems')
