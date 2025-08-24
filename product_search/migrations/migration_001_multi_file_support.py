"""
Migration to add multi-file support to the database
"""
import duckdb
import os
from datetime import datetime


def upgrade(db_path: str):
    """Add support for multiple imported files"""
    conn = duckdb.connect(db_path)
    
    try:
        # Create imported_files table to track all imported spreadsheets
        conn.execute("""
            CREATE TABLE IF NOT EXISTS imported_files (
                file_id INTEGER PRIMARY KEY,
                original_filename VARCHAR NOT NULL,
                import_date TIMESTAMP NOT NULL,
                row_count INTEGER DEFAULT 0,
                indexed_columns VARCHAR,
                file_size_mb DOUBLE,
                status VARCHAR DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Check if products table exists and has data
        table_exists = conn.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'products'
        """).fetchone()[0] > 0
        
        if table_exists:
            # Check if products table already has source_file_id column
            has_file_id = conn.execute("""
                SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_name = 'products' AND column_name = 'source_file_id'
            """).fetchone()[0] > 0
            
            if not has_file_id:
                try:
                    # Get existing data info first
                    row_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
                    
                    if row_count > 0:
                        print(f"Found existing data with {row_count} rows, preserving...")
                        
                        # Get all columns from existing table
                        columns_info = conn.execute("PRAGMA table_info(products)").fetchall()
                        existing_columns = [col[1] for col in columns_info]
                        
                        # Create backup table with existing data
                        conn.execute("CREATE TABLE products_backup AS SELECT * FROM products")
                        
                        # Drop the original table
                        conn.execute("DROP TABLE products")
                        
                        # Recreate table with source_file_id
                        column_defs = ["source_file_id INTEGER"]
                        for col in existing_columns:
                            if col.lower() != 'rowid':
                                column_defs.append(f'"{col}" VARCHAR')
                        
                        create_sql = f"""
                        CREATE TABLE products (
                            {', '.join(column_defs)}
                        )
                        """
                        conn.execute(create_sql)
                        
                        # Create entry for existing data as "Legacy Import"
                        conn.execute("""
                            INSERT INTO imported_files 
                            (file_id, original_filename, import_date, row_count, status)
                            VALUES (1, 'Legacy Import', CURRENT_TIMESTAMP, ?, 'active')
                        """, [row_count])
                        
                        # Copy data back with source_file_id = 1
                        existing_col_str = ', '.join([f'"{col}"' for col in existing_columns if col.lower() != 'rowid'])
                        insert_sql = f"""
                        INSERT INTO products (source_file_id, {existing_col_str})
                        SELECT 1, {existing_col_str} FROM products_backup
                        """
                        conn.execute(insert_sql)
                        
                        # Drop backup table
                        conn.execute("DROP TABLE products_backup")
                        
                        print("Successfully migrated existing data!")
                    else:
                        # Just add the column if no data exists
                        conn.execute("ALTER TABLE products ADD COLUMN source_file_id INTEGER")
                        
                except Exception as e:
                    print(f"Warning: Could not migrate existing data: {e}")
                    # Create entry for the attempt
                    try:
                        conn.execute("""
                            INSERT INTO imported_files 
                            (file_id, original_filename, import_date, row_count, status)
                            VALUES (1, 'Legacy Import (Migration Failed)', CURRENT_TIMESTAMP, 0, 'error')
                        """)
                    except:
                        pass
        
        # Create file_columns table to track indexed columns per file
        conn.execute("""
            CREATE TABLE IF NOT EXISTS file_columns (
                file_id INTEGER,
                column_name VARCHAR,
                is_indexed BOOLEAN DEFAULT FALSE,
                data_type VARCHAR,
                PRIMARY KEY (file_id, column_name)
            )
        """)
        
        # Create search_history table for tracking popular searches
        conn.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                search_id INTEGER PRIMARY KEY,
                search_term VARCHAR,
                result_count INTEGER,
                search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                execution_time_ms DOUBLE
            )
        """)
        
        # Create index on source_file_id for faster filtering
        if table_exists:
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_source_file 
                ON products(source_file_id)
            """)
        
        conn.commit()
        print("✅ Database migration completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def downgrade(db_path: str):
    """Revert the multi-file support changes"""
    conn = duckdb.connect(db_path)
    
    try:
        # Remove new tables
        conn.execute("DROP TABLE IF EXISTS imported_files")
        conn.execute("DROP TABLE IF EXISTS file_columns")
        conn.execute("DROP TABLE IF EXISTS search_history")
        
        # Remove source_file_id column from products if it exists
        table_exists = conn.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'products'
        """).fetchone()[0] > 0
        
        if table_exists:
            has_file_id = conn.execute("""
                SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_name = 'products' AND column_name = 'source_file_id'
            """).fetchone()[0] > 0
            
            if has_file_id:
                # DuckDB doesn't support DROP COLUMN directly, need to recreate table
                # Get all columns except source_file_id
                columns = conn.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'products' 
                    AND column_name != 'source_file_id'
                """).fetchall()
                
                column_list = [col[0] for col in columns]
                column_str = ', '.join([f'"{col}"' for col in column_list])
                
                # Create new table without source_file_id
                conn.execute(f"""
                    CREATE TABLE products_new AS 
                    SELECT {column_str} FROM products
                """)
                
                # Drop old table and rename new one
                conn.execute("DROP TABLE products")
                conn.execute("ALTER TABLE products_new RENAME TO products")
        
        conn.commit()
        print("✅ Database downgrade completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Downgrade failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    # For testing
    import sys
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
        upgrade(db_path)