"""016_add_chapters_and_chapter_id

Revision ID: 016
Revises: 015_extend_story_fields
Create Date: 2026-05-14

Adds:
- chapters table for per-chapter status tracking
- chapter_id column to tasks table
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid

revision = "016"
down_revision = "015_extend_story_fields"


def upgrade():
    # Create chapters table
    op.create_table(
        "chapters",
        sa.Column("id", UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "project_id",
            UUID(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("chapter_number", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(30),
            nullable=False,
            server_default="pending",
            index=True,
        ),
        sa.Column("current_stage", sa.String(50), nullable=True),
        sa.Column("video_file_id", UUID(), nullable=True),
        sa.Column("thumbnail_url", sa.String(500), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Add chapter_id to tasks
    op.add_column(
        "tasks",
        sa.Column(
            "chapter_id",
            UUID(),
            sa.ForeignKey("chapters.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )


def downgrade():
    op.drop_column("tasks", "chapter_id")
    op.drop_table("chapters")
