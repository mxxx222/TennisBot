#!/usr/bin/env python3
"""
🕐 ITF TENNIS ENHANCED PIPELINE SCHEDULER
==========================================

Long-running scheduler that executes enhanced pipeline with ITF Entries Intelligence:
1. ITF Entries Intelligence Scraper: 08:00 CET (07:00 UTC) - Daily
2. Enhanced Tennis AI Pipeline: 08:15 CET (07:15 UTC) - Daily (after intelligence update)

Uses Python's schedule library to manage timing.
Runs continuously, checking every minute for scheduled tasks.

Designed for Fly.io deployment with cron support.

Usage:
    python scripts/tennis_ai/scheduler_enhanced.py
"""

import os
import sys
import subprocess
import logging
import signal
import time
from pathlib import Path
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from telegram_secrets.env if it exists
env_path = project_root / 'telegram_secrets.env'
if env_path.exists():
    load_dotenv(env_path)

try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False
    print("❌ ERROR: schedule library not installed")
    print("   Install: pip install schedule")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

# Script paths (relative to project root)
ITF_ENTRIES_SCRIPT = project_root / 'scripts' / 'tennis_ai' / 'itf_entries_intelligence_scraper.py'
ENHANCED_PIPELINE_SCRIPT = project_root / 'scripts' / 'tennis_ai' / 'run_tennis_ai_enhanced.sh'

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    shutdown_requested = True


def run_script(script_path: Path, script_name: str, is_shell: bool = False) -> bool:
    """
    Run a Python script or shell script and log the results
    
    Args:
        script_path: Path to the script to run
        script_name: Human-readable name for logging
        is_shell: If True, run as shell script, else as Python script
        
    Returns:
        True if script executed successfully, False otherwise
    """
    if not script_path.exists():
        logger.error(f"❌ Script not found: {script_path}")
        return False
    
    logger.info(f"🚀 Starting {script_name}...")
    start_time = datetime.now()
    
    try:
        if is_shell:
            # Run shell script
            result = subprocess.run(
                ['bash', str(script_path)],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=7200,  # 2 hour timeout for full pipeline
            )
        else:
            # Run Python script
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout per job
            )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        if result.returncode == 0:
            logger.info(f"✅ {script_name} completed successfully in {duration:.1f}s")
            if result.stdout:
                # Log last 20 lines of output
                lines = result.stdout.strip().split('\n')
                if len(lines) > 20:
                    logger.debug(f"Output (last 20 lines):\n" + '\n'.join(lines[-20:]))
                else:
                    logger.debug(f"Output:\n{result.stdout}")
            return True
        else:
            logger.error(f"❌ {script_name} failed with exit code {result.returncode} after {duration:.1f}s")
            if result.stderr:
                logger.error(f"Error output:\n{result.stderr}")
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 20:
                    logger.debug(f"Output (last 20 lines):\n" + '\n'.join(lines[-20:]))
                else:
                    logger.debug(f"Output:\n{result.stdout}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"❌ {script_name} timed out")
        return False
    except Exception as e:
        logger.error(f"❌ Error running {script_name}: {e}", exc_info=True)
        return False


def job_itf_entries_intelligence():
    """Run ITF Entries Intelligence scraper job"""
    return run_script(ITF_ENTRIES_SCRIPT, "ITF Entries Intelligence Scraper", is_shell=False)


def job_enhanced_pipeline():
    """Run Enhanced Tennis AI Pipeline job"""
    return run_script(ENHANCED_PIPELINE_SCRIPT, "Enhanced Tennis AI Pipeline", is_shell=True)


def check_environment():
    """Check that required environment variables are set"""
    errors = []
    
    # Check Notion token
    if not (os.getenv('NOTION_TOKEN') or os.getenv('NOTION_API_KEY')):
        errors.append("NOTION_TOKEN or NOTION_API_KEY not set")
    
    # Check Notion database ID
    if not (os.getenv('NOTION_TENNIS_PREMATCH_DB_ID') or os.getenv('NOTION_PREMATCH_DB_ID')):
        errors.append("NOTION_TENNIS_PREMATCH_DB_ID or NOTION_PREMATCH_DB_ID not set")
    
    # Check OpenAI API key (required for analyzer)
    if not os.getenv('OPENAI_API_KEY'):
        errors.append("OPENAI_API_KEY not set (required for Enhanced Pipeline)")
    
    if errors:
        logger.error("❌ Missing required environment variables:")
        for error in errors:
            logger.error(f"   - {error}")
        logger.error("\n💡 Set these via: fly secrets set KEY=value")
        return False
    
    logger.info("✅ Environment variables validated")
    return True


def main():
    """Main scheduler loop"""
    global shutdown_requested
    
    logger.info("=" * 70)
    logger.info("🕐 ITF TENNIS ENHANCED PIPELINE SCHEDULER")
    logger.info("=" * 70)
    
    # Check environment
    if not check_environment():
        logger.error("❌ Environment check failed, exiting")
        sys.exit(1)
    
    # Verify scripts exist
    scripts_to_check = [
        (ITF_ENTRIES_SCRIPT, "ITF Entries Intelligence Scraper"),
        (ENHANCED_PIPELINE_SCRIPT, "Enhanced Tennis AI Pipeline"),
    ]
    
    for script_path, name in scripts_to_check:
        if not script_path.exists():
            logger.error(f"❌ Script not found: {script_path}")
            logger.error(f"   This is required for: {name}")
            sys.exit(1)
    
    logger.info("✅ All scripts found")
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Schedule jobs
    # Note: schedule library uses local time, but for Fly.io we want UTC
    # CET is UTC+1 (winter) or UTC+2 (summer)
    # 08:00 CET = 07:00 UTC (winter) or 06:00 UTC (summer)
    # Using 07:00 UTC as compromise (will be 08:00 CET in winter, 09:00 CET in summer)
    # For exact 08:00 CET, use 07:00 UTC in winter, 06:00 UTC in summer
    
    # ITF Entries Intelligence: 08:00 CET (07:00 UTC)
    schedule.every().day.at("07:00").do(job_itf_entries_intelligence)
    
    # Enhanced Pipeline: 08:15 CET (07:15 UTC) - 15 min after intelligence update
    schedule.every().day.at("07:15").do(job_enhanced_pipeline)
    
    logger.info("📅 Scheduled jobs:")
    logger.info("   - ITF Entries Intelligence: 07:00 UTC (08:00 CET winter, 09:00 CET summer)")
    logger.info("   - Enhanced Tennis AI Pipeline: 07:15 UTC (08:15 CET winter, 09:15 CET summer)")
    logger.info("")
    logger.info("🔄 Scheduler running... (Press Ctrl+C to stop)")
    logger.info("=" * 70)
    
    # Main loop
    last_log_time = time.time()
    while not shutdown_requested:
        try:
            # Run pending jobs
            schedule.run_pending()
            
            # Log status every 10 minutes
            current_time = time.time()
            if current_time - last_log_time >= 600:  # 10 minutes
                next_run = schedule.next_run()
                if next_run:
                    logger.info(f"⏰ Next job scheduled: {next_run.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                last_log_time = current_time
            
            # Sleep for 1 minute
            time.sleep(60)
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
            shutdown_requested = True
        except Exception as e:
            logger.error(f"❌ Error in scheduler loop: {e}", exc_info=True)
            # Continue running even if there's an error
            time.sleep(60)
    
    logger.info("🛑 Scheduler stopped")


if __name__ == "__main__":
    main()

