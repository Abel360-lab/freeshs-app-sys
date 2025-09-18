@echo off
echo Starting Celery Beat Scheduler...
echo.

REM Activate virtual environment
call venv\Scripts\activate

REM Start Celery beat scheduler
celery -A mysite beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler

if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Failed to start Celery beat
    echo Make sure Redis is running and Django is properly configured
    echo.
    pause
)
