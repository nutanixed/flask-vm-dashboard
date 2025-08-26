#!/bin/bash

# Flask VM Dashboard Startup Script
# This script starts the Flask application with proper error handling

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Flask VM Dashboard...${NC}"

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo -e "${RED}Error: app.py not found. Please run this script from the project directory.${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found. Please create it with required configuration.${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating one...${NC}"
    python3 -m venv .venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source .venv/bin/activate

# Install/upgrade dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check if Flask app can start
echo -e "${GREEN}Validating configuration...${NC}"
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

required_vars = ['DASHBOARD_USERNAME', 'DASHBOARD_PASSWORD', 'PRISM_IP', 'PRISM_USERNAME', 'PRISM_PASSWORD']
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

# Start the application
echo -e "${GREEN}Starting Flask application...${NC}"
echo -e "${YELLOW}Access the dashboard at: http://localhost:5000${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

python3 app.py