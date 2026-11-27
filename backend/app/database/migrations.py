"""Non-destructive schema compatibility migration helper for existing SQLite/SQL databases."""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


_WORKFLOW_EXECUTIONS_COLUMNS = {
    "workflow_revision_id": "VARCHAR(64)",
    "owner_id": "VARCHAR(100)",
    "is_candidate": "BOOLEAN NOT NULL DEFAULT 0",
    "failed_node_id": "VARCHAR(100)",
    "logs": "JSON",
    "metrics": "JSON",
    "execution_context": "JSON",
    "workflow_snapshot": "JSON",
}


def ensure_schema_compatibility(engine: Engine) -> None:
    """Adds missing Member 4 columns to existing main-branch databases without deleting data."""
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if "workflow_executions" not in table_names:
        return

    existing_cols = {col["name"] for col in inspector.get_columns("workflow_executions")}
    missing = [
        (col_name, col_type)
        for col_name, col_type in _WORKFLOW_EXECUTIONS_COLUMNS.items()
        if col_name not in existing_cols
    ]
    if not missing:
        return

    with engine.begin() as conn:
        for col_name, col_type in missing:
            conn.execute(
                text(f"ALTER TABLE workflow_executions ADD COLUMN {col_name} {col_type}")
            )
