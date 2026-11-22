import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.workflow import WorkflowModel, WorkflowExecutionModel
from app.services.workflow_service import WorkflowService
from app.schemas.workflow import WorkflowCreate, WorkflowExecutionCreate
from app.database.session import init_db


def test_database_persistence_and_relationships(db_session: Session):
    """Verify SQLAlchemy 2.0 ORM persistence and relationship mapping."""
    service = WorkflowService(db_session)

    # 1. Create parent workflow
    wf_in = WorkflowCreate(
        name="DB Test Workflow",
        description="Testing direct database relationships.",
        nodes=[{"id": "n1", "name": "Input", "type": "Input"}],
        edges=[],
    )
    workflow = service.create_workflow(wf_in)
    assert workflow.id is not None

    # 2. Create executions attached to workflow
    exec1 = service.create_execution(
        WorkflowExecutionCreate(status="completed", input_data={"x": 1}),
        workflow_id=workflow.id,
    )
    exec2 = service.create_execution(
        WorkflowExecutionCreate(status="failed", error_message="Test failure"),
        workflow_id=workflow.id,
    )

    db_session.refresh(workflow)

    # 3. Verify parent -> children relationship
    assert len(workflow.executions) == 2
    assert workflow.executions[0].id in (exec1.id, exec2.id)

    # 4. Verify child -> parent relationship
    assert exec1.workflow.id == workflow.id
    assert exec1.workflow.name == "DB Test Workflow"


def test_cascade_delete_executions(db_session: Session):
    """Verify that deleting a workflow automatically cascades to remove its execution records."""
    service = WorkflowService(db_session)

    # Create workflow and execution
    wf = service.create_workflow(WorkflowCreate(name="Cascade Target"))
    exec_record = service.create_execution(
        WorkflowExecutionCreate(status="completed"),
        workflow_id=wf.id,
    )
    exec_id = exec_record.id

    # Verify execution exists in DB
    assert db_session.query(WorkflowExecutionModel).filter_by(id=exec_id).first() is not None

    # Hard-delete parent workflow
    service.delete_workflow(wf.id, hard_delete=True)

    # Verify execution was deleted by cascade
    assert db_session.query(WorkflowExecutionModel).filter_by(id=exec_id).first() is None


def test_foreign_key_constraint_enforcement(db_session: Session):
    """Verify that SQLite foreign key constraint blocks orphaned execution records."""
    orphan_execution = WorkflowExecutionModel(
        workflow_id="non-existent-parent-workflow-id",
        status="pending",
    )
    db_session.add(orphan_execution)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_init_db_preserves_existing_data(db_session: Session):
    """Verify that calling init_db() does NOT delete or truncate existing data."""
    service = WorkflowService(db_session)
    wf = service.create_workflow(WorkflowCreate(name="Preserved Workflow"))
    wf_id = wf.id

    # Run init_db
    init_db(target_engine=db_session.get_bind())

    # Verify existing record is intact
    persisted = service.get_workflow(wf_id)
    assert persisted is not None
    assert persisted.name == "Preserved Workflow"


def test_transaction_rollback_on_failure(db_session: Session):
    """Verify transaction management safely rolls back on exception."""
    service = WorkflowService(db_session)
    wf = service.create_workflow(WorkflowCreate(name="Initial Workflow"))
    initial_count = db_session.query(WorkflowModel).count()

    try:
        # Intentionally force a transaction failure with invalid foreign key
        bad_exec = WorkflowExecutionModel(workflow_id="invalid-id")
        db_session.add(bad_exec)
        db_session.commit()
    except Exception:
        db_session.rollback()

    # Verify database state remained consistent and unchanged
    assert db_session.query(WorkflowModel).count() == initial_count

