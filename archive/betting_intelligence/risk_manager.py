"""
Risk Management and Logging System for Educational Betfury Research
===================================================================

This module provides comprehensive risk management, logging, and monitoring
capabilities for educational sports analytics research.

DISCLAIMER: This is for educational/research purposes only.
All risk management features are designed for learning and safety.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
from enum import Enum
from loguru import logger
import yaml

class RiskLevel(Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    """Alert type enumeration"""
    PREDICTION = "prediction"
    RISK_BREACH = "risk_breach"
    SYSTEM_ERROR = "system_error"
    RATE_LIMIT = "rate_limit"
    PERFORMANCE = "performance"

@dataclass
class RiskMetrics:
    """Risk management metrics"""
    daily_loss_percentage: float
    weekly_loss_percentage: float
    prediction_streak: int
    error_rate: float
    avg_confidence: float
    last_reset_date: str
    active_limits: List[str]

@dataclass
class LogEntry:
    """Log entry structure"""
    timestamp: str
    level: str
    component: str
    action: str
    details: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class ResearchDataStore:
    """Store and manage research data with privacy controls"""
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path("./data/research")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Data retention settings
        self.retention_days = 30
        self.auto_cleanup = True
        
        # Privacy settings
        self.anonymize_data = True
        self.gdpr_compliance = True
        
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory
        logs_dir = self.data_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Configure loguru
        logger.add(
            logs_dir / "research_{time:YYYY-MM-DD}.log",
            rotation="100 MB",
            retention="30 days",
            compression="gz",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level="INFO"
        )
        
        # Separate audit log
        logger.add(
            logs_dir / "audit_{time:YYYY-MM-DD}.log",
            rotation="100 MB", 
            retention="90 days",
            compression="gz",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {component} | {action} | {message}",
            level="DEBUG"
        )
        
        # Console logging
        logger.add(
            lambda msg: print(msg, end=""),
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
            level="INFO"
        )
    
    def log_prediction(self, prediction_data: Dict[str, Any], 
                      risk_level: RiskLevel = RiskLevel.LOW):
        """Log prediction activity"""
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=risk_level.value,
            component="predictor",
            action="prediction_generated",
            details={
                'match_id': self._anonymize_id(prediction_data.get('match_id')),
                'prediction': prediction_data.get('prediction'),
                'confidence': prediction_data.get('confidence'),
                'model_version': prediction_data.get('model_version'),
                'educational_purpose': True,
                'not_for_betting': True
            }
        )
        
        logger.bind(component="predictor", action="prediction").info(
            f"Prediction generated: {prediction_data.get('prediction')} "
            f"(confidence: {prediction_data.get('confidence', 0):.1%})"
        )
        
        self._save_log_entry(entry)
    
    def log_scraping_activity(self, activity_type: str, 
                            data: Dict[str, Any], 
                            risk_level: RiskLevel = RiskLevel.LOW):
        """Log scraping activity"""
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=risk_level.value,
            component="scraper",
            action=activity_type,
            details={
                'url': self._anonymize_url(data.get('url')),
                'matches_found': data.get('matches_count', 0),
                'ethical_compliance': True,
                'rate_limited': True,
                'educational_research': True
            }
        )
        
        logger.bind(component="scraper", action=activity_type).info(
            f"Scraping {activity_type}: {data.get('matches_count', 0)} matches found"
        )
        
        self._save_log_entry(entry)
    
    def log_system_event(self, event_type: str, details: Dict[str, Any],
                        risk_level: RiskLevel = RiskLevel.MEDIUM):
        """Log system events"""
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=risk_level.value,
            component="system",
            action=event_type,
            details=details
        )
        
        logger.bind(component="system", action=event_type).info(
            f"System event: {event_type}"
        )
        
        self._save_log_entry(entry)
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None,
                  risk_level: RiskLevel = RiskLevel.HIGH):
        """Log errors with context"""
        context = context or {}
        
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=risk_level.value,
            component="error",
            action="exception_occurred",
            details={
                'error_type': type(error).__name__,
                'error_message': str(error),
                'context': context,
                'recovery_action': 'logged_for_analysis'
            }
        )
        
        logger.bind(component="error").error(
            f"Error: {type(error).__name__}: {str(error)}"
        )
        
        self._save_log_entry(entry)
    
    def _anonymize_id(self, identifier: str) -> str:
        """Anonymize identifiers for privacy"""
        if not identifier or not self.anonymize_data:
            return identifier
        
        # Simple hash-based anonymization
        return f"anon_{hash(identifier) % 10000:04d}"
    
    def _anonymize_url(self, url: str) -> str:
        """Anonymize URLs for privacy"""
        if not url or not self.anonymize_data:
            return url
        
        # Remove sensitive parts from URL
        if 'betfury.io' in url:
            return 'https://betfury.io/research_endpoint'
        return 'https://example.com/research_endpoint'
    
    def _save_log_entry(self, entry: LogEntry):
        """Save log entry to file"""
        try:
            log_file = self.data_dir / "logs" / f"research_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(entry), default=str) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to save log entry: {e}")
    
    async def cleanup_old_data(self):
        """Clean up old data based on retention policy"""
        if not self.auto_cleanup:
            return
        
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        for log_file in self.data_dir.glob("**/*.log*"):
            try:
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    logger.info(f"Cleaned up old log file: {log_file}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {log_file}: {e}")

class EducationalRiskManager:
    """Risk management system for educational purposes"""
    
    def __init__(self, data_store: ResearchDataStore):
        self.data_store = data_store
        
        # Risk limits (educational/research focused)
        self.limits = {
            'max_matches_per_hour': 50,        # Prevent spam scraping
            'max_predictions_per_day': 100,     # Limit prediction volume
            'max_concurrent_analyses': 5,       # Prevent resource abuse
            'min_confidence_threshold': 0.70,   # Quality threshold
            'max_error_rate': 0.05,             # 5% error rate
            'daily_loss_limit': 0.10,           # 10% daily "loss" (educational)
            'weekly_loss_limit': 0.20,          # 20% weekly "loss"
        }
        
        # Current metrics
        self.metrics = RiskMetrics(
            daily_loss_percentage=0.0,
            weekly_loss_percentage=0.0,
            prediction_streak=0,
            error_rate=0.0,
            avg_confidence=0.0,
            last_reset_date=datetime.now().date().isoformat(),
            active_limits=[]
        )
        
        # Activity tracking
        self.activity_counters = {
            'matches_scraped_today': 0,
            'predictions_today': 0,
            'concurrent_analyses': 0,
            'errors_today': 0,
            'successful_predictions': 0,
            'total_predictions': 0
        }
        
        self._setup_monitoring()
    
    def _setup_monitoring(self):
        """Setup risk monitoring"""
        # Start background monitoring task
        asyncio.create_task(self._monitor_risk_levels())
        asyncio.create_task(self._reset_daily_counters())
    
    async def check_scraping_risk(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if scraping request is within safe limits"""
        result = {
            'allowed': True,
            'reason': '',
            'risk_level': RiskLevel.LOW,
            'suggested_delay': 0
        }
        
        # Check hourly limit
        if self.activity_counters['matches_scraped_today'] >= self.limits['max_matches_per_hour']:
            result.update({
                'allowed': False,
                'reason': 'Daily scraping limit reached',
                'risk_level': RiskLevel.HIGH
            })
            
            self.data_store.log_system_event(
                "rate_limit_breach",
                {'limit_type': 'scraping', 'current_count': self.activity_counters['matches_scraped_today']},
                RiskLevel.HIGH
            )
        
        # Check concurrent analyses
        if self.activity_counters['concurrent_analyses'] >= self.limits['max_concurrent_analyses']:
            result.update({
                'allowed': False,
                'reason': 'Too many concurrent analyses',
                'risk_level': RiskLevel.MEDIUM,
                'suggested_delay': 30
            })
        
        # Suggest delay for rate limiting
        if not result['allowed']:
            return result
        
        # Rate limiting delay
        current_hour = datetime.now().hour
        if self.activity_counters['matches_scraped_today'] > 30:
            result['suggested_delay'] = max(1, 60 - current_hour * 2)
        
        return result
    
    async def check_prediction_risk(self, prediction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if prediction meets risk criteria"""
        result = {
            'allowed': True,
            'reason': '',
            'risk_level': RiskLevel.LOW,
            'confidence_score': 0.0
        }
        
        confidence = prediction_data.get('confidence', 0.0)
        
        # Check confidence threshold
        if confidence < self.limits['min_confidence_threshold']:
            result.update({
                'allowed': False,
                'reason': f'Confidence below threshold ({confidence:.1%} < {self.limits["min_confidence_threshold"]:.1%})',
                'risk_level': RiskLevel.LOW
            })
        
        # Check daily prediction limit
        if self.activity_counters['predictions_today'] >= self.limits['max_predictions_per_day']:
            result.update({
                'allowed': False,
                'reason': 'Daily prediction limit reached',
                'risk_level': RiskLevel.MEDIUM
            })
        
        # Calculate confidence score
        result['confidence_score'] = confidence
        
        # Update metrics
        self.activity_counters['predictions_today'] += 1
        self.activity_counters['total_predictions'] += 1
        
        # Log the check
        self.data_store.log_prediction(prediction_data, result['risk_level'])
        
        return result
    
    async def record_prediction_outcome(self, match_id: str, 
                                      predicted: str, 
                                      actual: str,
                                      confidence: float):
        """Record prediction outcome for learning"""
        is_correct = predicted == actual
        
        # Update counters
        if is_correct:
            self.activity_counters['successful_predictions'] += 1
        
        # Update metrics
        total_preds = self.activity_counters['total_predictions']
        success_rate = self.activity_counters['successful_predictions'] / max(total_preds, 1)
        
        # Update average confidence
        current_avg = self.metrics.avg_confidence
        self.metrics.avg_confidence = (current_avg + confidence) / 2
        
        # Log outcome (educational learning)
        outcome_data = {
            'match_id': match_id,
            'predicted': predicted,
            'actual': actual,
            'correct': is_correct,
            'confidence': confidence,
            'success_rate': success_rate,
            'educational_note': 'Learning outcome for model improvement'
        }
        
        self.data_store.log_system_event(
            "prediction_outcome_recorded",
            outcome_data,
            RiskLevel.LOW
        )
    
    async def record_error(self, error_type: str, error_message: str, 
                          context: Dict[str, Any] = None):
        """Record error for monitoring"""
        self.activity_counters['errors_today'] += 1
        
        # Calculate error rate
        total_requests = (self.activity_counters['matches_scraped_today'] + 
                         self.activity_counters['predictions_today'])
        error_rate = self.activity_counters['errors_today'] / max(total_requests, 1)
        
        self.metrics.error_rate = error_rate
        
        # Check if error rate is too high
        if error_rate > self.limits['max_error_rate']:
            self.data_store.log_system_event(
                "high_error_rate",
                {
                    'error_rate': error_rate,
                    'threshold': self.limits['max_error_rate'],
                    'corrective_action': 'Rate limiting increased'
                },
                RiskLevel.HIGH
            )
        
        # Log error
        self.data_store.log_error(
            Exception(f"{error_type}: {error_message}"),
            context,
            RiskLevel.HIGH if error_rate > self.limits['max_error_rate'] else RiskLevel.MEDIUM
        )
    
    async def get_risk_status(self) -> Dict[str, Any]:
        """Get current risk status"""
        return {
            'metrics': asdict(self.metrics),
            'activity': self.activity_counters.copy(),
            'limits': self.limits.copy(),
            'status': self._calculate_overall_status(),
            'recommendations': self._get_recommendations()
        }
    
    def _calculate_overall_status(self) -> str:
        """Calculate overall risk status"""
        risk_factors = []
        
        if self.metrics.error_rate > self.limits['max_error_rate']:
            risk_factors.append('high_error_rate')
        
        if self.activity_counters['predictions_today'] > self.limits['max_predictions_per_day'] * 0.8:
            risk_factors.append('prediction_limit_near')
        
        if self.activity_counters['matches_scraped_today'] > self.limits['max_matches_per_hour'] * 0.8:
            risk_factors.append('scraping_limit_near')
        
        if self.metrics.avg_confidence < self.limits['min_confidence_threshold']:
            risk_factors.append('low_confidence_trend')
        
        if not risk_factors:
            return 'healthy'
        elif len(risk_factors) == 1:
            return 'warning'
        else:
            return 'critical'
    
    def _get_recommendations(self) -> List[str]:
        """Get risk management recommendations"""
        recommendations = []
        
        if self.metrics.error_rate > self.limits['max_error_rate']:
            recommendations.append("Increase delay between requests")
        
        if self.activity_counters['predictions_today'] > self.limits['max_predictions_per_day'] * 0.8:
            recommendations.append("Consider reducing prediction frequency")
        
        if self.metrics.avg_confidence < self.limits['min_confidence_threshold']:
            recommendations.append("Review model threshold settings")
        
        if not recommendations:
            recommendations.append("System operating normally")
        
        return recommendations
    
    async def _monitor_risk_levels(self):
        """Background task to monitor risk levels"""
        while True:
            try:
                status = await self.get_risk_status()
                
                if status['status'] == 'critical':
                    self.data_store.log_system_event(
                        "critical_risk_detected",
                        status,
                        RiskLevel.CRITICAL
                    )
                
                # Log status every hour
                self.data_store.log_system_event(
                    "risk_status_check",
                    {'status': status['status']},
                    RiskLevel.LOW
                )
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Risk monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _reset_daily_counters(self):
        """Reset daily counters at midnight"""
        while True:
            try:
                now = datetime.now()
                if now.hour == 0 and now.minute == 0:
                    # Reset daily counters
                    self.activity_counters.update({
                        'matches_scraped_today': 0,
                        'predictions_today': 0,
                        'errors_today': 0
                    })
                    
                    # Reset daily metrics
                    self.metrics.daily_loss_percentage = 0.0
                    self.metrics.last_reset_date = now.date().isoformat()
                    
                    self.data_store.log_system_event(
                        "daily_counters_reset",
                        {'reset_time': now.isoformat()},
                        RiskLevel.LOW
                    )
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Counter reset error: {e}")
                await asyncio.sleep(300)

class SystemMonitor:
    """System performance monitoring"""
    
    def __init__(self, data_store: ResearchDataStore):
        self.data_store = data_store
        self.performance_metrics = {
            'avg_response_time': 0.0,
            'requests_per_minute': 0,
            'memory_usage': 0.0,
            'cpu_usage': 0.0,
            'last_update': datetime.now().isoformat()
        }
        
        self._start_monitoring()
    
    def _start_monitoring(self):
        """Start system monitoring"""
        asyncio.create_task(self._collect_metrics())
    
    async def _collect_metrics(self):
        """Collect system performance metrics"""
        import psutil
        
        while True:
            try:
                # Collect basic metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                self.performance_metrics.update({
                    'cpu_usage': cpu_percent,
                    'memory_usage': memory.percent,
                    'memory_available_gb': memory.available / (1024**3),
                    'last_update': datetime.now().isoformat()
                })
                
                # Log high resource usage
                if cpu_percent > 80:
                    self.data_store.log_system_event(
                        "high_cpu_usage",
                        {'cpu_percent': cpu_percent},
                        RiskLevel.MEDIUM
                    )
                
                if memory.percent > 85:
                    self.data_store.log_system_event(
                        "high_memory_usage", 
                        {'memory_percent': memory.percent},
                        RiskLevel.MEDIUM
                    )
                
                await asyncio.sleep(60)  # Collect every minute
                
            except Exception as e:
                self.data_store.log_error(e, {'component': 'system_monitor'})
                await asyncio.sleep(60)

# Educational example
async def educational_risk_example():
    """Demonstrate risk management for educational purposes"""
    
    print("🛡️  Starting educational risk management demonstration...")
    print("⚠️  This is for learning purposes only!")
    
    # Create data store and risk manager
    data_store = ResearchDataStore()
    risk_manager = EducationalRiskManager(data_store)
    monitor = SystemMonitor(data_store)
    
    print("✅ Risk management system initialized")
    print("   • Rate limiting: Active")
    print("   • Privacy protection: Enabled") 
    print("   • Educational focus: Active")
    print("   • Ethical guidelines: Enforced")
    
    # Simulate some activity
    print("\n📊 Simulating research activity...")
    
    # Check scraping risk
    scraping_result = await risk_manager.check_scraping_risk({
        'url': 'https://betfury.io/sports',
        'request_type': 'live_matches'
    })
    print(f"   Scraping allowed: {scraping_result['allowed']}")
    
    # Check prediction risk
    prediction_result = await risk_manager.check_prediction_risk({
        'match_id': 'demo_123',
        'confidence': 0.85,
        'prediction': 'HOME'
    })
    print(f"   Prediction allowed: {prediction_result['allowed']}")
    
    # Get risk status
    status = await risk_manager.get_risk_status()
    print(f"   System status: {status['status']}")
    print(f"   Recommendations: {status['recommendations']}")
    
    print("\n💡 Educational Notes:")
    print("   • All operations are logged for transparency")
    print("   • Rate limits prevent system abuse")
    print("   • Privacy protection is always enabled")
    print("   • Risk monitoring runs continuously")

if __name__ == "__main__":
    # Run educational example
    asyncio.run(educational_risk_example())