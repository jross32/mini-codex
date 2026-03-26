@echo off
echo Starting Flask backend...
start cmd /k "python app.py"
echo Starting React frontend...
start cmd /k "npm start"
echo Both servers are starting in separate windows. Close this window if desired.
pause