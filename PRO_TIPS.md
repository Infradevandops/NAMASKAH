# 💡 Pro Tips for Enterprise Deployment

## 🎯 **Performance Pro Tips**

### **1. Database Optimization**
```sql
-- Create composite indexes for common queries
CREATE INDEX idx_verification_user_status ON verifications(user_id, status);
CREATE INDEX idx_transaction_user_date ON transactions(user_id, created_at DESC);

-- Partition large tables by date
CREATE TABLE verifications_2024 PARTITION OF verifications 
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

### **2. Connection Pool Tuning**
```python
# Optimal connection pool settings
POOL_SIZE = min(32, (CPU_CORES * 2) + 1)
MAX_OVERFLOW = POOL_SIZE * 2
POOL_TIMEOUT = 30
POOL_RECYCLE = 3600  # 1 hour
```

### **3. Async Optimization**
```python
# Use connection pooling for HTTP clients
import httpx

async_client = httpx.AsyncClient(
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
    timeout=httpx.Timeout(10.0)
)
```

## 🔒 **Security Pro Tips**

### **1. JWT Security**
```python
# Use short-lived access tokens + refresh tokens
ACCESS_TOKEN_EXPIRE = 15  # minutes
REFRESH_TOKEN_EXPIRE = 7  # days

# Implement token rotation
def rotate_refresh_token(old_token: str) -> str:
    # Invalidate old token and issue new one
```

### **2. API Rate Limiting**
```python
# Implement sliding window rate limiting
from redis import Redis
import time

class SlidingWindowRateLimit:
    def __init__(self, redis_client: Redis, window_size: int, max_requests: int):
        self.redis = redis_client
        self.window_size = window_size
        self.max_requests = max_requests
    
    async def is_allowed(self, key: str) -> bool:
        now = time.time()
        pipeline = self.redis.pipeline()
        pipeline.zremrangebyscore(key, 0, now - self.window_size)
        pipeline.zcard(key)
        pipeline.zadd(key, {str(now): now})
        pipeline.expire(key, self.window_size)
        results = pipeline.execute()
        
        return results[1] < self.max_requests
```

### **3. Input Validation**
```python
# Use Pydantic validators for strict validation
from pydantic import validator, Field

class UserCreate(BaseModel):
    email: str = Field(..., regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    password: str = Field(..., min_length=8, max_length=128)
    
    @validator('password')
    def validate_password_strength(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain digit')
        return v
```

## 📊 **Monitoring Pro Tips**

### **1. Custom Metrics**
```python
# Business metrics tracking
from prometheus_client import Counter, Histogram, Gauge

VERIFICATION_COUNTER = Counter('verifications_total', 'Total verifications', ['service', 'status'])
PAYMENT_HISTOGRAM = Histogram('payment_duration_seconds', 'Payment processing time')
ACTIVE_USERS_GAUGE = Gauge('active_users', 'Currently active users')

# Track business KPIs
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    
    # Track response times by endpoint
    endpoint = request.url.path
    REQUEST_DURATION.labels(endpoint=endpoint).observe(time.time() - start_time)
    
    return response
```

### **2. Distributed Tracing**
```python
# OpenTelemetry integration
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Setup tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)

span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Use in code
@tracer.start_as_current_span("create_verification")
async def create_verification(data: VerificationCreate):
    # Function implementation
```

### **3. Log Aggregation**
```python
# Structured logging with correlation IDs
import structlog
import uuid

def add_correlation_id(logger, method_name, event_dict):
    event_dict['correlation_id'] = str(uuid.uuid4())
    return event_dict

structlog.configure(
    processors=[
        add_correlation_id,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

## 🚀 **Deployment Pro Tips**

### **1. Blue-Green Deployment**
```bash
# Automated blue-green deployment script
#!/bin/bash
CURRENT_COLOR=$(kubectl get service namaskah-service -o jsonpath='{.spec.selector.version}')
NEW_COLOR=$([ "$CURRENT_COLOR" = "blue" ] && echo "green" || echo "blue")

# Deploy new version
kubectl set image deployment/namaskah-$NEW_COLOR app=namaskah:$NEW_VERSION

# Wait for rollout
kubectl rollout status deployment/namaskah-$NEW_COLOR

# Health check
if curl -f http://namaskah-$NEW_COLOR/health; then
    # Switch traffic
    kubectl patch service namaskah-service -p '{"spec":{"selector":{"version":"'$NEW_COLOR'"}}}'
    echo "Deployment successful: $NEW_COLOR"
else
    echo "Health check failed, rolling back"
    kubectl rollout undo deployment/namaskah-$NEW_COLOR
fi
```

### **2. Database Migration Strategy**
```python
# Zero-downtime migrations
class MigrationManager:
    async def migrate_with_rollback(self, migration_file: str):
        # Create backup
        backup_id = await self.create_backup()
        
        try:
            # Run migration
            await self.run_migration(migration_file)
            
            # Validate data integrity
            if not await self.validate_data_integrity():
                raise MigrationError("Data integrity check failed")
                
        except Exception as e:
            # Rollback on failure
            await self.restore_backup(backup_id)
            raise e
```

### **3. Feature Flag Implementation**
```python
# Advanced feature flags with gradual rollout
class FeatureFlag:
    def __init__(self, name: str, enabled: bool = False, rollout_percentage: int = 0):
        self.name = name
        self.enabled = enabled
        self.rollout_percentage = rollout_percentage
    
    def is_enabled_for_user(self, user_id: str) -> bool:
        if not self.enabled:
            return False
        
        # Use consistent hashing for gradual rollout
        user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        return (user_hash % 100) < self.rollout_percentage

# Usage
@app.get("/new-feature")
async def new_feature(request: Request):
    if not feature_flags.is_enabled_for_user("new_ui", request.state.user_id):
        raise HTTPException(404, "Feature not available")
    
    return {"message": "New feature enabled"}
```

## 🔧 **Troubleshooting Pro Tips**

### **1. Performance Debugging**
```python
# SQL query profiling
import time
from sqlalchemy import event

@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    if total > 0.1:  # Log slow queries
        logger.warning("Slow query", duration=total, query=statement[:100])
```

### **2. Memory Leak Detection**
```python
# Memory profiling
import psutil
import gc

@app.middleware("http")
async def memory_monitor(request: Request, call_next):
    process = psutil.Process()
    memory_before = process.memory_info().rss
    
    response = await call_next(request)
    
    memory_after = process.memory_info().rss
    memory_diff = memory_after - memory_before
    
    if memory_diff > 10 * 1024 * 1024:  # 10MB increase
        logger.warning("High memory usage", 
                      endpoint=request.url.path,
                      memory_increase=memory_diff)
        gc.collect()  # Force garbage collection
    
    return response
```

### **3. Circuit Breaker Pattern**
```python
# Advanced circuit breaker with metrics
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenError()
        
        try:
            result = await func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise e
    
    def on_success(self):
        self.failure_count = 0
        self.state = "CLOSED"
    
    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
```