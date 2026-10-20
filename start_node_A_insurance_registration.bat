@echo off
:: ============================================================
::  NODE A LAUNCHER (Friend 1 - Laptop 2)
::  Databases: insurance.db + registration.db
::  Port: 8001
:: ============================================================

title IIA Distributed Node A - Insurance + Registration (Port 8001)
color 0B

echo.
echo ============================================================
echo   IIA Information Integration Project - DISTRIBUTED NODE A
echo   Databases: insurance.db + registration.db
echo   Port:      8001
echo ============================================================
echo.

cd /d "%~dp0node_backend"
call start_node_A.bat
