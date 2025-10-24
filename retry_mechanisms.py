# Retry Mechanisms and Circuit Breaker Module
import time
import functools
import requests
import asyncio
from datetime import datetime, timedelta

# Circuit breaker state
circuit_breakers = {}


def retry_with_backoff(max_retries=3, backoff_factor=1, circuit_breaker_key=None):
    """Decorator for retry with exponential backoff"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if circuit_breaker_key and is_circuit_open(circuit_breaker_key):
                raise Exception(f"Circuit breaker open for {circuit_breaker_key}")

            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    if circuit_breaker_key:
                        record_success(circuit_breaker_key)
                    return result
                except Exception as e:
                    if circuit_breaker_key:
                        record_failure(circuit_breaker_key)

                    if attempt == max_retries:
                        raise e

                    wait_time = backoff_factor * (2**attempt)
                    time.sleep(wait_time)

        return wrapper

    return decorator


async def async_retry_with_backoff(
    max_retries=3, backoff_factor=1, circuit_breaker_key=None
):
    """Async version of retry decorator"""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if circuit_breaker_key and is_circuit_open(circuit_breaker_key):
                raise Exception(f"Circuit breaker open for {circuit_breaker_key}")

            for attempt in range(max_retries + 1):
                try:
                    result = await func(*args, **kwargs)
                    if circuit_breaker_key:
                        record_success(circuit_breaker_key)
                    return result
                except Exception as e:
                    if circuit_breaker_key:
                        record_failure(circuit_breaker_key)

                    if attempt == max_retries:
                        raise e

                    wait_time = backoff_factor * (2**attempt)
                    await asyncio.sleep(wait_time)

        return wrapper

    return decorator


def is_circuit_open(key):
    """Check if circuit breaker is open"""
    if key not in circuit_breakers:
        return False

    breaker = circuit_breakers[key]
    if breaker["state"] == "open":
        if datetime.now() > breaker["next_attempt"]:
            breaker["state"] = "half_open"
            return False
        return True

    return False


def record_success(key):
    """Record successful operation"""
    if key in circuit_breakers:
        circuit_breakers[key] = {"state": "closed", "failures": 0, "next_attempt": None}


def record_failure(key):
    """Record failed operation"""
    if key not in circuit_breakers:
        circuit_breakers[key] = {"state": "closed", "failures": 0, "next_attempt": None}

    breaker = circuit_breakers[key]
    breaker["failures"] += 1

    if breaker["failures"] >= 5:  # Threshold
        breaker["state"] = "open"
        breaker["next_attempt"] = datetime.now() + timedelta(minutes=5)


def check_service_health(service_name):
    """Check service health status"""
    if service_name not in circuit_breakers:
        return {"status": "closed", "failures": 0}

    breaker = circuit_breakers[service_name]
    return {
        "status": breaker["state"],
        "failures": breaker["failures"],
        "next_attempt": (
            breaker["next_attempt"].isoformat() if breaker["next_attempt"] else None
        ),
    }


def reset_circuit_breaker(service_name):
    """Manually reset circuit breaker"""
    if service_name in circuit_breakers:
        circuit_breakers[service_name] = {
            "state": "closed",
            "failures": 0,
            "next_attempt": None,
        }
        return True
    return False


class PaymentRetryManager:
    """Manage payment retry logic"""

    @staticmethod
    def should_retry(error_code):
        retry_codes = ["network_error", "timeout", "server_error"]
        return error_code in retry_codes


class SMSRetryManager:
    """Manage SMS retry logic"""

    @staticmethod
    def should_retry(status_code):
        return status_code in [500, 502, 503, 504]


class DatabaseRetryManager:
    """Manage database retry logic"""

    @staticmethod
    def should_retry(exception):
        return "connection" in str(exception).lower()


def textverified_api_call(method, url, **kwargs):
    """Make API call to TextVerified with retry"""
    response = requests.request(method, url, timeout=10, **kwargs)
    response.raise_for_status()
    return response


def paystack_api_call(method, url, **kwargs):
    """Make API call to Paystack with retry"""
    response = requests.request(method, url, timeout=10, **kwargs)
    response.raise_for_status()
    return response
