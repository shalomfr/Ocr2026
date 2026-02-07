@echo off
chcp 65001 >nul
title Hebrew OCR Training System

echo ============================================
echo   Hebrew OCR Training System - Starting...
echo ============================================
echo.

:: Kill any existing processes on ports 5000 and 5173
echo [1/4] Cleaning ports...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo    Ports 5000, 5173 cleared.
echo.

:: Set project root
set PROJECT_ROOT=%~dp0
cd /d "%PROJECT_ROOT%"

:: Check Python
echo [2/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo    ERROR: Python not found! Install Python 3.11+
    pause
    exit /b 1
)
echo    Python OK.
echo.

:: Install backend dependencies if needed
echo [3/4] Checking backend dependencies...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo    Installing dependencies...
    pip install -r backend\requirements.txt
) else (
    echo    Dependencies OK.
)
echo.

:: Start Backend in background
echo [4/4] Starting servers...
echo.
echo    Starting Backend on http://localhost:5000 ...
start "OCR-Backend" cmd /k "cd /d %PROJECT_ROOT% && python run.py"

:: Wait for backend to start
timeout /t 3 /nobreak >nul

:: Start Frontend
echo    Starting Frontend on http://localhost:5173 ...
start "OCR-Frontend" cmd /k "cd /d %PROJECT_ROOT%\frontend && npm install && npm run dev"

:: Wait for frontend to start
timeout /t 5 /nobreak >nul

:: Open browser
echo.
echo ============================================
echo   Backend:  http://localhost:5000
echo   Frontend: http://localhost:5173
echo ============================================
echo.
echo   Opening browser...
start http://localhost:5173

echo.
echo   To stop: close the two terminal windows
echo   or press Ctrl+C in each one.
echo.
pause
