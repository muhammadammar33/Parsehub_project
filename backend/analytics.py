#!/usr/bin/env python3
"""
Analytics helper - provides analytics data from SQLite database
Can be called as a CLI tool or imported as a module
"""

import json
import sys
from database import ParseHubDatabase
from analytics_service import AnalyticsService

def get_analytics_json(token: str = None) -> str:
    """Get analytics as JSON"""
    try:
        if token:
            # Use the comprehensive analytics service
            service = AnalyticsService()
            analytics = service.get_project_analytics(token)
            result = analytics if analytics else {"error": "Project not found"}
        else:
            # Fallback to basic analytics for all projects
            db = ParseHubDatabase()
            analytics_list = db.get_all_analytics()
            result = {"projects": analytics_list}
        
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return json.dumps({"error": str(e)}, indent=2)

def print_dashboard():
    """Print analytics dashboard"""
    db = ParseHubDatabase()
    analytics = db.get_all_analytics()
    
    print("\n" + "="*80)
    print("📊 PARSEHUB ANALYTICS DASHBOARD")
    print("="*80)
    
    total_runs = 0
    total_records = 0
    total_projects = len(analytics)
    
    for proj in analytics:
        print(f"\n📁 {proj['project_token']}")
        print(f"   Runs: {proj['total_runs']} | Completed: {proj['completed_runs']}")
        print(f"   Records: {proj['total_records']} | Avg Duration: {proj['avg_duration']}s")
        
        if proj['latest_run']:
            print(f"   Latest: {proj['latest_run']['status']} ({proj['latest_run']['pages_scraped']} pages)")
        
        total_runs += proj['total_runs']
        total_records += proj['total_records']
    
    print("\n" + "="*80)
    print(f"SUMMARY: {total_projects} projects | {total_runs} runs | {total_records} records")
    print("="*80 + "\n")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'dashboard':
            print_dashboard()
        else:
            # Get analytics for specific project
            token = sys.argv[1]
            print(get_analytics_json(token))
    else:
        # Print all analytics
        print(get_analytics_json())
