# Quick Start Guide - Enhanced PDF Service

## 🚀 Quick Installation (5 minutes)

### 1. Install Dependencies

```bash
pip install reportlab==4.0.9 qrcode==7.4.2
```

### 2. Add Configuration to settings.py

```python
# Add to your settings.py
SITE_URL = 'https://gcx.com.gh'  # Your domain
```

### 3. Add Logo (Optional)

Place your logo at: `media/logo/logo1.png`

### 4. Ready to Use!

```python
from applications.pdf_service import EnhancedApplicationPDFService

# Generate PDF
pdf_service = EnhancedApplicationPDFService()
pdf_path = pdf_service.generate_application_pdf(application)
```

## 📋 Key Features Comparison

| Feature | PHP Version | Django Version |
|---------|------------|----------------|
| Professional Header | ✅ | ✅ |
| Logo Integration | ✅ | ✅ |
| QR Code Verification | ✅ | ✅ |
| Document Hash | ✅ | ✅ |
| Photos in Sections | ✅ | ✅ |
| Document Status Table | ✅ | ✅ |
| Modern Table Styling | ✅ | ✅ |
| Section Backgrounds | ✅ | ✅ |
| Signatures | ✅ | ✅ |
| Footer Information | ✅ | ✅ |

## 🎨 Visual Features

### Header
- Logo on the left (100x60)
- Application ID, Status, Date in center
- Clean separator line

### Sections
- Gray background headers (#f0f0f0)
- Bold section titles (11pt)
- Consistent spacing

### Tables
- Header row with light gray background (#f5f5f5)
- Border color: #dddddd
- 6px padding
- 9pt font size

### Photos
- Auto-resize to fit (max 100x120)
- Positioned on right side of sections
- Maintains aspect ratio

### QR Code
- 1.5 inch square
- High error correction
- Centered with label

## 📝 Example Usage

### Basic PDF Generation

```python
from applications.models import SupplierApplication
from applications.pdf_service import EnhancedApplicationPDFService

# Get your application
application = SupplierApplication.objects.get(tracking_code='GCX-2025-001')

# Generate PDF
service = EnhancedApplicationPDFService()
pdf_path = service.generate_application_pdf(application)

print(f"PDF saved to: {pdf_path}")
```

### Download View

```python
# In views.py
from django.shortcuts import get_object_or_404
from applications.models import SupplierApplication
from applications.pdf_service import generate_application_pdf_response

def download_pdf(request, tracking_code):
    application = get_object_or_404(SupplierApplication, tracking_code=tracking_code)
    return generate_application_pdf_response(application)
```

### URL Configuration

```python
# In urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('applications/<str:tracking_code>/pdf/', views.download_pdf, name='download_pdf'),
]
```

## 🔐 Document Verification

### Add Verification View

```python
# In views.py
import hashlib
from django.shortcuts import render
from django.conf import settings

def verify_document(request):
    app_id = request.GET.get('id')
    provided_hash = request.GET.get('hash')
    
    try:
        application = SupplierApplication.objects.get(id=app_id)
        hash_string = f"{application.id}{application.tracking_code}{application.created_at}{settings.SECRET_KEY}"
        expected_hash = hashlib.sha256(hash_string.encode()).hexdigest()
        
        if provided_hash == expected_hash:
            return render(request, 'verify_success.html', {'application': application})
        else:
            return render(request, 'verify_error.html', {'error': 'Invalid hash'})
    except:
        return render(request, 'verify_error.html', {'error': 'Not found'})
```

### Add URL

```python
path('verify-document/', views.verify_document, name='verify_document'),
```

## 🎯 What's Included in the PDF

1. **Header Section**
   - Logo
   - Application ID
   - Status
   - Submission date

2. **Company Details**
   - Business information
   - Contact details
   - Registration numbers

3. **Commodities**
   - Selected commodities with checkmarks
   - Additional commodities

4. **Next of Kin**
   - Full details for all kin entries

5. **Team Members**
   - Representative information
   - Photos (if available)

6. **Bank Details**
   - All bank accounts

7. **Uploaded Documents**
   - Status table
   - Upload dates
   - Submission status

8. **Declarations**
   - Rules agreement
   - Declaration text
   - Signature details

9. **Verification**
   - QR code
   - Document hash

10. **Footer**
    - Generation details
    - Contact information

## 🔧 Common Customizations

### Change Header Color

```python
# In pdf_service.py, _add_header method
story.append(HRFlowable(width="100%", thickness=2, color=colors.blue))
```

### Change Section Background

```python
# In _create_custom_styles
'section_title': ParagraphStyle(
    # ...
    backgroundColor=colors.Color(0.85, 0.92, 1.0),  # Light blue
    # ...
),
```

### Add Custom Field

```python
# In _add_company_details
data = [
    ('Company Name:', application.business_name),
    ('Custom Field:', application.your_custom_field),  # Add here
    # ...
]
```

## ✅ Testing

### Test PDF Generation

```python
# In Django shell
python manage.py shell

from applications.models import SupplierApplication
from applications.pdf_service import EnhancedApplicationPDFService

# Get first application
app = SupplierApplication.objects.first()

# Generate PDF
service = EnhancedApplicationPDFService()
result = service.generate_application_pdf(app)

print(f"Success: {result is not None}")
print(f"PDF Path: {result}")
```

### Test QR Code

1. Generate a PDF
2. Open the PDF
3. Scan QR code with phone
4. Should redirect to verification URL

## 📊 Performance

- **Generation Time**: ~1-2 seconds per PDF
- **File Size**: ~200-500 KB (depends on images)
- **Memory Usage**: ~10-20 MB during generation

## 🐛 Troubleshooting

### "Cannot import reportlab"
```bash
pip install reportlab==4.0.9
```

### "Cannot import qrcode"
```bash
pip install qrcode==7.4.2
```

### Logo not showing
- Check path: `media/logo/logo1.png`
- Verify MEDIA_ROOT in settings
- Check file exists

### Photos not displaying
- Verify image file exists
- Check file field has value
- Ensure image format is supported

### QR code not working
- Add SITE_URL to settings
- Check URL is accessible
- Verify hash generation

## 📚 Next Steps

1. ✅ Install packages
2. ✅ Configure settings
3. ✅ Add logo
4. ✅ Test generation
5. ✅ Add verification view
6. ✅ Test QR code
7. ✅ Customize styling (optional)

## 💡 Tips

- Cache generated PDFs for better performance
- Use Celery for async generation
- Compress images before upload
- Test with sample data first
- Review PDF_SERVICE_GUIDE.md for advanced features

## 🎓 Full Documentation

See `PDF_SERVICE_GUIDE.md` for comprehensive documentation including:
- Detailed feature explanations
- Advanced customization
- Performance optimization
- Security considerations
- API reference

---

**Need Help?** Check the logs at `logs/django.log` for detailed error messages.


