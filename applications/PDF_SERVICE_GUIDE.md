# Enhanced PDF Service Guide

## Overview

The enhanced PDF service has been redesigned to match the professional GCX application format from your PHP example. It now includes modern styling, QR codes, document verification, and better layout.

## New Features

### 1. **Professional Header with Logo**
- Logo positioned on the left
- Application details centered
- Clean horizontal separator line

### 2. **Sections with Photos**
- Team member sections can display passport photos on the right side
- Automatic image resizing and aspect ratio preservation
- Professional layout with photos integrated into the section

### 3. **QR Code for Document Verification**
- Automatic QR code generation for each application
- Secure SHA-256 document hash
- Verification URL encoded in QR code
- Document hash stored in application (if field exists)

### 4. **Enhanced Tables**
- Modern table styling with borders
- Header rows with background color
- Better padding and spacing
- Professional appearance

### 5. **Uploaded Documents Status**
- Comprehensive table showing all document types
- Status indicators (✓ Submitted / ✗ Not Submitted)
- Upload dates when available
- Clear visual representation

### 6. **Modern Styling**
- Professional color scheme
- Consistent typography
- Better spacing and layout
- Background colors for section headers

### 7. **Comprehensive Footer**
- System-generated document notice
- Generation timestamp
- Contact information
- Document hash for verification

## Installation

### Step 1: Install Required Packages

```bash
pip install -r requirements.txt
```

This will install:
- `reportlab==4.0.9` - PDF generation library
- `qrcode==7.4.2` - QR code generation

### Step 2: Add Verification Hash Field (Optional)

If you want to store the verification hash in the database, add this field to your `SupplierApplication` model:

```python
# In applications/models.py
class SupplierApplication(models.Model):
    # ... existing fields ...
    
    verification_hash = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="SHA-256 hash for document verification"
    )
```

Then run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 3: Configure Site URL

Add this to your `settings.py`:

```python
# Site URL for QR code generation
SITE_URL = 'https://gcx.com.gh'  # Change to your actual domain
```

### Step 4: Add Logo

Place your logo at:
```
media/logo/logo1.png
```

## Usage

### Generate PDF for an Application

```python
from applications.pdf_service import EnhancedApplicationPDFService

# Create service instance
pdf_service = EnhancedApplicationPDFService()

# Generate PDF
pdf_path = pdf_service.generate_application_pdf(application)

if pdf_path:
    print(f"PDF generated successfully: {pdf_path}")
else:
    print("PDF generation failed")
```

### Generate PDF Response for Download

```python
from applications.pdf_service import generate_application_pdf_response

# In your view
def download_application_pdf(request, application_id):
    application = SupplierApplication.objects.get(id=application_id)
    return generate_application_pdf_response(application)
```

### Example View Integration

```python
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from applications.models import SupplierApplication
from applications.pdf_service import generate_application_pdf_response

@require_http_methods(["GET"])
def download_application_pdf(request, tracking_code):
    """Download PDF for a specific application."""
    application = get_object_or_404(
        SupplierApplication,
        tracking_code=tracking_code
    )
    
    try:
        return generate_application_pdf_response(application)
    except Exception as e:
        return HttpResponse(
            f"Error generating PDF: {str(e)}",
            status=500
        )
```

## Document Verification System

### QR Code Verification

Each PDF includes a QR code that encodes a verification URL:

```
https://gcx.com.gh/verify-document/?id={application_id}&hash={document_hash}
```

### Implementing Verification View

Create a view to verify documents:

```python
import hashlib
from django.shortcuts import render
from django.conf import settings
from applications.models import SupplierApplication

def verify_document(request):
    """Verify a document using QR code scan."""
    application_id = request.GET.get('id')
    provided_hash = request.GET.get('hash')
    
    if not application_id or not provided_hash:
        return render(request, 'verify_document.html', {
            'error': 'Invalid verification parameters'
        })
    
    try:
        application = SupplierApplication.objects.get(id=application_id)
        
        # Generate expected hash
        hash_string = f"{application.id}{application.tracking_code}{application.created_at}{settings.SECRET_KEY}"
        expected_hash = hashlib.sha256(hash_string.encode()).hexdigest()
        
        if provided_hash == expected_hash:
            return render(request, 'verify_document.html', {
                'verified': True,
                'application': application
            })
        else:
            return render(request, 'verify_document.html', {
                'error': 'Document verification failed - hash mismatch'
            })
    
    except SupplierApplication.DoesNotExist:
        return render(request, 'verify_document.html', {
            'error': 'Application not found'
        })
```

## Customization

### Changing Colors

Edit the color definitions in `_create_custom_styles()`:

```python
# Example: Change section header background color
'section_title': ParagraphStyle(
    # ...
    backgroundColor=colors.Color(0.90, 0.95, 1.0),  # Light blue
    # ...
),
```

### Adjusting Margins

Modify the `__init__` method:

```python
def __init__(self):
    self.page_size = A4
    self.margin = 0.75 * inch  # Change this value
    # ...
```

### Adding Custom Sections

Create a new method following this pattern:

```python
def _add_custom_section(self, story, application):
    """Add a custom section."""
    story.append(Paragraph("CUSTOM SECTION", self.styles['section_title']))
    story.append(Spacer(1, 5))
    
    # Add your content here
    story.append(Paragraph("Custom content", self.styles['value']))
    story.append(Spacer(1, 15))
```

Then add it to the `generate_application_pdf` method:

```python
# In generate_application_pdf method
self._add_company_details(story, application)
self._add_custom_section(story, application)  # Add your section
self._add_commodities_section(story, application)
```

### Photo Field Mapping

The service automatically looks for photos in team member records. To use different fields:

```python
# In _add_team_members method
photo_field = getattr(member, 'your_photo_field_name', None)
```

## Comparison with PHP Version

### Similarities
✓ Professional header with logo  
✓ QR code for verification  
✓ Document hash generation  
✓ Comprehensive document status table  
✓ Modern table styling  
✓ Section headers with background colors  
✓ Footer with generation details  

### Improvements
✓ Better error handling and logging  
✓ Automatic image resizing  
✓ More maintainable code structure  
✓ Django-native implementation  
✓ Reusable service class  
✓ Type hints and documentation  

## Troubleshooting

### Logo Not Showing
- Check that `media/logo/logo1.png` exists
- Verify `MEDIA_ROOT` is configured correctly in settings
- Check file permissions

### Photos Not Displaying
- Ensure photo fields have valid image files
- Check that file paths are accessible
- Verify image format is supported (PNG, JPEG, GIF)

### QR Code Not Generating
- Verify `qrcode` package is installed
- Check that `SITE_URL` is configured in settings
- Review logs for specific errors

### PDF Generation Fails
- Check all required packages are installed
- Review Django logs for detailed error messages
- Ensure application has all required relationships loaded

## Performance Considerations

### Large Images
The service automatically resizes images to fit within the PDF. For best performance:
- Keep image files under 2MB
- Use web-optimized formats (JPEG for photos, PNG for graphics)

### Memory Usage
PDF generation uses in-memory buffers. For high-volume applications:
- Consider using Celery for async generation
- Implement caching for frequently accessed PDFs

## Support

For issues or questions:
- Check Django logs: `logs/django.log`
- Review Python logs for PDF generation errors
- Ensure all dependencies are correctly installed

## License

This service is part of the GCX Supplier Application Portal.


