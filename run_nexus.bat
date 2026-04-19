@echo off
chcp 65001 >nul
title NEXUS Load Balancer Launcher
setlocal

echo ==========================================================
echo    NEXUS LOAD BALANCER -- STARTING ENGINES
echo ==========================================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.10+ from python.org
    pause
    exit /b
)

:: Install/Verify dependencies
echo [1/3] Verifying system dependencies...
pip install -r requirements.txt --quiet

:: Check for .env and warn if missing
if not exist .env (
    echo [WARN] .env file not found. Email features will be in Simulation Mode.
    echo        Copying .env.example template...
    copy .env.example .env >nul
)

echo [2/3] Checking Port 8000 availability...
netstat -ano | findstr :8000 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo.
    echo [ERROR] Port 8000 is occupied. 
    echo         Ensuring any stale processes are cleared...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill /f /pid %%a >nul 2>&1
)

echo [3/3] Launching Load Balancer Simulator...
echo.
echo --------------------------------------------------------
echo DASHBOARD: http://localhost:8000
echo --------------------------------------------------------
echo.

python run.py

if %errorlevel% neq 0 (
    echo.
    echo [CRITICAL] The simulation engine has crashed.
    pause
)

endlocal
