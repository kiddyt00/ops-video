"""rename owner_id to user_id in projects (no-op: fresh installs already have user_id)

Revision ID: 006_rename_owner_id_to_user_id
Revises: 005_add_project_soft_delete
Create Date: 2026-04-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006_rename_owner_id_to_user_id'
down_revision = '005_add_project_soft_delete'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Column is already user_id in fresh installs (001 creates it as user_id)
    # Only add index if it doesn't exist
    op.create_index('ix_projects_user_id', 'projects', ['user_id'], if_not_exists=True)


def downgrade() -> None:
    op.drop_index('ix_projects_user_id', 'projects')
