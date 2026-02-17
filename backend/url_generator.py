"""
URL Generator Service
Handles URL pattern detection and next page URL generation
"""

import re
import sys
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


class URLGenerator:
    """Generate next page URLs from original URLs"""

    # Common pagination patterns
    PATTERNS = {
        'query_page': r'[?&]page=(\d+)',
        'query_p': r'[?&]p=(\d+)',
        'query_offset': r'[?&]offset=(\d+)',
        'query_start': r'[?&]start=(\d+)',
        'path_page': r'/page[/-](\d+)',
        'path_p': r'/p/(\d+)',
        'path_products': r'/products/page[/-](\d+)',
        'query_custom': r'[?&](\w+)=(\d+)',  # Generic catch-all
    }

    @staticmethod
    def detect_pattern(url: str):
        """Detect pagination pattern in URL"""
        url_lower = url.lower()

        # Check each pattern
        for pattern_name, pattern_regex in URLGenerator.PATTERNS.items():
            match = re.search(pattern_regex, url_lower)
            if match:
                return {
                    'pattern_type': pattern_name,
                    'pattern_regex': pattern_regex,
                    'current_page': int(match.group(1)) if match.lastindex >= 1 else 1,
                    'match_groups': match.groups()
                }

        # No pattern found
        return {
            'pattern_type': 'unknown',
            'pattern_regex': None,
            'current_page': 1,
            'match_groups': []
        }

    @staticmethod
    def generate_next_url(url: str, next_page_number: int, pattern_info: dict = None):
        """Generate next page URL"""
        
        if pattern_info is None:
            pattern_info = URLGenerator.detect_pattern(url)

        pattern_type = pattern_info.get('pattern_type')

        try:
            # Query parameter patterns
            if 'query_page' in pattern_type or pattern_type == 'query_page':
                return re.sub(r'([?&]page=)\d+', rf'\g<1>{next_page_number}', url)

            elif 'query_p' in pattern_type or pattern_type == 'query_p':
                return re.sub(r'([?&]p=)\d+', rf'\g<1>{next_page_number}', url)

            elif 'query_offset' in pattern_type or pattern_type == 'query_offset':
                # For offset-based, we might need to calculate offset
                # Assuming each page has items_per_page (default 10 or 20)
                offset = (next_page_number - 1) * 20
                return re.sub(r'([?&]offset=)\d+', rf'\g<1>{offset}', url)

            elif 'query_start' in pattern_type or pattern_type == 'query_start':
                start = (next_page_number - 1) * 20
                return re.sub(r'([?&]start=)\d+', rf'\g<1>{start}', url)

            # Path-based patterns
            elif 'path_page' in pattern_type or pattern_type == 'path_page':
                return re.sub(r'/page[/-]\d+', f'/page-{next_page_number}', url)

            elif 'path_p' in pattern_type or pattern_type == 'path_p':
                return re.sub(r'/p/\d+', f'/p/{next_page_number}', url)

            elif 'path_products' in pattern_type or pattern_type == 'path_products':
                return re.sub(r'/products/page[/-]\d+', f'/products/page-{next_page_number}', url)

            elif pattern_type == 'query_custom':
                # Generic query parameter replacement
                if pattern_info.get('match_groups'):
                    param_name = pattern_info['match_groups'][0]
                    return re.sub(rf'([?&]{param_name}=)\d+', rf'\g<1>{next_page_number}', url)

            else:
                # Unknown pattern - try best guess
                # Try common patterns as fallback
                result = re.sub(r'([?&]page=)\d+', rf'\g<1>{next_page_number}', url)
                if result != url:
                    return result

                result = re.sub(r'([?&]p=)\d+', rf'\g<1>{next_page_number}', url)
                if result != url:
                    return result

                # If no substitution worked, append as query parameter
                separator = '&' if '?' in url else '?'
                return f"{url}{separator}page={next_page_number}"

        except Exception as e:
            print(f"[WARNING] Error generating next URL: {str(e)}", file=sys.stderr)
            # Fallback: append page parameter
            separator = '&' if '?' in url else '?'
            return f"{url}{separator}page={next_page_number}"

        return url

    @staticmethod
    def extract_page_number(url: str):
        """Extract current page number from URL"""
        pattern_info = URLGenerator.detect_pattern(url)
        return pattern_info.get('current_page', 1)

    @staticmethod
    def validate_url(url: str):
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    @staticmethod
    def get_base_url(url: str):
        """Get base URL without query parameters"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
