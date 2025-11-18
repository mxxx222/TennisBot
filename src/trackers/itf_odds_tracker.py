#!/usr/bin/env python3
"""
📈 ITF ODDS MOVEMENT TRACKER
============================

Tracks odds movements for ITF matches.
- Line Move % (Opening vs current odds change)
- Steam Move Alert (Flag if odds move >15% <2h before match)
- CLV Tracking (Closing Line Value = your odds vs closing odds)
Integrates with existing odds API.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Try to import existing odds API
try:
    from src.odds_api_integration import OddsAPIIntegration
    ODDS_API_AVAILABLE = True
except ImportError:
    ODDS_API_AVAILABLE = False

logger = logging.getLogger(__name__)


class ITFOddsTracker:
    """Tracks odds movements for ITF matches"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ITF Odds Tracker
        
        Args:
            config: Configuration dict
        """
        self.config = config or {}
        self.steam_threshold = self.config.get('steam_threshold', 0.15)  # 15%
        self.steam_time_window = self.config.get('steam_time_window', 2)  # 2 hours
        
        if ODDS_API_AVAILABLE:
            self.odds_api = OddsAPIIntegration()
        else:
            self.odds_api = None
            logger.warning("⚠️ Odds API not available")
        
        # Track odds history
        self.odds_history: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.info("📈 ITF Odds Tracker initialized")
    
    def track_opening_odds(self, match_id: str, odds: float, bookmaker: str = "Pinnacle"):
        """
        Track opening odds for a match
        
        Args:
            match_id: Match identifier
            odds: Opening odds
            bookmaker: Bookmaker name
        """
        if match_id not in self.odds_history:
            self.odds_history[match_id] = []
        
        self.odds_history[match_id].append({
            'odds': odds,
            'bookmaker': bookmaker,
            'timestamp': datetime.now(),
            'type': 'opening',
        })
        
        logger.debug(f"📊 Tracked opening odds for {match_id}: {odds} ({bookmaker})")
    
    def track_current_odds(self, match_id: str, odds: float, bookmaker: str = "Pinnacle"):
        """
        Track current odds for a match
        
        Args:
            match_id: Match identifier
            odds: Current odds
            bookmaker: Bookmaker name
        """
        if match_id not in self.odds_history:
            self.odds_history[match_id] = []
        
        self.odds_history[match_id].append({
            'odds': odds,
            'bookmaker': bookmaker,
            'timestamp': datetime.now(),
            'type': 'current',
        })
    
    def calculate_line_move(self, match_id: str) -> Optional[float]:
        """
        Calculate line move percentage (opening vs current)
        
        Args:
            match_id: Match identifier
            
        Returns:
            Line move percentage or None
        """
        if match_id not in self.odds_history:
            return None
        
        history = self.odds_history[match_id]
        
        # Find opening odds
        opening = next((h for h in history if h['type'] == 'opening'), None)
        if not opening:
            return None
        
        # Find most recent current odds
        current = next((h for h in reversed(history) if h['type'] == 'current'), None)
        if not current:
            return None
        
        # Calculate move percentage
        move_pct = ((current['odds'] - opening['odds']) / opening['odds']) * 100
        
        return move_pct
    
    def detect_steam_move(self, match_id: str, match_time: datetime) -> bool:
        """
        Detect steam move (odds move >15% <2h before match)
        
        Args:
            match_id: Match identifier
            match_time: Scheduled match time
            
        Returns:
            True if steam move detected
        """
        move_pct = self.calculate_line_move(match_id)
        if move_pct is None:
            return False
        
        # Check if within time window
        time_until_match = (match_time - datetime.now()).total_seconds() / 3600  # hours
        
        if time_until_match < self.steam_time_window and abs(move_pct) > (self.steam_threshold * 100):
            return True
        
        return False
    
    def calculate_clv(self, your_odds: float, closing_odds: float) -> float:
        """
        Calculate Closing Line Value (CLV)
        
        Args:
            your_odds: Your bet odds
            closing_odds: Closing line odds
            
        Returns:
            CLV percentage
        """
        your_implied_prob = 1.0 / your_odds
        closing_implied_prob = 1.0 / closing_odds
        
        clv = ((your_implied_prob - closing_implied_prob) / closing_implied_prob) * 100
        
        return clv
    
    async def get_match_odds(self, match_id: str, player_name: str) -> Optional[float]:
        """
        Get current odds for a match from odds API
        
        Args:
            match_id: Match identifier
            player_name: Player name
            
        Returns:
            Current odds or None
        """
        if not self.odds_api:
            return None
        
        try:
            # Use existing odds API to get odds
            # This is a simplified version
            odds_data = await self.odds_api.get_live_odds(sports=['tennis_wta'])
            
            # Find match odds (would need proper matching logic)
            # For now, return None
            return None
            
        except Exception as e:
            logger.debug(f"Error getting odds: {e}")
            return None


async def main():
    """Test ITF Odds Tracker"""
    print("📈 ITF ODDS TRACKER TEST")
    print("=" * 50)
    
    tracker = ITFOddsTracker()
    
    # Test tracking
    match_id = "test_match_1"
    tracker.track_opening_odds(match_id, 1.75, "Pinnacle")
    
    await asyncio.sleep(1)
    
    tracker.track_current_odds(match_id, 1.85, "Pinnacle")
    
    move_pct = tracker.calculate_line_move(match_id)
    print(f"\n📊 Line Move: {move_pct:.2f}%")
    
    # Test CLV
    clv = tracker.calculate_clv(1.75, 1.80)
    print(f"📊 CLV: {clv:.2f}%")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())

