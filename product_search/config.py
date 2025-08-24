import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'products.duckdb')

# Import performance settings
CHUNK_SIZE = 50000  # Increased from 10000 for better performance
FAST_IMPORT_CHUNK_SIZE = 100000  # Even larger chunks for fast import methods
IMPORT_METHOD = 'auto'  # 'auto', 'duckdb_native', 'pandas', 'openpyxl'

# Search settings
DEFAULT_SEARCH_LIMIT = 100
MAX_SEARCH_LIMIT = 1000
SEARCH_COLUMNS = ['ASSEMBLY', 'DESCRIPTION']
INDEXED_COLUMNS = ['ASSEMBLY', 'DESCRIPTION']

# Column visibility settings
DEFAULT_VISIBLE_COLUMNS = ['ASSEMBLY', 'DESCRIPTION']  # Columns shown by default
ALWAYS_VISIBLE_COLUMNS = []  # Columns that cannot be hidden (empty = no restrictions)
MAX_VISIBLE_COLUMNS = 10  # Maximum columns that can be selected for display

# Web settings
WEB_HOST = '0.0.0.0'
WEB_PORT = 8080
WEB_DEBUG = True

# DuckDB optimization settings
DUCKDB_MEMORY_LIMIT = '4GB'  # Adjust based on available RAM
DUCKDB_THREADS = 4  # Number of threads for parallel processing