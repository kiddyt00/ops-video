"""Add a migration message"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_name'), 'projects', ['name'], unique=False)

    # Tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('stage', sa.Enum('SCRIPT', 'STORYBOARD', 'IMAGE', 'AUDIO', 'VIDEO', name='taskstage'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', name='taskstatus'), nullable=False),
        sa.Column('parent_task_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('generator_type', sa.String(length=100), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=False),
        sa.Column('output_file_ids', sa.JSON(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['parent_task_id'], ['tasks.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_project_id'), 'tasks', ['project_id'], unique=False)
    op.create_index(op.f('ix_tasks_stage'), 'tasks', ['stage'], unique=False)
    op.create_index(op.f('ix_tasks_status'), 'tasks', ['status'], unique=False)

    # Task status logs table
    op.create_table(
        'task_status_logs',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('from_status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', name='taskstatus'), nullable=True),
        sa.Column('to_status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', name='taskstatus'), nullable=False),
        sa.Column('reason', sa.String(length=500), nullable=True),
        sa.Column('changed_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_status_logs_task_id'), 'task_status_logs', ['task_id'], unique=False)

    # Variant groups table
    op.create_table(
        'variant_groups',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('stage', sa.String(length=50), nullable=False),
        sa.Column('selected_file_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('parameters', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_variant_groups_project_id'), 'variant_groups', ['project_id'], unique=False)
    op.create_index(op.f('ix_variant_groups_stage'), 'variant_groups', ['stage'], unique=False)
    op.create_index(op.f('ix_variant_groups_task_id'), 'variant_groups', ['task_id'], unique=False)

    # Files table
    op.create_table(
        'files',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('variant_group_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('task_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('file_type', sa.Enum('IMAGE', 'AUDIO', 'VIDEO', 'SCRIPT', 'STORYBOARD', 'OTHER', name='filetype'), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('generation_params', sa.JSON(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('parent_file_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('is_selected', sa.Boolean(), nullable=False),
        sa.Column('selected_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['parent_file_id'], ['files.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['variant_group_id'], ['variant_groups.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_files_file_type'), 'files', ['file_type'], unique=False)
    op.create_index(op.f('ix_files_is_selected'), 'files', ['is_selected'], unique=False)
    op.create_index(op.f('ix_files_parent_file_id'), 'files', ['parent_file_id'], unique=False)
    op.create_index(op.f('ix_files_project_id'), 'files', ['project_id'], unique=False)
    op.create_index(op.f('ix_files_task_id'), 'files', ['task_id'], unique=False)
    op.create_index(op.f('ix_files_variant_group_id'), 'files', ['variant_group_id'], unique=False)

    # Add foreign key constraint for selected_file_id in variant_groups
    op.create_foreign_key(
        'fk_variant_groups_selected_file_id',
        'variant_groups',
        'files',
        ['selected_file_id'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_index(op.f('ix_variant_groups_selected_file_id'), 'variant_groups', ['selected_file_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('files')
    op.drop_table('variant_groups')
    op.drop_table('task_status_logs')
    op.drop_table('tasks')
    op.drop_table('projects')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS filetype')
    op.execute('DROP TYPE IF EXISTS taskstatus')
    op.execute('DROP TYPE IF EXISTS taskstage')
