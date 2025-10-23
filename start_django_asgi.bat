@echo off
echo Starting Django with ASGI for WebSocket support...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Verify virtual environment is activated
if not defined VIRTUAL_ENV (
    echo ERROR: Virtual environment not activated properly
    pause
    exit /b 1
)

REM Install daphne if not already installed
venv\Scripts\pip.exe install daphne

REM Start Django with ASGI
echo Starting Django with ASGI server...
venv\Scripts\daphne.exe -b localhost -p 8000 mysite.asgi:application

if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Failed to start Django with ASGI
    echo Make sure all dependencies are installed
    echo.
    pause
)
