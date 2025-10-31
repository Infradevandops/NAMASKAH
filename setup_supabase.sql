-- Setup Supabase database for Namaskah SMS
-- Run this in Supabase SQL Editor

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    email_verified BOOLEAN DEFAULT false,
    credits FLOAT DEFAULT 0.0,
    free_verifications FLOAT DEFAULT 1.0,
    verification_token VARCHAR(255),
    reset_token VARCHAR(255),
    reset_token_expires TIMESTAMPTZ,
    referral_code VARCHAR(50) UNIQUE,
    referred_by VARCHAR(255),
    referral_earnings FLOAT DEFAULT 0.0
);

-- API Keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id VARCHAR PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    user_id VARCHAR NOT NULL REFERENCES users(id),
    key VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    last_used TIMESTAMPTZ
);

-- Verifications table
CREATE TABLE IF NOT EXISTS verifications (
    id VARCHAR PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    user_id VARCHAR NOT NULL REFERENCES users(id),
    service_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20),
    capability VARCHAR(10),
    status VARCHAR(20),
    verification_code VARCHAR(20),
    cost FLOAT NOT NULL,
    call_duration FLOAT,
    transcription TEXT,
    audio_url VARCHAR,
    requested_carrier VARCHAR(50),
    requested_area_code VARCHAR(10),
    completed_at TIMESTAMPTZ
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id VARCHAR PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    user_id VARCHAR NOT NULL REFERENCES users(id),
    amount FLOAT NOT NULL,
    type VARCHAR(10) NOT NULL,
    description VARCHAR(255)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_users_referral_code ON users(referral_code);
CREATE INDEX IF NOT EXISTS ix_api_keys_key ON api_keys(key);
CREATE INDEX IF NOT EXISTS ix_verifications_service_name ON verifications(service_name);
CREATE INDEX IF NOT EXISTS ix_verifications_status ON verifications(status);
CREATE INDEX IF NOT EXISTS ix_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS ix_transactions_type ON transactions(type);

-- Create admin user
INSERT INTO users (
    id, email, password_hash, credits, free_verifications,
    is_admin, email_verified, referral_code
) VALUES (
    'admin_' || substr(md5(random()::text), 1, 16),
    'admin@namaskah.app',
    '$pbkdf2-sha256$100000$' || encode(gen_random_bytes(32), 'hex') || '$' || encode(gen_random_bytes(32), 'hex'),
    1000.0,
    10.0,
    true,
    true,
    'admin_' || substr(md5(random()::text), 1, 6)
) ON CONFLICT (email) DO UPDATE SET
    is_admin = true,
    email_verified = true,
    credits = GREATEST(users.credits, 1000.0);

-- Verify setup
SELECT 'Setup complete!' as status;
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;