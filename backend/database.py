import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ParseHubDatabase:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.getenv('DATABASE_PATH', 'd:\\Parsehub\\parsehub.db')
        self.db_path = db_path
        self.conn = None
        self.init_db()

    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def init_db(self):
        """Initialize database schema"""
        conn = self.connect()
        cursor = conn.cursor()

        # Projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                owner_email TEXT,
                main_site TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Runs table - tracks each execution
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                run_token TEXT UNIQUE NOT NULL,
                status TEXT,
                pages_scraped INTEGER DEFAULT 0,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration_seconds INTEGER,
                records_count INTEGER DEFAULT 0,
                data_file TEXT,
                is_empty BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        ''')

        # Scraped data table - stores individual records
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraped_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                project_id INTEGER NOT NULL,
                data_key TEXT,
                data_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (run_id) REFERENCES runs(id),
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        ''')

        # Key metrics table - for analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                date DATE,
                total_pages INTEGER DEFAULT 0,
                total_records INTEGER DEFAULT 0,
                runs_count INTEGER DEFAULT 0,
                avg_duration REAL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(project_id, date),
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        ''')

        # Recovery operations tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recovery_operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_run_id INTEGER NOT NULL,
                recovery_run_id INTEGER,
                project_id INTEGER NOT NULL,
                original_project_token TEXT,
                recovery_project_token TEXT,
                last_product_url TEXT,
                last_product_name TEXT,
                stopped_timestamp TIMESTAMP,
                recovery_triggered_timestamp TIMESTAMP,
                recovery_started_timestamp TIMESTAMP,
                recovery_completed_timestamp TIMESTAMP,
                status TEXT DEFAULT 'pending',
                original_data_count INTEGER DEFAULT 0,
                recovery_data_count INTEGER DEFAULT 0,
                final_data_count INTEGER DEFAULT 0,
                duplicates_removed INTEGER DEFAULT 0,
                attempt_number INTEGER DEFAULT 1,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (original_run_id) REFERENCES runs(id),
                FOREIGN KEY (recovery_run_id) REFERENCES runs(id)
            )
        ''')

        # Data lineage - tracks which data came from which run
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_lineage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scraped_data_id INTEGER NOT NULL,
                source_run_id INTEGER NOT NULL,
                recovery_operation_id INTEGER,
                is_duplicate BOOLEAN DEFAULT 0,
                duplicate_of_data_id INTEGER,
                product_url TEXT,
                product_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scraped_data_id) REFERENCES scraped_data(id),
                FOREIGN KEY (source_run_id) REFERENCES runs(id),
                FOREIGN KEY (recovery_operation_id) REFERENCES recovery_operations(id)
            )
        ''')

        # Run checkpoints - track progress snapshots
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS run_checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                snapshot_timestamp TIMESTAMP,
                item_count_at_time INTEGER,
                items_per_minute REAL,
                estimated_completion_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (run_id) REFERENCES runs(id)
            )
        ''')

        # Monitoring sessions - tracks real-time monitoring data collection
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitoring_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                run_token TEXT NOT NULL,
                target_pages INTEGER DEFAULT 1,
                status TEXT DEFAULT 'active',
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                total_records INTEGER DEFAULT 0,
                total_pages INTEGER DEFAULT 0,
                progress_percentage REAL DEFAULT 0,
                current_url TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        ''')

        # Enhanced scraped records with page and session tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraped_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                project_id INTEGER NOT NULL,
                run_token TEXT NOT NULL,
                page_number INTEGER,
                data_hash TEXT,
                data_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES monitoring_sessions(id),
                FOREIGN KEY (project_id) REFERENCES projects(id),
                UNIQUE(run_token, page_number, data_hash)
            )
        ''')

        # Analytics cache - stores complete analytics data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_token TEXT UNIQUE NOT NULL,
                run_token TEXT,
                total_records INTEGER DEFAULT 0,
                total_fields INTEGER DEFAULT 0,
                total_runs INTEGER DEFAULT 0,
                completed_runs INTEGER DEFAULT 0,
                progress_percentage REAL DEFAULT 0,
                status TEXT,
                analytics_json TEXT,
                stored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # CSV exports - stores complete CSV data for export
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS csv_exports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_token TEXT NOT NULL,
                run_token TEXT,
                csv_data TEXT,
                row_count INTEGER DEFAULT 0,
                stored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(project_token, run_token)
            )
        ''')

        # Analytics records - individual scraped records for display
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_token TEXT NOT NULL,
                run_token TEXT NOT NULL,
                record_index INTEGER,
                record_data TEXT NOT NULL,
                stored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(project_token, run_token, record_index)
            )
        ''')

        # Incremental scraping sessions - tracks overall scraping campaign
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraping_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_token TEXT NOT NULL,
                project_name TEXT NOT NULL,
                total_pages_target INTEGER NOT NULL,
                current_iteration INTEGER DEFAULT 1,
                pages_completed INTEGER DEFAULT 0,
                status TEXT DEFAULT 'running',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                UNIQUE(project_token, total_pages_target)
            )
        ''')

        # Iteration runs - tracks each ParseHub run in the session
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS iteration_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                iteration_number INTEGER NOT NULL,
                parsehub_project_token TEXT NOT NULL,
                parsehub_project_name TEXT NOT NULL,
                start_page_number INTEGER NOT NULL,
                end_page_number INTEGER NOT NULL,
                pages_in_this_run INTEGER NOT NULL,
                run_token TEXT NOT NULL,
                csv_data TEXT,
                records_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES scraping_sessions(id)
            )
        ''')

        # Combined scraped data - consolidated final results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS combined_scraped_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                consolidated_csv TEXT,
                total_records INTEGER DEFAULT 0,
                total_pages_scraped INTEGER DEFAULT 0,
                deduplicated_record_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(session_id),
                FOREIGN KEY (session_id) REFERENCES scraping_sessions(id)
            )
        ''')

        # URL patterns - store detected patterns for pagination
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS url_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_token TEXT UNIQUE NOT NULL,
                original_url TEXT NOT NULL,
                pattern_type TEXT,
                pattern_regex TEXT,
                last_page_placeholder TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_token) REFERENCES projects(token)
            )
        ''')

        conn.commit()
        self.disconnect()

    def add_project(self, token: str, title: str, owner_email: str = None, main_site: str = None):
        """Add or update project"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO projects (token, title, owner_email, main_site, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (token, title, owner_email, main_site))

        conn.commit()
        self.disconnect()

    def add_run(self, project_token: str, run_token: str, status: str, pages: int, 
                start_time: str, end_time: str = None, data_file: str = None, is_empty: bool = False):
        """Add a new run record"""
        conn = self.connect()
        cursor = conn.cursor()

        # Get project ID
        cursor.execute('SELECT id FROM projects WHERE token = ?', (project_token,))
        project = cursor.fetchone()
        
        if not project:
            self.disconnect()
            return None

        project_id = project['id']
        duration = None

        if start_time and end_time:
            try:
                start = datetime.fromisoformat(start_time)
                end = datetime.fromisoformat(end_time)
                duration = int((end - start).total_seconds())
            except:
                pass

        cursor.execute('''
            INSERT INTO runs 
            (project_id, run_token, status, pages_scraped, start_time, end_time, duration_seconds, data_file, is_empty)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (project_id, run_token, status, pages, start_time, end_time, duration, data_file, is_empty))

        conn.commit()
        run_id = cursor.lastrowid
        self.disconnect()

        return run_id

    def store_scraped_data(self, run_id: int, project_id: int = None, data: dict | list = None):
        """Store scraped data from JSON"""
        conn = self.connect()
        cursor = conn.cursor()

        # If project_id not provided, get it from run
        if project_id is None:
            cursor.execute('SELECT project_id FROM runs WHERE id = ?', (run_id,))
            run = cursor.fetchone()
            if run:
                project_id = run['project_id']
            else:
                self.disconnect()
                return 0

        records = 0

        if isinstance(data, list):
            # Array of records
            for item in data:
                if isinstance(item, dict):
                    for key, value in item.items():
                        cursor.execute('''
                            INSERT INTO scraped_data (run_id, project_id, data_key, data_value)
                            VALUES (?, ?, ?, ?)
                        ''', (run_id, project_id, key, str(value)))
                    records += 1
        elif isinstance(data, dict):
            # Check if it contains an array (like { product: [...] })
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                    # This is the data array
                    for item in value:
                        for field, field_value in item.items():
                            cursor.execute('''
                                INSERT INTO scraped_data (run_id, project_id, data_key, data_value)
                                VALUES (?, ?, ?, ?)
                            ''', (run_id, project_id, field, str(field_value)))
                        records += 1
                    break

        # Update records count in runs table
        cursor.execute('UPDATE runs SET records_count = ? WHERE id = ?', (records, run_id))

        conn.commit()
        self.disconnect()

        return records

    def get_project_analytics(self, project_token: str) -> dict:
        """Get analytics for a specific project"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM projects WHERE token = ?', (project_token,))
        project = cursor.fetchone()

        if not project:
            self.disconnect()
            return None

        project_id = project['id']

        # Total runs
        cursor.execute('SELECT COUNT(*) as count FROM runs WHERE project_id = ?', (project_id,))
        total_runs = cursor.fetchone()['count']

        # Completed runs
        cursor.execute('SELECT COUNT(*) as count FROM runs WHERE project_id = ? AND status = ?', 
                      (project_id, 'complete'))
        completed_runs = cursor.fetchone()['count']

        # Total records scraped
        cursor.execute('SELECT SUM(records_count) as total FROM runs WHERE project_id = ?', (project_id,))
        total_records = cursor.fetchone()['total'] or 0

        # Average duration
        cursor.execute('''
            SELECT AVG(duration_seconds) as avg_duration FROM runs 
            WHERE project_id = ? AND duration_seconds IS NOT NULL AND status = ?
        ''', (project_id, 'complete'))
        avg_duration = cursor.fetchone()['avg_duration'] or 0

        # Latest run
        cursor.execute('''
            SELECT run_token, status, pages_scraped, start_time, records_count FROM runs 
            WHERE project_id = ? ORDER BY created_at DESC LIMIT 1
        ''', (project_id,))
        latest_run = cursor.fetchone()

        # Pages scraped trend (last 10 runs)
        cursor.execute('''
            SELECT pages_scraped, start_time FROM runs 
            WHERE project_id = ? ORDER BY created_at DESC LIMIT 10
        ''', (project_id,))
        pages_trend = [dict(row) for row in cursor.fetchall()]

        self.disconnect()

        return {
            'project_token': project_token,
            'total_runs': total_runs,
            'completed_runs': completed_runs,
            'total_records': int(total_records),
            'avg_duration': round(avg_duration, 2),
            'latest_run': dict(latest_run) if latest_run else None,
            'pages_trend': pages_trend
        }

    def get_all_analytics(self) -> list:
        """Get analytics for all projects"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('SELECT token FROM projects')
        projects = cursor.fetchall()
        self.disconnect()

        analytics = []
        for project in projects:
            analytics.append(self.get_project_analytics(project['token']))

        return analytics

    def import_from_json(self, json_file: str, project_token: str, run_token: str, 
                        status: str, pages: int, start_time: str, end_time: str = None):
        """Import data from JSON file into database"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Ensure project exists
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM projects WHERE token = ?', (project_token,))
            project = cursor.fetchone()
            self.disconnect()

            if not project:
                return None

            project_id = project['id']

            # Add run record
            run_id = self.add_run(
                project_token=project_token,
                run_token=run_token,
                status=status,
                pages=pages,
                start_time=start_time,
                end_time=end_time,
                data_file=json_file,
                is_empty=len(str(data)) < 10
            )

            if run_id:
                # Store the data with proper project_id
                records = self.store_scraped_data(run_id, project_id, data)
                return {'run_id': run_id, 'records': records}
        except Exception as e:
            print(f"Error importing JSON: {e}")
            return None

    def export_data(self, project_token: str, format: str = 'json') -> str | None:
        """Export all project data"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM projects WHERE token = ?', (project_token,))
        project = cursor.fetchone()

        if not project:
            self.disconnect()
            return None

        project_id = project['id']

        cursor.execute('''
            SELECT run_token, status, pages_scraped, start_time, records_count 
            FROM runs WHERE project_id = ? ORDER BY created_at DESC
        ''', (project_id,))
        
        runs = [dict(row) for row in cursor.fetchall()]

        if format == 'json':
            self.disconnect()
            return json.dumps({'runs': runs, 'project_token': project_token}, indent=2)
        
        self.disconnect()
        return None

    # ========== RECOVERY OPERATIONS ==========

    def create_recovery_operation(self, original_run_id: int, project_id: int, 
                                 last_product_url: str, last_product_name: str = None) -> int:
        """Create a new recovery operation record"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO recovery_operations 
            (original_run_id, project_id, last_product_url, last_product_name, 
             stopped_timestamp, recovery_triggered_timestamp, status)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'pending')
        ''', (original_run_id, project_id, last_product_url, last_product_name))

        conn.commit()
        recovery_id = cursor.lastrowid
        self.disconnect()
        return recovery_id

    def link_recovery_run(self, recovery_operation_id: int, recovery_run_id: int):
        """Link a recovery run to a recovery operation"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE recovery_operations 
            SET recovery_run_id = ?, recovery_started_timestamp = CURRENT_TIMESTAMP, status = 'in_progress'
            WHERE id = ?
        ''', (recovery_run_id, recovery_operation_id))

        conn.commit()
        self.disconnect()

    def complete_recovery_operation(self, recovery_operation_id: int, 
                                   final_count: int, duplicates: int):
        """Mark recovery operation as complete"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE recovery_operations 
            SET recovery_completed_timestamp = CURRENT_TIMESTAMP, 
                status = 'completed',
                final_data_count = ?,
                duplicates_removed = ?
            WHERE id = ?
        ''', (final_count, duplicates, recovery_operation_id))

        conn.commit()
        self.disconnect()

    def get_last_product(self, run_id: int) -> dict:
        """Get the last product scraped from a run"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT data_key, data_value FROM scraped_data 
            WHERE run_id = ? 
            ORDER BY created_at DESC 
            LIMIT 1
        ''', (run_id,))

        result = cursor.fetchone()
        self.disconnect()
        return dict(result) if result else None

    def get_run_data_summary(self, run_id: int) -> dict:
        """Get summary of all data for a run"""
        conn = self.connect()
        cursor = conn.cursor()

        # Get run info
        cursor.execute('''
            SELECT r.run_token, r.status, r.pages_scraped, r.start_time, 
                   r.records_count, p.token as project_token
            FROM runs r
            JOIN projects p ON r.project_id = p.id
            WHERE r.id = ?
        ''', (run_id,))

        run_info = cursor.fetchone()
        
        if not run_info:
            self.disconnect()
            return None

        # Get sample of data
        cursor.execute('''
            SELECT data_key, data_value FROM scraped_data 
            WHERE run_id = ? 
            ORDER BY created_at DESC 
            LIMIT 5
        ''', (run_id,))

        sample_data = [dict(row) for row in cursor.fetchall()]

        self.disconnect()

        return {
            'run_token': run_info['run_token'],
            'status': run_info['status'],
            'pages_scraped': run_info['pages_scraped'],
            'start_time': run_info['start_time'],
            'records_count': run_info['records_count'],
            'project_token': run_info['project_token'],
            'sample_data': sample_data
        }

    def get_unique_product_urls(self, run_id: int) -> list:
        """Extract unique product URLs from scraped data"""
        conn = self.connect()
        cursor = conn.cursor()

        # Try common field names for URLs
        url_fields = ['url', 'product_url', 'link', 'href', 'page_url']
        
        for field in url_fields:
            cursor.execute('''
                SELECT DISTINCT data_value FROM scraped_data 
                WHERE run_id = ? AND data_key = ? AND data_value LIKE 'http%'
                ORDER BY created_at DESC
            ''', (run_id, field))
            
            urls = [row['data_value'] for row in cursor.fetchall()]
            if urls:
                self.disconnect()
                return urls

        self.disconnect()
        return []

    def record_data_lineage(self, run_id: int, product_urls: list, recovery_op_id: int = None):
        """Record which products came from which run for deduplication"""
        conn = self.connect()
        cursor = conn.cursor()

        for url in product_urls:
            # Create hash of URL for quick duplicate detection
            import hashlib
            product_hash = hashlib.md5(url.encode()).hexdigest()

            cursor.execute('''
                INSERT INTO data_lineage 
                (source_run_id, recovery_operation_id, product_url, product_hash)
                VALUES (?, ?, ?, ?)
            ''', (run_id, recovery_op_id, url, product_hash))

        conn.commit()
        self.disconnect()

    def get_recovery_status(self, project_id: int) -> dict:
        """Get current recovery status for a project"""
        conn = self.connect()
        cursor = conn.cursor()

        # Latest recovery operation
        cursor.execute('''
            SELECT * FROM recovery_operations 
            WHERE project_id = ? 
            ORDER BY created_at DESC 
            LIMIT 1
        ''', (project_id,))

        recovery = cursor.fetchone()
        self.disconnect()

        if not recovery:
            return {'status': 'none', 'in_recovery': False}

        return {
            'status': recovery['status'],
            'in_recovery': recovery['status'] in ['pending', 'in_progress'],
            'last_product_url': recovery['last_product_url'],
            'last_product_name': recovery['last_product_name'],
            'stopped_timestamp': recovery['stopped_timestamp'],
            'recovery_triggered_timestamp': recovery['recovery_triggered_timestamp'],
            'attempt_number': recovery['attempt_number'],
            'original_data_count': recovery['original_data_count'],
            'recovery_data_count': recovery['recovery_data_count'],
            'final_data_count': recovery['final_data_count'],
            'duplicates_removed': recovery['duplicates_removed']
        }

    def get_analytics_data(self, project_id: int) -> dict:
        """Get comprehensive analytics for a project"""
        conn = self.connect()
        cursor = conn.cursor()

        # Get all runs for this project
        cursor.execute('''
            SELECT id, run_token, status, pages_scraped, start_time, 
                   end_time, duration_seconds, records_count, created_at
            FROM runs 
            WHERE project_id = ? 
            ORDER BY created_at DESC
        ''', (project_id,))

        runs = [dict(row) for row in cursor.fetchall()]

        # Get total and unique records
        cursor.execute('''
            SELECT COUNT(*) as total_records FROM scraped_data
            WHERE project_id = ?
        ''', (project_id,))

        total_records = cursor.fetchone()['total_records']

        # Get latest run info
        cursor.execute('''
            SELECT records_count, pages_scraped, status FROM runs
            WHERE project_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (project_id,))

        latest_run = cursor.fetchone()

        # Check for active recovery
        recovery_status = self.get_recovery_status(project_id)

        self.disconnect()

        return {
            'total_runs': len(runs),
            'total_records': total_records,
            'latest_run': dict(latest_run) if latest_run else None,
            'runs_history': runs[:10],  # Last 10 runs
            'recovery_status': recovery_status,
            'scraping_rate': self._calculate_scraping_rate(runs)
        }

    def _calculate_scraping_rate(self, runs: list) -> dict:
        """Calculate scraping rate (items per minute)"""
        if not runs or len(runs) < 2:
            return {'items_per_minute': 0, 'estimated_total': 0}

        completed_runs = [r for r in runs if r['duration_seconds'] and r['records_count']]
        if not completed_runs:
            return {'items_per_minute': 0, 'estimated_total': 0}

        avg_rate = sum(r['records_count'] / (r['duration_seconds'] / 60) 
                       for r in completed_runs) / len(completed_runs)
        
        # If current run is in progress, estimate total
        current_run = runs[0]
        estimated_total = current_run['records_count']
        if current_run['status'] != 'complete' and avg_rate > 0 and current_run['duration_seconds']:
            # Estimate based on current progress and average rate
            minutes_elapsed = current_run['duration_seconds'] / 60
            estimated_total = int(avg_rate * minutes_elapsed * 1.5)  # 1.5x multiplier for estimated completion

        return {
            'items_per_minute': round(avg_rate, 2),
            'estimated_total': estimated_total
        }


    def create_project_with_pages(self, token: str, title: str, url: str, 
                                   target_pages: int = 1) -> bool:
        """
        Create a project with target pages for scraping
        
        Args:
            token: ParseHub API token
            title: Project title
            url: Target URL to scrape
            target_pages: Number of pages to scrape
        """
        self.connect()
        cursor = self.connection.cursor()
        
        try:
            # First, add the project
            cursor.execute('''
                INSERT INTO projects (token, title, url)
                VALUES (?, ?, ?)
            ''', (token, title, url))
            
            project_id = cursor.lastrowid
            
            # Store target pages in run_checkpoints
            cursor.execute('''
                INSERT INTO run_checkpoints 
                (project_id, checkpoint_type, checkpoint_data, created_at)
                VALUES (?, 'target_pages', ?, datetime('now'))
            ''', (project_id, json.dumps({
                'target_pages': target_pages,
                'url': url,
                'created_at': datetime.now().isoformat()
            })))
            
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error creating project with pages: {e}")
            return False
        finally:
            self.disconnect()
    
    def get_last_scraped_page(self, project_id: int) -> Optional[int]:
        """
        Get the last (highest) page number scraped for a project
        
        Returns:
            Page number or None if no pages scraped
        """
        self.connect()
        cursor = self.connection.cursor()
        
        try:
            cursor.execute('''
                SELECT json_extract(data, '$.page_number') as page_number
                FROM scraped_data
                WHERE project_id = ?
                ORDER BY CAST(json_extract(data, '$.page_number') AS INTEGER) DESC
                LIMIT 1
            ''', (project_id,))
            
            result = cursor.fetchone()
            return int(result[0]) if result and result[0] else None
        except Exception as e:
            print(f"Error getting last scraped page: {e}")
            return None
        finally:
            self.disconnect()
    
    def get_total_scraped_count(self, project_id: int) -> int:
        """Get total number of records scraped for a project"""
        self.connect()
        cursor = self.connection.cursor()
        
        try:
            cursor.execute('''
                SELECT COUNT(*) as total
                FROM scraped_data
                WHERE project_id = ?
            ''', (project_id,))
            
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            print(f"Error getting scraped count: {e}")
            return 0
        finally:
            self.disconnect()
    
    def get_target_pages(self, project_id: int) -> Optional[int]:
        """Get the target page count for a project"""
        self.connect()
        cursor = self.connection.cursor()
        
        try:
            cursor.execute('''
                SELECT checkpoint_data
                FROM run_checkpoints
                WHERE project_id = ? AND checkpoint_type = 'target_pages'
                ORDER BY created_at DESC
                LIMIT 1
            ''', (project_id,))
            
            result = cursor.fetchone()
            if result:
                data = json.loads(result[0])
                return data.get('target_pages')
            return None
        except Exception as e:
            print(f"Error getting target pages: {e}")
            return None
        finally:
            self.disconnect()
    
    def record_scraped_data_with_page(self, run_id: int, project_id: int, 
                                       page_number: int, data: dict) -> bool:
        """
        Record scraped data with page tracking
        
        Args:
            run_id: Run ID
            project_id: Project ID
            page_number: Current page number
            data: Scraped data (dict)
        """
        self.connect()
        cursor = self.connection.cursor()
        
        try:
            # Add page_number to data
            data_with_page = dict(data)
            data_with_page['page_number'] = page_number
            
            cursor.execute('''
                INSERT INTO scraped_data (run_id, project_id, data)
                VALUES (?, ?, ?)
            ''', (run_id, project_id, json.dumps(data_with_page)))
            
            # Update run checkpoint
            cursor.execute('''
                INSERT OR REPLACE INTO run_checkpoints
                (project_id, checkpoint_type, checkpoint_data, created_at)
                VALUES (?, 'last_page', ?, datetime('now'))
            ''', (project_id, json.dumps({
                'last_page': page_number,
                'total_records': self.get_total_scraped_count(project_id),
                'timestamp': datetime.now().isoformat()
            })))
            
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error recording scraped data with page: {e}")
            return False
        finally:
            self.disconnect()
    
    def get_pagination_checkpoint(self, project_id: int) -> dict:
        """
        Get pagination checkpoint data for a project
        
        Returns:
            {
                'last_page': int,
                'target_pages': int,
                'total_records': int,
                'pages_remaining': int,
                'completion_percentage': float
            }
        """
        self.connect()
        cursor = self.connection.cursor()
        
        try:
            # Get last page and target pages
            cursor.execute('''
                SELECT checkpoint_data
                FROM run_checkpoints
                WHERE project_id = ? AND checkpoint_type IN ('last_page', 'target_pages')
                ORDER BY created_at DESC
            ''', (project_id,))
            
            checkpoints = cursor.fetchall()
            last_page_data = None
            target_pages_data = None
            
            for checkpoint in checkpoints:
                data = json.loads(checkpoint[0])
                if 'last_page' in data:
                    last_page_data = data
                elif 'target_pages' in data:
                    target_pages_data = data
            
            last_page = last_page_data['last_page'] if last_page_data else 0
            target_pages = target_pages_data['target_pages'] if target_pages_data else 0
            total_records = last_page_data.get('total_records', self.get_total_scraped_count(project_id)) if last_page_data else 0
            
            pages_remaining = max(0, target_pages - last_page) if target_pages else 0
            completion_pct = (last_page / target_pages * 100) if target_pages > 0 else 0
            
            return {
                'last_page': last_page,
                'target_pages': target_pages,
                'total_records': total_records,
                'pages_remaining': pages_remaining,
                'completion_percentage': round(completion_pct, 2)
            }
        except Exception as e:
            print(f"Error getting pagination checkpoint: {e}")
            return None
        finally:
            self.disconnect()

    # ========== REAL-TIME MONITORING METHODS ==========

    def create_monitoring_session(self, project_id: int, run_token: str, target_pages: int = 1) -> int:
        """
        Create a new monitoring session for real-time data collection
        
        Args:
            project_id: Project ID
            run_token: ParseHub run token
            target_pages: Target number of pages to scrape
        
        Returns:
            Session ID or None if failed
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO monitoring_sessions 
                (project_id, run_token, target_pages, status, start_time, created_at, updated_at)
                VALUES (?, ?, ?, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (project_id, run_token, target_pages))
            
            conn.commit()
            session_id = cursor.lastrowid
            return session_id
        except Exception as e:
            print(f"Error creating monitoring session: {e}")
            return None
        finally:
            self.disconnect()

    def update_monitoring_session(self, session_id: int, status: str = None, 
                                 total_records: int = None, total_pages: int = None,
                                 progress_percentage: float = None, current_url: str = None,
                                 error_message: str = None) -> bool:
        """
        Update monitoring session with current status
        
        Args:
            session_id: Session ID to update
            status: New status ('active', 'completed', 'failed', 'cancelled')
            total_records: Total records found so far
            total_pages: Total pages scraped so far
            progress_percentage: Progress percentage (0-100)
            current_url: Current URL being scraped
            error_message: Error message if any
        
        Returns:
            True if update successful, False otherwise
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            update_fields = ['updated_at = CURRENT_TIMESTAMP']
            update_params = []
            
            if status is not None:
                update_fields.append('status = ?')
                update_params.append(status)
            
            if total_records is not None:
                update_fields.append('total_records = ?')
                update_params.append(total_records)
            
            if total_pages is not None:
                update_fields.append('total_pages = ?')
                update_params.append(total_pages)
            
            if progress_percentage is not None:
                update_fields.append('progress_percentage = ?')
                update_params.append(progress_percentage)
            
            if current_url is not None:
                update_fields.append('current_url = ?')
                update_params.append(current_url)
            
            if error_message is not None:
                update_fields.append('error_message = ?')
                update_params.append(error_message)
            
            if status == 'completed' or status == 'failed':
                update_fields.append('end_time = CURRENT_TIMESTAMP')
            
            update_params.append(session_id)
            
            query = f'''
                UPDATE monitoring_sessions 
                SET {', '.join(update_fields)}
                WHERE id = ?
            '''
            
            cursor.execute(query, tuple(update_params))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating monitoring session: {e}")
            return False
        finally:
            self.disconnect()

    def store_scraped_records(self, session_id: int, project_id: int, run_token: str,
                             records: list, page_number: int) -> int:
        """
        Store scraped records from a page with deduplication
        
        Args:
            session_id: Monitoring session ID
            project_id: Project ID
            run_token: ParseHub run token
            records: List of data records (dicts)
            page_number: Current page number
        
        Returns:
            Number of records stored (new records)
        """
        import hashlib
        
        conn = self.connect()
        cursor = conn.cursor()
        
        records_stored = 0
        
        try:
            for record in records:
                # Create hash of record data for deduplication
                record_json = json.dumps(record, sort_keys=True)
                data_hash = hashlib.md5(record_json.encode()).hexdigest()
                
                try:
                    cursor.execute('''
                        INSERT INTO scraped_records 
                        (session_id, project_id, run_token, page_number, data_hash, data_json)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (session_id, project_id, run_token, page_number, data_hash, record_json))
                    records_stored += 1
                except sqlite3.IntegrityError:
                    # Record already exists (duplicate), skip
                    pass
            
            conn.commit()
            return records_stored
        except Exception as e:
            print(f"Error storing scraped records: {e}")
            return 0
        finally:
            self.disconnect()

    def get_session_records(self, session_id: int, limit: int = 100, offset: int = 0) -> list:
        """
        Get paginated records from a monitoring session
        
        Args:
            session_id: Monitoring session ID
            limit: Number of records to fetch
            offset: Number of records to skip
        
        Returns:
            List of records as dicts
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, page_number, data_json, created_at
                FROM scraped_records
                WHERE session_id = ?
                ORDER BY created_at ASC
                LIMIT ? OFFSET ?
            ''', (session_id, limit, offset))
            
            records = cursor.fetchall()
            result = []
            
            for record in records:
                data = json.loads(record['data_json'])
                result.append({
                    'id': record['id'],
                    'page_number': record['page_number'],
                    'data': data,
                    'created_at': record['created_at']
                })
            
            return result
        except Exception as e:
            print(f"Error getting session records: {e}")
            return []
        finally:
            self.disconnect()

    def get_session_records_count(self, session_id: int) -> int:
        """Get total number of records in a session"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT COUNT(*) as total FROM scraped_records WHERE session_id = ?
            ''', (session_id,))
            
            result = cursor.fetchone()
            return result['total'] if result else 0
        except Exception as e:
            print(f"Error getting session records count: {e}")
            return 0
        finally:
            self.disconnect()

    def get_session_summary(self, session_id: int) -> dict:
        """
        Get summary of a monitoring session
        
        Args:
            session_id: Monitoring session ID
        
        Returns:
            Session summary dict with status, counts, timing
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, project_id, run_token, target_pages, status, 
                       start_time, end_time, total_records, total_pages, 
                       progress_percentage, current_url, error_message, created_at
                FROM monitoring_sessions
                WHERE id = ?
            ''', (session_id,))
            
            session = cursor.fetchone()
            
            if not session:
                return None
            
            # Get actual record count
            cursor.execute('''
                SELECT COUNT(*) as total, 
                       COUNT(DISTINCT page_number) as pages,
                       MAX(page_number) as max_page
                FROM scraped_records
                WHERE session_id = ?
            ''', (session_id,))
            
            counts = cursor.fetchone()
            
            return {
                'session_id': session['id'],
                'project_id': session['project_id'],
                'run_token': session['run_token'],
                'target_pages': session['target_pages'],
                'status': session['status'],
                'start_time': session['start_time'],
                'end_time': session['end_time'],
                'total_records': counts['total'],
                'total_pages': counts['pages'] or 0,
                'max_page_scraped': counts['max_page'],
                'progress_percentage': session['progress_percentage'],
                'current_url': session['current_url'],
                'error_message': session['error_message'],
                'created_at': session['created_at']
            }
        except Exception as e:
            print(f"Error getting session summary: {e}")
            return None
        finally:
            self.disconnect()

    def get_data_as_csv(self, session_id: int) -> str:
        """
        Export session data as CSV
        
        Args:
            session_id: Monitoring session ID
        
        Returns:
            CSV string or None if no records
        """
        import csv
        from io import StringIO
        
        records = self.get_session_records(session_id, limit=1000000, offset=0)
        
        if not records:
            return None
        
        try:
            # Get all unique keys across all records
            all_keys = set()
            for record in records:
                if isinstance(record['data'], dict):
                    all_keys.update(record['data'].keys())
            
            all_keys = sorted(list(all_keys))
            
            # Add metadata columns
            columns = ['page_number', 'created_at'] + all_keys
            
            # Create CSV
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=columns)
            writer.writeheader()
            
            for record in records:
                row = {
                    'page_number': record['page_number'],
                    'created_at': record['created_at']
                }
                
                if isinstance(record['data'], dict):
                    row.update(record['data'])
                
                writer.writerow({k: row.get(k, '') for k in columns})
            
            return output.getvalue()
        except Exception as e:
            print(f"Error converting to CSV: {e}")
            return None

    def get_monitoring_status_for_project(self, project_id: int) -> dict:
        """
        Get latest monitoring session status for a project
        
        Args:
            project_id: Project ID
        
        Returns:
            Latest session summary or None
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id FROM monitoring_sessions
                WHERE project_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            ''', (project_id,))
            
            session = cursor.fetchone()
            
            if not session:
                return None
            
            return self.get_session_summary(session['id'])
        except Exception as e:
            print(f"Error getting monitoring status: {e}")
            return None
        finally:
            self.disconnect()

    def store_analytics_data(self, project_token: str, run_token: str, analytics_data: dict, records: list, csv_data: str = None):
        """Store analytics data and records to database"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # Store analytics cache
            analytics_json = json.dumps(analytics_data)
            cursor.execute('''
                INSERT OR REPLACE INTO analytics_cache
                (project_token, run_token, total_records, total_fields, total_runs, completed_runs, 
                 progress_percentage, status, analytics_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                project_token,
                run_token,
                analytics_data['overview']['total_records_scraped'],
                analytics_data['data_quality']['total_fields'],
                analytics_data['overview']['total_runs'],
                analytics_data['overview']['completed_runs'],
                analytics_data['overview']['progress_percentage'],
                analytics_data['recovery']['status'],
                analytics_json,
                datetime.now().isoformat()
            ))
            
            # Store CSV data if provided
            if csv_data:
                cursor.execute('''
                    INSERT OR REPLACE INTO csv_exports
                    (project_token, run_token, csv_data, row_count, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    project_token,
                    run_token,
                    csv_data,
                    len(records),
                    datetime.now().isoformat()
                ))
            
            # Store individual records
            for idx, record in enumerate(records):
                record_json = json.dumps(record) if isinstance(record, dict) else str(record)
                cursor.execute('''
                    INSERT OR REPLACE INTO analytics_records
                    (project_token, run_token, record_index, record_data)
                    VALUES (?, ?, ?, ?)
                ''', (
                    project_token,
                    run_token,
                    idx,
                    record_json
                ))
            
            conn.commit()
            self.disconnect()
            return True
            
        except Exception as e:
            print(f"Error storing analytics data: {e}")
            self.disconnect()
            return False

    def get_analytics_data(self, project_token: str):
        """Retrieve stored analytics data"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # Get analytics cache
            cursor.execute('''
                SELECT project_token, run_token, total_records, total_fields, total_runs, 
                       completed_runs, progress_percentage, status, analytics_json, updated_at
                FROM analytics_cache
                WHERE project_token = ?
                ORDER BY updated_at DESC
                LIMIT 1
            ''', (project_token,))
            
            analytics_row = cursor.fetchone()
            
            if not analytics_row:
                self.disconnect()
                return None
            
            analytics = json.loads(analytics_row['analytics_json'])
            
            # Get CSV data
            cursor.execute('''
                SELECT csv_data FROM csv_exports
                WHERE project_token = ?
                ORDER BY updated_at DESC
                LIMIT 1
            ''', (project_token,))
            
            csv_row = cursor.fetchone()
            if csv_row and csv_row['csv_data']:
                analytics['csv_data'] = csv_row['csv_data']
            
            # Get records
            cursor.execute('''
                SELECT record_data FROM analytics_records
                WHERE project_token = ?
                ORDER BY record_index ASC
            ''', (project_token,))
            
            records = []
            for row in cursor.fetchall():
                try:
                    records.append(json.loads(row['record_data']))
                except:
                    records.append(row['record_data'])
            
            if records:
                analytics['raw_data'] = records
            
            self.disconnect()
            return analytics
            
        except Exception as e:
            print(f"Error retrieving analytics data: {e}")
            self.disconnect()
            return None

    def clear_analytics_data(self, project_token: str):
        """Clear analytics data for a project"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM analytics_cache WHERE project_token = ?', (project_token,))
            cursor.execute('DELETE FROM csv_exports WHERE project_token = ?', (project_token,))
            cursor.execute('DELETE FROM analytics_records WHERE project_token = ?', (project_token,))
            
            conn.commit()
            self.disconnect()
            return True
            
        except Exception as e:
            print(f"Error clearing analytics data: {e}")
            self.disconnect()
            return False


if __name__ == '__main__':
    db = ParseHubDatabase()
    
    # Test
    db.add_project('test_token', 'Test Project', 'test@example.com', 'https://example.com')
    print("[OK] Database initialized successfully!")
    print(f"Database file: {db.db_path}")
