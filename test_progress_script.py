#!/usr/bin/env python3
"""
Test the get_session_progress.py script directly.
"""

import subprocess
import json
import sys

# Test with session ID 1
test_input = json.dumps({'session_id': 1})

try:
    result = subprocess.run(
        [sys.executable, 'backend/get_session_progress.py'],
        input=test_input,
        capture_output=True,
        text=True,
        timeout=5
    )
    
    print("[TEST] Running get_session_progress.py with session_id=1")
    print(f"[INFO] Exit code: {result.returncode}")
    
    if result.stdout:
        print("[OUTPUT] stdout:")
        try:
            data = json.loads(result.stdout)
            print(json.dumps(data, indent=2))
        except json.JSONDecodeError as e:
            print(f"  {result.stdout}")
            print(f"  [ERROR] Failed to parse JSON: {e}")
    
    if result.stderr:
        print("[OUTPUT] stderr:")
        print(f"  {result.stderr}")
    
    if result.returncode == 0 and result.stdout:
        try:
            data = json.loads(result.stdout)
            print("\n[SUCCESS] Script executed successfully and returned valid JSON")
            print(f"  - Session: {data.get('project_name')} ({data.get('session_id')})")
            print(f"  - Progress: {data.get('pages_completed')}/{data.get('total_pages_target')} pages ({data.get('percentage')}%)")
            print(f"  - Status: {data.get('status')}")
            print(f"  - Iterations: {data.get('iterations_completed')}/{data.get('total_iterations_needed')}")
        except:
            pass
    else:
        print("\n[ERROR] Script failed or didn't return output")
    
except subprocess.TimeoutExpired:
    print("[ERROR] Script timed out")
except Exception as e:
    print(f"[ERROR] {e}")
