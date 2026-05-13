"""Add knowledge, prompt, relation, character_state tables

Revision ID: 014_add_knowledge_prompt_relation
Revises: 013_add_ai_model_is_active
Create Date: 2026-05-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '014_add_kb_prompt_rel_state'
down_revision = '013_add_ai_model_is_active'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'knowledge',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), unique=True, nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('built_in', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_knowledge_name', 'knowledge', ['name'])
    op.create_index('ix_knowledge_category', 'knowledge', ['category'])

    op.create_table(
        'prompts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), unique=True, nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template', sa.Text(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('built_in', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_prompts_name', 'prompts', ['name'])

    op.create_table(
        'relations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_name', sa.String(255), nullable=False),
        sa.Column('relation_type', sa.String(50), nullable=False),
        sa.Column('target_type', sa.String(50), nullable=False),
        sa.Column('target_name', sa.String(255), nullable=False),
        sa.Column('properties', postgresql.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_relations_project', 'relations', ['project_id'])
    op.create_index('ix_relations_source', 'relations', ['project_id', 'source_name'])

    op.create_table(
        'character_states',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('character_name', sa.String(255), nullable=False),
        sa.Column('chapter_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(30), nullable=False, server_default='alive'),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('faction', sa.String(255), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_char_states_project', 'character_states', ['project_id', 'character_name'])
    op.create_index('ix_char_states_chapter', 'character_states', ['project_id', 'chapter_number'])

    # Add foreign key constraints
    op.create_foreign_key('fk_relations_project', 'relations', 'projects', ['project_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_char_states_project', 'character_states', 'projects', ['project_id'], ['id'], ondelete='CASCADE')


def downgrade():
    op.drop_table('character_states')
    op.drop_table('relations')
    op.drop_table('prompts')
    op.drop_table('knowledge')
