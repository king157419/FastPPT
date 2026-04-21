# FastPPT Docker Deployment Guide

## Quick Start

### 1. Setup Environment

```bash
cd docker
cp .env.example .env
# Edit .env with your API keys and configuration
```

### 2. Start Services

```bash
docker-compose up -d
```

### 3. Check Status

```bash
docker-compose ps
docker-compose logs -f
```

### 4. Access Services

- Backend API: http://localhost:8000
- PPTXGenJS Service: http://localhost:3000
- Health Check: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Configuration

### Required Environment Variables

Edit `docker/.env`:

```bash
# API Keys (Required)
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# Database (Change passwords in production!)
POSTGRES_PASSWORD=change_this_secure_password
REDIS_PASSWORD=change_this_redis_password
```

### Optional Configuration

```bash
# RAGFlow Integration
RAGFLOW_BASE_URL=https://your-ragflow-instance.com
RAGFLOW_API_KEY=your_ragflow_api_key_here
RAGFLOW_KB_ID=your_knowledge_base_id_here

# Application Settings
APP_ENV=production
LOG_LEVEL=info
BACKEND_PORT=8000
PPTXGENJS_PORT=3000

# CORS (add your frontend domain)
CORS_ORIGINS=http://localhost:5173,https://your-domain.com
```

## Service Architecture

```
┌─────────────────┐
│   Frontend      │
│  (Vue.js)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│   FastAPI       │────▶│   PPTXGenJS     │
│   Backend       │     │   Service       │
│   (Port 8000)   │     │   (Port 3000)   │
└────┬────────┬───┘     └─────────────────┘
     │        │
     ▼        ▼
┌─────────┐ ┌─────────┐
│PostgreSQL│ │  Redis  │
│(Port 5432)│ │(Port 6379)│
└─────────┘ └─────────┘
```

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-03-26T10:00:00Z",
  "system": {
    "memory": {"percent": 45.2},
    "cpu": {"percent": 12.5}
  },
  "uptime_seconds": 3600
}
```

### Prometheus Metrics

```bash
curl http://localhost:8000/metrics
```

Metrics include:
- `fastppt_requests_total` - Total request count
- `fastppt_request_duration_seconds` - Request duration histogram
- `fastppt_errors_total` - Error count by type
- `fastppt_ppt_generated_total` - PPT generation count
- `fastppt_rag_queries_total` - RAG query count
- `fastppt_memory_usage_bytes` - Memory usage
- `fastppt_cpu_usage_percent` - CPU usage

### Error Logs

```bash
curl http://localhost:8000/admin/errors?limit=10
```

### Performance Stats

```bash
curl http://localhost:8000/admin/performance
```

## Logs

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f fastapi
docker-compose logs -f pptxgenjs
docker-compose logs -f postgres
docker-compose logs -f redis
```

### Log Files

Logs are persisted in Docker volumes:
- Backend logs: `backend_logs` volume → `/app/logs`
- PPTXGenJS logs: `pptxgenjs_logs` volume → `/app/logs`

Access logs:
```bash
docker exec -it fastppt-backend cat /app/logs/fastppt.log
```

## Database Management

### Connect to PostgreSQL

```bash
docker exec -it fastppt-postgres psql -U fastppt -d fastppt
```

### Backup Database

```bash
docker exec fastppt-postgres pg_dump -U fastppt fastppt > backup.sql
```

### Restore Database

```bash
cat backup.sql | docker exec -i fastppt-postgres psql -U fastppt -d fastppt
```

## Redis Management

### Connect to Redis

```bash
docker exec -it fastppt-redis redis-cli -a your_redis_password
```

### Check Cache

```bash
# Inside redis-cli
KEYS *
GET rag:cache:*
```

### Clear Cache

```bash
# Inside redis-cli
FLUSHDB
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs fastapi

# Check if ports are in use
netstat -an | grep 8000
netstat -an | grep 3000

# Restart service
docker-compose restart fastapi
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection
docker exec fastppt-backend python -c "import psycopg2; psycopg2.connect('postgresql://fastppt:password@postgres:5432/fastppt')"
```

### Memory Issues

```bash
# Check resource usage
docker stats

# Increase memory limit in docker-compose.yml
services:
  fastapi:
    deploy:
      resources:
        limits:
          memory: 2G
```

### Clear Everything and Restart

```bash
docker-compose down -v
docker-compose up -d
```

## Production Deployment

### Security Checklist

- [ ] Change default passwords in `.env`
- [ ] Use strong passwords (20+ characters)
- [ ] Enable HTTPS with reverse proxy (nginx/traefik)
- [ ] Restrict CORS origins to your domain
- [ ] Set `APP_ENV=production`
- [ ] Enable firewall rules
- [ ] Regular database backups
- [ ] Monitor disk space
- [ ] Set up log rotation

### Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL with Let's Encrypt

```bash
# Install certbot
apt-get install certbot python3-certbot-nginx

# Get certificate
certbot --nginx -d your-domain.com

# Auto-renewal
certbot renew --dry-run
```

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.yml
services:
  fastapi:
    deploy:
      replicas: 3
```

### Load Balancer

Use nginx or traefik for load balancing:

```nginx
upstream fastapi_backend {
    server localhost:8001;
    server localhost:8002;
    server localhost:8003;
}
```

## Maintenance

### Update Services

```bash
# Pull latest images
docker-compose pull

# Restart with new images
docker-compose up -d
```

### Cleanup

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune
```

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Check health: `curl http://localhost:8000/health`
3. Check metrics: `curl http://localhost:8000/metrics`
4. Review error logs: `curl http://localhost:8000/admin/errors`
