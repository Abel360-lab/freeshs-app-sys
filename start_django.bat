@echo off
echo Starting Django Development Server with WebSocket support...
echo.

REM Activate virtual environment
call venv\Scripts\activate

REM Check if daphne is installed
python -c "import daphne" 2>nul
if %ERRORLEVEL% neq 0 (
    echo Installing daphne for WebSocket support...
    pip install daphne
)

REM Start Django with ASGI for WebSocket support
echo Starting Django with ASGI (WebSocket support)...
daphne -b 0.0.0.0 -p 8000 mysite.asgi:application

if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Failed to start Django server with ASGI
    echo Trying fallback with runserver...
    python manage.py runserver
    if %ERRORLEVEL% neq 0 (
        echo.
        echo ERROR: Failed to start Django server
        echo Make sure all dependencies are installed and migrations are applied
        echo.
        pause
    )
)
