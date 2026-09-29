@echo off
chcp 65001 >nul
setlocal

REM This file is intentionally ASCII-only. Non-ASCII bytes inside a .bat can make
REM cmd mis-parse the file when the console starts at code page 936 (double-click),
REM which silently breaks later lines. Project paths are derived from %~dp0 instead
REM of being hardcoded, so no non-ASCII literal is needed anywhere in this file.

set "ROOT=%~dp0"

echo === Start local RAG system (native mode, no Docker) ===
echo.
echo Opening 4 windows: Ollama / Qdrant / Backend / Frontend
echo Close a window to stop that single service.
echo.

REM Hand each child script straight to `start`.
REM Do NOT use `cmd /k "title X && <script>"` here: that builds a command STRING
REM which cmd parses at the current console code page, and %ROOT% injects
REM non-ASCII bytes into it, corrupting the && chain. A plain file path is
REM resolved natively, so it is immune to that problem.
start "RAG-Ollama" "%ROOT%start_ollama.bat"

REM Give Ollama a head start. ping replaces timeout, because timeout fails with
REM "Input redirection is not supported" when this script runs with redirected input.
ping -n 6 127.0.0.1 >nul

start "RAG-Qdrant" "%ROOT%start_qdrant.bat"

ping -n 4 127.0.0.1 >nul

start "RAG-Backend" "%ROOT%start_backend.bat"

ping -n 4 127.0.0.1 >nul

start "RAG-Frontend" "%ROOT%frontend\start.bat"

echo.
echo Waiting for all services to be ready (up to 60s)...

REM The startup above is serial and the backend takes ~15-20s to be ready.
REM Fixed sleeps are unreliable: a question asked right after the windows open
REM hits a not-yet-ready backend and the frontend reports a connection error.
REM Poll the two ports instead, and only then print the "ready" message.
powershell -NoProfile -Command "for ($i = 0; $i -lt 30; $i++) { $p = (Get-NetTCPConnection -State Listen -LocalPort 8000,5173 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty LocalPort -Unique); if (($p -contains 8000) -and ($p -contains 5173)) { exit 0 }; Start-Sleep -Seconds 2 }; exit 1"
if errorlevel 1 (
    echo WARNING: some services are not ready yet. Check the four windows.
) else (
    echo All services ready. Open http://localhost:5173
)
echo Health check: http://localhost:8000/health

REM Pre-warm: pin both models into VRAM (keep_alive=-1) so the first question
REM does not pay the 30-70s model-loading cost. Both models fit in 4GB VRAM
REM (qwen2.5:3b ~2.2GB + bge-m3 ~0.6GB).
echo.
echo Pre-warming models into GPU memory...
powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; $c = @{ model='qwen2.5:3b'; messages=@(@{ role='user'; content='prewarm' }); stream=$false; keep_alive=-1 } | ConvertTo-Json -Depth 6; Invoke-RestMethod -Uri 'http://localhost:11434/api/chat' -Method Post -ContentType 'application/json' -Body $c -TimeoutSec 120 | Out-Null"
powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; $e = @{ model='bge-m3'; input='prewarm'; keep_alive=-1; options=@{ num_ctx=512 } } | ConvertTo-Json -Depth 6; Invoke-RestMethod -Uri 'http://localhost:11434/api/embed' -Method Post -ContentType 'application/json' -Body $e -TimeoutSec 120 | Out-Null"
echo Models pinned. Ask your question at http://localhost:5173
echo.
pause