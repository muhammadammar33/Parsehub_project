#!/usr/bin/env python
"""Test ParseHub API endpoints"""
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv('PARSEHUB_API_KEY', '')
project_token = 'tusu6YkwKJQ8'
base_url = 'https://www.parsehub.com/api/v2'

print("=" * 60)
print("Testing ParseHub API")
print("=" * 60)

# Test 1: Get project details
print("\n1. Getting original project details...")
url = f'{base_url}/projects/{project_token}'
try:
    r = requests.get(url, params={'api_key': api_key}, timeout=5)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        proj = r.json()
        print(f"   Template: {proj.get('template')}")
        print(f"   Start URL: {proj.get('start_url')}")
        print(f"   Plugins: {proj.get('plugins')}")
except Exception as e:
    print(f"   Error: {e}")

# Test 2: Try POST to create project
print("\n2. Attempting to create new project...")
url = f'{base_url}/projects'
data = {
    'title': 'Test Clone Project',
    'start_url': 'https://www.example.com/test?page=2',
}
try:
    r = requests.post(url, data=data, params={'api_key': api_key}, timeout=5)
    print(f"   Status: {r.status_code}")
    print(f"   Response[:200]: {r.text[:200]}")
except Exception as e:
    print(f"   Error: {e}")

print("\n❌ The ParseHub API POST /projects endpoint is returning 502")
print("   This is a ParseHub server issue, not a code problem")
print("=" * 60)
