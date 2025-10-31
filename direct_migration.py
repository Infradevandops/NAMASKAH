#!/usr/bin/env python3
"""Direct database migration without app dependencies"""

from sqlalchemy import create_engine, text
import sys

DATABASE_URL = "postgresql://postgres:ryskyx-8Padsa-timtabodh@db.oegyaxxlzmogrtgmhrcy.supabase.co:5432/postgres"

def run_direct_migration():
    """Create missing tables directly."""
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            print("🔄 Creating missing tables...")
            
            # Create support_tickets table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS support_tickets (
                    id VARCHAR PRIMARY KEY DEFAULT 'ticket_' || extract(epoch from now())::text,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                    updated_at TIMESTAMP WITH TIME ZONE,
                    user_id VARCHAR,
                    name VARCHAR NOT NULL,
                    email VARCHAR NOT NULL,
                    category VARCHAR NOT NULL,
                    message TEXT NOT NULL,
                    status VARCHAR NOT NULL DEFAULT 'open',
                    admin_response TEXT
                );
            """))
            
            # Create service_status table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS service_status (
                    id VARCHAR PRIMARY KEY DEFAULT 'status_' || extract(epoch from now())::text,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                    updated_at TIMESTAMP WITH TIME ZONE,
                    service_name VARCHAR NOT NULL,
                    status VARCHAR NOT NULL DEFAULT 'operational',
                    success_rate FLOAT NOT NULL DEFAULT 100.0,
                    last_checked TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
                );
            """))
            
            # Create indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_tickets_status ON support_tickets(status);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_service_status_service_name ON service_status(service_name);"))
            
            conn.commit()
            
        print("✅ Tables created successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_direct_migration()