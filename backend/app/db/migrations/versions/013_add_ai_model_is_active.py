"""Add is_active column to ai_models

Revision ID: 013_add_ai_model_is_active
Revises: 012_add_stories
Create Date: 2026-05-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '013_add_ai_model_is_active'
down_revision = '012_add_stories'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'ai_models',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    op.drop_column('ai_models', 'is_active')
