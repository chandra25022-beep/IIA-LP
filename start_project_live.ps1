# IIA Vehicle Integration System — 1-Click PowerShell Launcher
# IIIT Delhi - Distributed Information Integration Project

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   IIA VEHICLE INTEGRATION SYSTEM - LIVE DISTRIBUTED CLUSTER" -ForegroundColor Cyan
Write-Host "   IIIT Delhi - Distributed Information Integration Project" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[*] Pre-configured Cluster Endpoints:" -ForegroundColor Yellow
Write-Host "    - Master Node:  http://127.0.0.1:8000 (capture.db)" -ForegroundColor Gray
Write-Host "    - Node A URL:   https://mooned-antics-shorter.ngrok-free.dev (registration.db, insurance.db)" -ForegroundColor Gray
Write-Host "    - Node B URL:   https://manhood-overcome-copartner.ngrok-free.dev (theft.db, ministry.db)" -ForegroundColor Gray
Write-Host "    - AI Vision:    Google Gemini 3.5 Flash Active" -ForegroundColor Gray
Write-Host "    - Resilience:   Automatic zero-downtime local SQLite fallback enabled" -ForegroundColor Gray
Write-Host ""

$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) { $ProjectRoot = (Get-Location).Path }
$env:Path = "C:\Program Files\nodejs;" + $env:Path

$env:NODE_B_URL = "https://mooned-antics-shorter.ngrok-free.dev"
$env:NODE_C_URL = "https://manhood-overcome-copartner.ngrok-free.dev"

# 0. Check Remote Node Connections Live
python "$ProjectRoot\scripts\check_nodes.py"

# 1. Start Backend in new window
Write-Host "[*] Starting FastAPI Master Backend on port 8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectRoot\backend'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

# 2. Start Frontend in new window
Write-Host "[*] Starting React / Vite Frontend on port 5173..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:Path = 'C:\Program Files\nodejs;' + `$env:Path; Set-Location '$ProjectRoot\frontend'; & 'C:\Program Files\nodejs\npx.cmd' vite --host 0.0.0.0 --port 5173"

# Wait 3 seconds
Start-Sleep -Seconds 3

# 3. Open Browser
Write-Host "[*] Opening Browser..." -ForegroundColor Cyan
Start-Process "http://localhost:5173"
Start-Process "http://localhost:8000/docs"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "  Cluster is LIVE!" -ForegroundColor Green
Write-Host "    - Frontend UI:  http://localhost:5173" -ForegroundColor White
Write-Host "    - Backend Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "    - Run Viva Test: python scratch/test_evaluation_rubrics.py" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Green
