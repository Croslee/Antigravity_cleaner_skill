@echo off
title Antigravity Storage Cleaner Dashboard
echo ====================================================================
echo         🚀 Khoi dong Antigravity Storage Cleaner Dashboard 🚀
echo ====================================================================
echo.
echo Dang kiem tra moi truong Python va khoi dong may chu...

python "%~dp0cleaner_server.py"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LOI] Khong the khoi dong may chu. Vui long kiem tra Python da duoc cai dat.
    pause
)
