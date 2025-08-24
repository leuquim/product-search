# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Running the Application
```bash
# Linux/WSL users
./run.sh

# Windows users
run.bat

# Manual start (without auto-import)
python -m product_search.web_app
```

### Development Tasks
```bash
# Install dependencies
pip install -r requirements.txt

# Import Excel data manually
python -c "from product_search.importer import ExcelImporter; ExcelImporter('your-file.xlsx').import_to_database()"

# Run CLI commands
python -m product_search.cli import-data <excel_file>
python -m product_search.cli search <query>
python -m product_search.cli stats
```

### Testing and Validation
```bash
# Check if database has data
python -c "from product_search.database import ProductDatabase; db = ProductDatabase(); print(db.get_stats())"

# Test search functionality
python -c "from product_search.database import ProductDatabase; db = ProductDatabase(); results, count = db.search('test'); print(f'Found {count} results')"
```

## Architecture Overview

### Core Components

**ProductDatabase** (`database.py`): DuckDB-based database layer
- Handles all database operations using DuckDB for columnar storage
- Implements dynamic schema creation from Excel columns
- Provides fast full-text search with automatic indexing on ASSEMBLY and DESCRIPTION columns
- Column names are cleaned automatically (spaces→underscores, special chars removed)

**ExcelImporter** (`importer.py`): Excel to database import
- Chunk-based processing for memory efficiency (10k rows per chunk)
- Handles large files (500k+ rows) using openpyxl read-only mode
- Progress tracking with tqdm
- Automatic header detection and column mapping

**Flask Web Application** (`web_app.py`): Web interface
- Runs on all network interfaces (0.0.0.0:8080) for team access
- RESTful API endpoints for search, stats, and Lenovo Press integration
- Automatic port fallback if 8080 is occupied
- Real-time search with <100ms response times

**LenovoSearcher** (`lenovo_search.py`): Lenovo Press API integration
- Searches official Lenovo documentation
- Extracts part numbers from documentation pages
- Table data extraction from HTML pages
- Intelligent result highlighting

### Data Flow

1. **Import**: Excel file → ExcelImporter → DuckDB (chunked processing)
2. **Search**: Web UI → Flask API → ProductDatabase → DuckDB query
3. **Lenovo Integration**: Search term → LenovoSearcher → Lenovo Press API → Parsed results

### Key Configuration

All settings in `product_search/config.py`:
- `WEB_HOST = '0.0.0.0'` - Network-accessible by default
- `WEB_PORT = 8080` - Default port
- `DATABASE_PATH = 'products.duckdb'` - Database location
- `CHUNK_SIZE = 10000` - Import batch size
- `INDEXED_COLUMNS = ['ASSEMBLY', 'DESCRIPTION']` - Columns with indexes

### Database Schema

Dynamic schema based on Excel columns with automatic cleaning:
- Spaces converted to underscores
- Special characters removed
- All columns stored as VARCHAR for flexibility
- Automatic indexing on ASSEMBLY and DESCRIPTION

### Search Implementation

Uses DuckDB's ILIKE for case-insensitive pattern matching:
- Searches across ASSEMBLY and DESCRIPTION columns
- Results ordered to preserve original Excel column order
- Pagination support with limit/offset
- Sort by any column

## Project Structure

```
product_search/
├── __init__.py
├── cli.py           # Command-line interface
├── config.py        # Central configuration
├── database.py      # DuckDB operations
├── importer.py      # Excel import logic
├── lenovo_search.py # Lenovo Press integration
├── web_app.py       # Flask web server
├── static/
│   └── style.css    # Tailwind CSS styles
└── templates/
    └── index.html   # Web UI template
```

## Important Notes

- The application auto-detects Excel files matching patterns: `*.xlsx`, `*pricing*.xlsx`, `*product*.xlsx`, `*inventory*.xlsx`
- DuckDB provides columnar storage optimized for analytical queries
- The web interface uses Tailwind CSS with dark/light theme support
- Network access requires proper firewall configuration on Windows/WSL
- All file paths must be absolute when using the Python API directly