#!/usr/bin/env python3
"""
⚡ ITF LIVE MOMENTUM MONITOR
===========================

Monitors live matches from FlashScore scraper.
Detects "Set 1 Deficit Recovery" patterns:
- If ranked >200 player loses set 0-6 or 1-6 → auto-alert
- Calculate historical comeback % per player + surface
Push alerts to Telegram.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scrapers.flashscore_itf_scraper import FlashScoreITFScraper, ITFMatch

logger = logging.getLogger(__name__)


class ITFLiveMonitor:
    """Live momentum detection for ITF matches"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ITF Live Monitor
        
        Args:
            config: Configuration dict
        """
        self.config = config or {}
        self.min_ranking = self.config.get('min_ranking_for_momentum', 200)
        self.scraper = FlashScoreITFScraper(config.get('scraper', {}))
        
        # Tracked matches
        self.tracked_matches: Dict[str, ITFMatch] = {}
        self.alerted_matches: set = set()
        
        logger.info(f"⚡ ITF Live Monitor initialized (min ranking: {self.min_ranking})")
    
    def detect_set1_deficit(self, match: ITFMatch, player_ranking: Optional[int] = None) -> bool:
        """
        Detect if match has Set 1 Deficit pattern
        
        Args:
            match: ITFMatch object
            player_ranking: Player ranking (optional)
            
        Returns:
            True if Set 1 Deficit detected
        """
        if not match.set1_score:
            return False
        
        try:
            scores = match.set1_score.split('-')
            if len(scores) != 2:
                return False
            
            player1_games = int(scores[0])
            player2_games = int(scores[1])
            
            # Check if either player lost first set badly (0-6, 1-6, 2-6)
            if player1_games <= 2 or player2_games <= 2:
                # Check if player ranking >200 (if provided)
                if player_ranking is None or player_ranking > self.min_ranking:
                    return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Error detecting Set 1 Deficit: {e}")
            return False
    
    def calculate_comeback_percent(self, player_name: str, surface: Optional[str] = None) -> float:
        """
        Calculate historical comeback percentage for player
        
        Args:
            player_name: Player name
            surface: Surface type (optional)
            
        Returns:
            Historical comeback percentage (0.0-1.0)
        """
        # TODO: Query historical data from database
        # For now, return default value
        return 0.15  # 15% default comeback rate
    
    async def monitor_matches(self) -> List[Dict[str, Any]]:
        """
        Monitor live matches and detect momentum shifts
        
        Returns:
            List of alert dictionaries
        """
        alerts = []
        
        try:
            # Scrape current matches
            async with self.scraper:
                result = await self.scraper.run_scrape()
            
            if not result.get('success'):
                logger.warning("⚠️ Scraping failed")
                return alerts
            
            matches_data = result.get('matches', [])
            
            # Convert to ITFMatch objects
            for match_dict in matches_data:
                match = ITFMatch(
                    match_id=match_dict['match_id'],
                    tournament=match_dict['tournament'],
                    tournament_tier=match_dict['tournament_tier'],
                    surface=match_dict.get('surface'),
                    player1=match_dict['player1'],
                    player2=match_dict['player2'],
                    round=match_dict.get('round'),
                    match_status=match_dict['match_status'],
                    live_score=match_dict.get('live_score'),
                    set1_score=match_dict.get('set1_score'),
                    scheduled_time=datetime.fromisoformat(match_dict['scheduled_time']) if match_dict.get('scheduled_time') else None,
                    match_url=None,
                    scraped_at=datetime.fromisoformat(match_dict['scraped_at'])
                )
                
                # Only monitor live matches
                if match.match_status != 'live':
                    continue
                
                # Check for Set 1 Deficit
                if self.detect_set1_deficit(match):
                    # Check if already alerted
                    if match.match_id not in self.alerted_matches:
                        # Calculate comeback percentage
                        comeback_pct = self.calculate_comeback_percent(
                            match.player1 if match.set1_score.split('-')[0] < match.set1_score.split('-')[1] else match.player2,
                            match.surface
                        )
                        
                        alert = {
                            'type': 'set1_deficit_recovery',
                            'match_id': match.match_id,
                            'tournament': match.tournament,
                            'player1': match.player1,
                            'player2': match.player2,
                            'set1_score': match.set1_score,
                            'comeback_percent': comeback_pct,
                            'timestamp': datetime.now().isoformat(),
                        }
                        
                        alerts.append(alert)
                        self.alerted_matches.add(match.match_id)
                        
                        logger.info(f"⚡ Set 1 Deficit detected: {match.player1} vs {match.player2} ({match.set1_score})")
                
                # Update tracked matches
                self.tracked_matches[match.match_id] = match
            
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Error monitoring matches: {e}")
            import traceback
            traceback.print_exc()
            return alerts
    
    async def run_continuous_monitor(self, interval_seconds: int = 600):
        """
        Run continuous monitoring loop
        
        Args:
            interval_seconds: Seconds between monitoring cycles
        """
        logger.info(f"🚀 Starting continuous monitoring (interval: {interval_seconds}s)...")
        
        while True:
            try:
                alerts = await self.monitor_matches()
                
                if alerts:
                    logger.info(f"⚡ Found {len(alerts)} momentum alerts")
                    # Alerts would be sent to Telegram here
                
                await asyncio.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("⏹️ Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                await asyncio.sleep(interval_seconds)


async def main():
    """Test ITF Live Monitor"""
    print("⚡ ITF LIVE MONITOR TEST")
    print("=" * 50)
    
    config = {
        'min_ranking_for_momentum': 200,
        'scraper': {
            'target_tournaments': ['W15', 'W35', 'W50'],
            'rate_limit': 2.5,
        }
    }
    
    monitor = ITFLiveMonitor(config)
    alerts = await monitor.monitor_matches()
    
    if alerts:
        print(f"\n⚡ Found {len(alerts)} alerts:")
        for alert in alerts:
            print(f"   {alert['player1']} vs {alert['player2']} - Set 1: {alert['set1_score']}")
    else:
        print("\nℹ️ No momentum alerts detected")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())

