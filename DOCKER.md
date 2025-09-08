# 🐳 Docker Setup Guide for CumApp

This guide explains how to run CumApp using Docker containers.

## 📋 Prerequisites

1. **Docker** - Install from [docker.com](https://www.docker.com/get-started)
2. **Docker Compose** - Usually included with Docker Desktop
3. **Git** - For cloning the repository

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd smsproj
cp .env.example .env
```

### 2. Configure Environment Variables
Edit `.env` file with your API keys:
```env
# Required API Keys
TEXTVERIFIED_API_KEY=your_textverified_api_key
TEXTVERIFIED_EMAIL=your_email@example.com
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
GROQ_API_KEY=your_groq_api_key
```

### 3. Start Services
```bash
# Development mode (with hot reload)
./docker-dev.sh dev

# Or production mode
./docker-dev.sh prod

# Or manual start
docker-compose up -d
```

### 4. Access the Application
- **Application**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs

## 🛠 Development Commands

The `docker-dev.sh` script provides convenient commands:

```bash
# Build images
./docker-dev.sh build

# Start services
./docker-dev.sh start

# View logs
./docker-dev.sh logs
./docker-dev.sh logs app  # specific service

# Check health
./docker-dev.sh health

# Stop services
./docker-dev.sh stop

# Clean up everything
./docker-dev.sh clean

# Database operations
./docker-dev.sh db-shell
./docker-dev.sh db-backup

# Execute commands in container
./docker-dev.sh exec python --version
./docker-dev.sh shell  # open bash shell
```

## 📊 Services Overview

| Service | Port | Description |
|---------|------|-------------|
| **app** | 8000 | Main FastAPI application |
| **db** | 5432 | PostgreSQL database |
| **redis** | 6379 | Redis cache/sessions |
| **nginx** | 80/443 | Reverse proxy (production) |

## 🔧 Configuration Files

- **Dockerfile** - Main application container
- **docker-compose.yml** - Production services
- **docker-compose.dev.yml** - Development overrides
- **nginx.conf** - Nginx reverse proxy config
- **init-db.sql** - Database initialization

## 🏗 Architecture

```
┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │   FastAPI App   │
│  (Port 80/443)  │───▶│   (Port 8000)   │
└─────────────────┘    └─────────────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
            ┌─────────────┐ ┌─────────┐ ┌─────────┐
            │ PostgreSQL  │ │  Redis  │ │ External│
            │ (Port 5432) │ │(Port 6379)│ │   APIs  │
            └─────────────┘ └─────────┘ └─────────┘
```

## 🔍 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   lsof -i :8000
   
   # Kill the process or change port in docker-compose.yml
   ```

2. **Permission Denied**
   ```bash
   # Make script executable
   chmod +x docker-dev.sh
   ```

3. **Database Connection Issues**
   ```bash
   # Check database logs
   ./docker-dev.sh logs db
   
   # Reset database
   docker-compose down -v
   docker-compose up -d
   ```

4. **API Keys Not Working**
   - Verify `.env` file exists and has correct values
   - Check logs: `./docker-dev.sh logs app`
   - Ensure no extra spaces in environment variables

### Health Checks

```bash
# Check all services
./docker-dev.sh health

# Manual health checks
curl http://localhost:8000/health
docker-compose ps
```

## 🚀 Production Deployment

### 1. Environment Setup
```bash
# Copy production environment
cp .env.example .env.production

# Edit with production values
nano .env.production
```

### 2. SSL Certificates (Optional)
```bash
# Create SSL directory
mkdir ssl

# Add your certificates
cp your-cert.pem ssl/cert.pem
cp your-key.pem ssl/key.pem
```

### 3. Start Production Services
```bash
# Start with nginx reverse proxy
./docker-dev.sh prod

# Or manually
docker-compose --profile production up -d
```

### 4. Monitoring
```bash
# View all service status
./docker-dev.sh status

# Monitor logs
./docker-dev.sh logs

# Database backup
./docker-dev.sh db-backup
```

## 📈 Scaling

To scale the application:

```bash
# Scale app instances
docker-compose up -d --scale app=3

# Use load balancer
# Update nginx.conf with multiple upstream servers
```

## 🔒 Security Notes

1. **Change default passwords** in production
2. **Use environment-specific .env files**
3. **Enable SSL/TLS** for production
4. **Regularly update base images**
5. **Monitor logs** for suspicious activity

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [PostgreSQL Docker](https://hub.docker.com/_/postgres)
- [Redis Docker](https://hub.docker.com/_/redis)