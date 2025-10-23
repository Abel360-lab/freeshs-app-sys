# GCX Supplier Application Portal - Testing Guide

This document provides comprehensive testing instructions for the GCX Supplier Application Portal.

## 🧪 Test Scripts Overview

### 1. `test_simple.py` - Django Test Suite
- **Purpose**: Uses Django's built-in test framework
- **Best for**: Unit testing, database testing, isolated testing
- **Requirements**: Django environment setup
- **Features**:
  - Tests application form page loading
  - Tests application submission with file uploads
  - Tests success page functionality
  - Tests API endpoints (status, outstanding documents)
  - Tests admin functionality
  - Tests database seed data

### 2. `test_application_flow.py` - Comprehensive Integration Test
- **Purpose**: End-to-end testing with real HTTP requests
- **Best for**: Integration testing, user flow testing
- **Requirements**: Running Django server, `requests` library
- **Features**:
  - Tests complete user journey
  - Tests with real HTTP requests
  - Tests file uploads
  - Performance testing
  - Error handling testing

### 3. `test_flow.sh` / `test_flow.bat` - Automated Test Runner
- **Purpose**: Automated test execution with setup
- **Best for**: CI/CD, automated testing
- **Features**:
  - Checks server status
  - Runs migrations
  - Creates superuser
  - Seeds database
  - Runs all test suites
  - Provides colored output

## 🚀 Quick Start Testing

### Prerequisites
1. **Activate virtual environment**:
   ```bash
   # Linux/Mac
   source venv/bin/activate
   
   # Windows
   venv\Scripts\activate
   ```

2. **Start Django server**:
   ```bash
   python manage.py runserver
   ```

3. **Install additional dependencies** (for comprehensive tests):
   ```bash
   pip install requests
   ```

### Running Tests

#### Option 1: Automated Test Runner (Recommended)
```bash
# Linux/Mac
chmod +x test_flow.sh
./test_flow.sh

# Windows
test_flow.bat
```

#### Option 2: Individual Test Scripts
```bash
# Simple Django tests
python test_simple.py

# Comprehensive integration tests
python test_application_flow.py
```

#### Option 3: Django Test Framework
```bash
# Run all Django tests
python manage.py test

# Run specific app tests
python manage.py test applications

# Run with verbose output
python manage.py test applications --verbosity=2
```

## 📋 Test Coverage

### Core Functionality Tests
- ✅ **Application Form Loading**
  - Form renders correctly
  - All steps are present
  - Terms and conditions display
  - Logo loads properly

- ✅ **Application Submission**
  - Form data validation
  - File upload handling
  - Database record creation
  - Tracking code generation
  - Email notification (if configured)

- ✅ **Success Page**
  - Page loads with tracking code
  - Application details display
  - Action buttons work
  - Copy-to-clipboard functionality

- ✅ **API Endpoints**
  - Application status retrieval
  - Outstanding documents listing
  - Document upload functionality
  - Admin endpoints access

- ✅ **Admin Functionality**
  - Admin login
  - Application listing
  - Application review actions
  - Document verification

### Data Validation Tests
- ✅ **Required Fields**
  - Business information validation
  - Contact information validation
  - Commodity selection validation
  - Document upload validation

- ✅ **Field Format Validation**
  - Email format validation
  - Phone number format validation
  - File type validation
  - File size validation

- ✅ **Business Logic Validation**
  - Terms acceptance requirement
  - Declaration agreement requirement
  - Commodity selection requirement
  - Bank account validation

### Error Handling Tests
- ✅ **Form Validation Errors**
  - Missing required fields
  - Invalid field formats
  - File upload errors
  - Terms not accepted

- ✅ **API Error Responses**
  - Invalid tracking codes
  - Missing parameters
  - Authentication errors
  - Server errors

## 🔧 Test Configuration

### Environment Variables
Ensure these are set in your `.env` file:
```env
DEBUG=True
SECRET_KEY=your-secret-key
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
FRONTEND_PUBLIC_URL=http://localhost:8000
```

### Test Data
The test scripts automatically create:
- **Test Regions**: Greater Accra Region
- **Test Commodities**: Rice, Maize
- **Test Document Requirements**: Business Registration, VAT Certificate
- **Test Files**: PDF documents for upload testing
- **Test Applications**: Complete application records

## 📊 Test Results Interpretation

### Success Indicators
- ✅ **All tests pass**: Application is working correctly
- ✅ **Green checkmarks**: Individual test components working
- ✅ **No error messages**: Clean execution
- ✅ **Tracking codes generated**: Database operations successful

### Failure Indicators
- ❌ **Red X marks**: Test failures requiring attention
- ❌ **HTTP error codes**: Server or endpoint issues
- ❌ **Database errors**: Migration or model issues
- ❌ **File upload errors**: Media handling issues

### Common Issues and Solutions

#### 1. Server Not Running
```
❌ Server is not running or not accessible
```
**Solution**: Start Django server with `python manage.py runserver`

#### 2. Database Migration Issues
```
❌ Database migrations failed
```
**Solution**: Run `python manage.py migrate`

#### 3. Missing Dependencies
```
❌ ModuleNotFoundError: No module named 'requests'
```
**Solution**: Install with `pip install requests`

#### 4. File Upload Errors
```
❌ Application submission failed: 400
```
**Solution**: Check file permissions and media directory setup

#### 5. Email Configuration Issues
```
⚠️ Email sending failed
```
**Solution**: Configure email settings in `.env` file

## 🎯 Performance Testing

The comprehensive test script includes performance testing:
- **Response Time Measurement**: Average response times
- **Concurrent Request Testing**: Multiple simultaneous requests
- **Load Testing**: Multiple rapid requests
- **Memory Usage**: Resource consumption monitoring

### Performance Benchmarks
- **Form Loading**: < 2 seconds
- **Application Submission**: < 5 seconds
- **API Responses**: < 1 second
- **File Uploads**: < 10 seconds (depending on file size)

## 🔍 Debugging Tests

### Enable Debug Logging
Add to your `settings.py`:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'logs/django.log',
        },
    },
    'loggers': {
        'applications': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

### Test-Specific Debugging
```bash
# Run with debug output
python test_simple.py --debug

# Run specific test methods
python -m pytest test_simple.py::ApplicationFlowTest::test_application_submission -v
```

## 📈 Continuous Integration

### GitHub Actions Example
```yaml
name: Test GCX Application Portal

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install requests
    
    - name: Run tests
      run: |
        python manage.py migrate
        python manage.py seed_data
        python test_simple.py
        python test_application_flow.py
```

## 📝 Test Reports

### Generating Test Reports
```bash
# Generate HTML coverage report
coverage run --source='.' manage.py test
coverage html

# Generate XML report for CI
python manage.py test --verbosity=2 > test_results.xml
```

### Test Documentation
- **Test Results**: Stored in `test_results/`
- **Coverage Reports**: Generated in `htmlcov/`
- **Log Files**: Available in `logs/django.log`

## 🎉 Success Criteria

A successful test run should show:
- ✅ All form pages load correctly
- ✅ Application submission works end-to-end
- ✅ Success page displays properly
- ✅ API endpoints respond correctly
- ✅ Admin functionality works
- ✅ File uploads process successfully
- ✅ Database operations complete
- ✅ Email notifications sent (if configured)
- ✅ Performance meets benchmarks

## 📞 Support

If you encounter issues with testing:
1. Check the logs in `logs/django.log`
2. Verify all dependencies are installed
3. Ensure the Django server is running
4. Check database migrations are up to date
5. Verify environment variables are set correctly

For additional help, refer to the main README.md file or contact the development team.
