"""
Product Search - Import and search Excel product data with DuckDB

A Python application for importing large Excel files into DuckDB and 
providing fast search capabilities through CLI and web interfaces.
"""

__version__ = "1.0.0"
__author__ = "Product Search Team"

from .database import ProductDatabase
from .importer import ExcelImporter, import_excel_file, preview_excel_file
from .config import DATABASE_PATH, DEFAULT_SEARCH_LIMIT

__all__ = [
    'ProductDatabase',
    'ExcelImporter', 
    'import_excel_file',
    'preview_excel_file',
    'DATABASE_PATH',
    'DEFAULT_SEARCH_LIMIT'
]