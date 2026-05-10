"""Add login_count and metainfo columns to users

Revision ID: 007_add_user_extra_fields
Revises: 006_rename_owner_id_to_user_id
Create Date: 2026-05-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '007_add_user_extra_fields'
down_revision = '006_rename_owner_id_to_user_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('login_count', sa.String(50), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('metainfo', sa.JSON, nullable=False, server_default='{}'))


def downgrade() -> None:
    op.drop_column('users', 'metainfo')
    op.drop_column('users', 'login_count')
