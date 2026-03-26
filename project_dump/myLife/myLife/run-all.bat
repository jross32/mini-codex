@echo off
setlocal
set ROOT=%~dp0
cd /d %ROOT%

:: Detect LAN IPv4
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set IP=%%i
    goto :found
)
:found
set IP=%IP: =%
if "%IP%"=="" set IP=127.0.0.1

echo Detected IP: %IP%

:: CORS origins include localhost and LAN
set CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://%IP%:5173
:: Dev secrets (make these unique for you; length >=32 bytes to avoid JWT warnings)
set SECRET_KEY=dev-secret-please-change-32chars-long-abcdef123456
set JWT_SECRET_KEY=dev-jwt-secret-please-change-32chars-long-abcdef123456

:: Open firewall for API (5000) and Vite (5173) if not already
netsh advfirewall firewall add rule name="myLife API 5000" dir=in action=allow protocol=TCP localport=5000 >nul 2>&1
netsh advfirewall firewall add rule name="myLife Web 5173" dir=in action=allow protocol=TCP localport=5173 >nul 2>&1

:: Start Flask API
start "myLife API" cmd /k "cd /d %ROOT%api && set CORS_ORIGINS=%CORS_ORIGINS% && call venv\Scripts\activate && python -m app.main"

:: Start Vite frontend pointing to LAN API
start "myLife Web" cmd /k "cd /d %ROOT%web && set VITE_API_URL=http://%IP%:5000 && npm run dev -- --host --port 5173"

echo Both servers launching... close windows to stop.
