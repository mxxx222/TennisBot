#!/usr/bin/env python3
"""
A/B Testing Framework
=====================

Test multiple strategies in parallel.
Track performance per strategy.
Automatic strategy selection.

This is part of Layer 5: Continuous Learning.
"""

import logging
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


@dataclass
class StrategyResult:
    """Result for a single strategy"""
    strategy_id: str
    matches_played: int
    wins: int
    losses: int
    win_rate: float
    roi: float
    total_stake: float
    total_return: float
    start_date: str
    end_date: str


class ABTestingFramework:
    """A/B testing framework for strategy comparison"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize A/B testing framework
        
        Args:
            db_path: Path to A/B testing database
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / 'data' / 'ab_testing.db'
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        logger.info("✅ A/B Testing Framework initialized")
    
    def _init_database(self):
        """Initialize A/B testing database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Strategies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                strategy_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                config_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id TEXT NOT NULL,
                match_id TEXT,
                prediction_json TEXT,
                actual_result TEXT,
                stake REAL,
                return_amount REAL,
                profit REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id)
            )
        """)
        
        # Performance summary table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_summary (
                strategy_id TEXT PRIMARY KEY,
                matches_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                win_rate REAL DEFAULT 0.0,
                roi REAL DEFAULT 0.0,
                total_stake REAL DEFAULT 0.0,
                total_return REAL DEFAULT 0.0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def register_strategy(self,
                         strategy_id: str,
                         name: str,
                         description: str = "",
                         config: Optional[Dict] = None) -> bool:
        """
        Register a new strategy for A/B testing
        
        Args:
            strategy_id: Unique strategy identifier
            name: Strategy name
            description: Strategy description
            config: Strategy configuration dictionary
            
        Returns:
            True if successful
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            config_json = json.dumps(config) if config else "{}"
            
            cursor.execute("""
                INSERT OR REPLACE INTO strategies (strategy_id, name, description, config_json)
                VALUES (?, ?, ?, ?)
            """, (strategy_id, name, description, config_json))
            
            # Initialize performance summary
            cursor.execute("""
                INSERT OR IGNORE INTO performance_summary (strategy_id)
                VALUES (?)
            """, (strategy_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Registered strategy: {strategy_id} ({name})")
            return True
            
        except Exception as e:
            logger.error(f"Error registering strategy: {e}")
            return False
    
    def record_result(self,
                     strategy_id: str,
                     match_id: str,
                     prediction: Dict[str, Any],
                     actual_result: str,
                     stake: float,
                     return_amount: float) -> bool:
        """
        Record a strategy result
        
        Args:
            strategy_id: Strategy identifier
            match_id: Match identifier
            prediction: Prediction dictionary
            actual_result: Actual result ('win' or 'loss')
            stake: Stake amount
            return_amount: Return amount
            
        Returns:
            True if successful
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            profit = return_amount - stake
            prediction_json = json.dumps(prediction)
            
            cursor.execute("""
                INSERT INTO strategy_results 
                (strategy_id, match_id, prediction_json, actual_result, stake, return_amount, profit)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (strategy_id, match_id, prediction_json, actual_result, stake, return_amount, profit))
            
            # Update performance summary
            self._update_performance_summary(strategy_id, actual_result == 'win', stake, return_amount)
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording result: {e}")
            return False
    
    def _update_performance_summary(self, strategy_id: str, won: bool, stake: float, return_amount: float):
        """Update performance summary for a strategy"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Get current summary
        cursor.execute("""
            SELECT matches_played, wins, losses, total_stake, total_return
            FROM performance_summary WHERE strategy_id = ?
        """, (strategy_id,))
        
        row = cursor.fetchone()
        if row:
            matches_played, wins, losses, total_stake, total_return = row
        else:
            matches_played, wins, losses, total_stake, total_return = 0, 0, 0, 0.0, 0.0
        
        # Update
        matches_played += 1
        if won:
            wins += 1
        else:
            losses += 1
        
        total_stake += stake
        total_return += return_amount
        
        win_rate = wins / matches_played if matches_played > 0 else 0.0
        roi = (total_return - total_stake) / total_stake if total_stake > 0 else 0.0
        
        cursor.execute("""
            UPDATE performance_summary
            SET matches_played = ?, wins = ?, losses = ?, win_rate = ?, 
                roi = ?, total_stake = ?, total_return = ?, last_updated = ?
            WHERE strategy_id = ?
        """, (matches_played, wins, losses, win_rate, roi, total_stake, total_return,
              datetime.now().isoformat(), strategy_id))
        
        conn.commit()
        conn.close()
    
    def get_strategy_performance(self, strategy_id: str, days: int = 30) -> Optional[StrategyResult]:
        """
        Get performance for a strategy
        
        Args:
            strategy_id: Strategy identifier
            days: Number of days to look back
            
        Returns:
            StrategyResult object or None
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute("""
                SELECT matches_played, wins, losses, win_rate, roi, 
                       total_stake, total_return, last_updated
                FROM performance_summary
                WHERE strategy_id = ?
            """, (strategy_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            matches_played, wins, losses, win_rate, roi, total_stake, total_return, last_updated = row
            
            return StrategyResult(
                strategy_id=strategy_id,
                matches_played=matches_played,
                wins=wins,
                losses=losses,
                win_rate=win_rate,
                roi=roi,
                total_stake=total_stake,
                total_return=total_return,
                start_date=cutoff_date,
                end_date=last_updated
            )
            
        except Exception as e:
            logger.error(f"Error getting strategy performance: {e}")
            return None
    
    def get_best_strategy(self, metric: str = 'roi') -> Optional[str]:
        """
        Get best performing strategy
        
        Args:
            metric: Metric to use ('roi' or 'win_rate')
            
        Returns:
            Strategy ID of best strategy or None
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            if metric == 'roi':
                cursor.execute("""
                    SELECT strategy_id FROM performance_summary
                    WHERE matches_played >= 10
                    ORDER BY roi DESC
                    LIMIT 1
                """)
            else:
                cursor.execute("""
                    SELECT strategy_id FROM performance_summary
                    WHERE matches_played >= 10
                    ORDER BY win_rate DESC
                    LIMIT 1
                """)
            
            row = cursor.fetchone()
            conn.close()
            
            return row[0] if row else None
            
        except Exception as e:
            logger.error(f"Error getting best strategy: {e}")
            return None
    
    def get_all_strategies(self) -> List[Dict[str, Any]]:
        """
        Get all registered strategies
        
        Returns:
            List of strategy dictionaries
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT s.*, p.matches_played, p.win_rate, p.roi
                FROM strategies s
                LEFT JOIN performance_summary p ON s.strategy_id = p.strategy_id
                WHERE s.is_active = 1
            """)
            
            rows = cursor.fetchall()
            strategies = [dict(row) for row in rows]
            
            conn.close()
            return strategies
            
        except Exception as e:
            logger.error(f"Error getting strategies: {e}")
            return []


def main():
    """Test A/B testing framework"""
    print("\n" + "="*80)
    print("🧪 TESTING A/B TESTING FRAMEWORK")
    print("="*80)
    
    framework = ABTestingFramework()
    
    # Register test strategies
    framework.register_strategy(
        'strategy_1',
        'Conservative (Odds 1.40-1.60)',
        'Conservative betting with lower odds',
        {'min_odds': 1.40, 'max_odds': 1.60}
    )
    
    framework.register_strategy(
        'strategy_2',
        'Moderate (Odds 1.50-1.80)',
        'Moderate betting with medium odds',
        {'min_odds': 1.50, 'max_odds': 1.80}
    )
    
    # Get all strategies
    strategies = framework.get_all_strategies()
    print(f"\n📊 Registered Strategies: {len(strategies)}")
    for strategy in strategies:
        print(f"   {strategy['name']}: {strategy.get('win_rate', 0):.1%} win rate, {strategy.get('roi', 0):.1%} ROI")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()

