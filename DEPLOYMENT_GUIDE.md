# GCX Supplier Application Portal - Deployment Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Configuration](#database-configuration)
4. [File Storage Configuration](#file-storage-configuration)
5. [Email Configuration](#email-configuration)
6. [Web Server Configuration](#web-server-configuration)
7. [SSL/HTTPS Setup](#sslhttps-setup)
8. [Monitoring & Logging](#monitoring--logging)
9. [Backup Strategy](#backup-strategy)
10. [Performance Optimization](#performance-optimization)
11. [Security Hardening](#security-hardening)
12. [Docker Deployment](#docker-deployment)
13. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Ubuntu 20.04+ / CentOS 8+ / Windows Server 2019+
- **Python**: 3.11+
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: Minimum 20GB free space (100GB recommended for production)
- **CPU**: 2+ cores recommended

### Software Dependencies

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
sudo apt install -y postgresql postgresql-contrib
sudo apt install -y nginx redis-server
sudo apt install -y git curl wget

# CentOS/RHEL
sudo yum install -y python3.11 python3.11-devel
sudo yum install -y postgresql postgresql-server postgresql-contrib
sudo yum install -y nginx redis
sudo yum install -y git curl wget
```

## Environment Setup

### 1. Create Application User

```bash
# Create dedicated user for the application
sudo useradd -m -s /bin/bash gcx
sudo usermod -aG sudo gcx

# Switch to application user
sudo su - gcx
```

### 2. Clone Repository

```bash
# Clone the repository
git clone <repository-url> /home/gcx/gcx-portal
cd /home/gcx/gcx-portal

# Set proper permissions
chmod +x manage.py
```

### 3. Create Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 4. Environment Configuration

Create production environment file:

```bash
# Create .env file
cat > .env << EOF
# Django Settings
SECRET_KEY=your-super-secret-key-here-make-it-long-and-random
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,localhost

# Database
DATABASE_URL=postgresql://gcx_user:secure_password@localhost:5432/gcx_portal

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_PORT=587
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@your-domain.com

# File Storage
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Notification API
NOTIFICATION_API_BASE_URL=https://api.gcx.com.gh/notification-api/public/
FRONTEND_PUBLIC_URL=https://your-domain.com

# Security
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_BROWSER_XSS_FILTER=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Logging
LOG_LEVEL=INFO
LOG_FILE=/home/gcx/gcx-portal/logs/django.log
EOF

# Set proper permissions
chmod 600 .env
```

## Database Configuration

### PostgreSQL Setup

```bash
# Install PostgreSQL (if not already installed)
sudo apt install -y postgresql postgresql-contrib

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE gcx_portal;
CREATE USER gcx_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE gcx_portal TO gcx_user;
ALTER USER gcx_user CREATEDB;
\q
EOF

# Test database connection
psql -h localhost -U gcx_user -d gcx_portal -c "SELECT version();"
```

### Django Database Setup

```bash
# Activate virtual environment
source venv/bin/activate

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Seed initial data
python manage.py seed_data

# Collect static files
python manage.py collectstatic --noinput
```

## File Storage Configuration

### Option 1: Local Storage (Development)

```python
# In settings.py
MEDIA_ROOT = '/home/gcx/gcx-portal/media'
MEDIA_URL = '/media/'
```

### Option 2: AWS S3 (Production)

```python
# In settings.py
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME')
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_DEFAULT_ACL = 'public-read'
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
```

## Email Configuration

### Gmail SMTP Setup

```bash
# Enable 2-factor authentication on Gmail
# Generate app-specific password
# Use app password in EMAIL_HOST_PASSWORD
```

### Custom SMTP Server

```python
# In .env
EMAIL_HOST=mail.your-domain.com
EMAIL_HOST_USER=noreply@your-domain.com
EMAIL_HOST_PASSWORD=your-smtp-password
EMAIL_PORT=587
EMAIL_USE_TLS=True
```

### Email Testing

```bash
# Test email configuration
python manage.py shell << EOF
from django.core.mail import send_mail
from django.conf import settings

try:
    send_mail(
        'Test Email',
        'This is a test email from GCX Portal.',
        settings.DEFAULT_FROM_EMAIL,
        ['test@example.com'],
        fail_silently=False,
    )
    print("Email sent successfully!")
except Exception as e:
    print(f"Email failed: {e}")
EOF
```

## Web Server Configuration

### Nginx Configuration

```bash
# Create Nginx configuration
sudo tee /etc/nginx/sites-available/gcx-portal << EOF
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # File upload size
    client_max_body_size 100M;
    
    # Static files
    location /static/ {
        alias /home/gcx/gcx-portal/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /home/gcx/gcx-portal/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }
    
    # WebSocket support
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/gcx-portal /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Gunicorn Configuration

```bash
# Install Gunicorn
pip install gunicorn

# Create Gunicorn configuration
cat > gunicorn.conf.py << EOF
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
user = "gcx"
group = "gcx"
tmp_upload_dir = None
forwarded_allow_ips = "*"
secure_scheme_headers = {'X-FORWARDED-PROTO': 'https'}
EOF
```

### Systemd Service

```bash
# Create systemd service
sudo tee /etc/systemd/system/gcx-portal.service << EOF
[Unit]
Description=GCX Supplier Portal
After=network.target

[Service]
Type=exec
User=gcx
Group=gcx
WorkingDirectory=/home/gcx/gcx-portal
Environment=PATH=/home/gcx/gcx-portal/venv/bin
ExecStart=/home/gcx/gcx-portal/venv/bin/gunicorn --config gunicorn.conf.py mysite.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable gcx-portal
sudo systemctl start gcx-portal
sudo systemctl status gcx-portal
```

## SSL/HTTPS Setup

### Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run

# Setup auto-renewal cron job
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

### Custom SSL Certificate

```bash
# Place certificate files
sudo cp your-domain.crt /etc/ssl/certs/
sudo cp your-domain.key /etc/ssl/private/
sudo chmod 600 /etc/ssl/private/your-domain.key
```

## Monitoring & Logging

### Log Configuration

```python
# In settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/home/gcx/gcx-portal/logs/django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'applications': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### Log Rotation

```bash
# Configure logrotate
sudo tee /etc/logrotate.d/gcx-portal << EOF
/home/gcx/gcx-portal/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 gcx gcx
    postrotate
        systemctl reload gcx-portal
    endscript
}
EOF
```

### Monitoring with Prometheus

```bash
# Install Prometheus Node Exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz
tar xvfz node_exporter-1.6.1.linux-amd64.tar.gz
sudo mv node_exporter-1.6.1.linux-amd64/node_exporter /usr/local/bin/
sudo useradd --no-create-home --shell /bin/false node_exporter
sudo chown node_exporter:node_exporter /usr/local/bin/node_exporter

# Create systemd service for node_exporter
sudo tee /etc/systemd/system/node_exporter.service << EOF
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable node_exporter
sudo systemctl start node_exporter
```

## Backup Strategy

### Database Backup

```bash
# Create backup script
cat > /home/gcx/backup_db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/gcx/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="gcx_portal"
DB_USER="gcx_user"

mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h localhost -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/gcx_portal_$DATE.sql.gz

# Keep only last 30 days of backups
find $BACKUP_DIR -name "gcx_portal_*.sql.gz" -mtime +30 -delete

echo "Database backup completed: gcx_portal_$DATE.sql.gz"
EOF

chmod +x /home/gcx/backup_db.sh

# Setup daily backup cron job
echo "0 2 * * * /home/gcx/backup_db.sh" | crontab -
```

### File Backup

```bash
# Create file backup script
cat > /home/gcx/backup_files.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/gcx/backups"
DATE=$(date +%Y%m%d_%H%M%S)
SOURCE_DIR="/home/gcx/gcx-portal/media"

mkdir -p $BACKUP_DIR

# Media files backup
tar -czf $BACKUP_DIR/media_files_$DATE.tar.gz -C $SOURCE_DIR .

# Keep only last 7 days of backups
find $BACKUP_DIR -name "media_files_*.tar.gz" -mtime +7 -delete

echo "Files backup completed: media_files_$DATE.tar.gz"
EOF

chmod +x /home/gcx/backup_files.sh

# Setup daily backup cron job
echo "0 3 * * * /home/gcx/backup_files.sh" | crontab -
```

## Performance Optimization

### Redis Configuration

```bash
# Configure Redis
sudo tee -a /etc/redis/redis.conf << EOF
# Performance optimizations
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
EOF

sudo systemctl restart redis-server
```

### PostgreSQL Optimization

```bash
# Optimize PostgreSQL
sudo -u postgres psql -c "ALTER SYSTEM SET shared_buffers = '256MB';"
sudo -u postgres psql -c "ALTER SYSTEM SET effective_cache_size = '1GB';"
sudo -u postgres psql -c "ALTER SYSTEM SET maintenance_work_mem = '64MB';"
sudo -u postgres psql -c "ALTER SYSTEM SET checkpoint_completion_target = 0.9;"
sudo -u postgres psql -c "ALTER SYSTEM SET wal_buffers = '16MB';"
sudo -u postgres psql -c "ALTER SYSTEM SET default_statistics_target = 100;"
sudo -u postgres psql -c "SELECT pg_reload_conf();"
```

### Django Performance Settings

```python
# In settings.py
# Database connection pooling
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gcx_portal',
        'USER': 'gcx_user',
        'PASSWORD': 'secure_password',
        'HOST': 'localhost',
        'PORT': '5432',
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'MAX_CONNS': 20,
        },
    }
}

# Caching
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

## Security Hardening

### Firewall Configuration

```bash
# Configure UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### SSH Hardening

```bash
# Edit SSH configuration
sudo tee -a /etc/ssh/sshd_config << EOF
# Security hardening
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
EOF

sudo systemctl restart ssh
```

### Django Security Settings

```python
# In settings.py
# Security middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "mysite.wsgi:application"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      POSTGRES_DB: gcx_portal
      POSTGRES_USER: gcx_user
      POSTGRES_PASSWORD: secure_password
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    build: .
    command: gunicorn --bind 0.0.0.0:8000 mysite.wsgi:application
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://gcx_user:secure_password@db:5432/gcx_portal
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - ./ssl:/etc/ssl/certs
    depends_on:
      - web

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Error

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database exists
sudo -u postgres psql -c "\l"

# Test connection
psql -h localhost -U gcx_user -d gcx_portal -c "SELECT version();"
```

#### 2. Permission Denied Errors

```bash
# Fix file permissions
sudo chown -R gcx:gcx /home/gcx/gcx-portal
sudo chmod -R 755 /home/gcx/gcx-portal
sudo chmod 600 /home/gcx/gcx-portal/.env
```

#### 3. Static Files Not Loading

```bash
# Collect static files
source venv/bin/activate
python manage.py collectstatic --noinput

# Check Nginx configuration
sudo nginx -t
sudo systemctl reload nginx
```

#### 4. Email Not Sending

```bash
# Test email configuration
python manage.py shell << EOF
from django.core.mail import send_mail
from django.conf import settings
print(f"Email host: {settings.EMAIL_HOST}")
print(f"Email port: {settings.EMAIL_PORT}")
print(f"Email use TLS: {settings.EMAIL_USE_TLS}")
EOF
```

#### 5. WebSocket Connection Issues

```bash
# Check WebSocket configuration in Nginx
sudo nginx -t

# Check Django Channels
pip install channels
pip install channels-redis
```

### Log Analysis

```bash
# Check application logs
tail -f /home/gcx/gcx-portal/logs/django.log

# Check Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Check system logs
sudo journalctl -u gcx-portal -f
```

### Performance Monitoring

```bash
# Monitor system resources
htop
iostat -x 1
netstat -tulpn

# Monitor database connections
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Monitor Redis
redis-cli info memory
redis-cli info clients
```

### Health Checks

```bash
# Application health check
curl -f http://localhost:8000/health/ || echo "Application is down"

# Database health check
python manage.py check --database default

# Redis health check
redis-cli ping
```

## Maintenance

### Regular Maintenance Tasks

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python packages
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Run Django maintenance commands
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py clearsessions

# Clean up old logs
find /home/gcx/gcx-portal/logs -name "*.log" -mtime +30 -delete
```

### Monitoring Scripts

```bash
# Create health check script
cat > /home/gcx/health_check.sh << 'EOF'
#!/bin/bash

# Check if application is running
if ! curl -f http://localhost:8000/health/ > /dev/null 2>&1; then
    echo "Application is down, restarting..."
    sudo systemctl restart gcx-portal
fi

# Check database connection
if ! python manage.py check --database default > /dev/null 2>&1; then
    echo "Database connection failed"
    exit 1
fi

# Check Redis connection
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Redis connection failed"
    exit 1
fi

echo "All services are healthy"
EOF

chmod +x /home/gcx/health_check.sh

# Setup health check cron job
echo "*/5 * * * * /home/gcx/health_check.sh" | crontab -
```

## Recent Updates and Fixes

### Static and Media Files Serving (Fixed)

**Issue**: Static files (CSS/JS) and media files (images) were not loading when `DEBUG=False`.

**Solution**: 
1. **WhiteNoise Integration**: Added WhiteNoise middleware for static file serving with ASGI/Daphne
2. **Media File Serving**: Implemented proper media file serving using Django's `serve` view for production
3. **DEBUG Configuration**: Fixed DEBUG parsing to properly read from environment variables

**Configuration Changes**:
```python
# mysite/settings.py
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Added
    # ... other middleware
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# mysite/urls.py
# Added media file serving for production
urlpatterns += [
    path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
]
```

### WebSocket/Redis Connection Issues (Fixed)

**Issue**: WebSocket connections were failing due to Redis connection problems.

**Solution**: 
1. **In-Memory Channel Layer**: Temporarily switched to in-memory channel layer for WebSocket functionality
2. **Redis Configuration**: Updated Redis settings for better compatibility

**Configuration Changes**:
```python
# mysite/settings.py
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',  # Temporary solution
    },
}
```

### Environment Configuration (Enhanced)

**New**: Created comprehensive `.env` file with all necessary environment variables for production deployment.

**Key Features**:
- Complete Django configuration
- Email and SMS service settings
- Notification system configuration
- Security settings
- Performance optimization settings
- Celery and Redis configuration

### Production Deployment Checklist

1. **Environment Setup**:
   - [ ] Copy `.env` file to production server
   - [ ] Update environment variables for production
   - [ ] Set proper file permissions

2. **Static Files**:
   - [ ] Run `python manage.py collectstatic --noinput`
   - [ ] Verify WhiteNoise is serving static files
   - [ ] Test admin interface CSS/JS loading

3. **Media Files**:
   - [ ] Verify media files are accessible
   - [ ] Test image uploads and display
   - [ ] Check file permissions

4. **WebSocket Functionality**:
   - [ ] Test real-time dashboard updates
   - [ ] Verify WebSocket connections
   - [ ] Consider Redis setup for production

5. **Email Configuration**:
   - [ ] Test email sending functionality
   - [ ] Verify SMTP settings
   - [ ] Test notification templates

6. **Security**:
   - [ ] Update SECRET_KEY
   - [ ] Configure ALLOWED_HOSTS
   - [ ] Enable HTTPS in production
   - [ ] Review security settings

### Quick Start Commands

```bash
# 1. Setup environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup database
python manage.py migrate

# 4. Create superuser
python manage.py createsuperuser

# 5. Collect static files
python manage.py collectstatic --noinput

# 6. Start server
python manage.py runserver  # Development
# or
daphne -b 0.0.0.0 -p 8000 mysite.asgi:application  # Production with ASGI
```

This deployment guide provides comprehensive instructions for deploying the GCX Supplier Application Portal in a production environment. Follow the steps carefully and adapt them to your specific infrastructure requirements.
