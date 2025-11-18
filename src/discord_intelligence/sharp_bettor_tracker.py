"""
Sharp Bettor Tracker

Track verified sharp bettors and their picks
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class SharpBettor:
    """Sharp bettor profile"""
    user_id: int
    username: str
    win_rate: float
    roi: float
    total_picks: int
    verified: bool
    last_updated: str

@dataclass
class SharpPick:
    """Pick from a sharp bettor"""
    pick_id: str
    user_id: int
    username: str
    match_info: Dict[str, str]
    selection: str
    reasoning: Optional[str]
    timestamp: str
    channel: str
    server: str

class SharpBettorTracker:
    """Track and validate sharp bettors"""
    
    def __init__(self):
        self.sharp_bettors: Dict[int, SharpBettor] = {}
        self.pick_history: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        self.performance_cache = {}
        
        logger.info("✅ Sharp Bettor Tracker initialized")
    
    def register_sharp_bettor(
        self,
        user_id: int,
        username: str,
        verified: bool = False
    ):
        """Register a sharp bettor"""
        if user_id not in self.sharp_bettors:
            self.sharp_bettors[user_id] = SharpBettor(
                user_id=user_id,
                username=username,
                win_rate=0.0,
                roi=0.0,
                total_picks=0,
                verified=verified,
                last_updated=datetime.now().isoformat()
            )
            logger.info(f"✅ Registered sharp bettor: {username}")
    
    def record_pick(
        self,
        user_id: int,
        pick: Dict[str, Any]
    ):
        """Record a pick from a sharp bettor"""
        if user_id not in self.sharp_bettors:
            return
        
        pick_record = {
            'pick': pick,
            'timestamp': datetime.now().isoformat(),
            'outcome': None,  # Will be updated when result is known
        }
        
        self.pick_history[user_id].append(pick_record)
        self.sharp_bettors[user_id].total_picks += 1
        
        # Update performance periodically
        if len(self.pick_history[user_id]) % 10 == 0:
            self._update_performance(user_id)
    
    def record_outcome(
        self,
        user_id: int,
        pick_id: str,
        won: bool
    ):
        """Record outcome of a pick"""
        if user_id not in self.pick_history:
            return
        
        for pick_record in self.pick_history[user_id]:
            if pick_record['pick'].get('pick_id') == pick_id:
                pick_record['outcome'] = 'won' if won else 'lost'
                break
        
        self._update_performance(user_id)
    
    def _update_performance(self, user_id: int):
        """Update performance metrics for a sharp bettor"""
        if user_id not in self.pick_history:
            return
        
        picks = self.pick_history[user_id]
        completed_picks = [p for p in picks if p['outcome'] is not None]
        
        if not completed_picks:
            return
        
        wins = sum(1 for p in completed_picks if p['outcome'] == 'won')
        total = len(completed_picks)
        
        win_rate = wins / total if total > 0 else 0.0
        
        # Simple ROI calculation (would need stake/odds data for accurate ROI)
        roi = (wins / total - 0.5) * 2 if total > 0 else 0.0
        
        if user_id in self.sharp_bettors:
            self.sharp_bettors[user_id].win_rate = win_rate
            self.sharp_bettors[user_id].roi = roi
            self.sharp_bettors[user_id].last_updated = datetime.now().isoformat()
    
    def is_verified_sharp(self, user_id: int) -> bool:
        """Check if user is a verified sharp bettor"""
        if user_id not in self.sharp_bettors:
            return False
        
        bettor = self.sharp_bettors[user_id]
        
        # Check minimum requirements
        from config.discord_config import DiscordConfig
        min_win_rate = DiscordConfig.MIN_WIN_RATE
        min_roi = DiscordConfig.MIN_ROI
        
        return (
            bettor.verified or
            (bettor.win_rate >= min_win_rate and bettor.roi >= min_roi and bettor.total_picks >= 10)
        )
    
    def get_sharp_picks(
        self,
        hours_back: int = 24
    ) -> List[SharpPick]:
        """Get recent picks from verified sharps"""
        sharp_picks = []
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        for user_id, picks in self.pick_history.items():
            if not self.is_verified_sharp(user_id):
                continue
            
            bettor = self.sharp_bettors[user_id]
            
            for pick_record in picks:
                pick_time = datetime.fromisoformat(pick_record['timestamp'])
                if pick_time >= cutoff_time:
                    pick = pick_record['pick']
                    sharp_pick = SharpPick(
                        pick_id=pick.get('pick_id', ''),
                        user_id=user_id,
                        username=bettor.username,
                        match_info=pick.get('match_info', {}),
                        selection=pick.get('selection', ''),
                        reasoning=pick.get('reasoning'),
                        timestamp=pick_record['timestamp'],
                        channel=pick.get('channel', ''),
                        server=pick.get('server', '')
                    )
                    sharp_picks.append(sharp_pick)
        
        return sharp_picks
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of sharp bettor performance"""
        verified_sharps = [
            bettor for bettor in self.sharp_bettors.values()
            if self.is_verified_sharp(bettor.user_id)
        ]
        
        if not verified_sharps:
            return {
                'total_sharps': 0,
                'avg_win_rate': 0.0,
                'avg_roi': 0.0
            }
        
        avg_win_rate = sum(s.win_rate for s in verified_sharps) / len(verified_sharps)
        avg_roi = sum(s.roi for s in verified_sharps) / len(verified_sharps)
        
        return {
            'total_sharps': len(verified_sharps),
            'avg_win_rate': round(avg_win_rate, 3),
            'avg_roi': round(avg_roi, 3),
            'total_picks_tracked': sum(s.total_picks for s in verified_sharps)
        }

