#!/bin/bash

# GCX Supplier Application Portal - Test Runner
# ============================================

echo "🚀 GCX Supplier Application Portal - Test Runner"
echo "================================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run: python -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Check if Django server is running
echo "🔍 Checking if Django server is running..."
echo "⚠️  Please ensure Django server is running on http://localhost:8000"
echo "   Start server with: python manage.py runserver"
echo "   Press Enter to continue or Ctrl+C to cancel..."
read

# Run tests
echo ""
echo "🧪 Running tests..."
echo "=================="

# Run simple test first
echo "Running simple test..."
python test_simple.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Simple test passed! Running comprehensive test..."
    echo ""
    python test_application_flow.py
else
    echo ""
    echo "❌ Simple test failed. Please fix issues before running comprehensive test."
    exit 1
fi

echo ""
echo "🎉 Test run completed!"
