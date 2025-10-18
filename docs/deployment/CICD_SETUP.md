# CI/CD Setup Guide

## Overview
Automated testing, building, and deployment pipeline using GitHub Actions.

## Workflows Created

### 1. **CI/CD Pipeline** (`.github/workflows/ci.yml`)
**Triggers**: Push to main/develop, Pull requests

**Jobs**:
- **Test**: Run pytest with coverage
- **Lint**: Check code formatting (black, flake8)
- **Security**: Scan dependencies for vulnerabilities
- **Deploy**: Auto-deploy to Railway on main branch

**Status**: ✅ Ready

---

### 2. **Docker Build** (`.github/workflows/docker.yml`)
**Triggers**: Push to main, version tags

**Actions**:
- Build Docker image
- Push to Docker Hub
- Tag with version/branch name
- Cache layers for faster builds

**Status**: ✅ Ready

---

### 3. **Health Check** (`.github/workflows/health-check.yml`)
**Triggers**: Every 15 minutes, manual

**Actions**:
- Check `/health` endpoint
- Alert on failure (Slack)
- Monitor uptime

**Status**: ✅ Ready

---

### 4. **Database Backup** (`.github/workflows/backup.yml`)
**Triggers**: Daily at 2 AM UTC, manual

**Actions**:
- Dump PostgreSQL database
- Compress and upload to S3
- Retain last 7 days
- Auto-cleanup old backups

**Status**: ✅ Ready

---

### 5. **Deploy Staging** (`.github/workflows/deploy-staging.yml`)
**Triggers**: Push to develop branch

**Actions**:
- Deploy to staging environment
- Test before production

**Status**: ✅ Ready

---

## Required Secrets

Add these to GitHub repository settings → Secrets and variables → Actions:

### Deployment
```
RAILWAY_TOKEN          # Railway CLI token
DOCKER_USERNAME        # Docker Hub username
DOCKER_PASSWORD        # Docker Hub password/token
```

### Database
```
DATABASE_URL           # PostgreSQL connection string
AWS_ACCESS_KEY_ID      # For S3 backups
AWS_SECRET_ACCESS_KEY  # For S3 backups
S3_BACKUP_BUCKET       # S3 bucket name
```

### APIs
```
TEXTVERIFIED_API_KEY   # SMS API key
PAYSTACK_SECRET_KEY    # Payment gateway
GOOGLE_CLIENT_ID       # OAuth
JWT_SECRET_KEY         # JWT signing
```

### Monitoring
```
SLACK_WEBHOOK          # For alerts
SAFETY_API_KEY         # Security scanning (optional)
```

---

## Platform Configurations

### Railway (`railway.json`)
```json
{
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

### Render (`render.yaml`)
- Auto-deploy on push
- PostgreSQL database included
- Health check monitoring
- Environment variables managed

---

## Setup Steps

### 1. GitHub Secrets
```bash
# Go to: Settings → Secrets and variables → Actions
# Add all required secrets listed above
```

### 2. Railway Setup
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link project
railway link

# Get token for GitHub Actions
railway tokens create
# Add to GitHub secrets as RAILWAY_TOKEN
```

### 3. Docker Hub
```bash
# Create repository: namaskah/sms-platform
# Generate access token
# Add to GitHub secrets
```

### 4. Enable Workflows
```bash
# Push to trigger first run
git add .
git commit -m "Add CI/CD workflows"
git push origin main
```

---

## Deployment Flow

### Development
```
develop branch → Deploy to Staging → Manual testing
```

### Production
```
main branch → Run tests → Build Docker → Deploy to Railway → Health check
```

### Hotfix
```
hotfix branch → PR to main → Auto-deploy after merge
```

---

## Monitoring

### GitHub Actions
- View workflow runs: Actions tab
- Check logs for failures
- Re-run failed jobs

### Railway Dashboard
- Monitor deployments
- View logs
- Check metrics

### Health Checks
- Automated every 15 minutes
- Slack alerts on failure
- Manual trigger available

---

## Rollback Procedure

### Railway
```bash
railway rollback
```

### Docker
```bash
# Deploy specific version
docker pull namaskah/sms-platform:v1.0.0
railway up
```

### Database
```bash
# Restore from S3 backup
aws s3 cp s3://bucket/backups/backup.sql.gz .
gunzip backup.sql.gz
psql $DATABASE_URL < backup.sql
```

---

## Testing Locally

### Run CI checks locally
```bash
# Tests
pytest tests/ -v --cov

# Linting
black --check .
flake8 .

# Security
safety check
```

### Test Docker build
```bash
docker build -t namaskah-sms .
docker run -p 8000:8000 namaskah-sms
```

---

## Troubleshooting

### Workflow fails
1. Check logs in Actions tab
2. Verify secrets are set
3. Test locally first
4. Check Railway/Render status

### Deployment fails
1. Check environment variables
2. Verify database connection
3. Check API credentials
4. Review application logs

### Health check fails
1. Check production URL
2. Verify `/health` endpoint
3. Check server status
4. Review error logs

---

## Best Practices

### Commits
- Use conventional commits
- Tag releases: `v1.0.0`
- Write clear messages

### Branches
- `main`: Production
- `develop`: Staging
- `feature/*`: New features
- `hotfix/*`: Urgent fixes

### Testing
- Write tests for new features
- Maintain 80%+ coverage
- Test before merging

### Security
- Rotate secrets regularly
- Use environment variables
- Never commit credentials
- Review dependencies

---

## Metrics

### CI/CD Performance
- **Build Time**: ~3-5 minutes
- **Test Time**: ~1-2 minutes
- **Deploy Time**: ~2-3 minutes
- **Total**: ~6-10 minutes

### Uptime Targets
- **Production**: 99.9%
- **Staging**: 99%
- **Health Checks**: Every 15 min

---

## Cost Estimate

### GitHub Actions
- **Free tier**: 2,000 minutes/month
- **Expected usage**: ~500 minutes/month
- **Cost**: $0

### Railway
- **Starter**: $5/month
- **Pro**: $20/month (recommended)

### Docker Hub
- **Free tier**: Unlimited public repos
- **Cost**: $0

### S3 Backups
- **Storage**: ~$0.50/month
- **Transfers**: ~$0.10/month
- **Total**: ~$0.60/month

**Total Monthly**: ~$20-25

---

## Next Steps

1. ✅ Add GitHub secrets
2. ✅ Connect Railway/Render
3. ✅ Push to trigger first deployment
4. ✅ Verify health checks work
5. ✅ Test backup/restore
6. ✅ Monitor for 24 hours

---

**Version**: 1.0  
**Last Updated**: October 17, 2024  
**Status**: ✅ Production Ready
