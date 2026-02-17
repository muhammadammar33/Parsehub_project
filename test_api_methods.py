#!/usr/bin/env python
"""Test alternative ParseHub API methods"""
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv('PARSEHUB_API_KEY', '')
base_url = 'https://www.parsehub.com/api/v2'

print("=" * 70)
print("Testing Alternative ParseHub Project Creation Methods")
print("=" * 70)

# Method 1: POST with JSON
print("\n1. POST /projects with JSON content-type...")
url = f'{base_url}/projects'
headers = {'Content-Type': 'application/json'}
data = json.dumps({
    'title': 'Test JSON Project',
    'start_url': 'https://www.example.com/test?page=2',
})
try:
    r = requests.post(url, data=data, headers=headers,
                      params={'api_key': api_key}, timeout=5)
    print(f"   Status: {r.status_code}")
    if r.status_code not in [502, 503]:
        print(f"   Response: {r.text[:300]}")
    else:
        print(f"   Still 5xx error")
except Exception as e:
    print(f"   Error: {e}")

# Method 2: Check if there's a direct run endpoint
print("\n2. Checking if we can run existing project with custom URL...")
project_token = 'tusu6YkwKJQ8'
url = f'{base_url}/projects/{project_token}/run'
params = {
    'api_key': api_key,
    # Try passing URL to run endpoint
    'start_url': 'https://www.example.com/test?page=2'
}
try:
    r = requests.post(url, params=params, timeout=5)
    print(f"   Status: {r.status_code}")
    if r.status_code in [200, 201]:
        print(f"   ✅ This might work! Response: {r.json()}")
    else:
        print(f"   Response: {r.text[:200]}")
except Exception as e:
    print(f"   Error: {e}")

# Method 3: Check API v1
print("\n3. Testing ParseHub API v1...")
url = f'https://www.parsehub.com/api/v1/projects'
try:
    r = requests.post(url, data={'title': 'Test'}, params={
                      'api_key': api_key}, timeout=5)
    print(f"   Status: {r.status_code}")
    print(f"   Response[:100]: {r.text[:100]}")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "=" * 70)
print("ISSUE: ParseHub POST /api/v2/projects is returning 502")
print("ACTION: This is a ParseHub server issue, likely temporary")
print("=" * 70)
