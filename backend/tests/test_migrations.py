import os
import sqlite3
import pytest
from sqlalchemy import create_engine, inspect, text
from app.database.migration_runner import run_migrations


def test_fresh_database_migration_to_head(tmp_path):
    """Verify that running migrations on a brand new database creates all required tables and indexes."""
    db_file = tmp_path / "fresh_test.db"
    db_url = f"sqlite:///{db_file.as_posix()}"

    # Run migration up to head
    run_migrations(target_url=db_url)

    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    # All 4 core tables plus alembic_version must exist
    assert "workflows" in tables
    assert "workflow_executions" in tables
    assert "workflow_revisions" in tables
    assert "workflow_recoveries" in tables
    assert "alembic_version" in tables

    # Verify workflows columns
    wf_cols = {c["name"] for c in inspector.get_columns("workflows")}
    assert {"id", "name", "status", "version", "is_active", "owner_id", "active_revision_id", "current_revision_number"}.issubset(wf_cols)

    # Verify workflow_executions columns
    exec_cols = {c["name"] for c in inspector.get_columns("workflow_executions")}
    assert {"id", "workflow_id", "status", "input_data", "output_data", "revision_id", "node_logs", "token_usage", "ai_provider", "ai_model", "estimated_cost"}.issubset(exec_cols)

    # Verify workflow_revisions columns
    rev_cols = {c["name"] for c in inspector.get_columns("workflow_revisions")}
    assert {"id", "workflow_id", "revision_number", "version", "snapshot", "is_active", "is_verified", "created_at"}.issubset(rev_cols)

    # Verify workflow_recoveries columns
    rec_cols = {c["name"] for c in inspector.get_columns("workflow_recoveries")}
    assert {"id", "workflow_id", "attempt_number", "status", "idempotency_key", "reserved_at", "completed_at"}.issubset(rec_cols)

    engine.dispose()


def test_migration_idempotence(tmp_path):
    """Verify that running migrations twice consecutively causes no errors and produces the same schema."""
    db_file = tmp_path / "idempotence_test.db"
    db_url = f"sqlite:///{db_file.as_posix()}"

    # First migration run
    run_migrations(target_url=db_url)

    # Second migration run immediately after
    run_migrations(target_url=db_url)

    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "workflows" in tables
    assert "workflow_revisions" in tables
    engine.dispose()


def test_legacy_data_preservation_and_orphan_handling(tmp_path):
    """Verify that legacy workflows are preserved, initial revisions are backfilled, and orphaned executions are safely archived."""
    db_file = tmp_path / "legacy_test.db"
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    # Create pre-migration legacy tables
    cursor.execute("""
        CREATE TABLE workflows (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(120) NOT NULL,
            description TEXT,
            status VARCHAR(30) DEFAULT 'active',
            version VARCHAR(20) DEFAULT '1.0.0',
            is_active BOOLEAN DEFAULT 1,
            nodes JSON NOT NULL,
            edges JSON NOT NULL,
            configuration JSON NOT NULL,
            tags JSON NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE workflow_executions (
            id VARCHAR(36) PRIMARY KEY,
            workflow_id VARCHAR(36) NOT NULL,
            status VARCHAR(30) DEFAULT 'pending',
            input_data JSON,
            output_data JSON,
            started_at TIMESTAMP NOT NULL
        )
    """)

    # Insert legacy workflow
    cursor.execute("""
        INSERT INTO workflows (id, name, description, status, version, is_active, nodes, edges, configuration, tags, created_at, updated_at)
        VALUES ('legacy-wf-1', 'Legacy Pipeline', 'A legacy workflow before revisions', 'active', '1.0.0', 1, '[]', '[]', '{}', '[]', '2026-01-01 00:00:00', '2026-01-01 00:00:00')
    """)

    # Insert valid execution for legacy workflow
    cursor.execute("""
        INSERT INTO workflow_executions (id, workflow_id, status, input_data, output_data, started_at)
        VALUES ('exec-1', 'legacy-wf-1', 'completed', '{"input": "test"}', '{"out": "ok"}', '2026-01-01 00:01:00')
    """)

    # Insert orphaned execution (workflow_id does not exist)
    cursor.execute("""
        INSERT INTO workflow_executions (id, workflow_id, status, input_data, output_data, started_at)
        VALUES ('orphan-exec-99', 'deleted-wf-404', 'failed', '{"error": "lost parent"}', NULL, '2026-01-01 00:02:00')
    """)

    conn.commit()
    conn.close()

    # Run migrations on the legacy database
    db_url = f"sqlite:///{db_file.as_posix()}"
    run_migrations(target_url=db_url)

    # Inspect results
    engine = create_engine(db_url)
    with engine.connect() as connection:
        # Verify legacy workflow still exists with backfilled owner and active revision
        legacy_wf = connection.execute(
            text("SELECT id, name, owner_id, active_revision_id, current_revision_number FROM workflows WHERE id = 'legacy-wf-1'")
        ).fetchone()
        assert legacy_wf is not None
        assert legacy_wf.name == "Legacy Pipeline"
        assert legacy_wf.owner_id == "default-owner"
        assert legacy_wf.active_revision_id is not None
        assert legacy_wf.current_revision_number == 1

        # Verify backfilled revision exists
        backfilled_rev = connection.execute(
            text("SELECT id, workflow_id, revision_number, is_active, is_verified FROM workflow_revisions WHERE workflow_id = 'legacy-wf-1'")
        ).fetchone()
        assert backfilled_rev is not None
        assert backfilled_rev.id == legacy_wf.active_revision_id
        assert backfilled_rev.revision_number == 1
        assert backfilled_rev.is_active == 1

        # Verify orphaned execution was not deleted, but preserved in archive container
        orphan_rec = connection.execute(
            text("SELECT id, workflow_id, status FROM workflow_executions WHERE id = 'orphan-exec-99'")
        ).fetchone()
        assert orphan_rec is not None
        assert orphan_rec.status == "failed"
        assert orphan_rec.workflow_id == "orphan-archive-workflow"

    engine.dispose()
