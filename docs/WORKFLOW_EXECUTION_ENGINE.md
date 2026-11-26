# AgentForge AI – Member 4: Workflow Execution Engine Documentation

## 1. Executive Summary

This document details the architecture, implementation, node handlers, execution state management, performance monitoring, and FastAPI endpoints for the **Workflow Execution Engine** (Member 4) inside AgentForge AI.

The execution engine translates visual directed workflow graphs into deterministic, asynchronous execution pipelines, handling:
- Multi-node dependency resolution and topological ordering.
- Cycle detection using Kahn's algorithm.
- Data passing across connected input/output handles.
- Conditional branching with automatic pruning of untaken paths.
- Asynchronous Human-in-the-Loop approval gates with state checkpointing and resuming.
- High-precision performance monitoring tracking node durations, total execution time, AI provider API call counts, and token usage.
- Structured execution logging with sensitive data redaction.

---

## 2. 10-Stage Execution Engine Architecture

```
+-------------------------------------------------------------------------------+
|                      STAGE 1: RECEIVE WORKFLOW & INPUTS                       |
|   - Ingests workflow JSON topology and initial runtime input payload.         |
+-------------------------------------------------------------------------------+
                                       |
                                       v
+-------------------------------------------------------------------------------+
|                    STAGE 2: STRUCTURE & SCHEMA VALIDATION                     |
|   - Verifies node existence, non-empty list, and required properties.         |
+-------------------------------------------------------------------------------+
                                       |
                                       v
+-------------------------------------------------------------------------------+
|                      STAGE 3: BUILD GRAPH DATA STRUCTURE                      |
|   - Compiles node catalog and bidirectional edge adjacency lists.             |
+-------------------------------------------------------------------------------+
                                       |
                                       v
+-------------------------------------------------------------------------------+
|                  STAGE 4: TOPOLOGICAL ORDER & CYCLE DETECTION                 |
|   - Evaluates in-degree dependencies using Kahn's algorithm.                  |
|   - Raises CycleDetectedError if cyclic loops are present.                    |
+-------------------------------------------------------------------------------+
                                       |
                                       v
+-------------------------------------------------------------------------------+
|                     STAGE 5: EXECUTE NODE WITH HANDLER                        |
|   - Delegates execution to registered handler for each node type.             |
+-------------------------------------------------------------------------------+
                                       |
                                       v
+-------------------------------------------------------------------------------+
|                      STAGE 6: DATA TRANSFER & HANDLE MAPPING                  |
|   - Resolves incoming edges and maps sourceHandles to targetHandles.          |
+-------------------------------------------------------------------------------+
                                       |
                                       v
+-------------------------------------------------------------------------------+
|                    STAGE 7: CONDITIONAL BRANCHING & PRUNING                   |
|   - Evaluates condition operator; prunes untaken branch downstream nodes.     |
+-------------------------------------------------------------------------------+
                                       |
                                       v
+-------------------------------------------------------------------------------+
|                   STAGE 8: TRACK EXECUTION STATUS & TIMING                    |
|   - High-precision performance timers measure duration_ms per node.           |
+-------------------------------------------------------------------------------+
                                       |
                                       v
+-------------------------------------------------------------------------------+
|                      STAGE 9: STRUCTURED LOGGING & AUDIT                      |
|   - Records node IDs, timestamps, input/output summaries, errors, and tokens. |
+-------------------------------------------------------------------------------+
                                       |
                                       v
+-------------------------------------------------------------------------------+
|                   STAGE 10: STRUCTURED EXECUTION REPORT                       |
|   - Returns final output, status, full audit logs, and performance metrics.   |
+-------------------------------------------------------------------------------+
```

---

## 3. Supported Node Types & Handlers

The execution engine provides dedicated handlers for all 7 canonical workflow components:

| Node Type | Canonical / Aliases | Handler Class | Description & Key Features |
| :--- | :--- | :--- | :--- |
| **Input** | `Input`, `input` | `InputNodeHandler` | Ingests text, JSON, or files; validates required fields; passes data downstream. |
| **LLM** | `LLM`, `llm` | `LLMNodeHandler` | Calls Google Gemini API; supports prompt templating; records actual API calls & token metrics (`usageMetadata`). |
| **Document Reader** | `Document Reader`, `PDF Document Reader`, `PDF Reader` | `DocumentReaderNodeHandler` | Extracts text and metadata from PDF files using `pypdf`; supports chunking and overlap; guards corrupted files. |
| **Tool** | `Tool`, `Predefined Tool`, `tool` | `ToolNodeHandler` | Invokes registered, safe tools from `PredefinedToolRegistry` (Calculator, Text Formatter, Web Search, JSON Parser, HTTP Client). Strictly rejects `eval`/`exec`. |
| **Condition** | `Condition`, `condition` | `ConditionNodeHandler` | Evaluates safe comparison operators (`==`, `!=`, `>`, `<`, `>=`, `<=`, `contains`, `starts_with`, `is_empty`, etc.); routes execution to `true` or `false` branch. |
| **Human Approval** | `Human Approval`, `human approval` | `HumanApprovalNodeHandler` | Pauses execution with `WAITING_FOR_APPROVAL`; checkpoints execution state in database; resumes on approval; terminates on rejection. |
| **Output** | `Output`, `output` | `OutputNodeHandler` | Terminal step collecting upstream outputs and returning structured JSON, Markdown, or raw text. |

---

## 4. Execution State Machine

Workflows transition through the following strictly managed states:

- `PENDING`: Initial queued state prior to runner initialization.
- `RUNNING`: Workflow currently executing active nodes.
- `SUCCESS`: All required nodes completed without error.
- `FAILED`: An individual node raised an unhandled error; downstream nodes marked `SKIPPED`.
- `WAITING_FOR_APPROVAL`: Execution paused awaiting human sign-off; state checkpointed.
- `APPROVED`: Human approver accepted the waiting step; execution resumes from that step.
- `REJECTED`: Human approver denied the waiting step; workflow marked `REJECTED`.
- `SKIPPED`: Node bypassed due to untaken conditional branch or preceding failure.
- `CANCELLED`: Execution manually terminated.

---

## 5. Performance Monitoring & Metrics

The `ExecutionPerformanceMonitor` provides real-time, non-simulated runtime metrics:

1. **Individual Node Execution Duration**: Precise execution duration in milliseconds for every step.
2. **Total Workflow Duration**: Total wall-clock runtime in milliseconds.
3. **Actual AI API Calls**: Total real calls dispatched to external LLM providers.
4. **Actual Token Usage**: Extracted directly from Google Gemini provider responses (`promptTokenCount`, `candidatesTokenCount`, `totalTokenCount`).
5. **Execution Overhead on Repair**: Measures latency delta when executing self-repaired workflows.

---

## 6. FastAPI Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/workflows` | Persist a new visual workflow graph. |
| `GET` | `/api/v1/workflows` | List workflows with pagination (`skip`, `limit`). |
| `GET` | `/api/v1/workflows/{id}` | Retrieve workflow definition by ID. |
| `POST` | `/api/v1/workflows/{id}/execute` | Execute a stored workflow by ID with input parameters. |
| `POST` | `/api/v1/executions/run` | Execute an ad-hoc workflow definition directly without saving. |
| `GET` | `/api/v1/executions/{id}` | Retrieve execution status, output, metrics, and error info. |
| `GET` | `/api/v1/executions/{id}/logs` | Retrieve structured node-level execution trace logs. |
| `POST` | `/api/v1/executions/{id}/approve` | Approve a paused execution and resume downstream steps. |
| `POST` | `/api/v1/executions/{id}/reject` | Reject a paused execution and mark status as `REJECTED`. |

---

## 7. Inter-Member Integration Matrix

- **Member 1 (Backend & Database)**:
  - Extended `WorkflowExecutionModel` to store structured `logs`, `metrics`, `failed_node_id`, and `execution_context`.
  - Integrated with `ExecutionService` and SQLite database sessions.
- **Member 2 (AI Requirement Analysis)**:
  - Consumes workflows synthesized from user requirements.
  - LLM node handles Gemini rate limits, timeouts, and quota errors.
- **Member 3 (Workflow Generation)**:
  - Adheres strictly to `shared/workflow.schema.json` and `shared/node_definitions.json`.
  - Maps `sourceHandle` / `targetHandle` on edges for precision data passing.
- **Member 5 (Validation & Automated Testing)**:
  - Exposes `NodeExecutionLog` and `ExecutionMetrics` for reliability scoring.
  - Supports testing normal, edge-case, and boundary scenarios.
- **Member 6 (Failure Diagnosis & Self-Repair)**:
  - Flags exact `failed_node_id`, error messages, and execution traces.
  - Supports controlled re-execution with `reexecution=True` tracking repair overhead.

---

## 8. Test Suite Summary

The engine is verified via 25 automated Pytest tests across unit, node, graph, and API layers:

1. `test_simple_input_output_workflow`: Input -> Output data flow.
2. `test_input_llm_output_workflow_with_mocked_gemini`: Gemini reasoning and response passing.
3. `test_pdf_reader_workflow`: Text extraction from in-memory PDF.
4. `test_predefined_tool_execution`: Safe AST-based calculator execution.
5. `test_condition_true_branch`: Routing through TRUE branch; skipping FALSE.
6. `test_condition_false_branch`: Routing through FALSE branch; skipping TRUE.
7. `test_human_approval_waiting_state`: Execution pause and state preservation.
8. `test_human_approval_and_resume`: Resuming from checkpoint without re-running earlier steps.
9. `test_human_approval_rejection`: Rejection handling and workflow termination.
10. `test_missing_input_validation`: Error raised for missing mandatory input.
11. `test_unsupported_node_type`: Handling and rejection of invalid node types.
12. `test_invalid_connections`: Validation of edges pointing to non-existent nodes.
13. `test_cyclic_workflow_detection`: Cycle detection via Kahn's algorithm.
14. `test_failed_node_execution`: Failure isolation, logging, and status tracking.
15. `test_multiple_node_data_passing`: Multi-step data pipeline passing text transformations.
16. `test_execution_logs`: Comprehensive audit logging verification.
17. `test_node_level_execution_time`: Millisecond duration verification per node.
18. `test_complete_workflow_execution_time`: Total execution duration validation.
19. `test_api_call_and_token_usage_capture`: Precision token and API call accounting.
20. `test_controlled_reexecution_after_repair`: Re-execution and repair overhead tracking.
21. `test_create_and_execute_workflow_via_api`: Full end-to-end FastAPI workflow execution.
22. `test_ad_hoc_execution_run_endpoint`: Direct execution API test without prior save.
23. `test_human_approval_api_flow`: Full API pause, checkpoint, and approval resume flow.
24. `test_health_check_endpoint`: System health and SQLite database verification.
25. `test_root_redirects_to_docs`: OpenAPI documentation redirect check.
