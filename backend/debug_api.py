import requests
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

API_KEY = os.getenv('PARSEHUB_API_KEY')
BASE_URL = os.getenv('PARSEHUB_BASE_URL', 'https://www.parsehub.com/api/v2')

# Load the active runs
with open("active_runs.json", "r") as f:
    active = json.load(f)

# Test with first project
run = active["runs"][0]
token = run["token"]
run_token = run["run_token"]
project = run["project"]

print(f"Testing API call for: {project}")
print(f"  Token: {token}")
print(f"  Run Token: {run_token}")
print()

# First, check project data
print("1️⃣  Checking project status:")
url = f"{BASE_URL}/projects/{token}"
params = {"api_key": API_KEY}
r = requests.get(url, params=params)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"   Last Run Token: {data.get('last_run', {}).get('run_token')}")
    print(f"   Status: {data.get('last_run', {}).get('status')}")
else:
    print(f"   Error: {r.status_code} - {r.text[:200]}")

print()

# Now try data endpoint with BOTH tokens
print("2️⃣  Trying data endpoint with stored tokens:")
url = f"{BASE_URL}/projects/{token}/runs/{run_token}/data"
params = {"api_key": API_KEY}
r = requests.get(url, params=params)
print(f"   URL: {url}")
print(f"   Status: {r.status_code}")
if r.status_code != 200:
    print(f"   Error: {r.text[:300]}")
else:
    data = r.json()
    print(f"   [OK] Got data! Records: {len(data.get('results', []))}")

print()

# Try with latest run token from project info
print("3️⃣  Trying data endpoint with LATEST run token from project:")
latest_run_token = data.get('last_run', {}).get('run_token') if r.status_code == 200 else None
if latest_run_token:
    url = f"{BASE_URL}/projects/{token}/runs/{latest_run_token}/data"
    params = {"api_key": API_KEY}
    r = requests.get(url, params=params)
    print(f"   Latest Run Token: {latest_run_token}")
    print(f"   Status: {r.status_code}")
    if r.status_code != 200:
        print(f"   Error: {r.text[:300]}")
    else:
        data = r.json()
        print(f"   [OK] Got data! Records: {len(data.get('results', []))}")
else:
    print("   No latest run token available")

print()

# Try to list all runs
print("4️⃣  Trying to list all runs:")
url = f"{BASE_URL}/projects/{token}/runs"
params = {"api_key": API_KEY}
r = requests.get(url, params=params)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    runs = r.json()
    print(f"   Available runs: {len(runs)}")
    for i, run in enumerate(runs[:3]):
        print(f"     Run {i+1}: {run.get('run_token')} - {run.get('status')}")
else:
    print(f"   Error: {r.status_code} - {r.text[:300]}")
