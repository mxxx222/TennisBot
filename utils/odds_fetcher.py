"""
Odds fetching utility for Tennis ITF screening system
Handles API calls to The Odds API with proper rate limiting and error handling
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import time

from config.screening_config import ScreeningConfig

logger = logging.getLogger(__name__)

@dataclass
class TennisMatch:
    """Represents a tennis match with odds data"""
    id: str
    home_team: str
    away_team: str
    commence_time: datetime
    sport_title: str
    bookmakers: List[Dict]
    
    def get_best_odds(self) -> Tuple[float, float]:
        """Get best available odds for home and away players"""
        best_home = 0.0
        best_away = 0.0
        
        for bookmaker in self.bookmakers:
            markets = bookmaker.get('markets', [])
            for market in markets:
                if market.get('key') != 'h2h':
                    continue
                    
                outcomes = market.get('outcomes', [])
                for outcome in outcomes:
                    if outcome.get('name') == self.home_team:
                        best_home = max(best_home, outcome.get('price', 0))
                    elif outcome.get('name') == self.away_team:
                        best_away = max(best_away, outcome.get('price', 0))
        
        return best_home, best_away
    
    def is_itf_tournament(self) -> bool:
        """Check if this is an ITF-level tournament"""
        from config.screening_config import ALLOWED_TOURNAMENTS, EXCLUDED_TOURNAMENTS
        
        title_upper = self.sport_title.upper()
        
        # Check for excluded high-level tournaments
        for excluded in EXCLUDED_TOURNAMENTS:
            if excluded.upper() in title_upper:
                return False
        
        # Check for allowed ITF/Challenger tournaments
        for allowed in ALLOWED_TOURNAMENTS:
            if allowed.upper() in title_upper:
                return True
                
        # Default to True for ITF Women's tennis
        return True

class OddsFetcher:
    """Handles fetching tennis odds from The Odds API"""
    
    def __init__(self):
        self.config = ScreeningConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time = 0.0
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.config.REQUEST_DELAY:
            await asyncio.sleep(self.config.REQUEST_DELAY - elapsed)
        self.last_request_time = time.time()
    
    async def _make_request(self, url: str, params: Dict) -> Optional[Dict]:
        """Make HTTP request with error handling and retries"""
        await self._rate_limit()
        
        for attempt in range(self.config.MAX_RETRIES):
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Successfully fetched data from {url}")
                        return data
                    elif response.status == 429:
                        # Rate limit exceeded
                        logger.warning("Rate limit exceeded, waiting...")
                        await asyncio.sleep(self.config.RETRY_DELAY * (attempt + 1))
                        continue
                    else:
                        logger.error(f"API request failed with status {response.status}")
                        
            except Exception as e:
                logger.error(f"Request attempt {attempt + 1} failed: {e}")
                if attempt < self.config.MAX_RETRIES - 1:
                    await asyncio.sleep(self.config.RETRY_DELAY)
                    
        return None
    
    async def fetch_tennis_matches(self, hours_ahead: int = 48) -> List[TennisMatch]:
        """
        Fetch upcoming ITF Women's tennis matches
        
        Args:
            hours_ahead: How many hours ahead to look for matches
            
        Returns:
            List of TennisMatch objects with odds data
        """
        url = f"{self.config.ODDS_API_BASE_URL}/sports/{self.config.SPORT}/odds"
        
        params = {
            'apiKey': self.config.ODDS_API_KEY,
            'regions': self.config.REGIONS,
            'markets': self.config.MARKETS,
            'oddsFormat': self.config.ODDS_FORMAT,
            'dateFormat': self.config.DATE_FORMAT,
        }
        
        logger.info(f"Fetching ITF Women's tennis matches for next {hours_ahead} hours")
        
        data = await self._make_request(url, params)
        if not data:
            logger.error("Failed to fetch tennis matches")
            return []
        
        matches = []
        cutoff_time = datetime.now() + timedelta(hours=hours_ahead)
        
        for match_data in data:
            try:
                commence_time = datetime.fromisoformat(
                    match_data['commence_time'].replace('Z', '+00:00')
                )
                
                # Filter matches within time window
                if commence_time > cutoff_time:
                    continue
                
                match = TennisMatch(
                    id=match_data['id'],
                    home_team=match_data['home_team'],
                    away_team=match_data['away_team'], 
                    commence_time=commence_time,
                    sport_title=match_data.get('sport_title', 'Tennis'),
                    bookmakers=match_data.get('bookmakers', [])
                )
                
                # Only include ITF-level tournaments
                if match.is_itf_tournament():
                    matches.append(match)
                    
            except Exception as e:
                logger.error(f"Error parsing match data: {e}")
                continue
        
        logger.info(f"Found {len(matches)} ITF tennis matches")
        return matches
    
    async def get_sports_list(self) -> List[Dict]:
        """Get list of available sports (for debugging)"""
        url = f"{self.config.ODDS_API_BASE_URL}/sports"
        params = {'apiKey': self.config.ODDS_API_KEY}
        
        data = await self._make_request(url, params)
        return data or []

# Synchronous wrapper for backwards compatibility
class SyncOddsFetcher:
    """Synchronous wrapper for OddsFetcher"""
    
    def __init__(self):
        self.fetcher = OddsFetcher()
    
    def fetch_matches(self, hours_ahead: int = 48) -> List[TennisMatch]:
        """Synchronous version of fetch_tennis_matches"""
        async def _fetch():
            async with self.fetcher as fetcher:
                return await fetcher.fetch_tennis_matches(hours_ahead)
        
        return asyncio.run(_fetch())
    
    def get_sports(self) -> List[Dict]:
        """Synchronous version of get_sports_list"""
        async def _get_sports():
            async with self.fetcher as fetcher:
                return await fetcher.get_sports_list()
        
        return asyncio.run(_get_sports())
