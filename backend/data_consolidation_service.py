"""
Data Consolidation Service
Handles CSV merging, deduplication, and page counting
"""

import sys
import csv
import json
import hashlib
from io import StringIO
from typing import List, Dict, Tuple


class DataConsolidationService:
    """Service for consolidating and deduplicating scraped data"""

    @staticmethod
    def parse_csv_to_records(csv_text: str) -> Tuple[List[str], List[Dict]]:
        """
        Parse CSV text to headers and records
        Returns: (headers, records)
        """
        try:
            lines = csv_text.strip().split('\n')
            if not lines:
                return [], []

            # Parse header
            reader = csv.DictReader(lines)
            records = list(reader)
            headers = reader.fieldnames or []

            return headers, records
        except Exception as e:
            print(f"[ERROR] Error parsing CSV: {str(e)}", file=sys.stderr)
            return [], []

    @staticmethod
    def get_page_count_from_csv(csv_text: str) -> int:
        """
        Extract page count from CSV data
        Assumes there's a 'page' or 'page_number' column
        """
        try:
            headers, records = DataConsolidationService.parse_csv_to_records(csv_text)

            if not records:
                return 0

            # Try to find page column
            page_column = None
            for header in headers:
                if 'page' in header.lower():
                    page_column = header
                    break

            if not page_column:
                # If no page column, assume all records are from same page
                return 1

            # Get max page number
            max_page = 0
            for record in records:
                try:
                    page_num = int(record.get(page_column, 0))
                    max_page = max(max_page, page_num)
                except (ValueError, TypeError):
                    pass

            return max_page if max_page > 0 else 1
        except Exception as e:
            print(f"[WARNING] Error extracting page count: {str(e)}", file=sys.stderr)
            return 1

    @staticmethod
    def generate_record_hash(record: Dict) -> str:
        """
        Generate hash of a record for deduplication
        Uses all values to create unique hash
        """
        try:
            # Sort and stringify for consistent hashing
            record_str = json.dumps(record, sort_keys=True, default=str)
            return hashlib.md5(record_str.encode()).hexdigest()
        except Exception as e:
            print(f"[WARNING] Error generating hash: {str(e)}", file=sys.stderr)
            return hashlib.md5(json.dumps(record).encode()).hexdigest()

    @staticmethod
    def merge_csv_data(csv_files: List[str], deduplicate: bool = True) -> Tuple[str, int, int]:
        """
        Merge multiple CSV files
        Returns: (merged_csv, total_records, deduplicated_count)
        """
        all_records = []
        headers = None
        record_hashes = set()
        duplicates_found = 0

        try:
            for csv_text in csv_files:
                csv_headers, records = DataConsolidationService.parse_csv_to_records(csv_text)

                # Use first file's headers
                if headers is None:
                    headers = csv_headers

                # Add records
                for record in records:
                    if deduplicate:
                        record_hash = DataConsolidationService.generate_record_hash(record)
                        if record_hash in record_hashes:
                            duplicates_found += 1
                            continue
                        record_hashes.add(record_hash)

                    all_records.append(record)

            if not headers:
                return "", 0, 0

            # Convert back to CSV
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=headers)
            writer.writeheader()
            writer.writerows(all_records)

            merged_csv = output.getvalue()
            return merged_csv, len(all_records), duplicates_found

        except Exception as e:
            print(f"[ERROR] Error merging CSV files: {str(e)}", file=sys.stderr)
            return "", 0, 0

    @staticmethod
    def identify_unique_records(records: List[Dict], unique_key: str = None) -> Tuple[List[Dict], int]:
        """
        Identify and remove duplicate records
        Can use a specific column as unique key, or hash entire record
        Returns: (unique_records, duplicates_removed)
        """
        seen = set()
        unique_records = []
        duplicates = 0

        try:
            for record in records:
                if unique_key and unique_key in record:
                    # Use specific column as unique key
                    key = record[unique_key]
                else:
                    # Use hash of entire record
                    key = DataConsolidationService.generate_record_hash(record)

                if key not in seen:
                    seen.add(key)
                    unique_records.append(record)
                else:
                    duplicates += 1

            return unique_records, duplicates
        except Exception as e:
            print(f"[WARNING] Error identifying unique records: {str(e)}", file=sys.stderr)
            return records, 0

    @staticmethod
    def add_page_tracker_to_csv(csv_text: str, page_number: int, iteration: int) -> str:
        """
        Add source page and iteration information to CSV records
        """
        try:
            headers, records = DataConsolidationService.parse_csv_to_records(csv_text)

            # Add new columns
            if 'source_page' not in headers:
                headers.append('source_page')
            if 'source_iteration' not in headers:
                headers.append('source_iteration')

            # Add values to records
            for record in records:
                if 'source_page' not in record:
                    record['source_page'] = str(page_number)
                if 'source_iteration' not in record:
                    record['source_iteration'] = str(iteration)

            # Convert back to CSV
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=headers)
            writer.writeheader()
            writer.writerows(records)

            return output.getvalue()
        except Exception as e:
            print(f"[WARNING] Error adding page tracker: {str(e)}", file=sys.stderr)
            return csv_text

    @staticmethod
    def get_record_count(csv_text: str) -> int:
        """Get count of records in CSV (excluding header)"""
        try:
            lines = csv_text.strip().split('\n')
            # Subtract 1 for header
            return max(0, len(lines) - 1)
        except:
            return 0

    @staticmethod
    def compare_pages(scraped_pages: int, target_pages: int) -> Dict:
        """
        Compare scraped pages with target pages
        Returns: {is_complete, pages_remaining, percentage}
        """
        return {
            'is_complete': scraped_pages >= target_pages,
            'pages_remaining': max(0, target_pages - scraped_pages),
            'pages_completed': scraped_pages,
            'total_target': target_pages,
            'percentage': round((scraped_pages / target_pages * 100) if target_pages > 0 else 0, 1)
        }
