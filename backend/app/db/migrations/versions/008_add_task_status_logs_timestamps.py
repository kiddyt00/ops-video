"""Add created_at and updated_at to task_status_logs

Revision ID: 008_fix_logs_ts
Revises: 007_add_user_extra_fields
Create Date: 2026-05-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '008_fix_logs_ts'
down_revision = '007_add_user_extra_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('task_status_logs', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('task_status_logs', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.execute("UPDATE task_status_logs SET created_at = NOW(), updated_at = NOW() WHERE created_at IS NULL")
    op.alter_column('task_status_logs', 'created_at', nullable=False)
    op.alter_column('task_status_logs', 'updated_at', nullable=False)


def downgrade() -> None:
    op.drop_column('task_status_logs', 'updated_at')
    op.drop_column('task_status_logs', 'created_at')
