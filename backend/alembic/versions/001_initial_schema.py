"""Initial schema for workflows and workflow_executions with non-destructive migration

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. Workflows Table
    if 'workflows' not in existing_tables:
        op.create_table(
            'workflows',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('name', sa.String(length=120), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=30), server_default='active', nullable=False),
            sa.Column('version', sa.String(length=20), server_default='1.0.0', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False),
            sa.Column('workflow_json', sa.JSON(), nullable=True),
            sa.Column('nodes', sa.JSON(), nullable=False),
            sa.Column('edges', sa.JSON(), nullable=False),
            sa.Column('configuration', sa.JSON(), nullable=False),
            sa.Column('tags', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_workflows_id'), 'workflows', ['id'], unique=False)
        op.create_index(op.f('ix_workflows_name'), 'workflows', ['name'], unique=False)
        op.create_index(op.f('ix_workflows_status'), 'workflows', ['status'], unique=False)
        op.create_index(op.f('ix_workflows_created_at'), 'workflows', ['created_at'], unique=False)
    else:
        # Table exists: non-destructively ensure all columns exist
        wf_cols = [c['name'] for c in inspector.get_columns('workflows')]
        with op.batch_alter_table('workflows') as batch_op:
            if 'workflow_json' not in wf_cols:
                batch_op.add_column(sa.Column('workflow_json', sa.JSON(), nullable=True))
            if 'status' not in wf_cols:
                batch_op.add_column(sa.Column('status', sa.String(length=30), server_default='active', nullable=False))

    # 2. Workflow Executions Table
    if 'workflow_executions' not in existing_tables:
        op.create_table(
            'workflow_executions',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('workflow_id', sa.String(length=36), nullable=False),
            sa.Column('status', sa.String(length=30), server_default='pending', nullable=False),
            sa.Column('input_data', sa.JSON(), nullable=True),
            sa.Column('output_data', sa.JSON(), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('execution_duration', sa.Float(), nullable=True),
            sa.Column('repair_attempts', sa.Integer(), server_default='0', nullable=False),
            sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_workflow_executions_id'), 'workflow_executions', ['id'], unique=False)
        op.create_index(op.f('ix_workflow_executions_workflow_id'), 'workflow_executions', ['workflow_id'], unique=False)
        op.create_index(op.f('ix_workflow_executions_status'), 'workflow_executions', ['status'], unique=False)
        op.create_index(op.f('ix_workflow_executions_started_at'), 'workflow_executions', ['started_at'], unique=False)
        op.create_index('ix_executions_workflow_started', 'workflow_executions', ['workflow_id', 'started_at'], unique=False)
    else:
        # Table exists: non-destructively ensure all columns exist
        exec_cols = [c['name'] for c in inspector.get_columns('workflow_executions')]
        with op.batch_alter_table('workflow_executions') as batch_op:
            if 'input_data' not in exec_cols:
                batch_op.add_column(sa.Column('input_data', sa.JSON(), nullable=True))
            if 'output_data' not in exec_cols:
                batch_op.add_column(sa.Column('output_data', sa.JSON(), nullable=True))
            if 'execution_duration' not in exec_cols:
                batch_op.add_column(sa.Column('execution_duration', sa.Float(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'workflow_executions' in existing_tables:
        op.drop_table('workflow_executions')
    if 'workflows' in existing_tables:
        op.drop_table('workflows')
