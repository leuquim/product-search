# Lenovo Pricing Product Search

A fast, web-based product search application that imports Excel data into DuckDB for lightning-fast searches and includes Lenovo Press documentation integration.

## 🚀 Quick Start

### For Linux/WSL Users:
```bash
./run.sh
```

### For Windows Users:
```cmd
run.bat
```

That's it! The script will:
1. ✅ Install all required Python dependencies
2. ✅ Automatically find and import your Excel file (if not already imported)
3. ✅ Start the web server with network access enabled
4. ✅ Show you the URLs to access the application

## 📋 Prerequisites

- **Python 3.7+** (with pip)
- **Excel file** containing product data (optional - can be added later)

## 📁 Excel File Auto-Detection

The setup script automatically looks for Excel files matching these patterns:
- `*.xlsx`, `*.xls` - Any Excel file
- `*pricing*.xlsx` - Files with "pricing" in the name
- `*product*.xlsx` - Files with "product" in the name  
- `*inventory*.xlsx` - Files with "inventory" in the name

If no file is found, you'll be prompted to specify the path manually.

## 🌐 Network Access

The application runs on **all network interfaces** by default:

- **Local access**: http://localhost:8080
- **Network access**: http://[YOUR-IP]:8080

To find your IP address:
- **Windows**: Run `ipconfig` in Command Prompt
- **Linux**: Run `hostname -I` or `ip addr show`

### Windows Firewall (WSL Users)

If you're using WSL and others can't access the application, you may need to configure Windows Firewall:

```powershell
# Run in PowerShell as Administrator
netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0 connectport=8080 connectaddress=172.17.77.52
New-NetFirewallRule -DisplayName "WSL Port 8080" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow
```

## ✨ Features

### 🏠 Local Database Search
- **Lightning fast**: <100ms search performance with DuckDB
- **Smart column ordering**: ASSEMBLY and DESCRIPTION columns highlighted
- **Full-text search**: Search across all product fields
- **Dark/Light themes**: Automatic theme switching
- **Responsive design**: Works on desktop and mobile

### 🔍 Lenovo Press Integration
- **Documentation search**: Search Lenovo's official documentation
- **Part number matching**: Automatically extract part numbers from documents
- **Table extraction**: Pull structured data from documentation pages  
- **Intelligent highlighting**: Search terms highlighted in results
- **Flexible search**: Search by description only or with specific part numbers

## 🛠️ Manual Installation

If you prefer to set up manually:

```bash
# Install dependencies
pip install -r requirements.txt

# Import Excel data (optional)
python -c "from product_search.importer import ExcelImporter; ExcelImporter('your-file.xlsx').import_to_database()"

# Start server
python -m product_search.web_app
```

## 📊 Performance

- **Database**: DuckDB (columnar, analytical database)
- **Import speed**: ~10k rows/second  
- **Search speed**: <100ms for most queries
- **Memory usage**: Efficient chunk-based processing for large files
- **File size**: Handles Excel files up to 100MB+ (500k+ rows)

## 🔧 Configuration

Key settings in `product_search/config.py`:

```python
WEB_HOST = '0.0.0.0'          # Network access enabled
WEB_PORT = 8080               # Default port
DATABASE_PATH = 'products.duckdb'  # Database location
CHUNK_SIZE = 10000            # Import batch size
```

## 🚪 Stopping the Server

- Press **Ctrl+C** in the terminal to stop the server
- The script handles graceful shutdown automatically

## 🔍 Troubleshooting

**Import fails**: Check Excel file format and ensure it has headers in the first row

**Network access doesn't work**: 
- Check Windows Firewall settings
- For WSL, configure port forwarding (see Network Access section)
- Verify your IP address with `ipconfig` or `hostname -I`

**Port already in use**: The script automatically tries alternative ports (8081, 8082, etc.)

**Dependencies fail to install**: Ensure you have Python 3.7+ and pip installed

## 📝 Project Structure

```
lenovo-pricing/
├── run.sh              # Linux/WSL setup script
├── run.bat             # Windows setup script  
├── requirements.txt    # Python dependencies
├── products.duckdb     # Database (created after import)
├── product_search/     # Main application code
│   ├── database.py     # DuckDB operations
│   ├── importer.py     # Excel import logic
│   ├── web_app.py      # Flask web application
│   ├── lenovo_search.py # Lenovo Press integration
│   └── templates/      # Web UI templates
└── README.md           # This file
```

## 🎯 Usage Tips

1. **Large files**: The application efficiently handles files with 500k+ rows
2. **Search tips**: Use partial matches, the search is very forgiving
3. **Column ordering**: ASSEMBLY and DESCRIPTION are always shown first
4. **Theme switching**: Click the theme toggle in the top-right corner
5. **Lenovo search**: Leave part numbers empty to search by description only

---

**Built with**: Python, DuckDB, Flask, Tailwind CSS
**Performance**: Optimized for fast search and large datasets
**Network ready**: Share with your team out of the box