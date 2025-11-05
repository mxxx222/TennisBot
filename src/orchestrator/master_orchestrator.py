#!/usr/bin/env python3
"""
🚀 COMPREHENSIVE SCRAPING ORCHESTRATOR
=====================================

Master orchestrator for comprehensive sports data scraping
Coordinates all scraping modules for maximum data coverage

Features:
- Multi-source data aggregation
- Intelligent scheduling and rate limiting
- Data quality validation
- Real-time monitoring and alerts
- Automated data pipeline management
- Advanced error handling and recovery
- Performance optimization

Author: Master Data Orchestrator
Version: 6.0.0
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import queue
from pathlib import Path
import os
import sqlite3
from contextlib import asynccontextmanager
import pandas as pd
import numpy as np
from collections import defaultdict, deque
import schedule

# Import our custom scrapers
from advanced_tennis_scraper import AdvancedTennisScraper
from multi_sport_scraper import MultiSportScraper
from data_engine import AdvancedDataProcessor

@dataclass
class ScrapingJob:
    job_id: str
    source: str
    sport: str
    priority: int
    frequency: str  # 'realtime', 'hourly', 'daily'
    last_run: Optional[datetime]
    next_run: datetime
    data_type: str
    target_count: int
    success_rate: float
    enabled: bool

@dataclass
class ScrapingResult:
    job_id: str
    source: str
    sport: str
    records_count: int
    execution_time: float
    success: bool
    error_message: Optional[str]
    data_quality_score: float
    timestamp: datetime

class MasterScrapingOrchestrator:
    """Master orchestrator for comprehensive sports data scraping"""
    
    def __init__(self):
        self.setup_logging()
        self.setup_database()
        self.setup_scrapers()
        self.setup_scheduling()
        
        # Job management
        self.jobs = {}
        self.active_jobs = set()
        self.job_queue = queue.PriorityQueue()
        self.results_history = deque(maxlen=1000)
        
        # Rate limiting and throttling
        self.rate_limiters = defaultdict(lambda: {'requests': 0, 'reset_time': time.time()})
        self.global_rate_limit = 100  # requests per minute
        
        # Performance monitoring
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'data_quality_average': 0.0,
            'uptime_start': datetime.now()
        }
        
        # Data storage
        self.data_cache = {}
        self.quality_reports = []
        
        # Control flags
        self.running = False
        self.paused = False
        
    def setup_logging(self):
        """Setup comprehensive logging system"""
        # Create logs directory
        Path("logs").mkdir(exist_ok=True)
        
        # Main logger
        self.logger = logging.getLogger('orchestrator')
        self.logger.setLevel(logging.INFO)
        
        # File handler with rotation
        file_handler = logging.FileHandler('logs/orchestrator.log')
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Separate loggers for different components
        self.performance_logger = logging.getLogger('performance')
        self.error_logger = logging.getLogger('errors')
    
    def setup_database(self):
        """Setup SQLite database for job management and results"""
        db_path = Path("data/orchestrator.db")
        db_path.parent.mkdir(exist_ok=True)
        
        self.db_connection = sqlite3.connect(str(db_path), check_same_thread=False)
        self.db_lock = threading.Lock()
        
        # Create tables
        cursor = self.db_connection.cursor()
        
        # Jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraping_jobs (
                job_id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                sport TEXT NOT NULL,
                priority INTEGER NOT NULL,
                frequency TEXT NOT NULL,
                last_run TIMESTAMP,
                next_run TIMESTAMP NOT NULL,
                data_type TEXT NOT NULL,
                target_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraping_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                source TEXT NOT NULL,
                sport TEXT NOT NULL,
                records_count INTEGER DEFAULT 0,
                execution_time REAL DEFAULT 0.0,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                data_quality_score REAL DEFAULT 0.0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Performance metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.db_connection.commit()
        self.logger.info("Database setup completed")
    
    def setup_scrapers(self):
        """Initialize all scraping modules"""
        self.scrapers = {
            'tennis_advanced': AdvancedTennisScraper(),
            'multi_sport': MultiSportScraper(),
            'data_processor': AdvancedDataProcessor()
        }
        
        self.logger.info(f"Initialized {len(self.scrapers)} scraping modules")
    
    def setup_scheduling(self):
        """Setup job scheduling system"""
        self.scheduler = schedule
        
        # Define default scraping jobs
        default_jobs = [
            ScrapingJob(
                job_id='tennis_live_scores',
                source='flashscore',
                sport='tennis',
                priority=1,
                frequency='realtime',
                last_run=None,
                next_run=datetime.now(),
                data_type='live_scores',
                target_count=50,
                success_rate=0.0,
                enabled=True
            ),
            ScrapingJob(
                job_id='tennis_rankings',
                source='atp',
                sport='tennis',
                priority=2,
                frequency='daily',
                last_run=None,
                next_run=datetime.now(),
                data_type='rankings',
                target_count=100,
                success_rate=0.0,
                enabled=True
            ),
            ScrapingJob(
                job_id='football_premier_league',
                source='bbc',
                sport='football',
                priority=2,
                frequency='hourly',
                last_run=None,
                next_run=datetime.now(),
                data_type='league_table',
                target_count=20,
                success_rate=0.0,
                enabled=True
            ),
            ScrapingJob(
                job_id='basketball_nba',
                source='espn',
                sport='basketball',
                priority=3,
                frequency='hourly',
                last_run=None,
                next_run=datetime.now(),
                data_type='standings',
                target_count=30,
                success_rate=0.0,
                enabled=True
            ),
            ScrapingJob(
                job_id='betting_odds_comprehensive',
                source='oddsportal',
                sport='multi',
                priority=1,
                frequency='realtime',
                last_run=None,
                next_run=datetime.now(),
                data_type='odds',
                target_count=200,
                success_rate=0.0,
                enabled=True
            )
        ]
        
        # Add jobs to system
        for job in default_jobs:
            self.add_job(job)
    
    def add_job(self, job: ScrapingJob):
        """Add a new scraping job"""
        self.jobs[job.job_id] = job
        
        # Store in database
        with self.db_lock:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO scraping_jobs 
                (job_id, source, sport, priority, frequency, last_run, next_run, 
                 data_type, target_count, success_rate, enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job.job_id, job.source, job.sport, job.priority, job.frequency,
                job.last_run, job.next_run, job.data_type, job.target_count,
                job.success_rate, job.enabled
            ))
            self.db_connection.commit()
        
        self.logger.info(f"Added job: {job.job_id}")
    
    def remove_job(self, job_id: str):
        """Remove a scraping job"""
        if job_id in self.jobs:
            del self.jobs[job_id]
            
            with self.db_lock:
                cursor = self.db_connection.cursor()
                cursor.execute('DELETE FROM scraping_jobs WHERE job_id = ?', (job_id,))
                self.db_connection.commit()
            
            self.logger.info(f"Removed job: {job_id}")
    
    def enable_job(self, job_id: str):
        """Enable a scraping job"""
        if job_id in self.jobs:
            self.jobs[job_id].enabled = True
            self._update_job_in_db(self.jobs[job_id])
            self.logger.info(f"Enabled job: {job_id}")
    
    def disable_job(self, job_id: str):
        """Disable a scraping job"""
        if job_id in self.jobs:
            self.jobs[job_id].enabled = False
            self._update_job_in_db(self.jobs[job_id])
            self.logger.info(f"Disabled job: {job_id}")
    
    def _update_job_in_db(self, job: ScrapingJob):
        """Update job in database"""
        with self.db_lock:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                UPDATE scraping_jobs SET 
                last_run = ?, next_run = ?, success_rate = ?, enabled = ?
                WHERE job_id = ?
            ''', (job.last_run, job.next_run, job.success_rate, job.enabled, job.job_id))
            self.db_connection.commit()
    
    async def execute_job(self, job: ScrapingJob) -> ScrapingResult:
        """Execute a single scraping job"""
        start_time = time.time()
        self.logger.info(f"Executing job: {job.job_id}")
        
        try:
            # Check rate limits
            if not self._check_rate_limit(job.source):
                raise Exception(f"Rate limit exceeded for {job.source}")
            
            # Execute scraping based on job type
            data = await self._execute_job_by_type(job)
            
            # Process and validate data
            processed_data = await self._process_scraped_data(data, job)
            
            # Calculate data quality score
            quality_score = self._calculate_data_quality_score(processed_data, job)
            
            # Store data
            await self._store_scraped_data(processed_data, job)
            
            execution_time = time.time() - start_time
            
            result = ScrapingResult(
                job_id=job.job_id,
                source=job.source,
                sport=job.sport,
                records_count=len(processed_data) if isinstance(processed_data, list) else 1,
                execution_time=execution_time,
                success=True,
                error_message=None,
                data_quality_score=quality_score,
                timestamp=datetime.now()
            )
            
            # Update job statistics
            self._update_job_success_rate(job, True)
            
            self.logger.info(f"Job completed successfully: {job.job_id} ({result.records_count} records)")
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_message = str(e)
            
            result = ScrapingResult(
                job_id=job.job_id,
                source=job.source,
                sport=job.sport,
                records_count=0,
                execution_time=execution_time,
                success=False,
                error_message=error_message,
                data_quality_score=0.0,
                timestamp=datetime.now()
            )
            
            # Update job statistics
            self._update_job_success_rate(job, False)
            
            self.error_logger.error(f"Job failed: {job.job_id} - {error_message}")
        
        # Store result in database
        self._store_result(result)
        
        # Update performance metrics
        self._update_performance_metrics(result)
        
        return result
    
    async def _execute_job_by_type(self, job: ScrapingJob) -> Any:
        """Execute job based on its type and source"""
        if job.sport == 'tennis':
            return await self._execute_tennis_job(job)
        elif job.sport == 'football':
            return await self._execute_football_job(job)
        elif job.sport == 'basketball':
            return await self._execute_basketball_job(job)
        elif job.sport == 'multi' or job.data_type == 'odds':
            return await self._execute_multi_sport_job(job)
        else:
            raise ValueError(f"Unknown sport: {job.sport}")
    
    async def _execute_tennis_job(self, job: ScrapingJob) -> Any:
        """Execute tennis-specific scraping job"""
        scraper = self.scrapers['tennis_advanced']
        
        if job.data_type == 'live_scores':
            return await scraper.scrape_live_scores()
        elif job.data_type == 'rankings':
            return await scraper.scrape_atp_rankings()
        elif job.data_type == 'odds':
            return await scraper.scrape_betting_odds()
        else:
            return await scraper.run_comprehensive_scraping()
    
    async def _execute_football_job(self, job: ScrapingJob) -> Any:
        """Execute football-specific scraping job"""
        scraper = self.scrapers['multi_sport']
        
        if job.data_type == 'league_table':
            return await scraper.scrape_premier_league()
        elif job.data_type == 'live_scores':
            return await scraper._scrape_sport_live_scores('football')
        else:
            return await scraper.scrape_football_comprehensive()
    
    async def _execute_basketball_job(self, job: ScrapingJob) -> Any:
        """Execute basketball-specific scraping job"""
        scraper = self.scrapers['multi_sport']
        
        if job.data_type == 'standings':
            return await scraper.scrape_nba_standings()
        elif job.data_type == 'live_scores':
            return await scraper._scrape_sport_live_scores('basketball')
        else:
            return await scraper.scrape_basketball_comprehensive()
    
    async def _execute_multi_sport_job(self, job: ScrapingJob) -> Any:
        """Execute multi-sport scraping job"""
        scraper = self.scrapers['multi_sport']
        
        if job.data_type == 'odds':
            return await scraper.scrape_comprehensive_odds()
        elif job.data_type == 'live_scores':
            return await scraper.scrape_live_scores_all_sports()
        elif job.data_type == 'news':
            return await scraper.scrape_sports_news()
        else:
            return await scraper.run_comprehensive_sports_scraping()
    
    async def _process_scraped_data(self, data: Any, job: ScrapingJob) -> Any:
        """Process and clean scraped data"""
        if not data:
            return data
        
        processor = self.scrapers['data_processor']
        
        # Convert to DataFrame if it's a list of dictionaries
        if isinstance(data, list) and data and isinstance(data[0], dict):
            df = pd.DataFrame(data)
            
            # Clean and process data
            cleaned_df = processor.clean_data(df, job.sport)
            featured_df = processor.engineer_features(cleaned_df, job.sport)
            
            # Convert back to list of dictionaries
            return featured_df.to_dict('records')
        
        return data
    
    def _calculate_data_quality_score(self, data: Any, job: ScrapingJob) -> float:
        """Calculate data quality score"""
        if not data:
            return 0.0
        
        if isinstance(data, list):
            # Check if we got expected number of records
            target_ratio = min(len(data) / max(job.target_count, 1), 1.0)
            
            # Check data completeness
            if data and isinstance(data[0], dict):
                total_fields = len(data[0])
                complete_records = 0
                
                for record in data[:10]:  # Sample first 10 records
                    non_null_fields = sum(1 for v in record.values() if v is not None and v != '')
                    if non_null_fields / total_fields > 0.8:  # 80% completeness threshold
                        complete_records += 1
                
                completeness_ratio = complete_records / min(len(data), 10)
            else:
                completeness_ratio = 1.0
            
            return (target_ratio * 0.6 + completeness_ratio * 0.4) * 100
        
        return 50.0  # Default score for non-list data
    
    async def _store_scraped_data(self, data: Any, job: ScrapingJob):
        """Store scraped data to appropriate storage"""
        if not data:
            return
        
        # Create data directory
        data_dir = Path(f"data/scraped/{job.sport}")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{job.job_id}_{timestamp}.json"
        filepath = data_dir / filename
        
        # Store data
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        # Update cache
        self.data_cache[job.job_id] = {
            'data': data,
            'timestamp': datetime.now(),
            'filepath': str(filepath)
        }
    
    def _check_rate_limit(self, source: str) -> bool:
        """Check if request is within rate limits"""
        current_time = time.time()
        limiter = self.rate_limiters[source]
        
        # Reset counter if minute has passed
        if current_time - limiter['reset_time'] >= 60:
            limiter['requests'] = 0
            limiter['reset_time'] = current_time
        
        # Check if under limit
        if limiter['requests'] < self.global_rate_limit:
            limiter['requests'] += 1
            return True
        
        return False
    
    def _update_job_success_rate(self, job: ScrapingJob, success: bool):
        """Update job success rate"""
        # Simple moving average (can be improved with more sophisticated tracking)
        if hasattr(job, '_total_runs'):
            job._total_runs += 1
            job._successful_runs += 1 if success else 0
        else:
            job._total_runs = 1
            job._successful_runs = 1 if success else 0
        
        job.success_rate = job._successful_runs / job._total_runs
        
        # Update next run time based on frequency
        if job.frequency == 'realtime':
            job.next_run = datetime.now() + timedelta(minutes=5)
        elif job.frequency == 'hourly':
            job.next_run = datetime.now() + timedelta(hours=1)
        elif job.frequency == 'daily':
            job.next_run = datetime.now() + timedelta(days=1)
        
        job.last_run = datetime.now()
        self._update_job_in_db(job)
    
    def _store_result(self, result: ScrapingResult):
        """Store scraping result in database"""
        with self.db_lock:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT INTO scraping_results 
                (job_id, source, sport, records_count, execution_time, 
                 success, error_message, data_quality_score, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.job_id, result.source, result.sport, result.records_count,
                result.execution_time, result.success, result.error_message,
                result.data_quality_score, result.timestamp
            ))
            self.db_connection.commit()
        
        # Add to in-memory history
        self.results_history.append(result)
    
    def _update_performance_metrics(self, result: ScrapingResult):
        """Update performance metrics"""
        self.performance_metrics['total_requests'] += 1
        
        if result.success:
            self.performance_metrics['successful_requests'] += 1
        else:
            self.performance_metrics['failed_requests'] += 1
        
        # Update average response time
        total_time = (self.performance_metrics['average_response_time'] * 
                     (self.performance_metrics['total_requests'] - 1) + 
                     result.execution_time)
        self.performance_metrics['average_response_time'] = total_time / self.performance_metrics['total_requests']
        
        # Update average data quality
        if result.success:
            current_avg = self.performance_metrics['data_quality_average']
            success_count = self.performance_metrics['successful_requests']
            
            if success_count == 1:
                self.performance_metrics['data_quality_average'] = result.data_quality_score
            else:
                self.performance_metrics['data_quality_average'] = (
                    (current_avg * (success_count - 1) + result.data_quality_score) / success_count
                )
    
    async def run_scheduler(self):
        """Main scheduler loop"""
        self.running = True
        self.logger.info("Starting orchestrator scheduler")
        
        while self.running:
            try:
                if not self.paused:
                    # Find jobs that are ready to run
                    ready_jobs = [
                        job for job in self.jobs.values()
                        if job.enabled and job.next_run <= datetime.now() and job.job_id not in self.active_jobs
                    ]
                    
                    # Sort by priority (lower number = higher priority)
                    ready_jobs.sort(key=lambda x: x.priority)
                    
                    # Execute jobs concurrently (limit concurrent jobs)
                    max_concurrent = 5
                    current_active = len(self.active_jobs)
                    
                    if ready_jobs and current_active < max_concurrent:
                        jobs_to_run = ready_jobs[:max_concurrent - current_active]
                        
                        # Execute jobs
                        tasks = []
                        for job in jobs_to_run:
                            self.active_jobs.add(job.job_id)
                            task = asyncio.create_task(self._execute_job_with_cleanup(job))
                            tasks.append(task)
                        
                        # Don't wait for completion, let them run in background
                        if tasks:
                            self.logger.info(f"Started {len(tasks)} scraping jobs")
                
                # Wait before next scheduler cycle
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.error_logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _execute_job_with_cleanup(self, job: ScrapingJob):
        """Execute job and ensure cleanup"""
        try:
            result = await self.execute_job(job)
            return result
        finally:
            # Always remove from active jobs
            self.active_jobs.discard(job.job_id)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        uptime = datetime.now() - self.performance_metrics['uptime_start']
        
        status = {
            'orchestrator': {
                'running': self.running,
                'paused': self.paused,
                'uptime_seconds': uptime.total_seconds(),
                'uptime_formatted': str(uptime)
            },
            'jobs': {
                'total': len(self.jobs),
                'enabled': sum(1 for job in self.jobs.values() if job.enabled),
                'active': len(self.active_jobs),
                'ready_to_run': sum(1 for job in self.jobs.values() 
                                  if job.enabled and job.next_run <= datetime.now())
            },
            'performance': self.performance_metrics.copy(),
            'recent_results': [
                asdict(result) for result in list(self.results_history)[-10:]
            ],
            'data_cache': {
                'cached_jobs': len(self.data_cache),
                'cache_size_mb': sum(
                    len(json.dumps(cache['data'], default=str).encode('utf-8'))
                    for cache in self.data_cache.values()
                ) / (1024 * 1024)
            }
        }
        
        return status
    
    def get_job_statistics(self) -> Dict[str, Any]:
        """Get detailed job statistics"""
        stats = {}
        
        for job_id, job in self.jobs.items():
            # Get recent results for this job
            recent_results = [r for r in self.results_history if r.job_id == job_id][-10:]
            
            if recent_results:
                success_rate = sum(1 for r in recent_results if r.success) / len(recent_results)
                avg_execution_time = sum(r.execution_time for r in recent_results) / len(recent_results)
                avg_quality_score = sum(r.data_quality_score for r in recent_results if r.success) / max(1, sum(1 for r in recent_results if r.success))
            else:
                success_rate = 0.0
                avg_execution_time = 0.0
                avg_quality_score = 0.0
            
            stats[job_id] = {
                'job_info': asdict(job),
                'recent_performance': {
                    'success_rate': success_rate,
                    'avg_execution_time': avg_execution_time,
                    'avg_quality_score': avg_quality_score,
                    'recent_runs': len(recent_results)
                }
            }
        
        return stats
    
    def pause_orchestrator(self):
        """Pause the orchestrator"""
        self.paused = True
        self.logger.info("Orchestrator paused")
    
    def resume_orchestrator(self):
        """Resume the orchestrator"""
        self.paused = False
        self.logger.info("Orchestrator resumed")
    
    def stop_orchestrator(self):
        """Stop the orchestrator"""
        self.running = False
        self.logger.info("Orchestrator stopping...")
        
        # Close database connection
        if hasattr(self, 'db_connection'):
            self.db_connection.close()
    
    def export_data(self, job_id: Optional[str] = None, format: str = 'json') -> str:
        """Export scraped data"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if job_id and job_id in self.data_cache:
            # Export specific job data
            data = self.data_cache[job_id]['data']
            filename = f"export_{job_id}_{timestamp}.{format}"
        else:
            # Export all cached data
            data = {job_id: cache['data'] for job_id, cache in self.data_cache.items()}
            filename = f"export_all_{timestamp}.{format}"
        
        export_path = Path(f"data/exports/{filename}")
        export_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'json':
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        elif format == 'csv' and isinstance(data, list):
            df = pd.DataFrame(data)
            df.to_csv(export_path, index=False)
        
        self.logger.info(f"Data exported to {export_path}")
        return str(export_path)

# Example usage and testing
async def main():
    """Main function to test the orchestrator"""
    orchestrator = MasterScrapingOrchestrator()
    
    print("🚀 COMPREHENSIVE SCRAPING ORCHESTRATOR")
    print("=" * 60)
    
    try:
        # Start the orchestrator
        print("Starting orchestrator...")
        
        # Run for 2 minutes for demonstration
        await asyncio.wait_for(orchestrator.run_scheduler(), timeout=120)
        
    except asyncio.TimeoutError:
        print("\n⏰ Demo completed - stopping orchestrator")
    except KeyboardInterrupt:
        print("\n⛔ Interrupted by user")
    finally:
        orchestrator.stop_orchestrator()
    
    # Show final status
    status = orchestrator.get_system_status()
    print(f"\n📊 FINAL SYSTEM STATUS:")
    print(f"Total requests: {status['performance']['total_requests']}")
    print(f"Success rate: {status['performance']['successful_requests'] / max(1, status['performance']['total_requests']) * 100:.1f}%")
    print(f"Average execution time: {status['performance']['average_response_time']:.2f}s")
    print(f"Average data quality: {status['performance']['data_quality_average']:.1f}/100")
    print(f"Cached datasets: {status['data_cache']['cached_jobs']}")

if __name__ == "__main__":
    asyncio.run(main())