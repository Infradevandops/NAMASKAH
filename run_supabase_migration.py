#!/usr/bin/env python3
"""Run Alembic migrations on Supabase production database"""

import os
import sys
from alembic.config import Config
from alembic import command

# Set environment to production
os.environ['ENVIRONMENT'] = 'production'
os.environ['DATABASE_URL'] = 'postgresql://postgres:ryskyx-8Padsa-timtabodh@db.oegyaxxlzmogrtgmhrcy.supabase.co:5432/postgres'

def run_migrations():
    """Run all pending migrations."""
    try:
        # Configure Alembic
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", os.environ['DATABASE_URL'])
        
        print("🔄 Running database migrations...")
        
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        
        print("✅ Migrations completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()