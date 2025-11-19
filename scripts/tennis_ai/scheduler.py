#!/usr/bin/env python3
"""
🕐 ITF TENNIS PIPELINE SCHEDULER
=================================

Long-running scheduler that executes three cron jobs on schedule:
1. ITF Scraper: 06:00 & 18:00 UTC (2x daily)
2. Player Card Linker: 06:30 UTC (1x daily, after scraper)
3. GPT Analyzer: 07:00 & 19:00 UTC (2x daily, after linking)

Uses Python's schedule library to manage timing.
Runs continuously, checking every minute for scheduled tasks.

Usage:
    python scripts/tennis_ai/scheduler.py
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
SCRAPER_SCRIPT = project_root / 'run_itf_scraper.py'
LINKER_SCRIPT = project_root / 'scripts' / 'tennis_ai' / 'link_existing_matches.py'
ANALYZER_SCRIPT = project_root / 'scripts' / 'tennis_ai' / 'analyze_filtered_matches.py'

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    shutdown_requested = True


def run_script(script_path: Path, script_name: str) -> bool:
    """
    Run a Python script and log the results
    
    Args:
        script_path: Path to the script to run
        script_name: Human-readable name for logging
        
    Returns:
        True if script executed successfully, False otherwise
    """
    if not script_path.exists():
        logger.error(f"❌ Script not found: {script_path}")
        return False
    
    logger.info(f"🚀 Starting {script_name}...")
    start_time = datetime.now()
    
    try:
        # Run script in subprocess
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
                logger.debug(f"Output:\n{result.stdout}")
            return True
        else:
            logger.error(f"❌ {script_name} failed with exit code {result.returncode} after {duration:.1f}s")
            if result.stderr:
                logger.error(f"Error output:\n{result.stderr}")
            if result.stdout:
                logger.debug(f"Output:\n{result.stdout}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"❌ {script_name} timed out after 1 hour")
        return False
    except Exception as e:
        logger.error(f"❌ Error running {script_name}: {e}", exc_info=True)
        return False


def job_itf_scraper():
    """Run ITF scraper job"""
    return run_script(SCRAPER_SCRIPT, "ITF Scraper")


def job_player_card_linker():
    """Run player card linker job"""
    return run_script(LINKER_SCRIPT, "Player Card Linker")


def job_gpt_analyzer():
    """Run GPT analyzer job"""
    return run_script(ANALYZER_SCRIPT, "GPT Analyzer")


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
        errors.append("OPENAI_API_KEY not set (required for GPT Analyzer)")
    
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
    
    logger.info("=" * 60)
    logger.info("🕐 ITF TENNIS PIPELINE SCHEDULER")
    logger.info("=" * 60)
    
    # Check environment
    if not check_environment():
        logger.error("❌ Environment check failed, exiting")
        sys.exit(1)
    
    # Verify scripts exist
    scripts_to_check = [
        (SCRAPER_SCRIPT, "ITF Scraper"),
        (LINKER_SCRIPT, "Player Card Linker"),
        (ANALYZER_SCRIPT, "GPT Analyzer"),
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
    # ITF Scraper: 06:00 & 18:00 UTC (2x daily)
    schedule.every().day.at("06:00").do(job_itf_scraper)
    schedule.every().day.at("18:00").do(job_itf_scraper)
    
    # Player Card Linker: 06:30 UTC (1x daily, after scraper)
    schedule.every().day.at("06:30").do(job_player_card_linker)
    
    # GPT Analyzer: 07:00 & 19:00 UTC (2x daily, after linking)
    schedule.every().day.at("07:00").do(job_gpt_analyzer)
    schedule.every().day.at("19:00").do(job_gpt_analyzer)
    
    logger.info("📅 Scheduled jobs:")
    logger.info("   - ITF Scraper: 06:00 & 18:00 UTC (2x daily)")
    logger.info("   - Player Card Linker: 06:30 UTC (1x daily)")
    logger.info("   - GPT Analyzer: 07:00 & 19:00 UTC (2x daily)")
    logger.info("")
    logger.info("🔄 Scheduler running... (Press Ctrl+C to stop)")
    logger.info("=" * 60)
    
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

