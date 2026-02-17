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

run = active["runs"][0]
token = run["token"]
run_token = run["run_token"]
project = run["project"]

print(f"Testing different parse hub data endpoints:")
print(f"Project: {project}")
print(f"Token: {token}")
print(f"Run Token: {run_token}\n")

# Try endpoint 1: /runs/{run_token}/data
print("1️⃣  Trying: /projects/{token}/runs/{run_token}/data")
url = f"{BASE_URL}/projects/{token}/runs/{run_token}/data"
params = {"api_key": API_KEY}
r = requests.get(url, params=params)
print(f"   Status: {r.status_code}")
if r.status_code != 200:
    print(f"   Error: {r.text[:150]}\n")
else:
    print(f"   [OK] Success! Data available\n")

# Try endpoint 2: /runs/{run_token} (without /data)
print("2️⃣  Trying: /projects/{token}/runs/{run_token}")
url = f"{BASE_URL}/projects/{token}/runs/{run_token}"
params = {"api_key": API_KEY}
r = requests.get(url, params=params)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"   [OK] Success! Response keys: {list(data.keys())}")
    print(f"   Has 'data' key: {'data' in data}")
    print(f"   Full response:\n{json.dumps(data, indent=2)[:500]}\n")
else:
    print(f"   Error: {r.text[:150]}\n")

# Try endpoint 3: Get project data to see if data is embedded there
print("3️⃣  Checking project endpoint for data:")
url = f"{BASE_URL}/projects/{token}"
params = {"api_key": API_KEY}
r = requests.get(url, params=params)
if r.status_code == 200:
    data = r.json()
    last_run = data.get("last_run", {})
    print(f"   Last run keys: {list(last_run.keys())}")
    print(f"   Has data_ready: {last_run.get('data_ready')}")
    print()

# Try endpoint 4: Use output_file instead
print("4️⃣  Trying: /projects/{token}/runs/{run_token}/output")
url = f"{BASE_URL}/projects/{token}/runs/{run_token}/output"
params = {"api_key": API_KEY}
r = requests.get(url, params=params)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    print(f"   [OK] Success!\n")
else:
    print(f"   Error: {r.text[:150]}\n")

# Try with format=json parameter
print("5️⃣  Trying: /projects/{token}/runs/{run_token} with format=json")
url = f"{BASE_URL}/projects/{token}/runs/{run_token}"
params = {"api_key": API_KEY, "format": "json"}
r = requests.get(url, params=params)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"   [OK] Success! Response type: {type(data)}")
    if isinstance(data, dict):
        print(f"   Keys: {list(data.keys())}")
        if "data" in data:
            records = len(data.get("data", []))
            print(f"   Records found: {records}\n")
        else:
            print(f"   {json.dumps(data, indent=2)[:400]}\n")
else:
    print(f"   Error: {r.text[:150]}\n")
