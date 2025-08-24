import requests
from bs4 import BeautifulSoup
import re
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin


class LenovoSearcher:
    def __init__(self):
        self.base_url = "https://lenovopress.lenovo.com"
        self.search_api_url = f"{self.base_url}/press/search/jsonquery"
        
        # Simplified headers for API requests
        self.headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'DNT': '1',
            'Origin': self.base_url,
            'Referer': f'{self.base_url}/search',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }

    def search_lenovo_press(self, term: str, limit: int = 20) -> Dict[str, Any]:
        """Search Lenovo Press documentation"""
        try:
            # Prepare search data
            search_data = {
                'term': term,
                'resource_type': '',
                'drafts': '0',
                'withdrawn': '0',
                'entitled': '0',
                'sort': 'relevance',
                'limit': str(limit),
                'page': '1'
            }
            
            print(f"🔍 Searching Lenovo Press for: {term}")
            response = requests.post(
                self.search_api_url,
                headers=self.headers,
                data=search_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    # Build full URLs for relative links
                    items = data.get('items', [])
                    for item in items:
                        if 'relativeLink' in item:
                            item['fullUrl'] = urljoin(self.base_url, item['relativeLink'])
                    
                    return {
                        'success': True,
                        'items': items,
                        'total_items': data.get('pager', {}).get('total_items', 0),
                        'total_pages': data.get('pager', {}).get('total_pages', 0)
                    }
                else:
                    return {'success': False, 'error': 'API returned error status'}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            print(f"❌ Error searching Lenovo Press: {e}")
            return {'success': False, 'error': str(e)}

    def scrape_lenovo_page(self, url: str, part_numbers: List[str]) -> Dict[str, Any]:
        """Scrape a Lenovo Press page for matching part numbers"""
        try:
            print(f"📄 Scanning page: {url}")
            
            response = requests.get(url, headers={
                'User-Agent': self.headers['User-Agent'],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'DNT': '1'
            }, timeout=15)
            
            if response.status_code != 200:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for matches in the page
            matches = []
            page_text = soup.get_text().upper()
            
            for part_number in part_numbers:
                part_upper = part_number.upper()
                if part_upper in page_text:
                    # Found a match, try to extract table data
                    table_data = self.extract_table_data(soup, part_number)
                    matches.append({
                        'part_number': part_number,
                        'found': True,
                        'table_data': table_data,
                        'url': url
                    })
            
            return {
                'success': True,
                'url': url,
                'matches': matches,
                'total_matches': len(matches)
            }
            
        except Exception as e:
            print(f"❌ Error scraping page {url}: {e}")
            return {'success': False, 'error': str(e), 'url': url}

    def extract_table_data(self, soup: BeautifulSoup, part_number: str) -> List[Dict[str, Any]]:
        """Extract table data containing the specified part number"""
        try:
            tables = soup.find_all('table')
            extracted_tables = []
            
            for table in tables:
                table_text = table.get_text().upper()
                if part_number.upper() in table_text:
                    # Extract table structure
                    table_data = self.parse_table_structure(table)
                    if table_data:
                        extracted_tables.append({
                            'headers': table_data.get('headers', []),
                            'rows': table_data.get('rows', []),
                            'caption': table_data.get('caption', ''),
                            'row_count': len(table_data.get('rows', []))
                        })
            
            return extracted_tables
            
        except Exception as e:
            print(f"❌ Error extracting table data: {e}")
            return []

    def parse_table_structure(self, table) -> Optional[Dict[str, Any]]:
        """Parse HTML table into structured data"""
        try:
            # Get table caption if exists
            caption = ''
            caption_elem = table.find('caption')
            if caption_elem:
                caption = caption_elem.get_text().strip()
            
            # Extract headers
            headers = []
            header_row = table.find('tr')
            if header_row:
                for th in header_row.find_all(['th', 'td']):
                    headers.append(th.get_text().strip())
            
            # Extract data rows
            rows = []
            all_rows = table.find_all('tr')
            
            # Skip header row if it exists
            data_rows = all_rows[1:] if len(all_rows) > 1 else all_rows
            
            for row in data_rows:
                cells = row.find_all(['td', 'th'])
                if cells:  # Only add rows with actual cells
                    row_data = []
                    for cell in cells:
                        row_data.append(cell.get_text().strip())
                    rows.append(row_data)
            
            if headers or rows:
                return {
                    'caption': caption,
                    'headers': headers,
                    'rows': rows
                }
            
            return None
            
        except Exception as e:
            print(f"❌ Error parsing table structure: {e}")
            return None

    def search_and_scan(self, search_term: str, part_numbers: List[str], max_pages: int = 10) -> Dict[str, Any]:
        """Complete workflow: search Lenovo Press and scan results for part numbers"""
        start_time = time.time()
        
        try:
            # Step 1: Search Lenovo Press
            search_results = self.search_lenovo_press(search_term, limit=max_pages)
            
            if not search_results.get('success'):
                return search_results
            
            items = search_results.get('items', [])
            if not items:
                return {
                    'success': True,
                    'search_results': search_results,
                    'scan_results': [],
                    'total_matches': 0,
                    'pages_scanned': 0,
                    'duration': time.time() - start_time
                }
            
            # Step 2: Scan each page for part numbers
            scan_results = []
            total_matches = 0
            
            print(f"📊 Found {len(items)} documentation pages to scan")
            
            for i, item in enumerate(items):
                url = item.get('fullUrl')
                if url:
                    print(f"🔍 Scanning page {i+1}/{len(items)}: {item.get('title', 'Unknown')}")
                    
                    scan_result = self.scrape_lenovo_page(url, part_numbers)
                    scan_result['page_info'] = {
                        'title': item.get('title', ''),
                        'resourceType': item.get('resourceType', ''),
                        'publishDate': item.get('publishDate', ''),
                        'lastUpdate': item.get('lastUpdate', '')
                    }
                    scan_results.append(scan_result)
                    
                    if scan_result.get('success'):
                        total_matches += scan_result.get('total_matches', 0)
                    
                    # Small delay to be respectful
                    time.sleep(0.5)
            
            duration = time.time() - start_time
            
            return {
                'success': True,
                'search_results': search_results,
                'scan_results': scan_results,
                'total_matches': total_matches,
                'pages_scanned': len(scan_results),
                'duration': round(duration, 2)
            }
            
        except Exception as e:
            print(f"❌ Error in search and scan: {e}")
            return {
                'success': False,
                'error': str(e),
                'duration': time.time() - start_time
            }


def search_lenovo_for_parts(search_term: str, part_numbers: List[str], max_pages: int = 10) -> Dict[str, Any]:
    """Convenience function for searching Lenovo Press"""
    searcher = LenovoSearcher()
    return searcher.search_and_scan(search_term, part_numbers, max_pages)