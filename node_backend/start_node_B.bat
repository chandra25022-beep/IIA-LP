@echo off
:: ============================================================
::  IIA Distributed Node — NODE B (Friend 2)
::  Owns Databases: theft.db + ministry.db
::  Port: 8002
:: ============================================================

title IIA Distributed Node B - Theft + Ministry
color 0E

echo.
echo  ==============================================================
echo   IIA Information Integration Project - DISTRIBUTED NODE B
echo   Databases Owned: theft.db  +  ministry.db
echo   Port:            8002
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
    echo       Tell Master your LAN URL: http://%LOCAL_IP%:8002
    echo     If on DIFFERENT WiFi:
    echo       Install ngrok via: winget install ngrok.ngrok
    echo       Then run in a separate terminal: ngrok http 8002
) else (
    echo     ngrok detected! Starting ngrok tunnel in a new window...
    start "ngrok Tunnel - Node B (8002)" cmd /k "ngrok http 8002"
)
echo.

:: ── Step 5: Start Node B Fast-API Server ─────────────────────
echo  --------------------------------------------------------------
echo   STARTING NODE B SERVER on port 8002...
echo   Databases exposed: theft, ministry
echo  --------------------------------------------------------------
echo.

set NODE_DATABASES=theft,ministry
set NODE_PORT=8002
set NODE_HOST=0.0.0.0
python main.py
pause
