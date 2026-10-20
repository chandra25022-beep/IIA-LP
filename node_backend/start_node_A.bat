@echo off
:: ============================================================
::  IIA Distributed Node — NODE A (Friend 1)
::  Owns Databases: insurance.db + registration.db
::  Port: 8001
:: ============================================================

title IIA Distributed Node A - Insurance + Registration
color 0B

echo.
echo  ==============================================================
echo   IIA Information Integration Project - DISTRIBUTED NODE A
echo   Databases Owned: insurance.db  +  registration.db
echo   Port:            8001
echo  ==============================================================
echo.

cd /d "%~dp0"

:: ── Step 1: Virtual Environment Check / Setup ───────────────
echo [1/4] Setting up Python virtual environment...
if not exist "..\venv" (
    echo     Creating new virtual environment 'venv'...
    python -m venv ..\venv
)
call ..\venv\Scripts\activate.bat
echo     Virtual environment activated.
echo.

:: ── Step 2: Install Dependencies ────────────────────────────
echo [2/4] Installing Python requirements...
pip install -q fastapi "uvicorn[standard]" requests
echo     Dependencies installed successfully.
echo.

:: ── Step 3: Check Local IP ──────────────────────────────────
echo [3/4] Detecting Local Network IP...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address" 2^>nul') do (
    set LOCAL_IP=%%a
    goto :ip_done
)
:ip_done
set LOCAL_IP=%LOCAL_IP: =%
echo     Your Local IP on this WiFi/LAN is: %LOCAL_IP%
echo.

:: ── Step 4: Check ngrok (Optional for cross-WiFi/Internet) ──
echo [4/4] Checking ngrok for internet tunnel...
where ngrok >nul 2>&1
if errorlevel 1 (
    echo     [INFO] ngrok not detected in PATH.
    echo     If you and Master are on SAME WiFi / Mobile Hotspot:
    echo       Tell Master your LAN URL: http://%LOCAL_IP%:8001
    echo     If on DIFFERENT WiFi:
    echo       Install ngrok via: winget install ngrok.ngrok
    echo       Then run in a separate terminal: ngrok http 8001
) else (
    echo     ngrok detected! Starting ngrok tunnel in a new window...
    start "ngrok Tunnel - Node A (8001)" cmd /k "ngrok http 8001"
)
echo.

:: ── Step 5: Start Node A Fast-API Server ─────────────────────
echo  --------------------------------------------------------------
echo   STARTING NODE A SERVER on port 8001...
echo   Databases exposed: insurance, registration
echo  --------------------------------------------------------------
echo.

set NODE_DATABASES=insurance,registration
set NODE_PORT=8001
set NODE_HOST=0.0.0.0
python main.py
pause
