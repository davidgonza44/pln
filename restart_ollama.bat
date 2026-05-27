@echo off
REM Script to restart Ollama and verify connection

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo OLLAMA DIAGNOSTIC & RESTART SCRIPT
echo ============================================================
echo.

REM Kill any existing Ollama processes
echo [1/4] Stopping any running Ollama processes...
taskkill /F /IM ollama.exe >nul 2>&1
timeout /t 2 /nobreak

REM Start Ollama server
echo [2/4] Starting Ollama server...
start "Ollama Server" ollama serve
timeout /t 5 /nobreak

REM Test connection with curl
echo.
echo [3/4] Testing Ollama connection...
for /f "delims=" %%A in ('curl -s http://localhost:11434') do (
    echo Response: %%A
)

REM List models
echo.
echo [4/4] Checking installed models...
ollama list

echo.
echo ============================================================
echo SETUP COMPLETE
echo ============================================================
echo.
echo Backend should be running on: http://localhost:8000
echo Frontend is available at:     http://localhost:8000/
echo.
echo Open another terminal and run: python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
echo.
pause
