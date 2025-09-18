@echo off
echo Starting Celery Worker...
echo.

REM Activate virtual environment
call venv\Scripts\activate

REM Start Celery worker
celery -A mysite worker --loglevel=info --pool=solo

if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Failed to start Celery worker
    echo Make sure Redis is running and Django is properly configured
    echo.
    pause
)
