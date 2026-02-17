import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# ParseHub API configuration from environment
API_KEY = os.getenv('PARSEHUB_API_KEY')
API_BASE_URL = os.getenv('PARSEHUB_BASE_URL', 'https://www.parsehub.com/api/v2')

def fetch_projects():
    """Fetch all projects from ParseHub account"""
    try:
        print("🔄 Fetching ParseHub projects...")
        print("-" * 60)
        
        # Get all projects
        url = f"{API_BASE_URL}/projects"
        params = {"api_key": API_KEY}
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        projects = data.get("projects", [])
        
        if not projects:
            print("[ERROR] No projects found in your ParseHub account.")
            return []
        
        print(f"[OK] Successfully fetched {len(projects)} project(s)!\n")
        
        # Display projects in terminal
        for idx, project in enumerate(projects, 1):
            print(f"Project #{idx}")
            print(f"  Name: {project.get('title', 'N/A')}")
            print(f"  Token: {project.get('token', 'N/A')}")
            print(f"  Owner: {project.get('owner_email', 'N/A')}")
            print(f"  Maintained: {project.get('maintained', False)}")
            
            # Check if project has been run
            last_run = project.get('last_run')
            if last_run:
                print(f"  Last Run: {last_run.get('start_time', 'N/A')}")
                print(f"  Status: {last_run.get('status', 'N/A')}")
                print(f"  Pages Scraped: {last_run.get('pages', 0)}")
                print(f"  Data Ready: {last_run.get('data_ready', 0)}")
            else:
                print(f"  Last Run: Never")
            
            # Template info
            templates = project.get('templates_json', '[]')
            print(f"  Configuration: {len(templates)} characters of template data")
            print()
        
        # Save to file
        output_file = "parsehub_projects.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "fetch_time": datetime.now().isoformat(),
                "total_projects": len(projects),
                "projects": projects
            }, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Projects saved to: {output_file}")
        print("-" * 60)
        
        return projects
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] API Error: {e}")
        return []
    except json.JSONDecodeError:
        print("[ERROR] Error parsing API response")
        return []
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return []

if __name__ == "__main__":
    fetch_projects()
