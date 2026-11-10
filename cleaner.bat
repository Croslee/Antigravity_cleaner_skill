@echo off
title Antigravity Storage Cleaner Dashboard
echo ====================================================================
echo         Antigravity Storage Cleaner Dashboard
echo ====================================================================
echo.
echo Starting local server and opening web dashboard...

python "%~dp0cleaner_server.py"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Failed to start server. Please verify Python is installed.
    pause
)
