"""Add ai_models table

Revision ID: 009_add_ai_models
Revises: 008_fix_logs_ts
Create Date: 2026-05-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '009_fix_logs_ts'
down_revision = '008_fix_logs_ts'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'ai_models',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('category', sa.String(50), nullable=False, index=True),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('api_key', sa.Text, nullable=True),
        sa.Column('api_base_url', sa.String(500), nullable=True),
        sa.Column('is_enabled', sa.Boolean, default=True, nullable=False),
        sa.Column('is_builtin', sa.Boolean, default=False, nullable=False),
        sa.Column('config', sa.JSON, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table('ai_models')
