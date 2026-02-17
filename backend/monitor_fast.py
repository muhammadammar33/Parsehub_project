import requests
import json
import time
import sys
from datetime import datetime
from dotenv import load_dotenv
import os
from database import ParseHubDatabase

# Load environment variables from .env file
load_dotenv()

# Fix for Windows console Unicode issues
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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

def monitor_projects_fast(check_interval=10, max_wait=3600):
    """Monitor projects with faster polling to catch data before purging"""
    
    with open("active_runs.json", "r") as f:
        active = json.load(f)
    
    all_results = {
        "fetch_time": datetime.now().isoformat(),
        "total_projects": len(active["runs"]),
        "project_data": [],
        "monitoring_started": datetime.now().isoformat()
    }
    
    completed = {}  # token -> data
    failed = set()
    start_time = time.time()
    last_check = {}  # Track last status for each project
    
    print("📊 Starting FAST project monitoring...\n")
    print(f"Check interval: {check_interval}s (faster to catch data before purging)")
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
            
            # Get current status from project data
            project_info = get_project_data(token)
            
            if "error" in project_info:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [ERROR] {project}: API Error")
                failed.add(token)
                continue
            
            last_run = project_info.get("last_run", {})
            status = last_run.get("status")
            last_run_token = last_run.get("run_token")
            pages = last_run.get("pages", 0)
            
            # Only print if status changed
            current_status = last_check.get(token)
            if current_status != status:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {project}")
                print(f"  Status: {status} | Pages: {pages}")
                last_check[token] = status
            
            if status == "complete" and last_run_token:
                print(f"  [OK] COMPLETE - Fetching data immediately...")
                
                # Try to fetch data - do this ASAP while it's still available
                max_retries = 3
                for attempt in range(max_retries):
                    data = fetch_run_data(token, last_run_token)
                    
                    if "error" not in data:
                        # Success! Save data
                        filename = f"data_{token}.json"
                        with open(filename, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        
                        # Count records - look for the main data list in response
                        records = 0
                        for key, value in data.items():
                            if isinstance(value, list) and len(value) > 0:
                                records = len(value)
                                break
                        
                        # If no lists found, count non-empty string fields as 1 record
                        if records == 0 and any(isinstance(v, str) and v for v in data.values()):
                            records = 1
                        print(f"  💾 Saved {records} records to {filename}")
                        
                        # Store in database
                        db = ParseHubDatabase()
                        db.add_project(token, project, None, None)
                        run_id = db.add_run(token, last_run_token, "complete", pages, 
                                          last_run.get("start_time"), last_run.get("end_time"), 
                                          filename, False)
                        if run_id:
                            imported = db.store_scraped_data(run_id, None, data)
                            print(f"  📊 Stored {imported} records in database\n")
                        
                        all_results["project_data"].append({
                            "project": project,
                            "token": token,
                            "run_token": last_run_token,
                            "status": "complete",
                            "records": records,
                            "data_file": filename,
                            "database_id": run_id,
                            "completed_at": datetime.now().isoformat()
                        })
                        completed[token] = data
                        break
                    else:
                        if attempt < max_retries - 1:
                            print(f"  [WARNING]  Attempt {attempt + 1} failed, retrying in 2s...")
                            time.sleep(2)
                        else:
                            # All retries failed - data was purged
                            print(f"  [ERROR] Data purged (all {max_retries} attempts failed)\n")
                            all_results["project_data"].append({
                                "project": project,
                                "token": token,
                                "run_token": last_run_token,
                                "status": "complete",
                                "records": 0,
                                "pages_scraped": pages,
                                "note": "Data was purged before we could retrieve it"
                            })
                            completed[token] = None
            
            elif status == "error":
                print(f"  [ERROR] RUN ERROR\n")
                failed.add(token)
                all_results["project_data"].append({
                    "project": project,
                    "token": token,
                    "status": "error"
                })
        
        # Wait before next check
        if len(completed) + len(failed) < len(active["runs"]):
            time.sleep(check_interval)
    
    # Final summary
    print("\n" + "=" * 70)
    print("🎉 MONITORING COMPLETE")
    print("=" * 70)
    print(f"[OK] Completed & Data Saved: {sum(1 for v in completed.values() if v is not None)}")
    print(f"[OK] Completed (Data Purged): {sum(1 for v in completed.values() if v is None)}")
    print(f"[ERROR] Failed: {len(failed)}")
    print(f"[TIME]  Total time: {int(time.time() - start_time)}s")
    
    all_results["monitoring_ended"] = datetime.now().isoformat()
    all_results["data_saved_count"] = sum(1 for v in completed.values() if v is not None)
    all_results["data_purged_count"] = sum(1 for v in completed.values() if v is None)
    all_results["failed_count"] = len(failed)
    
    # Save results
    with open("monitoring_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n💾 Results saved to monitoring_results.json")

if __name__ == "__main__":
    try:
        # Use 10 second intervals to catch data before it's purged
        monitor_projects_fast(check_interval=10, max_wait=3600)
    except KeyboardInterrupt:
        print("\n\n⛔ Monitoring stopped by user")
