"""
Enhanced Flask web application with multi-file support
"""
from flask import Flask, render_template, request, jsonify, send_file
import time
import os
import tempfile
from werkzeug.utils import secure_filename
from .database import MultiFileDatabase
from .file_manager import FileManager
from .lenovo_search import search_lenovo_for_parts, LenovoSearcher
from .config import WEB_HOST, WEB_PORT, WEB_DEBUG, DEFAULT_SEARCH_LIMIT


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}


def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Main search page"""
    with MultiFileDatabase() as db:
        stats = db.get_stats()
    return render_template('index.html', stats=stats)


@app.route('/files')
def files_page():
    """File management page"""
    return render_template('files.html')


@app.route('/api/search')
def api_search():
    """API endpoint for search requests with multi-file support"""
    start_time = time.time()
    
    query = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', DEFAULT_SEARCH_LIMIT)), 1000)
    offset = int(request.args.get('offset', 0))
    file_ids = request.args.getlist('files[]', type=int)
    group_by_file = request.args.get('group', 'false').lower() == 'true'
    visible_columns = request.args.getlist('columns[]')
    
    try:
        with MultiFileDatabase() as db:
            if group_by_file:
                # Return results grouped by file
                result = db.search_grouped(query, file_ids if file_ids else None)
                
                # Filter grouped results by visible columns if specified
                if visible_columns and result['files']:
                    for filename, file_data in result['files'].items():
                        if file_data['results']:
                            filtered_results = []
                            for row in file_data['results']:
                                filtered_row = {}
                                # Always include source file info
                                if '_source_file' in row:
                                    filtered_row['_source_file'] = row['_source_file']
                                if 'source_file_id' in row:
                                    filtered_row['source_file_id'] = row['source_file_id']
                                
                                # Add requested visible columns
                                for col in visible_columns:
                                    if col in row:
                                        filtered_row[col] = row[col]
                                filtered_results.append(filtered_row)
                            file_data['results'] = filtered_results
                
                search_time = time.time() - start_time
                
                return jsonify({
                    'success': True,
                    'grouped': True,
                    'files': result['files'],
                    'total_count': result['total_count'],
                    'file_count': result['file_count'],
                    'search_time': round(search_time * 1000, 2),
                    'query': query,
                    'visible_columns': visible_columns
                })
            else:
                # Return flat results
                results, total_count = db.search(query, file_ids if file_ids else None, limit, offset)
                
                # Filter results by visible columns if specified
                if visible_columns and results:
                    filtered_results = []
                    for row in results:
                        filtered_row = {}
                        # Always include source file info
                        if '_source_file' in row:
                            filtered_row['_source_file'] = row['_source_file']
                        if 'source_file_id' in row:
                            filtered_row['source_file_id'] = row['source_file_id']
                        
                        # Add requested visible columns
                        for col in visible_columns:
                            if col in row:
                                filtered_row[col] = row[col]
                        filtered_results.append(filtered_row)
                    results = filtered_results
                
                search_time = time.time() - start_time
                
                return jsonify({
                    'success': True,
                    'grouped': False,
                    'results': results,
                    'total_count': total_count,
                    'returned_count': len(results),
                    'search_time': round(search_time * 1000, 2),
                    'query': query,
                    'offset': offset,
                    'limit': limit,
                    'visible_columns': visible_columns
                })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'results': [],
            'total_count': 0
        }), 500


@app.route('/api/files')
def api_get_files():
    """API endpoint to get list of imported files"""
    try:
        with MultiFileDatabase() as db:
            files = db.get_imported_files()
            stats = db.get_stats()
            
        return jsonify({
            'success': True,
            'files': files,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/files/preview', methods=['POST'])
def api_preview_file():
    """API endpoint to preview a file before importing"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Invalid file type'}), 400
    
    try:
        # Save temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)
        
        # Preview the file
        manager = FileManager()
        result = manager.preview_file(temp_path)
        
        # Clean up temp file
        os.remove(temp_path)
        
        return jsonify(result)
        
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/files/import', methods=['POST'])
def api_import_file():
    """API endpoint to import a file"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Invalid file type'}), 400
    
    try:
        # Get indexed columns
        import json
        indexed_columns = json.loads(request.form.get('indexed_columns', '[]'))
        
        # Save temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)
        
        # Import the file
        manager = FileManager()
        result = manager.import_file(temp_path, indexed_columns)
        
        # Clean up temp file
        os.remove(temp_path)
        
        return jsonify(result)
        
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/files/<int:file_id>', methods=['DELETE'])
def api_delete_file(file_id):
    """API endpoint to delete an imported file"""
    try:
        manager = FileManager()
        result = manager.delete_file(file_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/files/<int:file_id>/details')
def api_file_details(file_id):
    """API endpoint to get detailed info about a file"""
    try:
        manager = FileManager()
        result = manager.get_file_details(file_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/files/<int:file_id>/indexes', methods=['PUT'])
def api_update_indexes(file_id):
    """API endpoint to update indexed columns for a file"""
    try:
        import json
        data = request.get_json()
        indexed_columns = data.get('indexed_columns', [])
        
        manager = FileManager()
        result = manager.update_indexes(file_id, indexed_columns)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/export')
def api_export_results():
    """API endpoint to export search results to CSV"""
    query = request.args.get('q', '').strip()
    file_ids = request.args.getlist('files[]', type=int)
    
    try:
        manager = FileManager()
        result = manager.export_search_results(query, file_ids if file_ids else None)
        
        if result['success']:
            return send_file(result['output_path'], as_attachment=True, 
                           download_name=os.path.basename(result['output_path']))
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stats')
def api_stats():
    """API endpoint for database statistics"""
    try:
        with MultiFileDatabase() as db:
            stats = db.get_stats()
            
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/columns')
def api_columns():
    """API endpoint to get all unique columns across files"""
    try:
        with MultiFileDatabase() as db:
            # First try to get columns from file_columns table
            columns = db.conn.execute("""
                SELECT DISTINCT column_name 
                FROM file_columns 
                ORDER BY column_name
            """).fetchall()
            
            column_list = [col[0] for col in columns]
            
            # If file_columns table is empty, get columns directly from products table
            if not column_list:
                try:
                    # Get columns from products table schema
                    table_info = db.conn.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'products'
                        AND column_name NOT IN ('source_file_id')
                        ORDER BY column_name
                    """).fetchall()
                    
                    column_list = [col[0] for col in table_info]
                    print(f"Loaded {len(column_list)} columns from products table schema")
                    
                except Exception as schema_error:
                    # Fallback to PRAGMA table_info for older DuckDB versions
                    table_info = db.conn.execute("PRAGMA table_info(products)").fetchall()
                    column_list = [col[1] for col in table_info 
                                 if col[1] not in ['source_file_id']]
                    print(f"Loaded {len(column_list)} columns from PRAGMA table_info")
            
        return jsonify({
            'success': True,
            'columns': column_list
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'columns': []
        }), 500


# Keep existing Lenovo search endpoints
@app.route('/api/lenovo/search')
def api_lenovo_search():
    """API endpoint for Lenovo Press search"""
    start_time = time.time()
    
    search_term = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 10)), 20)
    
    if not search_term:
        return jsonify({
            'success': False,
            'error': 'Search term is required'
        }), 400
    
    try:
        searcher = LenovoSearcher()
        
        # If the search term looks like a part number (short alphanumeric), 
        # also scan pages for that part number
        if len(search_term) <= 10 and search_term.replace('-', '').replace('_', '').isalnum():
            print(f"🔍 Performing enhanced search with part number scanning for: {search_term}")
            results = searcher.search_and_scan(search_term, [search_term], max_pages=limit)
        else:
            # Just do basic search for longer terms
            results = searcher.search_lenovo_press(search_term, limit)
        
        search_time = time.time() - start_time
        results['search_time'] = round(search_time * 1000, 2)
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'search_time': round((time.time() - start_time) * 1000, 2)
        }), 500


def create_app():
    """Factory function to create Flask app"""
    return app


def run_server(host=WEB_HOST, port=WEB_PORT, debug=WEB_DEBUG):
    """Run the Flask development server"""
    print(f"🚀 Starting Enhanced Product Search web server...")
    print(f"✨ Now with multi-file support!")
    
    if host == '0.0.0.0':
        print(f"📍 Local access: http://localhost:{port}")
        print(f"🌐 Network access: http://[YOUR-IP]:{port}")
        print(f"📁 File management: http://localhost:{port}/files")
        print(f"💡 Find your IP with: ipconfig (Windows) or hostname -I (Linux)")
    else:
        print(f"📍 URL: http://{host}:{port}")
        print(f"📁 File management: http://{host}:{port}/files")
    
    print(f"🔍 Search across multiple Excel files")
    print(f"⏹️  Press Ctrl+C to stop the server")
    
    try:
        app.run(host=host, port=port, debug=debug)
    except OSError as e:
        if "access" in str(e).lower() or "permission" in str(e).lower():
            print(f"\n❌ Port {port} access denied. Trying alternative ports...")
            
            alternative_ports = [8081, 8082, 3000, 3001, 5001, 5002]
            for alt_port in alternative_ports:
                try:
                    print(f"🔄 Trying port {alt_port}...")
                    app.run(host=host, port=alt_port, debug=debug)
                    break
                except OSError:
                    continue
            else:
                print("❌ Could not find an available port.")
        else:
            print(f"❌ Server error: {e}")
            raise


if __name__ == '__main__':
    run_server()