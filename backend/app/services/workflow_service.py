import uuid
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.workflow import (
    WorkflowModel,
    WorkflowExecutionModel,
    WorkflowRevisionModel,
    WorkflowRecoveryModel,
    utc_now,
)
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowExecutionCreate,
    WorkflowExecutionUpdate,
    WorkflowRecoveryReserveRequest,
    WorkflowRecoveryCompleteRequest,
    WorkflowRevisionDiffResponse,
)
from app.core.logging import logger


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Helper to guarantee datetime has timezone info for safe arithmetic across SQLite."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


# -----------------------------------------------------------------------------
# PHASE 5 CORE ARCHITECTURAL COMPONENTS
# -----------------------------------------------------------------------------

class DurableAttempts:
    """Tracks, verifies, and enforces persistent repair attempt limits.
    
    Guarantees a strict ceiling of two repair attempts per incident/revision.
    """

    MAX_REPAIR_ATTEMPTS: int = 2

    @classmethod
    def check_and_reserve_attempt(cls, db: Session, workflow_id: str) -> int:
        """Atomically determine the next attempt number or raise if ceiling reached."""
        existing_count = (
            db.query(WorkflowRecoveryModel)
            .filter(
                WorkflowRecoveryModel.workflow_id == workflow_id,
                WorkflowRecoveryModel.status.in_(["reserved", "in_progress", "completed", "failed"]),
            )
            .count()
        )

        if existing_count >= cls.MAX_REPAIR_ATTEMPTS:
            raise ValueError(
                f"Maximum repair limit ({cls.MAX_REPAIR_ATTEMPTS}) exceeded for workflow '{workflow_id}'. Manual intervention required."
            )

        return existing_count + 1


class SnapshotSource:
    """Captures and validates immutable workflow graph snapshots."""

    @classmethod
    def create_snapshot(cls, workflow: WorkflowModel) -> Dict[str, Any]:
        return workflow.to_canonical_dict()


class RevisionLifecycle:
    """Coordinates lifecycle transitions of immutable workflow revisions."""

    @classmethod
    def create_initial_revision(
        cls, db: Session, workflow: WorkflowModel, creator_id: str, summary: str = "Initial creation"
    ) -> WorkflowRevisionModel:
        snapshot = SnapshotSource.create_snapshot(workflow)
        revision = WorkflowRevisionModel(
            id=str(uuid.uuid4()),
            workflow_id=workflow.id,
            revision_number=1,
            version=workflow.version or "1.0.0",
            snapshot=snapshot,
            change_summary=summary,
            created_by=creator_id,
            is_active=True,
            is_verified=True,
            created_at=utc_now(),
        )
        db.add(revision)
        workflow.active_revision_id = revision.id
        workflow.current_revision_number = 1
        return revision

    @classmethod
    def create_next_revision(
        cls, db: Session, workflow: WorkflowModel, modifier_id: str, summary: Optional[str] = None
    ) -> WorkflowRevisionModel:
        new_rev_number = (workflow.current_revision_number or 0) + 1
        snapshot = SnapshotSource.create_snapshot(workflow)
        revision = WorkflowRevisionModel(
            id=str(uuid.uuid4()),
            workflow_id=workflow.id,
            revision_number=new_rev_number,
            version=workflow.version or "1.0.0",
            snapshot=snapshot,
            change_summary=summary or f"Revision {new_rev_number}",
            created_by=modifier_id,
            is_active=True,
            is_verified=False,
            created_at=utc_now(),
        )
        db.add(revision)

        # Deactivate previous revisions as active
        db.query(WorkflowRevisionModel).filter(
            WorkflowRevisionModel.workflow_id == workflow.id,
            WorkflowRevisionModel.id != revision.id,
        ).update({"is_active": False})

        workflow.active_revision_id = revision.id
        workflow.current_revision_number = new_rev_number
        return revision


class RecoveryRecorder:
    """Records durable recovery events, timestamps, and promotion states."""

    @classmethod
    def record_reservation(
        cls,
        db: Session,
        workflow_id: str,
        attempt_number: int,
        execution_id: Optional[str],
        revision_id: Optional[str],
        idempotency_key: Optional[str],
        error_context: Optional[Dict[str, Any]],
    ) -> WorkflowRecoveryModel:
        recovery = WorkflowRecoveryModel(
            id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            revision_id=revision_id,
            execution_id=execution_id,
            attempt_number=attempt_number,
            status="reserved",
            idempotency_key=idempotency_key,
            error_context=error_context,
            reserved_at=utc_now(),
        )
        db.add(recovery)
        return recovery


# -----------------------------------------------------------------------------
# MAIN WORKFLOW SERVICE LAYER
# -----------------------------------------------------------------------------

class WorkflowService:
    """Service layer for workflow persistence, revisions, recovery, and execution tracking."""

    def __init__(self, db: Session):
        self.db = db

    # -------------------------------------------------------------------------
    # WORKFLOW GRAPH VALIDATION & AUTHORITATIVE CONSISTENCY (Phase 3)
    # -------------------------------------------------------------------------

    def validate_graph_integrity(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> None:
        """Prevent stale nodes and edges. Validate that every edge references valid nodes."""
        node_ids = {n.get("id") for n in nodes if isinstance(n, dict) and n.get("id")}
        
        seen_edges = set()
        for edge in edges:
            if not isinstance(edge, dict):
                continue
            source = edge.get("source")
            target = edge.get("target")

            if source and source not in node_ids:
                raise ValueError(f"Stale edge detected: source node '{source}' does not exist in workflow nodes.")
            if target and target not in node_ids:
                raise ValueError(f"Stale edge detected: target node '{target}' does not exist in workflow nodes.")

            edge_key = (source, target, edge.get("sourceHandle"), edge.get("targetHandle"))
            if edge_key in seen_edges:
                # Deduplicate or warn
                pass
            seen_edges.add(edge_key)

    # -------------------------------------------------------------------------
    # WORKFLOW CRUD (Phase 3)
    # -------------------------------------------------------------------------

    def get_workflow(
        self, workflow_id: str, include_inactive: bool = False
    ) -> Optional[WorkflowModel]:
        """Fetch a workflow by ID, optionally including inactive/soft-deleted records."""
        query = self.db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id)
        if not include_inactive:
            query = query.filter(
                WorkflowModel.is_active == True,
                WorkflowModel.status != "deleted",
            )
        return query.first()

    def list_workflows(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        owner_id: Optional[str] = None,
        include_inactive: bool = False,
    ) -> List[WorkflowModel]:
        """List workflows ordered by creation date with pagination and status filters."""
        query = self.db.query(WorkflowModel)
        if not include_inactive:
            query = query.filter(
                WorkflowModel.is_active == True,
                WorkflowModel.status != "deleted",
            )
        if status:
            query = query.filter(WorkflowModel.status == status.lower())
        if owner_id and owner_id != "admin":
            query = query.filter(
                (WorkflowModel.owner_id == owner_id) | (WorkflowModel.owner_id == "default-owner")
            )

        return (
            query.order_by(WorkflowModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_workflow(self, workflow_in: WorkflowCreate, creator_id: str = "default-owner") -> WorkflowModel:
        """Create and persist an authoritative workflow graph and its initial revision."""
        # 1. Validate graph structure
        self.validate_graph_integrity(workflow_in.nodes or [], workflow_in.edges or [])

        # 2. Generate backend authoritative UUID
        authoritative_id = str(uuid.uuid4())

        config_dict = (
            workflow_in.configuration.model_dump()
            if hasattr(workflow_in.configuration, "model_dump")
            else dict(workflow_in.configuration or {})
        )

        owner = workflow_in.owner_id or creator_id

        db_obj = WorkflowModel(
            id=authoritative_id,
            name=workflow_in.name,
            description=workflow_in.description,
            status=workflow_in.status.lower() if workflow_in.status else "active",
            version=workflow_in.version or "1.0.0",
            is_active=True if (workflow_in.status or "active") != "inactive" else False,
            owner_id=owner,
            nodes=workflow_in.nodes or [],
            edges=workflow_in.edges or [],
            configuration=config_dict,
            tags=workflow_in.tags or [],
            workflow_json=None,
        )

        try:
            self.db.add(db_obj)
            self.db.flush()

            # Synchronize canonical JSON using authoritative ID
            db_obj.workflow_json = db_obj.to_canonical_dict()

            # Create immutable Revision 1 (Phase 4)
            RevisionLifecycle.create_initial_revision(
                self.db, db_obj, creator_id=owner, summary=workflow_in.change_summary or "Initial creation"
            )

            self.db.commit()
            self.db.refresh(db_obj)

            logger.info("Created authoritative workflow: id=%s, name='%s', revision=1", db_obj.id, db_obj.name)
            return db_obj
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error("Failed to create workflow: %s", exc)
            raise

    def update_workflow(
        self,
        workflow_id: str,
        workflow_in: WorkflowUpdate,
        modifier_id: str = "default-owner",
    ) -> Optional[WorkflowModel]:
        """Update an existing workflow graph and append an immutable revision."""
        db_obj = self.get_workflow(workflow_id, include_inactive=True)
        if not db_obj:
            return None

        # Optimistic locking & Stale update prevention (Phase 4)
        if workflow_in.base_revision_id and db_obj.active_revision_id:
            if workflow_in.base_revision_id != db_obj.active_revision_id:
                raise ValueError(
                    f"Conflict: base_revision_id '{workflow_in.base_revision_id}' is stale. Active revision is '{db_obj.active_revision_id}'."
                )
        if workflow_in.base_revision_number is not None:
            if workflow_in.base_revision_number != db_obj.current_revision_number:
                raise ValueError(
                    f"Conflict: base_revision_number '{workflow_in.base_revision_number}' is stale. Current revision is '{db_obj.current_revision_number}'."
                )

        update_data = workflow_in.model_dump(exclude_unset=True)
        update_data.pop("base_revision_id", None)
        update_data.pop("base_revision_number", None)
        change_summary = update_data.pop("change_summary", None)

        # Validate graph integrity if nodes or edges are being updated
        target_nodes = update_data.get("nodes", db_obj.nodes)
        target_edges = update_data.get("edges", db_obj.edges)
        self.validate_graph_integrity(target_nodes or [], target_edges or [])

        topology_changed = False
        for field, value in update_data.items():
            if field == "configuration" and value is not None:
                new_conf = value.model_dump() if hasattr(value, "model_dump") else dict(value)
                if new_conf != db_obj.configuration:
                    db_obj.configuration = new_conf
                    topology_changed = True
            elif field == "nodes" and value is not None:
                if value != db_obj.nodes:
                    db_obj.nodes = value
                    topology_changed = True
            elif field == "edges" and value is not None:
                if value != db_obj.edges:
                    db_obj.edges = value
                    topology_changed = True
            elif field == "status" and value is not None:
                db_obj.status = value.lower()
                db_obj.is_active = db_obj.status not in ("inactive", "deleted")
            elif field == "is_active" and value is not None:
                db_obj.is_active = value
                if not value:
                    db_obj.status = "inactive"
            else:
                setattr(db_obj, field, value)

        db_obj.updated_at = utc_now()
        db_obj.workflow_json = db_obj.to_canonical_dict()

        try:
            # Create a new revision whenever workflow changes are saved
            if update_data:
                RevisionLifecycle.create_next_revision(
                    self.db, db_obj, modifier_id=modifier_id, summary=change_summary
                )

            self.db.commit()
            self.db.refresh(db_obj)
            logger.info("Updated workflow id=%s (rev=%s)", db_obj.id, db_obj.current_revision_number)
            return db_obj
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error("Failed to update workflow id=%s: %s", workflow_id, exc)
            raise

    def delete_workflow(self, workflow_id: str, hard_delete: bool = False) -> bool:
        """Delete workflow: soft-delete by default, hard-delete if specified."""
        db_obj = self.get_workflow(workflow_id, include_inactive=True)
        if not db_obj:
            return False

        try:
            if hard_delete:
                self.db.delete(db_obj)
            else:
                db_obj.is_active = False
                db_obj.status = "deleted"
                db_obj.updated_at = utc_now()

            self.db.commit()
            logger.info("Deleted workflow: id=%s (hard=%s)", workflow_id, hard_delete)
            return True
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error("Failed to delete workflow id=%s: %s", workflow_id, exc)
            raise

    # -------------------------------------------------------------------------
    # REVISION MANAGEMENT (Phase 4)
    # -------------------------------------------------------------------------

    def list_revisions(self, workflow_id: str) -> List[WorkflowRevisionModel]:
        """Retrieve all immutable revisions for a workflow ordered descending."""
        return (
            self.db.query(WorkflowRevisionModel)
            .filter(WorkflowRevisionModel.workflow_id == workflow_id)
            .order_by(WorkflowRevisionModel.revision_number.desc())
            .all()
        )

    def get_revision(self, workflow_id: str, revision_id: str) -> Optional[WorkflowRevisionModel]:
        """Retrieve a specific revision of a workflow by UUID or revision number."""
        query = self.db.query(WorkflowRevisionModel).filter(
            WorkflowRevisionModel.workflow_id == workflow_id
        )
        if str(revision_id).isdigit():
            return query.filter(
                (WorkflowRevisionModel.id == str(revision_id))
                | (WorkflowRevisionModel.revision_number == int(revision_id))
            ).first()
        return query.filter(WorkflowRevisionModel.id == str(revision_id)).first()

    def get_last_working_revision(self, workflow_id: str) -> Optional[WorkflowRevisionModel]:
        """Find the last-known-working revision with verified execution evidence."""
        return (
            self.db.query(WorkflowRevisionModel)
            .filter(
                WorkflowRevisionModel.workflow_id == workflow_id,
                WorkflowRevisionModel.is_verified == True,
            )
            .order_by(WorkflowRevisionModel.revision_number.desc())
            .first()
        )

    def promote_revision(
        self, workflow_id: str, revision_id: str, execution_id: Optional[str] = None
    ) -> WorkflowRevisionModel:
        """Promote a revision to active only when passing execution evidence is verified."""
        revision = self.get_revision(workflow_id, revision_id)
        if not revision:
            raise ValueError(f"Revision '{revision_id}' not found for workflow '{workflow_id}'.")

        # Check execution evidence
        passing_exec = None
        if execution_id:
            passing_exec = (
                self.db.query(WorkflowExecutionModel)
                .filter(
                    WorkflowExecutionModel.id == execution_id,
                    WorkflowExecutionModel.workflow_id == workflow_id,
                    WorkflowExecutionModel.status == "completed",
                )
                .first()
            )
        else:
            # Look for any completed execution attached to this revision or workflow
            passing_exec = (
                self.db.query(WorkflowExecutionModel)
                .filter(
                    WorkflowExecutionModel.workflow_id == workflow_id,
                    WorkflowExecutionModel.revision_id == revision_id,
                    WorkflowExecutionModel.status == "completed",
                )
                .first()
            )

        if not passing_exec and not revision.is_verified:
            raise ValueError(
                f"Cannot promote revision '{revision_id}': passing execution evidence is required."
            )

        # Mark revision as verified and active
        revision.is_verified = True
        revision.is_active = True
        if passing_exec:
            revision.last_execution_id = passing_exec.id

        # Deactivate other revisions
        self.db.query(WorkflowRevisionModel).filter(
            WorkflowRevisionModel.workflow_id == workflow_id,
            WorkflowRevisionModel.id != revision.id,
        ).update({"is_active": False})

        # Update parent workflow active revision and graph topology from snapshot
        workflow = revision.workflow
        workflow.active_revision_id = revision.id
        workflow.version = revision.version

        snapshot = revision.snapshot or {}
        workflow.nodes = snapshot.get("nodes", workflow.nodes)
        workflow.edges = snapshot.get("edges", workflow.edges)
        workflow.configuration = snapshot.get("configuration", workflow.configuration)
        workflow.updated_at = utc_now()
        workflow.workflow_json = workflow.to_canonical_dict()

        self.db.commit()
        self.db.refresh(revision)
        return revision

    def diff_revisions(
        self, workflow_id: str, source_rev_id: str, target_rev_id: str
    ) -> WorkflowRevisionDiffResponse:
        """Compare two immutable revisions and return node, edge, and config diffs."""
        r1 = self.get_revision(workflow_id, source_rev_id)
        r2 = self.get_revision(workflow_id, target_rev_id)

        if not r1:
            raise ValueError(f"Source revision '{source_rev_id}' not found.")
        if not r2:
            raise ValueError(f"Target revision '{target_rev_id}' not found.")

        snap1 = r1.snapshot or {}
        snap2 = r2.snapshot or {}

        nodes1 = {n.get("id"): n for n in snap1.get("nodes", [])}
        nodes2 = {n.get("id"): n for n in snap2.get("nodes", [])}

        nodes_added = [n for nid, n in nodes2.items() if nid not in nodes1]
        nodes_removed = [n for nid, n in nodes1.items() if nid not in nodes2]
        nodes_modified = [n for nid, n in nodes2.items() if nid in nodes1 and n != nodes1[nid]]

        edges1 = {e.get("id"): e for e in snap1.get("edges", [])}
        edges2 = {e.get("id"): e for e in snap2.get("edges", [])}

        edges_added = [e for eid, e in edges2.items() if eid not in edges1]
        edges_removed = [e for eid, e in edges1.items() if eid not in edges2]
        edges_modified = [e for eid, e in edges2.items() if eid in edges1 and e != edges1[eid]]

        conf1 = snap1.get("configuration", {})
        conf2 = snap2.get("configuration", {})
        config_diff = {}
        for k, v in conf2.items():
            if conf1.get(k) != v:
                config_diff[k] = {"from": conf1.get(k), "to": v}

        return WorkflowRevisionDiffResponse(
            workflow_id=workflow_id,
            source_revision_id=r1.id,
            target_revision_id=r2.id,
            source_revision_number=r1.revision_number,
            target_revision_number=r2.revision_number,
            nodes_added=nodes_added,
            nodes_removed=nodes_removed,
            nodes_modified=nodes_modified,
            edges_added=edges_added,
            edges_removed=edges_removed,
            edges_modified=edges_modified,
            configuration_changes=config_diff,
        )

    def restore_revision(
        self, workflow_id: str, revision_id: str, modifier_id: str = "default-owner", summary: Optional[str] = None
    ) -> WorkflowRevisionModel:
        """Restore an earlier revision by creating a new forward revision with its snapshot."""
        target_rev = self.get_revision(workflow_id, revision_id)
        if not target_rev:
            raise ValueError(f"Revision '{revision_id}' not found for workflow '{workflow_id}'.")

        workflow = target_rev.workflow
        snapshot = target_rev.snapshot or {}

        # Apply target snapshot to active workflow
        workflow.nodes = snapshot.get("nodes", [])
        workflow.edges = snapshot.get("edges", [])
        workflow.configuration = snapshot.get("configuration", {})
        workflow.updated_at = utc_now()
        workflow.workflow_json = workflow.to_canonical_dict()

        # Create new incremental revision
        restore_summary = summary or f"Restored from revision {target_rev.revision_number} ({target_rev.id})"
        new_rev = RevisionLifecycle.create_next_revision(
            self.db, workflow, modifier_id=modifier_id, summary=restore_summary
        )

        self.db.commit()
        self.db.refresh(new_rev)
        return new_rev

    # -------------------------------------------------------------------------
    # DURABLE REPAIR & RECOVERY (Phase 5)
    # -------------------------------------------------------------------------

    def reserve_recovery(
        self,
        workflow_id: str,
        reserve_in: WorkflowRecoveryReserveRequest,
    ) -> WorkflowRecoveryModel:
        """Atomically reserve a repair attempt adhering to the strict 2-attempt budget."""
        workflow = self.get_workflow(workflow_id, include_inactive=True)
        if not workflow:
            raise ValueError(f"Workflow '{workflow_id}' not found.")

        # Check idempotency key if provided to prevent duplicate requests
        if reserve_in.idempotency_key:
            existing = (
                self.db.query(WorkflowRecoveryModel)
                .filter(
                    WorkflowRecoveryModel.workflow_id == workflow_id,
                    WorkflowRecoveryModel.idempotency_key == reserve_in.idempotency_key,
                )
                .first()
            )
            if existing:
                return existing

        # Protect against concurrent overlapping repair reservations
        active_rec = (
            self.db.query(WorkflowRecoveryModel)
            .filter(
                WorkflowRecoveryModel.workflow_id == workflow_id,
                WorkflowRecoveryModel.status.in_(["reserved", "in_progress"]),
            )
            .first()
        )
        if active_rec:
            return active_rec

        # Enforce DurableAttempts ceiling
        attempt_num = DurableAttempts.check_and_reserve_attempt(self.db, workflow_id)

        recovery = RecoveryRecorder.record_reservation(
            db=self.db,
            workflow_id=workflow_id,
            attempt_number=attempt_num,
            execution_id=reserve_in.execution_id,
            revision_id=workflow.active_revision_id,
            idempotency_key=reserve_in.idempotency_key,
            error_context=reserve_in.error_context,
        )

        self.db.commit()
        self.db.refresh(recovery)
        logger.info("Reserved recovery attempt %s for workflow %s", attempt_num, workflow_id)
        return recovery

    def reserve_recovery_attempt(
        self, workflow_id: str, reserve_in: WorkflowRecoveryReserveRequest
    ) -> WorkflowRecoveryModel:
        """Alias for reserve_recovery."""
        return self.reserve_recovery(workflow_id, reserve_in)

    def complete_recovery(
        self,
        workflow_id: str,
        recovery_id: str,
        complete_in: WorkflowRecoveryCompleteRequest,
    ) -> WorkflowRecoveryModel:
        """Mark recovery completion and persist proposed graph patch."""
        recovery = (
            self.db.query(WorkflowRecoveryModel)
            .filter(
                WorkflowRecoveryModel.id == recovery_id,
                WorkflowRecoveryModel.workflow_id == workflow_id,
            )
            .first()
        )
        if not recovery:
            raise ValueError(f"Recovery '{recovery_id}' not found for workflow '{workflow_id}'.")

        recovery.status = complete_in.status
        recovery.completed_at = utc_now()
        if complete_in.proposed_patch:
            recovery.proposed_patch = complete_in.proposed_patch

        self.db.commit()
        self.db.refresh(recovery)
        return recovery

    def promote_recovery(self, workflow_id: str, recovery_id: str) -> WorkflowRecoveryModel:
        """Record promotion timestamp for a successfully verified recovery."""
        recovery = (
            self.db.query(WorkflowRecoveryModel)
            .filter(
                WorkflowRecoveryModel.id == recovery_id,
                WorkflowRecoveryModel.workflow_id == workflow_id,
            )
            .first()
        )
        if not recovery:
            raise ValueError(f"Recovery '{recovery_id}' not found.")

        recovery.status = "promoted"
        recovery.promoted_at = utc_now()
        self.db.commit()
        self.db.refresh(recovery)
        return recovery

    def rollback_recovery(self, workflow_id: str, recovery_id: str) -> WorkflowRecoveryModel:
        """Record rollback timestamp when recovery fails verification."""
        recovery = (
            self.db.query(WorkflowRecoveryModel)
            .filter(
                WorkflowRecoveryModel.id == recovery_id,
                WorkflowRecoveryModel.workflow_id == workflow_id,
            )
            .first()
        )
        if not recovery:
            raise ValueError(f"Recovery '{recovery_id}' not found.")

        recovery.status = "rolled_back"
        recovery.rolled_back_at = utc_now()
        self.db.commit()
        self.db.refresh(recovery)
        return recovery

    def list_workflow_recoveries(
        self, workflow_id: str, revision_id: Optional[str] = None
    ) -> List[WorkflowRecoveryModel]:
        """List durable recovery history for a workflow, optionally revision-scoped."""
        query = self.db.query(WorkflowRecoveryModel).filter(
            WorkflowRecoveryModel.workflow_id == workflow_id
        )
        if revision_id:
            query = query.filter(WorkflowRecoveryModel.revision_id == revision_id)
        return query.order_by(WorkflowRecoveryModel.attempt_number.asc()).all()

    def list_recoveries(
        self, workflow_id: str, revision_id: Optional[str] = None
    ) -> List[WorkflowRecoveryModel]:
        """Alias for list_workflow_recoveries."""
        return self.list_workflow_recoveries(workflow_id, revision_id=revision_id)

    def list_recoveries(self, workflow_id: str) -> List[WorkflowRecoveryModel]:
        """Retrieve recovery history for a workflow."""
        return (
            self.db.query(WorkflowRecoveryModel)
            .filter(WorkflowRecoveryModel.workflow_id == workflow_id)
            .order_by(WorkflowRecoveryModel.reserved_at.desc())
            .all()
        )

    # -------------------------------------------------------------------------
    # EXECUTION TELEMETRY & MANAGEMENT (Phase 6)
    # -------------------------------------------------------------------------

    def create_execution(
        self, execution_in: WorkflowExecutionCreate, workflow_id: Optional[str] = None
    ) -> WorkflowExecutionModel:
        """Persist a new execution record with telemetry metadata."""
        target_workflow_id = workflow_id or execution_in.workflow_id
        if not target_workflow_id:
            raise ValueError("workflow_id must be provided to create an execution.")

        parent_wf = self.get_workflow(target_workflow_id, include_inactive=True)
        if not parent_wf:
            raise ValueError(f"Workflow with ID '{target_workflow_id}' does not exist.")

        status_lower = execution_in.status.lower()
        now = utc_now()
        completed_at = now if status_lower in ("completed", "failed", "repaired") else None

        duration = execution_in.execution_duration
        if duration is None and completed_at:
            duration = 0.0

        # Attach active revision ID if not explicitly provided
        target_rev_id = execution_in.revision_id or parent_wf.active_revision_id

        exec_obj = WorkflowExecutionModel(
            workflow_id=target_workflow_id,
            revision_id=target_rev_id,
            status=status_lower,
            input_data=execution_in.input_data or execution_in.input_payload,
            output_data=execution_in.output_data or execution_in.output_result,
            error_message=execution_in.error_message,
            execution_duration=duration,
            repair_attempts=execution_in.repair_attempts,
            node_logs=execution_in.node_logs or [],
            token_usage=execution_in.token_usage,
            ai_provider=execution_in.ai_provider,
            ai_model=execution_in.ai_model,
            estimated_cost=execution_in.estimated_cost,
            reliability_report=execution_in.reliability_report,
            repair_report=execution_in.repair_report,
            started_at=now,
            completed_at=completed_at,
        )

        try:
            self.db.add(exec_obj)
            self.db.commit()
            self.db.refresh(exec_obj)
            return exec_obj
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error("Failed to record execution: %s", exc)
            raise

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecutionModel]:
        """Retrieve a specific execution record by ID."""
        return (
            self.db.query(WorkflowExecutionModel)
            .filter(WorkflowExecutionModel.id == execution_id)
            .first()
        )

    def update_execution(
        self, execution_id: str, execution_update: WorkflowExecutionUpdate
    ) -> Optional[WorkflowExecutionModel]:
        """Update execution telemetry, state transitions, and reports."""
        exec_obj = self.get_execution(execution_id)
        if not exec_obj:
            return None

        update_data = execution_update.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "status" and value is not None:
                exec_obj.status = value.lower()
                if exec_obj.status in ("completed", "failed", "repaired") and not exec_obj.completed_at:
                    exec_obj.completed_at = utc_now()
                    if exec_obj.execution_duration is None:
                        start_dt = ensure_utc(exec_obj.started_at)
                        end_dt = ensure_utc(exec_obj.completed_at)
                        if start_dt and end_dt:
                            exec_obj.execution_duration = max(0.0, (end_dt - start_dt).total_seconds())
            elif field in ("output_data", "output_result") and value is not None:
                exec_obj.output_data = value
            else:
                setattr(exec_obj, field, value)

        try:
            self.db.commit()
            self.db.refresh(exec_obj)
            return exec_obj
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error("Failed to update execution id=%s: %s", execution_id, exc)
            raise

    def list_executions(
        self,
        workflow_id: Optional[str] = None,
        revision_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
    ) -> List[WorkflowExecutionModel]:
        """Fetch execution telemetry with case-insensitive status filtering."""
        query = self.db.query(WorkflowExecutionModel)
        if workflow_id:
            query = query.filter(WorkflowExecutionModel.workflow_id == workflow_id)
        if revision_id:
            query = query.filter(WorkflowExecutionModel.revision_id == revision_id)
        if status:
            query = query.filter(WorkflowExecutionModel.status == status.lower())

        return (
            query.order_by(WorkflowExecutionModel.started_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def delete_execution(self, execution_id: str) -> bool:
        """Delete an execution record."""
        exec_obj = self.get_execution(execution_id)
        if not exec_obj:
            return False

        try:
            self.db.delete(exec_obj)
            self.db.commit()
            return True
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error("Failed to delete execution id=%s: %s", execution_id, exc)
            raise
