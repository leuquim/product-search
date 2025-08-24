"""
Fast Excel import module using DuckDB native functions and optimizations
"""
import os
import time
import duckdb
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from tqdm import tqdm
from .config import FAST_IMPORT_CHUNK_SIZE, DUCKDB_MEMORY_LIMIT, DUCKDB_THREADS


class FastExcelImporter:
    """Optimized Excel importer using DuckDB native functions"""
    
    def __init__(self, db_connection: duckdb.DuckDBPyConnection = None):
        self.conn = db_connection
        self._configure_duckdb()
    
    def _configure_duckdb(self):
        """Configure DuckDB for optimal performance"""
        if self.conn:
            try:
                # Set memory limit and threads
                self.conn.execute(f"SET memory_limit='{DUCKDB_MEMORY_LIMIT}'")
                self.conn.execute(f"SET threads={DUCKDB_THREADS}")
                # Disable preservation of insertion order for better performance
                self.conn.execute("SET preserve_insertion_order=false")
            except Exception as e:
                print(f"Warning: Could not set DuckDB configuration: {e}")
    
    def try_duckdb_native_import(self, file_path: str, file_id: int, 
                                 indexed_columns: List[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Try to import using DuckDB's native Excel reading capability.
        Returns (success, result_dict)
        """
        start_time = time.time()
        
        try:
            print("🚀 Attempting DuckDB native Excel import...")
            
            # First, try to install/load spatial extension (contains Excel support in DuckDB 0.10.0)
            try:
                self.conn.execute("INSTALL spatial")
            except:
                pass  # Extension might already be installed
            
            try:
                self.conn.execute("LOAD spatial")
            except Exception as e:
                print(f"Could not load spatial extension: {e}")
                return False, {"error": "Spatial extension not available"}
            
            # Test if we can read the Excel file
            test_query = f"SELECT COUNT(*) FROM st_read('{file_path}')"
            try:
                row_count = self.conn.execute(test_query).fetchone()[0]
                print(f"✅ DuckDB can read Excel file: {row_count:,} rows detected")
            except:
                # Try alternative method for newer DuckDB versions
                try:
                    test_query = f"SELECT COUNT(*) FROM '{file_path}'"
                    row_count = self.conn.execute(test_query).fetchone()[0]
                    print(f"✅ DuckDB can read Excel file: {row_count:,} rows detected")
                except:
                    return False, {"error": "DuckDB cannot read this Excel file"}
            
            # Get column information
            columns_query = f"SELECT * FROM st_read('{file_path}') LIMIT 0"
            columns_result = self.conn.execute(columns_query).description
            columns = [col[0] for col in columns_result]
            
            print(f"📊 Found {len(columns)} columns")
            
            # Create temporary table with the Excel data
            temp_table = f"temp_import_{file_id}_{int(time.time())}"
            
            print("📥 Loading Excel data into DuckDB...")
            create_temp_query = f"""
            CREATE TEMPORARY TABLE {temp_table} AS 
            SELECT {file_id} as source_file_id, * 
            FROM st_read('{file_path}')
            """
            
            self.conn.execute(create_temp_query)
            
            # Get actual row count
            actual_count = self.conn.execute(f"SELECT COUNT(*) FROM {temp_table}").fetchone()[0]
            
            # Insert into products table
            print(f"💾 Inserting {actual_count:,} rows into products table...")
            
            # Ensure products table exists and has necessary columns
            self._ensure_table_structure(columns)
            
            # Bulk insert from temporary table
            insert_query = f"""
            INSERT INTO products 
            SELECT * FROM {temp_table}
            """
            
            self.conn.execute(insert_query)
            
            # Clean up temporary table
            self.conn.execute(f"DROP TABLE {temp_table}")
            
            # Commit the transaction
            self.conn.commit()
            
            duration = time.time() - start_time
            
            print(f"✅ Native import completed: {actual_count:,} rows in {duration:.2f}s")
            print(f"⚡ Speed: {actual_count/duration:.0f} rows/second")
            
            return True, {
                "success": True,
                "method": "duckdb_native",
                "rows_imported": actual_count,
                "duration_seconds": round(duration, 2),
                "rows_per_second": round(actual_count/duration)
            }
            
        except Exception as e:
            print(f"❌ DuckDB native import failed: {e}")
            return False, {"error": str(e)}
    
    def import_with_pandas(self, file_path: str, file_id: int,
                          indexed_columns: List[str] = None) -> Dict[str, Any]:
        """
        Import using pandas with DuckDB integration for better performance than openpyxl
        """
        start_time = time.time()
        
        try:
            print("📊 Using pandas for Excel import...")
            
            # Read Excel file with pandas (uses openpyxl but optimized)
            print("📖 Reading Excel file with pandas...")
            df = pd.read_excel(file_path, engine='openpyxl')
            
            row_count = len(df)
            col_count = len(df.columns)
            
            print(f"✅ Loaded {row_count:,} rows, {col_count} columns")
            
            # Add source_file_id column
            df['source_file_id'] = file_id
            
            # Reorder columns to have source_file_id first
            cols = ['source_file_id'] + [col for col in df.columns if col != 'source_file_id']
            df = df[cols]
            
            # Ensure products table exists
            self._ensure_table_structure(list(df.columns)[1:])  # Exclude source_file_id
            
            # Register DataFrame with DuckDB for fast insertion
            print("💾 Inserting data into DuckDB...")
            self.conn.register('df_import', df)
            
            # Use SQL to insert from the registered DataFrame
            insert_query = """
            INSERT INTO products 
            SELECT * FROM df_import
            """
            
            self.conn.execute(insert_query)
            
            # Unregister the DataFrame
            self.conn.unregister('df_import')
            
            # Commit the transaction
            self.conn.commit()
            
            duration = time.time() - start_time
            
            print(f"✅ Pandas import completed: {row_count:,} rows in {duration:.2f}s")
            print(f"⚡ Speed: {row_count/duration:.0f} rows/second")
            
            return {
                "success": True,
                "method": "pandas",
                "rows_imported": row_count,
                "duration_seconds": round(duration, 2),
                "rows_per_second": round(row_count/duration)
            }
            
        except Exception as e:
            print(f"❌ Pandas import failed: {e}")
            self.conn.rollback()
            return {
                "success": False,
                "method": "pandas",
                "error": str(e)
            }
    
    def import_with_copy(self, file_path: str, file_id: int,
                        indexed_columns: List[str] = None) -> Dict[str, Any]:
        """
        Import using DuckDB's COPY statement (for CSV files or converted data)
        """
        start_time = time.time()
        
        try:
            print("📋 Using COPY statement for import...")
            
            # First convert Excel to CSV if needed (using pandas)
            df = pd.read_excel(file_path, engine='openpyxl')
            df['source_file_id'] = file_id
            
            # Create temporary CSV
            temp_csv = f"/tmp/temp_import_{file_id}_{int(time.time())}.csv"
            df.to_csv(temp_csv, index=False)
            
            row_count = len(df)
            
            # Ensure table structure
            self._ensure_table_structure(list(df.columns)[1:])
            
            # Use COPY for fast import
            copy_query = f"""
            COPY products FROM '{temp_csv}' (FORMAT CSV, HEADER TRUE)
            """
            
            self.conn.execute(copy_query)
            self.conn.commit()
            
            # Clean up temp file
            os.remove(temp_csv)
            
            duration = time.time() - start_time
            
            print(f"✅ COPY import completed: {row_count:,} rows in {duration:.2f}s")
            
            return {
                "success": True,
                "method": "copy",
                "rows_imported": row_count,
                "duration_seconds": round(duration, 2)
            }
            
        except Exception as e:
            print(f"❌ COPY import failed: {e}")
            return {
                "success": False,
                "method": "copy",
                "error": str(e)
            }
    
    def _ensure_table_structure(self, columns: List[str]):
        """Ensure products table exists with necessary columns"""
        try:
            # Check if table exists
            table_exists = self.conn.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'products'
            """).fetchone()[0] > 0
            
            if not table_exists:
                # Create table with source_file_id and dynamic columns
                column_defs = ["source_file_id INTEGER"]
                for col in columns:
                    clean_col = self._clean_column_name(col)
                    column_defs.append(f'"{clean_col}" VARCHAR')
                
                create_sql = f"""
                CREATE TABLE products (
                    {', '.join(column_defs)}
                )
                """
                self.conn.execute(create_sql)
            else:
                # Ensure all columns exist
                existing_columns = self.conn.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'products'
                """).fetchall()
                
                existing_set = {col[0].lower() for col in existing_columns}
                
                for col in columns:
                    clean_col = self._clean_column_name(col)
                    if clean_col.lower() not in existing_set:
                        try:
                            self.conn.execute(f"""
                                ALTER TABLE products ADD COLUMN "{clean_col}" VARCHAR
                            """)
                        except:
                            pass  # Column might already exist
                            
        except Exception as e:
            print(f"Warning: Table structure check failed: {e}")
    
    def _clean_column_name(self, col: str) -> str:
        """Clean column names for database compatibility"""
        clean_col = str(col).strip()
        clean_col = clean_col.replace(' ', '_').replace('-', '_').replace('.', '_')
        clean_col = clean_col.replace('/', '_').replace('(', '').replace(')', '')
        clean_col = clean_col.replace('[', '').replace(']', '').replace(',', '_')
        clean_col = ''.join(c for c in clean_col if c.isalnum() or c == '_')
        if clean_col and clean_col[0].isdigit():
            clean_col = f"col_{clean_col}"
        if not clean_col:
            clean_col = "unknown_column"
        return clean_col
    
    def auto_import(self, file_path: str, file_id: int, 
                   indexed_columns: List[str] = None) -> Dict[str, Any]:
        """
        Automatically try the fastest import method available
        """
        print(f"🔍 Auto-detecting best import method for {os.path.basename(file_path)}...")
        
        # Try methods in order of performance
        
        # 1. Try DuckDB native (fastest)
        success, result = self.try_duckdb_native_import(file_path, file_id, indexed_columns)
        if success:
            return result
        
        # 2. Try pandas method (second fastest)
        result = self.import_with_pandas(file_path, file_id, indexed_columns)
        if result.get("success"):
            return result
        
        # 3. If all else fails, return error
        return {
            "success": False,
            "error": "All fast import methods failed. Please use standard import."
        }