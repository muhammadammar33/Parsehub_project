import requests
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

API_KEY = os.getenv('PARSEHUB_API_KEY')

# Try different base URLs and endpoint patterns
with open("active_runs.json", "r") as f:
    active = json.load(f)

# Get Mann_Project which has data (is_empty=False)
mann_run = None
for run in active["runs"]:
    if "Mann_Project" in run["project"]:
        mann_run = run
        break

if not mann_run:
    print("Could not find Mann_Project")
    exit(1)

run_token = mann_run["run_token"]
token = mann_run["token"]

print(f"Testing different URL patterns with run_token: {run_token}\n")

# List of possible endpoints
endpoints = [
    # v2 variations
    f"https://www.parsehub.com/api/v2/runs/{run_token}/data?api_key={API_KEY}",
    f"https://www.parsehub.com/api/v2/{run_token}/data?api_key={API_KEY}",
    f"https://www.parsehub.com/api/v2/runs/{run_token}?api_key={API_KEY}",
    
    # Direct file downloads
    f"https://www.parsehub.com/api/{run_token}.json?api_key={API_KEY}",
    f"https://www.parsehub.com/api/{run_token}.csv?api_key={API_KEY}",
    
    # v1 style
    f"https://www.parsehub.com/api/v1/runs/{run_token}/data?api_key={API_KEY}",
    
    # Direct run endpoints
    f"https://www.parsehub.com/run/{run_token}/?api_key={API_KEY}",
    f"https://www.parsehub.com/run/{run_token}?api_key={API_KEY}",
    
    # Status check (might give us download URL)
    f"https://www.parsehub.com/api/v2/job/{run_token}?api_key={API_KEY}",
]

print("Testing endpoints:")
print("=" * 80)

for url in endpoints:
    short_url = url.replace(API_KEY, "***")
    r = requests.get(url, allow_redirects=False, timeout=5)
    
    status = r.status_code
    is_redirect = 300 <= status < 400
    
    if status == 200:
        print(f"[OK] {status}: {short_url}")
        try:
            data = r.json()
            print(f"   Response keys: {list(data.keys())[:5]}")
        except:
            print(f"   Response type: {r.headers.get('content-type', 'unknown')}")
            print(f"   First 100 chars: {r.text[:100]}")
    elif is_redirect:
        print(f"↪️  {status}: {short_url}")
        print(f"   Redirects to: {r.headers.get('location', 'N/A')}")
    elif status == 404:
        print(f"[ERROR] {status}: {short_url}")
    else:
        print(f"[WARNING]  {status}: {short_url}")

print("\n" + "=" * 80)
print("\nIf you see any 200 or redirects above, those are promising!")
