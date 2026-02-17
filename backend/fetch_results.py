import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

API_KEY = os.getenv('PARSEHUB_API_KEY')
BASE_URL = os.getenv('PARSEHUB_BASE_URL', 'https://www.parsehub.com/api/v2')

def get_project_data(token):
    """Get project details including last run info"""
    url = f"{BASE_URL}/projects/{token}"
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
        return {"error": str(e)}

def main():
    # Load active runs
    with open("active_runs.json", "r") as f:
        active = json.load(f)
    
    all_results = {
        "fetch_time": datetime.now().isoformat(),
        "total_projects": len(active["runs"]),
        "project_data": []
    }
    
    print("📥 Fetching project data...\n")
    
    for run in active["runs"]:
        token = run["token"]
        project = run["project"]
        
        print(f"Processing: {project}")
        
        # Get project details
        project_info = get_project_data(token)
        
        if "error" in project_info:
            print(f"  [ERROR] Error: {project_info['error']}\n")
            continue
        
        # Get the last run info
        last_run = project_info.get("last_run")
        
        if not last_run:
            print(f"  [WARNING]  No run data available\n")
            continue
        
        last_run_token = last_run.get("run_token")
        status = last_run.get("status")
        
        print(f"  Status: {status}")
        print(f"  Last Run Token: {last_run_token}")
        
        if status == "complete":
            print(f"  [OK] COMPLETE - Fetching data...")
            
            # Fetch the data
            data = fetch_run_data(token, last_run_token)
            
            if "error" in data:
                print(f"  [ERROR] Error fetching: {data['error']}\n")
                continue
            
            # Save data
            filename = f"data_{token}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            records = len(data.get("results", []))
            print(f"  💾 Saved {records} records to {filename}\n")
            
            all_results["project_data"].append({
                "project": project,
                "token": token,
                "run_token": last_run_token,
                "status": "complete",
                "records": records,
                "data_file": filename
            })
        else:
            print(f"  ⏳ Status: {status}\n")
            all_results["project_data"].append({
                "project": project,
                "token": token,
                "status": status
            })
    
    # Save consolidated results
    with open("project_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"💾 All results saved to project_results.json")

if __name__ == "__main__":
    main()
