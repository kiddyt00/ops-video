"""018_add_chapter_body_text

Add body_text column to chapters table for storing full narrative prose.
"""
from alembic import op
import sqlalchemy as sa


revision = "018_add_chapter_body_text"
down_revision = "017_add_file_oss_url"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("chapters", sa.Column("body_text", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("chapters", "body_text")
