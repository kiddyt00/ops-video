"""Add stories table

Revision ID: 012_add_stories
Revises: 011_add_storage_providers
Create Date: 2026-05-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '012_add_stories'
down_revision = '011_add_storage_providers'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the story_status enum type
    story_status = postgresql.ENUM(
        'draft', 'completed', 'archived',
        name='story_status',
        create_type=True
    )
    story_status.create(op.get_bind())

    op.create_table(
        'stories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('inspiration', sa.String, nullable=True),
        sa.Column('logline', sa.String, nullable=True),
        sa.Column('synopsis', sa.String, nullable=True),
        sa.Column('worldbuilding', postgresql.JSON, nullable=True),
        sa.Column('characters', postgresql.JSON, nullable=True),
        sa.Column('themes', postgresql.JSON, nullable=True),
        sa.Column('plot_points', postgresql.JSON, nullable=True),
        sa.Column('chapter_outline', postgresql.JSON, nullable=True),
        sa.Column('status', story_status, nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_stories_project_id'), 'stories', ['project_id'], unique=False)
    op.create_index(op.f('ix_stories_status'), 'stories', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_stories_status'), table_name='stories')
    op.drop_index(op.f('ix_stories_project_id'), table_name='stories')
    op.drop_table('stories')
    # Drop the enum type
    story_status = postgresql.ENUM(
        'draft', 'completed', 'archived',
        name='story_status',
        create_type=False
    )
    story_status.drop(op.get_bind())
