#!/usr/bin/env python3
"""
Alert System
============

Notify on model performance degradation.
Alert on significant feature shifts.
Weekly performance reports.

This is part of Layer 5: Continuous Learning.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ml.performance_dashboard import PerformanceDashboard
from src.ml.meta_learner import MetaLearner

logger = logging.getLogger(__name__)


class AlertSystem:
    """Alert system for performance monitoring"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize alert system
        
        Args:
            db_path: Path to databases
        """
        self.dashboard = PerformanceDashboard(db_path)
        self.meta_learner = MetaLearner()
        
        # Alert thresholds
        self.min_win_rate = 0.55  # Alert if win rate drops below 55%
        self.min_roi = 0.10        # Alert if ROI drops below 10%
        self.max_accuracy_drop = 0.10  # Alert if accuracy drops by 10%
        
        logger.info("✅ Alert System initialized")
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """
        Check for alerts
        
        Returns:
            List of alert dictionaries
        """
        alerts = []
        
        # Check model accuracy degradation
        model_metrics = self.dashboard.get_model_metrics()
        for model, accuracy in model_metrics['model_accuracies'].items():
            # Compare with baseline (would need historical tracking)
            # For now, check if accuracy is below threshold
            if accuracy < 0.50:
                alerts.append({
                    'type': 'model_degradation',
                    'severity': 'high',
                    'model': model,
                    'message': f'{model.upper()} accuracy is below 50%: {accuracy:.1%}',
                    'timestamp': datetime.now().isoformat()
                })
        
        # Check strategy performance
        strategy_metrics = self.dashboard.get_strategy_metrics()
        for strategy in strategy_metrics:
            if strategy['matches_played'] >= 10:  # Only check strategies with enough data
                if strategy['win_rate'] < self.min_win_rate:
                    alerts.append({
                        'type': 'low_win_rate',
                        'severity': 'medium',
                        'strategy': strategy['name'],
                        'win_rate': strategy['win_rate'],
                        'message': f"Strategy '{strategy['name']}' win rate is {strategy['win_rate']:.1%} (below {self.min_win_rate:.0%})",
                        'timestamp': datetime.now().isoformat()
                    })
                
                if strategy['roi'] < self.min_roi:
                    alerts.append({
                        'type': 'low_roi',
                        'severity': 'high',
                        'strategy': strategy['name'],
                        'roi': strategy['roi'],
                        'message': f"Strategy '{strategy['name']}' ROI is {strategy['roi']:.1%} (below {self.min_roi:.0%})",
                        'timestamp': datetime.now().isoformat()
                    })
        
        # Check system coverage
        system_metrics = self.dashboard.get_system_metrics()
        if system_metrics['coverage'] < 0.30:  # Less than 30% of matches have results
            alerts.append({
                'type': 'low_coverage',
                'severity': 'medium',
                'coverage': system_metrics['coverage'],
                'message': f"Match result coverage is {system_metrics['coverage']:.1%} (need more results for training)",
                'timestamp': datetime.now().isoformat()
            })
        
        return alerts
    
    def send_alerts(self, alerts: List[Dict[str, Any]]):
        """
        Send alerts (console output for now, could extend to email/Telegram)
        
        Args:
            alerts: List of alert dictionaries
        """
        if not alerts:
            logger.info("✅ No alerts to send")
            return
        
        logger.warning("=" * 80)
        logger.warning("⚠️ ALERTS DETECTED")
        logger.warning("=" * 80)
        
        for alert in alerts:
            severity_icon = "🔴" if alert['severity'] == 'high' else "🟡"
            logger.warning(f"{severity_icon} [{alert['type'].upper()}] {alert['message']}")
        
        logger.warning("=" * 80)
    
    def generate_weekly_report(self) -> Dict[str, Any]:
        """
        Generate weekly performance report
        
        Returns:
            Dictionary with weekly report
        """
        system_metrics = self.dashboard.get_system_metrics()
        model_metrics = self.dashboard.get_model_metrics()
        strategy_metrics = self.dashboard.get_strategy_metrics()
        
        # Get best strategy
        best_strategy = None
        if strategy_metrics:
            best_strategy = max(strategy_metrics, key=lambda s: s.get('roi', 0))
        
        report = {
            'week_start': (datetime.now() - timedelta(days=7)).isoformat(),
            'week_end': datetime.now().isoformat(),
            'system_metrics': system_metrics,
            'model_metrics': model_metrics,
            'strategy_metrics': strategy_metrics,
            'best_strategy': best_strategy,
            'alerts': self.check_alerts()
        }
        
        return report
    
    def print_weekly_report(self):
        """Print weekly report to console"""
        report = self.generate_weekly_report()
        
        print("\n" + "=" * 80)
        print("📊 WEEKLY PERFORMANCE REPORT")
        print("=" * 80)
        print(f"📅 Week: {report['week_start']} to {report['week_end']}")
        
        # System summary
        print("\n📈 System Summary:")
        print(f"   Total Matches: {report['system_metrics']['total_matches']}")
        print(f"   Results Coverage: {report['system_metrics']['coverage']:.1%}")
        
        # Best strategy
        if report['best_strategy']:
            print(f"\n🏆 Best Strategy: {report['best_strategy']['name']}")
            print(f"   Win Rate: {report['best_strategy']['win_rate']:.1%}")
            print(f"   ROI: {report['best_strategy']['roi']:.1%}")
        
        # Alerts
        if report['alerts']:
            print(f"\n⚠️ Alerts: {len(report['alerts'])}")
            for alert in report['alerts']:
                print(f"   - {alert['message']}")
        else:
            print("\n✅ No alerts")
        
        print("=" * 80)


def main():
    """Run alert system"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Alert System')
    parser.add_argument('--check', action='store_true', help='Check for alerts')
    parser.add_argument('--weekly-report', action='store_true', help='Generate weekly report')
    
    args = parser.parse_args()
    
    alert_system = AlertSystem()
    
    if args.weekly_report:
        alert_system.print_weekly_report()
    else:
        alerts = alert_system.check_alerts()
        alert_system.send_alerts(alerts)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()

