#!/usr/bin/env python3
import sqlite3
import sys
import os

os.chdir('d:\\Parsehub')

try:
    conn = sqlite3.connect('parsehub.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print("Tables in database:")
    for table in tables:
        print(f"  - {table}")
    
    # Check if required tables exist
    required = ['scraping_sessions', 'iteration_runs']
    print("\nRequired tables status:")
    for table in required:
        exists = table in tables
        status = "✓" if exists else "✗"
        print(f"  {status} {table}")
    
    # If tables exist, show their schema
    if 'scraping_sessions' in tables:
        print("\nscraping_sessions columns:")
        cursor.execute("PRAGMA table_info(scraping_sessions)")
        for row in cursor.fetchall():
            print(f"  - {row[1]} ({row[2]})")
    
    if 'iteration_runs' in tables:
        print("\niteration_runs columns:")
        cursor.execute("PRAGMA table_info(iteration_runs)")
        for row in cursor.fetchall():
            print(f"  - {row[1]} ({row[2]})")
    
    conn.close()
    sys.exit(0)
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
