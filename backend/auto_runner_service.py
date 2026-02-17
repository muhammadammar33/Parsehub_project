"""
Auto Runner Service
Handles automatic ParseHub project creation, execution, and iteration management
"""

import os
import sys
import time
import requests
from typing import Dict, List
from url_generator import URLGenerator
from scraping_session_service import ScrapingSessionService
from data_consolidation_service import DataConsolidationService


class AutoRunnerService:
    """Service for automating incremental scraping iterations"""

    def __init__(self):
        self.api_key = os.getenv('PARSEHUB_API_KEY', '')
        self.base_url = os.getenv('PARSEHUB_BASE_URL', 'https://www.parsehub.com/api/v2')
        self.session_service = ScrapingSessionService()

    def get_project_details(self, project_token: str) -> Dict:
        """Fetch project details from ParseHub API"""
        try:
            url = f"{self.base_url}/projects/{project_token}"
            response = requests.get(url, params={'api_key': self.api_key})
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'project': response.json()
                }
            return {'success': False, 'error': f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"[ERROR] Error fetching project: {str(e)}", file=sys.stderr)
            return {'success': False, 'error': str(e)}

    def create_project(self, original_project_token: str, new_project_name: str, 
                      new_start_url: str) -> Dict:
        """Create a new ParseHub project (clone of original with new URL)"""
        try:
            # Get original project details
            original = self.get_project_details(original_project_token)
            if not original['success']:
                return original

            project_data = original['project']

            # Create new project with same template/plugins but new URL
            create_url = f"{self.base_url}/projects"
            
            payload = {
                'title': new_project_name,
                'template': project_data.get('template'),  # Use same template
                'start_url': new_start_url,
            }

            response = requests.post(create_url, data=payload, params={'api_key': self.api_key})

            if response.status_code in [200, 201]:
                new_project = response.json()
                new_token = new_project.get('token')
                print(f"[OK] Created new project: {new_token}", file=sys.stderr)
                return {
                    'success': True,
                    'project_token': new_token,
                    'project': new_project
                }
            return {'success': False, 'error': f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            print(f"[ERROR] Error creating project: {str(e)}", file=sys.stderr)
            return {'success': False, 'error': str(e)}

    def trigger_run(self, project_token: str, start_url: str = None) -> Dict:
        """Trigger a ParseHub project run with optional custom URL"""
        try:
            url = f"{self.base_url}/projects/{project_token}/run"
            
            params = {'api_key': self.api_key}
            if start_url:
                params['start_url'] = start_url
                print(f"[OK] Triggering run with custom URL: {start_url}", file=sys.stderr)
            
            response = requests.post(url, params=params)

            if response.status_code in [200, 201]:
                run_data = response.json()
                run_token = run_data.get('run_token') or run_data.get('token')
                print(f"[OK] Triggered run: {run_token}", file=sys.stderr)
                return {
                    'success': True,
                    'run_token': run_token,
                    'run_data': run_data
                }
            return {'success': False, 'error': f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"[ERROR] Error triggering run: {str(e)}", file=sys.stderr)
            return {'success': False, 'error': str(e)}

    def get_run_status(self, run_token: str) -> Dict:
        """Get current status of a ParseHub run"""
        try:
            url = f"{self.base_url}/runs/{run_token}"
            response = requests.get(url, params={'api_key': self.api_key})

            if response.status_code == 200:
                run_data = response.json()
                return {
                    'success': True,
                    'status': run_data.get('status'),
                    'pages': run_data.get('pages_scraped', 0),
                    'data_count': run_data.get('data_count', 0),
                    'run_data': run_data
                }
            return {'success': False, 'error': f"HTTP {response.status_code}"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_run_data(self, run_token: str) -> Dict:
        """Fetch CSV data from completed ParseHub run"""
        try:
            url = f"{self.base_url}/runs/{run_token}/output"
            response = requests.get(url, params={'api_key': self.api_key, 'format': 'csv'})

            if response.status_code == 200:
                csv_data = response.text
                return {
                    'success': True,
                    'csv_data': csv_data,
                    'records_count': DataConsolidationService.get_record_count(csv_data)
                }
            return {'success': False, 'error': f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"[ERROR] Error fetching run data: {str(e)}", file=sys.stderr)
            return {'success': False, 'error': str(e)}

    def wait_for_completion(self, run_token: str, timeout_seconds: int = 3600, 
                           poll_interval: int = 10) -> Dict:
        """Wait for ParseHub run to complete"""
        start_time = time.time()
        last_pages = 0
        last_status = None

        while time.time() - start_time < timeout_seconds:
            status_res = self.get_run_status(run_token)

            if status_res['success']:
                status = status_res['status']
                pages = status_res['pages']

                if status != last_status or pages != last_pages:
                    print(f"[WAIT] Run {run_token}: status={status}, pages={pages}", file=sys.stderr)
                    last_status = status
                    last_pages = pages

                if status in ['complete', 'succeeded']:
                    print(f"[OK] Run completed: {pages} pages scraped", file=sys.stderr)
                    return {
                        'success': True,
                        'status': status,
                        'pages': pages
                    }
                elif status in ['failed', 'error']:
                    return {
                        'success': False,
                        'status': status,
                        'error': 'Run failed'
                    }

            time.sleep(poll_interval)

        return {
            'success': False,
            'status': 'timeout',
            'error': f'Run did not complete within {timeout_seconds} seconds'
        }

    def execute_iteration(self, session_id: int, iteration_number: int,
                         original_project_token: str, project_name: str,
                         start_page: int, end_page: int,
                         original_url: str) -> Dict:
        """
        Execute a single iteration:
        1. Generate next URL
        2. Trigger run with custom URL (no project creation needed!)
        3. Wait for completion
        4. Get data and update session
        """
        try:
            print(f"\n[START] Starting iteration {iteration_number} (pages {start_page}-{end_page})", file=sys.stderr)

            # Generate next URL
            pattern_info = URLGenerator.detect_pattern(original_url)
            next_url = URLGenerator.generate_next_url(original_url, start_page, pattern_info)
            print(f"[URL] Next URL: {next_url}", file=sys.stderr)

            # ✅ NEW: Trigger run with custom URL directly (no project creation!)
            run_res = self.trigger_run(original_project_token, start_url=next_url)
            if not run_res['success']:
                return {'success': False, 'error': f"Failed to trigger run: {run_res['error']}"}

            run_token = run_res['run_token']

            # Add iteration run to database
            iter_res = self.session_service.add_iteration_run(
                session_id, iteration_number, original_project_token, 
                f"{project_name} iteration {iteration_number}",
                start_page, end_page, run_token
            )

            if not iter_res['success']:
                return {'success': False, 'error': f"Failed to record iteration: {iter_res['error']}"}

            run_id = iter_res['run_id']

            # Wait for completion
            wait_res = self.wait_for_completion(run_token)
            if not wait_res['success']:
                return {'success': False, 'error': f"Run failed/timed out: {wait_res['error']}"}

            # Get data
            data_res = self.get_run_data(run_token)
            if not data_res['success']:
                return {'success': False, 'error': f"Failed to fetch data: {data_res['error']}"}

            csv_data = data_res['csv_data']
            records_count = data_res['records_count']

            # Update iteration run
            update_res = self.session_service.update_iteration_run(
                run_id, csv_data, records_count, 'completed'
            )

            if not update_res['success']:
                return {'success': False, 'error': f"Failed to update iteration: {update_res['error']}"}

            print(f"[OK] Iteration {iteration_number} complete: {records_count} records", file=sys.stderr)

            return {
                'success': True,
                'iteration_number': iteration_number,
                'pages_completed': end_page,
                'records_count': records_count,
                'csv_data': csv_data
            }

        except Exception as e:
            print(f"[ERROR] Error in iteration {iteration_number}: {str(e)}", file=sys.stderr)
            return {'success': False, 'error': str(e)}

    def run_incremental_scraping(self, session_id: int, project_token: str,
                                project_name: str, original_url: str,
                                total_pages_target: int,
                                pages_per_iteration: int = 5) -> Dict:
        """
        Run the complete incremental scraping process
        Automatically creates iterations until target is reached
        """
        try:
            print(f"\n{'='*60}", file=sys.stderr)
            print(f"[START] Starting incremental scraping campaign", file=sys.stderr)
            print(f"Target: {total_pages_target} pages", file=sys.stderr)
            print(f"Pages per iteration: {pages_per_iteration}", file=sys.stderr)
            print(f"{'='*60}\n", file=sys.stderr)

            all_csv_data = []
            iteration = 1
            current_page = 1

            while current_page <= total_pages_target:
                # Calculate page range for this iteration
                end_page = min(current_page + pages_per_iteration - 1, total_pages_target)

                # Execute iteration
                iter_res = self.execute_iteration(
                    session_id, iteration, project_token, project_name,
                    current_page, end_page, original_url
                )

                if not iter_res['success']:
                    print(f"[ERROR] Iteration failed: {iter_res['error']}", file=sys.stderr)
                    # Don't stop, try next iteration
                    iteration += 1
                    current_page = end_page + 1
                    continue

                # Collect CSV data
                all_csv_data.append(iter_res['csv_data'])

                # Update session progress
                pages_completed = end_page
                self.session_service.update_session_progress(
                    session_id, pages_completed, 'running'
                )

                # Move to next iteration
                iteration += 1
                current_page = end_page + 1

            # All iterations complete - consolidate data
            print(f"\n{'='*60}", file=sys.stderr)
            print(f"[CONSOLIDATE] Consolidating data from {len(all_csv_data)} iterations...", file=sys.stderr)

            merged_csv, total_records, dedup_count = DataConsolidationService.merge_csv_data(
                all_csv_data, deduplicate=True
            )

            # Save consolidated data
            consol_res = self.session_service.save_combined_data(
                session_id, merged_csv, total_records, total_pages_target, dedup_count
            )

            if consol_res['success']:
                # Mark session as complete
                self.session_service.mark_session_complete(session_id)
                print(f"[OK] Incremental scraping complete!", file=sys.stderr)
                print(f"   Total pages scraped: {total_pages_target}", file=sys.stderr)
                print(f"   Total records: {total_records}", file=sys.stderr)
                print(f"   Duplicates removed: {dedup_count}", file=sys.stderr)

                return {
                    'success': True,
                    'total_pages_scraped': total_pages_target,
                    'total_records': total_records,
                    'duplicates_removed': dedup_count,
                    'iterations_completed': iteration - 1
                }
            else:
                return {'success': False, 'error': 'Failed to consolidate data'}

        except Exception as e:
            print(f"[ERROR] Error in incremental scraping: {str(e)}", file=sys.stderr)
            return {'success': False, 'error': str(e)}
