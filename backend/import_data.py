import json
import os
from pathlib import Path
from database import ParseHubDatabase

def import_all_data():
    """Import all existing JSON data files into database"""
    
    db = ParseHubDatabase()
    
    # Load projects from parsehub_projects.json
    projects_file = 'd:\\Parsehub\\parsehub_projects.json'
    
    if not os.path.exists(projects_file):
        print("[ERROR] parsehub_projects.json not found")
        return
    
    with open(projects_file, 'r') as f:
        projects_data = json.load(f)
    
    projects = projects_data.get('projects', [])
    print(f"📊 Found {len(projects)} projects")
    
    for project in projects:
        token = project.get('token')
        title = project.get('title')
        owner = project.get('owner_email')
        site = project.get('main_site')
        
        # Add project to database
        db.add_project(token, title, owner, site)
        print(f"[OK] Added project: {title}")
        
        # Check for corresponding data file
        data_file = f'd:\\Parsehub\\data_{token}.json'
        if os.path.exists(data_file):
            last_run = project.get('last_run')
            if last_run:
                run_token = last_run.get('run_token')
                status = last_run.get('status')
                pages = last_run.get('pages', 0)
                start_time = last_run.get('start_time')
                end_time = last_run.get('end_time')
                
                result = db.import_from_json(
                    data_file, token, run_token, status, pages, start_time, end_time
                )
                
                if result:
                    print(f"   📁 Imported {result['records']} records from {data_file}")
                else:
                    print(f"   [WARNING]  Failed to import data from {data_file}")
            else:
                print(f"   [WARNING]  No run data for {data_file}")
    
    print("\n[OK] Data import complete!")
    
    # Show analytics
    print("\n📈 Project Analytics:")
    analytics = db.get_all_analytics()
    for proj_analytics in analytics:
        print(f"\n{proj_analytics['project_token']}:")
        print(f"  Total Runs: {proj_analytics['total_runs']}")
        print(f"  Completed: {proj_analytics['completed_runs']}")
        print(f"  Total Records: {proj_analytics['total_records']}")
        print(f"  Avg Duration: {proj_analytics['avg_duration']}s")

if __name__ == '__main__':
    import_all_data()
