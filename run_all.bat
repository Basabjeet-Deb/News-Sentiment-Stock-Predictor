@echo off
setlocal
cd /d "%~dp0"

REM One-click launcher entrypoint.
REM (Implementation lives in PowerShell to avoid cmd parsing edge-cases.)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_all.ps1"

pause

