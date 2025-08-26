#!/bin/bash

# Flask VM Dashboard Production Deployment Script
# This script sets up the complete production environment with Nginx and systemd

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Flask VM Dashboard Production Deployment ===${NC}"

# Check if running as root for system configuration
if [[ $EUID -eq 0 ]]; then
    echo -e "${RED}Warning: Running as root. This script will configure system services.${NC}"
    SUDO=""
else
    echo -e "${YELLOW}Running as non-root user. Will use sudo for system operations.${NC}"
    SUDO="sudo"
fi

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo -e "${RED}Error: app.py not found. Please run this script from the project directory.${NC}"
    exit 1
fi

echo -e "${GREEN}Step 1: Setting up Python environment...${NC}"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install/upgrade dependencies
echo -e "${GREEN}Installing Python dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo -e "${GREEN}Step 2: Validating configuration...${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found. Please create it with required configuration.${NC}"
    echo -e "${YELLOW}Required variables: DASHBOARD_USERNAME, DASHBOARD_PASSWORD, PRISM_IP, PRISM_USERNAME, PRISM_PASSWORD, SECRET_KEY${NC}"
    exit 1
fi

# Validate configuration
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

required_vars = ['DASHBOARD_USERNAME', 'DASHBOARD_PASSWORD', 'PRISM_IP', 'PRISM_USERNAME', 'PRISM_PASSWORD', 'SECRET_KEY']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    print(f'Error: Missing required environment variables: {missing_vars}')
    exit(1)
else:
    print('Configuration validated successfully!')
"

if [ $? -ne 0 ]; then
    echo -e "${RED}Configuration validation failed. Please check your .env file.${NC}"
    exit 1
fi

echo -e "${GREEN}Step 3: Setting up systemd service...${NC}"

# Copy systemd service file
$SUDO cp flask_vm_dashboard.service /etc/systemd/system/

# Reload systemd and enable service
$SUDO systemctl daemon-reload
$SUDO systemctl enable flask_vm_dashboard

echo -e "${GREEN}Step 4: Setting up Nginx...${NC}"

# Check if Nginx is installed
if ! command -v nginx &> /dev/null; then
    echo -e "${YELLOW}Nginx not found. Installing...${NC}"
    if command -v apt-get &> /dev/null; then
        $SUDO apt-get update
        $SUDO apt-get install -y nginx
    elif command -v yum &> /dev/null; then
        $SUDO yum install -y nginx
    elif command -v dnf &> /dev/null; then
        $SUDO dnf install -y nginx
    else
        echo -e "${RED}Could not install Nginx automatically. Please install it manually.${NC}"
        exit 1
    fi
fi

# Copy Nginx configuration
$SUDO cp etc/nginx/conf.d/flask_vm_dashboard.conf /etc/nginx/conf.d/

# Test Nginx configuration
echo -e "${GREEN}Testing Nginx configuration...${NC}"
$SUDO nginx -t

if [ $? -ne 0 ]; then
    echo -e "${RED}Nginx configuration test failed. Please check the configuration.${NC}"
    exit 1
fi

echo -e "${GREEN}Step 5: Setting up SSL certificates...${NC}"

# Check if SSL certificates exist
if [ ! -f "certs/fullchain.pem" ] || [ ! -f "certs/privkey.pem" ]; then
    echo -e "${YELLOW}SSL certificates not found in certs/ directory.${NC}"
    echo -e "${YELLOW}You can either:${NC}"
    echo -e "${YELLOW}1. Copy your existing certificates to certs/fullchain.pem and certs/privkey.pem${NC}"
    echo -e "${YELLOW}2. Generate self-signed certificates for testing${NC}"
    echo -e "${YELLOW}3. Use Let's Encrypt (certbot) for production${NC}"
    
    read -p "Generate self-signed certificates for testing? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        mkdir -p certs
        openssl req -x509 -newkey rsa:4096 -keyout certs/privkey.pem -out certs/fullchain.pem -days 365 -nodes \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        echo -e "${GREEN}Self-signed certificates generated.${NC}"
    fi
fi

echo -e "${GREEN}Step 6: Setting file permissions...${NC}"

# Set proper permissions
chmod +x start.sh
chmod 600 .env
chmod 644 certs/fullchain.pem 2>/dev/null || true
chmod 600 certs/privkey.pem 2>/dev/null || true

echo -e "${GREEN}Step 7: Starting services...${NC}"

# Start Flask application
$SUDO systemctl start flask_vm_dashboard
$SUDO systemctl status flask_vm_dashboard --no-pager

# Start/restart Nginx
$SUDO systemctl enable nginx
$SUDO systemctl restart nginx
$SUDO systemctl status nginx --no-pager

echo -e "${GREEN}Step 8: Verifying deployment...${NC}"

# Wait a moment for services to start
sleep 3

# Test Flask application
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health | grep -q "200"; then
    echo -e "${GREEN}✓ Flask application is running${NC}"
else
    echo -e "${RED}✗ Flask application health check failed${NC}"
fi

# Test Nginx
if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "301\|200"; then
    echo -e "${GREEN}✓ Nginx is running${NC}"
else
    echo -e "${RED}✗ Nginx health check failed${NC}"
fi

echo -e "${BLUE}=== Deployment Complete ===${NC}"
echo -e "${GREEN}Your Flask VM Dashboard is now running!${NC}"
echo ""
echo -e "${YELLOW}Access URLs:${NC}"
echo -e "  HTTP:  http://localhost (redirects to HTTPS)"
echo -e "  HTTPS: https://localhost"
echo -e "  Health: http://localhost:5000/health"
echo ""
echo -e "${YELLOW}Service Management:${NC}"
echo -e "  Flask:  sudo systemctl {start|stop|restart|status} flask_vm_dashboard"
echo -e "  Nginx:  sudo systemctl {start|stop|restart|status} nginx"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo -e "  Flask:  sudo journalctl -u flask_vm_dashboard -f"
echo -e "  Nginx:  sudo tail -f /var/log/nginx/flask_vm_dashboard_*.log"
echo ""
echo -e "${YELLOW}Configuration Files:${NC}"
echo -e "  Flask:  /etc/systemd/system/flask_vm_dashboard.service"
echo -e "  Nginx:  /etc/nginx/conf.d/flask_vm_dashboard.conf"