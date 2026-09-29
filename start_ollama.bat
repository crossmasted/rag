@echo off
chcp 65001 >nul
title RAG-Ollama
setlocal

REM This file is intentionally ASCII-only. Paths are derived from %~dp0 because the
REM project path contains non-ASCII characters, and hardcoding them in a .bat can
REM make cmd mis-parse the file when the console starts at code page 936.

set "OLLAMA_HOME=%~dp0tools\ollama"
set "OLLAMA_MODELS=%~dp0tools\ollama-data"

echo === Ollama (native mode) ===
echo.
echo Model dir: %OLLAMA_MODELS%
echo Port:      11434
echo Press Ctrl+C to stop
echo.

if not exist "%OLLAMA_HOME%\ollama.exe" (
    echo ERROR: not found: %OLLAMA_HOME%\ollama.exe
    pause
    exit /b 1
)

"%OLLAMA_HOME%\ollama.exe" serve

pause