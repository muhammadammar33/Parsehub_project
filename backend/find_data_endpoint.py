import requests
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

API_KEY = os.getenv('PARSEHUB_API_KEY')
BASE_URL = os.getenv('PARSEHUB_BASE_URL', 'https://www.parsehub.com/api/v2')

# Test with a project that HAS data
with open("active_runs.json", "r") as f:
    active = json.load(f)

# Find Mann_Project
mann_run = None
wix_run = None
for run in active["runs"]:
    if "Mann_Project" in run["project"]:
        mann_run = run
    if "Wix_Project" in run["project"]:
        wix_run = run

if not mann_run or not wix_run:
    print("Error: Could not find test projects")
    exit(1)

print(f"Testing with: {mann_run['project']}")
print(f"Token: {mann_run['token']}")
print(f"Run Token: {mann_run['run_token']}\n")

# Try to access CSV export
print("1️⃣  Trying CSV export:")
url = f"{BASE_URL}/projects/{mann_run['token']}/runs/{mann_run['run_token']}/csv"
params = {"api_key": API_KEY}
r = requests.get(url, params=params)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    print(f"   [OK] Got CSV! First 200 chars:\n{r.text[:200]}\n")
else:
    print(f"   Error: {r.text[:100]}\n")

# Try XLSX
print("2️⃣  Trying XLSX export:")
url = f"{BASE_URL}/projects/{mann_run['token']}/runs/{mann_run['run_token']}/xlsx"
params = {"api_key": API_KEY}
r = requests.get(url, params=params)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    print(f"   [OK] Got XLSX binary data\n")
else:
    print(f"   Error: {r.text[:100]}\n")

# Try JSON via query param
print("3️⃣  Trying JSON with query parameter format=json:")
url = f"{BASE_URL}/projects/{mann_run['token']}/last_run"
params = {"api_key": API_KEY, "format": "json"}
r = requests.get(url, params=params)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"   [OK] Got response! Type: {type(data)}")
    if isinstance(data, dict):
        print(f"   Keys: {list(data.keys())[:10]}\n")
    else:
        print()

# Try direct run data endpoint
print("4️⃣  Trying /run/{run_token}:")
url = f"{BASE_URL}/run/{mann_run['run_token']}"
params = {"api_key": API_KEY}
r = requests.get(url, params=params)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    print(f"   [OK] Got response!\n")
else:
    print(f"   Not found\n")

# Try webhook/callback approach
print("5️⃣  Checking webhook field from project:")
url = f"{BASE_URL}/projects/{mann_run['token']}"
params = {"api_key": API_KEY}
r = requests.get(url, params=params)
if r.status_code == 200:
    data = r.json()
    last_run = data.get("last_run", {})
    webhook = last_run.get("webhook")
    print(f"   Webhook configured: {webhook}\n")

# Try with HTML, XML formats
for fmt in ["html", "xml"]:
    print(f"6️⃣  Trying {fmt.upper()} format:")
    url = f"{BASE_URL}/projects/{mann_run['token']}/runs/{mann_run['run_token']}/{fmt}"
    params = {"api_key": API_KEY}
    r = requests.get(url, params=params)
    print(f"   Status: {r.status_code}\n")
