#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('d:\\Parsehub\\parsehub.db')
cursor = conn.cursor()

print("=== ALL Sessions ===")
cursor.execute("""
    SELECT id, project_token, project_name, total_pages_target, pages_completed, status 
    FROM scraping_sessions 
    ORDER BY id DESC
""")
for row in cursor.fetchall():
    print(f"  Session {row[0]}: token={row[1]}, name={row[2]}, target={row[3]}, completed={row[4]}, status={row[5]}")

print("\n=== ALL URL Patterns ===")
cursor.execute("SELECT id, project_token, original_url FROM url_patterns")
for row in cursor.fetchall():
    print(f"  {row[0]}: token={row[1]}, url={row[2]}")

print("\n=== Running Sessions ===")
cursor.execute("""
    SELECT id, project_token 
    FROM scraping_sessions 
    WHERE status = 'running'
""")
running = cursor.fetchall()
for session_id, project_token in running:
    # Check if URL exists
    cursor.execute("SELECT original_url FROM url_patterns WHERE project_token = ?", (project_token,))
    url_result = cursor.fetchone()
    url_status = f"✓ {url_result[0]}" if url_result else "✗ NO URL"
    print(f"  Session {session_id} (token={project_token}): {url_status}")

conn.close()
