#!/usr/bin/env python3
"""
PostgreSQL Migration Script
Migrates data from SQLite to PostgreSQL for production readiness.
"""
import os
import sys
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.config import settings
from app.models import Base


async def migrate_to_postgresql():
    """Migrate from SQLite to PostgreSQL."""

    print("🚀 Starting PostgreSQL Migration...")

    # Check if PostgreSQL is configured
    if "postgresql" not in settings.database_url:
        print("❌ DATABASE_URL must be configured for PostgreSQL")
        print(
            "   Update .env file with: DATABASE_URL=postgresql://user:pass@host:5432/db"
        )
        return False

    try:
        # Create PostgreSQL engine
        pg_engine = create_engine(settings.database_url)

        # Test connection
        with pg_engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL: {version}")

        # Create all tables
        print("📋 Creating database tables...")
        Base.metadata.create_all(bind=pg_engine)
        print("✅ Tables created successfully")

        # Run Alembic migrations
        print("🔄 Running Alembic migrations...")
        os.system("alembic upgrade head")
        print("✅ Migrations completed")

        print("🎉 PostgreSQL migration completed successfully!")
        print("📊 Next steps:")
        print("   1. Start your application: uvicorn main:app --reload")
        print("   2. Test database connectivity")
        print("   3. Verify all endpoints are working")

        return True

    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        print("💡 Troubleshooting:")
        print("   1. Ensure PostgreSQL is running")
        print("   2. Check DATABASE_URL in .env file")
        print("   3. Verify database credentials")
        return False


if __name__ == "__main__":
    success = asyncio.run(migrate_to_postgresql())
    sys.exit(0 if success else 1)
