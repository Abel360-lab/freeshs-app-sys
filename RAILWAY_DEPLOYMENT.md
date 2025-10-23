# 🚀 Railway Deployment Guide

## Prerequisites
1. GitHub account
2. Railway account (sign up at [railway.app](https://railway.app))
3. Your Django app pushed to GitHub

## Step 1: Push to GitHub
```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

## Step 2: Deploy on Railway

### Option A: Deploy from GitHub
1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will automatically detect it's a Django app

### Option B: Deploy with Railway CLI
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Deploy
railway up
```

## Step 3: Configure Environment Variables

In Railway dashboard, go to your project → Variables tab and add:

### Required Variables:
```
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-app-name.railway.app
```

### Database:
Railway automatically provides `DATABASE_URL` - no need to set manually.

### Optional Variables:
```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

NOTIFICATION_API_URL=https://your-notification-api.com
NOTIFICATION_API_KEY=your-api-key

SMS_PROVIDER=your-sms-provider
SMS_API_KEY=your-sms-api-key
SMS_SENDER_ID=your-sender-id
```

## Step 4: Database Setup

Railway will automatically:
1. Create a PostgreSQL database
2. Set the `DATABASE_URL` environment variable
3. Run migrations on deployment

## Step 5: Static Files

Railway will automatically:
1. Run `python manage.py collectstatic --noinput`
2. Serve static files via WhiteNoise

## Step 6: Create Superuser

After deployment, create a superuser:
```bash
# Using Railway CLI
railway run python manage.py createsuperuser

# Or in Railway dashboard → Deployments → View Logs → Connect to shell
```

## Step 7: Access Your App

Your app will be available at:
`https://your-app-name.railway.app`

## Troubleshooting

### Common Issues:

1. **Build Fails**: Check that all dependencies are in `requirements.txt`
2. **Database Errors**: Ensure `DATABASE_URL` is set
3. **Static Files Not Loading**: Check `STATIC_ROOT` and `STATIC_URL` settings
4. **CORS Errors**: Update `CORS_ALLOWED_ORIGINS` with your Railway domain

### View Logs:
```bash
railway logs
```

### Connect to Database:
```bash
railway connect
```

## Free Tier Limits

Railway's free tier includes:
- 500 hours of usage per month
- 1GB RAM
- 1GB storage
- PostgreSQL database
- Custom domains

## Cost Optimization

To stay within free limits:
1. Use Railway's sleep feature (app sleeps after 5 minutes of inactivity)
2. Optimize your app for low memory usage
3. Use efficient database queries
4. Minimize static file sizes

## Monitoring

Railway provides:
- Real-time logs
- Performance metrics
- Automatic deployments from GitHub
- Environment variable management
- Database management

## Next Steps

1. Set up custom domain (optional)
2. Configure SSL certificates (automatic)
3. Set up monitoring and alerts
4. Configure backup strategies
5. Set up CI/CD pipeline

## Support

- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Railway GitHub: https://github.com/railwayapp
