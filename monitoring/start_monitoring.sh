#!/bin/bash

# Namaskah SMS - Complete Docker Monitoring Setup
# This script deploys the full monitoring stack

set -e

echo "🚀 Starting Namaskah SMS Monitoring Stack..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Create monitoring network if it doesn't exist
docker network create monitoring 2>/dev/null || true

# Start monitoring stack
echo "📊 Starting Prometheus, Grafana, and AlertManager..."
docker-compose -f monitoring/docker-compose.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

services=("prometheus:9090" "grafana:3000" "alertmanager:9093" "cadvisor:8080")
for service in "${services[@]}"; do
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    if curl -f -s "http://localhost:$port" > /dev/null; then
        echo "✅ $name is healthy"
    else
        echo "❌ $name is not responding"
    fi
done

echo ""
echo "🎉 Monitoring stack is ready!"
echo ""
echo "📊 Access your monitoring tools:"
echo "   Grafana:      http://localhost:3000 (admin/admin123)"
echo "   Prometheus:   http://localhost:9090"
echo "   AlertManager: http://localhost:9093"
echo "   cAdvisor:     http://localhost:8080"
echo ""
echo "📈 Key metrics to monitor:"
echo "   - Container health and resource usage"
echo "   - Application performance (response times, error rates)"
echo "   - Database and Redis performance"
echo "   - System resources (CPU, memory, disk)"
echo ""
echo "🚨 Alerts are configured for:"
echo "   - Container failures and restarts"
echo "   - High resource usage"
echo "   - Application errors and slow responses"
echo "   - Database connectivity issues"
echo ""
echo "📧 Configure email/Slack notifications in monitoring/alertmanager.yml"
echo ""
echo "✅ Docker monitoring is now complete!"