@echo off
REM MVP PLN Ollama - Windows Startup Script
REM This script sets up the Python virtual environment and starts the backend

cd /d %~dp0

echo.
echo ============================================================
echo MVP PLN - Ollama Local Backend Startup
echo ============================================================
echo.

REM Check if .venv exists
if not exist ".venv" (
    echo [*] Creating Python virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        echo Make sure Python is installed and accessible
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip
echo [*] Upgrading pip...
python -m pip install --upgrade pip -q
if errorlevel 1 (
    echo WARNING: pip upgrade failed, continuing anyway...
)

REM Install requirements
echo [*] Installing dependencies from requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install requirements
    echo Check requirements.txt and your internet connection
    pause
    exit /b 1
)

REM Verify Ollama is accessible
echo.
echo [*] Verifying Ollama connection...
timeout /t 2 /nobreak >nul
curl -s http://localhost:11434 >nul 2>&1
if errorlevel 1 (
    echo WARNING: Ollama not responding on localhost:11434
    echo Make sure Ollama is running (open the Ollama app)
    echo.
)

REM Start backend server
echo.
echo ============================================================
echo Backend iniciado en http://127.0.0.1:8000
echo Frontend available at http://localhost:8000
echo Recuerda tener Ollama abierto y un modelo instalado
echo Ejemplo: ollama pull qwen2.5:7b
echo.
echo [Ctrl+C to stop the server]
echo ============================================================
echo.

uvicorn backend.main:app --host 127.0.0.1 --port 8000

pause
