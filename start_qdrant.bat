@echo off
chcp 65001 >nul
title RAG-Qdrant
setlocal

REM This file is intentionally ASCII-only, see start_all.bat for the reason.
set "QDRANT_HOME=%~dp0tools\qdrant"

echo === Qdrant vector database (native mode) ===
echo.

if not exist "%QDRANT_HOME%\qdrant.exe" (
    echo ERROR: not found: %QDRANT_HOME%\qdrant.exe
    pause
    exit /b 1
)

REM Keep both the binary and its data on D drive to save C drive space
set "QDRANT__STORAGE__STORAGE_PATH=%QDRANT_HOME%\storage"
set "QDRANT__SERVICE__HTTP_PORT=6333"
set "QDRANT__SERVICE__GRPC_PORT=6334"

echo Data dir:  %QDRANT__STORAGE__STORAGE_PATH%
echo HTTP port: 6333    gRPC port: 6334
echo Dashboard: http://localhost:6333/dashboard
echo Press Ctrl+C to stop
echo.

"%QDRANT_HOME%\qdrant.exe"

pause