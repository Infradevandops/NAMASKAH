# 🚀 Namaskah SMS - Quick Start Guide

## Production Deployment (30 Minutes)

### Step 1: Environment Setup (5 minutes)
```bash
# 1. Copy production environment template
cp .env.production.template .env.production

# 2. Edit with your production values
# Required: DATABASE_URL, REDIS_URL, TEXTVERIFIED_API_KEY, PAYSTACK_SECRET_KEY, DOMAIN

# 3. Validate configuration
python scripts/validate_config.py
```

### Step 2: Deploy Services (15 minutes)
```bash
# 1. Start production stack
docker-compose -f docker-compose.prod.yml up -d

# 2. Verify services are healthy
docker-compose -f docker-compose.prod.yml ps

# 3. Check application health
curl http://localhost/system/health
```

### Step 3: SSL & DNS (10 minutes)
```bash
# 1. Generate SSL certificate
docker-compose -f docker-compose.prod.yml run --rm certbot

# 2. Configure DNS A record pointing to your server IP

# 3. Verify HTTPS
curl https://your-domain.com/system/health
```

## Monitoring Setup (5 Minutes)

```bash
# Start complete monitoring stack
./monitoring/start_monitoring.sh

# Access dashboards
open http://localhost:3000  # Grafana (admin/admin123)
open http://localhost:9090  # Prometheus
open http://localhost:9093  # AlertManager
```

## Development Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup environment
cp .env.example .env

# 3. Run migrations
alembic upgrade head

# 4. Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Key Endpoints

- **Health Check**: `/system/health`
- **API Docs**: `/docs`
- **Metrics**: `/metrics`
- **Admin**: `/admin`

## Support

- **Documentation**: See individual markdown files
- **Issues**: Check logs via `docker-compose logs`
- **Monitoring**: Grafana dashboards for real-time insights