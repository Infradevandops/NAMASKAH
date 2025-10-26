"""Database migration utilities."""

import os
import subprocess
from typing import Optional
from sqlalchemy import text
from app.core.database import engine, get_db
from app.core.config import get_settings


class MigrationManager:
    """Database migration management."""

    def __init__(self):
        self.settings = get_settings()

    def run_migrations(self) -> bool:
        """Run pending migrations."""
        try:
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Migration failed: {e}")
            return False

    def create_migration(self, message: str) -> bool:
        """Create new migration."""
        try:
            result = subprocess.run(
                ["alembic", "revision", "--autogenerate", "-m", message],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Migration creation failed: {e}")
            return False

    def rollback_migration(self, revision: Optional[str] = None) -> bool:
        """Rollback to specific revision or previous."""
        try:
            target = revision or "-1"
            result = subprocess.run(
                ["alembic", "downgrade", target],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Rollback failed: {e}")
            return False

    def get_current_revision(self) -> Optional[str]:
        """Get current database revision."""
        try:
            result = subprocess.run(
                ["alembic", "current"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None

    def backup_database(self) -> bool:
        """Create database backup (SQLite only)."""
        if "sqlite" not in self.settings.database_url:
            print("Backup only supported for SQLite")
            return False

        try:
            import shutil
            from datetime import datetime

            db_path = self.settings.database_url.replace("sqlite:///", "")
            backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(db_path, backup_path)
            print(f"Database backed up to: {backup_path}")
            return True
        except Exception as e:
            print(f"Backup failed: {e}")
            return False

    def validate_schema(self) -> bool:
        """Validate database schema integrity."""
        try:
            with engine.connect() as conn:
                # Basic connectivity test
                conn.execute(text("SELECT 1"))

                # Check if all expected tables exist
                expected_tables = [
                    "users",
                    "verifications",
                    "transactions",
                    "api_keys",
                    "webhooks",
                    "service_status",
                    "support_tickets",
                ]

                for table in expected_tables:
                    result = conn.execute(
                        text(
                            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
                        )
                    )
                    if not result.fetchone():
                        print(f"Missing table: {table}")
                        return False

                return True
        except Exception as e:
            print(f"Schema validation failed: {e}")
            return False


# Global migration manager instance
migration_manager = MigrationManager()


def run_startup_migrations():
    """Run migrations on application startup."""
    try:
        if migration_manager.run_migrations():
            print("✅ Database migrations completed")
        else:
            print("⚠️ Database migrations failed")
    except Exception as e:
        print(f"⚠️ Migration startup error: {e}")
