@echo off
chcp 65001 >nul

REM This file is intentionally ASCII-only, see start_all.bat for the reason.

echo === Stop local RAG system ===
echo.

REM 1) Close the console windows that host our services.
REM    Matching on the COMMAND LINE rather than the window title, because the
REM    frontend window does not keep the title we set: npm/vite overwrite it,
REM    so it stays at the cmd default and a title match would never hit it.
REM    Only ASCII literals are used here on purpose.
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'cmd.exe' -and $_.CommandLine -match 'start_(ollama|qdrant|backend)[.]bat|frontend\\start[.]bat|start_all[.]bat' } | ForEach-Object { Write-Host ('closing window  pid ' + $_.ProcessId); Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"

REM 2) Fallback: stop whatever still holds the service ports. This also covers
REM    services that were started outside start_all.bat.
powershell -NoProfile -Command "$ports = 11434,6333,6334,8000,5173; $names = @{11434='Ollama'; 6333='Qdrant'; 6334='Qdrant(gRPC)'; 8000='Backend API'; 5173='Frontend'}; foreach ($p in $ports) { $conns = Get-NetTCPConnection -State Listen -LocalPort $p -ErrorAction SilentlyContinue; if ($conns) { foreach ($c in $conns) { Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Host ('stopped ' + $names[$p] + '  (port ' + $p + ')') } } else { Write-Host ('not running: ' + $names[$p] + '  (port ' + $p + ')') } }"

echo.
echo All services stopped.
pause