# AgentForge AI — Member 3: Workflow Generation & Component Management

## 1. Overview & Architecture

Member 3 owns the **Workflow Component Library**, the **Workflow Generation Engine**, **Graph Validation**, **Version Compatibility & Change Tracking**, and **Targeted Modification & Self-Repair Interfaces**.

This engine transforms structured AI Execution Plans synthesized by Member 2 (AI Architect) into executable, directed workflow graphs formatted for `@xyflow/react` on the frontend and LangGraph execution on Member 4/5's runtime.

```
+-----------------------------------------------------------------------------------+
|                        MEMBER 2: AI ARCHITECT EXECUTION PLAN                       |
|   { "name": "...", "steps": [ { "title": "...", "component_type": "LLM", ... } ] } |
+-----------------------------------------|-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                     MEMBER 3: WORKFLOW GENERATION ENGINE                          |
|                                                                                   |
|   +--------------------------+   +-----------------------+                        |
|   | 7-Node Component Library |   | Spatial Layout Engine |                        |
|   | - Canonical Configs      |   | - React Flow (X, Y)   |                        |
|   | - Handle Definitions     |   | - Horizontal Flow     |                        |
|   +--------------------------+   +-----------------------+                        |
|                                                                                   |
|   +--------------------------+   +-----------------------+                        |
|   | Comprehensive Validator  |   | Versioning & Diffing  |                        |
|   | - Topology & Cycles      |   | - SemVer Revisions    |                        |
|   | - Handle & Edge Integrity|   | - Immutability Engine |                        |
|   +--------------------------+   +-----------------------+                        |
+-----------------------------------------|-----------------------------------------+
                                          |
                      +-------------------+-------------------+
                      |                                       |
                      v                                       v
+-------------------------------------------+ +-------------------------------------+
|        FRONTEND (React Flow UI)           | |    MEMBER 4: EXECUTION ENGINE       |
|  - Canvas node rendering                  | |  - LangGraph StateGraph compilation |
|  - Real-time connection handles           | |  - Async execution & sandbox tools  |
|  - Configuration parameter drawer         | |  - Self-repair loop triggers        |
+-------------------------------------------+ +-------------------------------------+
```

---

## 2. The 7 Canonical Workflow Components

The component library maintains structured Pydantic configuration schemas and validation rules for each node type:

| Node Type | Category | Icon | Default Inputs | Default Outputs | Key Configuration Parameters |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Input** | `IO` | `FileInput` | `[]` | `["output"]` | `inputType` (text/json/file_url), `required`, `placeholder` |
| **LLM** | `AI` | `Bot` | `["prompt", "context"]` | `["response", "tokens"]` | `model` (e.g. gemini-1.5-pro), `temperature` (0.0-1.0), `systemPrompt`, `maxOutputTokens`, `responseFormat` |
| **Document Reader**| `Data` | `FileText` | `["filePath"]` | `["content", "metadata"]` | `chunkSize` (50-10000), `chunkOverlap` (< chunkSize), `extractTables`, `supportedExtensions` |
| **Tool** | `Action` | `Wrench` | `["params"]` | `["result", "error"]` | `toolName` (web_search/python_interpreter/http_request), `method`, `endpoint`, `timeoutSeconds` |
| **Condition** | `Logic` | `GitFork` | `["input"]` | `["true", "false"]` | `operator` (equals/not_equals/contains/greater_than/less_than/regex_match), `leftOperand`, `rightOperand` |
| **Human Approval** | `Control` | `UserCheck` | `["payload"]` | `["approved", "rejected"]`| `promptMessage`, `timeoutMinutes` (1-1440), `defaultAction` (reject/escalate/proceed) |
| **Output** | `IO` | `FileOutput` | `["input"]` | `[]` | `outputFormat` (markdown/json/raw_text/file_download), `includeExecutionMetrics` |

---

## 3. Data Contracts & JSON Specifications

### 3.1 Input Contract: Member 2 Execution Plan (`ExecutionPlan`)

```json
{
  "name": "Financial Analysis Pipeline",
  "description": "Reads earnings PDF, extracts summary via Gemini, branches on growth, and outputs report.",
  "version": "1.0.0",
  "steps": [
    {
      "id": "step_upload",
      "title": "User Document Upload",
      "component_type": "Input",
      "config": {
        "inputType": "file_url",
        "required": true
      },
      "next_steps": ["step_pdf"]
    },
    {
      "id": "step_pdf",
      "title": "Extract PDF Text",
      "component_type": "Document Reader",
      "config": {
        "chunkSize": 1200,
        "chunkOverlap": 150
      },
      "next_steps": ["step_llm"]
    },
    {
      "id": "step_llm",
      "title": "Summarize Financials",
      "component_type": "LLM",
      "config": {
        "model": "gemini-1.5-pro",
        "temperature": 0.3
      },
      "next_steps": ["step_decision"]
    },
    {
      "id": "step_decision",
      "title": "Evaluate Performance",
      "component_type": "Condition",
      "config": {
        "operator": "contains",
        "leftOperand": "revenue",
        "rightOperand": "positive"
      },
      "branch_conditions": {
        "true": "step_output",
        "false": "step_audit"
      }
    },
    {
      "id": "step_audit",
      "title": "Human Financial Audit",
      "component_type": "Human Approval",
      "config": {
        "promptMessage": "Review negative financial performance indicators."
      },
      "next_steps": ["step_output"]
    },
    {
      "id": "step_output",
      "title": "Generate Executive Summary",
      "component_type": "Output",
      "config": {
        "outputFormat": "markdown"
      }
    }
  ]
}
```

### 3.2 Output Contract: Member 4 / Frontend Workflow (`WorkflowCreate`)

Conforms strictly to `shared/workflow.schema.json`:

```json
{
  "name": "Financial Analysis Pipeline",
  "description": "Reads earnings PDF, extracts summary via Gemini, branches on growth, and outputs report.",
  "version": "1.0.0",
  "configuration": {
    "timeoutSeconds": 300,
    "maxRetries": 2,
    "autoRepairEnabled": true,
    "executionMode": "langgraph"
  },
  "nodes": [
    {
      "id": "node_input_1",
      "type": "Input",
      "name": "User Document Upload",
      "position": { "x": 80.0, "y": 150.0 },
      "config": {
        "inputType": "file_url",
        "defaultValue": "",
        "required": true,
        "placeholder": "Enter initial prompt or JSON payload..."
      },
      "inputHandles": [],
      "outputHandles": ["output"]
    },
    {
      "id": "node_document_reader_1",
      "type": "Document Reader",
      "name": "Extract PDF Text",
      "position": { "x": 340.0, "y": 190.0 },
      "config": {
        "chunkSize": 1200,
        "chunkOverlap": 150,
        "extractTables": false,
        "supportedExtensions": [".pdf", ".txt", ".md", ".docx"]
      },
      "inputHandles": ["filePath"],
      "outputHandles": ["content", "metadata"]
    }
  ],
  "edges": [
    {
      "id": "edge_1_node_input_1_node_document_reader_1",
      "source": "node_input_1",
      "target": "node_document_reader_1",
      "sourceHandle": "output"
    }
  ],
  "tags": ["generated"]
}
```

---

## 4. Workflow Validation Rules

The `WorkflowValidator` checks workflows across 4 distinct categories:

1. **Structural Integrity**:
   - Workflow must have at least one node.
   - Every node must have a unique ID (duplicate IDs are rejected).
2. **Component Configuration**:
   - Node types must belong to the 7 canonical types.
   - Component configuration values are verified against Pydantic models (e.g. `temperature` between 0.0 and 1.0; `chunkOverlap` strictly less than `chunkSize`).
3. **Connection & Edge Rules**:
   - Source and target node IDs must exist in the node catalog.
   - Direct self-loops (`source == target`) are forbidden.
   - Source handles and target handles must exist on the respective nodes.
   - Input nodes should not have incoming workflow edges; terminal Output nodes should not have outgoing edges.
4. **Graph Topology**:
   - Disconnected / orphaned nodes (zero incoming and zero outgoing) are flagged.
   - Cycle detection (DFS) warns if loops exist under DAG execution mode.

---

## 5. Version Compatibility & Change Tracking

- **SemVer Incrementing**: `increment_version(version, bump_type)` supports `"patch"`, `"minor"`, and `"major"`.
- **Workflow Comparison**: `compare_workflows(v1, v2) -> WorkflowDiff` computes:
  - Added / removed nodes
  - Modified node field and config dictionaries (capturing exact `before` and `after` values)
  - Added / removed / modified edges
  - Workflow-level configuration changes
  - `is_compatible`: boolean determining whether changes maintain external interface compatibility (e.g. preserves Input/Output entry points).
- **Workflow Rollback**:
  - `restore_version(target_workflow: WorkflowBase) -> WorkflowBase`: Restores an exact historical snapshot as an independent deep copy, preserving node IDs, connections, and configurations.
  - `rollback_to_version(current_workflow, target_version_workflow, bump="minor") -> Tuple[WorkflowBase, WorkflowDiff]`: Generates a new forward version restoring the target's topology and configuration, computing a structured diff between the current and rolled-back states.
  - `WorkflowHistory`: Multi-version repository supporting `save_version(wf)`, `get_version(ver)`, `list_versions()`, and non-destructive `rollback(target_version, current_workflow, bump)`.
- **Immutability Guarantee**: All rollback and modification operations produce new independent deep copies without mutating historical snapshots.

---

## 6. Targeted Modification & Self-Repair

The `WorkflowModifier` exposes targeted mutation primitives for Member 6's diagnostic and repair engine:

```python
from app.services.workflow import workflow_modifier

# 1. Update LLM prompt or parameters
updated_wf = workflow_modifier.update_node_config(
    original_wf,
    node_id="node_llm_1",
    config_updates={"temperature": 0.2, "systemPrompt": "Refined instructions."}
)

# 2. Add an intermediate fallback node
patched_wf = workflow_modifier.add_node(
    updated_wf,
    node=new_node,
    connect_after_node_id="node_document_reader_1",
    connect_before_node_id="node_llm_1"
)

# 3. Apply an automated self-repair patch
repaired_wf, diff = workflow_modifier.apply_patch(
    broken_wf,
    patch={
        "update_configs": [{"node_id": "node_llm_1", "config": {"temperature": 0.1}}],
        "remove_nodes": ["node_bad_step"],
        "reconnect_removed": True,
        "bump_version": "patch"
    }
)
```

---

## 7. REST API Endpoints

All endpoints are registered under `/api/v1/workflows`:

| Method | Endpoint | Request Body | Response | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/workflows/components` | None | `ComponentCatalogResponse` | List the 7 canonical node types, icons, handles, and field definitions. |
| `POST` | `/api/v1/workflows/generate` | `ExecutionPlan` / `ArchitectExecutionPlan` | `WorkflowCreate` (201) | Synthesize executable workflow JSON from AI execution plan. |
| `POST` | `/api/v1/workflows/generate-from-prompt` | `{"prompt": "..."}` | `GenerateFromPromptResponse` (201) | End-to-end: Prompt -> Member 2 Architect -> Member 3 Generator -> Validated Workflow. |
| `POST` | `/api/v1/workflows/validate` | `WorkflowValidationRequest` | `ValidationResult` (200) | Structural, configuration, handle, and topology validation report. |
| `POST` | `/api/v1/workflows/compare` | `WorkflowCompareRequest` | `WorkflowDiff` (200) | Compare two workflow revisions and compute delta. |
| `POST` | `/api/v1/workflows/modify` | `WorkflowModifyRequest` | `WorkflowModifyResponse` (200) | Apply targeted modifications or self-repair patch. |
| `POST` | `/api/v1/workflows/rollback` | `WorkflowRollbackRequest` | `WorkflowRollbackResponse` (200) | Rollback workflow to an earlier version while tracking changes. |

---

## 8. Integration Guidelines

- **Member 2 (AI Architect)**: When generating execution plans, ensure the step payload matches `ExecutionPlan` and `ExecutionPlanStep` models. Pass `branch_conditions` dictionary for Condition nodes.
- **Member 4 (Execution Engine)**: Consume `WorkflowCreate.nodes` and `WorkflowCreate.edges` directly into LangGraph StateGraph nodes and edges.
- **Member 1 (Database & Persistence)**: Use `WorkflowCreate` with `WorkflowService.create_workflow(db, workflow_in)` to persist generated workflows.
- **Frontend (Visual Editor)**: The `position` dictionary `{ "x": float, "y": float }` in each node is sized with horizontal flow spacing (stride = 260px) ready for React Flow canvas layout.

---

## 9. Performance Tracking & Execution Lifecycle Metadata

Generated workflows provide structural configuration flags and ISO-8601 timestamps to support runtime performance tracking without inventing runtime values statically:

1. **Workflow-Level Configuration (`WorkflowConfigurationSchema`)**:
   - `collectMetrics: bool = True`: Directs Member 4's execution runtime to collect execution duration, step latency, timestamps, and per-node execution status.
   - `timeoutSeconds: int = 300`: Maximum execution time before runtime raises a timeout exception.
2. **Output Node Metrics Reporting**:
   - `includeExecutionMetrics: bool = True`: Instructs the final Output component to include an execution summary (total elapsed time, step counts, token usage).
3. **Lifecycle Timestamps**:
   - Canonical definitions generated via `to_workflow_definition()` include ISO-8601 `createdAt` and `updatedAt` metadata timestamps.
4. **Boundary Separation**:
   - Static workflow definitions do **not** invent runtime execution metrics (such as execution duration, running step statuses, or logs). Those are captured dynamically by Member 4's LangGraph execution runner and persisted by Member 1 in execution history tables.
