"""Blue-green deployment system for task 13.3."""

import asyncio
import time
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class DeploymentConfig:
    """Deployment configuration."""

    app_name: str
    blue_version: str
    green_version: str
    health_check_url: str
    rollout_stages: List[int] = None

    def __post_init__(self):
        if self.rollout_stages is None:
            self.rollout_stages = [1, 10, 50, 100]


class BlueGreenDeployment:
    """Blue-green deployment manager."""

    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.current_traffic = {"blue": 100, "green": 0}
        self.metrics = {"error_rate": 0, "response_time": 0}

    async def deploy_green(self) -> bool:
        """Deploy green version."""
        print(f"Deploying green version: {self.config.green_version}")

        # Simulate deployment
        await asyncio.sleep(2)

        # Health check
        if await self._health_check("green"):
            print("Green deployment healthy")
            return True
        else:
            print("Green deployment failed health check")
            return False

    async def gradual_rollout(self) -> bool:
        """Perform gradual traffic rollout."""
        for stage in self.config.rollout_stages:
            print(f"Rolling out {stage}% traffic to green")

            # Update traffic split
            self.current_traffic = {"blue": 100 - stage, "green": stage}

            # Monitor metrics
            await asyncio.sleep(5)  # Wait for metrics

            if not await self._validate_metrics():
                print(f"Metrics validation failed at {stage}%")
                await self._rollback()
                return False

            print(f"Stage {stage}% successful")

        print("Gradual rollout completed successfully")
        return True

    async def _health_check(self, version: str) -> bool:
        """Check health of specific version."""
        try:
            import httpx

            url = f"{self.config.health_check_url}?version={version}"
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10)
                return response.status_code == 200
        except Exception:
            return False

    async def _validate_metrics(self) -> bool:
        """Validate deployment metrics."""
        # Simulate metrics collection
        await asyncio.sleep(1)

        # Check error rate threshold
        if self.metrics["error_rate"] > 5.0:  # 5% error rate threshold
            return False

        # Check response time threshold
        if self.metrics["response_time"] > 2000:  # 2s response time threshold
            return False

        return True

    async def _rollback(self):
        """Rollback to blue version."""
        print("Rolling back to blue version")
        self.current_traffic = {"blue": 100, "green": 0}
        await asyncio.sleep(1)
        print("Rollback completed")


class ABTestingFramework:
    """A/B testing framework for deployment validation."""

    def __init__(self):
        self.experiments = {}

    def create_experiment(self, name: str, traffic_split: Dict[str, int]):
        """Create A/B test experiment."""
        self.experiments[name] = {
            "traffic_split": traffic_split,
            "metrics": {"conversion_rate": 0, "error_rate": 0},
            "start_time": time.time(),
        }

    async def run_experiment(self, name: str, duration: int = 300) -> Dict:
        """Run A/B test experiment."""
        if name not in self.experiments:
            raise ValueError(f"Experiment {name} not found")

        experiment = self.experiments[name]

        # Simulate experiment running
        await asyncio.sleep(min(duration, 10))  # Simulate for testing

        # Collect results
        results = {
            "experiment": name,
            "duration": time.time() - experiment["start_time"],
            "traffic_split": experiment["traffic_split"],
            "metrics": experiment["metrics"],
            "winner": (
                "blue" if experiment["metrics"]["conversion_rate"] > 0.5 else "green"
            ),
        }

        return results


async def automated_deployment(config: DeploymentConfig) -> bool:
    """Automated blue-green deployment with validation."""
    deployment = BlueGreenDeployment(config)

    # Step 1: Deploy green version
    if not await deployment.deploy_green():
        return False

    # Step 2: Run A/B test
    ab_test = ABTestingFramework()
    ab_test.create_experiment("deployment_validation", {"blue": 50, "green": 50})

    test_results = await ab_test.run_experiment("deployment_validation", duration=60)

    if test_results["winner"] != "green":
        print("A/B test failed, keeping blue version")
        return False

    # Step 3: Gradual rollout
    success = await deployment.gradual_rollout()

    if success:
        print("Deployment completed successfully")
    else:
        print("Deployment failed, rolled back to blue")

    return success
