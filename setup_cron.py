#!/usr/bin/env python3
"""
Setup cron job for Tennis ITF Screener
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
        # No crontab exists yet
        return []

def setup_cron_job():
    """Setup the cron job for daily screening"""
    
    # Get script directory
    script_dir = Path(__file__).parent.absolute()
    wrapper_script = script_dir / "run_screener.sh"
    
    if not wrapper_script.exists():
        print(f"❌ Wrapper script not found: {wrapper_script}")
        return False
    
    # Cron job entry (06:00 UTC = 08:00 EET)
    cron_entry = f"0 6 * * * {wrapper_script}"
    
    # Get existing crontab
    existing_entries = get_current_crontab()
    
    # Check if our job already exists
    tennis_entries = [entry for entry in existing_entries if 'run_screener.sh' in entry]
    
    if tennis_entries:
        print("🔄 Tennis ITF Screener cron job already exists:")
        for entry in tennis_entries:
            print(f"   {entry}")
        
        response = input("Replace existing entry? (y/N): ").lower()
        if response != 'y':
            print("⏹️ Keeping existing cron job")
            return True
        
        # Remove existing tennis entries
        existing_entries = [entry for entry in existing_entries 
                          if 'run_screener.sh' not in entry and entry.strip()]
    
    # Add new entry
    new_entries = existing_entries + [cron_entry]
    
    # Write new crontab
    try:
        # Create temporary crontab file
        crontab_content = '\n'.join(new_entries) + '\n'
        
        # Install new crontab
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=crontab_content)
        
        if process.returncode == 0:
            print("✅ Cron job installed successfully!")
            print(f"📅 Will run daily at 08:00 EET (06:00 UTC)")
            print(f"📁 Script: {wrapper_script}")
            print(f"📝 Entry: {cron_entry}")
            return True
        else:
            print("❌ Failed to install cron job")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up cron job: {e}")
        return False

def remove_cron_job():
    """Remove the Tennis ITF Screener cron job"""
    
    existing_entries = get_current_crontab()
    tennis_entries = [entry for entry in existing_entries if 'run_screener.sh' in entry]
    
    if not tennis_entries:
        print("ℹ️ No Tennis ITF Screener cron job found")
        return True
    
    print("🗑️ Found Tennis ITF Screener cron jobs:")
    for entry in tennis_entries:
        print(f"   {entry}")
    
    response = input("Remove these entries? (y/N): ").lower()
    if response != 'y':
        print("⏹️ Keeping existing cron jobs")
        return True
    
    # Remove tennis entries
    new_entries = [entry for entry in existing_entries 
                  if 'run_screener.sh' not in entry and entry.strip()]
    
    try:
        # Write new crontab
        crontab_content = '\n'.join(new_entries) + '\n' if new_entries else ''
        
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=crontab_content)
        
        if process.returncode == 0:
            print("✅ Cron job removed successfully!")
            return True
        else:
            print("❌ Failed to remove cron job")
            return False
            
    except Exception as e:
        print(f"❌ Error removing cron job: {e}")
        return False

def show_cron_status():
    """Show current cron job status"""
    
    existing_entries = get_current_crontab()
    tennis_entries = [entry for entry in existing_entries if 'run_screener.sh' in entry]
    
    if tennis_entries:
        print("✅ Tennis ITF Screener cron job is active:")
        for entry in tennis_entries:
            print(f"   {entry}")
        
        # Show next execution time
        try:
            # This is a simplified check - in reality you'd parse the cron expression
            print("📅 Scheduled to run daily at 08:00 EET (06:00 UTC)")
        except:
            pass
    else:
        print("❌ No Tennis ITF Screener cron job found")
        print("💡 Run with --setup to install the cron job")

def main():
    """Main entry point"""
    
    if len(sys.argv) > 1:
        action = sys.argv[1]
        
        if action == '--setup':
            success = setup_cron_job()
            sys.exit(0 if success else 1)
        elif action == '--remove':
            success = remove_cron_job()
            sys.exit(0 if success else 1)
        elif action == '--status':
            show_cron_status()
            sys.exit(0)
        else:
            print(f"❌ Unknown action: {action}")
            sys.exit(1)
    
    # Default: show status and offer setup
    print("🎾 Tennis ITF Screener - Cron Job Setup")
    print("=" * 40)
    
    show_cron_status()
    
    print("\nOptions:")
    print("  --setup   Install/update cron job")
    print("  --remove  Remove cron job")
    print("  --status  Show current status")
    
    print("\nExample:")
    print("  python setup_cron.py --setup")

if __name__ == "__main__":
    main()
