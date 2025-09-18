# Real-time GCX Supplier Application System

This system now includes real-time features powered by Redis, Celery, and WebSockets.

## 🚀 Quick Start

### Option 1: Automated Start (Recommended)
```bash
# Run this single command to start everything
start_all.bat
```

### Option 2: Manual Start
You need to run these components in separate terminal windows:

1. **Start Redis Server**
   ```bash
   start_redis.bat
   ```

2. **Start Celery Worker** (Background Tasks)
   ```bash
   start_celery.bat
   ```

3. **Start Celery Beat** (Scheduled Tasks)
   ```bash
   start_celery_beat.bat
   ```

4. **Start Django Server** (Web + WebSockets)
   ```bash
   start_django.bat
   ```

## 🔧 Prerequisites

### Required Software
- **Redis Server**: Download from [Redis for Windows](https://github.com/microsoftarchive/redis/releases)
- **Python 3.8+** with virtual environment
- **Django 5.2+**

### Installation
```bash
# Install Redis (if not already installed)
# Option 1: Download from GitHub releases
# Option 2: Using Chocolatey
choco install redis-64

# Install Python dependencies
pip install redis celery django-celery-beat django-celery-results channels channels-redis
```

## 📊 Real-time Features

### 1. Live Dashboard Updates
- **WebSocket Connection**: Real-time data updates without page refresh
- **Status Distribution**: Live percentage updates
- **Recent Applications**: Auto-updating list
- **Connection Status**: Visual indicator of WebSocket connection

### 2. Background Job Processing
- **Queued Notifications**: Email notifications processed in background
- **Scheduled Tasks**: Automatic cleanup and maintenance
- **Heavy Operations**: Application approval, bulk operations

### 3. Notification System
- **Async Email Sending**: Non-blocking email delivery
- **Retry Logic**: Failed notifications automatically retried
- **Status Tracking**: Real-time notification status updates

## 🔄 System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Django Web    │    │   Redis Cache   │    │  Celery Worker  │
│   (WebSockets)  │◄──►│   (Message      │◄──►│  (Background    │
│                 │    │    Broker)      │    │   Tasks)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   Database      │    │  Email Service  │
│   (Real-time    │    │   (SQLite)      │    │  (SMTP)         │
│    Updates)     │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📈 Dashboard Features

### Real-time Updates
- **Live Statistics**: Application counts, status percentages
- **Auto-refresh**: Data updates every 5 minutes automatically
- **Manual Refresh**: Click refresh button for immediate updates
- **Connection Status**: Visual indicator of real-time connection

### Status Distribution
- **All Status Types**: Pending Review, Approved, Under Review, etc.
- **Accurate Percentages**: Fixed calculation precision issues
- **Clean Design**: Removed status badges for cleaner look
- **Live Updates**: Percentages update in real-time

## 🔔 Notification System

### Queued Processing
- **Background Sending**: Emails sent asynchronously
- **Retry Logic**: Failed emails automatically retried (max 3 times)
- **Status Tracking**: Real-time notification status
- **Bulk Operations**: Multiple notifications processed efficiently

### Notification Types
- **Application Approval**: With login credentials
- **Document Requests**: Missing document notifications
- **Status Updates**: Application status changes
- **System Notifications**: Maintenance and alerts

## 🛠️ Configuration

### Environment Variables
```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Celery Beat Schedule
- **Send Pending Notifications**: Every minute
- **Cleanup Old Notifications**: Daily
- **Update Dashboard Stats**: Every 5 minutes

## 🔍 Monitoring

### Celery Monitoring
```bash
# Monitor Celery tasks
celery -A mysite flower

# Check worker status
celery -A mysite status

# Inspect active tasks
celery -A mysite inspect active
```

### Redis Monitoring
```bash
# Connect to Redis CLI
redis-cli

# Monitor Redis commands
redis-cli monitor

# Check Redis info
redis-cli info
```

## 🐛 Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   - Ensure Redis server is running
   - Check Redis URL configuration
   - Verify Redis is accessible on port 6379

2. **Celery Worker Not Starting**
   - Check Redis connection
   - Verify Django settings
   - Check for import errors in tasks

3. **WebSocket Connection Failed**
   - Ensure Django server is running with ASGI
   - Check CHANNEL_LAYERS configuration
   - Verify Redis is running for channel layers

4. **Notifications Not Sending**
   - Check email configuration
   - Verify Celery worker is running
   - Check notification logs in Django admin

### Debug Commands
```bash
# Test Redis connection
python manage.py shell
>>> import redis
>>> r = redis.Redis(host='localhost', port=6379, db=0)
>>> r.ping()

# Test Celery connection
celery -A mysite inspect ping

# Check WebSocket routing
python manage.py shell
>>> from applications.routing import websocket_urlpatterns
>>> print(websocket_urlpatterns)
```

## 📝 Development

### Adding New Real-time Features
1. **Create WebSocket Consumer** in `applications/consumers.py`
2. **Add URL Pattern** in `applications/routing.py`
3. **Create JavaScript Client** in `static/js/`
4. **Add to Template** with WebSocket connection

### Adding Background Tasks
1. **Create Task Function** in `applications/tasks.py` or `notifications/tasks.py`
2. **Use @shared_task decorator**
3. **Call with .delay() method** for async execution
4. **Add to Beat Schedule** if recurring

## 🚀 Production Deployment

### Requirements
- **Redis Server**: Production Redis instance
- **Celery Workers**: Multiple worker processes
- **Web Server**: Nginx + Gunicorn + Daphne
- **Process Manager**: Supervisor or systemd

### Example Production Setup
```bash
# Install production dependencies
pip install gunicorn daphne supervisor

# Configure Nginx for WebSocket proxying
# Configure Supervisor for process management
# Set up Redis persistence
# Configure email service
```

## 📊 Performance

### Optimizations
- **Redis Caching**: Frequently accessed data cached
- **Database Indexing**: Optimized queries
- **WebSocket Compression**: Reduced bandwidth usage
- **Task Batching**: Efficient background processing

### Monitoring
- **Celery Flower**: Task monitoring dashboard
- **Redis Monitoring**: Memory and performance metrics
- **Django Debug Toolbar**: Development debugging
- **Application Logs**: Comprehensive logging system

---

## 🎯 Next Steps

1. **Start the system** using `start_all.bat`
2. **Visit the dashboard** at `http://localhost:8000/backoffice/`
3. **Test real-time features** by submitting applications
4. **Monitor background tasks** in Celery Flower
5. **Check notification delivery** in Django admin

The system is now fully real-time with background job processing! 🚀
