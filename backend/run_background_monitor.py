#!/usr/bin/env python3
"""
Background Session Monitor - Long-Running Service
This runs as a separate persistent process that monitors and executes scraping sessions.
Should be started once and kept running in the background.
"""

import sys
import time
import os

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from session_monitor import SessionMonitor


def main():
    """Start and run the session monitor indefinitely"""
    print("[START] Starting background session monitor service...", file=sys.stderr)
    
    try:
        monitor = SessionMonitor()
        
        # Run the monitor loop (this blocks indefinitely)
        print("[OK] Monitor initialized, entering main loop...", file=sys.stderr)
        monitor.monitor_loop()
        
    except KeyboardInterrupt:
        print("\n[STOP] Monitor interrupted by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Fatal error in monitor: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
