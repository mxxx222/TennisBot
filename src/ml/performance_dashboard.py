#!/usr/bin/env python3
"""
Performance Dashboard
====================

Real-time metrics: win rate, ROI, model accuracy.
Feature importance visualization.
Model comparison charts.

This is part of Layer 5: Continuous Learning.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ml.data_collector import MatchResultsDB
from src.ml.meta_learner import MetaLearner
from src.ml.ab_testing import ABTestingFramework

logger = logging.getLogger(__name__)


class PerformanceDashboard:
    """Performance dashboard for monitoring ML system"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize performance dashboard
        
        Args:
            db_path: Path to databases
        """
        self.db = MatchResultsDB(db_path)
        self.meta_learner = MetaLearner()
        self.ab_testing = ABTestingFramework()
        
        logger.info("✅ Performance Dashboard initialized")
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get overall system metrics
        
        Returns:
            Dictionary with system metrics
        """
        total_matches = self.db.count_matches()
        total_results = self.db.count_results()
        
        return {
            'total_matches': total_matches,
            'total_results': total_results,
            'coverage': total_results / max(total_matches, 1),
            'last_updated': datetime.now().isoformat()
        }
    
    def get_model_metrics(self) -> Dict[str, Any]:
        """
        Get model performance metrics
        
        Returns:
            Dictionary with model metrics
        """
        return {
            'meta_learner_weights': self.meta_learner.weights,
            'model_accuracies': self.meta_learner.accuracies,
            'agreement_bonus': self.meta_learner.agreement_bonus
        }
    
    def get_strategy_metrics(self) -> List[Dict[str, Any]]:
        """
        Get A/B testing strategy metrics
        
        Returns:
            List of strategy metrics
        """
        strategies = self.ab_testing.get_all_strategies()
        
        metrics = []
        for strategy in strategies:
            performance = self.ab_testing.get_strategy_performance(strategy['strategy_id'])
            if performance:
                metrics.append({
                    'strategy_id': strategy['strategy_id'],
                    'name': strategy['name'],
                    'matches_played': performance.matches_played,
                    'win_rate': performance.win_rate,
                    'roi': performance.roi,
                    'total_stake': performance.total_stake,
                    'total_return': performance.total_return
                })
        
        return metrics
    
    def print_dashboard(self):
        """Print dashboard to console"""
        print("\n" + "=" * 80)
        print("📊 PERFORMANCE DASHBOARD")
        print("=" * 80)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # System metrics
        system_metrics = self.get_system_metrics()
        print("\n📈 System Metrics:")
        print(f"   Total Matches: {system_metrics['total_matches']}")
        print(f"   Total Results: {system_metrics['total_results']}")
        print(f"   Coverage: {system_metrics['coverage']:.1%}")
        
        # Model metrics
        model_metrics = self.get_model_metrics()
        print("\n🤖 Model Metrics:")
        print(f"   Meta-Learner Weights:")
        for model, weight in model_metrics['meta_learner_weights'].items():
            accuracy = model_metrics['model_accuracies'].get(model, 0)
            print(f"      {model.upper()}: {weight:.1%} (accuracy: {accuracy:.1%})")
        
        # Strategy metrics
        strategy_metrics = self.get_strategy_metrics()
        if strategy_metrics:
            print("\n🎯 Strategy Performance:")
            for strategy in strategy_metrics:
                print(f"   {strategy['name']}:")
                print(f"      Matches: {strategy['matches_played']}")
                print(f"      Win Rate: {strategy['win_rate']:.1%}")
                print(f"      ROI: {strategy['roi']:.1%}")
        else:
            print("\n🎯 Strategy Performance: No strategies registered yet")
        
        print("=" * 80)


def main():
    """Run performance dashboard"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Performance Dashboard')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    dashboard = PerformanceDashboard()
    
    if args.json:
        import json
        output = {
            'system_metrics': dashboard.get_system_metrics(),
            'model_metrics': dashboard.get_model_metrics(),
            'strategy_metrics': dashboard.get_strategy_metrics(),
            'timestamp': datetime.now().isoformat()
        }
        print(json.dumps(output, indent=2))
    else:
        dashboard.print_dashboard()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()

