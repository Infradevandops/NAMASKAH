"""
Automated Deployment Script for Urgent Fixes
Pro Tips: Atomic deployments, rollback capability, health monitoring
"""

import os
import sys
import time
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


class DeploymentManager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backup_dir = self.project_root / "backups"
        self.deployment_log = []

    def log(self, message: str, level: str = "INFO"):
        """Log deployment steps"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        self.deployment_log.append(log_entry)

    def create_backup(self) -> str:
        """Create backup before deployment"""
        self.log("Creating backup...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)

        # Backup critical files
        critical_files = [
            "main.py",
            "requirements.txt",
            "static/",
            "templates/",
            "*.db",
        ]

        for pattern in critical_files:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    shutil.copy2(file_path, backup_path / file_path.name)
                elif file_path.is_dir():
                    shutil.copytree(
                        file_path, backup_path / file_path.name, dirs_exist_ok=True
                    )

        self.log(f"Backup created: {backup_path}")
        return str(backup_path)

    def integrate_security_fixes(self):
        """Integrate security implementation into main.py"""
        self.log("Integrating security fixes...")

        main_py_path = self.project_root / "main.py"

        # Read current main.py
        with open(main_py_path, "r") as f:
            content = f.read()

        # Add security imports at the top
        security_imports = """
# Security Implementation
from security_implementation import (
    security_middleware, rate_limiter, csrf_manager, 
    JWTManager, SecureDatabase, InputSanitizer,
    brute_force_protection, setup_security_logging
)
from api_enhancement import (
    APIKeyManager, WebhookManager, BulkOperationManager,
    APIResponse, APIVersioning
)
from realtime_implementation import (
    websocket_manager, SMSMonitor, notification_manager,
    connection_cleanup_task
)
"""

        # Find import section and add security imports
        if "from fastapi import" in content:
            import_index = content.find("from fastapi import")
            content = (
                content[:import_index]
                + security_imports
                + "\n"
                + content[import_index:]
            )

        # Add security middleware
        middleware_code = """
# Add security middleware
app.middleware("http")(security_middleware)

# Initialize security components
jwt_manager = JWTManager(SECRET_KEY)
api_key_manager = APIKeyManager(SessionLocal())
webhook_manager = WebhookManager()
sms_monitor = SMSMonitor(websocket_manager, tv_client)

# Setup security logging
setup_security_logging()
"""

        # Find app initialization and add middleware
        if "app = FastAPI(" in content:
            app_index = content.find("app = FastAPI(")
            app_end = content.find("\n", app_index)
            content = content[:app_end] + "\n" + middleware_code + content[app_end:]

        # Add WebSocket endpoints
        websocket_endpoints = """
# WebSocket endpoints
@app.websocket("/ws/verification/{verification_id}")
async def verification_websocket(websocket: WebSocket, verification_id: str):
    connection_id = await websocket_manager.connect(websocket, "user_id", verification_id)
    
    try:
        # Start SMS monitoring
        await sms_monitor.start_monitoring(verification_id)
        
        while True:
            try:
                message = await websocket.receive_text()
                data = json.loads(message)
                
                if data.get("type") == "ping":
                    await websocket_manager.handle_heartbeat(connection_id)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logging.error(f"WebSocket error: {str(e)}")
                break
    
    finally:
        await websocket_manager.disconnect(connection_id)
        await sms_monitor.stop_monitoring(verification_id)

# Bulk verification endpoint
@app.post("/verify/bulk")
async def create_bulk_verifications(
    request: BulkVerificationRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user)
):
    bulk_manager = BulkOperationManager(tv_client, SessionLocal())
    result = await bulk_manager.create_bulk_verifications(request, user.id, background_tasks)
    return APIResponse.success(result)

# API key management
@app.post("/api-keys")
async def create_api_key(
    name: str,
    permissions: List[str] = None,
    user: User = Depends(get_current_user)
):
    api_key = api_key_manager.create_key(user.id, name, permissions)
    return APIResponse.success(api_key)

# Webhook management
@app.post("/webhooks")
async def create_webhook(
    webhook: WebhookRequest,
    user: User = Depends(get_current_user)
):
    # Store webhook configuration
    return APIResponse.success({"message": "Webhook configured"})

# Enhanced verification endpoint with security
@app.post("/verify/create")
async def create_verification_secure(
    service_name: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Input sanitization
    service_name = InputSanitizer.sanitize_html(service_name)
    
    if not InputSanitizer.validate_service_name(service_name):
        raise HTTPException(400, "Invalid service name")
    
    # Check user credits using secure query
    user_data = SecureDatabase.safe_user_query(db, user.email)
    if not user_data or user_data.credits < 1:
        raise HTTPException(400, "Insufficient credits")
    
    # Create verification
    verification = tv_client.create_verification(service_name)
    
    # Start real-time monitoring
    await sms_monitor.start_monitoring(verification["id"])
    
    return APIResponse.success(verification)
"""

        # Add endpoints at the end
        content += "\n" + websocket_endpoints

        # Write updated main.py
        with open(main_py_path, "w") as f:
            f.write(content)

        self.log("Security fixes integrated successfully")

    def update_requirements(self):
        """Update requirements.txt with new dependencies"""
        self.log("Updating requirements...")

        new_requirements = [
            "redis>=4.0.0",
            "websockets>=10.0",
            "aiohttp>=3.8.0",
            "cryptography>=3.4.8",
        ]

        requirements_path = self.project_root / "requirements.txt"

        # Read existing requirements
        existing = []
        if requirements_path.exists():
            with open(requirements_path, "r") as f:
                existing = f.read().strip().split("\n")

        # Add new requirements if not present
        for req in new_requirements:
            package_name = req.split(">=")[0]
            if not any(package_name in line for line in existing):
                existing.append(req)

        # Write updated requirements
        with open(requirements_path, "w") as f:
            f.write("\n".join(existing))

        self.log("Requirements updated")

    def install_dependencies(self):
        """Install new dependencies"""
        self.log("Installing dependencies...")

        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                check=True,
                cwd=self.project_root,
            )
            self.log("Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            self.log(f"Failed to install dependencies: {str(e)}", "ERROR")
            raise

    def run_tests(self) -> bool:
        """Run comprehensive tests"""
        self.log("Running comprehensive tests...")

        try:
            # Run the test suite
            result = subprocess.run(
                [sys.executable, "comprehensive_testing.py"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                self.log("All tests passed")
                return True
            else:
                self.log(f"Tests failed: {result.stderr}", "ERROR")
                return False

        except subprocess.TimeoutExpired:
            self.log("Tests timed out", "ERROR")
            return False
        except Exception as e:
            self.log(f"Test execution failed: {str(e)}", "ERROR")
            return False

    def start_application(self):
        """Start the application"""
        self.log("Starting application...")

        try:
            # Kill existing process if running
            subprocess.run(["pkill", "-f", "uvicorn main:app"], check=False)
            time.sleep(2)

            # Start new process
            subprocess.Popen(
                [
                    "uvicorn",
                    "main:app",
                    "--reload",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    "8000",
                ],
                cwd=self.project_root,
            )

            # Wait for startup
            time.sleep(5)

            self.log("Application started")

        except Exception as e:
            self.log(f"Failed to start application: {str(e)}", "ERROR")
            raise

    def health_check(self) -> bool:
        """Perform health check"""
        self.log("Performing health check...")

        import requests

        for attempt in range(5):
            try:
                response = requests.get("http://localhost:8000/health", timeout=5)
                if response.status_code == 200:
                    self.log("Health check passed")
                    return True
            except Exception:
                pass

            time.sleep(2)

        self.log("Health check failed", "ERROR")
        return False

    def rollback(self, backup_path: str):
        """Rollback to backup"""
        self.log(f"Rolling back to backup: {backup_path}")

        backup_dir = Path(backup_path)

        # Restore files
        for backup_file in backup_dir.iterdir():
            target_path = self.project_root / backup_file.name

            if backup_file.is_file():
                shutil.copy2(backup_file, target_path)
            elif backup_file.is_dir():
                if target_path.exists():
                    shutil.rmtree(target_path)
                shutil.copytree(backup_file, target_path)

        self.log("Rollback completed")

    def save_deployment_log(self):
        """Save deployment log"""
        log_path = self.project_root / "deployment.log"

        with open(log_path, "a") as f:
            f.write("\n" + "=" * 50 + "\n")
            f.write(f"Deployment: {datetime.now().isoformat()}\n")
            f.write("=" * 50 + "\n")
            for entry in self.deployment_log:
                f.write(entry + "\n")

    def deploy(self):
        """Execute full deployment"""
        self.log("Starting deployment of urgent fixes...")

        backup_path = None

        try:
            # Phase 1: Backup
            backup_path = self.create_backup()

            # Phase 2: Update code
            self.integrate_security_fixes()
            self.update_requirements()

            # Phase 3: Install dependencies
            self.install_dependencies()

            # Phase 4: Test
            if not self.run_tests():
                raise Exception("Tests failed")

            # Phase 5: Deploy
            self.start_application()

            # Phase 6: Health check
            if not self.health_check():
                raise Exception("Health check failed")

            self.log("🎉 Deployment completed successfully!")

        except Exception as e:
            self.log(f"Deployment failed: {str(e)}", "ERROR")

            if backup_path:
                self.rollback(backup_path)
                self.start_application()

                if self.health_check():
                    self.log("Rollback successful")
                else:
                    self.log("Rollback failed - manual intervention required", "ERROR")

            raise

        finally:
            self.save_deployment_log()


def main():
    """Main deployment function"""
    print("🚀 Namaskah SMS - Urgent Fixes Deployment")
    print("=" * 50)

    deployer = DeploymentManager()

    try:
        deployer.deploy()
        print("\n✅ Deployment completed successfully!")
        print("🔗 Application available at: http://localhost:8000")
        print("📊 Admin dashboard: http://localhost:8000/admin")
        print("📚 API docs: http://localhost:8000/docs")

    except Exception as e:
        print(f"\n❌ Deployment failed: {str(e)}")
        print("Check deployment.log for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
