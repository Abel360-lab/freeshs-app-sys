@echo off
REM GCX Supplier Application Portal - Test Runner (Windows)
REM =====================================================

echo 🚀 GCX Supplier Application Portal - Test Runner
echo ================================================

REM Check if virtual environment exists
if not exist "venv" (
    echo ❌ Virtual environment not found. Please run: python -m venv venv
    pause
    exit /b 1
)

REM Activate virtual environment
echo 📦 Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if Django server is running
echo 🔍 Checking if Django server is running...
echo ⚠️  Please ensure Django server is running on http://localhost:8000
echo    Start server with: python manage.py runserver
echo    Press any key to continue...
pause >nul

REM Run tests
echo.
echo 🧪 Running tests...
echo ==================

REM Run simple test first
echo Running simple test...
python test_simple.py

if %errorlevel% equ 0 (
    echo.
    echo ✅ Simple test passed! Running comprehensive test...
    echo.
    python test_application_flow.py
) else (
    echo.
    echo ❌ Simple test failed. Please fix issues before running comprehensive test.
    pause
    exit /b 1
)

echo.
echo 🎉 Test run completed!
pause
