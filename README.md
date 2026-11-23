# AgentForge AI 🛠️⚡
### AI Multi-Agent Visual Workflow Builder

**AgentForge AI** is an advanced, production-ready AI workflow builder that enables developers and teams to visually design, configure, validate, execute, and monitor multi-agent workflows. It bridges non-technical users and AI agent engineering by translating natural language instructions into directed component graphs, validating topology and configurations, executing automated requirement tests, isolating failures through execution log evidence, and autonomously performing targeted self-repairs.

---

## 🌟 Technology Stack

- **Frontend**: React 19, TypeScript, Vite, React Flow (`@xyflow/react`), Tailwind CSS, Lucide React
- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLite, SQLAlchemy 2.0, Uvicorn
- **AI & Reasoning Layer**: Google Gemini API (`gemini-1.5-pro`, `gemini-1.5-flash`), with resilient server-side fallback
- **Testing & Tooling**: Pytest, Pytest-Asyncio, HTTPX

---

## 🤖 6 Specialized AI Agents

AgentForge AI incorporates six specialized, collaborating agents:

| # | Agent Name | Role | Primary Responsibility |
| :-: | :--- | :--- | :--- |
| **1** | **Planner Agent** | `Workflow Planner` | Plans workflow graph structure and node mapping from user intent or natural language requirements. |
| **2** | **Research Agent** | `Information Researcher` | Gathers context, extracts document data (PDF, DOCX, text), and enriches parameters for downstream tasks. |
| **3** | **Execution Agent** | `Workflow Executor` | Executes assigned workflow tasks in topological order, invokes Gemini models, and tracks state. |
| **4** | **Validation Agent** | `Workflow Validator` | Verifies graph correctness, topology (cycles, disconnected steps), and calculates dynamic readiness score. |
| **5** | **Error Detection Agent** | `Error Diagnostician` | Identifies runtime errors, isolates root causes, and generates the Diagnostic Triad with log evidence. |
| **6** | **Self-Repair Agent** | `Autonomous Repairer` | Executes autonomous 5-stage self-repairs strictly capped at 2 attempts, generating a terminal report. |

---

## 🧩 7 Canonical Workflow Components

AgentForge supports 7 standardized node primitives (`shared/node_definitions.json`):

1. **Input (`Input`)**: Trigger source (file upload, text prompt, webhook).
2. **Document Reader (`Document Reader`)**: Parses and extracts text, entities, and skills from documents.
3. **AI Assistant (`LLM`)**: Powered by Google Gemini for candidate scoring, reasoning, and summarization.
4. **Condition (`Condition`)**: Branching logic evaluating conditional rules (`fit_score >= 7`, boolean checks).
5. **Human Approval (`Human Approval`)**: Interactive human-in-the-loop checkpoint requiring sign-off.
6. **Tool (`Tool`)**: External operations (database sync, ERP integration, API dispatch).
7. **Output (`Output`)**: Terminal sink formatting scorecard, markdown summaries, and reports.

---

## 📁 Repository Structure

```
Agent_build/
├── frontend/                     # React + Vite visual workflow editor
│   ├── src/
│   │   ├── components/
│   │   │   ├── activity/        # Execution monitoring & self-repair UI
│   │   │   ├── agents/          # My Agents dashboard & catalog
│   │   │   ├── create/          # AI prompt-based agent generation
│   │   │   ├── dashboard/       # Main overview dashboard
│   │   │   ├── editor/          # React Flow canvas, library, & settings
│   │   │   ├── history/         # Execution history & logs viewer
│   │   │   ├── layout/          # Sidebar, Header, Help modal
│   │   │   └── validation/      # Readiness score & requirement tests
│   │   ├── context/             # Global WorkflowContext state management
│   │   └── types/               # TypeScript interfaces & types
│   ├── package.json
│   └── vite.config.ts
├── backend/                      # FastAPI REST service & AI agent engine
│   ├── app/
│   │   ├── agents/              # 6 Specialized AI Agents implementation
│   │   │   ├── planner_agent.py
│   │   │   ├── research_agent.py
│   │   │   ├── execution_agent.py
│   │   │   ├── validation_agent.py
│   │   │   ├── error_detection_agent.py
│   │   │   ├── self_repair_agent.py
│   │   │   └── requirement_analysis_agent.py # Member 2 LangGraph Architect
│   │   ├── api/v1/endpoints/    # REST endpoints (health, workflows, agents)
│   │   ├── core/                # Settings, environment, & Gemini client
│   │   ├── database/            # SQLAlchemy SQLite session & models
│   │   ├── models/              # Workflow & Execution database models
│   │   └── services/            # Workflow & Requirement analysis services
│   ├── tests/                   # Pytest automated test suite (24 tests)
│   └── requirements.txt
├── shared/                       # Shared schemas and node definitions
├── docs/                         # Architecture & API specifications
├── start.ps1                     # One-click Windows startup script
├── start.sh                      # One-click Linux / macOS startup script
└── README.md
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- **Node.js**: `v20.x` or `v22.x`
- **npm**: `v10.x` or higher
- **Python**: `v3.11` or `v3.12`

### 2. Configure Environment
```bash
# Windows PowerShell:
Copy-Item .env.example .env

# macOS / Linux:
cp .env.example .env
```
*(Optional: Add your `GEMINI_API_KEY` in `.env` for live Google Gemini LLM reasoning).*

### 3. One-Click Launch (Recommended)

**On Windows:**
```powershell
.\start.ps1
```

**On Linux / macOS:**
```bash
chmod +x start.sh
./start.sh
```

---

### 4. Manual Launch

#### Start Backend
```bash
cd backend
pip install -r requirements.txt
pytest -v
uvicorn app.main:app --reload --port 8000
```
- **Backend API**: `http://localhost:8000`
- **Swagger Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/api/v1/health`

#### Start Frontend
```bash
cd frontend
npm install
npm run dev
```
- **Frontend UI**: `http://localhost:5173`

---

## 📡 Key REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Service health status and database connectivity. |
| `GET` | `/api/v1/agents` | Lists the 6 active AI agents and their capabilities. |
| `POST` | `/api/v1/agents/plan` | Direct prompt planning with the Planner Agent. |
| `POST` | `/api/v1/agents/research` | Information extraction with the Research Agent. |
| `POST` | `/api/v1/agents/diagnose` | Failure diagnosis with the Error Detection Agent. |
| `POST` | `/api/v1/agents/repair` | Autonomous self-repair with the Self-Repair Agent. |
| `GET` | `/api/v1/workflows` | List all saved workflows from SQLite. |
| `POST` | `/api/v1/workflows` | Create and save a new workflow. |
| `POST` | `/api/v1/workflows/validate` | Validate workflow topology and calculate readiness score. |
| `POST` | `/api/v1/workflows/run-adhoc` | Execute live React Flow canvas workflow with Execution Agent. |
| `POST` | `/api/v1/workflows/{id}/run` | Execute saved workflow by ID. |
| `GET` | `/api/v1/workflows/executions/all` | List execution history across all agents. |
| `GET` | `/api/v1/workflows/executions/{id}` | Retrieve execution record with full log evidence and repair report. |

---

## 🧪 Testing & Verification

Run the complete backend test suite:
```bash
cd backend
python -m pytest -v
```

All 13 automated tests pass:
- `test_planner_agent_plan_workflow` ✅
- `test_research_agent_collect_and_extract` ✅
- `test_validation_agent_validates_graph` ✅
- `test_validation_agent_catches_missing_config` ✅
- `test_error_detection_and_self_repair_pipeline` ✅
- `test_list_agents_endpoint` ✅
- `test_plan_workflow_endpoint` ✅
- `test_run_adhoc_workflow_endpoint` ✅
- `test_list_all_executions_endpoint` ✅
- `test_health_check_endpoint` ✅
- `test_root_redirects_to_docs` ✅
- `test_create_and_get_workflow` ✅
- `test_validate_workflow_api` ✅

Frontend type-checking and production build verification:
```bash
cd frontend
npm run build
```
Builds cleanly with zero TypeScript errors.

---

## 🔒 Security Best Practices
- Secret API keys are strictly loaded on the backend via environment variables / `.env`.
- API keys are never bundled or exposed to frontend code.
- SQLite database migrations run safely on startup.
- CORS origins are restricted to configured localhost addresses.
