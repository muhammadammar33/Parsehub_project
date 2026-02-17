import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv('PARSEHUB_API_KEY')
BASE_URL = os.getenv('PARSEHUB_BASE_URL', 'https://www.parsehub.com/api/v2')

def run_project(token):
    """Trigger a new run for a project"""
    url = f"{BASE_URL}/projects/{token}/run"
    params = {"api_key": API_KEY}
    
    try:
        response = requests.post(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def main():
    # Load projects from your JSON file
    with open("parsehub_projects.json", "r") as f:
        data = json.load(f)
    
    results = []
    print("🚀 Starting new runs for all projects...\n")
    
    for project in data["projects"]:
        token = project["token"]
        title = project["title"]
        
        print(f"▶️  Running: {title}")
        run_data = run_project(token)
        
        if "error" not in run_data:
            print(f"   [OK] Run started! Run Token: {run_data.get('run_token')}\n")
            results.append({
                "project": title,
                "token": token,
                "run_token": run_data.get("run_token"),
                "status": "started"
            })
        else:
            print(f"   [ERROR] Error: {run_data['error']}\n")
    
    # Save results
    with open("active_runs.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "runs": results
        }, f, indent=2)
    
    print(f"💾 Results saved to active_runs.json")

if __name__ == "__main__":
    main()

