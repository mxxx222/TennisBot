"""
Performance Tracker

Track capper performance over time
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class CapperPerformance:
    """Capper performance metrics"""
    username: str
    win_rate: float
    roi: float
    total_picks: int
    verified: bool
    followers: int
    engagement_rate: float
    last_updated: str

class PerformanceTracker:
    """Track performance of Twitter cappers"""
    
    def __init__(self):
        self.capper_performance: Dict[str, CapperPerformance] = {}
        self.pick_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        logger.info("✅ Performance Tracker initialized")
    
    def record_pick(
        self,
        username: str,
        pick: Dict[str, Any]
    ):
        """Record a pick from a capper"""
        pick_record = {
            'pick': pick,
            'timestamp': datetime.now().isoformat(),
            'outcome': None,
        }
        
        self.pick_history[username].append(pick_record)
        
        # Initialize performance if needed
        if username not in self.capper_performance:
            self.capper_performance[username] = CapperPerformance(
                username=username,
                win_rate=0.0,
                roi=0.0,
                total_picks=0,
                verified=False,
                followers=0,
                engagement_rate=0.0,
                last_updated=datetime.now().isoformat()
            )
        
        self.capper_performance[username].total_picks += 1
    
    def record_outcome(
        self,
        username: str,
        pick_id: str,
        won: bool
    ):
        """Record outcome of a pick"""
        if username not in self.pick_history:
            return
        
        for pick_record in self.pick_history[username]:
            if pick_record['pick'].get('pick_id') == pick_id:
                pick_record['outcome'] = 'won' if won else 'lost'
                break
        
        self._update_performance(username)
    
    def _update_performance(self, username: str):
        """Update performance metrics for a capper"""
        if username not in self.pick_history:
            return
        
        picks = self.pick_history[username]
        completed_picks = [p for p in picks if p['outcome'] is not None]
        
        if not completed_picks:
            return
        
        wins = sum(1 for p in completed_picks if p['outcome'] == 'won')
        total = len(completed_picks)
        
        win_rate = wins / total if total > 0 else 0.0
        roi = (wins / total - 0.5) * 2 if total > 0 else 0.0
        
        if username in self.capper_performance:
            self.capper_performance[username].win_rate = win_rate
            self.capper_performance[username].roi = roi
            self.capper_performance[username].last_updated = datetime.now().isoformat()
    
    def is_profitable_capper(self, username: str) -> bool:
        """Check if capper is profitable"""
        if username not in self.capper_performance:
            return False
        
        capper = self.capper_performance[username]
        
        from config.twitter_config import TwitterConfig
        min_win_rate = TwitterConfig.MIN_WIN_RATE
        
        return (
            capper.verified or
            (capper.win_rate >= min_win_rate and capper.total_picks >= 10)
        )
    
    def get_top_cappers(self, limit: int = 10) -> List[CapperPerformance]:
        """Get top performing cappers"""
        profitable = [
            c for c in self.capper_performance.values()
            if self.is_profitable_capper(c.username)
        ]
        
        # Sort by win rate and ROI
        profitable.sort(key=lambda x: (x.win_rate, x.roi), reverse=True)
        
        return profitable[:limit]

