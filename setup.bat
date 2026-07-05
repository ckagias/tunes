@echo off
REM One-shot setup for Windows: installs missing prerequisites (Python, Node.js,
REM ffmpeg) via winget, creates the backend venv, installs both dependency sets,
REM and launches the app. Safe to double-click again any time — already-installed
REM things are skipped.
setlocal enabledelayedexpansion

cd /d "%~dp0"

set NEEDS_RESTART=0

echo ==============================================
echo  Tunes setup
echo ==============================================
echo.

REM --- winget itself ---
where winget >nul 2>nul
if errorlevel 1 (
    echo [ERROR] winget was not found on this system.
    echo.
    echo winget ships with Windows 11 and recent Windows 10 updates. Install
    echo "App Installer" from the Microsoft Store, then run this script again:
    echo   https://apps.microsoft.com/detail/9nblggh4nns1
    echo.
    echo Alternatively, install Python, Node.js, and ffmpeg manually yourself
    echo ^(see README.md^), then run this script again to finish setup.
    pause
    exit /b 1
)

REM --- Python ---
where python >nul 2>nul
if errorlevel 1 (
    echo [1/3] Python not found. Installing via winget...
    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    if errorlevel 1 (
        echo [ERROR] Python install failed. Install it manually from python.org and re-run this script.
        pause
        exit /b 1
    )
    set NEEDS_RESTART=1
) else (
    echo [1/3] Python already installed - OK
)

REM --- Node.js ---
where node >nul 2>nul
if errorlevel 1 (
    echo [2/3] Node.js not found. Installing via winget...
    winget install -e --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements
    if errorlevel 1 (
        echo [ERROR] Node.js install failed. Install it manually from nodejs.org and re-run this script.
        pause
        exit /b 1
    )
    set NEEDS_RESTART=1
) else (
    echo [2/3] Node.js already installed - OK
)

REM --- ffmpeg ---
where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo [3/3] ffmpeg not found. Installing via winget...
    winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
    if errorlevel 1 (
        echo [ERROR] ffmpeg install failed. Install it manually ^(see README.md^) and re-run this script.
        pause
        exit /b 1
    )
    set NEEDS_RESTART=1
) else (
    echo [3/3] ffmpeg already installed - OK
)

echo.

if "%NEEDS_RESTART%"=="1" (
    echo Some tools were just installed and Windows needs a fresh terminal to
    echo see them on PATH. Restarting setup in a new window to pick that up...
    echo.
    timeout /t 3 >nul
    start "" cmd /c "cd /d "%~dp0" && setup.bat"
    exit /b 0
)

echo All prerequisites present. Installing project dependencies...
echo.

cd backend
if not exist .venv (
    echo Creating Python virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate.bat
echo Installing backend dependencies ^(this can take a minute^)...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Backend dependency install failed. See the error above.
    pause
    exit /b 1
)
cd ..

cd frontend
echo Installing frontend dependencies ^(this can take a minute^)...
call npm install --silent
if errorlevel 1 (
    echo [ERROR] Frontend dependency install failed. See the error above.
    pause
    exit /b 1
)
cd ..

echo.
echo ==============================================
echo  Setup complete. Launching Tunes...
echo ==============================================
echo.

call dev.bat
