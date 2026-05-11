"""Add storage_providers table

Revision ID: 011_add_storage_providers
Revises: 010_add_character_cards
Create Date: 2026-05-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '011_add_storage_providers'
down_revision = '010_add_character_cards'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'storage_providers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('provider_type', sa.String(50), nullable=False),
        sa.Column('access_key', sa.String(500), nullable=False),
        sa.Column('secret_key', sa.String(500), nullable=False),
        sa.Column('bucket', sa.String(255), nullable=False),
        sa.Column('endpoint', sa.String(500), nullable=True),
        sa.Column('region', sa.String(100), nullable=True),
        sa.Column('path_prefix', sa.String(500), nullable=True),
        sa.Column('extra_config', postgresql.JSON, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_default', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('last_tested_at', sa.DateTime, nullable=True),
        sa.Column('last_test_status', sa.String(50), nullable=True),
        sa.Column('last_test_error', sa.Text, nullable=True),
        sa.Column('test_history', postgresql.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    op.create_index(op.f('ix_storage_providers_name'), 'storage_providers', ['name'], unique=True)


def downgrade() -> None:
    op.drop_table('storage_providers')
