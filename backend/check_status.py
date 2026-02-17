import requests
import json
import time
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

API_KEY = os.getenv('PARSEHUB_API_KEY')
BASE_URL = os.getenv('PARSEHUB_BASE_URL', 'https://www.parsehub.com/api/v2')

def check_status(token, run_token):
    """Check status of a running project"""
    url = f"{BASE_URL}/projects/{token}/runs/{run_token}"
    params = {"api_key": API_KEY}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def fetch_data(token, run_token):
    """Fetch scraped data from completed run"""
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
    
    results = {"timestamp": active["timestamp"], "runs_status": []}
    
    print("📊 Checking status of all runs...\n")
    
    for run in active["runs"]:
        project = run["project"]
        token = run["token"]
        run_token = run["run_token"]
        
        print(f"Checking: {project}")
        status = check_status(token, run_token)
        
        if "error" not in status:
            current_status = status.get("status")
            pages = status.get("pages", 0)
            print(f"  Status: {current_status}")
            print(f"  Pages: {pages}")
            
            if current_status == "complete":
                print(f"  [OK] COMPLETE - Fetching data...")
                data = fetch_data(token, run_token)
                
                if "error" not in data:
                    # Save data
                    filename = f"data_{token}.json"
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    
                    data_count = len(data.get("results", []))
                    print(f"  💾 Saved {data_count} records to {filename}\n")
                    
                    results["runs_status"].append({
                        "project": project,
                        "status": "complete",
                        "data_file": filename,
                        "records": data_count
                    })
                else:
                    print(f"  [ERROR] Error fetching data\n")
            elif current_status == "error":
                print(f"  [ERROR] RUN ERROR\n")
                results["runs_status"].append({
                    "project": project,
                    "status": "error"
                })
            else:
                print(f"  ⏳ Still running ({current_status})...\n")
                results["runs_status"].append({
                    "project": project,
                    "status": current_status,
                    "pages": pages
                })
        else:
            print(f"  [ERROR] Error: {status['error']}\n")
    
    # Save results
    with open("run_status.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"💾 Status saved to run_status.json")

if __name__ == "__main__":
    main()
