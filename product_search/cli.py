import click
import os
import json
import csv
from typing import Dict, Any
from .database import ProductDatabase
from .importer import ExcelImporter, import_excel_file, preview_excel_file
from .config import DEFAULT_SEARCH_LIMIT


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Product Search CLI - Import and search Excel product data"""
    pass


@cli.command()
@click.argument('excel_path', type=click.Path(exists=True))
@click.option('--clear', is_flag=True, help='Clear existing data before import')
@click.option('--preview', is_flag=True, help='Preview file without importing')
def import_data(excel_path: str, clear: bool, preview: bool):
    """Import Excel file into database"""
    
    if preview:
        try:
            print(f"Previewing: {excel_path}")
            preview_data = preview_excel_file(excel_path, 5)
            
            if preview_data:
                print(f"\nFirst 5 rows:")
                for i, row in enumerate(preview_data, 1):
                    print(f"\nRow {i}:")
                    for key, value in row.items():
                        print(f"  {key}: {value}")
            else:
                print("No data found in file")
                
        except Exception as e:
            click.echo(f"Error previewing file: {e}", err=True)
            return
    else:
        try:
            print(f"Starting import of: {excel_path}")
            result = import_excel_file(excel_path, clear)
            
            if result['success']:
                print(f"\n✅ Import successful!")
                print(f"Imported {result['total_imported']:,} rows in {result['duration_seconds']}s")
            else:
                print(f"❌ Import failed: {result['error']}")
                
        except Exception as e:
            click.echo(f"Error importing file: {e}", err=True)


@cli.command()
@click.argument('query', required=False)
@click.option('--limit', '-l', default=DEFAULT_SEARCH_LIMIT, help='Maximum results to return')
@click.option('--offset', '-o', default=0, help='Number of results to skip')
@click.option('--sort', '-s', default='rowid', help='Sort by column (rowid, ASSEMBLY, DESCRIPTION)')
@click.option('--format', '-f', type=click.Choice(['table', 'json', 'csv']), default='table', help='Output format')
@click.option('--interactive', '-i', is_flag=True, help='Interactive search mode')
def search(query: str, limit: int, offset: int, sort: str, format: str, interactive: bool):
    """Search products in database"""
    
    if interactive:
        interactive_search()
        return
    
    if not query:
        click.echo("Please provide a search query or use --interactive mode")
        return
    
    try:
        with ProductDatabase() as db:
            results, total_count = db.search(query, limit, offset, sort)
            
            if not results:
                print(f"No results found for: '{query}'")
                return
            
            print(f"Found {total_count} matches (showing {len(results)})")
            
            if format == 'json':
                click.echo(json.dumps(results, indent=2))
            elif format == 'csv':
                if results:
                    writer = csv.DictWriter(click.get_text_stream('stdout'), fieldnames=results[0].keys())
                    writer.writeheader()
                    writer.writerows(results)
            else:  # table format
                display_results_table(results)
                
    except Exception as e:
        click.echo(f"Search error: {e}", err=True)


def interactive_search():
    """Interactive search mode"""
    print("🔍 Interactive Search Mode")
    print("Type your search queries (press Enter to search, 'quit' to exit)")
    print("Commands: 'stats', 'help', 'quit'\n")
    
    with ProductDatabase() as db:
        while True:
            try:
                query = input("Search> ").strip()
                
                if not query:
                    continue
                    
                if query.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                    
                if query.lower() == 'help':
                    print("Commands:")
                    print("  stats     - Show database statistics")
                    print("  help      - Show this help")
                    print("  quit      - Exit interactive mode")
                    print("  <query>   - Search products")
                    continue
                    
                if query.lower() == 'stats':
                    stats = db.get_stats()
                    print(f"Database Statistics:")
                    for key, value in stats.items():
                        print(f"  {key}: {value}")
                    continue
                
                # Perform search
                results, total_count = db.search(query, DEFAULT_SEARCH_LIMIT)
                
                if not results:
                    print(f"No results found for: '{query}'\n")
                    continue
                
                print(f"Found {total_count} matches (showing first {len(results)}):")
                display_results_table(results[:5])  # Show first 5 for readability
                
                if len(results) > 5:
                    print(f"... and {len(results) - 5} more results")
                print()
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}\n")


def display_results_table(results):
    """Display results in table format"""
    if not results:
        return
    
    # Get all column names
    columns = list(results[0].keys())
    
    # Calculate column widths
    col_widths = {}
    for col in columns:
        max_width = max(
            len(str(col)),
            max(len(str(row.get(col, ''))) for row in results) if results else 0
        )
        col_widths[col] = min(max_width + 2, 30)  # Cap at 30 chars
    
    # Print header
    header = "| " + " | ".join(col.ljust(col_widths[col])[:col_widths[col]] for col in columns) + " |"
    separator = "+" + "+".join("-" * (col_widths[col] + 2) for col in columns) + "+"
    
    print(separator)
    print(header)
    print(separator)
    
    # Print rows
    for row in results:
        row_str = "| " + " | ".join(
            str(row.get(col, '')).ljust(col_widths[col])[:col_widths[col]] 
            for col in columns
        ) + " |"
        print(row_str)
    
    print(separator)


@cli.command()
def stats():
    """Show database statistics"""
    try:
        with ProductDatabase() as db:
            stats = db.get_stats()
            
            print("📊 Database Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
                
    except Exception as e:
        click.echo(f"Error getting stats: {e}", err=True)


@cli.command()
@click.option('--confirm', is_flag=True, help='Confirm deletion without prompt')
def clear(confirm: bool):
    """Clear all data from database"""
    
    if not confirm:
        if not click.confirm('Are you sure you want to clear all data?'):
            print("Operation cancelled")
            return
    
    try:
        with ProductDatabase() as db:
            db.clear_table()
            print("✅ Database cleared successfully")
            
    except Exception as e:
        click.echo(f"Error clearing database: {e}", err=True)


@cli.command()
@click.argument('output_path', type=click.Path())
@click.option('--format', '-f', type=click.Choice(['csv', 'json']), default='csv', help='Export format')
@click.option('--query', '-q', help='Filter results with search query')
@click.option('--limit', '-l', default=10000, help='Maximum records to export')
def export(output_path: str, format: str, query: str, limit: int):
    """Export data to CSV or JSON"""
    
    try:
        with ProductDatabase() as db:
            if query:
                results, total_count = db.search(query, limit)
                print(f"Exporting {len(results)} search results...")
            else:
                results, total_count = db.get_all(limit)
                print(f"Exporting {len(results)} records...")
            
            if not results:
                print("No data to export")
                return
            
            if format == 'json':
                with open(output_path, 'w') as f:
                    json.dump(results, f, indent=2)
            else:  # csv
                with open(output_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=results[0].keys())
                    writer.writeheader()
                    writer.writerows(results)
            
            print(f"✅ Exported {len(results)} records to {output_path}")
            
    except Exception as e:
        click.echo(f"Export error: {e}", err=True)


if __name__ == '__main__':
    cli()