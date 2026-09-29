@echo off
chcp 65001 >nul
title RAG-MySQL
setlocal

REM This file is intentionally ASCII-only, see start_all.bat for the reason.
REM Set MYSQL_HOME to your MySQL 8 install directory if it differs.

set "MYSQL_HOME=D:\MySQL\mysql-8.0.26-winx64"

echo === MySQL 8 (native mode) ===
echo.
echo Install dir: %MYSQL_HOME%
echo Port:        3306
echo Press Ctrl+C to stop
echo.

if not exist "%MYSQL_HOME%\bin\mysqld.exe" (
    echo ERROR: not found: %MYSQL_HOME%\bin\mysqld.exe
    echo Edit MYSQL_HOME in this file to point at your MySQL install.
    pause
    exit /b 1
)

if not exist "%MYSQL_HOME%\my.ini" (
    echo ERROR: not found: %MYSQL_HOME%\my.ini
    pause
    exit /b 1
)

"%MYSQL_HOME%\bin\mysqld.exe" --defaults-file="%MYSQL_HOME%\my.ini"

pause
