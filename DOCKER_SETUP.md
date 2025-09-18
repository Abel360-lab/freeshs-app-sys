# Docker Setup for GCX Supplier Application System

This guide will help you set up Redis using Docker for the real-time features.

## 🐳 Prerequisites

### Install Docker Desktop
1. **Download Docker Desktop**: Visit [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. **Install Docker Desktop**: Run the installer and follow the setup wizard
3. **Start Docker Desktop**: Launch Docker Desktop and ensure it's running
4. **Verify Installation**: Open Command Prompt and run:
   ```bash
   docker --version
   docker-compose --version
   ```

## 🚀 Quick Start

### Option 1: Automated Start (Recommended)
```bash
# This will start Redis with Docker automatically
start_all.bat
```

### Option 2: Manual Start
1. **Start Redis with Docker**:
   ```bash
   start_redis.bat
   ```

2. **Start Celery Worker** (in new terminal):
   ```bash
   start_celery.bat
   ```

3. **Start Celery Beat** (in new terminal):
   ```bash
   start_celery_beat.bat
   ```

4. **Start Django Server** (in new terminal):
   ```bash
   start_django.bat
   ```

## 📊 Redis Management

### Redis Commander (Web UI)
- **URL**: http://localhost:8081
- **Features**: Browse Redis data, monitor keys, execute commands
- **Access**: Automatically started with Redis

### Docker Commands
```bash
# Start Redis services
docker-compose up -d

# Stop Redis services
docker-compose down

# View Redis logs
docker-compose logs redis

# Restart Redis
docker-compose restart redis

# Check Redis status
docker-compose ps
```

## 🔧 Configuration

### Redis Connection
- **Host**: localhost
- **Port**: 6379
- **Database**: 0 (default)
- **Password**: None (default)

### Environment Variables
```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## 🐛 Troubleshooting

### Common Issues

1. **Docker Not Running**
   ```
   ERROR: Docker is not installed or not running
   ```
   **Solution**: Start Docker Desktop and wait for it to fully load

2. **Port Already in Use**
   ```
   ERROR: Port 6379 is already in use
   ```
   **Solution**: Stop any existing Redis instances or change the port in docker-compose.yml

3. **Docker Compose Not Found**
   ```
   ERROR: Docker Compose is not available
   ```
   **Solution**: Update Docker Desktop to the latest version

4. **Permission Denied**
   ```
   ERROR: Permission denied
   ```
   **Solution**: Run Command Prompt as Administrator

### Debug Commands
```bash
# Check Docker status
docker --version
docker-compose --version

# Check running containers
docker ps

# Check Redis container logs
docker-compose logs redis

# Test Redis connection
docker exec -it gcx_redis redis-cli ping
```

## 📈 Monitoring

### Redis Commander
- **URL**: http://localhost:8081
- **Features**:
  - Browse all Redis keys
  - Monitor memory usage
  - Execute Redis commands
  - View real-time data

### Command Line Monitoring
```bash
# Connect to Redis CLI
docker exec -it gcx_redis redis-cli

# Monitor Redis commands
docker exec -it gcx_redis redis-cli monitor

# Check Redis info
docker exec -it gcx_redis redis-cli info

# Check memory usage
docker exec -it gcx_redis redis-cli info memory
```

## 🔄 Data Persistence

### Redis Data Volume
- **Location**: Docker volume `redis_data`
- **Persistence**: Data survives container restarts
- **Backup**: Data is stored in Docker volume

### Backup Commands
```bash
# Create backup
docker exec gcx_redis redis-cli BGSAVE

# Copy backup file
docker cp gcx_redis:/data/dump.rdb ./redis_backup.rdb
```

## 🚀 Production Considerations

### Security
- **Password Protection**: Add password to Redis configuration
- **Network Security**: Use Docker networks for internal communication
- **Access Control**: Limit Redis access to application containers only

### Performance
- **Memory Limits**: Set appropriate memory limits for Redis container
- **Persistence**: Configure appropriate persistence settings
- **Monitoring**: Set up proper monitoring and alerting

### Example Production Configuration
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    container_name: gcx_redis_prod
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --requirepass your_secure_password
    restart: always
    environment:
      - REDIS_PASSWORD=your_secure_password
    healthcheck:
      test: ["CMD", "redis-cli", "--no-auth-warning", "-a", "your_secure_password", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 📝 Next Steps

1. **Install Docker Desktop** if not already installed
2. **Run `start_redis.bat`** to start Redis with Docker
3. **Verify Redis is running** at http://localhost:8081
4. **Start the application** with `start_all.bat`
5. **Test real-time features** in the dashboard

The system is now ready to run with Docker! 🐳
