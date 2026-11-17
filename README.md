# AgentForge AI 🛠️⚡

**AgentForge AI** is an AI-powered visual agent builder that converts natural language instructions into executable visual workflows. It automatically generates workflows, validates topology, tests functionality, detects failures, and attempts autonomous self-repairs.

---

## 🌟 Technology Stack

- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, React Flow (`@xyflow/react`), Lucide React
- **Backend**: Python 3.11, FastAPI, Pydantic v2, SQLite, SQLAlchemy 2.0
- **AI & Reasoning Layer**: Google Gemini API, LangGraph (StateGraph runtime)
- **Testing**: Pytest, Pytest-Asyncio, HTTPX

---

## 📁 Monorepo Architecture

```
agent_workflow/
├── frontend/             # React + Vite visual workflow editor
├── backend/              # FastAPI + SQLAlchemy SQLite API service
│   ├── app/
│   │   ├── api/v1/       # Endpoints (including /api/v1/health)
│   │   ├── core/         # App settings & environment configs
│   │   ├── database/     # SQLAlchemy engine & session factory
│   │   ├── models/       # Database models (Workflow, Execution)
│   │   ├── schemas/      # Pydantic schemas
│   │   └── services/     # Business logic & workflow services
│   └── tests/            # Pytest test suite
├── shared/               # Single Source of Truth
│   ├── workflow.schema.json  # Workflow JSON Schema (Draft 2020-12)
│   ├── node_definitions.json # 7 canonical node type catalog
│   └── types.ts              # Shared TypeScript definitions
├── docs/                 # Engineering Documentation
│   ├── ARCHITECTURE.md       # High-level diagrams & self-repair loop
│   ├── API_SPECIFICATION.md  # REST API specification & schemas
│   ├── DEVELOPMENT_GUIDE.md  # 6-member team guide & conventions
│   └── README.md
├── .env.example          # Environment variables template (No secrets)
├── .gitignore            # Git exclusion rules
└── README.md             # This document
```

---

## 👥 Six-Member Engineering Team Responsibilities

| # | Role / Member | Key Responsibilities | Primary Ownership |
| :-: | :--- | :--- | :--- |
| **1** | **Frontend Development** | Visual drag-and-drop canvas with React Flow, node parameter sidebars, execution status indicators, and responsive UI. | `frontend/` |
| **2** | **Backend and Database** | RESTful routing, SQLite/SQLAlchemy ORM models, migrations, CRUD endpoints, and database connection lifecycle. | `backend/app/api/`, `backend/app/database/`, `backend/app/models/` |
| **3** | **AI Agent Architect** | Google Gemini API integration, prompt orchestration, translating natural language prompts into valid structured workflow graphs. | `backend/app/services/ai/` |
| **4** | **Workflow Generation & Components** | Graph topology validation, cycle detection, input/output port compatibility, component catalog, schema versioning. | `shared/`, `backend/app/services/workflow/` |
| **5** | **Workflow Execution Engine** | Compiling workflow graphs to LangGraph `StateGraph`, asynchronous node runner, tool execution sandbox, human approval gates. | `backend/app/services/engine/` |
| **6** | **Testing, Validation & Self-Repair** | End-to-end Pytest test suite, failure diagnosis agent, automated graph patching and self-repair verification loop. | `backend/tests/`, `backend/app/services/repair/` |

---

## 🧩 Supported Node Types

The 7 standard node primitives supported by AgentForge AI (defined in `shared/node_definitions.json`):

1. **Input** (`FileInput`): Ingests user prompts, payloads, or webhook triggers.
2. **LLM** (`Bot`): Executes prompts and reasoning chains with Google Gemini models.
3. **Document Reader** (`FileText`): Extracts and chunks text from PDF, DOCX, Markdown, and text context.
4. **Tool** (`Wrench`): Performs API calls, search queries, or custom Python actions.
5. **Condition** (`GitFork`): Branching logic evaluating conditional expressions.
6. **Human Approval** (`UserCheck`): Human-in-the-loop pause gate requiring user sign-off.
7. **Output** (`FileOutput`): Terminal node returning formatted results, reports, and metrics.

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- **Node.js**: `v20.x` or `v22.x`
- **npm**: `v10.x` or higher
- **Python**: `v3.11.x`

### 2. Configure Environment
```bash
# On Windows PowerShell:
Copy-Item .env.example .env

# On macOS / Linux:
cp .env.example .env
```
*(Do not commit your `.env` or real API key).*

### 3. Start Backend
```bash
cd backend

# Create virtual environment (if not already created)
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run automated tests
pytest -v

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```
- API Base: `http://localhost:8000/api/v1`
- Health Check: `http://localhost:8000/api/v1/health`
- Interactive API Docs: `http://localhost:8000/docs`

### 4. Start Frontend
In a separate terminal:
```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
- Frontend UI: `http://localhost:5173`

---

## 📚 Documentation Links
- [System Architecture](docs/ARCHITECTURE.md)
- [API Specification](docs/API_SPECIFICATION.md)
- [Developer Guide](docs/DEVELOPMENT_GUIDE.md)
- [Shared Schema & Contracts](shared/README.md)

