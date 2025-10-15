#!/bin/bash

# PostgreSQL Setup Script for Namaskah SMS

echo "🔧 Setting up PostgreSQL for Namaskah SMS..."

# Create PostgreSQL user and database
sudo -u postgres psql <<EOF
CREATE USER namaskah_user WITH PASSWORD 'secure_password_here';
CREATE DATABASE namaskah_db OWNER namaskah_user;
GRANT ALL PRIVILEGES ON DATABASE namaskah_db TO namaskah_user;
\c namaskah_db
GRANT ALL ON SCHEMA public TO namaskah_user;
EOF

echo "✅ PostgreSQL database created!"
echo "📝 Update your .env file with:"
echo "DATABASE_URL=postgresql://namaskah_user:secure_password_here@localhost:5432/namaskah_db"
echo ""
echo "🚀 Run: python reset_db.py to initialize tables"
