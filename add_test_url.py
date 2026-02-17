#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('d:\\Parsehub\\parsehub.db')
cursor = conn.cursor()

# Add a test URL for the test session
test_url = "https://example.com/products?page=1"  
test_token = "test_token_123"

cursor.execute('''
    INSERT OR REPLACE INTO url_patterns
    (project_token, original_url, pattern_type, pattern_regex, last_page_placeholder)
    VALUES (?, ?, 'auto_detected', '', '')
''', (test_token, test_url))

conn.commit()

print(f"[OK] Saved URL for test session:")
print(f"  Token: {test_token}")
print(f"  URL: {test_url}")

# Verify
cursor.execute("SELECT * FROM url_patterns WHERE project_token = ?", (test_token,))
row = cursor.fetchone()
if row:
    print(f"\n[VERIFY] Confirmed in database: {row}")

conn.close()
