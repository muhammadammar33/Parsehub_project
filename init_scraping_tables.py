#!/usr/bin/env python3
"""
Initialize the database schema for incremental scraping.
Creates:
- scraping_sessions: Track overall incremental scraping sessions
- iteration_runs: Track individual iterations within a session
- url_patterns: Store URL patterns for incremental pagination
"""

import sqlite3
import sys
import os
from datetime import datetime

os.chdir('d:\\Parsehub')

try:
    conn = sqlite3.connect('parsehub.db')
    cursor = conn.cursor()
    
    print("[INIT] Creating scraping_sessions table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scraping_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_token TEXT NOT NULL,
            project_name TEXT NOT NULL,
            total_pages_target INTEGER NOT NULL,
            pages_completed INTEGER DEFAULT 0,
            current_iteration INTEGER DEFAULT 0,
            status TEXT DEFAULT 'running',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_token, total_pages_target)
        )
    ''')
    print("[OK] scraping_sessions table created")
    
    print("[INIT] Creating iteration_runs table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS iteration_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            iteration_number INTEGER NOT NULL,
            parsehub_project_name TEXT,
            parsehub_project_token TEXT,
            run_token TEXT,
            start_page_number INTEGER,
            end_page_number INTEGER,
            csv_data TEXT,
            records_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES scraping_sessions(id),
            UNIQUE(session_id, iteration_number)
        )
    ''')
    print("[OK] iteration_runs table created")
    
    print("[INIT] Creating url_patterns table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS url_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_token TEXT NOT NULL,
            original_url TEXT NOT NULL,
            pattern_type TEXT DEFAULT 'unknown',
            pattern_regex TEXT,
            last_page_placeholder TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_token)
        )
    ''')
    print("[OK] url_patterns table created")
    
    # Commit the changes
    conn.commit()
    
    # Verify tables were created
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('scraping_sessions', 'iteration_runs', 'url_patterns')")
    created_tables = [row[0] for row in cursor.fetchall()]
    
    print(f"\n[SUCCESS] Created {len(created_tables)} table(s):")
    for table in created_tables:
        print(f"  ✓ {table}")
    
    conn.close()
    sys.exit(0)
    
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)
