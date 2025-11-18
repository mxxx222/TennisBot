#!/usr/bin/env python3
"""
📊 TENNISEXPLORER MONITOR
=========================

Monitoring and metrics for TennisExplorer scraper.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.monitoring.alert_thresholds import AlertThresholds

logger = logging.getLogger(__name__)


class TennisExplorerMonitor:
    """
    Monitor for TennisExplorer scraper
    """
    
    def __init__(self):
        """Initialize monitor"""
        self.start_time = datetime.now()
        self.metrics = {
            'matches_scraped': 0,
            'matches_stored': 0,
            'h2h_scraped': 0,
            'form_scraped': 0,
            'odds_scraped': 0,
            'enrichment_success': 0,
            'enrichment_failures': 0,
            'roi_opportunities': 0,
            'alerts_sent': 0,
            'errors': 0,
            'errors_by_type': {}
        }
        
        self.error_log: List[Dict] = []
        
        # Last update tracking for timeout detection
        self.last_update_time: Optional[datetime] = None
        
        # Alert thresholds
        self.alert_thresholds = AlertThresholds()
        
        logger.info("📊 TennisExplorer Monitor initialized")
    
    def record_match_scraped(self):
        """Record match scraped"""
        self.metrics['matches_scraped'] += 1
    
    def record_match_stored(self):
        """Record match stored"""
        self.metrics['matches_stored'] += 1
    
    def record_h2h_scraped(self):
        """Record H2H scraped"""
        self.metrics['h2h_scraped'] += 1
    
    def record_form_scraped(self):
        """Record form scraped"""
        self.metrics['form_scraped'] += 1
    
    def record_odds_scraped(self):
        """Record odds scraped"""
        self.metrics['odds_scraped'] += 1
    
    def record_enrichment_success(self):
        """Record successful enrichment"""
        self.metrics['enrichment_success'] += 1
    
    def record_enrichment_failure(self, error_type: str = 'unknown'):
        """Record enrichment failure"""
        self.metrics['enrichment_failures'] += 1
        self.metrics['errors_by_type'][error_type] = self.metrics['errors_by_type'].get(error_type, 0) + 1
    
    def record_roi_opportunity(self, ev_pct: float = 0.0):
        """Record ROI opportunity detected"""
        self.metrics['roi_opportunities'] += 1
        
        # Check if should alert
        if self.alert_thresholds.check_roi_opportunity(ev_pct):
            return {
                'should_alert': True,
                'type': 'roi_opportunity',
                'message': f'High ROI opportunity detected: {ev_pct:.1f}% EV',
                'severity': 'info'
            }
        return {'should_alert': False}
    
    def record_alert_sent(self):
        """Record alert sent"""
        self.metrics['alerts_sent'] += 1
    
    def record_error(self, error: Exception, context: str = ''):
        """Record error"""
        self.metrics['errors'] += 1
        error_type = type(error).__name__
        self.metrics['errors_by_type'][error_type] = self.metrics['errors_by_type'].get(error_type, 0) + 1
        
        self.error_log.append({
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'error_message': str(error),
            'context': context
        })
        
        # Keep only last 100 errors
        if len(self.error_log) > 100:
            self.error_log = self.error_log[-100:]
        
        # Check error rate threshold
        total_requests = self.metrics['matches_scraped'] + self.metrics['h2h_scraped'] + self.metrics['form_scraped']
        if self.alert_thresholds.check_error_rate(self.metrics['errors'], total_requests):
            return {
                'should_alert': True,
                'type': 'error_rate',
                'message': f'High error rate: {self.metrics["errors"]} errors in {total_requests} requests',
                'severity': 'critical'
            }
        return {'should_alert': False}
    
    def update_last_activity(self):
        """Update last activity timestamp"""
        self.last_update_time = datetime.now()
    
    def check_pipeline_timeout(self) -> Dict:
        """Check if pipeline has timed out"""
        if self.alert_thresholds.check_pipeline_timeout(self.last_update_time):
            return {
                'should_alert': True,
                'type': 'pipeline_timeout',
                'message': f'Pipeline has not updated in {self.alert_thresholds.PIPELINE_TIMEOUT_THRESHOLD.current_value:.0f} minutes',
                'severity': 'critical'
            }
        return {'should_alert': False}
    
    def get_uptime(self) -> float:
        """Get uptime in seconds"""
        return (datetime.now() - self.start_time).total_seconds()
    
    def get_enrichment_success_rate(self) -> float:
        """Get enrichment success rate"""
        total = self.metrics['enrichment_success'] + self.metrics['enrichment_failures']
        if total == 0:
            return 0.0
        return (self.metrics['enrichment_success'] / total) * 100
    
    def get_metrics_summary(self) -> Dict:
        """Get metrics summary"""
        uptime_hours = self.get_uptime() / 3600
        
        return {
            'uptime_hours': round(uptime_hours, 2),
            'matches_scraped': self.metrics['matches_scraped'],
            'matches_stored': self.metrics['matches_stored'],
            'h2h_scraped': self.metrics['h2h_scraped'],
            'form_scraped': self.metrics['form_scraped'],
            'odds_scraped': self.metrics['odds_scraped'],
            'enrichment_success_rate': round(self.get_enrichment_success_rate(), 2),
            'roi_opportunities': self.metrics['roi_opportunities'],
            'alerts_sent': self.metrics['alerts_sent'],
            'errors': self.metrics['errors'],
            'errors_by_type': self.metrics['errors_by_type'].copy()
        }
    
    def log_summary(self):
        """Log metrics summary"""
        summary = self.get_metrics_summary()
        logger.info("📊 Metrics Summary:")
        logger.info(f"   Uptime: {summary['uptime_hours']:.1f} hours")
        logger.info(f"   Matches scraped: {summary['matches_scraped']}")
        logger.info(f"   Matches stored: {summary['matches_stored']}")
        logger.info(f"   Enrichment success rate: {summary['enrichment_success_rate']:.1f}%")
        logger.info(f"   ROI opportunities: {summary['roi_opportunities']}")
        logger.info(f"   Alerts sent: {summary['alerts_sent']}")
        logger.info(f"   Errors: {summary['errors']}")

