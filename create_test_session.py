#!/usr/bin/env python3
"""
Create a test session for testing the progress API.
"""

import sqlite3
import sys
import os

os.chdir('d:\\Parsehub')

try:
    conn = sqlite3.connect('parsehub.db')
    cursor = conn.cursor()
    
    print("[TEST] Creating test session...")
    cursor.execute('''
        INSERT INTO scraping_sessions 
        (project_token, project_name, total_pages_target, pages_completed, status)
        VALUES (?, ?, ?, ?, ?)
    ''', ('test_token_123', 'Test Project', 165, 45, 'running'))
    
    session_id = cursor.lastrowid
    conn.commit()
    print(f"[OK] Created test session with ID: {session_id}")
    
    # Create some test iterations
    print("[TEST] Creating test iterations...")
    for i in range(1, 6):
        start_page = (i - 1) * 10 + 1
        end_page = i * 10
        status = 'completed' if i <= 5 else 'pending'
        
        cursor.execute('''
            INSERT INTO iteration_runs
            (session_id, iteration_number, parsehub_project_name, start_page_number, 
             end_page_number, records_count, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, i, f'Test Project Run {i}', start_page, end_page, 
              100 + i * 10, status))
    
    conn.commit()
    print("[OK] Created 5 test iterations")
    
    # Verify the data
    print("\n[VERIFY] Fetching test data...")
    cursor.execute('SELECT id, project_name, pages_completed, status FROM scraping_sessions WHERE id = ?', 
                   (session_id,))
    session = cursor.fetchone()
    print(f"  Session: {session}")
    
    cursor.execute('SELECT iteration_number, start_page_number, end_page_number, records_count, status FROM iteration_runs WHERE session_id = ? ORDER BY iteration_number',
                   (session_id,))
    iterations = cursor.fetchall()
    print(f"  Iterations found: {len(iterations)}")
    for it in iterations:
        print(f"    - Iteration {it[0]}: pages {it[1]}-{it[2]}, {it[3]} records, status={it[4]}")
    
    conn.close()
    print(f"\n[SUCCESS] Test session ready. Session ID: {session_id}")
    print("Now you can test with: http://localhost:3000/api/projects/incremental/progress?session_id=" + str(session_id))
    sys.exit(0)
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
