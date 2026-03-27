#!/bin/bash
#
# PhysiqAI API Service Installation Script
# Installs systemd service and health check cron job
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="physiqai-api"
SERVICE_FILE="physiqai-api.service"
SERVICE_SOURCE="/home/clawd/.openclaw/workspace/projects/physiqai/backend/api/${SERVICE_FILE}"
SERVICE_DEST="/etc/systemd/system/${SERVICE_FILE}"
HEALTH_SCRIPT="/home/clawd/.openclaw/workspace/projects/physiqai/scripts/api_health_check.sh"
LOG_DIR="/home/clawd/.openclaw/workspace/projects/physiqai/logs"

# Helper functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

verify_paths() {
    print_info "Verifying installation paths..."
    
    if [[ ! -f "$SERVICE_SOURCE" ]]; then
        print_error "Service file not found: $SERVICE_SOURCE"
        exit 1
    fi
    
    if [[ ! -f "$HEALTH_SCRIPT" ]]; then
        print_error "Health check script not found: $HEALTH_SCRIPT"
        exit 1
    fi
    
    # Ensure log directory exists with correct permissions
    mkdir -p "$LOG_DIR"
    chown -R clawd:clawd "$LOG_DIR"
    chmod 755 "$LOG_DIR"
    
    print_success "All paths verified"
}

install_service() {
    print_info "Installing systemd service..."
    
    # Copy service file
    cp "$SERVICE_SOURCE" "$SERVICE_DEST"
    chmod 644 "$SERVICE_DEST"
    
    # Reload systemd
    systemctl daemon-reload
    
    print_success "Service file installed to $SERVICE_DEST"
}

enable_service() {
    print_info "Enabling service to start on boot..."
    systemctl enable "$SERVICE_NAME"
    print_success "Service enabled"
}

start_service() {
    print_info "Starting PhysiqAI API service..."
    systemctl start "$SERVICE_NAME"
    
    # Wait a moment and check status
    sleep 2
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_success "Service started successfully"
    else
        print_error "Service failed to start"
        systemctl status "$SERVICE_NAME" --no-pager
        exit 1
    fi
}

setup_health_check() {
    print_info "Setting up health check cron job..."
    
    # Make health script executable
    chmod +x "$HEALTH_SCRIPT"
    chown clawd:clawd "$HEALTH_SCRIPT"
    
    # Create cron job (runs every minute, script handles 30s intervals internally)
    CRON_JOB="*/1 * * * * $HEALTH_SCRIPT >/dev/null 2>&1"
    
    # Remove any existing physiqai health check entries
    crontab -u clawd -l 2>/dev/null | grep -v "api_health_check.sh" | crontab -u clawd - 2>/dev/null || true
    
    # Add new cron job
    (crontab -u clawd -l 2>/dev/null; echo "$CRON_JOB") | crontab -u clawd -
    
    print_success "Health check cron job installed (runs every minute)"
}

verify_installation() {
    print_info "Verifying installation..."
    
    # Check service status
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_success "Service is running"
    else
        print_error "Service is not running"
    fi
    
    # Check if health endpoint responds
    sleep 1
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://localhost:5001/api/health" 2>/dev/null || echo "000")
    if [[ "$HTTP_CODE" == "200" ]]; then
        print_success "Health endpoint responding (HTTP 200)"
    else
        print_error "Health endpoint not responding (HTTP ${HTTP_CODE})"
    fi
    
    # Check cron job
    if crontab -u clawd -l 2>/dev/null | grep -q "api_health_check.sh"; then
        print_success "Health check cron job installed"
    else
        print_error "Health check cron job not found"
    fi
}

show_status() {
    echo ""
    echo "========================================="
    echo "  PhysiqAI API Installation Complete"
    echo "========================================="
    echo ""
    echo "Service Status:"
    systemctl status "$SERVICE_NAME" --no-pager | head -5
    echo ""
    echo "Useful Commands:"
    echo "  Check status:   sudo systemctl status $SERVICE_NAME"
    echo "  View logs:      sudo journalctl -u $SERVICE_NAME -f"
    echo "  Restart:        sudo systemctl restart $SERVICE_NAME"
    echo "  Stop:           sudo systemctl stop $SERVICE_NAME"
    echo "  Health logs:    tail -f $LOG_DIR/health_check.log"
    echo ""
    echo "Health Check:"
    echo "  Cron runs every minute (script checks API every 30s)"
    echo "  After 3 failures, service auto-restarts"
    echo "  Logs to: $LOG_DIR/health_check.log"
    echo ""
}

# Main installation flow
main() {
    echo "========================================="
    echo "  PhysiqAI API Service Installer"
    echo "========================================="
    echo ""
    
    check_root
    verify_paths
    install_service
    enable_service
    start_service
    setup_health_check
    verify_installation
    show_status
    
    print_success "Installation complete!"
}

# Handle uninstall option
uninstall() {
    echo "Uninstalling PhysiqAI API service..."
    
    check_root
    
    # Stop and disable service
    systemctl stop "$SERVICE_NAME" 2>/dev/null || true
    systemctl disable "$SERVICE_NAME" 2>/dev/null || true
    
    # Remove service file
    rm -f "$SERVICE_DEST"
    systemctl daemon-reload
    
    # Remove cron job
    crontab -u clawd -l 2>/dev/null | grep -v "api_health_check.sh" | crontab -u clawd - 2>/dev/null || true
    
    print_success "Uninstallation complete"
}

# Parse arguments
case "${1:-}" in
    --uninstall|-u)
        uninstall
        ;;
    --help|-h)
        echo "Usage: $0 [--uninstall|-u]"
        echo ""
        echo "Options:"
        echo "  --uninstall, -u    Remove the service and cron job"
        echo "  --help, -h         Show this help message"
        exit 0
        ;;
    *)
        main
        ;;
esac
