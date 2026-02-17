"""
Monitoring Service - Continuously monitors projects for stops and triggers auto-recovery
"""

import requests
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from database import ParseHubDatabase
from recovery_service import RecoveryService
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MonitoringService:
    def __init__(self):
        self.db = ParseHubDatabase()
        self.recovery_service = RecoveryService()
        self.scheduler = BackgroundScheduler()
        self.api_key = os.getenv('PARSEHUB_API_KEY', '')
        self.base_url = os.getenv('PARSEHUB_BASE_URL', 'https://www.parsehub.com/api/v2')
        self.stop_detection_minutes = int(os.getenv('STOP_DETECTION_MINUTES', '5'))
        self.check_interval = int(os.getenv('MONITOR_CHECK_INTERVAL', '60'))  # seconds
        self.monitored_projects = {}
        self.recovery_attempts = {}  # Track recovery attempts
        self.max_recovery_attempts = int(os.getenv('MAX_RECOVERY_ATTEMPTS', '3'))

    def start(self):
        """Start the monitoring service"""
        if self.scheduler.running:
            logger.warning("Scheduler already running")
            return

        # Add monitoring job
        self.scheduler.add_job(
            self.check_all_projects,
            trigger=IntervalTrigger(seconds=self.check_interval),
            id='monitor_projects',
            name='Monitor all projects for stops'
        )

        self.scheduler.start()
        logger.info(f"[OK] Monitoring Service started (check interval: {self.check_interval}s)")

    def stop(self):
        """Stop the monitoring service"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("[OK] Monitoring Service stopped")

    def get_all_projects(self) -> List[Dict]:
        """Get all projects from ParseHub"""
        try:
            response = requests.get(
                f"{self.base_url}/projects",
                params={'api_key': self.api_key},
                timeout=10
            )

            if response.status_code == 200:
                return response.json().get('projects', [])

            return []

        except Exception as e:
            logger.error(f"Error fetching projects: {e}")
            return []

    def check_all_projects(self):
        """Check status of all projects"""
        try:
            projects = self.get_all_projects()
            logger.info(f"Checking {len(projects)} projects...")

            for project in projects:
                project_token = project.get('token')
                if not project_token:
                    continue

                self.check_single_project(project_token, project)

        except Exception as e:
            logger.error(f"Error in check_all_projects: {e}")

    def check_single_project(self, project_token: str, project_data: Dict = None):
        """Check if a single project needs recovery"""
        try:
            status_check = self.recovery_service.check_project_status(project_token)
            status = status_check.get('status')

            logger.debug(f"Project {project_token}: {status}")

            # Check if project should be recovered
            if status in ['stuck', 'cancelled'] or (status == 'completed' and self._is_incomplete_run(project_data)):
                self._handle_stop_detected(project_token, status, status_check)

        except Exception as e:
            logger.error(f"Error checking project {project_token}: {e}")

    def _is_incomplete_run(self, project_data: Dict) -> bool:
        """Check if a completed run looks incomplete"""
        if not project_data:
            return False

        last_run = project_data.get('last_run', {})
        pages_scraped = last_run.get('pages_scraped', 0)
        data_count = last_run.get('data_count', 0)

        # If very low data, might be incomplete
        return pages_scraped < 5 and data_count < 20

    def _handle_stop_detected(self, project_token: str, stop_reason: str, status_check: Dict):
        """Handle when a project stop is detected"""
        logger.warning(f"🛑 Project {project_token} stopped: {stop_reason}")

        # Check if already in recovery or hit max attempts
        if project_token in self.recovery_attempts:
            attempt_count = self.recovery_attempts[project_token]
            if attempt_count >= self.max_recovery_attempts:
                logger.warning(f"Max recovery attempts ({self.max_recovery_attempts}) reached for {project_token}")
                return
        else:
            self.recovery_attempts[project_token] = 0

        # Trigger auto-recovery
        self.trigger_recovery(project_token)

    def trigger_recovery(self, project_token: str) -> Dict:
        """Trigger recovery for a project"""
        try:
            logger.info(f"🔄 Triggering recovery for project {project_token}...")

            result = self.recovery_service.trigger_auto_recovery(project_token)

            if result.get('success'):
                self.recovery_attempts[project_token] = self.recovery_attempts.get(project_token, 0) + 1
                logger.info(f"[OK] Recovery triggered successfully: {result.get('message')}")
            else:
                logger.error(f"[ERROR] Recovery failed: {result.get('message')}")

            return result

        except Exception as e:
            logger.error(f"Error triggering recovery: {e}")
            return {'success': False, 'message': str(e)}

    def get_monitoring_status(self) -> Dict:
        """Get current monitoring status"""
        return {
            'running': self.scheduler.running if hasattr(self, 'scheduler') else False,
            'check_interval_seconds': self.check_interval,
            'stop_detection_minutes': self.stop_detection_minutes,
            'max_recovery_attempts': self.max_recovery_attempts,
            'recovery_attempts': self.recovery_attempts
        }

    def reset_recovery_counter(self, project_token: str):
        """Reset recovery attempt counter for a project"""
        if project_token in self.recovery_attempts:
            del self.recovery_attempts[project_token]
            logger.info(f"Reset recovery counter for {project_token}")

    # ==================== REAL-TIME DATA MONITORING ====================
    
    def monitor_run_realtime(self, project_id: int, run_token: str, target_pages: int = 1) -> Dict:
        """
        Monitor a scraping run in real-time and store data to database
        
        Args:
            project_id: Database project ID
            run_token: ParseHub run token
            target_pages: Target number of pages to scrape
        
        Returns:
            Dictionary with final monitoring status
        """
        try:
            # Create monitoring session
            session_id = self.db.create_monitoring_session(project_id, run_token, target_pages)
            
            if not session_id:
                logger.error(f"Failed to create monitoring session for {run_token}")
                return {'error': 'Failed to create session'}
            
            logger.info(f"📊 Started monitoring run {run_token} (session: {session_id})")
            
            # Monitor until completion
            poll_count = 0
            while True:
                # Get current run status
                status_data = self.get_run_status(run_token)
                
                if not status_data:
                    logger.warning(f"[WARNING] Could not get status for run {run_token}")
                    time.sleep(2)
                    continue
                
                # Fetch and store new data
                new_records = self.fetch_and_store_data(session_id, project_id, run_token)
                
                # Update session with current status
                current_status = status_data.get('status', 'running')
                total_records = status_data.get('data_count', 0)
                total_pages = status_data.get('pages_crawled', 0)
                progress_pct = status_data.get('progress_percentage', 0)
                current_url = status_data.get('current_url', '')
                
                self.db.update_monitoring_session(
                    session_id,
                    status=current_status,
                    total_records=total_records,
                    total_pages=total_pages,
                    progress_percentage=progress_pct,
                    current_url=current_url
                )
                
                poll_count += 1
                logger.info(f"📈 Poll #{poll_count}: {total_records} records, {total_pages}/{target_pages} pages")
                
                # Check if completed
                if current_status in ['succeeded', 'failed', 'cancelled']:
                    logger.info(f"[OK] Run {run_token} {current_status}")
                    # Final update
                    self.db.update_monitoring_session(
                        session_id,
                        status=current_status,
                        total_records=total_records,
                        total_pages=total_pages,
                        progress_percentage=100 if current_status == 'succeeded' else progress_pct
                    )
                    break
                
                # Wait before next poll
                time.sleep(2)
            
            # Get final session data
            final_status = self.db.get_session_summary(session_id)
            return final_status if final_status else {'error': 'No data available', 'session_id': session_id}
            
        except Exception as e:
            logger.error(f"[ERROR] Error monitoring run: {e}")
            return {'error': str(e)}
    
    def fetch_and_store_data(self, session_id: str, project_id: int, run_token: str, 
                            offset: int = 0, limit: int = 100) -> int:
        """
        Fetch paginated data from ParseHub and store to database
        
        Args:
            session_id: Monitoring session ID
            project_id: Project ID
            run_token: Run token
            offset: Data offset for pagination
            limit: Records per request
        
        Returns:
            Count of newly stored records
        """
        try:
            # Fetch from ParseHub
            url = f'{self.base_url}/runs/{run_token}/data'
            params = {
                'api_key': self.api_key,
                'offset': offset,
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            records = data.get('data', [])
            total = data.get('total_count', 0)
            
            if not records:
                return 0
            
            # Store records
            page_number = (offset // limit) + 1
            stored_count = self.db.store_scraped_records(
                session_id, project_id, run_token, records, page_number
            )
            
            # If more data exists, recursively fetch next chunk
            if offset + limit < total:
                stored_count += self.fetch_and_store_data(
                    session_id, project_id, run_token,
                    offset + limit, limit
                )
            
            return stored_count
            
        except Exception as e:
            logger.warning(f"[WARNING] Error fetching data: {e}")
            return 0
    
    def get_run_status(self, run_token: str) -> Optional[Dict]:
        """
        Get current status of a ParseHub run
        
        Returns:
            Dict with status, data_count, pages_crawled, progress_percentage
        """
        try:
            url = f'{self.base_url}/runs/{run_token}'
            params = {'api_key': self.api_key}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'status': data.get('status', 'unknown'),
                'data_count': data.get('data_count', 0),
                'pages_crawled': data.get('pages_crawled', 0),
                'progress_percentage': self._calculate_progress(data),
                'current_url': data.get('page_crawled_url', ''),
                'error': data.get('error_log', '')
            }
        except Exception as e:
            logger.warning(f"[WARNING] Error getting run status: {e}")
            return None
    
    def get_monitoring_status_for_project(self, project_id: int) -> Optional[Dict]:
        """
        Get latest monitoring status for a project
        
        Returns:
            Dict with latest run status and data count
        """
        try:
            summary = self.db.get_monitoring_status_for_project(project_id)
            return summary
        except Exception as e:
            logger.warning(f"[WARNING] Error getting monitoring status: {e}")
            return None
    
    def _calculate_progress(self, data: Dict) -> float:
        """Calculate progress percentage from run data"""
        try:
            pages_crawled = data.get('pages_crawled', 0)
            if pages_crawled > 0:
                # Estimate based on pages (simplified)
                return min(int(pages_crawled * 10), 99)
            return 0
        except:
            return 0


# Global monitoring service instance
_monitoring_service = None


def get_monitoring_service() -> MonitoringService:
    """Get or create the global monitoring service instance"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service


def start_monitoring():
    """Start the global monitoring service"""
    service = get_monitoring_service()
    service.start()
    return service


def stop_monitoring():
    """Stop the global monitoring service"""
    service = get_monitoring_service()
    service.stop()


if __name__ == '__main__':
    service = start_monitoring()
    print("Monitoring service is running. Press Ctrl+C to stop.")
    
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_monitoring()
        print("[OK] Stopped")
