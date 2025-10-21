"""
Comprehensive Retry Mechanisms for Namaskah SMS
Implements exponential backoff, circuit breaker, and robust error handling
"""

import asyncio
import time
import random
import logging
from typing import Callable, Any, Optional, Dict, List
from functools import wraps
from datetime import datetime, timedelta, timezone
import requests
from enum import Enum

logger = logging.getLogger(__name__)

class RetryError(Exception):
    """Custom exception for retry failures"""
    pass

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class RetryConfig:
    """Configuration for retry mechanisms"""
    MAX_RETRIES = 3
    BASE_DELAY = 1.0
    MAX_DELAY = 30.0
    EXPONENTIAL_BASE = 2
    JITTER = True
    TIMEOUT = 30.0

class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    FAILURE_THRESHOLD = 5
    RECOVERY_TIMEOUT = 60.0
    SUCCESS_THRESHOLD = 3

class CircuitBreaker:
    """Circuit breaker implementation for API calls"""
    
    def __init__(self, config: CircuitBreakerConfig = None):
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        
    def can_execute(self) -> bool:
        """Check if request can be executed"""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def on_success(self):
        """Record successful execution"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.SUCCESS_THRESHOLD:
                self._reset()
        else:
            self.failure_count = 0
    
    def on_failure(self):
        """Record failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
        elif self.failure_count >= self.config.FAILURE_THRESHOLD:
            self.state = CircuitState.OPEN
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset"""
        return (time.time() - self.last_failure_time) >= self.config.RECOVERY_TIMEOUT
    
    def _reset(self):
        """Reset circuit breaker to closed state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

# Global circuit breakers for different services
circuit_breakers = {
    'textverified': CircuitBreaker(),
    'paystack': CircuitBreaker(),
    'database': CircuitBreaker()
}

def exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 30.0, 
                       exponential_base: float = 2, jitter: bool = True) -> float:
    """Calculate exponential backoff delay with optional jitter"""
    delay = min(base_delay * (exponential_base ** attempt), max_delay)
    
    if jitter:
        # Add random jitter (±25%)
        jitter_range = delay * 0.25
        delay += random.uniform(-jitter_range, jitter_range)
    
    return max(0, delay)

def is_retryable_error(exception: Exception) -> bool:
    """Determine if an error is retryable"""
    retryable_exceptions = (
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.HTTPError
    )
    
    if isinstance(exception, retryable_exceptions):
        return True
    
    # Check for specific HTTP status codes
    if isinstance(exception, requests.exceptions.HTTPError):
        status_code = exception.response.status_code if exception.response else 0
        # Retry on 5xx errors and some 4xx errors
        return status_code >= 500 or status_code in [408, 429]
    
    return False

def retry_with_backoff(
    max_retries: int = RetryConfig.MAX_RETRIES,
    base_delay: float = RetryConfig.BASE_DELAY,
    max_delay: float = RetryConfig.MAX_DELAY,
    exponential_base: float = RetryConfig.EXPONENTIAL_BASE,
    jitter: bool = RetryConfig.JITTER,
    circuit_breaker_key: Optional[str] = None
):
    """Decorator for retry with exponential backoff and circuit breaker"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            circuit_breaker = circuit_breakers.get(circuit_breaker_key) if circuit_breaker_key else None
            
            # Check circuit breaker
            if circuit_breaker and not circuit_breaker.can_execute():
                raise RetryError(f"Circuit breaker open for {circuit_breaker_key}")
            
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    
                    # Record success in circuit breaker
                    if circuit_breaker:
                        circuit_breaker.on_success()
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    # Record failure in circuit breaker
                    if circuit_breaker:
                        circuit_breaker.on_failure()
                    
                    # Don't retry on final attempt or non-retryable errors
                    if attempt == max_retries or not is_retryable_error(e):
                        break
                    
                    # Calculate delay and wait
                    delay = exponential_backoff(
                        attempt, base_delay, max_delay, exponential_base, jitter
                    )
                    
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    
                    time.sleep(delay)
            
            # All retries exhausted
            logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
            raise RetryError(f"Max retries exceeded: {last_exception}")
        
        return wrapper
    return decorator

async def async_retry_with_backoff(
    func: Callable,
    *args,
    max_retries: int = RetryConfig.MAX_RETRIES,
    base_delay: float = RetryConfig.BASE_DELAY,
    max_delay: float = RetryConfig.MAX_DELAY,
    exponential_base: float = RetryConfig.EXPONENTIAL_BASE,
    jitter: bool = RetryConfig.JITTER,
    circuit_breaker_key: Optional[str] = None,
    **kwargs
) -> Any:
    """Async version of retry with exponential backoff"""
    
    circuit_breaker = circuit_breakers.get(circuit_breaker_key) if circuit_breaker_key else None
    
    # Check circuit breaker
    if circuit_breaker and not circuit_breaker.can_execute():
        raise RetryError(f"Circuit breaker open for {circuit_breaker_key}")
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Record success in circuit breaker
            if circuit_breaker:
                circuit_breaker.on_success()
            
            return result
            
        except Exception as e:
            last_exception = e
            
            # Record failure in circuit breaker
            if circuit_breaker:
                circuit_breaker.on_failure()
            
            # Don't retry on final attempt or non-retryable errors
            if attempt == max_retries or not is_retryable_error(e):
                break
            
            # Calculate delay and wait
            delay = exponential_backoff(
                attempt, base_delay, max_delay, exponential_base, jitter
            )
            
            logger.warning(
                f"Async attempt {attempt + 1} failed for {func.__name__}: {e}. "
                f"Retrying in {delay:.2f}s"
            )
            
            await asyncio.sleep(delay)
    
    # All retries exhausted
    logger.error(f"All {max_retries + 1} async attempts failed for {func.__name__}")
    raise RetryError(f"Max retries exceeded: {last_exception}")

class PaymentRetryManager:
    """Specialized retry manager for payment operations"""
    
    RETRY_CONFIG = {
        'max_attempts': 5,
        'retry_delays': [1, 3, 10, 30, 120],  # seconds
        'retry_conditions': ['timeout', 'network_error', '5xx_error', 'rate_limit']
    }
    
    @classmethod
    def should_retry_payment(cls, exception: Exception, attempt: int) -> bool:
        """Determine if payment should be retried"""
        if attempt >= cls.RETRY_CONFIG['max_attempts']:
            return False
        
        # Check for retryable conditions
        if isinstance(exception, requests.exceptions.Timeout):
            return True
        
        if isinstance(exception, requests.exceptions.ConnectionError):
            return True
        
        if isinstance(exception, requests.exceptions.HTTPError):
            status_code = exception.response.status_code if exception.response else 0
            return status_code >= 500 or status_code == 429
        
        return False
    
    @classmethod
    def get_retry_delay(cls, attempt: int) -> float:
        """Get retry delay for payment attempt"""
        if attempt < len(cls.RETRY_CONFIG['retry_delays']):
            return cls.RETRY_CONFIG['retry_delays'][attempt]
        return cls.RETRY_CONFIG['retry_delays'][-1]

class SMSRetryManager:
    """Specialized retry manager for SMS retrieval"""
    
    RETRY_CONFIG = {
        'max_attempts': 10,
        'check_interval': 30,  # seconds
        'timeout': 300,        # 5 minutes total
        'exponential_backoff': True
    }
    
    @classmethod
    async def wait_for_sms(cls, verification_id: str, get_messages_func: Callable) -> List[str]:
        """Wait for SMS with retry logic"""
        start_time = time.time()
        attempt = 0
        
        while attempt < cls.RETRY_CONFIG['max_attempts']:
            try:
                messages = await async_retry_with_backoff(
                    get_messages_func,
                    verification_id,
                    max_retries=2,
                    circuit_breaker_key='textverified'
                )
                
                if messages:
                    return messages
                
                # Check timeout
                if time.time() - start_time > cls.RETRY_CONFIG['timeout']:
                    break
                
                # Calculate wait time
                if cls.RETRY_CONFIG['exponential_backoff']:
                    wait_time = exponential_backoff(attempt, cls.RETRY_CONFIG['check_interval'])
                else:
                    wait_time = cls.RETRY_CONFIG['check_interval']
                
                logger.info(f"No SMS yet for {verification_id}, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                
                attempt += 1
                
            except Exception as e:
                logger.error(f"SMS retrieval error for {verification_id}: {e}")
                break
        
        return []

class DatabaseRetryManager:
    """Specialized retry manager for database operations"""
    
    @staticmethod
    @retry_with_backoff(
        max_retries=3,
        base_delay=0.5,
        max_delay=5.0,
        circuit_breaker_key='database'
    )
    def execute_with_retry(db_operation: Callable, *args, **kwargs):
        """Execute database operation with retry"""
        return db_operation(*args, **kwargs)

# Health check functions
def check_service_health(service_name: str) -> Dict[str, Any]:
    """Check health of a service"""
    circuit_breaker = circuit_breakers.get(service_name)
    
    if not circuit_breaker:
        return {"status": "unknown", "message": "No circuit breaker configured"}
    
    return {
        "status": circuit_breaker.state.value,
        "failure_count": circuit_breaker.failure_count,
        "success_count": circuit_breaker.success_count,
        "last_failure": circuit_breaker.last_failure_time
    }

def reset_circuit_breaker(service_name: str) -> bool:
    """Manually reset a circuit breaker"""
    circuit_breaker = circuit_breakers.get(service_name)
    
    if circuit_breaker:
        circuit_breaker._reset()
        logger.info(f"Circuit breaker reset for {service_name}")
        return True
    
    return False

# Usage examples and decorators for common operations
@retry_with_backoff(circuit_breaker_key='textverified')
def textverified_api_call(method: str, url: str, **kwargs):
    """Make TextVerified API call with retry"""
    response = requests.request(method, url, timeout=30, **kwargs)
    response.raise_for_status()
    return response

@retry_with_backoff(circuit_breaker_key='paystack')
def paystack_api_call(method: str, url: str, **kwargs):
    """Make Paystack API call with retry"""
    response = requests.request(method, url, timeout=30, **kwargs)
    response.raise_for_status()
    return response

# Monitoring and metrics
class RetryMetrics:
    """Track retry metrics for monitoring"""
    
    def __init__(self):
        self.metrics = {
            'total_attempts': 0,
            'successful_retries': 0,
            'failed_retries': 0,
            'circuit_breaker_trips': 0
        }
    
    def record_attempt(self):
        self.metrics['total_attempts'] += 1
    
    def record_successful_retry(self):
        self.metrics['successful_retries'] += 1
    
    def record_failed_retry(self):
        self.metrics['failed_retries'] += 1
    
    def record_circuit_breaker_trip(self):
        self.metrics['circuit_breaker_trips'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics.copy()

# Global metrics instance
retry_metrics = RetryMetrics()