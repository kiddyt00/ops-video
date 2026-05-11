"""Add character_cards table

Revision ID: 010_add_character_cards
Revises: 009_fix_logs_ts
Create Date: 2026-05-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '010_add_character_cards'
down_revision = '009_fix_logs_ts'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'character_cards',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('front_view_url', sa.String(500), nullable=True),
        sa.Column('side_view_url', sa.String(500), nullable=True),
        sa.Column('back_view_url', sa.String(500), nullable=True),
        sa.Column('reference_images', postgresql.JSON, nullable=True),
        sa.Column('traits', postgresql.JSON, nullable=True),
        sa.Column('usage_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_character_cards_project_id'), 'character_cards', ['project_id'], unique=False)
    op.create_index(op.f('ix_character_cards_name'), 'character_cards', ['name'], unique=False)


def downgrade() -> None:
    op.drop_table('character_cards')
