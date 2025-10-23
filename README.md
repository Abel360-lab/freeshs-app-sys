# GCX Supplier Application Portal

A comprehensive, production-ready Django application for managing supplier applications to the Ghana Commodity Exchange (GCX). This portal provides a complete ecosystem for application submission, review, and management with advanced features including multi-language support, theme customization, real-time updates, and comprehensive admin tools.

## Features

### For Applicants (Public)
- **Multi-step Application Form**: Intuitive 6-step wizard with real-time validation
- **No Login Required**: Submit applications without creating accounts
- **Multi-language Support**: Available in 16+ languages including Ghanaian languages
- **Theme Customization**: Light/Dark/Auto theme modes with independent settings
- **Document Upload**: Upload required documents with drag-and-drop interface
- **Status Tracking**: Real-time application status updates using tracking codes
- **Mobile Responsive**: Optimized for all device sizes with touch-friendly interface
- **Background Images**: Professional commodity-themed backgrounds
- **Real-time Validation**: Instant feedback on form fields and document requirements

### For Administrators
- **Professional Backoffice Portal** (`/backoffice/`) - Modern, responsive admin interface
- **Real-time Dashboard**: Live statistics, charts, and application metrics
- **Advanced Search & Filtering**: Real-time search with instant results
- **Document Management**: Upload, verify, and manage application documents
- **Application Workflow**: Complete review process with status management
- **One-click Actions**: Approve, reject, request documents, activate accounts
- **Notification System**: Automated email notifications with customizable templates
- **Audit Logging**: Comprehensive tracking of all admin actions
- **Multi-language Admin**: Admin interface supports multiple languages
- **Theme Customization**: Independent theme settings for admin portal
- **WebSocket Integration**: Real-time updates across all admin interfaces
- **Export & Reporting**: PDF generation and data export capabilities

### For Approved Suppliers
- **Automatic Account Creation**: User accounts created upon application approval
- **Supplier Portal Access**: Dedicated dashboard for approved suppliers
- **Application History**: View all submitted applications and their status
- **Document Management**: Access to uploaded documents and verification status
- **Profile Management**: Update personal and business information
- **Password Management**: Secure password change functionality
- **Multi-language Support**: Supplier portal available in multiple languages

## Technology Stack

- **Backend**: Django 5.2.6, Django REST Framework
- **Database**: SQLite (development), PostgreSQL-ready (production)
- **Frontend**: Bootstrap 5, HTML5, JavaScript, ApexCharts
- **Real-time**: WebSockets (Django Channels), Redis
- **File Storage**: Local (development), S3-ready (production)
- **Email**: SMTP with configurable backend
- **Authentication**: Custom User model with role-based access

## Latest Features & Improvements

### ✅ Multi-language Support (i18n)
- **16+ Languages**: English, Ghanaian languages (Akan, Ewe, Ga, Hausa, Twi), and international languages
- **Dynamic Language Switching**: Seamless language switching with URL prefix handling
- **Independent Language Settings**: Separate language preferences for different user types
- **Translation Management**: Django's built-in translation system with gettext support

### ✅ Advanced Theme System
- **Three-Mode Themes**: Auto (system preference), Light, and Dark modes
- **Independent Theme Storage**: Separate theme preferences for application form and backoffice
- **Django Admin-Style Toggle**: Professional theme switching with SVG icons
- **System Integration**: Auto mode respects OS theme preferences

### ✅ Enhanced User Experience
- **Professional UI**: Modern, responsive design with Bootstrap 5
- **Commodity Images**: Visual commodity selection with image cards
- **Background Themes**: Professional commodity-themed backgrounds
- **Mobile Optimization**: Touch-friendly interface with responsive breakpoints
- **Toast Notifications**: Modern notification system for user feedback

### ✅ Comprehensive Admin Tools
- **Advanced Application Management**: Complete workflow with timeline tracking
- **Document Verification System**: Upload, view, and verify documents with notes
- **Notification Templates**: Customizable email templates for all scenarios
- **Audit Logging**: Complete tracking of all admin actions and changes
- **Real-time Updates**: WebSocket-powered live updates across all interfaces

### ✅ Simplified Status System
- Streamlined from 8+ statuses to 4 clear statuses
- Automatic status transitions based on admin actions
- Cleaner workflow and better user experience

### ✅ Real-time Features
- Live dashboard updates via WebSockets
- Real-time search and filtering (no trigger button needed)
- Instant status updates across all admin interfaces

## Project Structure

```
freeshs_app_sys/
├── accounts/                 # Custom User model and authentication
├── applications/             # Main application models and views
├── core/                    # Core models (regions, commodities, warehouses)
├── documents/               # Document management and verification
├── notifications/           # Email and SMS notifications
├── reviews/                 # Review workflow and comments
├── mysite/                  # Django project settings
├── templates/               # HTML templates
├── static/                  # Static files (CSS, JS, images)
├── media/                   # Uploaded files
└── logs/                    # Application logs
```

## Installation & Setup

### Prerequisites

- Python 3.11+
- Virtual environment (recommended)
- Git

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd freeshs_app_sys

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=true
ALLOWED_HOSTS=*
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_PORT=587
EMAIL_USE_TLS=true
NOTIFICATION_API_BASE_URL=http://dev.gcx.com.gh/notification-api/public/
FRONTEND_PUBLIC_URL=http://localhost:8000
```

### 3. Database Setup

```bash
# Run migrations
python manage.py migrate

# Seed initial data (regions, commodities, document requirements)
python manage.py seed_data
```

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

Or use the seeded admin account:
- Email: admin@gcx.com.gh
- Password: admin123

### 5. Run Development Server

```bash
python manage.py runserver
```

The application will be available at:
- **Application Form**: http://localhost:8000/apply/
- **Backoffice Portal**: http://localhost:8000/backoffice/ (Admin interface)
- **Django Admin**: http://localhost:8000/admin/ (Legacy admin)
- **API Documentation**: http://localhost:8000/api/

## API Endpoints

### Public Endpoints (No Authentication Required)

- `POST /api/applications/submit/` - Submit new application
- `GET /api/applications/{tracking_code}/status/` - Check application status
- `GET /api/applications/{tracking_code}/outstanding/` - Get outstanding documents
- `POST /api/applications/{tracking_code}/outstanding/upload/` - Upload documents

### Admin Endpoints (Authentication Required)

- `GET /api/admin/applications/` - List applications
- `GET /api/admin/applications/{id}/` - Get application details
- `POST /api/admin/applications/{id}/request-more-docs/` - Request more documents
- `POST /api/admin/applications/{id}/approve/` - Approve application
- `POST /api/admin/applications/{id}/reject/` - Reject application
- `POST /api/admin/documents/{id}/verify/` - Verify document

## Application Workflow

### 1. Application Submission
1. Applicant visits `/apply/`
2. Fills out multi-step form with:
   - Business information
   - Commodities to supply
   - Team member details
   - Next of kin information
   - Bank account details
   - Declaration and signature
3. System generates tracking code
4. Application status: **PENDING_REVIEW**
5. Confirmation email sent

### 2. Admin Review Process
1. Admin opens application → Status changes to **UNDER_REVIEW**
2. Admin reviews application details
3. Admin verifies uploaded documents
4. Admin can request additional documents (status remains **UNDER_REVIEW**)
5. Admin makes approval/rejection decision

### 3. Final Decision
- **APPROVED**: All documents verified, supplier account created, credentials emailed
- **REJECTED**: Application declined with reason

## Application Status System

The system uses a simplified 4-status workflow:

1. **PENDING_REVIEW** - Newly submitted applications (default status)
2. **UNDER_REVIEW** - Admin has opened the application or requested documents
3. **APPROVED** - Application approved, supplier account created
4. **REJECTED** - Application rejected

### Status Transitions
- **New Application** → `PENDING_REVIEW`
- **Admin Opens Application** → `UNDER_REVIEW`
- **Admin Requests Documents** → `UNDER_REVIEW` (remains)
- **Admin Approves** → `APPROVED`
- **Admin Rejects** → `REJECTED`

## Data Models

### Core Models
- **User**: Custom user model with roles (ADMIN, REVIEWER, SUPPLIER)
- **Region**: Ghana regions lookup
- **Commodity**: Commodities that can be supplied
- **Warehouse**: Warehouse locations

### Application Models
- **SupplierApplication**: Main application model
- **TeamMember**: Team member with experience
- **NextOfKin**: Next of kin information
- **BankAccount**: Bank account details

### Document Models
- **DocumentRequirement**: Required document types
- **DocumentUpload**: Uploaded documents
- **OutstandingDocumentRequest**: Requests for additional docs

### Review Models
- **ReviewComment**: Review comments
- **ReviewChecklist**: Review checklist
- **ReviewDecision**: Final review decisions

## Security Features

- Role-based access control
- File type validation
- File size limits (10MB)
- Phone number validation (Ghana format)
- Email uniqueness validation
- Signed tokens for document uploads
- Audit logging for admin actions

## Production Deployment

### Database
Update `DATABASES` in `settings.py` for PostgreSQL:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gcx_portal',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### File Storage
Configure S3 for production:

```python
# Add to settings.py
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = 'your-access-key'
AWS_SECRET_ACCESS_KEY = 'your-secret-key'
AWS_STORAGE_BUCKET_NAME = 'your-bucket-name'
AWS_S3_REGION_NAME = 'your-region'
```

### Environment Variables
Set production environment variables:
- `DEBUG=False`
- `SECRET_KEY=your-production-secret-key`
- `ALLOWED_HOSTS=your-domain.com`
- Database credentials
- Email credentials
- S3 credentials

## Testing

```bash
# Run tests
python manage.py test

# Run specific app tests
python manage.py test applications
python manage.py test documents
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please contact the development team or create an issue in the repository.
