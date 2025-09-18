@echo off
echo Starting GCX Supplier Application System with Real-time Features
echo ================================================================
echo.

echo This will start:
echo 1. Redis Server (Docker)
echo 2. Celery Worker (Background Tasks)
echo 3. Celery Beat (Scheduled Tasks)
echo 4. Django Server (Web + WebSockets)
echo.

echo PREREQUISITES:
echo - Docker Desktop must be installed and running
echo - See DOCKER_SETUP.md for installation instructions
echo.

echo IMPORTANT: You need to run each component in a separate terminal window
echo.

echo Starting Redis Server in new window...
start "Redis Server" cmd /k "start_redis.bat"

timeout /t 3 /nobreak >nul

echo Starting Celery Worker in new window...
start "Celery Worker" cmd /k "start_celery.bat"

timeout /t 3 /nobreak >nul

echo Starting Celery Beat in new window...
start "Celery Beat" cmd /k "start_celery_beat.bat"

timeout /t 3 /nobreak >nul

echo Starting Django Server with ASGI in new window...
start "Django Server (ASGI)" cmd /k "start_django_asgi.bat"

echo.
echo All components are starting...
echo.
echo Check each window for any errors
echo.
echo Once all are running, visit: http://localhost:8000/backoffice/
echo.
pause
