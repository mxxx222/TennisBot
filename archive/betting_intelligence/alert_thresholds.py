#!/usr/bin/env python3
"""
🚨 ALERT THRESHOLDS
===================

Defines alert thresholds for monitoring system health.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta


@dataclass
class AlertThreshold:
    """Alert threshold configuration"""
    name: str
    threshold_value: float
    current_value: float
    alert_type: str  # 'error_rate', 'roi_opportunity', 'pipeline_timeout'
    severity: str  # 'critical', 'warning', 'info'
    last_alerted: Optional[datetime] = None
    cooldown_minutes: int = 60  # Don't alert more than once per hour
    
    def should_alert(self) -> bool:
        """Check if threshold is exceeded and cooldown has passed"""
        if self.alert_type == 'error_rate':
            exceeded = self.current_value > self.threshold_value
        elif self.alert_type == 'roi_opportunity':
            exceeded = self.current_value >= self.threshold_value
        elif self.alert_type == 'pipeline_timeout':
            # For timeout, check if last update was too long ago
            exceeded = self.current_value > self.threshold_value
        else:
            exceeded = False
        
        if not exceeded:
            return False
        
        # Check cooldown
        if self.last_alerted:
            elapsed = (datetime.now() - self.last_alerted).total_seconds() / 60
            if elapsed < self.cooldown_minutes:
                return False
        
        return True
    
    def record_alert(self):
        """Record that alert was sent"""
        self.last_alerted = datetime.now()


class AlertThresholds:
    """Default alert thresholds"""
    
    # Error rate threshold (10%)
    ERROR_RATE_THRESHOLD = AlertThreshold(
        name="Error Rate",
        threshold_value=10.0,  # 10%
        current_value=0.0,
        alert_type='error_rate',
        severity='critical'
    )
    
    # ROI opportunity threshold (5% edge)
    ROI_OPPORTUNITY_THRESHOLD = AlertThreshold(
        name="ROI Opportunity",
        threshold_value=5.0,  # 5% EV
        current_value=0.0,
        alert_type='roi_opportunity',
        severity='info'
    )
    
    # Pipeline timeout (2 hours)
    PIPELINE_TIMEOUT_THRESHOLD = AlertThreshold(
        name="Pipeline Timeout",
        threshold_value=120.0,  # 120 minutes = 2 hours
        current_value=0.0,
        alert_type='pipeline_timeout',
        severity='critical'
    )
    
    @staticmethod
    def check_error_rate(error_count: int, total_requests: int) -> bool:
        """Check if error rate exceeds threshold"""
        if total_requests == 0:
            return False
        
        error_rate = (error_count / total_requests) * 100
        AlertThresholds.ERROR_RATE_THRESHOLD.current_value = error_rate
        
        if AlertThresholds.ERROR_RATE_THRESHOLD.should_alert():
            AlertThresholds.ERROR_RATE_THRESHOLD.record_alert()
            return True
        return False
    
    @staticmethod
    def check_roi_opportunity(ev_pct: float) -> bool:
        """Check if ROI opportunity exceeds threshold"""
        AlertThresholds.ROI_OPPORTUNITY_THRESHOLD.current_value = ev_pct
        
        if AlertThresholds.ROI_OPPORTUNITY_THRESHOLD.should_alert():
            AlertThresholds.ROI_OPPORTUNITY_THRESHOLD.record_alert()
            return True
        return False
    
    @staticmethod
    def check_pipeline_timeout(last_update: datetime) -> bool:
        """Check if pipeline hasn't updated in too long"""
        if not last_update:
            return True  # Never updated = critical
        
        minutes_since_update = (datetime.now() - last_update).total_seconds() / 60
        AlertThresholds.PIPELINE_TIMEOUT_THRESHOLD.current_value = minutes_since_update
        
        if AlertThresholds.PIPELINE_TIMEOUT_THRESHOLD.should_alert():
            AlertThresholds.PIPELINE_TIMEOUT_THRESHOLD.record_alert()
            return True
        return False

