# 🏆 Production Best Practices & Pro Tips

## 🔒 **Security Best Practices**

### **1. Environment Security**
```bash
# Use strong secrets (256-bit minimum)
SECRET_KEY=$(openssl rand -hex 32)

# Separate configs per environment
.env.development
.env.staging  
.env.production

# Never commit secrets to git
echo "*.env" >> .gitignore
```

### **2. Database Security**
```python
# Use connection pooling
SQLALCHEMY_POOL_SIZE=20
SQLALCHEMY_MAX_OVERFLOW=30
SQLALCHEMY_POOL_TIMEOUT=30
SQLALCHEMY_POOL_RECYCLE=3600

# Enable SSL for production
DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=require"
```

### **3. API Security**
```python
# Rate limiting per endpoint
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Implement sliding window rate limiting
    # Use Redis for distributed rate limiting
```

## 🚀 **Performance Optimization**

### **1. Database Optimization**
```python
# Add database indexes
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_verification_user_id ON verifications(user_id);
CREATE INDEX idx_verification_status ON verifications(status);

# Use database connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True
)
```

### **2. Caching Strategy**
```python
# Redis caching for frequently accessed data
@lru_cache(maxsize=1000)
def get_user_by_id(user_id: str):
    # Cache user data for 15 minutes
    
# Cache API responses
@app.middleware("http")
async def cache_middleware(request: Request, call_next):
    # Implement response caching for GET requests
```

### **3. Async Operations**
```python
# Use async for I/O operations
async def send_notification(user_id: str, message: str):
    # Async email/SMS sending
    
# Background task processing
from celery import Celery
celery_app = Celery("namaskah", broker="redis://localhost:6379")
```

## 📊 **Monitoring & Observability**

### **1. Structured Logging**
```python
import structlog

logger = structlog.get_logger()

# Log with context
logger.info("user_login", user_id=user.id, ip=request.client.host)
```

### **2. Metrics Collection**
```python
# Prometheus metrics
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests')
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
```

### **3. Health Checks**
```python
# Comprehensive health checks
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": await check_database(),
        "redis": await check_redis(),
        "external_apis": await check_external_services()
    }
```

## 🔄 **DevOps Best Practices**

### **1. CI/CD Pipeline**
```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: pytest --cov=app --cov-fail-under=90
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: kubectl apply -f k8s/
```

### **2. Container Optimization**
```dockerfile
# Multi-stage build
FROM python:3.11-slim as builder
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **3. Kubernetes Deployment**
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: namaskah-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: namaskah-app
  template:
    spec:
      containers:
      - name: app
        image: namaskah:latest
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

## 🛡️ **Error Handling & Recovery**

### **1. Circuit Breaker Pattern**
```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=30)
async def call_external_api():
    # Protect against external API failures
```

### **2. Retry Logic**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def reliable_api_call():
    # Retry with exponential backoff
```

### **3. Graceful Degradation**
```python
async def get_verification_status(verification_id: str):
    try:
        return await external_api.get_status(verification_id)
    except ExternalServiceError:
        # Fallback to cached data
        return await get_cached_status(verification_id)
```

## 📈 **Scalability Patterns**

### **1. Database Scaling**
```python
# Read replicas for scaling reads
class DatabaseRouter:
    def db_for_read(self, model, **hints):
        return 'replica'
    
    def db_for_write(self, model, **hints):
        return 'primary'
```

### **2. Horizontal Scaling**
```yaml
# Auto-scaling configuration
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: namaskah-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: namaskah-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### **3. Caching Layers**
```python
# Multi-level caching
L1_CACHE = {}  # In-memory cache
L2_CACHE = redis_client  # Redis cache
L3_CACHE = database  # Database cache
```