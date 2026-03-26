@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "DRY_RUN=0"
set "CLEAN_START=1"
set "RUN_TESTS=0"
set "TEST_HEADED=0"

:parse_args
if "%~1"=="" goto args_done
if /I "%~1"=="--dry-run" (
  set "DRY_RUN=1"
  shift
  goto parse_args
)
if /I "%~1"=="--clean" (
  set "CLEAN_START=1"
  shift
  goto parse_args
)
if /I "%~1"=="--no-clean" (
  set "CLEAN_START=0"
  shift
  goto parse_args
)
if /I "%~1"=="--test" (
  set "RUN_TESTS=1"
  shift
  goto parse_args
)
if /I "%~1"=="--test-headed" (
  set "RUN_TESTS=1"
  set "TEST_HEADED=1"
  shift
  goto parse_args
)
echo [WARN] Ignoring unknown argument: %~1
shift
goto parse_args

:args_done

for %%I in ("%~dp0.") do set "PROJECT_ROOT=%%~fI"
set "FRONTEND_DIR=%PROJECT_ROOT%\frontend"
set "VENV_DIR=%PROJECT_ROOT%\.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_ACTIVATE=%VENV_DIR%\Scripts\activate.bat"

if not exist "%PROJECT_ROOT%\app.py" (
  echo [ERROR] Could not find app.py in "%PROJECT_ROOT%".
  pause
  exit /b 1
)

if not exist "%PROJECT_ROOT%\requirements.txt" (
  echo [ERROR] Could not find requirements.txt in "%PROJECT_ROOT%".
  pause
  exit /b 1
)

if not exist "%FRONTEND_DIR%\package.json" (
  echo [ERROR] Could not find frontend\package.json in "%FRONTEND_DIR%".
  pause
  exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
  where py >nul 2>nul
  if errorlevel 1 (
    echo [ERROR] Python is not installed or not on PATH.
    pause
    exit /b 1
  )
  set "SYSTEM_PYTHON=py -3"
) else (
  set "SYSTEM_PYTHON=python"
)

where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] npm is not installed or not on PATH.
  pause
  exit /b 1
)

pushd "%PROJECT_ROOT%" >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Could not access project root: "%PROJECT_ROOT%".
  pause
  exit /b 1
)

if not exist "%VENV_PYTHON%" (
  echo [SETUP] Creating virtual environment...
  call %SYSTEM_PYTHON% -m venv "%VENV_DIR%"
  if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    popd
    pause
    exit /b 1
  )
)

echo [SETUP] Ensuring backend dependencies...
call "%VENV_PYTHON%" -m pip install -r "%PROJECT_ROOT%\requirements.txt"
if errorlevel 1 (
  echo [ERROR] Backend dependency install failed.
  popd
  pause
  exit /b 1
)

if not exist "%FRONTEND_DIR%\node_modules" (
  echo [SETUP] Installing frontend dependencies...
  pushd "%FRONTEND_DIR%"
  call npm install
  if errorlevel 1 (
    echo [ERROR] Frontend dependency install failed.
    popd
    popd
    pause
    exit /b 1
  )
  popd
)

if "%LIFEOS_BACKEND_PORT%"=="" set "LIFEOS_BACKEND_PORT=5000"
if "%LIFEOS_FRONTEND_PORT%"=="" set "LIFEOS_FRONTEND_PORT=5173"
if "%LIFEOS_BIND_HOST%"=="" set "LIFEOS_BIND_HOST=0.0.0.0"
if "%LIFEOS_DEBUG%"=="" set "LIFEOS_DEBUG=1"
if "%LIFEOS_RELOADER%"=="" set "LIFEOS_RELOADER=0"
if "%LIFEOS_CLEAN_START%"=="" set "LIFEOS_CLEAN_START=%CLEAN_START%"
call :normalize_boolean LIFEOS_DEBUG 1
call :normalize_boolean LIFEOS_RELOADER 0
call :normalize_boolean LIFEOS_CLEAN_START 1

if "%LIFEOS_CLEAN_START%"=="1" (
  echo [SETUP] Stopping existing LifeOS backend/frontend processes...
  call :stop_existing_instances
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Sleep -Seconds 1" >nul 2>nul
)

if "%LIFEOS_PUBLIC_IP%"=="" (
  call :detect_lan_ip
)
if "%LIFEOS_PUBLIC_IP%"=="" set "LIFEOS_PUBLIC_IP=127.0.0.1"
call :trim_var LIFEOS_PUBLIC_IP

call :find_free_port "%LIFEOS_BACKEND_PORT%" LIFEOS_BACKEND_PORT
call :find_free_port "%LIFEOS_FRONTEND_PORT%" LIFEOS_FRONTEND_PORT

set "API_BASE_URL=http://%LIFEOS_PUBLIC_IP%:%LIFEOS_BACKEND_PORT%"
call :trim_var API_BASE_URL

echo [INFO] Project root: %PROJECT_ROOT%
echo [INFO] Backend bind host: %LIFEOS_BIND_HOST%
echo [INFO] Public IP: %LIFEOS_PUBLIC_IP%
echo [INFO] Backend port: %LIFEOS_BACKEND_PORT%
echo [INFO] Frontend port: %LIFEOS_FRONTEND_PORT%
echo [INFO] Debug mode: %LIFEOS_DEBUG%
echo [INFO] Reloader: %LIFEOS_RELOADER%
echo [INFO] Clean start: %LIFEOS_CLEAN_START%
if "%RUN_TESTS%"=="1" (
  if "%TEST_HEADED%"=="1" (
    echo [INFO] E2E mode: headed
  ) else (
    echo [INFO] E2E mode: headless
  )
)
echo [INFO] VITE_API_BASE_URL: %API_BASE_URL%

if "%DRY_RUN%"=="1" (
  if "%RUN_TESTS%"=="1" (
    echo [DRY RUN] Startup checks complete. Skipping E2E execution.
  ) else (
    echo [DRY RUN] Startup checks complete. Skipping terminal launch.
  )
  popd
  exit /b 0
)

if "%RUN_TESTS%"=="1" goto run_e2e_tests

echo [START] Launching backend terminal...
start "LifeOS Backend" cmd /k "cd /d ""%PROJECT_ROOT%"" && call ""%VENV_ACTIVATE%"" && set LIFEOS_HOST=%LIFEOS_BIND_HOST% && set LIFEOS_PORT=%LIFEOS_BACKEND_PORT% && set LIFEOS_DEBUG=%LIFEOS_DEBUG% && set LIFEOS_RELOADER=%LIFEOS_RELOADER% && python ""%PROJECT_ROOT%\app.py"""

echo [START] Launching frontend terminal...
start "LifeOS Frontend" cmd /k "cd /d ""%FRONTEND_DIR%"" && set VITE_API_BASE_URL=%API_BASE_URL% && npm run dev -- --host %LIFEOS_BIND_HOST% --port %LIFEOS_FRONTEND_PORT%"

echo.
echo LifeOS is starting in separate terminals:
echo - Backend local:   http://127.0.0.1:%LIFEOS_BACKEND_PORT%
echo - Backend network: http://%LIFEOS_PUBLIC_IP%:%LIFEOS_BACKEND_PORT%
echo - Frontend local:  http://127.0.0.1:%LIFEOS_FRONTEND_PORT%
echo - Frontend network:http://%LIFEOS_PUBLIC_IP%:%LIFEOS_FRONTEND_PORT%
echo.
echo Close the opened terminal windows to stop the services.

popd
exit /b 0

:run_e2e_tests
echo [TEST] Running frontend E2E smoke checks...
pushd "%FRONTEND_DIR%"
if errorlevel 1 (
  echo [ERROR] Could not access frontend directory.
  popd
  pause
  exit /b 1
)

echo [TEST] Ensuring Playwright Chromium browser is available...
call npx playwright install chromium
if errorlevel 1 (
  echo [ERROR] Failed to install Playwright browser dependencies.
  popd
  popd
  pause
  exit /b 1
)

set "CI=1"
if "%TEST_HEADED%"=="1" (
  call npm run test:e2e:headed
) else (
  call npm run test:e2e
)
set "E2E_EXIT=%ERRORLEVEL%"
popd

if "%E2E_EXIT%"=="0" (
  echo [TEST] E2E smoke checks passed.
) else (
  echo [TEST] E2E smoke checks failed with exit code %E2E_EXIT%.
)

popd
exit /b %E2E_EXIT%

:detect_lan_ip
for /f "usebackq delims=" %%I in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -ne '127.0.0.1' -and $_.IPAddress -notlike '169.254*' } | Select-Object -ExpandProperty IPAddress -First 1)"`) do (
  set "LIFEOS_PUBLIC_IP=%%I"
  goto :eof
)
set "LIFEOS_PUBLIC_IP=127.0.0.1"
exit /b 0

:normalize_boolean
setlocal EnableDelayedExpansion
set "raw=!%~1!"
if not defined raw set "raw=%~2"
set "normalized=%~2"
if /I "!raw!"=="1" set "normalized=1"
if /I "!raw!"=="0" set "normalized=0"
if /I "!raw!"=="true" set "normalized=1"
if /I "!raw!"=="false" set "normalized=0"
if /I "!raw!"=="yes" set "normalized=1"
if /I "!raw!"=="no" set "normalized=0"
if /I "!raw!"=="on" set "normalized=1"
if /I "!raw!"=="off" set "normalized=0"
endlocal & set "%~1=%normalized%"
exit /b 0

:trim_var
setlocal EnableDelayedExpansion
set "raw=!%~1!"
if not defined raw (
  endlocal & exit /b 0
)
for /f "tokens=* delims= " %%A in ("!raw!") do set "trimmed=%%A"
:trim_var_right
if not defined trimmed goto trim_var_done
if "!trimmed:~-1!"==" " set "trimmed=!trimmed:~0,-1!" & goto trim_var_right
:trim_var_done
endlocal & set "%~1=%trimmed%"
exit /b 0

:stop_existing_instances
taskkill /FI "WINDOWTITLE eq LifeOS Backend*" /T /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq LifeOS Frontend*" /T /F >nul 2>nul
for /f "usebackq delims=" %%I in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$root = '%PROJECT_ROOT%'.ToLower(); Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -and $_.CommandLine.ToLower().Contains($root) -and (($_.Name -ieq 'python.exe' -and $_.CommandLine.ToLower().Contains('app.py')) -or ($_.Name -ieq 'node.exe' -and $_.CommandLine.ToLower().Contains('vite'))) } | ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop } catch {} }; Write-Output done"`) do set "LIFEOS_STOP_DONE=%%I"
echo [INFO] Existing launcher processes were stopped (if any were running).
exit /b 0

:find_free_port
setlocal EnableDelayedExpansion
set "candidate=%~1"
if not defined candidate set "candidate=5000"
if "!candidate!"=="" set "candidate=5000"

:find_free_port_loop
set "busy=0"
for /f "usebackq delims=" %%I in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$inUse = Get-NetTCPConnection -LocalPort %candidate% -State Listen -ErrorAction SilentlyContinue; if($inUse){'1'} else {'0'}"`) do set "busy=%%I"
if /I "!busy!"=="1" (
  set /a candidate+=1
  if !candidate! GTR 65535 set "candidate=1024"
  goto :find_free_port_loop
)
endlocal & set "%~2=%candidate%"
exit /b 0
