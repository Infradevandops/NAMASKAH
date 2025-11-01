-- Create missing payment_logs table for Paystack integration
CREATE TABLE IF NOT EXISTS payment_logs (
    id VARCHAR PRIMARY KEY DEFAULT 'payment_log_' || extract(epoch from now())::text,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE,
    user_id VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    reference VARCHAR UNIQUE NOT NULL,
    amount_ngn FLOAT NOT NULL,
    amount_usd FLOAT NOT NULL,
    namaskah_amount FLOAT NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'initialized',
    payment_method VARCHAR NOT NULL DEFAULT 'paystack',
    webhook_received BOOLEAN DEFAULT FALSE,
    credited BOOLEAN DEFAULT FALSE,
    error_message TEXT
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS ix_payment_logs_user_id ON payment_logs(user_id);
CREATE INDEX IF NOT EXISTS ix_payment_logs_reference ON payment_logs(reference);
CREATE INDEX IF NOT EXISTS ix_payment_logs_status ON payment_logs(status);

-- Verify table exists
SELECT 
    schemaname,
    tablename 
FROM pg_tables 
WHERE schemaname = 'public' 
    AND tablename = 'payment_logs';