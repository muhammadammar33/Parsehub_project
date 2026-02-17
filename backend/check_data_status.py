import requests
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

API_KEY = os.getenv('PARSEHUB_API_KEY')
BASE_URL = os.getenv('PARSEHUB_BASE_URL', 'https://www.parsehub.com/api/v2')

# Load active runs to get all project tokens
with open("active_runs.json", "r") as f:
    active = json.load(f)

print("📊 Checking data status for ALL projects:\n")
print("=" * 80)

all_empty = True

for run in active["runs"]:
    token = run["token"]
    project = run["project"]
    
    url = f"{BASE_URL}/projects/{token}"
    params = {"api_key": API_KEY}
    r = requests.get(url, params=params)
    
    if r.status_code == 200:
        data = r.json()
        last_run = data.get("last_run", {})
        
        is_empty = last_run.get("is_empty", False)
        data_ready = last_run.get("data_ready", 0)
        pages = last_run.get("pages", 0)
        status = last_run.get("status", "unknown")
        output_type = data.get("options_json", "{}")
        
        # Extract output type from options_json
        try:
            opts = json.loads(output_type) if isinstance(output_type, str) else {}
            output_format = opts.get("outputType", "unknown")
        except:
            output_format = "unknown"
        
        print(f"Project: {project}")
        print(f"  Status: {status} | Pages: {pages}")
        print(f"  Data Ready: {data_ready} | Empty: {is_empty}")
        print(f"  Output Format: {output_format}")
        
        if is_empty:
            print(f"  [WARNING]  NO DATA - Run returned empty results!")
        else:
            print(f"  [OK] Data available!")
            all_empty = False
        
        print()

print("=" * 80)
if all_empty:
    print("[ERROR] PROBLEM IDENTIFIED:")
    print("   All projects are returning empty data (is_empty=True)")
    print("\n   Possible causes:")
    print("   1. Templates are not extracting any data (template misconfiguration)")
    print("   2. Website content doesn't match the template selectors")
    print("   3. Pages required CSS selectors that aren't on the page")
    print("\n   Solution:")
    print("   1. Test templates in ParseHub UI to ensure they capture data")
    print("   2. Check if CSS selectors/XPath still match the website structure")
    print("   3. Re-run projects manually from ParseHub dashboard and verify")
else:
    print("[OK] Some projects have data available")
    print("   Use a different endpoint to fetch it")
