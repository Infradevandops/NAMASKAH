"""Performance baseline and benchmarking for task 15.1."""
import asyncio
import time
import statistics
from typing import Dict, List, Any
from dataclasses import dataclass
import httpx


@dataclass
class PerformanceMetric:
    """Performance metric data point."""
    endpoint: str
    response_time: float
    status_code: int
    timestamp: float


class PerformanceBaseline:
    """Establish and track performance baselines."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.baseline_metrics = {}
        self.test_endpoints = [
            "/system/health",
            "/auth/login",
            "/verify/create", 
            "/wallet/balance",
            "/services/list"
        ]
    
    async def establish_baseline(self, iterations: int = 100) -> Dict[str, Any]:
        """Establish performance baseline for key endpoints."""
        print(f"Establishing baseline with {iterations} iterations...")
        
        baseline_results = {}
        
        for endpoint in self.test_endpoints:
            metrics = await self._benchmark_endpoint(endpoint, iterations)
            
            baseline_results[endpoint] = {
                "avg_response_time": statistics.mean(metrics),
                "p50_response_time": statistics.median(metrics),
                "p95_response_time": self._percentile(metrics, 95),
                "p99_response_time": self._percentile(metrics, 99),
                "min_response_time": min(metrics),
                "max_response_time": max(metrics),
                "iterations": iterations
            }
        
        self.baseline_metrics = baseline_results
        return baseline_results
    
    async def _benchmark_endpoint(self, endpoint: str, iterations: int) -> List[float]:
        """Benchmark single endpoint."""
        metrics = []
        
        async with httpx.AsyncClient() as client:
            for _ in range(iterations):
                start_time = time.time()
                
                try:
                    response = await client.get(f"{self.base_url}{endpoint}", timeout=10)
                    response_time = (time.time() - start_time) * 1000  # Convert to ms
                    metrics.append(response_time)
                except Exception:
                    # Record timeout as 10 seconds
                    metrics.append(10000)
                
                # Small delay between requests
                await asyncio.sleep(0.01)
        
        return metrics
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile."""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    async def run_regression_test(self) -> Dict[str, Any]:
        """Run performance regression test against baseline."""
        if not self.baseline_metrics:
            raise ValueError("No baseline established. Run establish_baseline() first.")
        
        print("Running performance regression test...")
        
        regression_results = {}
        
        for endpoint in self.test_endpoints:
            current_metrics = await self._benchmark_endpoint(endpoint, 50)
            current_avg = statistics.mean(current_metrics)
            baseline_avg = self.baseline_metrics[endpoint]["avg_response_time"]
            
            regression_percent = ((current_avg - baseline_avg) / baseline_avg) * 100
            
            regression_results[endpoint] = {
                "baseline_avg": baseline_avg,
                "current_avg": current_avg,
                "regression_percent": regression_percent,
                "passed": regression_percent < 25  # 25% regression threshold
            }
        
        return regression_results


class ContinuousPerformanceMonitor:
    """Continuous performance monitoring."""
    
    def __init__(self):
        self.performance_history = []
        self.alert_thresholds = {
            "response_time_p95": 2000,  # 2 seconds
            "error_rate": 5.0,          # 5%
            "throughput_min": 100       # 100 requests/minute
        }
    
    async def monitor_performance(self, duration_minutes: int = 60):
        """Monitor performance continuously."""
        print(f"Starting continuous monitoring for {duration_minutes} minutes...")
        
        end_time = time.time() + (duration_minutes * 60)
        
        while time.time() < end_time:
            # Collect metrics every minute
            metrics = await self._collect_current_metrics()
            self.performance_history.append(metrics)
            
            # Check for alerts
            if self._should_alert(metrics):
                await self._send_performance_alert(metrics)
            
            await asyncio.sleep(60)  # Wait 1 minute
        
        return self.performance_history
    
    async def _collect_current_metrics(self) -> Dict[str, Any]:
        """Collect current performance metrics."""
        # Simulate metrics collection
        return {
            "timestamp": time.time(),
            "response_time_p95": 150 + (time.time() % 100),  # Simulate variation
            "error_rate": 1.0 + (time.time() % 3),
            "throughput": 120 + (time.time() % 50),
            "active_connections": 25 + int(time.time() % 20)
        }
    
    def _should_alert(self, metrics: Dict[str, Any]) -> bool:
        """Check if metrics exceed alert thresholds."""
        return (
            metrics["response_time_p95"] > self.alert_thresholds["response_time_p95"] or
            metrics["error_rate"] > self.alert_thresholds["error_rate"] or
            metrics["throughput"] < self.alert_thresholds["throughput_min"]
        )
    
    async def _send_performance_alert(self, metrics: Dict[str, Any]):
        """Send performance alert."""
        print(f"PERFORMANCE ALERT: {metrics}")


async def run_performance_baseline():
    """Run complete performance baseline establishment."""
    baseline = PerformanceBaseline()
    
    # Establish baseline
    baseline_results = await baseline.establish_baseline(iterations=100)
    
    print("\n=== PERFORMANCE BASELINE ESTABLISHED ===")
    for endpoint, metrics in baseline_results.items():
        print(f"{endpoint}:")
        print(f"  Average: {metrics['avg_response_time']:.2f}ms")
        print(f"  P95: {metrics['p95_response_time']:.2f}ms")
        print(f"  P99: {metrics['p99_response_time']:.2f}ms")
    
    # Run regression test
    regression_results = await baseline.run_regression_test()
    
    print("\n=== REGRESSION TEST RESULTS ===")
    all_passed = True
    for endpoint, result in regression_results.items():
        status = "PASS" if result["passed"] else "FAIL"
        print(f"{endpoint}: {status} ({result['regression_percent']:+.1f}%)")
        if not result["passed"]:
            all_passed = False
    
    print(f"\nOverall: {'PASS' if all_passed else 'FAIL'}")
    return baseline_results, regression_results