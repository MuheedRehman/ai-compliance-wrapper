"""billing layer

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-09 20:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'tenant_subscriptions',
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('stripe_customer_id', sa.String(), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(), nullable=True),
        sa.Column('plan_id', sa.String(), nullable=False, server_default='free'),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id'], ),
        sa.PrimaryKeyConstraint('tenant_id')
    )
    op.create_index(op.f('ix_tenant_subscriptions_stripe_customer_id'), 'tenant_subscriptions', ['stripe_customer_id'], unique=False)
    op.create_index(op.f('ix_tenant_subscriptions_stripe_subscription_id'), 'tenant_subscriptions', ['stripe_subscription_id'], unique=False)

    op.create_table(
        'entitlements',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('feature_key', sa.String(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=True, default=False),
        sa.Column('limit_value', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_entitlements_tenant_id'), 'entitlements', ['tenant_id'], unique=False)

    op.create_table(
        'usage_meters',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False, default=1),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usage_meters_tenant_id'), 'usage_meters', ['tenant_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_usage_meters_tenant_id'), table_name='usage_meters')
    op.drop_table('usage_meters')
    op.drop_index(op.f('ix_entitlements_tenant_id'), table_name='entitlements')
    op.drop_table('entitlements')
    op.drop_index(op.f('ix_tenant_subscriptions_stripe_subscription_id'), table_name='tenant_subscriptions')
    op.drop_index(op.f('ix_tenant_subscriptions_stripe_customer_id'), table_name='tenant_subscriptions')
    op.drop_table('tenant_subscriptions')
