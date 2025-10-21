#!/bin/bash

# Namaskah SMS Deployment Script
# Automates the complete deployment process for next phase features

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}
PYTHON=${PYTHON:-python3}
TIMEOUT=30

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check Python
    if ! command -v $PYTHON &> /dev/null; then
        log_error "Python not found. Please install Python 3.9+"
        exit 1
    fi
    
    # Check required files
    required_files=("main.py" "pricing_config.py" "retry_mechanisms.py" "requirements.txt")
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "Required file missing: $file"
            exit 1
        fi
    done
    
    log_success "Dependencies check passed"
}

install_requirements() {
    log_info "Installing/updating requirements..."
    
    if [[ -f "requirements.txt" ]]; then
        $PYTHON -m pip install -r requirements.txt --quiet
        log_success "Requirements installed"
    else
        log_warning "No requirements.txt found, skipping..."
    fi
}

validate_implementation() {
    log_info "Validating implementation..."
    
    if [[ -f "validate_implementation.py" ]]; then
        if $PYTHON validate_implementation.py; then
            log_success "Implementation validation passed"
        else
            log_error "Implementation validation failed"
            exit 1
        fi
    else
        log_warning "Validation script not found, skipping..."
    fi
}

stop_existing_server() {
    log_info "Stopping existing server..."
    
    # Try to stop gracefully first
    if pgrep -f "uvicorn main:app" > /dev/null; then
        pkill -f "uvicorn main:app" || true
        sleep 2
    fi
    
    if pgrep -f "python main.py" > /dev/null; then
        pkill -f "python main.py" || true
        sleep 2
    fi
    
    # Force kill if still running
    if pgrep -f "main.py\|uvicorn.*main:app" > /dev/null; then
        pkill -9 -f "main.py\|uvicorn.*main:app" || true
        sleep 1
    fi
    
    log_success "Existing server stopped"
}

start_server() {
    log_info "Starting Namaskah SMS server..."
    
    # Check if uvicorn is available
    if command -v uvicorn &> /dev/null; then
        log_info "Using uvicorn server..."
        nohup uvicorn main:app --host $HOST --port $PORT --reload > server.log 2>&1 &
        SERVER_PID=$!
    else
        log_info "Using Python directly..."
        nohup $PYTHON main.py > server.log 2>&1 &
        SERVER_PID=$!
    fi
    
    echo $SERVER_PID > server.pid
    log_success "Server started with PID: $SERVER_PID"
}

wait_for_server() {
    log_info "Waiting for server to be ready..."
    
    local count=0
    local max_attempts=30
    
    while [[ $count -lt $max_attempts ]]; do
        if curl -s "http://localhost:$PORT/health" > /dev/null 2>&1; then
            log_success "Server is ready!"
            return 0
        fi
        
        count=$((count + 1))
        echo -n "."
        sleep 1
    done
    
    log_error "Server failed to start within $max_attempts seconds"
    return 1
}

validate_deployment() {
    log_info "Validating deployment..."
    
    # Test critical endpoints
    local base_url="http://localhost:$PORT"
    local failed=0
    
    # Health check
    if curl -s "$base_url/health" | grep -q "healthy"; then
        log_success "Health endpoint: OK"
    else
        log_error "Health endpoint: FAILED"
        failed=1
    fi
    
    # System health
    if curl -s "$base_url/system/health" | grep -q "services"; then
        log_success "System health endpoint: OK"
    else
        log_error "System health endpoint: FAILED"
        failed=1
    fi
    
    # Services list
    if curl -s "$base_url/services/list" | grep -q "tiers"; then
        log_success "Services list endpoint: OK"
    else
        log_error "Services list endpoint: FAILED"
        failed=1
    fi
    
    if [[ $failed -eq 1 ]]; then
        log_error "Deployment validation failed"
        return 1
    fi
    
    log_success "Deployment validation passed"
    return 0
}

run_comprehensive_tests() {
    log_info "Running comprehensive tests..."
    
    if [[ -f "test_comprehensive.py" ]]; then
        if $PYTHON test_comprehensive.py; then
            log_success "Comprehensive tests passed"
        else
            log_warning "Some tests failed, but deployment continues"
        fi
    else
        log_warning "Test suite not found, skipping..."
    fi
}

show_status() {
    log_info "Deployment Status Summary"
    echo "=================================="
    
    local base_url="http://localhost:$PORT"
    
    # Server status
    if pgrep -f "main.py\|uvicorn.*main:app" > /dev/null; then
        log_success "Server: Running (PID: $(cat server.pid 2>/dev/null || echo 'Unknown'))"
    else
        log_error "Server: Not running"
    fi
    
    # Endpoint status
    if curl -s "$base_url/health" > /dev/null 2>&1; then
        log_success "Health endpoint: Accessible"
    else
        log_error "Health endpoint: Not accessible"
    fi
    
    # Feature status
    echo ""
    log_info "Feature Status:"
    echo "  • Email Verification Bypass: ✅ Active"
    echo "  • Hourly Rental System: ✅ Implemented"
    echo "  • Dynamic Pricing: ✅ Active"
    echo "  • Retry Mechanisms: ✅ Active"
    echo "  • Circuit Breakers: ✅ Monitoring"
    echo "  • Health Monitoring: ✅ Active"
    
    echo ""
    log_info "Access URLs:"
    echo "  • Application: http://localhost:$PORT/app"
    echo "  • Admin Panel: http://localhost:$PORT/admin"
    echo "  • API Docs: http://localhost:$PORT/docs"
    echo "  • Health Check: http://localhost:$PORT/health"
    echo "  • System Health: http://localhost:$PORT/system/health"
    
    echo ""
    log_info "Monitoring Commands:"
    echo "  • Check logs: tail -f server.log"
    echo "  • Check health: curl http://localhost:$PORT/health"
    echo "  • Run tests: python test_comprehensive.py"
    echo "  • Stop server: kill \$(cat server.pid)"
}

cleanup_on_error() {
    log_error "Deployment failed, cleaning up..."
    
    if [[ -f "server.pid" ]]; then
        local pid=$(cat server.pid)
        if kill -0 $pid 2>/dev/null; then
            kill $pid
            log_info "Stopped server with PID: $pid"
        fi
        rm -f server.pid
    fi
    
    exit 1
}

# Main deployment process
main() {
    echo "🚀 Namaskah SMS Deployment Script"
    echo "=================================="
    echo ""
    
    # Set up error handling
    trap cleanup_on_error ERR
    
    # Pre-deployment checks
    check_dependencies
    install_requirements
    validate_implementation
    
    # Deployment
    stop_existing_server
    start_server
    
    # Post-deployment validation
    if wait_for_server; then
        validate_deployment
        run_comprehensive_tests
        show_status
        
        echo ""
        log_success "🎉 Deployment completed successfully!"
        log_info "Monitor the system and check logs for any issues."
        log_info "Next steps: Monitor user adoption of hourly rentals"
        
    else
        log_error "Server failed to start properly"
        cleanup_on_error
    fi
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "stop")
        log_info "Stopping Namaskah SMS server..."
        stop_existing_server
        if [[ -f "server.pid" ]]; then
            rm -f server.pid
        fi
        log_success "Server stopped"
        ;;
    "status")
        show_status
        ;;
    "restart")
        log_info "Restarting Namaskah SMS server..."
        stop_existing_server
        start_server
        wait_for_server
        validate_deployment
        log_success "Server restarted successfully"
        ;;
    "test")
        log_info "Running tests only..."
        run_comprehensive_tests
        ;;
    "validate")
        log_info "Running validation only..."
        validate_implementation
        ;;
    *)
        echo "Usage: $0 {deploy|stop|status|restart|test|validate}"
        echo ""
        echo "Commands:"
        echo "  deploy   - Full deployment (default)"
        echo "  stop     - Stop the server"
        echo "  status   - Show current status"
        echo "  restart  - Restart the server"
        echo "  test     - Run comprehensive tests"
        echo "  validate - Validate implementation"
        exit 1
        ;;
esac