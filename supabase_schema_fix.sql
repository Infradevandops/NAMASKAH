-- Fix Supabase database schema for production
-- Run this in Supabase SQL Editor

-- Create support_tickets table
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

-- Create service_status table  
CREATE TABLE IF NOT EXISTS service_status (
    id VARCHAR PRIMARY KEY DEFAULT 'status_' || extract(epoch from now())::text,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE,
    service_name VARCHAR NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'operational',
    success_rate FLOAT NOT NULL DEFAULT 100.0,
    last_checked TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create verifications table if missing
CREATE TABLE IF NOT EXISTS verifications (
    id VARCHAR PRIMARY KEY DEFAULT 'verify_' || extract(epoch from now())::text,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE,
    user_id VARCHAR NOT NULL REFERENCES users(id),
    service_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20),
    capability VARCHAR(10),
    status VARCHAR(20) DEFAULT 'pending',
    verification_code VARCHAR(20),
    cost FLOAT NOT NULL DEFAULT 0.0,
    call_duration FLOAT,
    transcription TEXT,
    audio_url VARCHAR,
    requested_carrier VARCHAR(50),
    requested_area_code VARCHAR(10),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Create transactions table if missing
CREATE TABLE IF NOT EXISTS transactions (
    id VARCHAR PRIMARY KEY DEFAULT 'txn_' || extract(epoch from now())::text,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE,
    user_id VARCHAR NOT NULL REFERENCES users(id),
    amount FLOAT NOT NULL,
    type VARCHAR(10) NOT NULL,
    description VARCHAR(255)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS ix_support_tickets_status ON support_tickets(status);
CREATE INDEX IF NOT EXISTS ix_support_tickets_user_id ON support_tickets(user_id);
CREATE INDEX IF NOT EXISTS ix_service_status_service_name ON service_status(service_name);
CREATE INDEX IF NOT EXISTS ix_verifications_status ON verifications(status);
CREATE INDEX IF NOT EXISTS ix_verifications_user_id ON verifications(user_id);
CREATE INDEX IF NOT EXISTS ix_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS ix_transactions_type ON transactions(type);

-- Verify tables exist
SELECT 
    schemaname,
    tablename 
FROM pg_tables 
WHERE schemaname = 'public' 
    AND tablename IN ('users', 'verifications', 'transactions', 'support_tickets', 'service_status')
ORDER BY tablename;