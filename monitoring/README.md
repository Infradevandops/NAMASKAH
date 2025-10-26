# 🐳 Docker Monitoring Stack

## Overview

Complete Docker monitoring solution for Namaskah SMS platform with Prometheus, Grafana, AlertManager, and container metrics.

## 🚀 Quick Start (5 minutes)

```bash
# Start complete monitoring stack
./monitoring/start_monitoring.sh

# Access dashboards
open http://localhost:3000  # Grafana (admin/admin123)
open http://localhost:9090  # Prometheus
open http://localhost:9093  # AlertManager
```

## 📊 Monitoring Components

### Core Services
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards  
- **AlertManager**: Alert routing and notifications
- **cAdvisor**: Docker container metrics

### Exporters
- **Node Exporter**: System metrics (CPU, memory, disk)
- **Postgres Exporter**: Database performance metrics
- **Redis Exporter**: Cache performance metrics
- **NGINX Exporter**: Load balancer metrics

## 📈 Available Metrics

### Container Metrics
```promql
# Container CPU usage
rate(container_cpu_usage_seconds_total[5m]) * 100

# Container memory usage
(container_memory_usage_bytes / container_spec_memory_limit_bytes) * 100

# Container restart count
increase(container_restart_count[1h])
```

### Application Metrics
```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Response time P95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### Infrastructure Metrics
```promql
# System CPU usage
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# System memory usage
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Disk usage
(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100
```

## 🚨 Alert Configuration

### Critical Alerts (Immediate Response)
- Container down or restart loop
- High error rate (>5%)
- Database/Redis connection failure
- Payment processing failures

### Warning Alerts (Review Required)
- High CPU/memory usage (>80%)
- Slow response times (P95 >2s)
- Low disk space (>85%)
- Low verification success rate (<80%)

### Alert Channels
- **Email**: devops@namaskah.com
- **Slack**: Configure webhook in `alertmanager.yml`
- **PagerDuty**: Configure integration key

## 🔧 Configuration

### Prometheus Targets
Edit `monitoring/prometheus.yml` to add/remove monitoring targets:

```yaml
scrape_configs:
  - job_name: 'namaskah-app'
    static_configs:
      - targets: ['host.docker.internal:8000']
```

### Alert Rules
Edit `monitoring/alert_rules.yml` to customize alert thresholds:

```yaml
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
  for: 2m
```

### Notification Channels
Edit `monitoring/alertmanager.yml` for email/Slack/PagerDuty:

```yaml
slack_configs:
  - api_url: 'YOUR_SLACK_WEBHOOK_URL'
    channel: '#alerts'
```

## 📊 Grafana Dashboards

### Pre-configured Dashboards
1. **Docker Overview**: Container health and resource usage
2. **Application Performance**: Request rates, response times, errors
3. **Infrastructure**: System resources and network
4. **Business Metrics**: SMS verifications, payments, users

### Custom Dashboard Creation
1. Login to Grafana (admin/admin123)
2. Create new dashboard
3. Add panels with PromQL queries
4. Save and share with team

## 🔍 Troubleshooting

### Services Not Starting
```bash
# Check Docker logs
docker-compose -f monitoring/docker-compose.yml logs

# Restart specific service
docker-compose -f monitoring/docker-compose.yml restart prometheus
```

### Metrics Not Appearing
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Verify application metrics endpoint
curl http://localhost:8000/metrics
```

### Alerts Not Firing
```bash
# Check alert rules
curl http://localhost:9090/api/v1/rules

# Test alert expression
curl "http://localhost:9090/api/v1/query?query=up==0"
```

## 📱 Mobile Monitoring

### Grafana Mobile App
1. Download Grafana mobile app
2. Connect to http://your-server:3000
3. View dashboards on mobile device

### Alert Notifications
- Configure push notifications via Grafana mobile app
- Set up SMS alerts via webhook integration

## 🔒 Security

### Access Control
- Change default Grafana password
- Configure LDAP/OAuth authentication
- Set up role-based access control

### Network Security
- Use reverse proxy for external access
- Configure SSL/TLS certificates
- Implement IP whitelisting

## 📈 Performance Optimization

### Prometheus Retention
```yaml
# Adjust retention period in docker-compose.yml
command:
  - '--storage.tsdb.retention.time=15d'
```

### Scrape Intervals
```yaml
# Optimize scrape intervals based on needs
scrape_interval: 30s  # Production workloads
scrape_interval: 15s  # Development/testing
```

## 🎯 Monitoring Best Practices

### Key Metrics to Watch
1. **Golden Signals**: Latency, traffic, errors, saturation
2. **Business Metrics**: Conversion rates, revenue, user activity
3. **Infrastructure**: Resource utilization, capacity planning

### Alert Fatigue Prevention
- Set appropriate thresholds
- Use alert grouping and inhibition
- Implement escalation policies
- Regular alert rule review

### Dashboard Design
- Focus on actionable metrics
- Use consistent color schemes
- Group related metrics together
- Include context and annotations

---

**Status**: Complete Docker monitoring solution ready
**Setup Time**: 5 minutes
**Maintenance**: Automated with health checks