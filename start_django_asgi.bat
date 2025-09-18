@echo off
echo Starting Django with ASGI for WebSocket support...
echo.

REM Activate virtual environment
call venv\Scripts\activate

REM Install daphne if not already installed
pip install daphne

REM Start Django with ASGI
echo Starting Django with ASGI server...
daphne -b 172.25.221.239  -p 8000 mysite.asgi:application

if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Failed to start Django with ASGI
    echo Make sure all dependencies are installed
    echo.
    pause
)
