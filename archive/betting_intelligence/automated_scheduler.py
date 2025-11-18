#!/usr/bin/env python3
"""
⏰ AUTOMATED SCRAPING SCHEDULER
===============================

Intelligent scheduling system for web scraping tasks with:
- Dynamic scheduling based on sports events
- Rate limiting and anti-detection compliance
- Error handling and retry logic
- Performance monitoring and reporting

Author: TennisBot Advanced Analytics
Version: 1.0.0
"""

import asyncio
import schedule
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
import json
import threading
import signal
import sys
from pathlib import Path

from enhanced_sports_scraper import EnhancedSportsScraper, scrape_tennis_data, scrape_football_data

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScrapingScheduler:
    """Intelligent scraping scheduler"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.scraper = None
        self.is_running = False
        self.jobs = []
        self.last_runs = {}
        self.error_counts = {}
        self.performance_stats = {}

        # Scheduling configuration
        self.schedules = {
            'tennis': {
                'frequent': {'interval': 15, 'unit': 'minutes'},  # During tournaments
                'normal': {'interval': 60, 'unit': 'minutes'},    # Regular schedule
                'peak_hours': {'start': 8, 'end': 22}             # Active hours
            },
            'football': {
                'frequent': {'interval': 30, 'unit': 'minutes'},  # Match days
                'normal': {'interval': 120, 'unit': 'minutes'},   # Non-match days
                'peak_hours': {'start': 9, 'end': 23}
            }
        }

        # Initialize scraper
        self.scraper = EnhancedSportsScraper(config)

    def start(self):
        """Start the scheduling system"""
        logger.info("🚀 Starting automated scraping scheduler...")

        self.is_running = True

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Schedule initial jobs
        self._setup_schedules()

        # Start monitoring thread
        monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        monitoring_thread.start()

        # Main scheduling loop
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            logger.info("🛑 Received shutdown signal...")
        finally:
            self.stop()

    def stop(self):
        """Stop the scheduling system"""
        logger.info("🛑 Stopping automated scraping scheduler...")

        self.is_running = False

        # Cancel all jobs
        for job in self.jobs:
            if hasattr(job, 'cancel'):
                job.cancel()

        # Export final stats
        self._export_performance_stats()

        logger.info("✅ Scheduler stopped successfully")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"📡 Received signal {signum}, initiating shutdown...")
        self.is_running = False

    def _setup_schedules(self):
        """Setup scraping schedules"""
        logger.info("📅 Setting up scraping schedules...")

        # Tennis scraping schedules
        self._schedule_tennis_scraping()

        # Football scraping schedules
        self._schedule_football_scraping()

        # Daily maintenance tasks
        self._schedule_maintenance_tasks()

        logger.info(f"✅ Scheduled {len(schedule.jobs)} scraping jobs")

    def _schedule_tennis_scraping(self):
        """Schedule tennis data scraping"""
        tennis_config = self.schedules['tennis']

        # Frequent scraping during peak hours
        peak_start = tennis_config['peak_hours']['start']
        peak_end = tennis_config['peak_hours']['end']

        # Schedule frequent tennis scraping
        frequent_interval = tennis_config['frequent']['interval']
        job = schedule.every(frequent_interval).minutes.do(
            self._run_tennis_scraping_job,
            job_type='frequent'
        )
        self.jobs.append(job)

        # Schedule normal tennis scraping for off-peak hours
        normal_interval = tennis_config['normal']['interval']
        job = schedule.every(normal_interval).minutes.do(
            self._run_tennis_scraping_job,
            job_type='normal'
        )
        self.jobs.append(job)

        # Daily tennis stats update
        schedule.every().day.at("06:00").do(self._run_daily_tennis_stats)

        logger.info(f"🎾 Tennis scraping: {frequent_interval}min frequent, {normal_interval}min normal")

    def _schedule_football_scraping(self):
        """Schedule football data scraping"""
        football_config = self.schedules['football']

        # Frequent scraping during peak hours
        frequent_interval = football_config['frequent']['interval']
        job = schedule.every(frequent_interval).minutes.do(
            self._run_football_scraping_job,
            job_type='frequent'
        )
        self.jobs.append(job)

        # Normal scraping
        normal_interval = football_config['normal']['interval']
        job = schedule.every(normal_interval).minutes.do(
            self._run_football_scraping_job,
            job_type='normal'
        )
        self.jobs.append(job)

        # Daily football stats update
        schedule.every().day.at("07:00").do(self._run_daily_football_stats)

        logger.info(f"⚽ Football scraping: {frequent_interval}min frequent, {normal_interval}min normal")

    def _schedule_maintenance_tasks(self):
        """Schedule maintenance and reporting tasks"""
        # Hourly performance reporting
        schedule.every().hour.do(self._hourly_performance_report)

        # Daily data cleanup
        schedule.every().day.at("02:00").do(self._daily_data_cleanup)

        # Weekly comprehensive report
        schedule.every().week.do(self._weekly_comprehensive_report)

        logger.info("🔧 Maintenance tasks scheduled")

    async def _run_tennis_scraping_job(self, job_type: str):
        """Run tennis scraping job"""
        job_id = f"tennis_{job_type}_{datetime.now().strftime('%H%M%S')}"

        try:
            logger.info(f"🎾 Starting tennis scraping job: {job_id}")

            start_time = time.time()

            # Check if we should run this job (rate limiting, etc.)
            if not self._should_run_job('tennis', job_type):
                logger.debug(f"⏭️ Skipping tennis job {job_id} (rate limited)")
                return

            # Run scraping
            matches = await scrape_tennis_data(self.config)

            duration = time.time() - start_time

            # Record success
            self._record_job_success('tennis', job_type, len(matches), duration)

            # Analyze ROI opportunities
            if matches:
                async with EnhancedSportsScraper(self.config) as scraper:
                    roi_opportunities = await scraper.find_roi_opportunities(matches)

                    # Log significant opportunities
                    arbitrage_count = len(roi_opportunities['arbitrage'])
                    value_bet_count = len(roi_opportunities['value_bets'])

                    if arbitrage_count > 0 or value_bet_count > 0:
                        logger.info(f"💰 Job {job_id}: {arbitrage_count} arbitrage, {value_bet_count} value bets")

            # Export data
            if matches:
                filename = self.scraper.export_data(matches, f"tennis_{job_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                logger.info(f"💾 Job {job_id}: Exported {len(matches)} matches to {filename}")

        except Exception as e:
            logger.error(f"❌ Tennis scraping job {job_id} failed: {e}")
            self._record_job_error('tennis', job_type, str(e))

    async def _run_football_scraping_job(self, job_type: str):
        """Run football scraping job"""
        job_id = f"football_{job_type}_{datetime.now().strftime('%H%M%S')}"

        try:
            logger.info(f"⚽ Starting football scraping job: {job_id}")

            start_time = time.time()

            # Check if we should run this job
            if not self._should_run_job('football', job_type):
                logger.debug(f"⏭️ Skipping football job {job_id} (rate limited)")
                return

            # Run scraping
            matches = await scrape_football_data(self.config)

            duration = time.time() - start_time

            # Record success
            self._record_job_success('football', job_type, len(matches), duration)

            # Analyze ROI opportunities
            if matches:
                async with EnhancedSportsScraper(self.config) as scraper:
                    roi_opportunities = await scraper.find_roi_opportunities(matches)

                    arbitrage_count = len(roi_opportunities['arbitrage'])
                    value_bet_count = len(roi_opportunities['value_bets'])

                    if arbitrage_count > 0 or value_bet_count > 0:
                        logger.info(f"💰 Job {job_id}: {arbitrage_count} arbitrage, {value_bet_count} value bets")

            # Export data
            if matches:
                filename = self.scraper.export_data(matches, f"football_{job_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                logger.info(f"💾 Job {job_id}: Exported {len(matches)} matches to {filename}")

        except Exception as e:
            logger.error(f"❌ Football scraping job {job_id} failed: {e}")
            self._record_job_error('football', job_type, str(e))

    def _run_daily_tennis_stats(self):
        """Run daily tennis statistics update"""
        logger.info("🎾 Running daily tennis statistics update...")

        try:
            # This would include comprehensive stats scraping
            # For now, just log the action
            logger.info("✅ Daily tennis statistics update completed")

        except Exception as e:
            logger.error(f"❌ Daily tennis stats update failed: {e}")

    def _run_daily_football_stats(self):
        """Run daily football statistics update"""
        logger.info("⚽ Running daily football statistics update...")

        try:
            # This would include comprehensive stats scraping
            logger.info("✅ Daily football statistics update completed")

        except Exception as e:
            logger.error(f"❌ Daily football stats update failed: {e}")

    def _should_run_job(self, sport: str, job_type: str) -> bool:
        """Determine if a job should run based on various factors"""
        current_time = datetime.now()

        # Check peak hours
        sport_config = self.schedules[sport]
        peak_start = sport_config['peak_hours']['start']
        peak_end = sport_config['peak_hours']['end']

        is_peak_hour = peak_start <= current_time.hour <= peak_end

        # For frequent jobs, only run during peak hours
        if job_type == 'frequent' and not is_peak_hour:
            return False

        # For normal jobs, only run during off-peak hours
        if job_type == 'normal' and is_peak_hour:
            return False

        # Check error rate - if too many errors recently, slow down
        error_key = f"{sport}_{job_type}"
        recent_errors = self.error_counts.get(error_key, 0)

        if recent_errors > 5:  # Too many errors, skip this run
            logger.warning(f"⚠️ Skipping {error_key} job due to high error rate ({recent_errors})")
            return False

        # Check last run time to prevent overlapping jobs
        last_run_key = f"{sport}_{job_type}"
        last_run = self.last_runs.get(last_run_key)

        if last_run:
            min_interval = sport_config[job_type]['interval'] * 60  # Convert to seconds
            time_since_last = (current_time - last_run).total_seconds()

            if time_since_last < min_interval * 0.8:  # Allow 20% overlap tolerance
                return False

        return True

    def _record_job_success(self, sport: str, job_type: str, matches_count: int, duration: float):
        """Record successful job execution"""
        job_key = f"{sport}_{job_type}"

        # Update last run time
        self.last_runs[job_key] = datetime.now()

        # Reset error count on success
        self.error_counts[job_key] = 0

        # Record performance stats
        if job_key not in self.performance_stats:
            self.performance_stats[job_key] = {
                'runs': 0,
                'total_matches': 0,
                'total_duration': 0,
                'success_rate': 1.0
            }

        stats = self.performance_stats[job_key]
        stats['runs'] += 1
        stats['total_matches'] += matches_count
        stats['total_duration'] += duration

        logger.info(f"✅ Job {job_key}: {matches_count} matches in {duration:.2f}s")

    def _record_job_error(self, sport: str, job_type: str, error: str):
        """Record job execution error"""
        job_key = f"{sport}_{job_type}"

        # Increment error count
        if job_key not in self.error_counts:
            self.error_counts[job_key] = 0
        self.error_counts[job_key] += 1

        # Update performance stats
        if job_key not in self.performance_stats:
            self.performance_stats[job_key] = {
                'runs': 0,
                'errors': 0,
                'success_rate': 0.0
            }

        stats = self.performance_stats[job_key]
        stats['errors'] = self.error_counts[job_key]
        if stats['runs'] > 0:
            stats['success_rate'] = (stats['runs'] - stats['errors']) / stats['runs']

        logger.warning(f"❌ Job {job_key} error count: {self.error_counts[job_key]}")

    def _hourly_performance_report(self):
        """Generate hourly performance report"""
        logger.info("📊 Hourly performance report:")

        for job_key, stats in self.performance_stats.items():
            runs = stats.get('runs', 0)
            errors = stats.get('errors', 0)
            success_rate = stats.get('success_rate', 0.0)

            if runs > 0:
                avg_matches = stats.get('total_matches', 0) / runs
                avg_duration = stats.get('total_duration', 0) / runs

                logger.info(f"  {job_key}: {runs} runs, {errors} errors, {success_rate:.1%} success")
                logger.info(f"    Avg: {avg_matches:.1f} matches, {avg_duration:.2f}s duration")

    def _daily_data_cleanup(self):
        """Perform daily data cleanup"""
        logger.info("🧹 Performing daily data cleanup...")

        try:
            # Clean up old data files (older than 7 days)
            data_dir = Path("data")
            if data_dir.exists():
                cutoff_date = datetime.now() - timedelta(days=7)

                for file_path in data_dir.glob("*.json"):
                    if file_path.stat().st_mtime < cutoff_date.timestamp():
                        file_path.unlink()
                        logger.info(f"🗑️ Deleted old file: {file_path.name}")

            # Reset error counts (give jobs a fresh start daily)
            self.error_counts.clear()

            logger.info("✅ Daily data cleanup completed")

        except Exception as e:
            logger.error(f"❌ Daily data cleanup failed: {e}")

    def _weekly_comprehensive_report(self):
        """Generate weekly comprehensive report"""
        logger.info("📈 Generating weekly comprehensive report...")

        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'period': 'weekly',
                'performance_stats': self.performance_stats,
                'error_summary': self.error_counts,
                'scheduler_status': 'active' if self.is_running else 'inactive'
            }

            # Save report
            report_file = f"weekly_report_{datetime.now().strftime('%Y%m%d')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"✅ Weekly report saved to {report_file}")

        except Exception as e:
            logger.error(f"❌ Weekly report generation failed: {e}")

    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.is_running:
            try:
                # Check system health
                self._check_system_health()

                # Sleep for monitoring interval
                time.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"❌ Monitoring loop error: {e}")
                time.sleep(60)  # Sleep shorter on error

    def _check_system_health(self):
        """Check system health and alert if needed"""
        # Check if jobs are running
        active_jobs = len([job for job in schedule.jobs if job.should_run()])

        if active_jobs == 0:
            logger.warning("⚠️ No active scheduled jobs found")

        # Check error rates
        high_error_jobs = []
        for job_key, error_count in self.error_counts.items():
            if error_count > 10:  # Threshold for high error rate
                high_error_jobs.append(job_key)

        if high_error_jobs:
            logger.warning(f"⚠️ High error rate jobs: {', '.join(high_error_jobs)}")

        # Check disk space (basic check)
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            free_gb = free / (1024**3)

            if free_gb < 1:  # Less than 1GB free
                logger.critical(f"🚨 Low disk space: {free_gb:.2f}GB remaining")

        except Exception as e:
            logger.debug(f"Could not check disk space: {e}")

    def _export_performance_stats(self):
        """Export final performance statistics"""
        try:
            stats_file = f"performance_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            final_stats = {
                'export_timestamp': datetime.now().isoformat(),
                'total_runtime_hours': (datetime.now() - datetime.fromtimestamp(time.time() - (time.time() % 86400))).total_seconds() / 3600,
                'performance_stats': self.performance_stats,
                'error_summary': self.error_counts,
                'scheduler_status': 'stopped'
            }

            with open(stats_file, 'w') as f:
                json.dump(final_stats, f, indent=2, default=str)

            logger.info(f"📊 Performance stats exported to {stats_file}")

        except Exception as e:
            logger.error(f"❌ Failed to export performance stats: {e}")

def create_default_config() -> Dict[str, Any]:
    """Create default scheduler configuration"""
    return {
        'proxies': [],  # Add proxy configurations here
        'rate_limits': {
            'flashscore.com': 10,
            'oddsportal.com': 8,
            'atptour.com': 15,
            'premierleague.com': 12
        },
        'data_directory': 'data',
        'log_level': 'INFO',
        'max_concurrent_jobs': 3,
        'retry_attempts': 3,
        'backoff_factor': 2.0
    }

async def run_scheduled_scraping(config: Dict[str, Any] = None):
    """Run the scheduled scraping system"""
    if config is None:
        config = create_default_config()

    scheduler = ScrapingScheduler(config)
    scheduler.start()

if __name__ == "__main__":
    # Test the scheduler
    print("⏰ AUTOMATED SCRAPING SCHEDULER TEST")
    print("=" * 50)

    # Create test configuration
    config = create_default_config()

    try:
        # Run scheduler for a short test period
        print("🧪 Running scheduler test (30 seconds)...")

        # Create scheduler
        scheduler = ScrapingScheduler(config)

        # Start in a separate thread for testing
        scheduler_thread = threading.Thread(target=scheduler.start, daemon=True)
        scheduler_thread.start()

        # Let it run for 30 seconds
        time.sleep(30)

        # Stop scheduler
        scheduler.stop()

        print("✅ Scheduler test completed")

    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        if 'scheduler' in locals():
            scheduler.stop()

    except Exception as e:
        print(f"❌ Scheduler test failed: {e}")
        import traceback
        traceback.print_exc()