#!/usr/bin/env python3
"""
Sportbex API Client
===================

Fetches tennis match data from Sportbex API.
Supports rate limiting, error handling, and retries.

API Documentation: https://trial.sportbex.com
"""

import asyncio
import aiohttp
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import os
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / 'telegram_secrets.env'
if env_path.exists():
    load_dotenv(env_path)

logger = logging.getLogger(__name__)


@dataclass
class SportbexMatch:
    """Represents a tennis match from Sportbex API"""
    match_id: str
    tournament: str
    player1: str
    player2: str
    player1_odds: Optional[float] = None
    player2_odds: Optional[float] = None
    commence_time: Optional[datetime] = None
    surface: Optional[str] = None
    tournament_tier: Optional[str] = None
    player1_ranking: Optional[int] = None
    player2_ranking: Optional[int] = None
    raw_data: Optional[Dict] = None


class SportbexClient:
    """Client for Sportbex API"""
    
    BASE_URL = "https://trial-api.sportbex.com/api"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Sportbex API client
        
        Args:
            api_key: Sportbex API key (defaults to env var SPORTBEX_API_KEY)
        """
        # Try to get API key from environment or use default trial key
        self.api_key = api_key or os.getenv('SPORTBEX_API_KEY') or 'Fbmm5Xt57NzVjdKdGwPIQY7EXKOmYAt2MfFWXVCb'
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time = 0.0
        self.min_request_delay = 0.2  # 200ms between requests (500 requests/day = ~1 req/3 min)
        self.request_count = 0
        self.max_requests_per_day = 500
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'sportbex-api-key': self.api_key,
                'Content-Type': 'application/json',
                'User-Agent': 'TennisBot/1.0'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_delay:
            await asyncio.sleep(self.min_request_delay - elapsed)
        self.last_request_time = time.time()
        
        # Check daily limit
        if self.request_count >= self.max_requests_per_day:
            logger.warning(f"Daily request limit reached: {self.request_count}/{self.max_requests_per_day}")
            raise Exception("Daily API request limit exceeded")
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make HTTP request with error handling and retries
        
        Args:
            endpoint: API endpoint (e.g., '/matches')
            params: Query parameters
            
        Returns:
            JSON response data or None if failed
        """
        await self._rate_limit()
        
        url = f"{self.BASE_URL}{endpoint}"
        max_retries = 3
        retry_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                async with self.session.get(url, params=params) as response:
                    self.request_count += 1
                    
                    if response.status == 200:
                        # Check if response is JSON
                        content_type = response.headers.get('Content-Type', '')
                        if 'application/json' in content_type:
                            data = await response.json()
                            logger.debug(f"Successfully fetched from {endpoint}")
                            return data
                        else:
                            # Response is not JSON (might be HTML)
                            text = await response.text()
                            if text.strip().startswith('<!DOCTYPE') or text.strip().startswith('<html'):
                                logger.warning(f"API returned HTML instead of JSON. Endpoint might be wrong: {endpoint}")
                                logger.debug(f"Response preview: {text[:200]}")
                            else:
                                # Try to parse as JSON anyway
                                try:
                                    import json
                                    data = json.loads(text)
                                    return data
                                except:
                                    logger.warning(f"Could not parse response as JSON from {endpoint}")
                            return None
                    elif response.status == 401:
                        logger.error("Unauthorized - check API key")
                        return None
                    elif response.status == 429:
                        logger.warning("Rate limit exceeded, waiting...")
                        await asyncio.sleep(retry_delay * (attempt + 1))
                        continue
                    elif response.status == 404:
                        logger.warning(f"Endpoint not found: {endpoint}")
                        return None
                    else:
                        error_text = await response.text()
                        logger.error(f"API request failed: {response.status} - {error_text}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                            continue
                        return None
                        
            except aiohttp.ClientError as e:
                logger.error(f"Request attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                return None
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return None
        
        return None
    
    async def get_matches(self, 
                         sport: str = "tennis",
                         days_ahead: int = 2,
                         tournament_types: Optional[List[str]] = None) -> List[SportbexMatch]:
        """
        Fetch tennis matches from Sportbex API
        
        Args:
            sport: Sport type (default: tennis)
            days_ahead: Number of days ahead to fetch (default: 2)
            tournament_types: Filter by tournament types (ITF, ATP, etc.)
            
        Returns:
            List of SportbexMatch objects
        """
        logger.info(f"Fetching tennis matches for next {days_ahead} days")
        
        # Step 1: Get tennis competitions (competition ID 2 = Tennis)
        competitions_data = await self._make_request('/betfair/competitions/2')
        
        if not competitions_data or not isinstance(competitions_data, list):
            logger.warning("No competitions found")
            return []
        
        logger.info(f"Found {len(competitions_data)} tennis competitions")
        
        # Step 2: Fetch matches from each competition
        matches = []
        for comp in competitions_data[:20]:  # Limit to first 20 competitions
            comp_id = comp.get('competition', {}).get('id')
            comp_name = comp.get('competition', {}).get('name', '')
            
            if not comp_id:
                continue
            
            # Filter by tournament types if specified
            if tournament_types:
                comp_upper = comp_name.upper()
                if not any(tier.upper() in comp_upper for tier in tournament_types):
                    continue
            
            # Fetch events (matches) for this competition
            # Endpoint: /betfair/event/{sportId}/{competitionId}
            events_data = await self._make_request(f'/betfair/event/2/{comp_id}')
            
            if events_data:
                comp_matches = await self._parse_events(events_data, comp_name, comp_id)
                matches.extend(comp_matches)
        
        logger.info(f"✅ Found {len(matches)} total matches")
        return matches
    
    async def _parse_events(self, events_data: Any, competition_name: str, competition_id: str) -> List[SportbexMatch]:
        """
        Parse events (matches) from Sportbex API response and fetch odds
        
        Args:
            events_data: API response with events
            competition_name: Competition/tournament name
            competition_id: Competition ID
            
        Returns:
            List of SportbexMatch objects
        """
        matches = []
        
        if not isinstance(events_data, list):
            return matches
        
        for event_item in events_data:
            try:
                event = event_item.get('event', {}) if 'event' in event_item else event_item
                
                # Extract event information
                event_id = str(event.get('id') or event.get('eventId') or hash(str(event)))
                event_name = event.get('name', '')
                
                if not event_name:
                    continue
                
                # Parse player names from event name (format: "Player A v Player B")
                players = event_name.split(' v ')
                if len(players) != 2:
                    # Try other separators
                    for sep in [' vs ', ' - ', ' / ']:
                        if sep in event_name:
                            players = event_name.split(sep)
                            break
                
                if len(players) != 2:
                    logger.debug(f"Could not parse players from event name: {event_name}")
                    continue
                
                player1 = players[0].strip()
                player2 = players[1].strip()
                
                # Extract start time
                start_time = event.get('openDate') or event.get('startTime') or event.get('start') or event.get('date')
                commence_time = self._parse_datetime(start_time)
                
                # Fetch markets (odds) for this event
                # First get market IDs
                markets_data = await self._make_request(f'/betfair/markets/2/{event_id}')
                player1_odds = None
                player2_odds = None
                
                if markets_data and isinstance(markets_data, list):
                    # Find Match Odds market
                    for market in markets_data:
                        market_name = market.get('marketName', '')
                        market_id = market.get('marketId') or market.get('id')
                        
                        # Look for Match Odds market
                        if market_id and ('Match Odds' in market_name or 'MATCH_ODDS' in market_name.upper()):
                            # Fetch odds using listMarketBook endpoint
                            odds_data = await self._fetch_market_odds(str(market_id))
                            
                            if odds_data and isinstance(odds_data, dict):
                                # Parse odds from market book
                                runners = odds_data.get('runners', [])
                                
                                # Match runners to players by selectionId order (usually first = player1, second = player2)
                                # Or try to match by name if available
                                for idx, runner in enumerate(runners):
                                    # Get price from availableToBack or lastPriceTraded
                                    price = None
                                    ex = runner.get('ex', {})
                                    if ex and 'availableToBack' in ex and len(ex['availableToBack']) > 0:
                                        price = ex['availableToBack'][0].get('price')
                                    elif 'lastPriceTraded' in runner:
                                        price = runner['lastPriceTraded']
                                    
                                    if price:
                                        # Simple matching: first runner = player1, second = player2
                                        if idx == 0:
                                            player1_odds = float(price)
                                        elif idx == 1:
                                            player2_odds = float(price)
                            
                            # Break after finding Match Odds market
                            break
                
                # Extract tournament tier
                tournament_tier = self._extract_tournament_tier(competition_name)
                
                match = SportbexMatch(
                    match_id=event_id,
                    tournament=competition_name,
                    player1=player1,
                    player2=player2,
                    player1_odds=player1_odds,
                    player2_odds=player2_odds,
                    commence_time=commence_time,
                    tournament_tier=tournament_tier,
                    raw_data=event
                )
                
                matches.append(match)
                
            except Exception as e:
                logger.error(f"Error parsing event: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                continue
        
        return matches
    
    def _parse_matches(self, data: Dict, tournament_types: Optional[List[str]] = None) -> List[SportbexMatch]:
        """
        Parse API response into SportbexMatch objects
        
        Args:
            data: API response JSON
            tournament_types: Optional filter for tournament types
            
        Returns:
            List of SportbexMatch objects
        """
        matches = []
        
        # Handle different possible response structures
        matches_data = []
        
        if isinstance(data, list):
            matches_data = data
        elif isinstance(data, dict):
            # Try common keys
            matches_data = (
                data.get('matches', []) or
                data.get('data', []) or
                data.get('results', []) or
                []
            )
        
        for match_data in matches_data:
            try:
                # Extract match information (structure may vary)
                match_id = str(match_data.get('id') or match_data.get('match_id') or hash(str(match_data)))
                
                # Extract players
                player1 = (
                    match_data.get('player1') or
                    match_data.get('home_player') or
                    match_data.get('player_a') or
                    match_data.get('home_team') or
                    ''
                )
                player2 = (
                    match_data.get('player2') or
                    match_data.get('away_player') or
                    match_data.get('player_b') or
                    match_data.get('away_team') or
                    ''
                )
                
                if not player1 or not player2:
                    continue
                
                # Extract tournament
                tournament = (
                    match_data.get('tournament') or
                    match_data.get('competition') or
                    match_data.get('league') or
                    'Unknown Tournament'
                )
                
                # Extract odds
                player1_odds = self._extract_odds(match_data, 'player1', 'home')
                player2_odds = self._extract_odds(match_data, 'player2', 'away')
                
                # Extract commence time
                commence_time = self._parse_datetime(
                    match_data.get('commence_time') or
                    match_data.get('start_time') or
                    match_data.get('date') or
                    match_data.get('scheduled_time')
                )
                
                # Extract surface
                surface = (
                    match_data.get('surface') or
                    match_data.get('court_surface') or
                    None
                )
                
                # Extract tournament tier
                tournament_tier = self._extract_tournament_tier(tournament)
                
                # Extract rankings (if available)
                player1_ranking = match_data.get('player1_ranking') or match_data.get('home_ranking')
                player2_ranking = match_data.get('player2_ranking') or match_data.get('away_ranking')
                
                # Filter by tournament types if specified
                if tournament_types:
                    if not any(tier in tournament.upper() for tier in tournament_types):
                        continue
                
                match = SportbexMatch(
                    match_id=match_id,
                    tournament=tournament,
                    player1=player1,
                    player2=player2,
                    player1_odds=player1_odds,
                    player2_odds=player2_odds,
                    commence_time=commence_time,
                    surface=surface,
                    tournament_tier=tournament_tier,
                    player1_ranking=player1_ranking,
                    player2_ranking=player2_ranking,
                    raw_data=match_data
                )
                
                matches.append(match)
                
            except Exception as e:
                logger.error(f"Error parsing match data: {e}")
                continue
        
        return matches
    
    def _extract_odds(self, data: Dict, player_key: str, alt_key: str) -> Optional[float]:
        """Extract odds for a player from various possible structures"""
        # Try direct keys
        odds = data.get(f'{player_key}_odds') or data.get(f'{alt_key}_odds')
        if odds:
            return float(odds)
        
        # Try nested structures
        if 'odds' in data:
            odds_data = data['odds']
            if isinstance(odds_data, dict):
                odds = odds_data.get(player_key) or odds_data.get(alt_key)
                if odds:
                    return float(odds)
        
        # Try bookmakers structure
        if 'bookmakers' in data:
            for bookmaker in data['bookmakers']:
                if 'markets' in bookmaker:
                    for market in bookmaker['markets']:
                        if market.get('key') == 'h2h' and 'outcomes' in market:
                            for outcome in market['outcomes']:
                                if outcome.get('name') == data.get(player_key) or outcome.get('name') == data.get(alt_key):
                                    return float(outcome.get('price', 0))
        
        return None
    
    async def _fetch_market_odds(self, market_id: str) -> Optional[Dict]:
        """
        Fetch odds for a market using listMarketBook endpoint
        
        Args:
            market_id: Market ID
            
        Returns:
            Market book data with odds
        """
        try:
            # POST request to listMarketBook
            url = f"{self.BASE_URL}/betfair/listMarketBook/2"
            await self._rate_limit()
            
            payload = {"marketIds": [market_id]}
            
            async with self.session.post(
                url,
                json=payload,
                headers={'sportbex-api-key': self.api_key, 'Content-Type': 'application/json'}
            ) as response:
                self.request_count += 1
                
                if response.status == 200:
                    data = await response.json()
                    # API returns: {"status": true, "data": [...]}
                    if isinstance(data, dict) and data.get('status') and data.get('data'):
                        market_books = data['data']
                        if isinstance(market_books, list) and len(market_books) > 0:
                            return market_books[0]  # Return first market book
                    elif isinstance(data, list) and len(data) > 0:
                        return data[0]
                    return data
                else:
                    logger.debug(f"Failed to fetch market odds: {response.status}")
                    return None
        except Exception as e:
            logger.debug(f"Error fetching market odds: {e}")
            return None
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string into datetime object"""
        if not dt_str:
            return None
        
        try:
            # Try ISO format with timezone
            if 'T' in dt_str:
                if dt_str.endswith('Z'):
                    # UTC timezone
                    dt_str = dt_str.replace('Z', '+00:00')
                elif '+' not in dt_str and dt_str.count('-') >= 3:
                    # Add UTC timezone if missing
                    dt_str = dt_str + '+00:00'
                return datetime.fromisoformat(dt_str)
            
            # Try common formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y %H:%M']:
                try:
                    return datetime.strptime(dt_str, fmt)
                except ValueError:
                    continue
            
            return None
        except Exception as e:
            logger.debug(f"Could not parse datetime: {dt_str} - {e}")
            return None
    
    def _extract_tournament_tier(self, tournament: str) -> Optional[str]:
        """Extract tournament tier from tournament name"""
        tournament_upper = tournament.upper()
        
        # ITF Women
        if 'W15' in tournament_upper:
            return 'W15'
        elif 'W25' in tournament_upper:
            return 'W25'
        elif 'W35' in tournament_upper:
            return 'W35'
        elif 'W50' in tournament_upper:
            return 'W50'
        elif 'W60' in tournament_upper:
            return 'W60'
        elif 'W75' in tournament_upper:
            return 'W75'
        elif 'W80' in tournament_upper:
            return 'W80'
        elif 'W100' in tournament_upper:
            return 'W100'
        # ATP Challenger
        elif 'CHALLENGER' in tournament_upper:
            return 'ATP Challenger'
        elif 'ATP' in tournament_upper and 'CHALLENGER' in tournament_upper:
            return 'ATP Challenger'
        
        return None
    
    async def test_connection(self) -> bool:
        """Test API connection"""
        try:
            # Try a simple endpoint
            data = await self._make_request('/health') or await self._make_request('/')
            return data is not None
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


# Synchronous wrapper for backwards compatibility
class SyncSportbexClient:
    """Synchronous wrapper for SportbexClient"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = SportbexClient(api_key)
    
    def get_matches(self, **kwargs) -> List[SportbexMatch]:
        """Synchronous version of get_matches"""
        async def _fetch():
            async with self.client as client:
                return await client.get_matches(**kwargs)
        
        return asyncio.run(_fetch())
    
    def test_connection(self) -> bool:
        """Synchronous version of test_connection"""
        async def _test():
            async with self.client as client:
                return await client.test_connection()
        
        return asyncio.run(_test())


async def main():
    """Test Sportbex API client"""
    print("🧪 Testing Sportbex API Client")
    print("=" * 50)
    
    client = SportbexClient()
    
    async with client:
        # Test connection
        print("\n1. Testing connection...")
        connected = await client.test_connection()
        print(f"   {'✅ Connected' if connected else '⚠️ Connection test inconclusive (API may not have /health endpoint)'}")
        
        # Fetch matches
        print("\n2. Fetching tennis matches...")
        matches = await client.get_matches(days_ahead=2)
        
        print(f"\n✅ Found {len(matches)} matches")
        
        if matches:
            print("\n📊 Sample matches:")
            for i, match in enumerate(matches[:5], 1):
                print(f"\n   {i}. {match.player1} vs {match.player2}")
                print(f"      Tournament: {match.tournament}")
                print(f"      Odds: {match.player1_odds} / {match.player2_odds}")
                print(f"      Time: {match.commence_time}")
                print(f"      Tier: {match.tournament_tier}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())

