#!/usr/bin/env python3
"""
📅 WEEKLY REPORT SCHEDULER
==========================

Schedules weekly report generation.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.notion.weekly_report_generator import WeeklyReportGenerator
from src.monitoring.tennisexplorer_monitor import TennisExplorerMonitor

logger = logging.getLogger(__name__)


class WeeklyReportScheduler:
    """Schedules and generates weekly reports"""
    
    def __init__(self, monitor: Optional[TennisExplorerMonitor] = None):
        """
        Initialize weekly report scheduler
        
        Args:
            monitor: TennisExplorerMonitor instance (optional)
        """
        self.monitor = monitor or TennisExplorerMonitor()
        self.report_generator = WeeklyReportGenerator()
        self.last_report_date = None
        
        logger.info("📅 Weekly Report Scheduler initialized")
    
    def should_generate_report(self) -> bool:
        """Check if it's time to generate a weekly report"""
        # Generate report every Monday
        today = datetime.now()
        
        # Check if it's Monday
        if today.weekday() != 0:  # Monday = 0
            return False
        
        # Check if we already generated a report today
        if self.last_report_date and self.last_report_date.date() == today.date():
            return False
        
        return True
    
    def generate_and_store_report(self) -> Optional[str]:
        """
        Generate and store weekly report
        
        Returns:
            Report page ID if successful
        """
        if not self.should_generate_report():
            return None
        
        logger.info("📊 Generating weekly report...")
        
        # Get metrics from monitor
        metrics = self.monitor.get_metrics_summary()
        
        # Calculate date range (last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Generate report
        report = self.report_generator.generate_weekly_report(
            metrics, start_date, end_date
        )
        
        # Store in Notion
        page_id = self.report_generator.store_weekly_report(report)
        
        if page_id:
            self.last_report_date = datetime.now()
            logger.info(f"✅ Weekly report generated and stored: {page_id}")
        
        return page_id


def main():
    """Test weekly report generation"""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("📅 Testing Weekly Report Scheduler...")
    print("=" * 60)
    
    monitor = TennisExplorerMonitor()
    # Simulate some metrics
    for _ in range(100):
        monitor.record_match_scraped()
    for _ in range(10):
        monitor.record_roi_opportunity(ev_pct=8.5)
    
    scheduler = WeeklyReportScheduler(monitor)
    
    # Force report generation (for testing)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    metrics = monitor.get_metrics_summary()
    report = scheduler.report_generator.generate_weekly_report(metrics, start_date, end_date)
    
    print("\n📊 Report Preview:")
    print(f"   Period: {report['period']}")
    print(f"   Matches: {report['total_matches']}")
    print(f"   Opportunities: {report['total_opportunities']}")
    print(f"   Error Rate: {report['error_rate']}%")
    print(f"\n💡 Insights:")
    for insight in report['insights']:
        print(f"   • {insight}")


if __name__ == "__main__":
    main()

