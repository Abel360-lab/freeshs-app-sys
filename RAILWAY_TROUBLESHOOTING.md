# 🚨 Railway Deployment Troubleshooting Guide

## ✅ **Pre-Deployment Checklist**

### 1. **Environment Variables Setup**
In Railway Dashboard → Variables tab, ensure you have:

```
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-app-name.railway.app
DATABASE_URL=postgresql://... (Railway provides this automatically)
```

### 2. **Required Files Present**
- ✅ `requirements.txt` - Clean dependencies
- ✅ `railway.json` - Railway configuration
- ✅ `Procfile` - Process configuration
- ✅ `start.sh` - Startup script (optional)
- ✅ `core/health_views.py` - Health check endpoints

## 🔍 **Common Issues & Solutions**

### **Issue 1: Health Check Fails**
**Symptoms:** `Healthcheck failed!` or `service unavailable`

**Solutions:**
1. **Check health check path:**
   - Current: `/core/health/simple/`
   - Alternative: `/` (root path)

2. **Verify health check endpoint:**
   ```bash
   # Test locally
   curl http://localhost:8000/core/health/simple/
   # Should return: {"status": "ok"}
   ```

3. **Check if app is binding to correct port:**
   - Must bind to `0.0.0.0:$PORT`
   - Railway provides `$PORT` environment variable

### **Issue 2: Database Connection Errors**
**Symptoms:** `database connection failed` or migration errors

**Solutions:**
1. **Check DATABASE_URL:**
   - Railway automatically provides this
   - Should be PostgreSQL format: `postgresql://user:pass@host:port/db`

2. **Test database connection:**
   ```python
   # In Django shell
   from django.db import connection
   connection.ensure_connection()
   ```

3. **Check database service:**
   - In Railway dashboard, ensure PostgreSQL service is running
   - Check if database is provisioned

### **Issue 3: Static Files Not Loading**
**Symptoms:** CSS/JS files return 404

**Solutions:**
1. **Check STATIC_ROOT setting:**
   ```python
   STATIC_ROOT = os.getenv('STATIC_ROOT', BASE_DIR / 'staticfiles')
   ```

2. **Verify collectstatic runs:**
   - Should run during deployment
   - Check logs for collectstatic output

3. **Check WhiteNoise configuration:**
   ```python
   MIDDLEWARE = [
       'whitenoise.middleware.WhiteNoiseMiddleware',
       # ... other middleware
   ]
   ```

### **Issue 4: App Won't Start**
**Symptoms:** Container exits immediately or won't start

**Solutions:**
1. **Check startup command:**
   - Current: `python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py runserver 0.0.0.0:$PORT`
   - Alternative: Use `start.sh` script

2. **Check dependencies:**
   - Ensure all packages in `requirements.txt`
   - Check for version conflicts

3. **Check logs:**
   - Railway Dashboard → Deployments → View Logs
   - Look for Python errors or import errors

### **Issue 5: Memory Issues**
**Symptoms:** App crashes with memory errors

**Solutions:**
1. **Optimize Gunicorn workers:**
   ```bash
   gunicorn mysite.wsgi:application --workers 1 --max-requests 1000
   ```

2. **Check memory usage:**
   - Railway free tier: 1GB RAM
   - Monitor in Railway dashboard

3. **Optimize Django settings:**
   ```python
   # Disable debug in production
   DEBUG = False
   
   # Use efficient database queries
   # Add database connection pooling
   ```

## 🛠️ **Debugging Steps**

### **Step 1: Check Railway Logs**
1. Go to Railway Dashboard
2. Click on your project
3. Go to "Deployments" tab
4. Click on latest deployment
5. Check "Logs" tab for errors

### **Step 2: Test Locally**
```bash
# Test with Railway-like environment
export PORT=8000
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py runserver 0.0.0.0:$PORT
```

### **Step 3: Check Health Endpoints**
```bash
# Test health check locally
curl http://localhost:8000/core/health/simple/
curl http://localhost:8000/core/health/
```

### **Step 4: Verify Database**
```bash
# Check database connection
python manage.py shell
>>> from django.db import connection
>>> connection.ensure_connection()
>>> print("Database connected!")
```

## 🔧 **Alternative Configurations**

### **Option 1: Simple Django Runserver**
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py runserver 0.0.0.0:$PORT",
    "healthcheckPath": "/",
    "healthcheckTimeout": 60
  }
}
```

### **Option 2: Gunicorn with Workers**
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn mysite.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 120",
    "healthcheckPath": "/",
    "healthcheckTimeout": 60
  }
}
```

### **Option 3: Using Startup Script**
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "chmod +x start.sh && ./start.sh",
    "healthcheckPath": "/core/health/simple/",
    "healthcheckTimeout": 300
  }
}
```

## 📊 **Monitoring & Maintenance**

### **Check App Status:**
1. Railway Dashboard → Metrics
2. Check CPU, Memory, Network usage
3. Monitor response times

### **View Real-time Logs:**
```bash
# Using Railway CLI
railway logs

# Or in Railway Dashboard
# Deployments → View Logs
```

### **Database Management:**
```bash
# Connect to database
railway connect

# Run Django commands
railway run python manage.py shell
railway run python manage.py createsuperuser
```

## 🚀 **Deployment Commands**

### **Manual Deployment:**
```bash
# Using Railway CLI
railway login
railway init
railway up
```

### **GitHub Integration:**
1. Connect GitHub repo to Railway
2. Enable auto-deploy on push
3. Railway will deploy automatically

## 📞 **Getting Help**

### **Railway Resources:**
- [Railway Documentation](https://docs.railway.app)
- [Railway Discord](https://discord.gg/railway)
- [Railway GitHub](https://github.com/railwayapp)

### **Django Resources:**
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Django on Railway](https://docs.railway.app/guides/django)

### **Common Error Messages:**
- `ModuleNotFoundError`: Check requirements.txt
- `Database connection failed`: Check DATABASE_URL
- `Static files not found`: Check collectstatic
- `Health check failed`: Check health endpoint
- `Port binding failed`: Check $PORT environment variable
