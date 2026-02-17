"""
Session Monitor
Continuously monitors database for active scraping sessions
and executes incremental scraping operations
"""

import sys
import time
import threading
import json
from scraping_session_service import ScrapingSessionService
from auto_runner_service import AutoRunnerService


class SessionMonitor:
    """Monitors database for active sessions and executes scraping"""

    def __init__(self):
        self.session_service = ScrapingSessionService()
        self.auto_runner = AutoRunnerService()
        self.is_running = True
        self.active_sessions = set()

    def get_active_sessions(self):
        """Get all active scraping sessions from database"""
        try:
            conn = self.session_service.db.connect()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, project_token, project_name, total_pages_target,
                       pages_completed, current_iteration
                FROM scraping_sessions
                WHERE status = 'running'
            ''')

            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'session_id': row[0],
                    'project_token': row[1],
                    'project_name': row[2],
                    'total_pages_target': row[3],
                    'pages_completed': row[4],
                    'current_iteration': row[5]
                })

            conn.close()
            return sessions
        except Exception as e:
            print(f"[ERROR] Failed to fetch active sessions: {str(e)}", file=sys.stderr)
            return []

    def process_session(self, session):
        """Process a single scraping session"""
        try:
            session_id = session['session_id']
            project_token = session['project_token']
            project_name = session['project_name']
            total_pages = session['total_pages_target']
            pages_completed = session['pages_completed']
            current_iteration = session['current_iteration'] or 1

            print(f"[PROCESS] Starting iteration {current_iteration} for session {session_id}", 
                  file=sys.stderr)

            # Check if session is complete
            if pages_completed >= total_pages:
                print(f"[OK] Session {session_id} is complete! ({pages_completed}/{total_pages} pages)", 
                      file=sys.stderr)
                self.session_service.mark_session_complete(session_id)
                return

            # Get original URL
            original_url = self._get_original_url(session_id)
            
            if not original_url:
                print(f"[ERROR] No original URL found for session {session_id}. Cannot proceed.", 
                      file=sys.stderr)
                print(f"[DEBUG] Will retry in next cycle...", file=sys.stderr)
                return

            print(f"[PROCESS] Using URL: {original_url}", file=sys.stderr)

            # Calculate iteration parameters
            pages_per_iteration = 10  # Default - you can make this configurable
            start_page = pages_completed + 1
            end_page = min(start_page + pages_per_iteration - 1, total_pages)

            print(f"[PROCESS] Iteration {current_iteration}: pages {start_page}-{end_page}", 
                  file=sys.stderr)

            # Execute iteration
            print(f"[EXECUTE] Calling auto_runner.execute_iteration()...", file=sys.stderr)
            iter_res = self.auto_runner.execute_iteration(
                session_id, current_iteration, project_token, project_name,
                start_page, end_page, original_url
            )

            if iter_res['success']:
                # Update session progress
                new_pages_completed = iter_res['pages_completed']
                print(f"[SUCCESS] Iteration {current_iteration} completed: {new_pages_completed} pages", 
                      file=sys.stderr)
                
                self.session_service.update_session_progress(
                    session_id, new_pages_completed, 'running'
                )

                print(f"[MONITOR] Session {session_id} progress: {new_pages_completed}/{total_pages} pages",
                      file=sys.stderr)

                # If more iterations needed, the next monitor loop will handle it
                if new_pages_completed >= total_pages:
                    print(f"[COMPLETE] All pages scraped for session {session_id}!", file=sys.stderr)
                    self.session_service.mark_session_complete(session_id)
            else:
                print(f"[ERROR] Iteration {current_iteration} failed: {iter_res.get('error')}", 
                      file=sys.stderr)
                print(f"[RETRY] Will retry iteration {current_iteration} in next cycle", file=sys.stderr)

        except Exception as e:
            print(f"[ERROR] Exception in process_session: {str(e)}", file=sys.stderr)
            import traceback
            print(traceback.format_exc(), file=sys.stderr)

    def _get_original_url(self, session_id):
        """Get original URL from session_urls.json file (no database locks!)"""
        try:
            import os
            
            session_urls_file = os.path.join(
                os.path.dirname(__file__), '..',
                'session_urls.json'
            )
            
            print(f"[DEBUG] Looking for session URL in: {session_urls_file}", file=sys.stderr)
            
            if not os.path.exists(session_urls_file):
                print(f"[DEBUG] Session URLs file not found", file=sys.stderr)
                return None
            
            with open(session_urls_file, 'r') as f:
                sessions = json.load(f)
            
            session_key = str(session_id)
            if session_key in sessions:
                url = sessions[session_key]['url']
                print(f"[OK] Retrieved URL from file: {url}", file=sys.stderr)
                return url
            else:
                print(f"[DEBUG] No URL found for session {session_id}", file=sys.stderr)
                return None
                
        except Exception as e:
            print(f"[ERROR] Failed to get original URL: {str(e)}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return None

    def monitor_loop(self):
        """Main monitoring loop - runs continuously"""
        print("[OK] Session monitor started!", file=sys.stderr)
        loop_count = 0

        while self.is_running:
            try:
                loop_count += 1
                print(f"[MONITOR] Loop #{loop_count} - Checking for active sessions...", file=sys.stderr)

                # Get all active sessions
                sessions = self.get_active_sessions()

                if sessions:
                    print(f"[MONITOR] Found {len(sessions)} active session(s)", file=sys.stderr)

                    for session in sessions:
                        session_id = session['session_id']
                        pages_completed = session['pages_completed']
                        total_pages = session['total_pages_target']
                        
                        print(f"[MONITOR] Session {session_id}: {pages_completed}/{total_pages} pages", 
                              file=sys.stderr)

                        # Check if complete
                        if pages_completed >= total_pages:
                            print(f"[OK] Session {session_id} is complete!", file=sys.stderr)
                            self.session_service.mark_session_complete(session_id)
                            continue

                        # Try to process
                        try:
                            self.process_session(session)
                        except Exception as e:
                            print(f"[ERROR] Failed to process session {session_id}: {str(e)}", 
                                  file=sys.stderr)

                        # Give a moment between sessions
                        time.sleep(2)
                else:
                    print(f"[MONITOR] No active sessions found", file=sys.stderr)

                # Sleep before next check - reduced from 10 to 5 seconds for faster response
                print(f"[MONITOR] Sleeping 5 seconds before next check...", file=sys.stderr)
                time.sleep(5)

            except Exception as e:
                print(f"[ERROR] Monitor loop error: {str(e)}", file=sys.stderr)
                import traceback
                print(traceback.format_exc(), file=sys.stderr)
                time.sleep(5)  # Wait before retrying

    def start(self):
        """Start the monitor in a background thread (for compatibility)"""
        thread = threading.Thread(target=self.monitor_loop, daemon=False)
        thread.start()
        print("[OK] Background monitor thread started (non-daemon)", file=sys.stderr)
        return thread

    def stop(self):
        """Stop the monitor"""
        self.is_running = False
        print("[OK] Monitor stopped", file=sys.stderr)


# Global monitor instance
_monitor = None


def start_session_monitor():
    """Start the global session monitor"""
    global _monitor
    if _monitor is None:
        _monitor = SessionMonitor()
        _monitor.start()
    return _monitor


def get_session_monitor():
    """Get the global session monitor"""
    global _monitor
    if _monitor is None:
        _monitor = SessionMonitor()
        _monitor.start()
    return _monitor
