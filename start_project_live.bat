@echo off
title IIA Uninsured Vehicle System — 1-Click Live Launcher
color 0B

echo ======================================================================
echo    IIA VEHICLE INTEGRATION SYSTEM - LIVE DISTRIBUTED CLUSTER
echo    IIIT Delhi - Information Integration & Applications (Project Part B)
echo ======================================================================
echo.
echo [*] Pre-configured Cluster Endpoints:
echo     - Master Node:  http://127.0.0.1:8000  (capture.db)
echo     - Node A URL:   https://mooned-antics-shorter.ngrok-free.dev (registration.db, insurance.db)
echo     - Node B URL:   https://manhood-overcome-copartner.ngrok-free.dev (theft.db, ministry.db)
echo     - AI Vision:    Google Gemini 3.5 Flash Active
echo     - Resilience:   Automatic zero-downtime local SQLite fallback enabled
echo.

set "PROJECT_ROOT=%~dp0"
set "GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE"
set "NODE_B_URL=https://mooned-antics-shorter.ngrok-free.dev"
set "NODE_C_URL=https://manhood-overcome-copartner.ngrok-free.dev"

:: 1. Launch FastAPI Backend
echo [*] Starting FastAPI Master Backend on port 8000...
start "IIA Backend (Master)" cmd /k "cd /d %PROJECT_ROOT%backend && set GEMINI_API_KEY=%GEMINI_API_KEY%&& set NODE_B_URL=%NODE_B_URL%&& set NODE_C_URL=%NODE_C_URL%&& python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

:: 2. Launch React Frontend
echo [*] Starting React / Vite Frontend on port 5173...
start "IIA Frontend (Vite)" cmd /k "cd /d %PROJECT_ROOT%frontend && npm run dev -- --host 127.0.0.1 --port 5173"

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
