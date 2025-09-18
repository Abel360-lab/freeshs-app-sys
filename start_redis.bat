@echo off
echo Starting Redis Server with Docker...
echo.

REM Check if Docker is running
docker --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker is not installed or not running
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

REM Check if docker-compose is available
docker-compose --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker Compose is not available
    echo Please make sure Docker Desktop is properly installed
    echo.
    pause
    exit /b 1
)

echo Starting Redis and Redis Commander...
docker-compose up -d redis redis-commander

if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Failed to start Redis with Docker
    echo Please check Docker is running and try again
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Redis is running on localhost:6379
echo ✅ Redis Commander (Web UI) is available at: http://localhost:8081
echo.
echo To stop Redis: docker-compose down
echo To view logs: docker-compose logs redis
echo.
pause
