# Deployment Guide

This guide covers deployment options for QwenDBC in various environments.

## Table of Contents

- [Docker Deployment](#docker-deployment)
- [Production Configuration](#production-configuration)
- [Environment Variables](#environment-variables)
- [Reverse Proxy Setup](#reverse-proxy-setup)
- [SSL/TLS Configuration](#ssltls-configuration)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)
- [Scaling Considerations](#scaling-considerations)

---

## Docker Deployment

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: "3.8"

services:
  backend:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    container_name: qwen-backend-prod
    volumes:
      - models_data:/app/models
      - chroma_data:/app/chroma_db
      - ./logs:/app/logs
    environment:
      - MODEL_NAME=${MODEL_NAME}
      - MODEL_FILE=${MODEL_FILE}
      - N_THREADS=${N_THREADS:-8}
      - MAX_CONTEXT_LENGTH=${MAX_CONTEXT_LENGTH:-4096}
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=False
    ports:
      - "127.0.0.1:8000:8000"  # Only accessible locally
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 120s
    deploy:
      resources:
        limits:
          memory: 16G
        reservations:
          memory: 8G

  frontend:
    build:
      context: .
      dockerfile: docker/Dockerfile.frontend
    container_name: qwen-frontend-prod
    environment:
      - REACT_APP_API_URL=/api/v1
    ports:
      - "127.0.0.1:3000:3000"  # Only accessible locally
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped

volumes:
  models_data:
  chroma_data:
```

### Deploy to Production

```bash
# Set environment variables
export SECRET_KEY=$(openssl rand -hex 32)
export MODEL_NAME="Qwen/Qwen2.5-1.5B-Instruct-GGUF"
export MODEL_FILE="qwen2.5-1.5b-instruct-q4_k_m.gguf"

# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

---

## Production Configuration

### Security Hardening

1. **Change Default Secret Key**

```env
SECRET_KEY=<generate-strong-random-key>
```

Generate secure key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

2. **Restrict CORS Origins**

```env
ALLOWED_ORIGINS=["https://your-domain.com"]
```

3. **Disable Debug Mode**

```env
DEBUG=False
```

4. **Use Non-Root User** (in Dockerfile)

```dockerfile
RUN adduser --disabled-password --gecos '' appuser
USER appuser
```

### Resource Limits

Set appropriate resource limits based on your model size:

| Model Size | RAM Required | CPU Threads | Disk Space |
|------------|--------------|-------------|------------|
| 1.5B       | 4-8 GB       | 4-8         | 5 GB       |
| 3B         | 8-16 GB      | 8-12        | 10 GB      |
| 7B         | 16-32 GB     | 12-16       | 20 GB      |

---

## Environment Variables

### Complete Environment Reference

```env
# Application
APP_NAME=Qwen LLM App
APP_VERSION=1.0.0
DEBUG=False

# Server
HOST=0.0.0.0
PORT=8000

# Model Configuration
MODEL_NAME=Qwen/Qwen2.5-1.5B-Instruct-GGUF
MODEL_FILE=qwen2.5-1.5b-instruct-q4_k_m.gguf
MODEL_PATH=./models
MAX_CONTEXT_LENGTH=4096
N_THREADS=8
N_BATCH=512

# Generation Defaults
TEMPERATURE=0.7
TOP_P=0.9
MAX_TOKENS=2048

# RAG Configuration
CHROMA_DB_PATH=./chroma_db
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Security
SECRET_KEY=<your-secret-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=["https://your-domain.com"]

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Environment Files

**Development**: `.env.development`
**Staging**: `.env.staging`
**Production**: `.env.production`

Load specific environment:

```bash
set -a
source .env.production
set +a
docker-compose up -d
```

---

## Reverse Proxy Setup

### Nginx Configuration

Create `/etc/nginx/sites-available/qwendbc`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000" always;

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeouts for long-running requests
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # WebSocket support for streaming
    location /api/v1/chat/completions/stream {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Disable buffering for streaming
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding off;
    }

    # Rate limiting
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
    }
}
```

### Rate Limiting Configuration

Add to nginx `http` block:

```nginx
http {
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    
    # ... rest of config
}
```

### Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/qwendbc /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## SSL/TLS Configuration

### Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal (already configured by certbot)
sudo certbot renew --dry-run
```

### Automatic Renewal Cron Job

```bash
# Edit crontab
sudo crontab -e

# Add renewal job
0 3 * * * certbot renew --quiet --post-hook "systemctl reload nginx"
```

---

## Monitoring & Logging

### Application Logs

Configure log rotation `/etc/logrotate.d/qwendbc`:

```
/var/log/qwendbc/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 www-data www-data
    postrotate
        systemctl reload nginx
    endscript
}
```

### Docker Logs

```bash
# View recent logs
docker-compose logs --tail=100

# Follow logs in real-time
docker-compose logs -f

# Export logs
docker-compose logs > application.log
```

### Health Checks

Monitor service health:

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' qwen-backend-prod

# Test health endpoint
curl http://localhost:8000/api/v1/health
```

### Prometheus Metrics (Future)

Export metrics for monitoring:

```python
from prometheus_fastapi_instrumentator import Instrumentator

instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)
```

---

## Backup & Recovery

### Backup Strategy

#### Automated Backup Script

Create `backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/backups/qwendbc"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup ChromaDB
docker run --rm \
  -v qwendbc_chroma_data:/data \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/chroma_db_$DATE.tar.gz -C /data .

# Backup configuration
cp .env.production $BACKUP_DIR/env_$DATE.backup

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

#### Restore from Backup

```bash
# Stop services
docker-compose down

# Restore ChromaDB
docker run --rm \
  -v qwendbc_chroma_data:/data \
  -v /backups/qwendbc:/backup \
  alpine tar xzf /backup/chroma_db_YYYYMMDD_HHMMSS.tar.gz -C /data

# Restart services
docker-compose up -d
```

### Disaster Recovery Plan

1. **Document current configuration**
2. **Regular backup testing**
3. **Maintain offline copies of models**
4. **Keep dependency versions documented**

---

## Scaling Considerations

### Vertical Scaling

Increase resources on single server:

```yaml
deploy:
  resources:
    limits:
      cpus: '16'
      memory: 32G
    reservations:
      cpus: '8'
      memory: 16G
```

### Horizontal Scaling (Future)

For multiple instances:

1. **Load Balancer**: HAProxy or Nginx
2. **Shared Storage**: NFS for models
3. **Session Management**: Redis
4. **Database**: External ChromaDB cluster

### Caching Layer

Implement Redis caching:

```python
from redis import Redis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.on_event("startup")
async def startup():
    redis = Redis("redis://localhost:6379")
    FastAPICache.init(RedisBackend(redis), prefix="qwendbc-cache")
```

---

## Production Checklist

Before going live:

- [ ] Change all default passwords and keys
- [ ] Enable HTTPS with valid certificate
- [ ] Configure firewall rules
- [ ] Set up log rotation
- [ ] Configure backup automation
- [ ] Test disaster recovery
- [ ] Set up monitoring alerts
- [ ] Document runbooks
- [ ] Configure rate limiting
- [ ] Enable security headers
- [ ] Test failover procedures
- [ ] Review and restrict CORS
- [ ] Disable debug mode
- [ ] Set resource limits
- [ ] Configure health checks

---

## Troubleshooting Production Issues

### Common Issues

#### High Memory Usage

```bash
# Monitor memory
docker stats qwen-backend-prod

# Solution: Reduce model size or increase limits
```

#### Slow Response Times

```bash
# Check CPU usage
docker stats

# Check disk I/O
iostat -x 1

# Solution: Use SSD, reduce concurrent requests
```

#### Connection Timeouts

```bash
# Check network connectivity
docker exec qwen-backend-prod curl http://localhost:8000/api/v1/health

# Solution: Increase timeout settings
```

---

*Last updated: January 2025*
*Version: 1.0.0*
