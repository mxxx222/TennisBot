#!/usr/bin/env python3
"""
📊 ITF ROI TRACKER
==================

Integrates ITF strategies into Live Stats Dashboard.
Tracks ROI per strategy (Momentum Shift, Underdog Upset, etc.).
Adds to Strategy Matrix structure.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class ITFROITracker:
    """Tracks ROI for ITF strategies"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ITF ROI Tracker
        
        Args:
            config: Configuration dict
        """
        self.config = config or {}
        self.strategies = [
            'momentum_shift',
            'underdog_upset',
            'retirement_pattern',
        ]
        
        # Strategy performance tracking
        self.strategy_stats: Dict[str, Dict[str, Any]] = {}
        
        logger.info("📊 ITF ROI Tracker initialized")
    
    def update_strategy_performance(self, strategy_name: str, result: Dict[str, Any]):
        """
        Update performance metrics for a strategy
        
        Args:
            strategy_name: Strategy name
            result: Result dictionary with bets, wins, roi, etc.
        """
        if strategy_name not in self.strategy_stats:
            self.strategy_stats[strategy_name] = {
                'total_bets': 0,
                'wins': 0,
                'losses': 0,
                'total_stake': 0.0,
                'total_profit': 0.0,
                'roi': 0.0,
                'win_rate': 0.0,
                'last_updated': datetime.now().isoformat(),
            }
        
        stats = self.strategy_stats[strategy_name]
        
        # Update metrics
        stats['total_bets'] += result.get('total_bets', 0)
        stats['wins'] += result.get('wins', 0)
        stats['losses'] += result.get('losses', 0)
        stats['total_stake'] += result.get('total_stake', 0.0)
        stats['total_profit'] += result.get('total_profit', 0.0)
        
        # Recalculate ROI and win rate
        if stats['total_stake'] > 0:
            stats['roi'] = (stats['total_profit'] / stats['total_stake']) * 100
        
        if stats['total_bets'] > 0:
            stats['win_rate'] = (stats['wins'] / stats['total_bets']) * 100
        
        stats['last_updated'] = datetime.now().isoformat()
        
        logger.info(f"📊 Updated {strategy_name}: ROI={stats['roi']:.2f}%, Win Rate={stats['win_rate']:.1f}%")
    
    def get_strategy_matrix(self) -> Dict[str, Any]:
        """
        Get strategy performance matrix
        
        Returns:
            Strategy matrix dictionary
        """
        matrix = {
            'timestamp': datetime.now().isoformat(),
            'strategies': {}
        }
        
        for strategy_name, stats in self.strategy_stats.items():
            matrix['strategies'][strategy_name] = {
                'total_bets': stats['total_bets'],
                'wins': stats['wins'],
                'losses': stats['losses'],
                'total_stake': stats['total_stake'],
                'total_profit': stats['total_profit'],
                'roi': stats['roi'],
                'win_rate': stats['win_rate'],
                'last_updated': stats['last_updated'],
            }
        
        return matrix
    
    def export_to_notion(self, notion_updater) -> bool:
        """
        Export strategy matrix to Notion Live Stats Dashboard
        
        Args:
            notion_updater: Notion updater instance
            
        Returns:
            True if successful
        """
        # TODO: Implement Notion export
        # Would update Live Stats Dashboard with strategy performance
        logger.info("📊 Strategy matrix ready for Notion export")
        return True
    
    def export_to_json(self, filepath: Optional[str] = None):
        """
        Export strategy matrix to JSON file
        
        Args:
            filepath: Output file path (optional)
        """
        if not filepath:
            filepath = Path(__file__).parent.parent.parent / 'data' / f'itf_roi_matrix_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        matrix = self.get_strategy_matrix()
        
        with open(filepath, 'w') as f:
            json.dump(matrix, f, indent=2)
        
        logger.info(f"✅ Exported ROI matrix to {filepath}")


def main():
    """Test ITF ROI Tracker"""
    print("📊 ITF ROI TRACKER TEST")
    print("=" * 50)
    
    tracker = ITFROITracker()
    
    # Test updating strategy performance
    result = {
        'total_bets': 10,
        'wins': 7,
        'losses': 3,
        'total_stake': 100.0,
        'total_profit': 25.0,
    }
    
    tracker.update_strategy_performance('momentum_shift', result)
    
    matrix = tracker.get_strategy_matrix()
    print(f"\n📊 Strategy Matrix:")
    for name, stats in matrix['strategies'].items():
        print(f"\n   {name}:")
        print(f"      ROI: {stats['roi']:.2f}%")
        print(f"      Win Rate: {stats['win_rate']:.1f}%")
        print(f"      Total Bets: {stats['total_bets']}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()

