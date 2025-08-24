#!/bin/bash

# Lenovo Product Search - Quick Start
# Sets up virtual environment and starts the application

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Determine Python command
if command -v python3 &> /dev/null; then
    PYTHON="python3"
    PIP="pip3"
else
    PYTHON="python"
    PIP="pip"
fi

echo -e "${BLUE}🚀 Lenovo Product Search - Quick Start${NC}"
echo

# Check python3-venv availability
echo -e "${BLUE}📋 Checking requirements...${NC}"
if ! $PYTHON -m venv --help &> /dev/null; then
    echo -e "${RED}❌ python3-venv is not installed${NC}"
    echo -e "${YELLOW}💡 Install with: sudo apt install python3.10-venv${NC}"
    return 1 2>/dev/null || exit 1
fi

# Setup virtual environment
if [ ! -d "venv" ]; then
    echo -e "${BLUE}📦 Creating virtual environment...${NC}"
    if ! $PYTHON -m venv venv; then
        echo -e "${RED}❌ Failed to create virtual environment${NC}"
        return 1 2>/dev/null || exit 1
    fi
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment found${NC}"
fi

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    echo -e "${RED}❌ Could not find activation script${NC}"
    return 1 2>/dev/null || exit 1
fi

# Check if dependencies need installation
NEED_INSTALL=false
if ! python -c "import duckdb, flask, openpyxl, pandas" 2>/dev/null; then
    NEED_INSTALL=true
fi

# Install dependencies with full progress
if [ "$NEED_INSTALL" = true ]; then
    echo -e "${BLUE}📥 Installing dependencies...${NC}"
    echo
    
    # Show full pip output with progress bars, downloads, etc.
    if ! $PIP install -r requirements.txt; then
        echo
        echo -e "${RED}❌ Dependency installation failed${NC}"
        return 1 2>/dev/null || exit 1
    fi
    
    echo
    echo -e "${GREEN}✅ All dependencies installed successfully${NC}"
else
    echo -e "${GREEN}✅ Dependencies already installed${NC}"
fi

# Run database migration
echo -e "${BLUE}🔧 Updating database schema...${NC}"
python -c "
import sys, os
sys.path.insert(0, '.')
try:
    from product_search.migrations.migration_001_multi_file_support import upgrade
    from product_search.config import DATABASE_PATH
    if os.path.exists(DATABASE_PATH):
        upgrade(DATABASE_PATH)
except: pass
" 2>/dev/null

echo
echo -e "${GREEN}🎉 Setup complete! Starting application...${NC}"
echo -e "${BLUE}📍 Web Interface: http://localhost:8080${NC}"
echo -e "${BLUE}📁 File Manager: http://localhost:8080/files${NC}"
echo
echo -e "${YELLOW}💡 Features:${NC}"
echo -e "${YELLOW}   • Import multiple Excel files${NC}"
echo -e "${YELLOW}   • Search across all files${NC}"
echo -e "${YELLOW}   • Column visibility controls${NC}"
echo
echo -e "${YELLOW}⏹️  Press Ctrl+C to stop${NC}"
echo

# Start the application
python -m product_search.web_app