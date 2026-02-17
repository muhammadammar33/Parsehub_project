#!/usr/bin/env python3
"""
Start incremental scraping session.
Called by Next.js API route with JSON args.
Creates session and ensures background monitor is running.
"""

import sys
import json
import os
import subprocess
import time
from scraping_session_service import ScrapingSessionService

# Session URL storage file (avoids database locks)
SESSION_URLS_FILE = os.path.join(os.path.dirname(__file__), '..', 'session_urls.json')


def save_session_url(session_id: int, original_url: str):
    """Save session URL to JSON file (bypasses database locks)"""
    try:
        # Load existing sessions
        if os.path.exists(SESSION_URLS_FILE):
            with open(SESSION_URLS_FILE, 'r') as f:
                sessions = json.load(f)
        else:
            sessions = {}
        
        # Add/update this session
        sessions[str(session_id)] = {
            'url': original_url,
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Save back
        os.makedirs(os.path.dirname(SESSION_URLS_FILE), exist_ok=True)
        with open(SESSION_URLS_FILE, 'w') as f:
            json.dump(sessions, f, indent=2)
        
        print(f"[OK] Saved session {session_id} URL to file", file=sys.stderr)
        return True
    except Exception as e:
        print(f"[ERROR] Could not save session URL: {str(e)}", file=sys.stderr)
        return False


def is_monitor_running():
    """Check if background monitor process is already running"""
    try:
        # Try to connect to database and ping it
        from scraping_session_service import ScrapingSessionService
        service = ScrapingSessionService()
        conn = service.db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        # Monitor is likely running if DB is accessible
        return True
    except:
        return False


def start_background_monitor():
    """Start the background monitor as a separate process"""
    try:
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        monitor_script = os.path.join(backend_dir, 'run_background_monitor.py')
        
        # Start the monitor process in background
        # Use Popen with close_fds to detach from parent process
        if sys.platform == 'win32':
            # Windows: Use CREATE_NEW_PROCESS_GROUP to detach
            subprocess.Popen(
                [sys.executable, monitor_script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0,
                close_fds=True
            )
        else:
            # Unix/Linux: Use preexec_fn to detach
            subprocess.Popen(
                [sys.executable, monitor_script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setpgrp if hasattr(os, 'setpgrp') else None,
                close_fds=True
            )
        
        print(f"[OK] Started background monitor process", file=sys.stderr)
        time.sleep(1)  # Give it a moment to start
        return True
    except Exception as e:
        print(f"[WARNING] Could not start background monitor: {str(e)}", file=sys.stderr)
        return False


def main():
    try:
        # Read arguments from stdin or command line
        if len(sys.argv) > 1:
            # Arguments passed as JSON string
            args = json.loads(sys.argv[1])
        else:
            # Read from stdin
            args = json.loads(sys.stdin.read())

        project_token = args.get('project_token')
        project_name = args.get('project_name')
        original_url = args.get('original_url', '').strip()
        total_pages = int(args.get('total_pages', 10))
        pages_per_iteration = int(args.get('pages_per_iteration', 5))

        # Validate
        if not all([project_token, project_name, original_url]):
            print(json.dumps({
                'success': False,
                'error': 'Missing required fields: project_token, project_name, original_url'
            }))
            sys.exit(1)

        # Create session
        session_service = ScrapingSessionService()
        session_res = session_service.create_session(project_token, project_name, total_pages)

        if not session_res.get('success'):
            print(json.dumps({
                'success': False,
                'error': session_res.get('error', 'Failed to create session')
            }))
            sys.exit(1)

        session_id = session_res.get('session_id')

        # Save the original URL to JSON file (avoids database locks!)
        url_saved = save_session_url(session_id, original_url)
        if url_saved:
            print(f"[OK] Session {session_id} created with URL: {original_url}", file=sys.stderr)
        else:
            print(f"[WARNING] Could not save URL, but continuing...", file=sys.stderr)

        # Start the background monitor as a separate process if not already running
        if not is_monitor_running():
            print(f"[INFO] Starting background monitor process...", file=sys.stderr)
            start_background_monitor()
        else:
            print(f"[INFO] Background monitor already running", file=sys.stderr)

        # Return success with session details immediately
        # The actual scraping will happen in the background
        print(json.dumps({
            'success': True,
            'session_id': session_id,
            'message': f'Started incremental scraping for {total_pages} pages',
            'status': 'running',
            'info': 'Scraping running in background...'
        }))

    except json.JSONDecodeError as e:
        print(json.dumps({
            'success': False,
            'error': f'Invalid JSON input: {str(e)}'
        }))
        sys.exit(1)
    except Exception as e:
        import traceback
        print(json.dumps({
            'success': False,
            'error': str(e),
            'details': traceback.format_exc()
        }))
        sys.exit(1)


if __name__ == '__main__':
    main()
