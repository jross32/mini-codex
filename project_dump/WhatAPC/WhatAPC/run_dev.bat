@echo off
setlocal EnableExtensions

rem Resolve absolute repo root (strip trailing slash)
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "BACKEND_DIR=%ROOT%\backend"
set "FRONTEND_DIR=%ROOT%\frontend"
set "BACKEND_PORT=5000"
set "FRONTEND_PORT=5173"
set "API_BASE=http://localhost:%BACKEND_PORT%/api"

if not exist "%BACKEND_DIR%\app.py" (
  echo [ERROR] Missing backend app: "%BACKEND_DIR%\app.py"
  exit /b 1
)
if not exist "%FRONTEND_DIR%\package.json" (
  echo [ERROR] Missing frontend package: "%FRONTEND_DIR%\package.json"
  exit /b 1
)

rem Pick backend interpreter (prefer project venv)
set "PYTHON_CMD=python"
if exist "%BACKEND_DIR%\.venv\Scripts\python.exe" (
  set "PYTHON_CMD=%BACKEND_DIR%\.venv\Scripts\python.exe"
) else (
  where python >nul 2>&1
  if errorlevel 1 (
    echo [ERROR] Python not found and backend venv missing.
    echo Create venv in "%BACKEND_DIR%\.venv" or install Python on PATH.
    exit /b 1
  )
)

where npm >nul 2>&1
if errorlevel 1 (
  echo [ERROR] npm not found. Install Node.js and try again.
  exit /b 1
)
if not exist "%FRONTEND_DIR%\node_modules" (
  echo [ERROR] Frontend dependencies missing at "%FRONTEND_DIR%\node_modules".
  echo Run: cd /d "%FRONTEND_DIR%" ^&^& npm install
  exit /b 1
)

rem Launch backend in its own window with explicit env
start "WhatAPC Backend" /D "%BACKEND_DIR%" cmd /k "set FLASK_ENV=development&&set PORT=%BACKEND_PORT%&&set DATABASE_URL=sqlite:///whatapc.db&&set CORS_ORIGINS=http://localhost:%FRONTEND_PORT%&&%PYTHON_CMD% app.py"

rem Small delay so frontend doesn't race API startup logs
timeout /t 1 /nobreak >nul

rem Launch frontend in its own window
start "WhatAPC Frontend" /D "%FRONTEND_DIR%" cmd /k "set VITE_API_BASE=%API_BASE%&&npm run dev"

echo Backend:  http://localhost:%BACKEND_PORT%
echo Frontend: http://localhost:%FRONTEND_PORT%
echo API base: %API_BASE%
echo Two terminals opened. Use Ctrl+C in each window to stop.

endlocal
