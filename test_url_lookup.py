#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, 'd:\\Parsehub\\backend')

from scraping_session_service import ScrapingSessionService

service = ScrapingSessionService()

print("Testing _get_original_url logic...")

# Test: Get URL for session 1
session_id = 1

try:
    conn = service.db.connect()
    cursor = conn.cursor()

    # Step 1: Get project token from session
    print(f"\n[STEP 1] Getting project token for session {session_id}...")
    cursor.execute('SELECT project_token FROM scraping_sessions WHERE id = ?', (session_id,))
    result = cursor.fetchone()
    
    if result:
        project_token = result[0]
        print(f"  Found: {project_token}")
    else:
        print(f"  ERROR: No session found!")
        conn.close()
        sys.exit(1)

    # Step 2: Get URL pattern
    print(f"\n[STEP 2] Getting URL pattern for project token {project_token}...")
    cursor.execute('''
        SELECT original_url FROM url_patterns
        WHERE project_token = ?
    ''', (project_token,))

    result = cursor.fetchone()
    if result:
        original_url = result[0]
        print(f"  Found: {original_url}")
    else:
        print(f"  ERROR: No URL pattern found!")
        print(f"  Checking all URL patterns in database:")
        cursor.execute("SELECT project_token, original_url FROM url_patterns")
        for row in cursor.fetchall():
            print(f"    - {row[0]}: {row[1]}")

    conn.close()

except Exception as e:
    print(f"\n[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()
