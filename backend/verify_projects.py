import requests
import json
import time
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

API_KEY = os.getenv('PARSEHUB_API_KEY')
BASE_URL = os.getenv('PARSEHUB_BASE_URL', 'https://www.parsehub.com/api/v2')

def verify_project_exists(token):
    """Verify if a project exists"""
    url = f"{BASE_URL}/projects/{token}"
    params = {"api_key": API_KEY}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def check_all_projects():
    """Verify all project tokens are valid"""
    
    with open("active_runs.json", "r") as f:
        active = json.load(f)
    
    print("🔍 Verifying project tokens...\n")
    
    for run in active["runs"]:
        token = run["token"]
        project = run["project"]
        
        print(f"Verifying: {project}")
        print(f"  Token: {token}")
        
        project_data = verify_project_exists(token)
        
        if "error" in project_data:
            print(f"  [ERROR] Error: {project_data['error']}")
        else:
            print(f"  [OK] Project exists")
            print(f"  Title: {project_data.get('title')}")
            print(f"  Last Run: {project_data.get('last_run', {}).get('start_time', 'Never')}")
        print()

if __name__ == "__main__":
    check_all_projects()
