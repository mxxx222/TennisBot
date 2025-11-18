"""
Real-time odds tracking system
Handles continuous monitoring of odds movements across multiple leagues
"""

import asyncio
import aiohttp
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
import json

from config.live_config import LiveMonitoringConfig, MOVEMENT_PATTERNS

logger = logging.getLogger(__name__)

@dataclass
class OddsSnapshot:
    """Represents odds at a specific point in time"""
    match_id: str
    home_team: str
    away_team: str
    home_odds: float
    away_odds: float
    timestamp: datetime
    league: str
    commence_time: datetime
    bookmaker: str = "default"
    
    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
        if isinstance(self.commence_time, str):
            self.commence_time = datetime.fromisoformat(self.commence_time.replace('Z', '+00:00'))

@dataclass
class OddsMovement:
    """Represents a detected odds movement"""
    match_id: str
    team: str
    old_odds: float
    new_odds: float
    change: float
    timestamp: datetime
    movement_type: str
    significance: str  # LOW, MEDIUM, HIGH, CRITICAL
    
    @property
    def change_percentage(self) -> float:
        """Calculate percentage change"""
        if self.old_odds == 0:
            return 0.0
        return ((self.new_odds - self.old_odds) / self.old_odds) * 100

class OddsTracker:
    """Real-time odds tracking and movement detection"""
    
    def __init__(self):
        self.config = LiveMonitoringConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Storage for current and historical odds
        self.current_odds: Dict[str, OddsSnapshot] = {}
        self.odds_history: Dict[str, List[OddsSnapshot]] = {}
        
        # Movement tracking
        self.detected_movements: List[OddsMovement] = []
        self.last_alert_times: Dict[str, datetime] = {}
        
        # Performance tracking
        self.request_count = 0
        self.error_count = 0
        self.last_update_time = None
        
        # Rate limiting
        self.last_request_times: Dict[str, float] = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def fetch_league_odds(self, league: str) -> List[OddsSnapshot]:
        """Fetch current odds for a specific league"""
        url = f"{self.config.ODDS_API_BASE_URL}/sports/{league}/odds"
        
        params = {
            'apiKey': self.config.ODDS_API_KEY,
            'regions': 'eu',
            'markets': 'h2h',
            'oddsFormat': 'decimal',
            'dateFormat': 'iso'
        }
        
        try:
            # Rate limiting
            await self._rate_limit(league)
            
            async with self.session.get(url, params=params) as response:
                self.request_count += 1
                
                if response.status == 200:
                    data = await response.json()
                    snapshots = []
                    
                    for match_data in data:
                        # Only process matches in next 48 hours
                        commence_time = datetime.fromisoformat(
                            match_data['commence_time'].replace('Z', '+00:00')
                        )
                        
                        # Make datetime.now() timezone-aware for comparison
                        from datetime import timezone
                        now_utc = datetime.now(timezone.utc)
                        
                        if commence_time > now_utc + timedelta(hours=48):
                            continue
                        
                        # Extract best odds from bookmakers
                        home_odds, away_odds = self._extract_best_odds(match_data)
                        
                        if home_odds > 0 and away_odds > 0:
                            snapshot = OddsSnapshot(
                                match_id=match_data['id'],
                                home_team=match_data['home_team'],
                                away_team=match_data['away_team'],
                                home_odds=home_odds,
                                away_odds=away_odds,
                                timestamp=datetime.now(),
                                league=league,
                                commence_time=commence_time
                            )
                            snapshots.append(snapshot)
                    
                    logger.debug(f"Fetched {len(snapshots)} odds from {league}")
                    return snapshots
                
                elif response.status == 429:
                    logger.warning(f"Rate limit hit for {league}")
                    await asyncio.sleep(60)  # Wait 1 minute
                    return []
                
                else:
                    logger.error(f"API error for {league}: {response.status}")
                    self.error_count += 1
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching odds for {league}: {e}")
            self.error_count += 1
            return []
    
    def _extract_best_odds(self, match_data: Dict) -> Tuple[float, float]:
        """Extract best available odds from bookmakers"""
        best_home = 0.0
        best_away = 0.0
        
        bookmakers = match_data.get('bookmakers', [])
        for bookmaker in bookmakers:
            markets = bookmaker.get('markets', [])
            for market in markets:
                if market.get('key') != 'h2h':
                    continue
                
                outcomes = market.get('outcomes', [])
                for outcome in outcomes:
                    price = outcome.get('price', 0)
                    name = outcome.get('name', '')
                    
                    if name == match_data['home_team']:
                        best_home = max(best_home, price)
                    elif name == match_data['away_team']:
                        best_away = max(best_away, price)
        
        return best_home, best_away
    
    async def _rate_limit(self, league: str):
        """Implement rate limiting per league"""
        now = time.time()
        last_request = self.last_request_times.get(league, 0)
        
        time_since_last = now - last_request
        min_interval = 60 / len(self.config.TARGET_LEAGUES)  # Distribute requests
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_times[league] = time.time()
    
    def detect_movements(self, new_snapshots: List[OddsSnapshot]) -> List[OddsMovement]:
        """Detect significant odds movements"""
        movements = []
        
        for snapshot in new_snapshots:
            match_key = f"{snapshot.match_id}_{snapshot.league}"
            
            # Check if we have previous odds for this match
            if match_key in self.current_odds:
                old_snapshot = self.current_odds[match_key]
                
                # Check home team odds movement
                home_movement = self._analyze_movement(
                    snapshot.match_id,
                    snapshot.home_team,
                    old_snapshot.home_odds,
                    snapshot.home_odds,
                    snapshot.timestamp
                )
                if home_movement:
                    movements.append(home_movement)
                
                # Check away team odds movement
                away_movement = self._analyze_movement(
                    snapshot.match_id,
                    snapshot.away_team,
                    old_snapshot.away_odds,
                    snapshot.away_odds,
                    snapshot.timestamp
                )
                if away_movement:
                    movements.append(away_movement)
            
            # Update current odds
            self.current_odds[match_key] = snapshot
            
            # Add to history
            if match_key not in self.odds_history:
                self.odds_history[match_key] = []
            self.odds_history[match_key].append(snapshot)
            
            # Limit history size
            if len(self.odds_history[match_key]) > 100:
                self.odds_history[match_key] = self.odds_history[match_key][-50:]
        
        return movements
    
    def _analyze_movement(self, match_id: str, team: str, old_odds: float, 
                         new_odds: float, timestamp: datetime) -> Optional[OddsMovement]:
        """Analyze if odds movement is significant"""
        
        if old_odds == 0 or new_odds == 0:
            return None
        
        change = new_odds - old_odds
        abs_change = abs(change)
        
        # Only track significant movements
        if abs_change < self.config.MIN_ODDS_CHANGE:
            return None
        
        # Determine movement type and significance
        movement_type = self._classify_movement(old_odds, new_odds)
        significance = self._determine_significance(abs_change, old_odds, new_odds)
        
        return OddsMovement(
            match_id=match_id,
            team=team,
            old_odds=old_odds,
            new_odds=new_odds,
            change=change,
            timestamp=timestamp,
            movement_type=movement_type,
            significance=significance
        )
    
    def _classify_movement(self, old_odds: float, new_odds: float) -> str:
        """Classify the type of odds movement"""
        change = new_odds - old_odds
        
        # Check if entering or exiting profitable range
        in_range_old = self.config.MIN_ODDS <= old_odds <= self.config.MAX_ODDS
        in_range_new = self.config.MIN_ODDS <= new_odds <= self.config.MAX_ODDS
        
        if not in_range_old and in_range_new:
            return MOVEMENT_PATTERNS['ENTERING_RANGE']
        elif in_range_old and not in_range_new:
            return MOVEMENT_PATTERNS['EXITING_RANGE']
        elif abs(change) >= self.config.SIGNIFICANT_CHANGE:
            if change < 0:
                return MOVEMENT_PATTERNS['SIGNIFICANT_DROP']
            else:
                return MOVEMENT_PATTERNS['SIGNIFICANT_RISE']
        else:
            return 'normal_movement'
    
    def _determine_significance(self, abs_change: float, old_odds: float, 
                              new_odds: float) -> str:
        """Determine the significance level of the movement"""
        
        # Check if entering profitable range
        in_range_new = self.config.MIN_ODDS <= new_odds <= self.config.MAX_ODDS
        
        if in_range_new and abs_change >= self.config.CRITICAL_CHANGE:
            return 'CRITICAL'
        elif in_range_new and abs_change >= self.config.SIGNIFICANT_CHANGE:
            return 'HIGH'
        elif in_range_new:
            return 'MEDIUM'
        elif abs_change >= self.config.CRITICAL_CHANGE:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def get_value_opportunities(self) -> List[OddsSnapshot]:
        """Get current odds that are in the profitable range"""
        opportunities = []
        
        for snapshot in self.current_odds.values():
            # Check home team odds
            if self.config.MIN_ODDS <= snapshot.home_odds <= self.config.MAX_ODDS:
                opportunities.append(snapshot)
            
            # Check away team odds (create separate snapshot)
            elif self.config.MIN_ODDS <= snapshot.away_odds <= self.config.MAX_ODDS:
                away_snapshot = OddsSnapshot(
                    match_id=snapshot.match_id + "_away",
                    home_team=snapshot.away_team,  # Flip for away bet
                    away_team=snapshot.home_team,
                    home_odds=snapshot.away_odds,
                    away_odds=snapshot.home_odds,
                    timestamp=snapshot.timestamp,
                    league=snapshot.league,
                    commence_time=snapshot.commence_time
                )
                opportunities.append(away_snapshot)
        
        return opportunities
    
    def cleanup_old_data(self):
        """Clean up old odds data to prevent memory issues"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # Clean up current odds for finished matches
        to_remove = []
        for match_key, snapshot in self.current_odds.items():
            if snapshot.commence_time < cutoff_time:
                to_remove.append(match_key)
        
        for key in to_remove:
            del self.current_odds[key]
            if key in self.odds_history:
                del self.odds_history[key]
        
        # Clean up old alert times
        old_alerts = []
        for match_id, alert_time in self.last_alert_times.items():
            if alert_time < cutoff_time:
                old_alerts.append(match_id)
        
        for match_id in old_alerts:
            del self.last_alert_times[match_id]
        
        logger.info(f"Cleaned up {len(to_remove)} old matches and {len(old_alerts)} old alerts")
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        return {
            'total_requests': self.request_count,
            'error_count': self.error_count,
            'error_rate': self.error_count / max(self.request_count, 1),
            'tracked_matches': len(self.current_odds),
            'total_movements': len(self.detected_movements),
            'last_update': self.last_update_time.isoformat() if self.last_update_time else None
        }
