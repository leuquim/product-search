#!/bin/bash

# Quick Start Script for Lenovo Pricing Product Search
# Fast startup without reinstalling dependencies

# Removed 'set -e' to prevent terminal crashes on errors

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Change to script directory
cd "$(dirname "$0")"

# Determine Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
else
    PYTHON_CMD="python"
    PIP_CMD="pip"
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo -e "${GREEN}✓ Virtual environment found${NC}"
    
    # Try different activation script locations (Linux vs Windows style)
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    else
        echo -e "${YELLOW}⚠ Activation script not found, recreating venv...${NC}"
        rm -rf venv
        $PYTHON_CMD -m venv venv
        if [ -f "venv/bin/activate" ]; then
            source venv/bin/activate
        else
            source venv/Scripts/activate
        fi
        echo -e "${BLUE}Installing dependencies...${NC}"
        if ! $PIP_CMD install -q -r requirements.txt; then
            echo -e "${RED}❌ Failed to install dependencies. Please check your internet connection and try again.${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓ Setup complete!${NC}"
    fi
    
    # Check if dependencies are installed (quick check for key package)
    if ! $PYTHON_CMD -c "import duckdb" 2>/dev/null; then
        echo -e "${YELLOW}⚠ Dependencies missing, installing...${NC}"
        if ! $PIP_CMD install -q -r requirements.txt; then
            echo -e "${RED}❌ Failed to install dependencies. Please check your internet connection and try again.${NC}"
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}Setting up virtual environment (first time only)...${NC}"
    if ! $PYTHON_CMD -m venv venv; then
        echo -e "${RED}❌ Failed to create virtual environment. Make sure python3-venv is installed.${NC}"
        echo -e "${BLUE}💡 Try: sudo apt install python3.10-venv${NC}"
        exit 1
    fi
    
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    else
        echo -e "${RED}❌ Could not find activation script${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}Installing dependencies...${NC}"
    if ! $PIP_CMD install -q -r requirements.txt; then
        echo -e "${RED}❌ Failed to install dependencies. Please check your internet connection and try again.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Setup complete!${NC}"
fi

# Run migration if needed (silent check)
$PYTHON_CMD -c "
import sys
sys.path.insert(0, '.')
from product_search.migrations.migration_001_multi_file_support import upgrade
from product_search.config import DATABASE_PATH
import os
if os.path.exists(DATABASE_PATH):
    try:
        upgrade(DATABASE_PATH)
    except:
        pass
" 2>/dev/null || true

# Start the enhanced web app
echo -e "${GREEN}🚀 Starting Lenovo Product Search (Multi-File Edition)${NC}"
echo -e "${BLUE}📍 Local: http://localhost:8080${NC}"
echo -e "${BLUE}📁 Files: http://localhost:8080/files${NC}"
echo -e "${YELLOW}⏹  Press Ctrl+C to stop${NC}"
echo

# Run the enhanced version with column visibility
echo -e "${GREEN}🎨 New Feature: Column visibility control!${NC}"
echo -e "${BLUE}   - Select which columns to show in search results${NC}"
echo -e "${BLUE}   - Default: ASSEMBLY and DESCRIPTION${NC}"
echo -e "${BLUE}   - Use 'Select Columns' button in search interface${NC}"
echo ""

# Start the web application
echo -e "${GREEN}Starting web application...${NC}"
if ! $PYTHON_CMD -m product_search.web_app; then
    echo -e "${RED}❌ Failed to start web application${NC}"
    echo -e "${BLUE}💡 Check that all dependencies are installed correctly${NC}"
    exit 1
fi