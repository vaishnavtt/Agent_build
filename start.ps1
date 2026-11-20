# =====================================================================
# AgentForge AI - Quick Startup Script (PowerShell / Windows)
# =====================================================================
# Usage: Right-click and "Run with PowerShell" or run in a PS terminal
#   .\start.ps1
# =====================================================================

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  AgentForge AI - Multi-Agent Workflow Builder"              -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Add tools directory to PATH if available
$toolsPath = "C:\Users\FALCON JNB\.gemini\antigravity\tools"
if (Test-Path "$toolsPath\mingit\cmd") {
    $env:PATH = "$toolsPath\mingit\cmd;$toolsPath\node;$env:PATH"
}

# 1. Copy .env.example → .env if not already present
if (-not (Test-Path ".\.env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[INFO] Created .env from .env.example" -ForegroundColor Yellow
    Write-Host "[INFO] Edit .env and add your GEMINI_API_KEY (optional)" -ForegroundColor Yellow
}

# 2. Backend Setup
Write-Host ""
Write-Host "[BACKEND] Installing Python dependencies..." -ForegroundColor Green
Set-Location "backend"
python -m pip install -r requirements.txt --quiet

Write-Host "[BACKEND] Running tests..." -ForegroundColor Green
python -m pytest -v --tb=short

Write-Host "[BACKEND] Starting FastAPI server on http://localhost:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PWD'; uvicorn app.main:app --reload --port 8000"

Set-Location ".."

# 3. Frontend Setup
Write-Host ""
Write-Host "[FRONTEND] Installing npm packages..." -ForegroundColor Green
Set-Location "frontend"
npm install --silent

Write-Host "[FRONTEND] Starting Vite dev server on http://localhost:5173 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PWD'; npm run dev"

Set-Location ".."

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  AgentForge AI is starting up!"                             -ForegroundColor Cyan
Write-Host "  Backend:  http://localhost:8000"                           -ForegroundColor Green
Write-Host "  Frontend: http://localhost:5173"                           -ForegroundColor Green
Write-Host "  API Docs: http://localhost:8000/docs"                      -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
