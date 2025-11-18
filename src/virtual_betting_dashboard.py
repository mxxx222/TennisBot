#!/usr/bin/env python3
"""
📊 VIRTUAL BETTING DASHBOARD
============================
Monitoring dashboard and reporting system for virtual betting and ML calibration.
Provides daily/weekly reports, performance metrics, and calibration analysis.

Author: TennisBot Dashboard System
Version: 1.0.0
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys

# Add project paths
sys.path.append(str(Path(__file__).parent.parent))

from src.virtual_betting_tracker import VirtualBettingTracker
from src.ml_calibration_engine import CalibrationEngine
from src.ml_auto_retrainer import MLAutoRetrainer

logger = logging.getLogger(__name__)

class VirtualBettingDashboard:
    """Dashboard for monitoring virtual betting and calibration"""
    
    def __init__(
        self,
        virtual_tracker: VirtualBettingTracker,
        calibration_engine: CalibrationEngine,
        auto_retrainer: Optional[MLAutoRetrainer] = None
    ):
        """
        Initialize dashboard
        
        Args:
            virtual_tracker: VirtualBettingTracker instance
            calibration_engine: CalibrationEngine instance
            auto_retrainer: Optional MLAutoRetrainer instance
        """
        self.tracker = virtual_tracker
        self.calibration_engine = calibration_engine
        self.auto_retrainer = auto_retrainer
        
        logger.info("✅ VirtualBettingDashboard initialized")
    
    def get_daily_report(self, date: datetime = None) -> Dict[str, Any]:
        """
        Generate daily performance report
        
        Args:
            date: Date for report (defaults to today)
            
        Returns:
            Dictionary with daily report data
        """
        if date is None:
            date = datetime.now()
        
        try:
            stats = self.tracker.get_statistics()
            calibration = self.calibration_engine.analyze_calibration()
            
            # Get pending bets count
            pending_bets = self.tracker.get_pending_bets()
            
            # Calculate daily metrics
            daily_metrics = self._calculate_daily_metrics(date)
            
            return {
                'report_date': date.strftime('%Y-%m-%d'),
                'generated_at': datetime.now().isoformat(),
                'virtual_betting_stats': stats,
                'pending_bets': len(pending_bets),
                'calibration_summary': {
                    'status': calibration.get('status'),
                    'total_samples': calibration.get('total_samples', 0),
                    'overall_accuracy': calibration.get('overall_metrics', {}).get('overall_accuracy', 0),
                    'calibration_gap': calibration.get('overall_metrics', {}).get('calibration_gap', 0),
                    'brier_score': calibration.get('brier_score', 0)
                },
                'daily_metrics': daily_metrics,
                'recommendations': calibration.get('recommendations', [])
            }
        except Exception as e:
            logger.error(f"❌ Error generating daily report: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_weekly_report(self, week_start: datetime = None) -> Dict[str, Any]:
        """
        Generate weekly performance report
        
        Args:
            week_start: Start of week (defaults to Monday of current week)
            
        Returns:
            Dictionary with weekly report data
        """
        if week_start is None:
            # Get Monday of current week
            today = datetime.now()
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday)
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        week_end = week_start + timedelta(days=7)
        
        try:
            # Get daily reports for the week
            daily_reports = []
            current_date = week_start
            while current_date < week_end:
                daily_reports.append(self.get_daily_report(current_date))
                current_date += timedelta(days=1)
            
            # Aggregate weekly metrics
            weekly_stats = self._aggregate_weekly_metrics(daily_reports)
            
            # Get calibration analysis
            calibration = self.calibration_engine.analyze_calibration()
            surface_analysis = self.calibration_engine.get_calibration_by_surface()
            
            return {
                'week_start': week_start.strftime('%Y-%m-%d'),
                'week_end': (week_end - timedelta(days=1)).strftime('%Y-%m-%d'),
                'generated_at': datetime.now().isoformat(),
                'weekly_stats': weekly_stats,
                'daily_reports': daily_reports,
                'calibration_analysis': calibration,
                'surface_analysis': surface_analysis,
                'retraining_status': self._get_retraining_status()
            }
        except Exception as e:
            logger.error(f"❌ Error generating weekly report: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _calculate_daily_metrics(self, date: datetime) -> Dict[str, Any]:
        """Calculate daily-specific metrics"""
        try:
            import sqlite3
            
            date_str = date.strftime('%Y-%m-%d')
            
            with sqlite3.connect(self.tracker.db_path) as conn:
                cursor = conn.cursor()
                
                # Bets placed today
                cursor.execute('''
                    SELECT COUNT(*) FROM virtual_bets
                    WHERE DATE(timestamp) = ?
                ''', (date_str,))
                bets_placed = cursor.fetchone()[0]
                
                # Bets resolved today
                cursor.execute('''
                    SELECT COUNT(*) FROM virtual_bets
                    WHERE DATE(updated_at) = ? AND status IN ('won', 'lost')
                ''', (date_str,))
                bets_resolved = cursor.fetchone()[0]
                
                # P&L today
                cursor.execute('''
                    SELECT COALESCE(SUM(profit_loss), 0) FROM virtual_bets
                    WHERE DATE(updated_at) = ? AND profit_loss IS NOT NULL
                ''', (date_str,))
                daily_pl = cursor.fetchone()[0] or 0.0
                
                # Win rate today
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) as won
                    FROM virtual_bets
                    WHERE DATE(updated_at) = ? AND status IN ('won', 'lost')
                ''', (date_str,))
                result = cursor.fetchone()
                total_resolved = result[0] or 0
                won = result[1] or 0
                win_rate = (won / total_resolved * 100) if total_resolved > 0 else 0.0
                
                return {
                    'bets_placed': bets_placed,
                    'bets_resolved': bets_resolved,
                    'daily_profit_loss': round(daily_pl, 2),
                    'win_rate': round(win_rate, 2),
                    'wins': won,
                    'losses': total_resolved - won
                }
        except Exception as e:
            logger.error(f"❌ Error calculating daily metrics: {e}")
            return {}
    
    def _aggregate_weekly_metrics(
        self,
        daily_reports: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate metrics across the week"""
        try:
            total_bets_placed = sum(
                r.get('daily_metrics', {}).get('bets_placed', 0)
                for r in daily_reports
            )
            
            total_bets_resolved = sum(
                r.get('daily_metrics', {}).get('bets_resolved', 0)
                for r in daily_reports
            )
            
            total_pl = sum(
                r.get('daily_metrics', {}).get('daily_profit_loss', 0)
                for r in daily_reports
            )
            
            total_wins = sum(
                r.get('daily_metrics', {}).get('wins', 0)
                for r in daily_reports
            )
            
            total_losses = sum(
                r.get('daily_metrics', {}).get('losses', 0)
                for r in daily_reports
            )
            
            weekly_win_rate = (
                (total_wins / (total_wins + total_losses) * 100)
                if (total_wins + total_losses) > 0 else 0.0
            )
            
            # Get overall stats
            overall_stats = self.tracker.get_statistics()
            
            return {
                'total_bets_placed': total_bets_placed,
                'total_bets_resolved': total_bets_resolved,
                'weekly_profit_loss': round(total_pl, 2),
                'weekly_win_rate': round(weekly_win_rate, 2),
                'total_wins': total_wins,
                'total_losses': total_losses,
                'current_bankroll': overall_stats.get('current_bankroll', 0),
                'bankroll_change': overall_stats.get('bankroll_change', 0),
                'bankroll_change_pct': overall_stats.get('bankroll_change_pct', 0)
            }
        except Exception as e:
            logger.error(f"❌ Error aggregating weekly metrics: {e}")
            return {}
    
    def _get_retraining_status(self) -> Dict[str, Any]:
        """Get status of auto-retraining"""
        if not self.auto_retrainer:
            return {'status': 'not_configured'}
        
        try:
            should_retrain = self.auto_retrainer.should_retrain()
            last_retrain = self.auto_retrainer.last_retrain_date
            
            return {
                'should_retrain': should_retrain,
                'last_retrain_date': last_retrain.isoformat() if last_retrain else None,
                'min_samples_required': self.auto_retrainer.min_samples_for_retrain,
                'retrain_interval_days': self.auto_retrainer.retrain_interval_days
            }
        except Exception as e:
            logger.error(f"❌ Error getting retraining status: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def export_report(
        self,
        report_type: str = 'daily',
        output_path: str = None
    ) -> str:
        """
        Export report to JSON file
        
        Args:
            report_type: 'daily' or 'weekly'
            output_path: Output file path (auto-generated if None)
            
        Returns:
            Path to exported file
        """
        if output_path is None:
            data_dir = Path(__file__).parent.parent / 'data' / 'reports'
            data_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = str(data_dir / f'{report_type}_report_{timestamp}.json')
        
        if report_type == 'daily':
            report = self.get_daily_report()
        elif report_type == 'weekly':
            report = self.get_weekly_report()
        else:
            raise ValueError(f"Invalid report_type: {report_type}")
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"✅ {report_type.capitalize()} report exported to {output_path}")
        return output_path
    
    def print_summary(self):
        """Print a summary of current status"""
        print("\n" + "="*80)
        print("📊 VIRTUAL BETTING & ML CALIBRATION SUMMARY")
        print("="*80)
        
        # Virtual betting stats
        stats = self.tracker.get_statistics()
        print(f"\n💰 Virtual Betting Stats:")
        print(f"  Total Bets: {stats.get('total_bets', 0)}")
        print(f"  Pending: {stats.get('pending_bets', 0)}")
        print(f"  Won: {stats.get('won_bets', 0)}")
        print(f"  Lost: {stats.get('lost_bets', 0)}")
        print(f"  Win Rate: {stats.get('win_rate', 0):.2f}%")
        print(f"  Total P&L: {stats.get('total_profit_loss', 0):.2f}")
        print(f"  ROI: {stats.get('roi', 0):.2f}%")
        print(f"  Bankroll: {stats.get('current_bankroll', 0):.2f} "
              f"({stats.get('bankroll_change_pct', 0):+.2f}%)")
        
        # Calibration summary
        calibration = self.calibration_engine.analyze_calibration()
        if calibration.get('status') == 'success':
            overall = calibration.get('overall_metrics', {})
            print(f"\n📊 Calibration Analysis:")
            print(f"  Total Samples: {calibration.get('total_samples', 0)}")
            print(f"  Overall Accuracy: {overall.get('overall_accuracy', 0):.2%}")
            print(f"  Avg Confidence: {overall.get('avg_confidence', 0):.2%}")
            print(f"  Calibration Gap: {overall.get('calibration_gap', 0):.4f}")
            print(f"  Brier Score: {calibration.get('brier_score', 0):.4f}")
            print(f"  Reliability: {overall.get('reliability', 0):.2%}")
        
        # Retraining status
        if self.auto_retrainer:
            retrain_status = self._get_retraining_status()
            print(f"\n🔄 Auto-Retraining Status:")
            print(f"  Should Retrain: {retrain_status.get('should_retrain', False)}")
            if retrain_status.get('last_retrain_date'):
                print(f"  Last Retrain: {retrain_status['last_retrain_date']}")
            print(f"  Min Samples Required: {retrain_status.get('min_samples_required', 0)}")
        
        print("\n" + "="*80 + "\n")

