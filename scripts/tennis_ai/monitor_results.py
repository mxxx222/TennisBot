#!/usr/bin/env python3
"""
Automated monitoring script for match results.
Runs periodically to check for completed matches and update results.
Can be run manually or via cron job.
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / 'telegram_secrets.env'
if env_path.exists():
    load_dotenv(env_path)

# Import tracking script
sys.path.insert(0, str(project_root / 'scripts' / 'tennis_ai'))
from track_results import track_results

# CONFIG
CHECK_INTERVAL = 30  # minutes
MAX_ITERATIONS = None  # None = run indefinitely

def monitor_results():
    """Monitor match results periodically"""
    print("🔄 Starting Match Result Monitor...")
    print("=" * 70)
    print(f"Check interval: {CHECK_INTERVAL} minutes")
    print(f"Max iterations: {MAX_ITERATIONS or 'Unlimited'}")
    print(f"Press Ctrl+C to stop")
    print("")
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            print(f"\n{'='*70}")
            print(f"🔄 Check #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*70}\n")
            
            # Run tracking
            track_results()
            
            # Check if we should stop
            if MAX_ITERATIONS and iteration >= MAX_ITERATIONS:
                print(f"\n✅ Completed {MAX_ITERATIONS} iterations")
                break
            
            # Wait for next check
            if MAX_ITERATIONS is None or iteration < MAX_ITERATIONS:
                print(f"\n⏳ Waiting {CHECK_INTERVAL} minutes until next check...")
                time.sleep(CHECK_INTERVAL * 60)
    
    except KeyboardInterrupt:
        print(f"\n\n🛑 Monitor stopped by user")
        print(f"   Completed {iteration} checks")

if __name__ == '__main__':
    monitor_results()


