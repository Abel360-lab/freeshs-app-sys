#!/bin/bash

# Create logs directory
mkdir -p logs

# Set Railway environment
export RAILWAY_ENVIRONMENT=true

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start Django development server
python manage.py runserver 0.0.0.0:$PORT