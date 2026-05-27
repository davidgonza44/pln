@echo off
REM Quick start script for MVP PLN Ollama
REM This script checks prerequisites and starts the backend

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo MVP PLN - QUICK START
echo ============================================================
echo.

REM Check if backend is already running
echo [*] Checking if backend is already running...
curl -s http://localhost:8000 >nul 2>&1
if !errorlevel! equ 0 (
    echo.
    echo [OK] Backend is already running!
    echo Open your browser: http://localhost:8000
    pause
    exit /b 0
)

REM Check if .venv exists
if not exist ".venv" (
    echo [*] Creating Python virtual environment...
    python -m venv .venv
    if !errorlevel! neq 0 (
        echo.
        echo [ERROR] Failed to create virtual environment
        echo Make sure Python is installed
        pause
        exit /b 1
    )
)

REM Activate and install
echo [*] Setting up dependencies...
call .venv\Scripts\activate.bat
python -m pip install -q -r requirements.txt
if !errorlevel! neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

REM Check Ollama
echo.
echo [*] Checking Ollama...
curl -s http://localhost:11434 >nul 2>&1
if !errorlevel! neq 0 (
    echo [WARNING] Ollama not responding - make sure it's open!
)

REM Start backend
echo.
echo ============================================================
echo [OK] Starting backend on http://localhost:8000
echo ============================================================
echo.
echo Open your browser: http://localhost:8000
echo Close this window to stop the server
echo.

uvicorn backend.main:app --host 127.0.0.1 --port 8000

pause
