"""Standalone Member 6 demonstration. All team adapters here are fixtures."""

import json
from dataclasses import replace
from typing import Literal

from fastapi import Request
from pydantic import TypeAdapter

from app.schemas.repair import CandidateExecution, FailureInformation, TestVerification, VerificationResult
from app.services.repair.diagnosis import (
    AcceptanceCriterion,
    ConfigurationEvidence,
    ConfigurationFieldDefinition,
    DiagnosisContext,
    DiagnosticCode,
    DiagnosticNode,
    OriginalRequirements,
)
from app.services.repair.gemini_diagnosis import ProviderIssue, ProviderReply
from app.services.repair.graph_policy import GraphPermit, PortPair, fingerprint
from app.services.repair.history import HistoryPage, StoredRecovery
from app.services.repair.integration import RepairBindings, RepairService
from app.services.repair.planning import (
    ConfigurationLayout,
    FieldPurpose,
    ReplacementProvenance,
    ReplacementSource,
    ScalarFieldPolicy,
    TrustedReplacement,
)
from app.services.repair.recovery_contracts import (
    AttemptReservation,
    BaselineTest,
    CandidateEvidence,
    RecoveryScope,
    RevisionConflict,
    RevisionUpdate,
    VerificationBaseline,
)
from app.services.repair.service import WorkflowSnapshot


class DemoTeam:
    """In-memory examples of the interfaces. This class is never wired into the API."""

    def __init__(self, *, error: DiagnosticCode = DiagnosticCode.MISSING_REQUIRED_CONFIGURATION, regression: bool = False,
                 workflow_id: str = "demo-workflow"):
        self.scope = RecoveryScope(workflow_id=workflow_id, workflow_revision_id="demo-original", execution_run_id="demo-run")
        graph = {"nodes": [{"id": "output", "type": "Output", "config": {}}], "edges": []}
        working = {"nodes": [{"id": "output", "type": "Output", "config": {"outputFormat": "json"}}], "edges": []}
        self.original = WorkflowSnapshot(self.scope.workflow_id, self.scope.workflow_revision_id, json.dumps(graph))
        self.last_working = WorkflowSnapshot(self.scope.workflow_id, "demo-working", json.dumps(working))
        self.active = self.original
        self.requirements = OriginalRequirements("Return JSON.", (AcceptanceCriterion("format", "Output format is JSON."),))
        self.failure = FailureInformation(
            **self.scope.model_dump(), failed_node_id="output", error_code=error,
            error_message="Synthetic failure from the standalone demonstration.", failed_test_ids=("failed-format",),
        )
        self.context = DiagnosisContext(
            self.scope.workflow_id, self.scope.workflow_revision_id, self.scope.execution_run_id,
            (DiagnosticNode("output", "Output", {}),), ConfigurationEvidence("output", "outputFormat", True),
        )
        self.definition = ConfigurationFieldDefinition("outputFormat", required=True, allow_automatic_repair=True)
        self.regression = regression
        self.claimed = False
        self.reserved: list[int] = []
        self.finished = None
        self.events = []
        self.candidates: list[WorkflowSnapshot] = []

    def bindings(self) -> RepairBindings:
        return RepairBindings(
            access=self, failures=self, requirements=self, replacements=self, snapshots=self, attempts=self,
            verifier=self, lifecycle=self, recorder=self, gemini=self,
            policies={"Output": (ScalarFieldPolicy(
                self.definition, "demo-schema", ConfigurationLayout.NODE_CONFIG,
                FieldPurpose.DATA, TypeAdapter(Literal["json"]),
            ),)},
        )

    def allows(self, request, scope, action):
        return scope == self.scope

    def get_failure(self, scope):
        return (self.failure, self.context) if scope == self.scope else None

    def get_original_requirements(self, workflow_id, revision_id):
        return self.requirements

    def save_snapshot(self, workflow_id, revision_id):
        if revision_id != self.active.revision_id:
            raise RevisionConflict()
        return self.original

    def get_replacement(self, target):
        value = json.loads(self.last_working.graph_json)["nodes"][0]["config"][target.field_name]
        return TrustedReplacement(value, ReplacementProvenance(
            target, self.last_working.revision_id, ReplacementSource.LAST_KNOWN_WORKING_REVISION,
        ))

    def begin(self, scope):
        if self.claimed:
            return AttemptReservation.CONFLICT
        self.claimed = True
        return AttemptReservation.RESERVED

    def reserve(self, scope, number, *, limit):
        if number > limit:
            return AttemptReservation.LIMIT_REACHED
        if not self.claimed or number != len(self.reserved) + 1:
            return AttemptReservation.CONFLICT
        self.reserved.append(number)
        return AttemptReservation.RESERVED

    def finish(self, scope, result):
        self.finished = result

    def get_baseline(self, workflow_id, revision_id, execution_run_id):
        return VerificationBaseline(
            workflow_id=workflow_id, workflow_revision_id=revision_id, execution_run_id=execution_run_id,
            failed_tests=(BaselineTest(test_id="failed-format", definition_revision_id="demo-test-v1"),),
            regression_tests=(BaselineTest(test_id="regression-shape", definition_revision_id="demo-test-v1"),),
        )

    def verify(self, candidate, baseline):
        self.candidates.append(candidate)
        graph = json.loads(candidate.graph_json)
        node, = graph["nodes"]
        assert node["id"] == "output" and node["type"] == "Output" and not graph["edges"]
        rendered = json.dumps({"document": "example"}) if node["config"]["outputFormat"] == "json" else ""
        assert json.loads(rendered)["document"] == "example"
        expected_document = "fixture regression" if self.regression else "example"
        regression_status = "passed" if json.loads(rendered)["document"] == expected_document else "failed"
        return CandidateEvidence(candidate.workflow_id, baseline, VerificationResult(
            candidate_revision_id=candidate.revision_id,
            structural_validation="passed",
            execution=CandidateExecution(run_id="demo-candidate-run", status="passed"),
            required_failed_test_ids=("failed-format",),
            required_regression_test_ids=("regression-shape",),
            failed_test_reruns=(TestVerification(test_id="failed-format", status="passed"),),
            regression_test_reruns=(TestVerification(test_id="regression-shape", status=regression_status),),
        ))

    def promote_candidate(self, candidate, *, expected_revision_id):
        if self.active.revision_id != expected_revision_id:
            return RevisionUpdate.CONFLICT
        self.active = candidate
        return RevisionUpdate.CONFIRMED

    def find_last_working_snapshot(self, workflow_id):
        return self.last_working

    def restore_snapshot(self, snapshot, *, expected_revision_id):
        return self.promote_candidate(snapshot, expected_revision_id=expected_revision_id)

    def record_attempt(self, original, execution_run_id, attempt):
        self.events.append(attempt)

    def record_outcome(self, result):
        self.events.append(result)

    def generate(self, context):
        return ProviderReply(issue=ProviderIssue.SDK_UNAVAILABLE)


class GraphDemo(DemoTeam):
    """A two-node public text transfer. No provider, database, or external tool."""

    def __init__(self, *, missing=False, workflow_id="demo-workflow"):
        super().__init__(workflow_id=workflow_id)
        self.ports = PortPair(source="input", target="output", sourceHandle="text", targetHandle="document")
        edge = {"id": "transfer", **self.ports.model_dump()}
        graph = {"nodes": [{"id": "input", "type": "Input", "outputHandles": ["text"]},
                           {"id": "output", "type": "Output", "inputHandles": ["document"]}],
                 "edges": [edge], "requirements": ["Transfer public text"], "testCriteria": ["Preserve text"]}
        self.last_working = replace(self.last_working, graph_json=json.dumps(graph))
        graph["edges"] = [] if missing else [{**edge, "targetHandle": "unknown"}]
        self.original = replace(self.original, graph_json=json.dumps(graph))
        self.active = self.original
        self.failure = self.failure.model_copy(update={"error_code": "NO_PATH_TO_OUTPUT" if missing else "INVALID_TARGET_HANDLE"})
        self.context = replace(self.context, configuration_evidence=None, affected_connection_id="transfer")
        self.permission = GraphPermit(**self.scope.model_dump(), failed_node_id="output", error_code=self.failure.error_code,
            edge_id="transfer", operation="restore_connection" if missing else "restore_mapping",
            policy_id="fixture-public-transfer", schema_id="member3-named-handles-v1", fingerprint=fingerprint(graph),
            source_revision_id=self.last_working.revision_id, ports=self.ports, source_type="string", target_type="string",
            classification="public_data", verification="structure_execution_failed_and_regression_tests")

    def bindings(self):
        return replace(super().bindings(), graph_authority=self, history=self)

    def permit(self, failure, edge_id):
        return self.permission if edge_id == "transfer" and failure == self.failure else None

    def working_snapshot(self, permit):
        return self.last_working

    def read(self, request, scope, offset, limit):
        if not self.allows(request, scope, "history"):
            raise PermissionError
        records = (StoredRecovery("demo-recovery", self.finished),) if self.finished else ()
        return HistoryPage(scope, records[offset:offset + limit])

    def verify(self, candidate, baseline):
        graph = json.loads(candidate.graph_json)
        edge, = graph["edges"]
        def transfer(sample):
            output = {edge["targetHandle"]: {"text": sample}[edge["sourceHandle"]]}
            return output.get("document")
        def check(test, sample):
            return TestVerification(test_id=test.test_id, status="passed" if transfer(sample) == sample else "failed")
        return CandidateEvidence(candidate.workflow_id, baseline, VerificationResult(
            candidate_revision_id=candidate.revision_id,
            structural_validation="passed" if graph == json.loads(self.last_working.graph_json) else "failed",
            execution=CandidateExecution(run_id="fixture-transfer-run", status="passed"),
            required_failed_test_ids=("failed-format",), required_regression_test_ids=("regression-shape",),
            failed_test_reruns=(check(baseline.failed_tests[0], "sample"),),
            regression_test_reruns=(check(baseline.regression_tests[0], ""),)))


def graph_demo():
    request = Request({"type": "http"})
    report = {}
    for name, team in (("missing_connection", GraphDemo(missing=True)), ("mapping", GraphDemo()),
                       ("unapproved_connection", GraphDemo(missing=True))):
        bindings = team.bindings()
        if name == "unapproved_connection":
            bindings = replace(bindings, graph_authority=None)
        service = RepairService(bindings)
        code, outcome = service.run(team.scope, request, "recover")
        assert code == 200 and outcome.status == ("human_review" if name == "unapproved_connection" else "promoted")
        report[name] = outcome.status
        code, page = service.history(team.scope, request, 0, 10)
        assert code == 200 and page.records[0].status == outcome.status
        report["history_" + name] = page.records[0].status
    return report


def run_demo() -> dict:
    request = Request({"type": "http", "method": "POST", "path": "/demo"})
    scenarios = {
        "A_controlled_repair": (DemoTeam(), "promoted"),
        "B_missing_credentials": (DemoTeam(error=DiagnosticCode.MISSING_API_CREDENTIALS), "human_review"),
        "C_failed_regression": (DemoTeam(regression=True), "rolled_back"),
        "D_missing_dependencies": (DemoTeam(), "dependencies_unavailable"),
        "E_stale_revision": (DemoTeam(), "revision_conflict"),
    }
    report = {}
    for name, (team, expected) in scenarios.items():
        if name.startswith("E_"):
            team.active = replace(team.original, revision_id="demo-newer-edit")
        bindings = RepairBindings() if name.startswith("D_") else team.bindings()
        _, outcome = RepairService(bindings).run(team.scope, request, "recover")
        assert outcome.status == expected
        assert json.loads(team.original.graph_json)["nodes"][0]["config"] == {}
        assert team.requirements.acceptance_criteria[0].description == "Output format is JSON."
        report[name] = {"status": outcome.status, "attempts": len(outcome.attempts), "rollback": outcome.rollback}
    return report


if __name__ == "__main__":
    print("Member 6 demonstration · synthetic data and fixture adapters")
    print(json.dumps({**run_demo(), **graph_demo()}, indent=2))
