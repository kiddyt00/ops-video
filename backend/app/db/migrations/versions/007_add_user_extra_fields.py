"""Fix column name: rename metadata to metainfo in users

Revision ID: 007_add_user_extra_fields
Revises: 006_rename_owner_id_to_user_id
Create Date: 2026-05-10 00:00:00.000000

"""
from alembic import op

revision = '007_add_user_extra_fields'
down_revision = '006_rename_owner_id_to_user_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The model uses 'metainfo' but migration 002 created 'metadata'
    op.execute("ALTER TABLE users RENAME COLUMN metadata TO metainfo")


def downgrade() -> None:
    op.execute("ALTER TABLE users RENAME COLUMN metainfo TO metadata")
