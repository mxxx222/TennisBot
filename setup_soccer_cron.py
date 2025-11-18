#!/usr/bin/env python3
"""
Setup cron job for Soccer Screener
Configures daily execution at 08:00 EET (06:00 UTC)
"""

import os
import subprocess
import sys
from pathlib import Path

def get_current_crontab():
    """Get current crontab entries"""
    try:
        result = subprocess.run(['crontab', '-l'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except subprocess.CalledProcessError:
        return []

def setup_soccer_cron():
    """Setup the cron job for daily soccer screening"""
    
    script_dir = Path(__file__).parent.absolute()
    wrapper_script = script_dir / "run_soccer_screener.sh"
    
    if not wrapper_script.exists():
        print(f"❌ Wrapper script not found: {wrapper_script}")
        return False
    
    # Cron job entry (06:00 UTC = 08:00 EET)
    cron_entry = f"0 6 * * * {wrapper_script}"
    
    # Get existing crontab
    existing_entries = get_current_crontab()
    
    # Check if soccer job already exists
    soccer_entries = [entry for entry in existing_entries if 'run_soccer_screener.sh' in entry]
    
    if soccer_entries:
        print("🔄 Soccer Screener cron job already exists:")
        for entry in soccer_entries:
            print(f"   {entry}")
        
        response = input("Replace existing entry? (y/N): ").lower()
        if response != 'y':
            print("⏹️ Keeping existing cron job")
            return True
        
        # Remove existing soccer entries
        existing_entries = [entry for entry in existing_entries 
                          if 'run_soccer_screener.sh' not in entry and entry.strip()]
    
    # Add new entry
    new_entries = existing_entries + [cron_entry]
    
    # Write new crontab
    try:
        crontab_content = '\n'.join(new_entries) + '\n'
        
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=crontab_content)
        
        if process.returncode == 0:
            print("✅ Soccer Screener cron job installed successfully!")
            print(f"⚽ Will run daily at 08:00 EET (06:00 UTC)")
            print(f"📁 Script: {wrapper_script}")
            print(f"📝 Entry: {cron_entry}")
            return True
        else:
            print("❌ Failed to install cron job")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up cron job: {e}")
        return False

def main():
    print("⚽ Soccer Screener - Cron Job Setup")
    print("=" * 40)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--setup':
        success = setup_soccer_cron()
        sys.exit(0 if success else 1)
    
    print("💡 Run with --setup to install daily automation")
    print("Example: python3 setup_soccer_cron.py --setup")

if __name__ == "__main__":
    main()
