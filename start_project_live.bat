@echo off
title IIA Uninsured Vehicle System — 1-Click Live Launcher
color 0B

echo ======================================================================
echo    IIA VEHICLE INTEGRATION SYSTEM - LIVE DISTRIBUTED CLUSTER
echo    IIIT Delhi - Information Integration and Applications (Project Part B)
echo ======================================================================
echo.

set "PROJECT_ROOT=%~dp0"
set "PATH=C:\Program Files\nodejs;%PATH%"
set "NODE_B_URL=https://mooned-antics-shorter.ngrok-free.dev"
set "NODE_C_URL=https://manhood-overcome-copartner.ngrok-free.dev"

:: 0. Check Remote Node Connections Live
python "%PROJECT_ROOT%scripts\check_nodes.py"

:: 1. Launch FastAPI Backend
echo [*] Starting FastAPI Master Backend on port 8000...
start "IIA Backend (Master)" cmd /k "cd /d %PROJECT_ROOT%backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

:: 2. Launch React Frontend
echo [*] Starting React / Vite Frontend on port 5173...
start "IIA Frontend (Vite)" cmd /k "cd /d %PROJECT_ROOT%frontend && set PATH=C:\Program Files\nodejs;%%PATH%%&& npx vite --host 0.0.0.0 --port 5173"

:: Wait 3 seconds for servers to initialize
timeout /t 3 >nul

:: 3. Launch Web Browser
echo [*] Opening Web Dashboard...
start http://localhost:5173
start http://localhost:8000/docs

echo.
echo ======================================================================
echo  Cluster is LIVE!
echo    - Frontend UI:  http://localhost:5173
echo    - Backend Docs: http://localhost:8000/docs
echo    - Run Viva Test: python scratch/test_evaluation_rubrics.py
echo ======================================================================
pause
