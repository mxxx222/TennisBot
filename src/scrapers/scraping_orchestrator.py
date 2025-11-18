#!/usr/bin/env python3
"""
🎼 UNIFIED SCRAPING ORCHESTRATOR
================================

Central coordination system for all scraping operations with:
- Unified API for all scraping components
- Intelligent resource allocation
- Performance monitoring and optimization
- Error handling and recovery
- Real-time status tracking

Author: TennisBot Advanced Analytics
Version: 1.0.0
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import threading
import time

from enhanced_sports_scraper import EnhancedSportsScraper, scrape_tennis_data, scrape_football_data
from automated_scheduler import ScrapingScheduler
from data_pipeline import DataCleaningPipeline, clean_scraped_data
from compliance_manager import ComplianceManager
from scraping_utils import ScrapingMetrics

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OrchestratorConfig:
    """Configuration for the scraping orchestrator"""
    max_concurrent_scrapers: int = 3
    enable_scheduler: bool = True
    enable_compliance: bool = True
    enable_data_cleaning: bool = True
    data_retention_days: int = 7
    performance_monitoring: bool = True
    auto_recovery: bool = True

@dataclass
class ScrapingJob:
    """Represents a scraping job"""
    job_id: str
    sport: str
    priority: int = 1  # 1=low, 2=medium, 3=high
    status: str = "pending"  # pending, running, completed, failed
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: float = 0.0
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}

class ScrapingOrchestrator:
    """Unified orchestrator for all scraping operations"""

    def __init__(self, config: OrchestratorConfig = None):
        self.config = config or OrchestratorConfig()

        # Core components
        self.scraper = None
        self.scheduler = None
        self.compliance_manager = None
        self.data_pipeline = None

        # Job management
        self.jobs = {}  # job_id -> ScrapingJob
        self.job_queue = asyncio.Queue()
        self.active_jobs = set()
        self.completed_jobs = []

        # Performance tracking
        self.performance_stats = {
            'total_jobs': 0,
            'successful_jobs': 0,
            'failed_jobs': 0,
            'avg_completion_time': 0.0,
            'uptime': 0.0
        }

        # Control flags
        self.is_running = False
        self.shutdown_event = threading.Event()

        # Initialize components
        self._init_components()

    def _init_components(self):
        """Initialize all orchestrator components"""
        logger.info("🔧 Initializing scraping orchestrator components...")

        # Initialize scraper
        scraper_config = {}  # Would load from config file
        self.scraper = EnhancedSportsScraper(scraper_config)

        # Initialize scheduler if enabled
        if self.config.enable_scheduler:
            scheduler_config = {}  # Would load from config file
            self.scheduler = ScrapingScheduler(scheduler_config)

        # Initialize compliance manager if enabled
        if self.config.enable_compliance:
            compliance_config = {}  # Would load from config file
            self.compliance_manager = ComplianceManager(compliance_config)

        # Initialize data pipeline if enabled
        if self.config.enable_data_cleaning:
            pipeline_config = {}  # Would load from config file
            self.data_pipeline = DataCleaningPipeline(pipeline_config)

        logger.info("✅ All components initialized")

    async def start(self):
        """Start the orchestrator"""
        logger.info("🚀 Starting scraping orchestrator...")

        self.is_running = True
        start_time = time.time()

        try:
            # Start background tasks
            tasks = []

            # Job processing task
            tasks.append(asyncio.create_task(self._job_processor()))

            # Monitoring task
            if self.config.performance_monitoring:
                tasks.append(asyncio.create_task(self._performance_monitor()))

            # Auto-recovery task
            if self.config.auto_recovery:
                tasks.append(asyncio.create_task(self._auto_recovery()))

            # Wait for all tasks
            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"❌ Orchestrator error: {e}")
        finally:
            self.is_running = False
            self.performance_stats['uptime'] = time.time() - start_time
            logger.info("🛑 Orchestrator stopped")

    def stop(self):
        """Stop the orchestrator"""
        logger.info("🛑 Stopping orchestrator...")
        self.is_running = False
        self.shutdown_event.set()

    async def submit_job(self, sport: str, priority: int = 1, **kwargs) -> str:
        """Submit a new scraping job"""
        job_id = f"{sport}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(kwargs)) % 1000}"

        job = ScrapingJob(
            job_id=job_id,
            sport=sport,
            priority=priority,
            metadata=kwargs
        )

        self.jobs[job_id] = job
        await self.job_queue.put(job)

        logger.info(f"📋 Submitted job {job_id} for {sport} scraping")
        return job_id

    def get_job_status(self, job_id: str) -> Optional[ScrapingJob]:
        """Get status of a specific job"""
        return self.jobs.get(job_id)

    def get_active_jobs(self) -> List[ScrapingJob]:
        """Get all active jobs"""
        return [job for job in self.jobs.values() if job.status == "running"]

    def get_completed_jobs(self, limit: int = 10) -> List[ScrapingJob]:
        """Get recently completed jobs"""
        return sorted(
            [job for job in self.jobs.values() if job.status in ["completed", "failed"]],
            key=lambda x: x.completed_at or x.created_at,
            reverse=True
        )[:limit]

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            'orchestrator': {
                'running': self.is_running,
                'uptime': self.performance_stats.get('uptime', 0),
                'config': asdict(self.config)
            },
            'jobs': {
                'total': len(self.jobs),
                'active': len(self.get_active_jobs()),
                'pending': self.job_queue.qsize(),
                'completed': len([j for j in self.jobs.values() if j.status == "completed"]),
                'failed': len([j for j in self.jobs.values() if j.status == "failed"])
            },
            'performance': self.performance_stats.copy(),
            'components': {
                'scraper': self.scraper is not None,
                'scheduler': self.scheduler is not None,
                'compliance': self.compliance_manager is not None,
                'data_pipeline': self.data_pipeline is not None
            }
        }

        return status

    async def _job_processor(self):
        """Main job processing loop"""
        logger.info("⚙️ Starting job processor...")

        # Create semaphore for concurrent job limit
        semaphore = asyncio.Semaphore(self.config.max_concurrent_scrapers)

        while self.is_running:
            try:
                # Get next job from queue
                job = await asyncio.wait_for(self.job_queue.get(), timeout=1.0)

                # Process job with semaphore
                asyncio.create_task(self._process_job_with_semaphore(job, semaphore))

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"❌ Job processor error: {e}")
                await asyncio.sleep(1)

    async def _process_job_with_semaphore(self, job: ScrapingJob, semaphore: asyncio.Semaphore):
        """Process a job with concurrency control"""
        async with semaphore:
            await self._process_job(job)

    async def _process_job(self, job: ScrapingJob):
        """Process a single scraping job"""
        try:
            # Update job status
            job.status = "running"
            job.started_at = datetime.now().isoformat()
            self.active_jobs.add(job.job_id)

            logger.info(f"🏃 Starting job {job.job_id} for {job.sport}")

            # Execute job based on sport
            if job.sport == "tennis":
                result = await self._execute_tennis_job(job)
            elif job.sport == "football":
                result = await self._execute_football_job(job)
            else:
                raise ValueError(f"Unsupported sport: {job.sport}")

            # Process results
            if self.config.enable_data_cleaning and self.data_pipeline:
                logger.info(f"🧹 Cleaning data for job {job.job_id}")
                cleaned_data, metrics = self.data_pipeline.process_scraped_data(result)

                # Validate quality
                if not self.data_pipeline.validate_data_quality(cleaned_data, metrics):
                    logger.warning(f"⚠️ Data quality issues for job {job.job_id}")
                    job.metadata['quality_warnings'] = True

                result = cleaned_data
                job.metadata['quality_metrics'] = asdict(metrics)

            # Find ROI opportunities
            if hasattr(self.scraper, 'find_roi_opportunities'):
                logger.info(f"💰 Analyzing ROI for job {job.job_id}")
                roi_opportunities = await self.scraper.find_roi_opportunities(result)
                job.metadata['roi_opportunities'] = roi_opportunities

            # Mark job as completed
            job.status = "completed"
            job.completed_at = datetime.now().isoformat()
            job.result = result
            job.progress = 100.0

            # Update performance stats
            self.performance_stats['total_jobs'] += 1
            self.performance_stats['successful_jobs'] += 1

            logger.info(f"✅ Job {job.job_id} completed successfully")

        except Exception as e:
            # Mark job as failed
            job.status = "failed"
            job.completed_at = datetime.now().isoformat()
            job.error = str(e)
            job.progress = 0.0

            # Update performance stats
            self.performance_stats['total_jobs'] += 1
            self.performance_stats['failed_jobs'] += 1

            logger.error(f"❌ Job {job.job_id} failed: {e}")

        finally:
            # Clean up
            self.active_jobs.discard(job.job_id)
            self.job_queue.task_done()

    async def _execute_tennis_job(self, job: ScrapingJob) -> List[Dict[str, Any]]:
        """Execute tennis scraping job"""
        # Get date range from job metadata
        date_range = job.metadata.get('date_range')

        # Scrape tennis data
        matches = await self.scraper.scrape_comprehensive_data('tennis', date_range)

        return [asdict(match) for match in matches]

    async def _execute_football_job(self, job: ScrapingJob) -> List[Dict[str, Any]]:
        """Execute football scraping job"""
        # Get date range from job metadata
        date_range = job.metadata.get('date_range')

        # Scrape football data
        matches = await self.scraper.scrape_comprehensive_data('football', date_range)

        return [asdict(match) for match in matches]

    async def _performance_monitor(self):
        """Monitor system performance"""
        while self.is_running:
            try:
                # Collect performance metrics
                status = await self.get_system_status()

                # Log performance summary every 5 minutes
                logger.info(f"📊 Performance: {status['jobs']['active']} active, "
                          f"{status['jobs']['completed']} completed, "
                          f"{status['jobs']['failed']} failed")

                # Check for performance issues
                if status['jobs']['failed'] > status['jobs']['total'] * 0.1:  # >10% failure rate
                    logger.warning("⚠️ High job failure rate detected")

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"❌ Performance monitor error: {e}")
                await asyncio.sleep(60)

    async def _auto_recovery(self):
        """Auto-recovery for failed jobs"""
        while self.is_running:
            try:
                # Find failed jobs that can be retried
                failed_jobs = [job for job in self.jobs.values()
                             if job.status == "failed" and
                             job.metadata.get('retry_count', 0) < 3]

                for job in failed_jobs:
                    # Reset job for retry
                    job.status = "pending"
                    job.error = None
                    job.metadata['retry_count'] = job.metadata.get('retry_count', 0) + 1

                    # Re-queue job
                    await self.job_queue.put(job)

                    logger.info(f"🔄 Retrying failed job {job.job_id} (attempt {job.metadata['retry_count']})")

                await asyncio.sleep(600)  # Check every 10 minutes

            except Exception as e:
                logger.error(f"❌ Auto-recovery error: {e}")
                await asyncio.sleep(60)

    def export_status_report(self, filename: str = None) -> str:
        """Export comprehensive status report"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"orchestrator_status_{timestamp}.json"

        # Get current status
        status = asyncio.run(self.get_system_status())

        # Add additional details
        status['jobs_detail'] = {
            'active_jobs': [asdict(job) for job in self.get_active_jobs()],
            'recent_completed': [asdict(job) for job in self.get_completed_jobs(5)]
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"📋 Exported orchestrator status to {filename}")
        return filename

# Convenience functions for easy usage
async def create_orchestrator(config: Dict[str, Any] = None) -> ScrapingOrchestrator:
    """Create and configure a scraping orchestrator"""
    orchestrator_config = OrchestratorConfig(**config) if config else OrchestratorConfig()
    return ScrapingOrchestrator(orchestrator_config)

async def quick_scrape(sport: str, config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Quick scraping function for immediate results"""
    orchestrator = await create_orchestrator(config)

    # Submit job
    job_id = await orchestrator.submit_job(sport, priority=2)

    # Wait for completion (with timeout)
    timeout = 300  # 5 minutes
    start_time = time.time()

    while time.time() - start_time < timeout:
        job = orchestrator.get_job_status(job_id)
        if job and job.status == "completed":
            return job.result
        elif job and job.status == "failed":
            raise Exception(f"Job failed: {job.error}")

        await asyncio.sleep(5)

    raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")

if __name__ == "__main__":
    # Test the orchestrator
    print("🎼 UNIFIED SCRAPING ORCHESTRATOR TEST")
    print("=" * 50)

    async def main():
        try:
            # Create orchestrator
            config = {
                'max_concurrent_scrapers': 2,
                'enable_scheduler': False,  # Disable for testing
                'enable_compliance': True,
                'enable_data_cleaning': True
            }

            orchestrator = await create_orchestrator(config)

            # Start orchestrator in background
            orchestrator_task = asyncio.create_task(orchestrator.start())

            # Give it a moment to start
            await asyncio.sleep(2)

            print("🧪 Testing job submission...")

            # Submit tennis scraping job
            tennis_job_id = await orchestrator.submit_job("tennis", priority=2)
            print(f"📋 Submitted tennis job: {tennis_job_id}")

            # Wait for job to complete
            timeout = 120  # 2 minutes
            start_time = time.time()

            while time.time() - start_time < timeout:
                job = orchestrator.get_job_status(tennis_job_id)
                if job:
                    print(f"📊 Job status: {job.status} ({job.progress:.1f}%)")

                    if job.status == "completed":
                        print(f"✅ Tennis job completed! Got {len(job.result) if job.result else 0} matches")

                        # Show ROI opportunities if any
                        roi = job.metadata.get('roi_opportunities', {})
                        arbitrage = roi.get('arbitrage', [])
                        value_bets = roi.get('value_bets', [])

                        if arbitrage:
                            print(f"💰 Found {len(arbitrage)} arbitrage opportunities")
                        if value_bets:
                            print(f"💎 Found {len(value_bets)} value bets")

                        break
                    elif job.status == "failed":
                        print(f"❌ Tennis job failed: {job.error}")
                        break

                await asyncio.sleep(10)

            # Stop orchestrator
            orchestrator.stop()
            await orchestrator_task

            # Export final status
            status_file = orchestrator.export_status_report()
            print(f"📋 Final status exported to: {status_file}")

            print("✅ Orchestrator test completed")

        except Exception as e:
            print(f"❌ Orchestrator test failed: {e}")
            import traceback
            traceback.print_exc()

    # Run the test
    asyncio.run(main())