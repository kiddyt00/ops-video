"""Add project_shares table

Revision ID: 003_add_project_shares
Revises: 002_add_users
Create Date: 2026-04-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_add_project_shares'
down_revision = '002_add_users'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'project_shares',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('owner_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('shared_with_user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('permission', sa.String(20), nullable=False, server_default='view'),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.UniqueConstraint('project_id', 'shared_with_user_id', name='uq_project_share_user'),
    )
    op.create_index('ix_project_shares_project_id', 'project_shares', ['project_id'])
    op.create_index('ix_project_shares_owner_id', 'project_shares', ['owner_id'])
    op.create_index('ix_project_shares_shared_with_user_id', 'project_shares', ['shared_with_user_id'])


def downgrade() -> None:
    op.drop_table('project_shares')
