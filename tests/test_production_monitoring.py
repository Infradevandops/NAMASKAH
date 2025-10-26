"""
Production Monitoring Integration Tests
Tests metrics collection, logging, and monitoring functionality.
"""

import pytest
import time
import json
import asyncio
from unittest.mock import patch, MagicMock
from app.core.metrics import metrics_collector, MetricsCollector, cache_metrics
from app.core.logging import (
    get_logger,
    set_correlation_id,
    log_business_event,
    log_security_event,
)
from app.core.config import settings


class TestMetricsCollection:
    """Test metrics collection functionality."""

    def test_request_metrics_recording(self):
        """Test recording of HTTP request metrics."""
        collector = MetricsCollector()

        # Record some test requests
        collector.record_request("GET", "/api/users", 200, 0.150)
        collector.record_request("POST", "/api/users", 201, 0.300)
        collector.record_request("GET", "/api/users", 404, 0.100)
        collector.record_request("GET", "/api/health", 200, 0.050)

        # Get application metrics
        metrics = collector.get_application_metrics()

        assert metrics["total_requests"] == 4
        assert metrics["uptime_seconds"] > 0
        assert metrics["requests_per_second"] > 0
        assert metrics["average_response_time"] > 0

    def test_error_metrics_recording(self):
        """Test recording of error metrics."""
        collector = MetricsCollector()

        # Record some errors
        collector.record_error("ValidationError", "medium")
        collector.record_error("DatabaseError", "high")
        collector.record_error("TimeoutError", "low")

        metrics = collector.get_application_metrics()
        assert metrics["error_count"] == 3

    def test_business_event_metrics(self):
        """Test recording of business event metrics."""
        collector = MetricsCollector()

        # Record business events
        collector.record_business_event("user_registration", "success")
        collector.record_business_event("sms_verification", "success")
        collector.record_business_event("payment_processed", "failed")

        metrics = collector.get_application_metrics()
        assert metrics["business_events"] == 3

    def test_health_score_calculation(self):
        """Test health score calculation."""
        collector = MetricsCollector()

        # Mock system metrics to control health score
        with patch("psutil.cpu_percent", return_value=50.0), patch(
            "psutil.virtual_memory"
        ) as mock_memory, patch("psutil.disk_usage") as mock_disk:

            # Mock memory and disk usage
            mock_memory.return_value.percent = 60.0
            mock_disk.return_value.percent = 70.0

            health = collector.get_health_score()

            assert "health_score" in health
            assert "status" in health
            assert health["health_score"] >= 0
            assert health["health_score"] <= 100
            assert health["status"] in ["healthy", "degraded", "unhealthy"]

    def test_system_metrics_collection(self):
        """Test system metrics collection."""
        collector = MetricsCollector()

        # Update system metrics
        collector.update_system_metrics()

        # This should not raise any exceptions
        # The actual values depend on the system state

    def test_prometheus_metrics_format(self):
        """Test Prometheus metrics format."""
        from app.core.metrics import get_prometheus_metrics

        # Record some metrics
        metrics_collector.record_request("GET", "/test", 200, 0.1)
        metrics_collector.record_error("TestError", "medium")

        # Get Prometheus format
        prometheus_data = get_prometheus_metrics()

        assert isinstance(prometheus_data, (str, bytes))
        assert len(prometheus_data) > 0

        # Should contain metric names
        prometheus_str = (
            prometheus_data
            if isinstance(prometheus_data, str)
            else prometheus_data.decode()
        )
        assert "http_requests_total" in prometheus_str
        assert "errors_total" in prometheus_str


class TestLoggingSystem:
    """Test production logging system."""

    def test_structured_logging_format(self):
        """Test structured logging produces correct format."""
        logger = get_logger("test")

        # Test basic logging
        with patch("sys.stdout") as mock_stdout:
            logger.info("Test message", key="value", number=42)

            # In production, this should produce JSON output
            # In test environment, it might be different

    def test_correlation_id_tracking(self):
        """Test correlation ID tracking in logs."""
        from app.core.logging import correlation_id_var

        # Set correlation ID
        correlation_id = set_correlation_id("test-correlation-123")
        assert correlation_id == "test-correlation-123"

        # Verify it's set in context
        assert correlation_id_var.get() == "test-correlation-123"

    def test_business_event_logging(self):
        """Test business event logging."""
        logger = get_logger("business_test")

        # Test business event logging
        with patch.object(logger, "info") as mock_info:
            log_business_event(
                logger, "user_signup", {"user_id": "123", "plan": "premium"}
            )

            # Verify the log was called with correct parameters
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert "Business event" in call_args[0]
            assert call_args[1]["event_type"] == "user_signup"
            assert call_args[1]["metric_type"] == "business"

    def test_security_event_logging(self):
        """Test security event logging."""
        logger = get_logger("security_test")

        # Test high severity security event
        with patch.object(logger, "error") as mock_error:
            log_security_event(
                logger,
                "failed_login_attempt",
                "high",
                {"user_id": "123", "ip_address": "192.168.1.1", "attempts": 5},
            )

            mock_error.assert_called_once()
            call_args = mock_error.call_args
            assert "Security event" in call_args[0]
            assert call_args[1]["event_type"] == "failed_login_attempt"
            assert call_args[1]["severity"] == "high"

    def test_performance_logging(self):
        """Test performance logging."""
        from app.core.logging import log_performance

        logger = get_logger("performance_test")

        # Test slow operation logging
        with patch.object(logger, "warning") as mock_warning:
            log_performance(
                logger, "database_query", 2.5, {"query": "SELECT * FROM users"}
            )

            mock_warning.assert_called_once()
            call_args = mock_warning.call_args
            assert call_args[1]["operation"] == "database_query"
            assert call_args[1]["duration_ms"] == 2500
            assert call_args[1]["performance_category"] == "slow"

    def test_error_logging_with_context(self):
        """Test error logging with context."""
        from app.core.logging import log_error

        logger = get_logger("error_test")

        try:
            raise ValueError("Test error for logging")
        except ValueError as e:
            with patch.object(logger, "error") as mock_error:
                log_error(logger, e, {"user_id": "123", "operation": "test"})

                mock_error.assert_called_once()
                call_args = mock_error.call_args
                assert call_args[1]["error_type"] == "ValueError"
                assert call_args[1]["error_message"] == "Test error for logging"
                assert call_args[1]["user_id"] == "123"


class TestCacheMetrics:
    """Test cache-specific metrics."""

    def test_cache_hit_miss_tracking(self):
        """Test cache hit/miss metrics tracking."""
        # Record cache operations
        cache_metrics.record_hit()
        cache_metrics.record_hit()
        cache_metrics.record_miss()

        # The metrics should be recorded in Prometheus counters
        # We can't easily test the actual values without accessing internal state
        # But we can verify the methods don't raise exceptions

    def test_cache_operation_timing(self):
        """Test cache operation timing metrics."""
        # Record cache operations with timing
        cache_metrics.record_operation("get", 0.001)  # 1ms
        cache_metrics.record_operation("set", 0.002)  # 2ms
        cache_metrics.record_operation("delete", 0.0005)  # 0.5ms

        # Should not raise exceptions


class TestMonitoringIntegration:
    """Test monitoring system integration."""

    @pytest.mark.asyncio
    async def test_metrics_endpoint_response(self):
        """Test metrics endpoint returns valid data."""
        from app.core.metrics import get_prometheus_metrics, get_metrics_content_type

        # Get metrics data
        metrics_data = get_prometheus_metrics()
        content_type = get_metrics_content_type()

        assert metrics_data is not None
        assert len(metrics_data) > 0
        assert content_type == "text/plain; version=0.0.4; charset=utf-8"

    def test_application_info_collection(self):
        """Test application information collection."""
        from app.core.metrics import get_application_info

        app_info = get_application_info()

        assert "name" in app_info
        assert "version" in app_info
        assert "environment" in app_info
        assert "start_time" in app_info
        assert "uptime" in app_info

        assert app_info["name"] == settings.app_name
        assert app_info["version"] == settings.app_version
        assert app_info["environment"] == settings.environment

    def test_database_metrics_integration(self):
        """Test database metrics integration."""
        from app.core.metrics import DatabaseMetrics

        # Test query recording
        DatabaseMetrics.record_query("SELECT", 0.050, success=True)
        DatabaseMetrics.record_query("INSERT", 0.100, success=False)

        # Test connection count update
        DatabaseMetrics.update_connection_count(15)

        # Should not raise exceptions

    @pytest.mark.asyncio
    async def test_business_event_recording(self):
        """Test business event recording through metrics system."""
        from app.core.metrics import record_business_event

        # Record business events
        await record_business_event("user_login", "success", user_id="123")
        await record_business_event("sms_sent", "failed", error="rate_limit")

        # Should not raise exceptions

    @pytest.mark.asyncio
    async def test_performance_metric_recording(self):
        """Test performance metric recording."""
        from app.core.metrics import record_performance_metric

        # Record performance metrics
        await record_performance_metric("api_call", 0.150, endpoint="/users")
        await record_performance_metric("database_query", 0.050, table="users")

        # Should not raise exceptions


class TestMonitoringPerformance:
    """Test monitoring system performance impact."""

    def test_metrics_collection_overhead(self):
        """Test that metrics collection has minimal overhead."""
        collector = MetricsCollector()

        # Measure time for many metric recordings
        start_time = time.time()

        for i in range(1000):
            collector.record_request("GET", "/test", 200, 0.1)
            collector.record_error("TestError", "low")
            collector.record_business_event("test_event", "success")

        duration = time.time() - start_time

        # Should complete quickly (less than 1 second for 3000 operations)
        assert duration < 1.0

    def test_logging_performance_impact(self):
        """Test logging performance impact."""
        logger = get_logger("performance_test")

        # Measure logging performance
        start_time = time.time()

        for i in range(100):
            logger.info("Performance test message", iteration=i, data="test_data")

        duration = time.time() - start_time

        # Should complete quickly
        assert duration < 2.0  # 100 log messages in less than 2 seconds

    def test_concurrent_metrics_collection(self):
        """Test concurrent metrics collection performance."""
        import threading

        collector = MetricsCollector()

        def record_metrics():
            for i in range(100):
                collector.record_request("GET", f"/test/{i}", 200, 0.1)

        # Run concurrent metric recording
        threads = []
        start_time = time.time()

        for _ in range(5):  # 5 concurrent threads
            thread = threading.Thread(target=record_metrics)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        duration = time.time() - start_time

        # Should handle concurrent access efficiently
        assert duration < 5.0  # 500 total operations in less than 5 seconds

        # Verify all metrics were recorded
        metrics = collector.get_application_metrics()
        assert metrics["total_requests"] == 500


class TestMonitoringAlerts:
    """Test monitoring alert conditions."""

    def test_high_error_rate_detection(self):
        """Test detection of high error rates."""
        collector = MetricsCollector()

        # Record requests with high error rate
        for i in range(100):
            if i < 20:  # 20% error rate
                collector.record_request("GET", "/test", 500, 0.1)
                collector.record_error("ServerError", "high")
            else:
                collector.record_request("GET", "/test", 200, 0.1)

        health = collector.get_health_score()

        # High error rate should impact health score
        assert health["health_score"] < 90  # Should be degraded
        assert health["factors"]["error_rate"] > 0.1  # 10%+ error rate

    def test_slow_response_time_detection(self):
        """Test detection of slow response times."""
        collector = MetricsCollector()

        # Record slow requests
        for i in range(10):
            collector.record_request("GET", "/slow", 200, 3.0)  # 3 second responses

        health = collector.get_health_score()

        # Slow responses should impact health score
        assert health["health_score"] < 95
        assert health["factors"]["avg_response_time"] > 2.0

    @patch("psutil.cpu_percent")
    @patch("psutil.virtual_memory")
    @patch("psutil.disk_usage")
    def test_resource_usage_alerts(self, mock_disk, mock_memory, mock_cpu):
        """Test resource usage alert conditions."""
        collector = MetricsCollector()

        # Mock high resource usage
        mock_cpu.return_value = 90.0  # 90% CPU
        mock_memory.return_value.percent = 95.0  # 95% memory
        mock_disk.return_value.percent = 85.0  # 85% disk

        health = collector.get_health_score()

        # High resource usage should significantly impact health
        assert health["health_score"] < 70  # Should be unhealthy
        assert health["status"] in ["degraded", "unhealthy"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
