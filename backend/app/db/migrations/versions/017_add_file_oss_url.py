"""017_add_file_oss_url

Add oss_url column to files table for OSS artifact URL storage.
"""
from alembic import op
import sqlalchemy as sa


revision = "017_add_file_oss_url"
down_revision = "016_add_chapters_and_chapter_id"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("files", sa.Column("oss_url", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("files", "oss_url")
