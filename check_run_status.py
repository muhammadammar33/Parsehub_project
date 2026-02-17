#!/usr/bin/env python
"""Check run status"""
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv('PARSEHUB_API_KEY', '')
run_token = 'tEYPeTu5hJyo'
url = f'https://www.parsehub.com/api/v2/runs/{run_token}'

r = requests.get(url, params={'api_key': api_key})
if r.status_code == 200:
    data = r.json()
    print(f'Status: {data.get("status")}')
    print(f'Pages: {data.get("pages")}')
    print(f'Data Count: {data.get("data_count")}')
    print(f'Start Time: {data.get("start_time")}')
    print(f'End Time: {data.get("end_time")}')
    print(f'Full response keys: {list(data.keys())}')
else:
    print(f'Error: {r.status_code}')
    print(f'Response: {r.text[:200]}')
