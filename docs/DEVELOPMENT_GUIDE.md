# AgentForge AI - Developer Guide

Welcome to the **AgentForge AI** development team! This guide details local environment setup, workflows, branch strategies, and team collaboration protocols for all six team members.

---

## 1. System Prerequisites

Ensure you have the following installed:
- **Node.js**: `v20.x` or `v22.x` (LTS recommended)
- **npm**: `v10.x` or later
- **Python**: `v3.11.x`
- **Git**

---

## 2. Quickstart Setup Instructions

### Step 1: Clone Repository & Configure Environment

```bash
# Clone the project
git clone <repository-url>
cd agent_workflow

# Copy environment variables template
# On Windows PowerShell:
Copy-Item .env.example .env

# On macOS / Linux:
cp .env.example .env
```

> **IMPORTANT**: Never commit `.env` or your real `GEMINI_API_KEY` to source control.

---

### Step 2: Backend Setup (FastAPI & SQLite)

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend test suite
pytest -v

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```

- API Base: `http://localhost:8000/api/v1`
- Swagger UI Documentation: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/api/v1/health`

---

### Step 3: Frontend Setup (React, Vite, Tailwind, React Flow)

In a separate terminal window:

```bash
cd frontend

# Install npm packages
npm install

# Start Vite development server
npm run dev
```

- Local Dev URL: `http://localhost:5173`
- The frontend will automatically proxy API requests from `/api` to `http://localhost:8000`.

---

## 3. Team Member Module Ownership & Responsibilities

| Member | Domain | Primary Directories | Key Deliverables |
| :--- | :--- | :--- | :--- |
| **Member 1** | **Frontend Development** | `frontend/src/` | Interactive visual canvas with `@xyflow/react`, node configuration sidebars, real-time execution animation, responsive layout. |
| **Member 2** | **Backend and Database** | `backend/app/api/`, `backend/app/database/`, `backend/app/models/` | SQLAlchemy models, SQLite persistence, workflow CRUD routes, database migrations (Alembic), API security. |
| **Member 3** | **AI Agent Architect** | `backend/app/services/ai/` | Google Gemini API integration, prompt templates for natural-language-to-DAG conversion, intent parsing, token optimization. |
| **Member 4** | **Workflow Generation & Components** | `shared/`, `backend/app/services/workflow/` | Node definitions catalog, DAG cycle validation, port type compatibility checkers, schema versioning. |
| **Member 5** | **Workflow Execution Engine** | `backend/app/services/engine/` | LangGraph state graph compilation, asynchronous step runner, sandbox tool execution, human-in-the-loop pause gates. |
| **Member 6** | **Testing, Validation & Self-Repair** | `backend/tests/`, `backend/app/services/repair/` | Pytest test suites, graph stress-testing, automated diagnostic agent, self-repair patching loop. |

---

## 4. Git Workflow & Branch Strategy

Each team member works on a designated feature branch off `main`:

```bash
# Branch Naming Standard
git checkout -b feat/m1-frontend-node-canvas
git checkout -b feat/m2-backend-workflow-crud
git checkout -b feat/m3-gemini-prompt-compiler
git checkout -b feat/m4-dag-cycle-validator
git checkout -b feat/m5-langgraph-runtime
git checkout -b feat/m6-self-repair-suite
```

### Shared Schema Protocol
- The `shared/` directory is the single source of truth.
- **Rule**: Any change to `shared/workflow.schema.json` or `shared/node_definitions.json` requires explicit sign-off from all 6 team members before merging to `main`.
- TypeScript definitions (`shared/types.ts`) and Pydantic schemas (`backend/app/schemas/workflow.py`) must remain synchronized with `shared/workflow.schema.json`.

---

## 5. Verification Commands

Run these checks before committing code:

```bash
# Frontend type check & production build
cd frontend
npm run build

# Backend unit & integration tests
cd backend
pytest -v
```

