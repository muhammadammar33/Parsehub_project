import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv('PARSEHUB_API_KEY')
BASE_URL = os.getenv('PARSEHUB_BASE_URL', 'https://www.parsehub.com/api/v2')

def get_all_runs(token):
    """Get all previous runs for a project to find data"""
    url = f"{BASE_URL}/projects/{token}/runs"
    params = {"api_key": API_KEY}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def fetch_run_data(token, run_token):
    """Fetch data from a specific run"""
    url = f"{BASE_URL}/runs/{run_token}/data"
    params = {"api_key": API_KEY}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return None

def recover_project_data(token, project_name):
    """Try to recover data from most recent completed runs"""
    
    print(f"\n🔍 Attempting to recover data for: {project_name}")
    
    # Get all runs
    runs_data = get_all_runs(token)
    
    if "error" in runs_data:
        print(f"  [ERROR] Could not fetch runs list: {runs_data['error']}")
        return None
    
    runs = runs_data.get("runs", [])
    
    if not runs:
        print(f"  [WARNING]  No runs found")
        return None
    
    print(f"  Found {len(runs)} total runs")
    
    # Try each run from most recent to oldest
    recovered = []
    for idx, run in enumerate(runs):
        run_token = run.get("run_token")
        status = run.get("status")
        start_time = run.get("start_time")
        pages = run.get("pages", 0)
        
        if status != "complete":
            continue
        
        print(f"  [{idx+1}] Trying run {run_token} (Pages: {pages}, Time: {start_time})...")
        
        # Try to fetch data
        data = fetch_run_data(token, run_token)
        
        if data and "results" in data:
            records = len(data.get("results", []))
            print(f"      [OK] SUCCESS! Retrieved {records} records")
            
            filename = f"recovered_data_{token}_{idx}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump({
                    "recovered_at": datetime.now().isoformat(),
                    "run_token": run_token,
                    "pages": pages,
                    "records_count": records,
                    "data": data
                }, f, indent=2, ensure_ascii=False)
            
            recovered.append({
                "run_token": run_token,
                "status": "success",
                "records": records,
                "pages": pages,
                "file": filename
            })
        else:
            print(f"      [ERROR] Data not available (purged or error)")
            recovered.append({
                "run_token": run_token,
                "status": "purged",
                "pages": pages
            })
    
    if recovered:
        print(f"\n  📊 Recovery Summary: {sum(1 for r in recovered if r['status'] == 'success')}/{len([r for r in recovered if r['status'] != 'error'])} runs with data available")
        return recovered
    else:
        print(f"  [ERROR] Could not recover data from any run")
        return None

def main():
    """Try to recover data from all projects"""
    
    with open("active_runs.json", "r") as f:
        active = json.load(f)
    
    recovery_results = {
        "recovery_time": datetime.now().isoformat(),
        "projects": []
    }
    
    print("=" * 70)
    print("🔄 DATA RECOVERY SYSTEM")
    print("=" * 70)
    print(f"Attempting to recover data from {len(active['runs'])} projects...\n")
    
    for run in active["runs"]:
        token = run["token"]
        project = run["project"]
        
        recovered = recover_project_data(token, project)
        
        recovery_results["projects"].append({
            "project": project,
            "token": token,
            "recovered_runs": recovered
        })
    
    # Save recovery report
    with open("data_recovery_report.json", "w") as f:
        json.dump(recovery_results, f, indent=2)
    
    print("\n" + "=" * 70)
    print("💾 Recovery report saved to: data_recovery_report.json")
    print("=" * 70)

if __name__ == "__main__":
    main()
