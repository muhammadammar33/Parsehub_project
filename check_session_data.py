#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('d:\\Parsehub\\parsehub.db')
cursor = conn.cursor()

print("=== Checking URL Patterns ===")
cursor.execute("SELECT * FROM url_patterns")
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(f"  {row}")
else:
    print("  No URL patterns found!")

print("\n=== Checking Sessions ===")
cursor.execute("SELECT id, project_token, project_name, total_pages_target, pages_completed, status FROM scraping_sessions")
for row in cursor.fetchall():
    print(f"  Session {row[0]}: {row[1]} ({row[2]}) - {row[4]}/{row[3]} pages, status={row[5]}")

conn.close()
