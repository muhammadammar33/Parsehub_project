import requests
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

API_KEY = os.getenv('PARSEHUB_API_KEY')
BASE_URL = os.getenv('PARSEHUB_BASE_URL', 'https://www.parsehub.com/api/v2')

with open("active_runs.json", "r") as f:
    active = json.load(f)

run = active["runs"][0]
token = run["token"]
project = run["project"]

print(f"Inspecting project structure for data access method:\n")

url = f"{BASE_URL}/projects/{token}"
params = {"api_key": API_KEY}
r = requests.get(url, params=params)

if r.status_code == 200:
    data = r.json()
    last_run = data.get("last_run", {})
    
    print(f"Project: {project}")
    print(f"Token: {token}")
    print(f"\nLast Run Details:")
    for key, value in last_run.items():
        if isinstance(value, str) and len(str(value)) > 100:
            print(f"  {key}: {str(value)[:80]}...")
        else:
            print(f"  {key}: {value}")
    
    print(f"\nLooking for data access URLs...")
    run_token = last_run.get("run_token")
    
    # Check for direct file endpoints
    print(f"\nTrying direct file download endpoints:")
    
    # Try JSON export
    test_urls = [
        f"/projects/{token}/runs/{run_token}.json",
        f"/projects/{token}/runs/{run_token}",
        f"/projects/{token}/last_run.json",
        f"/projects/{token}/last_run/data",
    ]
    
    for path in test_urls:
        test_url = BASE_URL + path
        test_params = {"api_key": API_KEY}
        test_r = requests.get(test_url, params=test_params)
        print(f"  {path}")
        print(f"    Status: {test_r.status_code}")
        if test_r.status_code == 200 and len(test_r.text) > 20:
            try:
                data = test_r.json()
                if isinstance(data, dict):
                    print(f"    [OK] Got JSON! Keys: {list(data.keys())[:5]}")
                    if "results" in data or "data" in data:
                        print(f"    Contains data!")
                else:
                    print(f"    Got response: {str(test_r.text)[:100]}")
            except:
                print(f"    Not JSON")
    
    # Try the old/alternative API endpoint
    print(f"\nTrying alternative API endpoints:")
    alt_urls = [
        f"https://www.parsehub.com/api/v2/projects?api_key={API_KEY}",  # Check if we can get different format
    ]

else:
    print(f"Error: {r.status_code}")
