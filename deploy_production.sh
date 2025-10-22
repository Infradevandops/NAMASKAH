#!/bin/bash
# Namaskah SMS Production Deployment Script

set -e

echo "🚀 Starting Namaskah SMS deployment..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
echo "🐍 Installing Python dependencies..."
sudo apt install -y python3 python3-pip python3-venv nginx supervisor

# Create application directory
APP_DIR="/opt/namaskah"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Copy application files
echo "📁 Copying application files..."
cp -r . $APP_DIR/
cd $APP_DIR

# Create virtual environment
echo "🔧 Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Set up environment
echo "⚙️ Setting up environment..."
cp .env.production.example .env.production
echo "Please edit .env.production with your actual values"

# Create systemd service
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/namaskah.service > /dev/null <<EOF
[Unit]
Description=Namaskah SMS Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/namaskah > /dev/null <<EOF
server {
    listen 80;
    server_name namaskah.app www.namaskah.app;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static/ {
        alias $APP_DIR/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/namaskah /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Enable and start services
echo "🔄 Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable namaskah
sudo systemctl start namaskah

# Install SSL certificate (Let's Encrypt)
echo "🔒 Installing SSL certificate..."
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d namaskah.app -d www.namaskah.app --non-interactive --agree-tos --email admin@namaskah.app

echo "✅ Deployment complete!"
echo "🌐 Your application is now running at https://namaskah.app"
echo "📊 Monitor at https://namaskah.app/monitoring"
