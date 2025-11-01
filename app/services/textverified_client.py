"""Production TextVerified API client with circuit breaker and health checks."""
import asyncio
import time
from typing import Dict, Any, Optional
from enum import Enum
import httpx
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class TextVerifiedClient:
    """Production-ready TextVerified API client with circuit breaker."""
    
    def __init__(self):
        self.api_key = settings.textverified_api_key
        self.base_url = "https://www.textverified.com/api"
        self.timeout = 30
        self.max_retries = 3
        
        # Circuit breaker configuration
        self.circuit_state = CircuitState.CLOSED
        self.failure_count = 0
        self.failure_threshold = 5
        self.recovery_timeout = 60
        self.last_failure_time = 0
        
        # Health check
        self.last_health_check = 0
        self.health_check_interval = 300  # 5 minutes
        self.is_healthy = True
        
    async def health_check(self) -> bool:
        """Check API health status."""
        current_time = time.time()
        if current_time - self.last_health_check < self.health_check_interval:
            return self.is_healthy
            
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/GetBalance",
                    params={"bearer": self.api_key}
                )
                self.is_healthy = response.status_code == 200
                if self.is_healthy:
                    self._reset_circuit()
                    
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            self.is_healthy = False
            
        self.last_health_check = current_time
        return self.is_healthy
        
    def _reset_circuit(self):
        """Reset circuit breaker to closed state."""
        self.circuit_state = CircuitState.CLOSED
        self.failure_count = 0
        
    def _record_failure(self):
        """Record API failure and update circuit state."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.circuit_state = CircuitState.OPEN
            logger.warning("Circuit breaker opened due to failures")
            
    def _can_attempt_request(self) -> bool:
        """Check if request can be attempted based on circuit state."""
        if self.circuit_state == CircuitState.CLOSED:
            return True
            
        if self.circuit_state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.circuit_state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker half-open, attempting recovery")
                return True
            return False
            
        return True  # HALF_OPEN
        
    async def make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make API request with circuit breaker protection."""
        if not self._can_attempt_request():
            logger.warning("Circuit breaker open, using fallback")
            return {"error": "Service temporarily unavailable"}
            
        if not await self.health_check():
            logger.warning("API unhealthy, using fallback")
            return {"error": "Service health check failed"}
            
        request_params = {"bearer": self.api_key}
        if params:
            request_params.update(params)
            
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(
                        f"{self.base_url}/{endpoint}",
                        params=request_params
                    )
                    
                    if response.status_code == 200:
                        if self.circuit_state == CircuitState.HALF_OPEN:
                            self._reset_circuit()
                        return response.json()
                        
                    elif response.status_code == 429:
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limited, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                        
                    else:
                        logger.error(f"API error: {response.status_code}")
                        self._record_failure()
                        break
                        
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    self._record_failure()
                    
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                self._record_failure()
                break
                
        return {"error": "API request failed after retries"}

# Global client instance
textverified_client = TextVerifiedClient()