"""Member 6 bridge to Member 5's published, in-process WorkflowValidator."""
from typing import Protocol

from app.schemas.repair import VerificationStatus
from app.services.repair.graph_policy import read_graph
from app.services.repair.service import WorkflowSnapshot


class ValidationReport(Protocol):
    workflow_id: str | None
    is_valid: bool
    total_nodes: int
    total_connections: int
    errors: list


class PublishedValidator(Protocol):
    def validate(self, nodes: list, edges: list, workflow_id: str) -> ValidationReport: ...


class Member5StructuralValidation:
    def __init__(self, validator: PublishedValidator):
        self.validator = validator

    def check(self, candidate: WorkflowSnapshot) -> VerificationStatus:
        graph = read_graph(candidate)
        nodes, edges = graph["nodes"], graph["edges"]
        counts = len(nodes), len(edges)
        report = self.validator.validate(nodes=nodes, edges=edges, workflow_id=candidate.workflow_id)
        if (report.workflow_id != candidate.workflow_id or (report.total_nodes, report.total_connections) != counts
                or type(report.is_valid) is not bool or not isinstance(report.errors, list)
                or report.is_valid == bool(report.errors)):
            return VerificationStatus.NOT_RUN
        return VerificationStatus.PASSED if report.is_valid else VerificationStatus.FAILED
