-- Complete payment system database setup

-- Verify payment_logs table exists
SELECT 'payment_logs table' as table_name, COUNT(*) as exists 
FROM information_schema.tables 
WHERE table_name = 'payment_logs';

-- Create transactions table if missing
CREATE TABLE IF NOT EXISTS transactions (
    id VARCHAR PRIMARY KEY DEFAULT 'txn_' || extract(epoch from now())::text,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE,
    user_id VARCHAR NOT NULL,
    amount FLOAT NOT NULL,
    type VARCHAR(10) NOT NULL,
    description VARCHAR(255)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS ix_transactions_type ON transactions(type);

-- Verify all payment tables exist
SELECT 
    schemaname,
    tablename 
FROM pg_tables 
WHERE schemaname = 'public' 
    AND tablename IN ('payment_logs', 'transactions')
ORDER BY tablename;