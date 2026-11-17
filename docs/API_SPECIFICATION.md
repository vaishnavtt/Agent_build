# AgentForge AI - API Specification

## Overview

- **Protocol**: HTTP/1.1 / JSON
- **Base URL**: `http://localhost:8000/api/v1`
- **Interactive Documentation**: `http://localhost:8000/docs` (Swagger UI) & `http://localhost:8000/redoc` (ReDoc)
- **Status Conventions**:
  - `200 OK`: Request succeeded.
  - `201 Created`: Resource successfully created.
  - `400 Bad Request`: Validation or schema failure.
  - `404 Not Found`: Workflow or resource does not exist.
  - `422 Unprocessable Entity`: Pydantic payload validation error.
  - `500 Internal Server Error`: Unexpected server or execution engine exception.

---

## 1. System Endpoints

### 1.1 Health Check (Implemented)

Returns server operational status and verifies SQLite database connectivity.

- **Method**: `GET`
- **Path**: `/api/v1/health`
- **Authentication**: None

#### Request Example
```bash
curl -X GET http://localhost:8000/api/v1/health
```

#### Response Example (`200 OK`)
```json
{
  "status": "ok",
  "service": "AgentForge AI",
  "version": "1.0.0",
  "timestamp": "2026-11-17T10:33:24.201370Z",
  "database": "connected",
  "details": {
    "environment": "development",
    "supported_nodes_count": 7,
    "docs_url": "/docs"
  }
}
```

---

## 2. Workflow Management Endpoints (Planned for Member 2)

### 2.1 List Workflows
- **Method**: `GET`
- **Path**: `/api/v1/workflows`
- **Query Params**:
  - `skip` (int, default 0)
  - `limit` (int, default 20)

### 2.2 Create Workflow
- **Method**: `POST`
- **Path**: `/api/v1/workflows`
- **Request Body**: Conforms to `WorkflowCreate` schema (`shared/workflow.schema.json`).

```json
{
  "name": "Market Research Agent",
  "description": "Scrapes market trends and summarizes findings",
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
      "name": "User Query",
      "position": { "x": 100, "y": 150 },
      "config": { "inputType": "text" }
    },
    {
      "id": "node_llm_1",
      "type": "LLM",
      "name": "Gemini Summarizer",
      "position": { "x": 350, "y": 150 },
      "config": { "model": "gemini-1.5-pro", "temperature": 0.7 }
    },
    {
      "id": "node_output_1",
      "type": "Output",
      "name": "Summary Output",
      "position": { "x": 600, "y": 150 },
      "config": { "outputFormat": "markdown" }
    }
  ],
  "edges": [
    {
      "id": "edge_1",
      "source": "node_input_1",
      "target": "node_llm_1"
    },
    {
      "id": "edge_2",
      "source": "node_llm_1",
      "target": "node_output_1"
    }
  ],
  "tags": ["research", "summary"]
}
```

### 2.3 Get Workflow by ID
- **Method**: `GET`
- **Path**: `/api/v1/workflows/{workflow_id}`

---

## 3. AI Workflow Generation (Planned for Member 3)

### 3.1 Generate Workflow from Natural Language Prompt
- **Method**: `POST`
- **Path**: `/api/v1/workflows/generate`
- **Request Body**:
```json
{
  "prompt": "Create an agent that reads a financial PDF document, extracts key revenue numbers with Gemini, checks if revenue grew, and emails the CFO if revenue decreased.",
  "model": "gemini-1.5-pro"
}
```
- **Response**: Complete synthesized `AgentForgeWorkflow` JSON payload ready for canvas rendering.

---

## 4. Execution Engine & Self-Repair (Planned for Member 5 & 6)

### 4.1 Execute Workflow
- **Method**: `POST`
- **Path**: `/api/v1/workflows/{workflow_id}/execute`
- **Request Body**:
```json
{
  "inputs": {
    "query": "Q3 2026 performance summary"
  }
}
```

### 4.2 Trigger Self-Repair
- **Method**: `POST`
- **Path**: `/api/v1/workflows/{workflow_id}/repair`
- **Request Body**:
```json
{
  "executionId": "exec-uuid",
  "errorDetails": "Node 'node_tool_1' raised 404: Endpoint not found",
  "failedNodeId": "node_tool_1"
}
```
- **Response**: Patched workflow graph and explanation of applied self-repair fixes.

