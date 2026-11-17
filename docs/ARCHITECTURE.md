# AgentForge AI - System Architecture

AgentForge AI is an autonomous, AI-driven visual workflow builder that translates natural language instructions into executable directed graphs, validates their integrity, tests their execution, detects faults, and automatically applies self-repair interventions.

---

## 1. High-Level System Architecture

```
+-----------------------------------------------------------------------------------+
|                                 USER INTERFACE                                    |
|   +---------------------------------------------------------------------------+   |
|   |                      React + TypeScript + Tailwind CSS                    |   |
|   |         +-------------------------------------------------------+         |   |
|   |         |           React Flow (@xyflow/react) Canvas           |         |   |
|   |         |   [Input] -> [LLM] -> [Tool / Condition] -> [Output]  |         |   |
|   |         +-------------------------------------------------------+         |   |
|   +---------------------------------------------------------------------------+   |
+-----------------------------------------|-----------------------------------------+
                                          | REST API (HTTP / JSON)
                                          v
+-----------------------------------------------------------------------------------+
|                                FASTAPI BACKEND                                    |
|                                                                                   |
|   +-------------------+   +--------------------+   +--------------------------+   |
|   |   API Routers     |   |   Pydantic Schemas |   |   Domain Services        |   |
|   |  - /api/v1/health |   |  - Node & Edge     |   |  - WorkflowService       |   |
|   |  - /workflows     |   |  - Validation      |   |  - CompilerService       |   |
|   |  - /execute       |   |  - Execution Trace |   |  - SelfRepairService     |   |
|   +-------------------+   +--------------------+   +--------------------------+   |
|             |                       |                           |                 |
|             +-----------------------+---------------------------+                 |
|                                     |                                             |
|                                     v                                             |
|   +---------------------------------------------------------------------------+   |
|   |                           SQLAlchemy ORM & SQLite                         |   |
|   |    [Workflows Table]              [Workflow Executions / History Table]   |   |
|   +---------------------------------------------------------------------------+   |
+-----------------------------------------|-----------------------------------------+
                                          |
                      +-------------------+-------------------+
                      |                                       |
                      v                                       v
+-------------------------------------------+ +-------------------------------------+
|        AI & REASONING LAYER (Gemini)      | |      WORKFLOW EXECUTION ENGINE      |
|  - Natural Language Intent Parser         | |  - LangGraph StateGraph Compiler    |
|  - Structured Graph Synthesizer           | |  - Asynchronous Node Runner         |
|  - Diagnostic & Self-Repair Agent         | |  - Tool Execution Sandbox           |
|                                           | |  - Human-in-the-Loop Approval Gate  |
+-------------------------------------------+ +-------------------------------------+
```

---

## 2. Monorepo Organization

```
agent_workflow/
├── frontend/             # React 19 + TypeScript + Vite + Tailwind CSS + React Flow
│   ├── src/
│   │   ├── components/   # Visual canvas, navbar, dashboard, node drawers
│   │   ├── App.tsx       # Root view & health indicator
│   │   ├── main.tsx      # Application entrypoint
│   │   └── index.css     # Tailwind & React Flow styles
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── backend/              # FastAPI + SQLAlchemy + SQLite
│   ├── app/
│   │   ├── api/v1/       # Versioned API endpoints (health, workflows)
│   │   ├── core/         # Settings, environment variables, security
│   │   ├── database/     # SQLAlchemy engine, session generator, Base
│   │   ├── models/       # Database ORM models (Workflow, WorkflowExecution)
│   │   ├── schemas/      # Pydantic validation schemas
│   │   └── services/     # Business logic & graph compilers
│   ├── tests/            # Pytest test suite (health check, graph tests)
│   ├── requirements.txt
│   └── pytest.ini
├── shared/               # Single Source of Truth contracts
│   ├── workflow.schema.json  # JSON Schema specification
│   ├── node_definitions.json # 7 canonical node type catalog
│   ├── types.ts              # TypeScript interface definitions
│   └── README.md
├── docs/                 # Team, Architecture & API Documentation
│   ├── ARCHITECTURE.md
│   ├── API_SPECIFICATION.md
│   ├── DEVELOPMENT_GUIDE.md
│   └── README.md
├── .env.example          # Sample environment variables
├── .gitignore            # Git exclusion rules
└── README.md             # Project overview & quickstart
```

---

## 3. The 7 Canonical Workflow Node Types

1. **Input (`FileInput`)**: Ingests prompts, initial variables, webhook payloads, or uploaded files.
2. **LLM (`Bot`)**: Generates outputs, evaluates reasoning, and executes instructions using Google Gemini.
3. **Document Reader (`FileText`)**: Extracts and splits content from PDF, DOCX, Markdown, and plain text.
4. **Tool (`Wrench`)**: Invokes external web APIs, Python interpreters, search engines, or database queries.
5. **Condition (`GitFork`)**: Evaluates expressions or conditional branches (`true`/`false`/branch keys).
6. **Human Approval (`UserCheck`)**: Human-in-the-loop gate pausing workflow until user sign-off.
7. **Output (`FileOutput`)**: Terminal node aggregating, formatting, and presenting workflow results.

---

## 4. Self-Repair and Validation Loop

```
+-------------------+
| Natural Language  |
| Instruction       |
+---------+---------+
          |
          v
+-------------------+
| AI Graph Builder  |
| (Gemini 1.5 Pro)  |
+---------+---------+
          |
          v
+-------------------+        Schema or cycle violation
| Topology & Schema |-----------------------------------------+
| Validation        |                                         |
+---------+---------+                                         |
          | Valid                                             |
          v                                                   |
+-------------------+                                         |
| LangGraph Runtime |                                         |
| Execution         |                                         |
+---------+---------+                                         |
          |                                                   |
     +----+----+                                              |
     |         |                                              |
  Success    Runtime Error / Assertion Failure                |
     |         |                                              v
     |         v                                    +-------------------+
     |    +---------------------------------------->| Self-Repair Agent |
     |                                              | (Analyzes stack,  |
     |                                              |  repairs graph)   |
     |                                              +---------+---------+
     |                                                        |
     |                                      Max retries not   |
     |                                      exceeded          v
     |                                              +-------------------+
     |                                              | Re-evaluate Graph |
     |                                              +-------------------+
     v
+-------------------+
| Final Output      |
+-------------------+
```

---

## 5. Six-Member Engineering Team Responsibilities

### Member 1: Frontend Development
- Owns the `frontend/` directory.
- Builds the React Flow canvas, node palette drag-and-drop, connection validation visuals, node parameter sidebars, and execution trace animation.
- Interfaces with the REST API using shared TypeScript types (`shared/types.ts`).

### Member 2: Backend and Database
- Owns `backend/app/api/`, `backend/app/database/`, and `backend/app/models/`.
- Implements SQLAlchemy ORM models, SQLite persistence, Alembic migrations, database indexing, and CRUD endpoints for workflows and execution records.
- Ensures robust CORS, session handling, and configuration management.

### Member 3: AI Agent Architect
- Owns AI integration using Google Gemini API (`backend/app/services/ai/`).
- Designs system prompts, few-shot examples, and structured JSON output prompts that translate natural language user queries into valid `AgentForgeWorkflow` JSON.
- Evaluates model latency, token budgets, and temperature configurations.

### Member 4: Workflow Generation & Component Management
- Owns `shared/` specifications, `node_definitions.json`, and graph structure validators.
- Develops graph topological sorting, directed acyclic graph (DAG) cycle detection, and handle type-compatibility checkers (ensuring source output matches target input).
- Maintains backward-compatible schema versioning.

### Member 5: Workflow Execution Engine
- Owns execution runtime and LangGraph integration (`backend/app/services/engine/`).
- Compiles workflow JSON graphs into executable LangGraph `StateGraph` workflows.
- Handles asynchronous execution, node state propagation, tool sandbox execution, and human approval pause/resume states.

### Member 6: Testing, Validation and Self-Repair
- Owns `backend/tests/`, automated test suites, and the self-repair loop (`backend/app/services/repair/`).
- Implements static graph analysis tests, failure diagnosis routines, and the automated graph patching agent that corrects broken schemas or failed tool calls.
- Measures self-repair convergence rates and test coverage.

