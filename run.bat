@echo off
REM Lenovo Pricing Product Search - Setup and Run Script (Windows)
REM This script installs dependencies, imports data, and starts the web server

setlocal enabledelayedexpansion

echo.
echo ============================================
echo  Lenovo Pricing Product Search
echo ============================================
echo.

REM Change to script directory
cd /d "%~dp0"
echo [INFO] Current directory: %cd%

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed. Please install Python 3.7+ first.
    pause
    exit /b 1
)

echo [SUCCESS] Python found

REM Install dependencies
echo [INFO] Installing Python dependencies...
if exist requirements.txt (
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [SUCCESS] Dependencies installed successfully
) else (
    echo [ERROR] requirements.txt not found!
    pause
    exit /b 1
)

REM Check for data
echo [INFO] Checking for data...

REM Check if database exists and has data
if exist products.duckdb (
    python -c "import duckdb; conn = duckdb.connect('products.duckdb'); result = conn.execute('SELECT COUNT(*) FROM products').fetchone(); print('DB_SIZE=' + str(result[0]) if result else 'DB_SIZE=0'); conn.close()" > temp_db_check.txt 2>nul
    for /f "tokens=2 delims==" %%a in (temp_db_check.txt) do set DB_SIZE=%%a
    del temp_db_check.txt 2>nul
    
    if defined DB_SIZE (
        if !DB_SIZE! gtr 0 (
            echo [SUCCESS] Database already exists with !DB_SIZE! records
            goto start_server
        )
    )
)

REM Look for Excel files
set EXCEL_FILE=
for %%f in (*.xlsx *.xls *pricing*.xlsx *product*.xlsx *inventory*.xlsx) do (
    if exist "%%f" (
        set EXCEL_FILE=%%f
        goto found_excel
    )
)

:found_excel
if defined EXCEL_FILE (
    echo [INFO] Found Excel file: %EXCEL_FILE%
    echo [INFO] Importing data into database...
    
    python -c "from product_search.importer import ExcelImporter; importer = ExcelImporter('%EXCEL_FILE%'); importer.import_to_database(); print('✅ Data import completed successfully!')"
    
    if errorlevel 1 (
        echo [ERROR] Data import failed!
        pause
        exit /b 1
    )
    echo [SUCCESS] Data imported successfully!
) else (
    echo [WARNING] No Excel file found in current directory
    echo Please ensure your Excel file is in this directory.
    echo Looking for: *.xlsx, *.xls, *pricing*.xlsx, *product*.xlsx, *inventory*.xlsx
    echo.
    set /p USER_FILE="Enter the path to your Excel file (or press Enter to skip): "
    
    if defined USER_FILE (
        if exist "!USER_FILE!" (
            echo [INFO] Importing data from: !USER_FILE!
            python -c "from product_search.importer import ExcelImporter; importer = ExcelImporter('!USER_FILE!'); importer.import_to_database(); print('✅ Data import completed successfully!')"
            
            if errorlevel 1 (
                echo [ERROR] Data import failed!
                pause
                exit /b 1
            )
            echo [SUCCESS] Data imported successfully!
        ) else (
            echo [WARNING] File not found. Starting web server without data.
        )
    ) else (
        echo [WARNING] No Excel file provided. Starting web server without data.
    )
)

:start_server
echo.
echo [INFO] Starting web server...
echo.
echo 🚀 Lenovo Pricing Product Search
echo 📍 Local access: http://localhost:8080
echo 🌐 Network access: http://[YOUR-IP]:8080
echo 💡 Find your IP with: ipconfig
echo ⏹️  Press Ctrl+C to stop the server
echo.

REM Start the server
python -m product_search.web_app

pause