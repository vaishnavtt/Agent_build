"""Additive migration: immutable revisions, durable recovery, and execution telemetry

Revision ID: 002_revisions_recovery_and_telemetry
Revises: 001_initial_schema
Create Date: 2026-11-27 12:00:00.000000

"""
import json
import uuid
from datetime import datetime, timezone
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_revisions_recovery_and_telemetry'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. Alter workflows table: add owner_id, active_revision_id, current_revision_number
    if 'workflows' in existing_tables:
        wf_cols = [c['name'] for c in inspector.get_columns('workflows')]
        with op.batch_alter_table('workflows') as batch_op:
            if 'owner_id' not in wf_cols:
                batch_op.add_column(
                    sa.Column('owner_id', sa.String(length=100), server_default='default-owner', nullable=False)
                )
            if 'active_revision_id' not in wf_cols:
                batch_op.add_column(
                    sa.Column('active_revision_id', sa.String(length=36), nullable=True)
                )
            if 'current_revision_number' not in wf_cols:
                batch_op.add_column(
                    sa.Column('current_revision_number', sa.Integer(), server_default='1', nullable=False)
                )

    # 2. Create workflow_revisions table if not exists
    if 'workflow_revisions' not in existing_tables:
        op.create_table(
            'workflow_revisions',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('workflow_id', sa.String(length=36), nullable=False),
            sa.Column('revision_number', sa.Integer(), nullable=False),
            sa.Column('version', sa.String(length=20), server_default='1.0.0', nullable=False),
            sa.Column('snapshot', sa.JSON(), nullable=False),
            sa.Column('change_summary', sa.Text(), nullable=True),
            sa.Column('created_by', sa.String(length=100), server_default='default-owner', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default=sa.text('0'), nullable=False),
            sa.Column('is_verified', sa.Boolean(), server_default=sa.text('0'), nullable=False),
            sa.Column('last_execution_id', sa.String(length=36), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_workflow_revisions_id'), 'workflow_revisions', ['id'], unique=False)
        op.create_index(op.f('ix_workflow_revisions_workflow_id'), 'workflow_revisions', ['workflow_id'], unique=False)
        op.create_index(op.f('ix_workflow_revisions_revision_number'), 'workflow_revisions', ['revision_number'], unique=False)
        op.create_index(op.f('ix_workflow_revisions_created_at'), 'workflow_revisions', ['created_at'], unique=False)
        op.create_index('ix_revisions_workflow_num', 'workflow_revisions', ['workflow_id', 'revision_number'], unique=False)

    # 3. Create workflow_recoveries table if not exists
    if 'workflow_recoveries' not in existing_tables:
        op.create_table(
            'workflow_recoveries',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('workflow_id', sa.String(length=36), nullable=False),
            sa.Column('revision_id', sa.String(length=36), nullable=True),
            sa.Column('execution_id', sa.String(length=36), nullable=True),
            sa.Column('attempt_number', sa.Integer(), server_default='1', nullable=False),
            sa.Column('status', sa.String(length=30), server_default='reserved', nullable=False),
            sa.Column('idempotency_key', sa.String(length=100), nullable=True),
            sa.Column('error_context', sa.JSON(), nullable=True),
            sa.Column('proposed_patch', sa.JSON(), nullable=True),
            sa.Column('reserved_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('promoted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('rolled_back_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['revision_id'], ['workflow_revisions.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['execution_id'], ['workflow_executions.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_workflow_recoveries_id'), 'workflow_recoveries', ['id'], unique=False)
        op.create_index(op.f('ix_workflow_recoveries_workflow_id'), 'workflow_recoveries', ['workflow_id'], unique=False)
        op.create_index(op.f('ix_workflow_recoveries_status'), 'workflow_recoveries', ['status'], unique=False)
        op.create_index(op.f('ix_workflow_recoveries_idempotency_key'), 'workflow_recoveries', ['idempotency_key'], unique=True)
        op.create_index('ix_recoveries_workflow_attempt', 'workflow_recoveries', ['workflow_id', 'attempt_number'], unique=False)

    # 4. Alter workflow_executions table: add revision_id and telemetry fields
    if 'workflow_executions' in existing_tables:
        exec_cols = [c['name'] for c in inspector.get_columns('workflow_executions')]
        with op.batch_alter_table('workflow_executions') as batch_op:
            if 'revision_id' not in exec_cols:
                batch_op.add_column(sa.Column('revision_id', sa.String(length=36), nullable=True))
            if 'node_logs' not in exec_cols:
                batch_op.add_column(sa.Column('node_logs', sa.JSON(), nullable=True))
            if 'token_usage' not in exec_cols:
                batch_op.add_column(sa.Column('token_usage', sa.JSON(), nullable=True))
            if 'ai_provider' not in exec_cols:
                batch_op.add_column(sa.Column('ai_provider', sa.String(length=50), nullable=True))
            if 'ai_model' not in exec_cols:
                batch_op.add_column(sa.Column('ai_model', sa.String(length=100), nullable=True))
            if 'estimated_cost' not in exec_cols:
                batch_op.add_column(sa.Column('estimated_cost', sa.Float(), nullable=True))
            if 'reliability_report' not in exec_cols:
                batch_op.add_column(sa.Column('reliability_report', sa.JSON(), nullable=True))
            if 'repair_report' not in exec_cols:
                batch_op.add_column(sa.Column('repair_report', sa.JSON(), nullable=True))

    # 5. Data Migration & Backfill
    # A) Orphaned executions: verify all executions point to existing workflow IDs
    try:
        orphans = conn.execute(
            sa.text(
                "SELECT id, workflow_id FROM workflow_executions "
                "WHERE workflow_id NOT IN (SELECT id FROM workflows)"
            )
        ).fetchall()

        if orphans:
            now_iso = datetime.now(timezone.utc).isoformat()
            archive_id = "orphan-archive-workflow"
            # Ensure placeholder archive workflow exists
            conn.execute(
                sa.text(
                    "INSERT OR IGNORE INTO workflows (id, name, description, status, version, is_active, owner_id, nodes, edges, configuration, tags, created_at, updated_at) "
                    "VALUES (:id, :name, :description, :status, :version, :is_active, :owner_id, :nodes, :edges, :configuration, :tags, :created_at, :updated_at)"
                ),
                {
                    "id": archive_id,
                    "name": "Archived Orphan Executions",
                    "description": "Preserved legacy executions whose parent workflow was missing.",
                    "status": "archived",
                    "version": "1.0.0",
                    "is_active": 0,
                    "owner_id": "system",
                    "nodes": "[]",
                    "edges": "[]",
                    "configuration": "{}",
                    "tags": '["archive"]',
                    "created_at": now_iso,
                    "updated_at": now_iso,
                },
            )
            # Re-associate orphans with archive container
            conn.execute(
                sa.text(
                    "UPDATE workflow_executions SET workflow_id = :archive_id "
                    "WHERE workflow_id NOT IN (SELECT id FROM workflows)"
                ),
                {"archive_id": archive_id},
            )
    except Exception:
        pass

    # B) Initial Revisions Backfill for Workflows without an active revision
    try:
        workflows_without_revisions = conn.execute(
            sa.text("SELECT id, name, description, version, nodes, edges, configuration, tags, created_at, updated_at FROM workflows WHERE active_revision_id IS NULL")
        ).fetchall()

        for wf in workflows_without_revisions:
            rev_id = str(uuid.uuid4())
            now_iso = datetime.now(timezone.utc).isoformat()
            
            def parse_json_col(col_val, default):
                if isinstance(col_val, (dict, list)):
                    return col_val
                if isinstance(col_val, str):
                    try:
                        return json.loads(col_val)
                    except Exception:
                        pass
                return default

            snapshot = {
                "schemaVersion": "1.0.0",
                "metadata": {
                    "id": wf[0],
                    "name": wf[1],
                    "description": wf[2] or "",
                    "version": wf[3] or "1.0.0",
                    "author": "AgentForge AI",
                },
                "nodes": parse_json_col(wf[4], []),
                "edges": parse_json_col(wf[5], []),
                "configuration": parse_json_col(wf[6], {}),
            }
            conn.execute(
                sa.text(
                    "INSERT INTO workflow_revisions (id, workflow_id, revision_number, version, snapshot, change_summary, created_by, is_active, is_verified, created_at) "
                    "VALUES (:id, :wf_id, :rev_num, :version, :snapshot, :summary, :created_by, :is_active, :is_verified, :created_at)"
                ),
                {
                    "id": rev_id,
                    "wf_id": wf[0],
                    "rev_num": 1,
                    "version": wf[3] or "1.0.0",
                    "snapshot": json.dumps(snapshot),
                    "summary": "Initial baseline revision backfill",
                    "created_by": "migration",
                    "is_active": 1,
                    "is_verified": 1,
                    "created_at": now_iso,
                },
            )
            conn.execute(
                sa.text("UPDATE workflows SET active_revision_id = :rev_id, current_revision_number = 1 WHERE id = :wf_id"),
                {"rev_id": rev_id, "wf_id": wf[0]},
            )
    except Exception as exc:
        print(f"Error backfilling revisions: {exc}")


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'workflow_recoveries' in existing_tables:
        op.drop_table('workflow_recoveries')
    if 'workflow_revisions' in existing_tables:
        op.drop_table('workflow_revisions')
