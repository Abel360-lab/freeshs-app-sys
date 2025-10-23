# GCX Supplier Application Portal - Technical Documentation

## Architecture Overview

### Technology Stack
- **Backend**: Django 5.2.6, Django REST Framework, Django Channels
- **Database**: PostgreSQL (production), SQLite (development)
- **Cache**: Redis
- **Web Server**: Nginx + Gunicorn
- **Real-time**: WebSockets (Django Channels)
- **File Storage**: AWS S3 (production), Local (development)
- **Email**: SMTP with customizable backends

### System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (Bootstrap 5) │◄──►│   (Django)      │◄──►│   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx         │    │   Redis Cache   │    │   File Storage  │
│   (Reverse      │    │   (Sessions &   │    │   (S3/Local)    │
│    Proxy)       │    │    Cache)       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Core Components

### Django Apps Structure

#### `accounts/` - User Management
- Custom User model with role-based access
- Authentication views and password management
- User profile management

#### `applications/` - Main Application Logic
- SupplierApplication model and workflow
- Document submission and verification
- Real-time WebSocket consumers
- Background task processing

#### `core/` - Core Models and Services
- Region, Commodity, Warehouse models
- Notification services
- Template management

#### `documents/` - Document Management
- Document upload and verification
- File type validation and security
- Document requirement management

#### `notifications/` - Notification System
- Email template management
- SMS integration (via API)
- Notification logging and tracking

#### `reviews/` - Review Workflow
- Review comments and checklist
- Decision tracking and audit

## Database Schema

### Key Models

#### User Model
```python
class User(AbstractUser):
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    must_change_password = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=20, blank=True)
```

#### SupplierApplication Model
```python
class SupplierApplication(models.Model):
    tracking_code = models.CharField(max_length=20, unique=True)
    business_name = models.CharField(max_length=200)
    email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    user = models.ForeignKey(User, null=True, blank=True)
    # ... other fields
```

#### DocumentUpload Model
```python
class DocumentUpload(models.Model):
    application = models.ForeignKey(SupplierApplication)
    requirement = models.ForeignKey(DocumentRequirement)
    file = models.FileField(upload_to='documents/')
    verified = models.BooleanField(default=False)
    verifier_note = models.TextField(blank=True)
```

## API Architecture

### RESTful Endpoints

#### Public API
- `POST /api/applications/submit/` - Submit application
- `GET /api/applications/{tracking_code}/status/` - Check status
- `POST /api/applications/{tracking_code}/upload/` - Upload documents

#### Admin API
- `GET /api/admin/applications/` - List applications
- `POST /api/admin/applications/{id}/approve/` - Approve application
- `POST /api/admin/documents/{id}/verify/` - Verify document

### WebSocket Events
- `application_updated` - Status changes
- `new_application` - New submissions
- `document_uploaded` - Document events

## Security Implementation

### Authentication & Authorization
- Role-based access control (ADMIN, REVIEWER, SUPPLIER)
- Session-based authentication with CSRF protection
- Password complexity requirements
- Account lockout after failed attempts

### Data Protection
- File type validation and virus scanning
- SQL injection prevention via Django ORM
- XSS protection with template escaping
- CSRF tokens on all forms

### File Security
- Secure file upload with type validation
- File size limits (10MB max)
- Virus scanning integration
- Secure file serving

## Multi-language Implementation

### Django i18n Setup
```python
# settings.py
USE_I18N = True
USE_L10N = True
LANGUAGE_CODE = 'en'
LANGUAGES = [
    ('en', _('English')),
    ('ak', _('Akan')),
    # ... other languages
]
```

### URL Internationalization
```python
# urls.py
urlpatterns = i18n_patterns(
    path('', include('applications.urls')),
    # ... other patterns
    prefix_default_language=False
)
```

### Template Translation
```html
{% load i18n %}
{% trans "Welcome to GCX Portal" %}
```

## Theme System Architecture

### CSS Variable System
```css
:root {
    --bg-primary: #ffffff;
    --text-primary: #2c3e50;
    /* ... other variables */
}

[data-theme="dark"] {
    --bg-primary: #1a1a1a;
    --text-primary: #ffffff;
    /* ... dark theme variables */
}
```

### JavaScript Theme Management
```javascript
function setTheme(mode) {
    document.documentElement.dataset.theme = mode;
    localStorage.setItem("theme", mode);
}
```

## Real-time Features

### WebSocket Implementation
```python
# consumers.py
class ApplicationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("admin_updates", self.channel_name)
    
    async def application_updated(self, event):
        await self.send(text_data=json.dumps(event))
```

### Frontend WebSocket Client
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/admin/');
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    updateDashboard(data);
};
```

## Performance Optimization

### Database Optimization
- Connection pooling with `CONN_MAX_AGE`
- Database indexing on frequently queried fields
- Query optimization with `select_related` and `prefetch_related`

### Caching Strategy
- Redis for session storage and caching
- Template fragment caching
- Static file caching with long expiration

### Frontend Optimization
- Minified CSS and JavaScript
- Image optimization and lazy loading
- CDN integration for static assets

## Deployment Architecture

### Production Stack
```
Internet → Nginx → Gunicorn → Django → PostgreSQL
                ↓
            Redis Cache
                ↓
            AWS S3 Storage
```

### Environment Configuration
```python
# Production settings
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com']
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
```

## Monitoring & Logging

### Application Logging
```python
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/gcx-portal/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```

### Health Checks
- Database connectivity monitoring
- Redis cache status
- File storage accessibility
- External API availability

## Testing Strategy

### Test Types
- Unit tests for models and views
- Integration tests for API endpoints
- Frontend tests with Selenium
- Load testing for performance

### Test Configuration
```python
# settings/test.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
```

## Backup & Recovery

### Database Backups
```bash
# Daily automated backup
pg_dump gcx_portal | gzip > backup_$(date +%Y%m%d).sql.gz
```

### File Backups
```bash
# Media files backup
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/
```

## Development Workflow

### Local Development
```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Code Quality
- Black for code formatting
- Flake8 for linting
- Pre-commit hooks
- Automated testing in CI/CD

## API Documentation

### Authentication
- Session-based for web interface
- Token-based for API access
- OAuth2 for third-party integrations

### Rate Limiting
- 100 requests/hour for public endpoints
- 1000 requests/hour for authenticated users
- File upload limits: 10 uploads/hour

### Error Handling
```json
{
    "error": "Validation failed",
    "details": {
        "email": ["Enter a valid email address."]
    },
    "code": "VALIDATION_ERROR"
}
```

This technical documentation provides developers with comprehensive information about the system architecture, implementation details, and best practices for maintaining and extending the GCX Supplier Application Portal.
