@echo off
title IIA Vehicle System — Local Multi-Node Launcher
color 0A

echo =====================================================
echo   IIA VEHICLE IDENTIFICATION SYSTEM (Local Demo)
echo   Uninsured Vehicle Detection — IIIT Delhi
echo   Starting all 4 nodes locally:
echo     - Node B (Insurance + Registration) on port 8001
echo     - Node C (Theft + Ministry) on port 8002
echo     - Master Backend (FastAPI + Mediator) on port 8000
echo     - Frontend (React + Vite) on port 5173
echo =====================================================
echo.

set "PROJECT_ROOT=%~dp0"
set "BACKEND_DIR=%PROJECT_ROOT%backend"
set "NODE_BACKEND_DIR=%PROJECT_ROOT%node_backend"
set "FRONTEND_DIR=%PROJECT_ROOT%frontend"
set "DATA_DIR=%PROJECT_ROOT%data"

:: Seed databases if not already seeded
if not exist "%DATA_DIR%\capture.db" (
    echo [*] Seeding databases with demo data...
    set PYTHONUTF8=1
    python scripts\seed_databases.py
)

:: 1. Start Node B
echo [*] Starting Node B (Insurance ^& Registration) on port 8001...
start "IIA Node B (Port 8001)" cmd /k "set NODE_DATABASES=insurance,registration && set NODE_PORT=8001 && cd /d "%NODE_BACKEND_DIR%" && python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload"

:: 2. Start Node C
echo [*] Starting Node C (Theft ^& Ministry) on port 8002...
start "IIA Node C (Port 8002)" cmd /k "set NODE_DATABASES=theft,ministry && set NODE_PORT=8002 && cd /d "%NODE_BACKEND_DIR%" && python -m uvicorn main:app --host 127.0.0.1 --port 8002 --reload"

:: 3. Start Master Backend
echo [*] Starting Master Backend on port 8000...
start "IIA Master Backend (Port 8000)" cmd /k "set NODE_B_URL=http://localhost:8001 && set NODE_C_URL=http://localhost:8002 && cd /d "%BACKEND_DIR%" && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

:: 4. Start Frontend
echo [*] Starting Frontend on port 5173...
start "IIA Frontend (Port 5173)" cmd /k "cd /d "%FRONTEND_DIR%" && npm.cmd run dev -- --host 127.0.0.1 --port 5173"

echo.
echo =====================================================
echo   All 4 services are running!
echo   Frontend UI:  http://localhost:5173
echo   API Docs:     http://localhost:8000/docs
echo =====================================================
pause
