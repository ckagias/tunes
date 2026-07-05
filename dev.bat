@echo off
REM Runs both the FastAPI backend and the Vite frontend for local development,
REM both in this one window with interleaved output. Ctrl+C stops both.
setlocal

cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0dev.ps1"
