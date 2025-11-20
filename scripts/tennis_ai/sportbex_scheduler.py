#!/usr/bin/env python3
"""
Sportbex Scheduler
==================

Python scheduler for daily candidate screening.
Runs sportbex_daily_candidates.py daily at 08:00 EET.

Alternative to n8n workflow - pure Python solution.
"""

import schedule
import time
import logging
import subprocess
import sys
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_daily_candidates():
    """Run the daily candidates pipeline"""
    logger.info("🕐 Scheduled run triggered at 08:00 EET")
    
    # Get script path
    script_path = Path(__file__).parent / 'sportbex_daily_candidates.py'
    
    if not script_path.exists():
        logger.error(f"❌ Script not found: {script_path}")
        return
    
    try:
        # Run the script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            logger.info("✅ Daily candidates pipeline completed successfully")
            logger.info(result.stdout)
        else:
            logger.error(f"❌ Pipeline failed with return code {result.returncode}")
            logger.error(result.stderr)
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Pipeline timed out after 5 minutes")
    except Exception as e:
        logger.error(f"❌ Error running pipeline: {e}")


def main():
    """Main scheduler loop"""
    logger.info("🚀 Starting Sportbex Scheduler")
    logger.info("📅 Schedule: Daily at 08:00 EET")
    logger.info("💡 Press Ctrl+C to stop")
    
    # Schedule daily run at 08:00 EET (06:00 UTC, adjust as needed)
    # Note: Adjust time based on your timezone
    schedule.every().day.at("08:00").do(run_daily_candidates)
    
    # For testing, you can also schedule a run in 1 minute
    # schedule.every(1).minutes.do(run_daily_candidates)
    
    logger.info("⏰ Scheduler started. Waiting for next run...")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("\n👋 Scheduler stopped by user")


if __name__ == "__main__":
    main()

