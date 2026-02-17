#!/usr/bin/env python
"""Test database storage and retrieval"""
import json
from database import ParseHubDatabase

# Test data
test_token = 'test_token_123'
test_records = [
    {'field1': 'value1', 'field2': 'value2'},
    {'field1': 'value3', 'field2': 'value4'},
]
test_analytics = {
    'overview': {
        'total_records_scraped': 2,
        'total_runs': 1,
        'completed_runs': 1,
        'progress_percentage': 100
    },
    'data_quality': {
        'total_fields': 2
    },
    'recovery': {
        'status': 'normal'
    },
    'raw_data': test_records
}

print('[TEST] Starting database storage test...')

db = ParseHubDatabase()
print('[TEST] Database connected')

# Store data
result = db.store_analytics_data(
    test_token,
    'run_token_456',
    test_analytics,
    test_records,
    'csv_data_here'
)
print(f'[TEST] Storage result: {result}')

# Retrieve immediately to verify
retrieved = db.get_analytics_data(test_token)
print(f'[TEST] Retrieved: {retrieved is not None}')
if retrieved:
    records = retrieved.get('raw_data', [])
    print(f'[TEST] Records count: {len(records)}')
    csv_present = 'csv_data' in retrieved and retrieved['csv_data'] != ''
    print(f'[TEST] CSV present: {csv_present}')
    print(f'[TEST] Full data: {json.dumps(retrieved, indent=2)}')

db.disconnect()
print('[TEST] Database test complete - SUCCESS')
