#!/usr/bin/env python3
"""
📊 THE ODDS API INTEGRATION
===========================
Real-time odds data integration with The Odds API for live betting intelligence.
Provides comprehensive odds comparison across multiple bookmakers for optimal value detection.

Features:
- 🔄 Real-time odds fetching from The Odds API
- 📊 Multi-bookmaker comparison
- 💰 Value betting identification
- 🎯 Arbitrage opportunity detection
- 📈 Odds movement tracking
- 🛡️ Market efficiency analysis
"""

import asyncio
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import os
from dataclasses import dataclass

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OddsData:
    """Structured odds data from The Odds API"""
    sport_key: str
    sport_title: str
    commence_time: datetime
    home_team: str
    away_team: str
    bookmakers: List[Dict[str, Any]]
    
    # Calculated fields
    best_odds: Dict[str, Dict[str, float]]
    arbitrage_opportunity: Optional[Dict[str, Any]]
    value_bets: List[Dict[str, Any]]
    market_margin: float

class OddsAPIIntegration:
    """Integration with The Odds API for real-time odds data"""
    
    def __init__(self, api_key: str = None):
        """Initialize The Odds API integration"""
        logger.info("📊 Initializing The Odds API Integration...")
        
        # Get API key
        self.api_key = api_key or os.getenv('ODDS_API_KEY') or "1108325cf70df63e93c3d2aa09813f63"
        
        if not self.api_key:
            logger.error("❌ No Odds API key provided")
            raise ValueError("Odds API key is required")
        
        # API configuration
        self.base_url = "https://api.the-odds-api.com/v4"
        self.supported_sports = {
            'soccer_epl': 'English Premier League',
            'soccer_spain_la_liga': 'Spanish La Liga',
            'soccer_germany_bundesliga': 'German Bundesliga',
            'soccer_italy_serie_a': 'Italian Serie A',
            'soccer_france_ligue_one': 'French Ligue 1',
            'soccer_uefa_champs_league': 'UEFA Champions League',
            'tennis_atp': 'ATP Tennis',
            'tennis_wta': 'WTA Tennis',
            'basketball_nba': 'NBA Basketball',
            'icehockey_nhl': 'NHL Ice Hockey'
        }
        
        # Bookmaker preferences (ordered by reliability)
        self.preferred_bookmakers = [
            'pinnacle',
            'bet365',
            'betfair',
            'unibet',
            'williamhill',
            'betway',
            'marathonbet',
            'betsson'
        ]
        
        # Market mappings
        self.market_mappings = {
            'h2h': 'Match Winner',
            'spreads': 'Point Spread / Asian Handicap',
            'totals': 'Over/Under Totals'
        }
        
        # Rate limiting
        self.requests_made = 0
        self.last_request_time = datetime.now()
        self.max_requests_per_month = 500  # Free tier limit
        
        logger.info("✅ The Odds API Integration initialized")
    
    async def get_live_odds(self, sports: List[str] = None, markets: List[str] = None) -> List[OddsData]:
        """Get live odds for specified sports and markets"""
        
        if sports is None:
            sports = ['soccer_epl', 'tennis_atp', 'basketball_nba']
        
        if markets is None:
            markets = ['h2h', 'spreads', 'totals']
        
        logger.info(f"📊 Fetching live odds for {len(sports)} sports...")
        
        all_odds_data = []
        
        for sport in sports:
            try:
                sport_odds = await self._fetch_sport_odds(sport, markets)
                all_odds_data.extend(sport_odds)
                
                # Rate limiting - wait between requests
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Error fetching odds for {sport}: {e}")
        
        logger.info(f"✅ Retrieved odds for {len(all_odds_data)} matches")
        return all_odds_data
    
    async def _fetch_sport_odds(self, sport_key: str, markets: List[str]) -> List[OddsData]:
        """Fetch odds for a specific sport"""
        
        if sport_key not in self.supported_sports:
            logger.warning(f"⚠️ Unsupported sport: {sport_key}")
            return []
        
        # Check rate limiting
        if not self._check_rate_limit():
            logger.warning("⚠️ Rate limit reached, skipping request")
            return []
        
        # Build API URL
        url = f"{self.base_url}/sports/{sport_key}/odds"
        
        params = {
            'apiKey': self.api_key,
            'regions': 'eu,us,au',  # European, US, and Australian bookmakers
            'markets': ','.join(markets),
            'oddsFormat': 'decimal',
            'dateFormat': 'iso'
        }
        
        try:
            logger.info(f"🔍 Fetching {sport_key} odds...")
            
            response = requests.get(url, params=params, timeout=30)
            self.requests_made += 1
            self.last_request_time = datetime.now()
            
            if response.status_code == 200:
                data = response.json()
                return self._process_odds_data(data, sport_key)
            
            elif response.status_code == 401:
                logger.error("❌ Invalid API key")
                return []
            
            elif response.status_code == 429:
                logger.warning("⚠️ Rate limit exceeded")
                return []
            
            else:
                logger.error(f"❌ API error: {response.status_code} - {response.text}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request error: {e}")
            return []
    
    def _process_odds_data(self, raw_data: List[Dict], sport_key: str) -> List[OddsData]:
        """Process raw odds data from API"""
        
        processed_odds = []
        
        for match_data in raw_data:
            try:
                # Parse match information
                commence_time = datetime.fromisoformat(match_data['commence_time'].replace('Z', '+00:00'))
                
                # Skip matches that have already started
                from datetime import timezone
                current_time = datetime.now(timezone.utc)
                if commence_time <= current_time:
                    continue
                
                # Extract team names
                home_team = match_data['home_team']
                away_team = match_data['away_team']
                
                # Process bookmaker odds
                bookmakers = match_data.get('bookmakers', [])
                
                if not bookmakers:
                    continue
                
                # Calculate best odds and opportunities
                best_odds = self._calculate_best_odds(bookmakers)
                arbitrage_opportunity = self._detect_arbitrage(bookmakers)
                value_bets = self._identify_value_bets(bookmakers, best_odds)
                market_margin = self._calculate_market_margin(bookmakers)
                
                # Create OddsData object
                odds_data = OddsData(
                    sport_key=sport_key,
                    sport_title=self.supported_sports[sport_key],
                    commence_time=commence_time,
                    home_team=home_team,
                    away_team=away_team,
                    bookmakers=bookmakers,
                    best_odds=best_odds,
                    arbitrage_opportunity=arbitrage_opportunity,
                    value_bets=value_bets,
                    market_margin=market_margin
                )
                
                processed_odds.append(odds_data)
                
            except Exception as e:
                logger.error(f"❌ Error processing match data: {e}")
                continue
        
        return processed_odds
    
    def _calculate_best_odds(self, bookmakers: List[Dict]) -> Dict[str, Dict[str, float]]:
        """Calculate best available odds for each market and outcome"""
        
        best_odds = {}
        
        for bookmaker in bookmakers:
            bookmaker_name = bookmaker['key']
            
            for market in bookmaker.get('markets', []):
                market_key = market['key']
                
                if market_key not in best_odds:
                    best_odds[market_key] = {}
                
                for outcome in market.get('outcomes', []):
                    outcome_name = outcome['name']
                    odds_value = outcome['price']
                    
                    # Track best odds for each outcome
                    if (outcome_name not in best_odds[market_key] or 
                        odds_value > best_odds[market_key][outcome_name]):
                        best_odds[market_key][outcome_name] = odds_value
        
        return best_odds
    
    def _detect_arbitrage(self, bookmakers: List[Dict]) -> Optional[Dict[str, Any]]:
        """Detect arbitrage opportunities"""
        
        for market_key in ['h2h']:  # Focus on main markets for arbitrage
            market_odds = {}
            
            # Collect all odds for this market
            for bookmaker in bookmakers:
                bookmaker_name = bookmaker['key']
                
                for market in bookmaker.get('markets', []):
                    if market['key'] == market_key:
                        for outcome in market.get('outcomes', []):
                            outcome_name = outcome['name']
                            odds_value = outcome['price']
                            
                            if outcome_name not in market_odds:
                                market_odds[outcome_name] = []
                            
                            market_odds[outcome_name].append({
                                'bookmaker': bookmaker_name,
                                'odds': odds_value
                            })
            
            # Check for arbitrage
            if len(market_odds) >= 2:  # Need at least 2 outcomes
                best_odds_per_outcome = {}
                
                for outcome, odds_list in market_odds.items():
                    best_odds_per_outcome[outcome] = max(odds_list, key=lambda x: x['odds'])
                
                # Calculate total implied probability
                total_implied_prob = sum(1/odds_data['odds'] for odds_data in best_odds_per_outcome.values())
                
                if total_implied_prob < 1.0:  # Arbitrage opportunity exists
                    profit_margin = (1 - total_implied_prob) * 100
                    
                    return {
                        'market': market_key,
                        'profit_margin': profit_margin,
                        'best_odds': best_odds_per_outcome,
                        'total_implied_probability': total_implied_prob
                    }
        
        return None
    
    def _identify_value_bets(self, bookmakers: List[Dict], best_odds: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
        """Identify value betting opportunities"""
        
        value_bets = []
        
        # Simple value detection based on odds variance
        for market_key, outcomes in best_odds.items():
            if len(outcomes) < 2:
                continue
            
            # Calculate average odds for comparison
            avg_odds = {}
            odds_counts = {}
            
            for bookmaker in bookmakers:
                for market in bookmaker.get('markets', []):
                    if market['key'] == market_key:
                        for outcome in market.get('outcomes', []):
                            outcome_name = outcome['name']
                            odds_value = outcome['price']
                            
                            if outcome_name not in avg_odds:
                                avg_odds[outcome_name] = 0
                                odds_counts[outcome_name] = 0
                            
                            avg_odds[outcome_name] += odds_value
                            odds_counts[outcome_name] += 1
            
            # Calculate averages
            for outcome in avg_odds:
                if odds_counts[outcome] > 0:
                    avg_odds[outcome] /= odds_counts[outcome]
            
            # Identify value bets (best odds significantly higher than average)
            for outcome, best_odd in outcomes.items():
                if outcome in avg_odds:
                    avg_odd = avg_odds[outcome]
                    value_percentage = ((best_odd - avg_odd) / avg_odd) * 100
                    
                    if value_percentage > 5.0:  # 5% minimum value
                        value_bets.append({
                            'market': market_key,
                            'outcome': outcome,
                            'best_odds': best_odd,
                            'average_odds': avg_odd,
                            'value_percentage': value_percentage
                        })
        
        return value_bets
    
    def _calculate_market_margin(self, bookmakers: List[Dict]) -> float:
        """Calculate average market margin (bookmaker edge)"""
        
        margins = []
        
        for bookmaker in bookmakers:
            for market in bookmaker.get('markets', []):
                if market['key'] == 'h2h':  # Focus on main market
                    outcomes = market.get('outcomes', [])
                    
                    if len(outcomes) >= 2:
                        total_implied_prob = sum(1/outcome['price'] for outcome in outcomes)
                        margin = (total_implied_prob - 1) * 100
                        margins.append(margin)
        
        return sum(margins) / len(margins) if margins else 0.0
    
    def _check_rate_limit(self) -> bool:
        """Check if we can make another API request"""
        
        # Simple monthly limit check
        if self.requests_made >= self.max_requests_per_month:
            return False
        
        # Could add more sophisticated rate limiting here
        return True
    
    async def get_odds_for_match(self, sport_key: str, home_team: str, away_team: str) -> Optional[OddsData]:
        """Get odds for a specific match"""
        
        sport_odds = await self._fetch_sport_odds(sport_key, ['h2h', 'spreads', 'totals'])
        
        # Find matching match
        for odds_data in sport_odds:
            if (odds_data.home_team.lower() == home_team.lower() and 
                odds_data.away_team.lower() == away_team.lower()):
                return odds_data
        
        return None
    
    async def monitor_odds_movement(self, sport_key: str, duration_minutes: int = 60) -> Dict[str, Any]:
        """Monitor odds movement over time"""
        
        logger.info(f"📊 Monitoring odds movement for {duration_minutes} minutes...")
        
        initial_odds = await self._fetch_sport_odds(sport_key, ['h2h'])
        movement_data = {}
        
        # Store initial odds
        for odds_data in initial_odds:
            match_key = f"{odds_data.home_team}_vs_{odds_data.away_team}"
            movement_data[match_key] = {
                'initial_odds': odds_data.best_odds,
                'movements': []
            }
        
        # Monitor for specified duration
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        while datetime.now() < end_time:
            await asyncio.sleep(300)  # Check every 5 minutes
            
            current_odds = await self._fetch_sport_odds(sport_key, ['h2h'])
            
            for odds_data in current_odds:
                match_key = f"{odds_data.home_team}_vs_{odds_data.away_team}"
                
                if match_key in movement_data:
                    # Calculate movement
                    initial = movement_data[match_key]['initial_odds']
                    current = odds_data.best_odds
                    
                    movement = self._calculate_odds_movement(initial, current)
                    
                    if movement:
                        movement_data[match_key]['movements'].append({
                            'timestamp': datetime.now(),
                            'movement': movement
                        })
        
        return movement_data
    
    def _calculate_odds_movement(self, initial_odds: Dict, current_odds: Dict) -> Optional[Dict[str, Any]]:
        """Calculate odds movement between two time points"""
        
        movements = {}
        
        for market, outcomes in initial_odds.items():
            if market in current_odds:
                for outcome, initial_odd in outcomes.items():
                    if outcome in current_odds[market]:
                        current_odd = current_odds[market][outcome]
                        
                        if initial_odd != current_odd:
                            change_percentage = ((current_odd - initial_odd) / initial_odd) * 100
                            
                            movements[f"{market}_{outcome}"] = {
                                'initial': initial_odd,
                                'current': current_odd,
                                'change_percentage': change_percentage
                            }
        
        return movements if movements else None
    
    def get_api_usage_stats(self) -> Dict[str, Any]:
        """Get API usage statistics"""
        
        return {
            'requests_made': self.requests_made,
            'requests_remaining': self.max_requests_per_month - self.requests_made,
            'last_request': self.last_request_time.isoformat() if self.last_request_time else None,
            'usage_percentage': (self.requests_made / self.max_requests_per_month) * 100
        }

async def main():
    """Test The Odds API integration"""
    print("📊 THE ODDS API INTEGRATION TEST")
    print("=" * 50)
    
    # Initialize with API key
    odds_api = OddsAPIIntegration()
    
    print(f"🔑 API Key: {odds_api.api_key[:10]}...")
    print(f"📊 Supported Sports: {len(odds_api.supported_sports)}")
    
    # Test 1: Get live odds
    print(f"\n🔍 Test 1: Fetching live odds...")
    
    try:
        live_odds = await odds_api.get_live_odds(['soccer_epl', 'tennis_atp'], ['h2h'])
        
        print(f"✅ Retrieved odds for {len(live_odds)} matches")
        
        if live_odds:
            # Show first match details
            first_match = live_odds[0]
            print(f"\n📊 Sample Match: {first_match.home_team} vs {first_match.away_team}")
            print(f"🏆 Sport: {first_match.sport_title}")
            print(f"📅 Time: {first_match.commence_time}")
            print(f"📈 Market Margin: {first_match.market_margin:.2f}%")
            
            if first_match.best_odds:
                print(f"💰 Best Odds: {first_match.best_odds}")
            
            if first_match.arbitrage_opportunity:
                arb = first_match.arbitrage_opportunity
                print(f"🎯 Arbitrage: {arb['profit_margin']:.2f}% profit possible")
            
            if first_match.value_bets:
                print(f"💎 Value Bets: {len(first_match.value_bets)} opportunities")
                for vb in first_match.value_bets[:2]:
                    print(f"   • {vb['outcome']}: {vb['value_percentage']:.1f}% value")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: API usage stats
    print(f"\n📈 API Usage Statistics:")
    stats = odds_api.get_api_usage_stats()
    print(f"• Requests Made: {stats['requests_made']}")
    print(f"• Requests Remaining: {stats['requests_remaining']}")
    print(f"• Usage: {stats['usage_percentage']:.1f}%")
    
    print(f"\n✅ The Odds API integration test completed!")

if __name__ == "__main__":
    asyncio.run(main())
