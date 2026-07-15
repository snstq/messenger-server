@echo off
echo ========================================
echo   Messenger Server + Public Tunnel
echo ========================================
echo.

REM Start Python server in background
echo Starting Python server...
start /B python server.py
timeout /t 2 /nobreak >nul

REM Start localtunnel to expose port 8765
echo.
echo Starting public tunnel...
echo.
lt --port 8765

pause
