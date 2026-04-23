"""Add parameter_presets table

Revision ID: 004_add_parameter_presets
Revises: 003_add_project_shares
Create Date: 2026-04-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_add_parameter_presets'
down_revision = '003_add_project_shares'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'parameter_presets',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('generator_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('parameters', sa.JSON, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    op.create_index('ix_parameter_presets_generator_type', 'parameter_presets', ['generator_type'])
    op.create_index('ix_parameter_presets_user_id', 'parameter_presets', ['user_id'])


def downgrade() -> None:
    op.drop_table('parameter_presets')
