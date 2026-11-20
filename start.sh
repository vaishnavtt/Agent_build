#!/bin/bash
# =====================================================================
# AgentForge AI - Quick Startup Script (Linux / macOS)
# =====================================================================
# Usage: chmod +x start.sh && ./start.sh
# =====================================================================

set -e

echo "============================================================"
echo "  AgentForge AI - Multi-Agent Workflow Builder"
echo "============================================================"

# 1. Copy .env.example → .env if not already present
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "[INFO] Created .env from .env.example"
    echo "[INFO] Edit .env and add your GEMINI_API_KEY (optional)"
fi

# 2. Backend Setup
echo ""
echo "[BACKEND] Installing Python dependencies..."
cd backend
python3 -m pip install -r requirements.txt --quiet

echo "[BACKEND] Running tests..."
python3 -m pytest -v --tb=short

echo "[BACKEND] Starting FastAPI server on http://localhost:8000 ..."
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
echo "[BACKEND] Started (PID: $BACKEND_PID)"

cd ..

# 3. Frontend Setup
echo ""
echo "[FRONTEND] Installing npm packages..."
cd frontend
npm install --silent

echo "[FRONTEND] Starting Vite dev server on http://localhost:5173 ..."
npm run dev &
FRONTEND_PID=$!
echo "[FRONTEND] Started (PID: $FRONTEND_PID)"

cd ..

echo ""
echo "============================================================"
echo "  AgentForge AI is running!"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo "  API Docs: http://localhost:8000/docs"
echo "  Press Ctrl+C to stop all servers"
echo "============================================================"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
