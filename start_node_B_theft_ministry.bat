@echo off
:: ============================================================
::  NODE B LAUNCHER (Friend 2 - Laptop 3)
::  Databases: theft.db + ministry.db
::  Port: 8002
:: ============================================================

title IIA Distributed Node B - Theft + Ministry (Port 8002)
color 0E

echo.
echo ============================================================
echo   IIA Information Integration Project - DISTRIBUTED NODE B
echo   Databases: theft.db + ministry.db
echo   Port:      8002
echo ============================================================
echo.

cd /d "%~dp0node_backend"
call start_node_B.bat
