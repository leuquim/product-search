#!/bin/bash

# Lenovo Pricing Product Search - Setup and Run Script
# This script installs dependencies, imports data, and starts the web server

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE} Lenovo Pricing Product Search${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo
}

# Check if Python is available
check_python() {
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        print_error "Python is not installed. Please install Python 3.7+ first."
        exit 1
    fi
    
    # Use python3 if available, otherwise python
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        PIP_CMD="pip3"
    else
        PYTHON_CMD="python"
        PIP_CMD="pip"
    fi
    
    print_success "Python found: $PYTHON_CMD"
}

# Install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    if [ -f "requirements.txt" ]; then
        $PIP_CMD install -r requirements.txt
        print_success "Dependencies installed successfully"
    else
        print_error "requirements.txt not found!"
        exit 1
    fi
}

# Check for Excel file and import if needed
check_and_import_data() {
    print_status "Checking for data..."
    
    # Look for Excel files
    EXCEL_FILE=""
    
    # Check for common Excel file patterns
    for pattern in "*.xlsx" "*.xls" "*pricing*.xlsx" "*product*.xlsx" "*inventory*.xlsx"; do
        if ls $pattern 1> /dev/null 2>&1; then
            EXCEL_FILE=$(ls $pattern | head -1)
            break
        fi
    done
    
    # Check if database already exists
    if [ -f "products.duckdb" ]; then
        # Check if database has data
        DB_SIZE=$($PYTHON_CMD -c "
import os
import duckdb
try:
    conn = duckdb.connect('products.duckdb')
    result = conn.execute('SELECT COUNT(*) FROM products').fetchone()
    print(result[0] if result else 0)
    conn.close()
except:
    print(0)
" 2>/dev/null || echo "0")
        
        if [ "$DB_SIZE" -gt "0" ]; then
            print_success "Database already exists with $DB_SIZE records"
            return 0
        else
            print_warning "Database exists but is empty, will reimport data"
        fi
    fi
    
    # If no Excel file found, prompt user
    if [ -z "$EXCEL_FILE" ]; then
        echo
        print_warning "No Excel file found in current directory"
        echo "Please ensure your Excel file is in this directory and run again."
        echo "Looking for files matching: *.xlsx, *.xls, *pricing*.xlsx, *product*.xlsx, *inventory*.xlsx"
        echo
        read -p "Enter the path to your Excel file (or press Enter to skip): " USER_FILE
        
        if [ -n "$USER_FILE" ] && [ -f "$USER_FILE" ]; then
            EXCEL_FILE="$USER_FILE"
        else
            print_warning "No Excel file provided. Starting web server without data."
            return 0
        fi
    fi
    
    # Import the Excel file
    if [ -n "$EXCEL_FILE" ]; then
        print_status "Found Excel file: $EXCEL_FILE"
        print_status "Importing data into database..."
        
        $PYTHON_CMD -c "
from product_search.importer import ExcelImporter
importer = ExcelImporter('$EXCEL_FILE')
importer.import_to_database()
print('✅ Data import completed successfully!')
"
        
        if [ $? -eq 0 ]; then
            print_success "Data imported successfully!"
        else
            print_error "Data import failed!"
            exit 1
        fi
    fi
}

# Start the web server
start_server() {
    print_status "Starting web server..."
    echo
    echo -e "${GREEN}🚀 Lenovo Pricing Product Search${NC}"
    echo -e "${GREEN}📍 Local access: http://localhost:8080${NC}"
    echo -e "${GREEN}🌐 Network access: http://[YOUR-IP]:8080${NC}"
    echo -e "${YELLOW}💡 Find your IP with: ipconfig (Windows) or hostname -I (Linux)${NC}"
    echo -e "${BLUE}⏹️  Press Ctrl+C to stop the server${NC}"
    echo
    
    # Start the server
    $PYTHON_CMD -m product_search.web_app
}

# Main execution
main() {
    print_header
    
    # Change to script directory
    cd "$(dirname "$0")"
    
    print_status "Current directory: $(pwd)"
    
    # Check Python
    check_python
    
    # Install dependencies
    install_dependencies
    
    # Check and import data
    check_and_import_data
    
    # Start server
    start_server
}

# Handle Ctrl+C gracefully
trap 'echo -e "\n${YELLOW}Server stopped by user${NC}"; exit 0' INT

# Run main function
main "$@"