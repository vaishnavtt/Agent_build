# AgentForge AI - REST API Specification

## Overview

- **Protocol**: HTTP/1.1 / JSON
- **Base URL**: `http://localhost:8000/api/v1`
- **Interactive Documentation**: `http://localhost:8000/docs` (Swagger UI) & `http://localhost:8000/redoc` (ReDoc)
- **Status Conventions**:
  - `200 OK`: Request succeeded.
  - `201 Created`: Resource successfully created.
  - `204 No Content`: Resource successfully deleted.
  - `400 Bad Request`: Validation or schema failure.
  - `404 Not Found`: Workflow or execution record not found.
  - `422 Unprocessable Entity`: Pydantic payload validation error.
  - `500 Internal Server Error`: Server exception.

---

## 1. System Endpoints

### 1.1 Health Check
Returns server operational status and verifies SQLite database connectivity.
- **Method**: `GET`
- **Path**: `/api/v1/health`
- **Response**: `200 OK`
```json
{
  "status": "ok",
  "service": "AgentForge AI",
  "version": "1.0.0",
  "timestamp": "2026-11-20T12:00:00.000000Z",
  "database": "connected",
  "details": {
    "environment": "development",
    "supported_nodes_count": 7,
    "docs_url": "/docs"
  }
}
```

---

## 2. Multi-Agent System Endpoints (`/api/v1/agents`)

### 2.1 List Specialized AI Agents
Lists all 6 specialized AI agents with roles and active capabilities.
- **Method**: `GET`
- **Path**: `/api/v1/agents`
- **Response**: `200 OK` with 6 agents:
  1. **Planner Agent** – Workflow topology & graph planning
  2. **Research Agent** – Document reading & entity extraction
  3. **Execution Agent** – Task runner & state machine
  4. **Validation Agent** – Topological verification & readiness scoring
  5. **Error Detection Agent** – Failure diagnosis & Diagnostic Triad
  6. **Self-Repair Agent** – Autonomous 5-stage repair loop (max 2 attempts)

### 2.2 Plan Workflow with Planner Agent
- **Method**: `POST`
- **Path**: `/api/v1/agents/plan`
- **Request Body**:
```json
{
  "prompt": "Create an invoice processing agent that extracts line items and syncs with ERP",
  "requirements": ["Read invoice PDF", "Extract totals", "Audit over $1000", "ERP sync"]
}
```

### 2.3 Research Information with Research Agent
- **Method**: `POST`
- **Path**: `/api/v1/agents/research`
- **Request Body**:
```json
{
  "topic": "Candidate evaluation requirements for fullstack engineer",
  "context": {"required_skills": ["React", "Python"]}
}
```

### 2.4 Diagnose Error with Error Detection Agent
- **Method**: `POST`
- **Path**: `/api/v1/agents/diagnose`
- **Request Body**:
```json
{
  "workflow": { "name": "Active Agent", "nodes": [], "edges": [] },
  "execution_steps": [
    { "componentName": "AI Assistant", "componentType": "LLM", "status": "failed" }
  ],
  "error_message": "Missing instructions"
}
```

### 2.5 Repair Workflow with Self-Repair Agent
- **Method**: `POST`
- **Path**: `/api/v1/agents/repair`
- **Request Body**:
```json
{
  "workflow": { "name": "Faulty Agent", "nodes": [], "edges": [] },
  "diagnosis": { "failed_node_id": "node-3", "failed_component_type": "LLM" },
  "attempt": 1
}
```

---

## 3. Workflow Management Endpoints (`/api/v1/workflows`)

### 3.1 List Workflows
- **Method**: `GET`
- **Path**: `/api/v1/workflows?skip=0&limit=50`

### 3.2 Create Workflow
- **Method**: `POST`
- **Path**: `/api/v1/workflows`
- **Request Body**: Conforms to `WorkflowCreate` schema.

### 3.3 Get Workflow by ID
- **Method**: `GET`
- **Path**: `/api/v1/workflows/{workflow_id}`

### 3.4 Update Workflow
- **Method**: `PUT`
- **Path**: `/api/v1/workflows/{workflow_id}`

### 3.5 Delete Workflow (Soft Delete)
- **Method**: `DELETE`
- **Path**: `/api/v1/workflows/{workflow_id}`

### 3.6 Validate Workflow Graph
Evaluates structural integrity, component configurations, and calculates weighted dynamic readiness score.
- **Method**: `POST`
- **Path**: `/api/v1/workflows/validate`
- **Request Body**:
```json
{
  "nodes": [...],
  "edges": [...]
}
```
- **Response**:
```json
{
  "is_valid": true,
  "readiness_score": 100,
  "issues": [],
  "metrics": {
    "total_nodes": 6,
    "total_edges": 5,
    "errors_count": 0,
    "warnings_count": 0
  }
}
```

---

## 4. Execution Engine & History Endpoints

### 4.1 Execute Adhoc Canvas Workflow
Executes the current visual canvas nodes directly, invoking AI agents and auto-repairing errors if encountered.
- **Method**: `POST`
- **Path**: `/api/v1/workflows/run-adhoc`
- **Request Body**:
```json
{
  "name": "Candidate Screener",
  "nodes": [...],
  "edges": [...],
  "auto_repair": true
}
```

### 4.2 Run Persisted Workflow by ID
- **Method**: `POST`
- **Path**: `/api/v1/workflows/{workflow_id}/run`
- **Request Body**:
```json
{
  "input_payload": { "candidate_id": "C-104" },
  "auto_repair": true
}
```

### 4.3 List All Executions
- **Method**: `GET`
- **Path**: `/api/v1/workflows/executions/all?skip=0&limit=50`

### 4.4 Get Single Execution Record with Log Evidence
- **Method**: `GET`
- **Path**: `/api/v1/workflows/executions/{execution_id}`
