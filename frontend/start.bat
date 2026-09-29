@echo off
chcp 65001 >nul
title RAG-Frontend
setlocal

REM This file is intentionally ASCII-only, see ..\start_all.bat for the reason.
REM Use the bundled portable Node 20. The system Node 14 is too old for Vite.
set "NODE_HOME=%~dp0..\tools\node20\node-v20.18.0-win-x64"

echo === RAG frontend ===
echo.

if not exist "%NODE_HOME%\node.exe" (
    echo ERROR: portable Node.js not found: %NODE_HOME%
    pause
    exit /b 1
)
set "PATH=%NODE_HOME%;%PATH%"

echo Node.js version:
node --version
echo.

cd /d "%~dp0"

if not exist node_modules (
    echo First run: installing dependencies...
    call npm install
    echo.
)

echo Starting dev server...
echo URL: http://localhost:5173
echo Press Ctrl+C to stop
echo.
call npm run dev

pause