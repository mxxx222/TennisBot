#!/usr/bin/env python3
"""
⏰ TENNISEXPLORER SCHEDULER
===========================

Job scheduler for TennisExplorer scraper tasks.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Try to import APScheduler
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.cron import CronTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ APScheduler not available, using schedule library fallback")

logger = logging.getLogger(__name__)


class TennisExplorerScheduler:
    """
    Scheduler for TennisExplorer tasks
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize scheduler
        
        Args:
            config: Configuration dict
        """
        self.config = config or {}
        self.scheduler = None
        self.jobs = {}
        
        if APSCHEDULER_AVAILABLE:
            self.scheduler = AsyncIOScheduler()
            logger.info("✅ APScheduler initialized")
        else:
            logger.warning("⚠️ Using schedule library fallback")
        
        logger.info("⏰ TennisExplorer Scheduler initialized")
    
    def start(self):
        """Start scheduler"""
        if self.scheduler:
            self.scheduler.start()
            logger.info("✅ Scheduler started")
    
    def stop(self):
        """Stop scheduler"""
        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("✅ Scheduler stopped")
    
    def add_live_matches_job(self, func, interval_seconds: int = 30):
        """Add live matches scraping job"""
        if not self.scheduler:
            return
        
        job = self.scheduler.add_job(
            func,
            trigger=IntervalTrigger(seconds=interval_seconds),
            id='live_matches',
            name='Scrape Live Matches',
            replace_existing=True
        )
        self.jobs['live_matches'] = job
        logger.info(f"✅ Added live matches job (every {interval_seconds}s)")
    
    def add_tournament_calendar_job(self, func, interval_hours: int = 4):
        """Add tournament calendar scraping job"""
        if not self.scheduler:
            return
        
        job = self.scheduler.add_job(
            func,
            trigger=IntervalTrigger(hours=interval_hours),
            id='tournament_calendar',
            name='Scrape Tournament Calendar',
            replace_existing=True
        )
        self.jobs['tournament_calendar'] = job
        logger.info(f"✅ Added tournament calendar job (every {interval_hours}h)")
    
    def add_rankings_job(self, func, hour: int = 6):
        """Add rankings scraping job (daily)"""
        if not self.scheduler:
            return
        
        job = self.scheduler.add_job(
            func,
            trigger=CronTrigger(hour=hour, minute=0),
            id='rankings',
            name='Scrape Rankings',
            replace_existing=True
        )
        self.jobs['rankings'] = job
        logger.info(f"✅ Added rankings job (daily at {hour}:00)")
    
    def add_roi_detection_job(self, func, interval_seconds: int = 30):
        """Add ROI detection job"""
        if not self.scheduler:
            return
        
        job = self.scheduler.add_job(
            func,
            trigger=IntervalTrigger(seconds=interval_seconds),
            id='roi_detection',
            name='ROI Detection',
            replace_existing=True
        )
        self.jobs['roi_detection'] = job
        logger.info(f"✅ Added ROI detection job (every {interval_seconds}s)")
    
    def add_weather_update_job(self, func, interval_hours: int = 2):
        """Add weather update job"""
        if not self.scheduler:
            return
        
        job = self.scheduler.add_job(
            func,
            trigger=IntervalTrigger(hours=interval_hours),
            id='weather_update',
            name='Update Weather',
            replace_existing=True
        )
        self.jobs['weather_update'] = job
        logger.info(f"✅ Added weather update job (every {interval_hours}h)")
    
    def add_weekly_report_job(self, func, day_of_week: int = 0, hour: int = 8):
        """
        Add weekly report job (runs every Monday)
        
        Args:
            func: Function to call
            day_of_week: Day of week (0=Monday, 6=Sunday)
            hour: Hour to run (0-23)
        """
        if not self.scheduler:
            return
        
        try:
            from apscheduler.triggers.cron import CronTrigger
            job = self.scheduler.add_job(
                func,
                trigger=CronTrigger(day_of_week=day_of_week, hour=hour, minute=0),
                id='weekly_report',
                name='Generate Weekly Report',
                replace_existing=True
            )
            self.jobs['weekly_report'] = job
            logger.info(f"✅ Added weekly report job (Monday at {hour}:00)")
        except ImportError:
            logger.warning("⚠️ CronTrigger not available, weekly report job not added")

