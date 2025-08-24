"""
Product Search - Import and search Excel product data with DuckDB

A Python application for importing large Excel files into DuckDB and 
providing fast search capabilities through CLI and web interfaces.
"""

__version__ = "1.0.0"
__author__ = "Product Search Team"

from .database import MultiFileDatabase
from .file_manager import FileManager
from .config import DATABASE_PATH, DEFAULT_SEARCH_LIMIT
from .web_app import create_app, run_server

__all__ = [
    'MultiFileDatabase',
    'FileManager',
    'DATABASE_PATH',
    'DEFAULT_SEARCH_LIMIT',
    'create_app',
    'run_server'
]