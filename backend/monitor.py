import requests
import json
import time
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
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

def monitor_projects(check_interval=30, max_wait=3600):
    """Monitor projects until all complete"""
    
    with open("active_runs.json", "r") as f:
        active = json.load(f)
    
    all_results = {
        "fetch_time": datetime.now().isoformat(),
        "total_projects": len(active["runs"]),
        "project_data": [],
        "monitoring_started": datetime.now().isoformat()
    }
    
    completed = set()
    failed = set()
    start_time = time.time()
    
    print("📊 Starting project monitoring...\n")
    print(f"Check interval: {check_interval}s")
    print(f"Max wait time: {max_wait}s\n")
    print("=" * 70)
    
    while len(completed) + len(failed) < len(active["runs"]):
        elapsed = time.time() - start_time
        
        if elapsed > max_wait:
            print(f"\n[TIME]  Max wait time reached ({max_wait}s)")
            break
        
        for run in active["runs"]:
            token = run["token"]
            project = run["project"]
            
            if token in completed or token in failed:
                continue
            
            # Get current status from project data (not from stored run token)
            project_info = get_project_data(token)
            
            if "error" in project_info:
                print(f"[ERROR] {project}: Error - {project_info['error']}")
                failed.add(token)
                continue
            
            last_run = project_info.get("last_run", {})
            status = last_run.get("status")
            last_run_token = last_run.get("run_token")  # Use latest run token from project
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {project}")
            print(f"  Status: {status}")
            
            if status == "complete":
                print(f"  [OK] COMPLETE")
                
                # Try to fetch the data using LATEST run token
                if last_run_token:
                    data = fetch_run_data(token, last_run_token)
                    
                    if "error" in data:
                        # Data may have been purged, save what we have
                        print(f"  ℹ️  Data not available (purged): {data['error']}")
                        all_results["project_data"].append({
                            "project": project,
                            "token": token,
                            "run_token": last_run_token,
                            "status": "complete",
                            "records": 0,
                            "note": "Data was purged by ParseHub"
                        })
                    else:
                        # Save data
                        filename = f"data_{token}.json"
                        with open(filename, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        
                        records = len(data.get("results", []))
                        print(f"  💾 Saved {records} records to {filename}")
                        
                        all_results["project_data"].append({
                            "project": project,
                            "token": token,
                            "run_token": last_run_token,
                            "status": "complete",
                            "records": records,
                            "data_file": filename,
                            "completed_at": datetime.now().isoformat()
                        })
                    completed.add(token)
                else:
                    print(f"  [WARNING]  No run token available")
                    failed.add(token)
                    
            elif status == "error":
                print(f"  [ERROR] RUN ERROR")
                failed.add(token)
                all_results["project_data"].append({
                    "project": project,
                    "token": token,
                    "status": "error"
                })
            else:
                print(f"  ⏳ {status}...")
                pages = last_run.get("pages", "?")
                print(f"  Pages: {pages}")
            
            print()
        
        # Wait before next check
        if len(completed) + len(failed) < len(active["runs"]):
            print(f"⏳ Next check in {check_interval}s... (Press Ctrl+C to stop)\n")
            time.sleep(check_interval)
    
    # Final summary
    print("\n" + "=" * 70)
    print("🎉 MONITORING COMPLETE")
    print("=" * 70)
    print(f"[OK] Completed: {len(completed)}")
    print(f"[ERROR] Failed: {len(failed)}")
    print(f"[TIME]  Total time: {int(time.time() - start_time)}s")
    
    all_results["monitoring_ended"] = datetime.now().isoformat()
    all_results["completed_count"] = len(completed)
    all_results["failed_count"] = len(failed)
    
    # Save results
    with open("monitoring_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n💾 Results saved to monitoring_results.json")

if __name__ == "__main__":
    try:
        monitor_projects(check_interval=30, max_wait=3600)
    except KeyboardInterrupt:
        print("\n\n⛔ Monitoring stopped by user")

