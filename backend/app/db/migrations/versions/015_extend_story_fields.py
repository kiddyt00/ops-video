"""Extend Story model with new optional fields

Revision ID: 015_extend_story_fields
Revises: 014_add_knowledge_prompt_relation
Create Date: 2026-05-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '015_extend_story_fields'
down_revision = '014_add_knowledge_prompt_relation'
branch_labels = None
depends_on = None


def upgrade() -> None:
    for col, col_type in [
        ("title_suggestions", sa.JSON()),
        ("target_audience", sa.String(255)),
        ("style_tags", sa.JSON()),
        ("word_count_estimate", sa.Integer()),
        ("golden_finger_detail", sa.Text()),
        ("power_system", sa.JSON()),
        ("world_map_hints", sa.Text()),
        ("prologue_preview", sa.Text()),
    ]:
        op.add_column("stories", sa.Column(col, col_type, nullable=True))


def downgrade() -> None:
    for col in [
        "title_suggestions", "target_audience", "style_tags",
        "word_count_estimate", "golden_finger_detail",
        "power_system", "world_map_hints", "prologue_preview",
    ]:
        op.drop_column("stories", col)
