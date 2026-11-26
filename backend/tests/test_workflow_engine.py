"""
AgentForge AI - Member 3 Test Suite: Workflow Generation, Component Management & Validation
Tests all 17 required scenarios:
1. Successful workflow generation
2. Generation of all seven supported node types
3. Unique node ID generation
4. Correct edge generation
5. Invalid node configuration
6. Unsupported node types
7. Missing required inputs / handle validation
8. Invalid connections (nonexistent source/target)
9. Disconnected nodes
10. Duplicate node IDs
11. Workflow JSON structure
12. Workflow version compatibility
13. Workflow version comparison
14. Added and removed nodes in diff
15. Modified node configurations in diff
16. Targeted workflow modifications
17. Preservation of original workflow (immutability)
Plus:
- Valid and invalid execution plans
- API endpoint integration
"""

import copy
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.workflow import (
    WorkflowBase,
    WorkflowCreate,
    WorkflowNodeSchema,
    WorkflowEdgeSchema,
    NodePosition,
)
from app.services.workflow import (
    component_library,
    workflow_generator,
    workflow_validator,
    workflow_modifier,
    compare_workflows,
    increment_version,
    restore_version,
    rollback_to_version,
    WorkflowHistory,
    ExecutionPlan,
    ExecutionPlanStep,
    ValidationSeverity,
    ValidationCategory,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_valid_plan() -> ExecutionPlan:
    """A realistic execution plan from Member 2 (AI Architect)."""
    return ExecutionPlan(
        name="Financial Analysis Pipeline",
        description="Reads earnings PDF, extracts summary via Gemini, branches on growth, and outputs report.",
        version="1.0.0",
        steps=[
            ExecutionPlanStep(
                title="User Document Upload",
                component_type="Input",
                config={"inputType": "file_url", "required": True},
                next_steps=["Extract PDF Text"],
            ),
            ExecutionPlanStep(
                title="Extract PDF Text",
                component_type="Document Reader",
                config={"chunkSize": 1200, "chunkOverlap": 150},
                next_steps=["Summarize Financials"],
            ),
            ExecutionPlanStep(
                title="Summarize Financials",
                component_type="LLM",
                config={"model": "gemini-1.5-pro", "temperature": 0.3},
                next_steps=["Evaluate Performance"],
            ),
            ExecutionPlanStep(
                title="Evaluate Performance",
                component_type="Condition",
                config={"operator": "contains", "leftOperand": "revenue", "rightOperand": "positive"},
                branch_conditions={
                    "true": "Generate Executive Summary",
                    "false": "Human Financial Audit",
                },
            ),
            ExecutionPlanStep(
                title="Human Financial Audit",
                component_type="Human Approval",
                config={"promptMessage": "Review negative financial performance indicators."},
                next_steps=["Generate Executive Summary"],
            ),
            ExecutionPlanStep(
                title="Generate Executive Summary",
                component_type="Output",
                config={"outputFormat": "markdown"},
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Test 1 & 2: Generation of workflow & all 7 supported node types
# ---------------------------------------------------------------------------

def test_1_successful_workflow_generation(sample_valid_plan):
    """Test 1: Verify successful workflow generation from a valid execution plan."""
    wf = workflow_generator.generate(sample_valid_plan)
    assert wf is not None
    assert wf.name == "Financial Analysis Pipeline"
    assert len(wf.nodes) == 6
    assert len(wf.edges) == 6  # 4 sequential + 2 branch edges
    assert wf.version == "1.0.0"
    assert "generated" in wf.tags


def test_2_generation_of_all_seven_supported_node_types():
    """Test 2: Verify generation of all 7 canonical node types in a single workflow."""
    plan = ExecutionPlan(
        name="All 7 Node Types Test Plan",
        steps=[
            ExecutionPlanStep(title="Input Step", component_type="Input"),
            ExecutionPlanStep(title="Doc Reader Step", component_type="Document Reader"),
            ExecutionPlanStep(title="LLM Reasoning Step", component_type="LLM"),
            ExecutionPlanStep(title="External API Step", component_type="Tool"),
            ExecutionPlanStep(
                title="Decision Step",
                component_type="Condition",
                branch_conditions={"true": "Approval Gate Step", "false": "Output Terminal Step"},
            ),
            ExecutionPlanStep(title="Approval Gate Step", component_type="Human Approval"),
            ExecutionPlanStep(title="Output Terminal Step", component_type="Output"),
        ],
    )

    wf = workflow_generator.generate(plan)
    generated_types = {n.type for n in wf.nodes}
    expected_types = {
        "Input",
        "LLM",
        "Document Reader",
        "Tool",
        "Condition",
        "Human Approval",
        "Output",
    }
    assert generated_types == expected_types
    assert len(wf.nodes) == 7

    # Validate that generated workflow passes validation
    res = workflow_validator.validate(wf)
    assert res.is_valid is True
    assert res.metrics.supported_nodes_count == 7


# ---------------------------------------------------------------------------
# Test 3: Unique node ID generation
# ---------------------------------------------------------------------------

def test_3_unique_node_id_generation():
    """Test 3: Verify that multiple nodes of the same type receive unique deterministic IDs."""
    plan = ExecutionPlan(
        name="Multi LLM Pipeline",
        steps=[
            ExecutionPlanStep(title="Primary LLM", component_type="LLM"),
            ExecutionPlanStep(title="Critic LLM", component_type="LLM"),
            ExecutionPlanStep(title="Final Polish LLM", component_type="LLM"),
        ],
    )
    wf = workflow_generator.generate(plan)
    node_ids = [n.id for n in wf.nodes]
    assert len(node_ids) == len(set(node_ids))
    assert len(node_ids) == 3
    assert node_ids == ["node_llm_1", "node_llm_2", "node_llm_3"]


# ---------------------------------------------------------------------------
# Test 4: Correct edge generation
# ---------------------------------------------------------------------------

def test_4_correct_edge_generation(sample_valid_plan):
    """Test 4: Verify sequential and conditional edge generation connects correct node IDs."""
    wf = workflow_generator.generate(sample_valid_plan)
    node_map = {n.name: n.id for n in wf.nodes}

    # Verify input -> doc reader
    edge1 = next(
        e for e in wf.edges
        if e.source == node_map["User Document Upload"] and e.target == node_map["Extract PDF Text"]
    )
    assert edge1 is not None

    # Verify condition branches
    cond_true_edge = next(
        e for e in wf.edges
        if e.source == node_map["Evaluate Performance"] and e.condition == "true"
    )
    assert cond_true_edge.target == node_map["Generate Executive Summary"]

    cond_false_edge = next(
        e for e in wf.edges
        if e.source == node_map["Evaluate Performance"] and e.condition == "false"
    )
    assert cond_false_edge.target == node_map["Human Financial Audit"]


# ---------------------------------------------------------------------------
# Test 5: Invalid node configuration
# ---------------------------------------------------------------------------

def test_5_invalid_node_configuration():
    """Test 5: Validator detects invalid config values (e.g. temperature > 1.0, overlap > chunkSize)."""
    invalid_wf = WorkflowBase(
        name="Invalid Config Test",
        nodes=[
            WorkflowNodeSchema(
                id="node_llm_bad",
                type="LLM",
                name="Bad LLM",
                position=NodePosition(x=100, y=100),
                config={"temperature": 2.5, "model": "gemini-1.5-pro"},  # invalid: temp > 1.0
            ),
            WorkflowNodeSchema(
                id="node_doc_bad",
                type="Document Reader",
                name="Bad Doc Reader",
                position=NodePosition(x=300, y=100),
                config={"chunkSize": 500, "chunkOverlap": 800},  # invalid: overlap >= chunkSize
            ),
        ],
        edges=[],
    )
    res = workflow_validator.validate(invalid_wf)
    assert res.is_valid is False
    config_errors = [e for e in res.errors if e.category == ValidationCategory.CONFIGURATION]
    assert len(config_errors) >= 2
    assert any("temperature" in e.description for e in config_errors)
    assert any("chunkOverlap" in e.description for e in config_errors)


# ---------------------------------------------------------------------------
# Test 6: Unsupported node types
# ---------------------------------------------------------------------------

def test_6_unsupported_node_types():
    """Test 6: Validator detects unsupported/bogus node types."""
    invalid_wf = WorkflowBase(
        name="Unsupported Node Type Test",
        nodes=[
            WorkflowNodeSchema(
                id="node_quantum_ai",
                type="Quantum AI Engine",  # type: ignore - unsupported
                name="Quantum Node",
                position=NodePosition(x=100, y=100),
                config={},
            )
        ],
        edges=[],
    )
    res = workflow_validator.validate(invalid_wf)
    assert res.is_valid is False
    unsupported_errs = [e for e in res.errors if "unsupported" in e.title.lower()]
    assert len(unsupported_errs) == 1
    assert unsupported_errs[0].node_id == "node_quantum_ai"


# ---------------------------------------------------------------------------
# Test 7: Missing required inputs / handle validation
# ---------------------------------------------------------------------------

def test_7_missing_required_inputs_and_handle_warnings():
    """Test 7: Validator warns if edge points to non-existent handles on a node."""
    wf = WorkflowBase(
        name="Handle Test",
        nodes=[
            WorkflowNodeSchema(
                id="node_in",
                type="Input",
                name="Input",
                position=NodePosition(x=0, y=0),
                outputHandles=["output"],
            ),
            WorkflowNodeSchema(
                id="node_llm",
                type="LLM",
                name="LLM",
                position=NodePosition(x=200, y=0),
                inputHandles=["prompt", "context"],
            ),
        ],
        edges=[
            WorkflowEdgeSchema(
                id="edge_1",
                source="node_in",
                target="node_llm",
                sourceHandle="non_existent_output",
                targetHandle="non_existent_input",
            )
        ],
    )
    res = workflow_validator.validate(wf)
    warnings = [w for w in res.warnings if "Handle" in w.title]
    assert len(warnings) == 2


# ---------------------------------------------------------------------------
# Test 8: Invalid connections (nonexistent source/target)
# ---------------------------------------------------------------------------

def test_8_invalid_connections_nonexistent_nodes():
    """Test 8: Validator errors out on edges referencing phantom nodes."""
    wf = WorkflowBase(
        name="Phantom Edge Test",
        nodes=[
            WorkflowNodeSchema(
                id="node_1",
                type="Input",
                name="Valid Node",
                position=NodePosition(x=0, y=0),
            )
        ],
        edges=[
            WorkflowEdgeSchema(
                id="edge_phantom_1",
                source="node_1",
                target="node_ghost_target",
            ),
            WorkflowEdgeSchema(
                id="edge_phantom_2",
                source="node_ghost_source",
                target="node_1",
            ),
        ],
    )
    res = workflow_validator.validate(wf)
    assert res.is_valid is False
    conn_errors = [e for e in res.errors if e.category == ValidationCategory.CONNECTION]
    assert len(conn_errors) == 2


# ---------------------------------------------------------------------------
# Test 9: Disconnected / orphaned nodes
# ---------------------------------------------------------------------------

def test_9_disconnected_orphaned_nodes():
    """Test 9: Validator flags completely disconnected components in multi-node workflows."""
    wf = WorkflowBase(
        name="Disconnected Node Test",
        nodes=[
            WorkflowNodeSchema(
                id="node_in",
                type="Input",
                name="Input",
                position=NodePosition(x=0, y=0),
            ),
            WorkflowNodeSchema(
                id="node_out",
                type="Output",
                name="Output",
                position=NodePosition(x=400, y=0),
            ),
            WorkflowNodeSchema(
                id="node_orphan",
                type="Tool",
                name="Forgotten Web Search",
                position=NodePosition(x=200, y=200),
            ),
        ],
        edges=[
            WorkflowEdgeSchema(id="edge_in_out", source="node_in", target="node_out")
        ],
    )
    res = workflow_validator.validate(wf)
    assert res.is_valid is False
    orphan_errors = [e for e in res.errors if e.id == "disconnected_node_node_orphan"]
    assert len(orphan_errors) == 1
    assert res.metrics.disconnected_nodes_count == 1


# ---------------------------------------------------------------------------
# Test 10: Duplicate node IDs
# ---------------------------------------------------------------------------

def test_10_duplicate_node_ids():
    """Test 10: Validator strictly flags duplicate node IDs."""
    wf = WorkflowBase(
        name="Duplicate IDs Test",
        nodes=[
            WorkflowNodeSchema(
                id="duplicate_node_id",
                type="Input",
                name="First Node",
                position=NodePosition(x=0, y=0),
            ),
            WorkflowNodeSchema(
                id="duplicate_node_id",
                type="Output",
                name="Second Node With Same ID",
                position=NodePosition(x=200, y=0),
            ),
        ],
        edges=[],
    )
    res = workflow_validator.validate(wf)
    assert res.is_valid is False
    dup_errors = [e for e in res.errors if "Duplicate Node ID" in e.title]
    assert len(dup_errors) == 1
    assert dup_errors[0].node_id == "duplicate_node_id"


# ---------------------------------------------------------------------------
# Test 11: Workflow JSON structure & Schema conformance
# ---------------------------------------------------------------------------

def test_11_workflow_json_structure(sample_valid_plan):
    """Test 11: Validate generated JSON has required keys matching shared/workflow.schema.json."""
    wf = workflow_generator.generate(sample_valid_plan)
    json_data = wf.model_dump()

    assert "name" in json_data
    assert "version" in json_data
    assert "configuration" in json_data
    assert "nodes" in json_data
    assert "edges" in json_data

    # Check node structure
    for node in json_data["nodes"]:
        assert "id" in node
        assert "type" in node
        assert "name" in node
        assert "position" in node
        assert "x" in node["position"]
        assert "y" in node["position"]
        assert "config" in node

    # Check edge structure
    for edge in json_data["edges"]:
        assert "id" in edge
        assert "source" in edge
        assert "target" in edge

    # Canonical schema definition export
    definition = workflow_generator.to_workflow_definition(wf)
    assert definition["schemaVersion"] == "1.0.0"
    assert "metadata" in definition
    assert "id" in definition["metadata"]
    assert definition["metadata"]["name"] == wf.name
    assert "createdAt" in definition["metadata"]
    assert "updatedAt" in definition["metadata"]
    assert len(definition["nodes"]) == len(wf.nodes)
    assert len(definition["edges"]) == len(wf.edges)

    # Validate canonical definition through validator
    canonical_res = workflow_validator.validate(definition)
    assert canonical_res.is_valid is True

    # Reconstruct back via from_workflow_definition
    reconstructed = workflow_generator.from_workflow_definition(definition)
    assert reconstructed.name == wf.name
    assert len(reconstructed.nodes) == len(wf.nodes)
    assert len(reconstructed.edges) == len(wf.edges)


# ---------------------------------------------------------------------------
# Test 12: Workflow version compatibility
# ---------------------------------------------------------------------------

def test_12_workflow_version_compatibility():
    """Test 12: Test semver incrementing and version compatibility checks."""
    assert increment_version("1.0.0", "patch") == "1.0.1"
    assert increment_version("1.0.0", "minor") == "1.1.0"
    assert increment_version("1.0.0", "major") == "2.0.0"

    v1 = WorkflowBase(
        name="V1 Workflow",
        version="1.0.0",
        nodes=[
            WorkflowNodeSchema(id="in_1", type="Input", name="In", position=NodePosition(x=0, y=0)),
            WorkflowNodeSchema(id="out_1", type="Output", name="Out", position=NodePosition(x=200, y=0)),
        ],
        edges=[WorkflowEdgeSchema(id="e1", source="in_1", target="out_1")],
    )

    # V2 removes the Input node - breaking external contract
    v2 = WorkflowBase(
        name="V2 Incompatible",
        version="2.0.0",
        nodes=[
            WorkflowNodeSchema(id="llm_1", type="LLM", name="Solo LLM", position=NodePosition(x=100, y=0)),
        ],
        edges=[],
    )

    diff = compare_workflows(v1, v2)
    assert diff.is_compatible is False


# ---------------------------------------------------------------------------
# Test 13: Workflow version comparison
# ---------------------------------------------------------------------------

def test_13_workflow_version_comparison():
    """Test 13: Compare two versions and verify diff object captures all structural delta."""
    v1 = WorkflowBase(
        name="Search Pipeline",
        version="1.0.0",
        nodes=[
            WorkflowNodeSchema(id="n_in", type="Input", name="Prompt", position=NodePosition(x=0, y=0)),
            WorkflowNodeSchema(id="n_tool", type="Tool", name="Search", position=NodePosition(x=200, y=0)),
        ],
        edges=[WorkflowEdgeSchema(id="e1", source="n_in", target="n_tool")],
    )

    v2 = WorkflowBase(
        name="Search Pipeline Enhanced",
        version="1.1.0",
        nodes=[
            WorkflowNodeSchema(id="n_in", type="Input", name="Prompt", position=NodePosition(x=0, y=0)),
            WorkflowNodeSchema(
                id="n_tool",
                type="Tool",
                name="Search",
                position=NodePosition(x=200, y=0),
                config={"timeoutSeconds": 45},  # Modified config
            ),
            WorkflowNodeSchema(id="n_out", type="Output", name="Output", position=NodePosition(x=400, y=0)),  # Added node
        ],
        edges=[
            WorkflowEdgeSchema(id="e1", source="n_in", target="n_tool"),
            WorkflowEdgeSchema(id="e2", source="n_tool", target="n_out"),  # Added edge
        ],
    )

    diff = compare_workflows(v1, v2)
    assert diff.version_from == "1.0.0"
    assert diff.version_to == "1.1.0"
    assert len(diff.added_nodes) == 1
    assert diff.added_nodes[0].id == "n_out"
    assert len(diff.modified_nodes) == 1
    assert diff.modified_nodes[0].node_id == "n_tool"
    assert len(diff.added_edges) == 1
    assert diff.added_edges[0].id == "e2"
    assert diff.is_compatible is True


# ---------------------------------------------------------------------------
# Test 14: Added and removed nodes tracking
# ---------------------------------------------------------------------------

def test_14_added_and_removed_nodes_tracking():
    """Test 14: Accurately tracks both added and removed nodes."""
    v1 = WorkflowBase(
        name="Old Pipeline",
        version="1.0.0",
        nodes=[
            WorkflowNodeSchema(id="node_a", type="Input", name="A", position=NodePosition(x=0, y=0)),
            WorkflowNodeSchema(id="node_b", type="Tool", name="B", position=NodePosition(x=200, y=0)),
        ],
        edges=[],
    )

    v2 = WorkflowBase(
        name="New Pipeline",
        version="1.1.0",
        nodes=[
            WorkflowNodeSchema(id="node_a", type="Input", name="A", position=NodePosition(x=0, y=0)),
            WorkflowNodeSchema(id="node_c", type="LLM", name="C", position=NodePosition(x=300, y=0)),
        ],
        edges=[],
    )

    diff = compare_workflows(v1, v2)
    assert len(diff.removed_nodes) == 1
    assert diff.removed_nodes[0].id == "node_b"
    assert len(diff.added_nodes) == 1
    assert diff.added_nodes[0].id == "node_c"


# ---------------------------------------------------------------------------
# Test 15: Modified node configurations tracking
# ---------------------------------------------------------------------------

def test_15_modified_node_configurations_tracking():
    """Test 15: Accurately captures before and after values for changed node config parameters."""
    v1 = WorkflowBase(
        name="LLM Tuning",
        version="1.0.0",
        nodes=[
            WorkflowNodeSchema(
                id="llm_1",
                type="LLM",
                name="Reasoning Agent",
                position=NodePosition(x=100, y=100),
                config={"model": "gemini-1.5-pro", "temperature": 0.2},
            )
        ],
        edges=[],
    )

    v2 = WorkflowBase(
        name="LLM Tuning",
        version="1.0.1",
        nodes=[
            WorkflowNodeSchema(
                id="llm_1",
                type="LLM",
                name="Reasoning Agent",
                position=NodePosition(x=100, y=100),
                config={"model": "gemini-1.5-pro", "temperature": 0.8},
            )
        ],
        edges=[],
    )

    diff = compare_workflows(v1, v2)
    assert len(diff.modified_nodes) == 1
    mod = diff.modified_nodes[0]
    assert mod.node_id == "llm_1"
    assert "temperature" in mod.config_changes
    assert mod.config_changes["temperature"]["before"] == 0.2
    assert mod.config_changes["temperature"]["after"] == 0.8


# ---------------------------------------------------------------------------
# Test 16: Targeted workflow modifications
# ---------------------------------------------------------------------------

def test_16_targeted_workflow_modifications(sample_valid_plan):
    """Test 16: Test targeted modifications (config update, add node, remove node with reconnect)."""
    wf = workflow_generator.generate(sample_valid_plan)
    original_node_count = len(wf.nodes)

    # 1. Update LLM prompt and temperature
    updated_wf = workflow_modifier.update_node_config(
        wf,
        node_id="node_llm_1",
        config_updates={"temperature": 0.1, "systemPrompt": "You are an expert equity research analyst."},
    )
    llm_node = next(n for n in updated_wf.nodes if n.id == "node_llm_1")
    assert llm_node.config["temperature"] == 0.1
    assert "equity research" in llm_node.config["systemPrompt"]
    assert updated_wf.version == "1.0.1"

    # 2. Add an intermediate tool node after Extract PDF Text
    tool_node = WorkflowNodeSchema(
        id="node_sec_filing_search",
        type="Tool",
        name="SEC Filing Web Query",
        position=NodePosition(x=300, y=250),
        config={"toolName": "web_search"},
    )
    with_tool_wf = workflow_modifier.add_node(
        updated_wf,
        node=tool_node,
        connect_after_node_id="node_document_reader_1",
        connect_before_node_id="node_llm_1",
    )
    assert len(with_tool_wf.nodes) == original_node_count + 1
    assert with_tool_wf.version == "1.1.0"

    # 3. Remove Human Audit node and reconnect
    without_audit_wf = workflow_modifier.remove_node(
        with_tool_wf,
        node_id="node_human_approval_1",
        reconnect=True,
    )
    assert not any(n.id == "node_human_approval_1" for n in without_audit_wf.nodes)
    assert without_audit_wf.version == "1.2.0"


# ---------------------------------------------------------------------------
# Test 17: Preservation of the original workflow (immutability)
# ---------------------------------------------------------------------------

def test_17_preservation_of_original_workflow(sample_valid_plan):
    """Test 17: Verify original workflow remains strictly unmodified when new versions are generated."""
    wf_original = workflow_generator.generate(sample_valid_plan)
    original_dump = copy.deepcopy(wf_original.model_dump())

    # Perform extensive modifications
    wf_v2 = workflow_modifier.update_node_config(wf_original, "node_llm_1", {"temperature": 0.05})
    wf_v3 = workflow_modifier.add_node(
        wf_v2,
        WorkflowNodeSchema(
            id="brand_new_node",
            type="Output",
            name="Backup Export",
            position=NodePosition(x=800, y=200),
            config={"outputFormat": "json"},
        )
    )

    # Verify original workflow is 100% byte-for-byte identical to its initial state
    assert wf_original.model_dump() == original_dump
    assert wf_original.version == "1.0.0"
    assert len(wf_original.nodes) == len(original_dump["nodes"])


# ---------------------------------------------------------------------------
# API Endpoints Integration Tests
# ---------------------------------------------------------------------------

def test_api_component_catalog():
    """Verify GET /api/v1/workflows/components returns all 7 components."""
    response = client.get("/api/v1/workflows/components")
    assert response.status_code == 200
    data = response.json()
    assert data["total_components"] == 7
    types = [c["type"] for c in data["components"]]
    assert "Input" in types
    assert "LLM" in types
    assert "Human Approval" in types


def test_api_workflow_generation(sample_valid_plan):
    """Verify POST /api/v1/workflows/generate builds valid workflow JSON."""
    payload = sample_valid_plan.model_dump()
    response = client.post("/api/v1/workflows/generate", json=payload)
    assert response.status_code == 201
    wf_data = response.json()
    assert wf_data["name"] == "Financial Analysis Pipeline"
    assert len(wf_data["nodes"]) == 6


def test_api_workflow_validate(sample_valid_plan):
    """Verify POST /api/v1/workflows/validate evaluates validity correctly."""
    wf = workflow_generator.generate(sample_valid_plan)
    response = client.post("/api/v1/workflows/validate", json={"workflow": wf.model_dump()})
    assert response.status_code == 200
    result = response.json()
    assert result["is_valid"] is True
    assert result["metrics"]["total_nodes"] == 6


def test_api_workflow_modify(sample_valid_plan):
    """Verify POST /api/v1/workflows/modify applies patches and returns diff."""
    wf = workflow_generator.generate(sample_valid_plan)
    patch = {
        "update_configs": [
            {"node_id": "node_llm_1", "config": {"temperature": 0.4}}
        ],
        "bump_version": "patch",
    }
    response = client.post(
        "/api/v1/workflows/modify",
        json={"workflow": wf.model_dump(), "patch": patch},
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["workflow"]["version"] == "1.0.1"
    assert res_data["diff"]["has_changes"] is True
    assert len(res_data["diff"]["modified_nodes"]) == 1


# ---------------------------------------------------------------------------
# Test: Workflow Rollback Preservation & Immutability
# ---------------------------------------------------------------------------

def test_workflow_rollback_preservation_and_immutability(sample_valid_plan):
    """
    Verifies that:
    1. restore_version creates an independent exact replica preserving node IDs, connections, and configurations.
    2. rollback_to_version creates a new forward version restoring target topology and configurations.
    3. Neither original historical versions nor current versions are unexpectedly mutated.
    4. WorkflowHistory correctly tracks revisions and executes rollback without corrupting past snapshots.
    """
    # 1. Generate baseline workflow v1 (version 1.0.0)
    wf_v1 = workflow_generator.generate(sample_valid_plan)
    wf_v1.version = "1.0.0"
    v1_dump = copy.deepcopy(wf_v1.model_dump())
    v1_node_ids = {n.id for n in wf_v1.nodes}
    v1_edge_ids = {e.id for e in wf_v1.edges}

    # Verify restore_version directly
    restored_v1 = restore_version(wf_v1)
    assert restored_v1.name == wf_v1.name
    assert {n.id for n in restored_v1.nodes} == v1_node_ids
    assert {e.id for e in restored_v1.edges} == v1_edge_ids
    # Check that mutating restored does not mutate wf_v1
    restored_v1.nodes[0].name = "Mutated Name"
    assert wf_v1.nodes[0].name != "Mutated Name"

    # 2. Apply a modification to create v2 (version 1.1.0)
    patch = {
        "update_configs": [
            {"node_id": "node_llm_1", "config": {"temperature": 0.95}}
        ],
        "add_nodes": [
            {
                "type": "Tool",
                "name": "Audit Logging Tool",
                "position": {"x": 800, "y": 400},
                "config": {"tool_name": "audit_logger"},
            }
        ],
        "bump_version": "minor",
    }
    wf_v2, diff_v1_to_v2 = workflow_modifier.apply_patch(wf_v1, patch)
    v2_dump = copy.deepcopy(wf_v2.model_dump())
    assert wf_v2.version == "1.1.0"
    assert len(wf_v2.nodes) == len(wf_v1.nodes) + 1

    # 3. Rollback from v2 to v1
    rolled_back_wf, rollback_diff = rollback_to_version(wf_v2, wf_v1, bump="minor")

    # Assert new forward version number (1.2.0)
    assert rolled_back_wf.version == "1.2.0"

    # Assert target topology and configuration preservation
    assert len(rolled_back_wf.nodes) == len(wf_v1.nodes)
    assert {n.id for n in rolled_back_wf.nodes} == v1_node_ids
    assert {e.id for e in rolled_back_wf.edges} == v1_edge_ids

    # Assert specific node config rolled back
    target_llm = next(n for n in wf_v1.nodes if n.id == "node_llm_1")
    rolled_back_llm = next(n for n in rolled_back_wf.nodes if n.id == "node_llm_1")
    assert rolled_back_llm.config["temperature"] == target_llm.config["temperature"]

    # Assert diff reflects the rollback removal of the newly added node in v2
    assert rollback_diff.has_changes is True
    assert len(rollback_diff.removed_nodes) == 1
    assert rollback_diff.removed_nodes[0].name == "Audit Logging Tool"

    # 4. Strict immutability: Ensure historical wf_v1 and wf_v2 are completely unmodified
    assert wf_v1.model_dump() == v1_dump
    assert wf_v2.model_dump() == v2_dump

    # 5. WorkflowHistory class verification
    history = WorkflowHistory()
    history.save_version(wf_v1)
    history.save_version(wf_v2)
    assert history.list_versions() == ["1.0.0", "1.1.0"]

    rolled_from_history, hist_diff = history.rollback(target_version="1.0.0", bump="minor")
    assert rolled_from_history.version == "1.2.0"
    assert len(rolled_from_history.nodes) == len(wf_v1.nodes)
    assert history.list_versions() == ["1.0.0", "1.1.0", "1.2.0"]

    # Past snapshots in history remain intact
    assert history.get_version("1.0.0").model_dump() == v1_dump
    assert history.get_version("1.1.0").model_dump() == v2_dump


# ---------------------------------------------------------------------------
# Test: Workflow Performance Tracking Configuration
# ---------------------------------------------------------------------------

def test_workflow_performance_tracking_configuration(sample_valid_plan):
    """
    Verifies that generated workflows contain configuration and metadata to support
    runtime execution performance tracking (duration, status, timestamps, metrics)
    WITHOUT inventing hallucinated runtime metrics during workflow generation.
    """
    wf = workflow_generator.generate(sample_valid_plan)

    # 1. Performance tracking flag on workflow configuration
    assert hasattr(wf.configuration, "collectMetrics")
    assert wf.configuration.collectMetrics is True
    assert wf.configuration.timeoutSeconds > 0

    # 2. Output node execution metrics reporting flag
    output_nodes = [n for n in wf.nodes if n.type == "Output"]
    assert len(output_nodes) > 0
    for out_node in output_nodes:
        assert "includeExecutionMetrics" in out_node.config
        assert out_node.config["includeExecutionMetrics"] is True

    # 3. Timestamp metadata for lifecycle and duration tracking
    definition = workflow_generator.to_workflow_definition(wf)
    metadata = definition.get("metadata", {})
    assert "createdAt" in metadata
    assert "updatedAt" in metadata
    # Verify ISO-8601 formatting
    assert "T" in metadata["createdAt"]
    assert "T" in metadata["updatedAt"]

    # 4. Strict check: static workflow generation does NOT invent fake runtime values
    # (e.g. execution duration, runtime status like 'completed', execution logs)
    wf_dict = wf.model_dump()
    for node in wf_dict.get("nodes", []):
        assert "executionDuration" not in node
        assert "runtimeStatus" not in node
        assert "logs" not in node
        assert "executionTimeMs" not in node


# ---------------------------------------------------------------------------
# Test: API Workflow Rollback Endpoint
# ---------------------------------------------------------------------------

def test_api_workflow_rollback(sample_valid_plan):
    """Verify POST /api/v1/workflows/rollback restores target workflow version."""
    wf_v1 = workflow_generator.generate(sample_valid_plan)
    wf_v1.version = "1.0.0"

    patch = {
        "update_configs": [
            {"node_id": "node_llm_1", "config": {"temperature": 0.1}}
        ],
        "bump_version": "minor",
    }
    wf_v2, _ = workflow_modifier.apply_patch(wf_v1, patch)

    payload = {
        "current": wf_v2.model_dump(),
        "target": wf_v1.model_dump(),
        "bump_version": "minor",
    }
    response = client.post("/api/v1/workflows/rollback", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["workflow"]["version"] == "1.2.0"
    assert data["diff"]["has_changes"] is True
    # Verify temperature reverted back to original
    reverted_llm = next(n for n in data["workflow"]["nodes"] if n["id"] == "node_llm_1")
    original_llm = next(n for n in wf_v1.nodes if n.id == "node_llm_1")
    assert reverted_llm["config"]["temperature"] == original_llm.config["temperature"]
