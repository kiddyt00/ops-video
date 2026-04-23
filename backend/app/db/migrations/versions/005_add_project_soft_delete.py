"""Add soft delete to projects

Revision ID: 005_add_project_soft_delete
Revises: 004_add_parameter_presets
Create Date: 2026-04-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005_add_project_soft_delete'
down_revision = '004_add_parameter_presets'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('projects', sa.Column('is_deleted', sa.Boolean, nullable=False, server_default='false'))
    op.add_column('projects', sa.Column('deleted_at', sa.DateTime, nullable=True))
    op.create_index('ix_projects_is_deleted', 'projects', ['is_deleted'])


def downgrade() -> None:
    op.drop_index('ix_projects_is_deleted', 'projects')
    op.drop_column('projects', 'deleted_at')
    op.drop_column('projects', 'is_deleted')
