#!/bin/bash
# SSL Certificate Setup and Management Script
# Supports Let's Encrypt and custom certificates

set -e

# Configuration
DOMAIN="${DOMAIN:-api.namaskah.app}"
EMAIL="${EMAIL:-admin@namaskah.app}"
CERT_PATH="/etc/ssl/certs"
KEY_PATH="/etc/ssl/private"
WEBROOT="/var/www/certbot"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v openssl &> /dev/null; then
        log_error "OpenSSL is required but not installed"
        exit 1
    fi
    
    if ! command -v nginx &> /dev/null; then
        log_warn "Nginx not found - make sure it's installed for production"
    fi
    
    log_info "Dependencies check completed"
}

generate_self_signed() {
    log_info "Generating self-signed certificate for development..."
    
    # Create directories
    sudo mkdir -p "$CERT_PATH" "$KEY_PATH"
    
    # Generate private key
    sudo openssl genrsa -out "$KEY_PATH/namaskah.key" 2048
    
    # Generate certificate
    sudo openssl req -new -x509 -key "$KEY_PATH/namaskah.key" \
        -out "$CERT_PATH/namaskah.crt" -days 365 \
        -subj "/C=NG/ST=Lagos/L=Lagos/O=Namaskah/CN=$DOMAIN"
    
    # Set permissions
    sudo chmod 600 "$KEY_PATH/namaskah.key"
    sudo chmod 644 "$CERT_PATH/namaskah.crt"
    
    log_info "Self-signed certificate generated successfully"
    log_warn "Self-signed certificates should only be used for development"
}

setup_letsencrypt() {
    log_info "Setting up Let's Encrypt certificate..."
    
    # Check if certbot is installed
    if ! command -v certbot &> /dev/null; then
        log_info "Installing certbot..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y certbot
        elif command -v yum &> /dev/null; then
            sudo yum install -y certbot
        else
            log_error "Please install certbot manually"
            exit 1
        fi
    fi
    
    # Create webroot directory
    sudo mkdir -p "$WEBROOT"
    
    # Stop nginx temporarily for standalone mode
    if systemctl is-active --quiet nginx; then
        log_info "Stopping nginx for certificate generation..."
        sudo systemctl stop nginx
        RESTART_NGINX=true
    fi
    
    # Generate certificate
    log_info "Requesting certificate from Let's Encrypt..."
    sudo certbot certonly \
        --standalone \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        -d "$DOMAIN"
    
    # Copy certificates to expected locations
    sudo cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$CERT_PATH/namaskah.crt"
    sudo cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$KEY_PATH/namaskah.key"
    
    # Set permissions
    sudo chmod 600 "$KEY_PATH/namaskah.key"
    sudo chmod 644 "$CERT_PATH/namaskah.crt"
    
    # Restart nginx if it was running
    if [ "$RESTART_NGINX" = true ]; then
        log_info "Starting nginx..."
        sudo systemctl start nginx
    fi
    
    log_info "Let's Encrypt certificate installed successfully"
}

setup_auto_renewal() {
    log_info "Setting up automatic certificate renewal..."
    
    # Create renewal script
    cat > /tmp/renew_cert.sh << 'EOF'
#!/bin/bash
# Auto-renewal script for Let's Encrypt certificates

DOMAIN="${DOMAIN:-api.namaskah.app}"
CERT_PATH="/etc/ssl/certs"
KEY_PATH="/etc/ssl/private"

# Renew certificate
certbot renew --quiet

# Copy renewed certificates
if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$CERT_PATH/namaskah.crt"
    cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$KEY_PATH/namaskah.key"
    
    # Reload nginx
    systemctl reload nginx
    
    echo "Certificate renewed successfully"
fi
EOF
    
    # Install renewal script
    sudo mv /tmp/renew_cert.sh /usr/local/bin/renew_cert.sh
    sudo chmod +x /usr/local/bin/renew_cert.sh
    
    # Add to crontab (run twice daily)
    (crontab -l 2>/dev/null; echo "0 */12 * * * /usr/local/bin/renew_cert.sh") | sudo crontab -
    
    log_info "Auto-renewal configured (runs twice daily)"
}

validate_certificate() {
    log_info "Validating SSL certificate..."
    
    if [ ! -f "$CERT_PATH/namaskah.crt" ]; then
        log_error "Certificate file not found: $CERT_PATH/namaskah.crt"
        return 1
    fi
    
    if [ ! -f "$KEY_PATH/namaskah.key" ]; then
        log_error "Private key file not found: $KEY_PATH/namaskah.key"
        return 1
    fi
    
    # Check certificate validity
    if ! openssl x509 -in "$CERT_PATH/namaskah.crt" -noout -checkend 86400; then
        log_warn "Certificate expires within 24 hours"
    fi
    
    # Check certificate and key match
    cert_hash=$(openssl x509 -noout -modulus -in "$CERT_PATH/namaskah.crt" | openssl md5)
    key_hash=$(openssl rsa -noout -modulus -in "$KEY_PATH/namaskah.key" | openssl md5)
    
    if [ "$cert_hash" != "$key_hash" ]; then
        log_error "Certificate and private key do not match"
        return 1
    fi
    
    # Show certificate info
    log_info "Certificate information:"
    openssl x509 -in "$CERT_PATH/namaskah.crt" -noout -subject -dates
    
    log_info "SSL certificate validation completed successfully"
}

test_ssl_config() {
    log_info "Testing SSL configuration..."
    
    # Test nginx configuration
    if command -v nginx &> /dev/null; then
        if sudo nginx -t; then
            log_info "Nginx configuration is valid"
        else
            log_error "Nginx configuration test failed"
            return 1
        fi
    fi
    
    # Test SSL connection (if server is running)
    if nc -z localhost 443 2>/dev/null; then
        log_info "Testing SSL connection..."
        echo | openssl s_client -connect localhost:443 -servername "$DOMAIN" 2>/dev/null | \
            openssl x509 -noout -dates
    else
        log_warn "HTTPS server not running - skipping connection test"
    fi
}

show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  self-signed    Generate self-signed certificate (development only)"
    echo "  letsencrypt    Setup Let's Encrypt certificate (production)"
    echo "  renew          Renew existing certificate"
    echo "  validate       Validate existing certificate"
    echo "  test           Test SSL configuration"
    echo "  auto-renew     Setup automatic renewal"
    echo ""
    echo "Environment variables:"
    echo "  DOMAIN         Domain name (default: api.namaskah.app)"
    echo "  EMAIL          Email for Let's Encrypt (default: admin@namaskah.app)"
}

main() {
    case "${1:-}" in
        "self-signed")
            check_dependencies
            generate_self_signed
            validate_certificate
            ;;
        "letsencrypt")
            check_dependencies
            setup_letsencrypt
            setup_auto_renewal
            validate_certificate
            ;;
        "renew")
            /usr/local/bin/renew_cert.sh
            ;;
        "validate")
            validate_certificate
            ;;
        "test")
            test_ssl_config
            ;;
        "auto-renew")
            setup_auto_renewal
            ;;
        *)
            show_usage
            exit 1
            ;;
    esac
}

main "$@"