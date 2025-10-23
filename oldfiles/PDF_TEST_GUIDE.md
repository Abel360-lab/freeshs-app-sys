# PDF Generation Test Guide

This guide explains how to test the enhanced PDF generation service for supplier applications.

## Test Files Created

### 1. Django Management Command (Recommended)
**File:** `applications/management/commands/test_pdf_simple.py`
**Usage:** `python manage.py test_pdf_simple`

This is the simplest way to test PDF generation with existing application data.

### 2. Comprehensive Test Script
**File:** `test_pdf_generation.py`
**Usage:** `python test_pdf_generation.py`

This script creates test data and performs comprehensive testing.

### 3. Django Shell Test
**File:** `test_pdf_simple.py`
**Usage:** `python manage.py shell < test_pdf_simple.py`

Quick test that can be run from Django shell.

## How to Test PDF Generation

### Method 1: Using Existing Application Data (Easiest)

```bash
# Activate virtual environment
venv\Scripts\activate

# Run the simple test with existing data
python manage.py test_pdf_simple
```

This will:
- Use the first available application in the database
- Generate a PDF for that application
- Validate the PDF format
- Check for key content
- Display file size and path

### Method 2: Create Test Data and Test

```bash
# Activate virtual environment
venv\Scripts\activate

# Run comprehensive test (creates test data)
python test_pdf_generation.py
```

This will:
- Create test application with sample data
- Generate PDF with all sections
- Validate PDF content
- Option to clean up test data

### Method 3: Django Shell Test

```bash
# Activate virtual environment
venv\Scripts\activate

# Run shell test
python manage.py shell < test_pdf_simple.py
```

## Expected Results

When the test runs successfully, you should see:

```
Starting PDF Generation Test
Using application: [TRACKING_CODE]
Company: [COMPANY_NAME]
Testing PDF generation...
PDF generated successfully!
Path: applications/pdfs/supplier_application_[TRACKING_CODE].pdf
File size: [SIZE] bytes
Full path: [FULL_PATH]
PDF format is valid
Found [X]/5 key content items
Found content:
  - SUPPLIER
  - APPLICATION FORM
  - COMPANY DETAILS
  - [COMPANY_NAME]
  - Ghana Commodity Exchange
```

## PDF Content Validation

The test checks for the following key content in the generated PDF:

1. **SUPPLIER** - Main title
2. **APPLICATION FORM** - Subtitle
3. **COMPANY DETAILS** - Section header
4. **Company Name** - Actual company name from application
5. **Ghana Commodity Exchange** - Footer information

## PDF Structure

The enhanced PDF includes these sections:

### Header
- GCX logo (if available)
- "SUPPLIER APPLICATION FORM" title
- Professional horizontal line

### Application Reference
- Tracking code
- Application date
- Current status

### Company Details
- Company name and business type
- Registration and TIN numbers
- Complete address information
- Contact details

### Commodities Section
- Checkbox-style formatting (☑/☐)
- Common commodities: Maize, Soya, Cashew, Sesame, Sorghum, Rice, Shea, Cowpea
- Additional commodities field

### Next of Kin Details
- Complete personal information
- Relationship and contact details
- ID information

### Trading Representatives
- Individual representative details
- Position and experience
- Contact information

### Bank Account Details
- Bank information
- Account details in registered business name

### Document Requirements
- Checklist format with status indicators
- Document type, status, and comments

### Declarations & Compliance
- Rules and regulations agreement
- Professional declaration text
- Signature section

### Footer
- Complete GCX contact details
- Office address and contact numbers
- Generation timestamp

## Troubleshooting

### Common Issues

1. **No applications found**
   - Solution: Create an application first or use `--create-test-data` flag

2. **PDF generation fails**
   - Check Django logs for detailed error messages
   - Ensure all required fields are filled in the application

3. **Content validation fails**
   - This is normal for complex PDFs - the PDF is still valid
   - Check the file size and format validation results

4. **File not found errors**
   - Check that the media directory exists and is writable
   - Ensure proper Django settings for media files

### Debug Mode

To see detailed logging, add this to your Django settings:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'applications.pdf_service': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## Manual PDF Verification

After running the test, you can manually verify the PDF by:

1. **Opening the PDF file** in a PDF viewer
2. **Checking the content** matches the application data
3. **Verifying the formatting** is professional and complete
4. **Testing the download** functionality in the web interface

## File Locations

Generated PDFs are stored in:
- **Relative path:** `applications/pdfs/supplier_application_[TRACKING_CODE].pdf`
- **Full path:** `[MEDIA_ROOT]/applications/pdfs/supplier_application_[TRACKING_CODE].pdf`

## Success Criteria

A successful PDF generation test should show:

✅ **PDF generated successfully**  
✅ **Valid PDF format** (starts with %PDF)  
✅ **Reasonable file size** (typically 50-200KB)  
✅ **File exists and is readable**  
✅ **Contains expected content sections**  

The PDF should be a professional-looking document that matches the GCX Trading Member application format with proper styling, tables, and comprehensive application information.
