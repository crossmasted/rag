@echo off
chcp 65001 >nul
title RAG-Backend
setlocal

REM This file is intentionally ASCII-only, see start_all.bat for the reason.
set "PROJECT=%~dp0"
set "VENV_PY=%PROJECT%backend\.venv\Scripts\python.exe"

echo === RAG backend API (native mode) ===
echo.

if not exist "%VENV_PY%" (
    echo ERROR: virtualenv not found: %VENV_PY%
    echo Run first: python -m venv "%PROJECT%backend\.venv"
    pause
    exit /b 1
)

REM Point at the native local services instead of docker service names
set "OLLAMA_HOST=http://localhost:11434"
set "QDRANT_HOST=localhost"
set "QDRANT_PORT=6333"
set "MAX_CONCURRENT=5"

cd /d "%PROJECT%backend"

echo Ollama:      %OLLAMA_HOST%
echo Qdrant:      %QDRANT_HOST%:%QDRANT_PORT%
echo API docs:    http://localhost:8000/docs
echo Press Ctrl+C to stop
echo.

"%VENV_PY%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000

pause