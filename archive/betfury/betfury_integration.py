#!/usr/bin/env python3
"""
🎰 BETFURY.IO INTEGRATION
========================
Integration with Betfury.io betting platform to generate direct betting links
for all match opportunities identified by the betting intelligence system.

Features:
- 🔗 Direct betting page links for each match
- 🎯 Market-specific URLs for quick betting
- 📱 Mobile-optimized links
- 🏆 Sport-specific page routing
- 💰 Affiliate link support
- 🔄 URL validation and formatting
"""

import logging
import urllib.parse
from datetime import datetime
from typing import Dict, List, Optional, Any
import re

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BetfuryIntegration:
    """Integration with Betfury.io betting platform"""
    
    def __init__(self, affiliate_code: str = None):
        """Initialize Betfury integration"""
        logger.info("🎰 Initializing Betfury.io Integration...")
        
        # Betfury base URLs
        self.base_url = "https://betfury.io"
        self.sports_base = f"{self.base_url}/sports"
        
        # Affiliate code for referrals (optional)
        self.affiliate_code = affiliate_code
        
        # Sport URL mappings
        self.sport_urls = {
            'football': f"{self.sports_base}/football",
            'soccer': f"{self.sports_base}/football",  # Alternative name
            'tennis': f"{self.sports_base}/tennis",
            'basketball': f"{self.sports_base}/basketball",
            'ice_hockey': f"{self.sports_base}/ice-hockey",
            'hockey': f"{self.sports_base}/ice-hockey",  # Alternative name
            'baseball': f"{self.sports_base}/baseball",
            'american_football': f"{self.sports_base}/american-football",
            'esports': f"{self.sports_base}/esports"
        }
        
        # League-specific URL patterns
        self.league_patterns = {
            # Football/Soccer
            'premier_league': 'england/premier-league',
            'la_liga': 'spain/laliga',
            'bundesliga': 'germany/bundesliga',
            'serie_a': 'italy/serie-a',
            'ligue_1': 'france/ligue-1',
            'champions_league': 'europe/champions-league',
            'europa_league': 'europe/europa-league',
            
            # Tennis
            'atp_masters': 'atp',
            'wta_premier': 'wta',
            'grand_slam': 'grand-slam',
            'wimbledon': 'wimbledon',
            'us_open': 'us-open',
            'french_open': 'french-open',
            'australian_open': 'australian-open',
            
            # Basketball
            'nba': 'usa/nba',
            'euroleague': 'europe/euroleague',
            'ncaa': 'usa/ncaa',
            
            # Ice Hockey
            'nhl': 'usa/nhl',
            'khl': 'russia/khl'
        }
        
        # Market type mappings for Betfury
        self.market_mappings = {
            'match_winner': 'moneyline',
            '1x2': 'match-result',
            'over_under': 'totals',
            'over_under_2.5': 'total-goals',
            'both_teams_score': 'both-teams-to-score',
            'asian_handicap': 'handicap',
            'correct_score': 'correct-score',
            'first_goal_scorer': 'first-goalscorer',
            'double_chance': 'double-chance',
            'draw_no_bet': 'draw-no-bet'
        }
        
        logger.info("✅ Betfury.io Integration initialized")
    
    def generate_match_link(self, home_team: str, away_team: str, sport: str, 
                           league: str = None, market: str = None) -> str:
        """Generate direct Betfury link for a specific match"""
        
        # Normalize sport name
        sport_normalized = self._normalize_sport_name(sport)
        
        # Get base sport URL
        sport_url = self.sport_urls.get(sport_normalized, self.sports_base)
        
        # Add league if available
        if league:
            league_pattern = self._get_league_pattern(league)
            if league_pattern:
                sport_url = f"{sport_url}/{league_pattern}"
        
        # Generate match-specific URL
        match_slug = self._create_match_slug(home_team, away_team)
        match_url = f"{sport_url}/{match_slug}"
        
        # Add market parameter if specified
        if market:
            market_param = self.market_mappings.get(market.lower(), market)
            match_url = f"{match_url}?market={market_param}"
        
        # Add affiliate code if available
        if self.affiliate_code:
            separator = '&' if '?' in match_url else '?'
            match_url = f"{match_url}{separator}ref={self.affiliate_code}"
        
        return match_url
    
    def generate_sport_link(self, sport: str, league: str = None) -> str:
        """Generate link to sport or league page"""
        
        sport_normalized = self._normalize_sport_name(sport)
        sport_url = self.sport_urls.get(sport_normalized, self.sports_base)
        
        if league:
            league_pattern = self._get_league_pattern(league)
            if league_pattern:
                sport_url = f"{sport_url}/{league_pattern}"
        
        # Add affiliate code if available
        if self.affiliate_code:
            sport_url = f"{sport_url}?ref={self.affiliate_code}"
        
        return sport_url
    
    def generate_market_link(self, home_team: str, away_team: str, sport: str, 
                           market: str, league: str = None) -> str:
        """Generate direct link to specific market for a match"""
        
        base_match_url = self.generate_match_link(home_team, away_team, sport, league)
        
        # Remove existing query parameters
        if '?' in base_match_url:
            base_match_url = base_match_url.split('?')[0]
        
        # Add market-specific parameters
        market_param = self.market_mappings.get(market.lower(), market)
        market_url = f"{base_match_url}?market={market_param}"
        
        # Add affiliate code if available
        if self.affiliate_code:
            market_url = f"{market_url}&ref={self.affiliate_code}"
        
        return market_url
    
    def generate_multiple_links(self, match_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate multiple betting links for a match"""
        
        home_team = match_data.get('home_team', '')
        away_team = match_data.get('away_team', '')
        sport = match_data.get('sport', '')
        league = match_data.get('league', '')
        
        links = {}
        
        # Main match page
        links['main'] = self.generate_match_link(home_team, away_team, sport, league)
        
        # Common markets
        common_markets = ['match_winner', 'over_under', 'both_teams_score', 'asian_handicap']
        
        for market in common_markets:
            market_name = market.replace('_', ' ').title()
            links[market_name] = self.generate_market_link(
                home_team, away_team, sport, market, league
            )
        
        return links
    
    def create_betting_buttons(self, match_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Create betting button data for Telegram inline keyboards"""
        
        links = self.generate_multiple_links(match_data)
        
        buttons = []
        
        # Main betting button
        buttons.append({
            'text': '🎰 Bet on Betfury.io',
            'url': links['main']
        })
        
        # Market-specific buttons
        market_buttons = [
            ('💰 Match Winner', links.get('Match Winner')),
            ('📊 Over/Under', links.get('Over Under')),
            ('⚽ Both Teams Score', links.get('Both Teams Score')),
            ('🎯 Asian Handicap', links.get('Asian Handicap'))
        ]
        
        for text, url in market_buttons:
            if url:
                buttons.append({
                    'text': text,
                    'url': url
                })
        
        return buttons
    
    def _normalize_sport_name(self, sport: str) -> str:
        """Normalize sport name for URL generation"""
        
        sport_lower = sport.lower().strip()
        
        # Handle common variations
        sport_mappings = {
            'soccer': 'football',
            'american_football': 'american_football',
            'ice_hockey': 'ice_hockey',
            'hockey': 'ice_hockey'
        }
        
        return sport_mappings.get(sport_lower, sport_lower)
    
    def _get_league_pattern(self, league: str) -> Optional[str]:
        """Get URL pattern for league"""
        
        league_lower = league.lower().replace(' ', '_')
        
        # Try exact match first
        if league_lower in self.league_patterns:
            return self.league_patterns[league_lower]
        
        # Try partial matches
        for pattern_key, pattern_value in self.league_patterns.items():
            if pattern_key in league_lower or league_lower in pattern_key:
                return pattern_value
        
        return None
    
    def _create_match_slug(self, home_team: str, away_team: str) -> str:
        """Create URL slug for match"""
        
        # Clean team names
        home_clean = self._clean_team_name(home_team)
        away_clean = self._clean_team_name(away_team)
        
        # Create slug
        slug = f"{home_clean}-vs-{away_clean}"
        
        return slug.lower()
    
    def _clean_team_name(self, team_name: str) -> str:
        """Clean team name for URL"""
        
        # Remove special characters and replace spaces
        cleaned = re.sub(r'[^\w\s-]', '', team_name)
        cleaned = re.sub(r'\s+', '-', cleaned.strip())
        
        # Handle common team name variations
        replacements = {
            'fc': '',
            'football-club': '',
            'basketball-club': '',
            'hockey-club': ''
        }
        
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)
        
        # Remove multiple dashes
        cleaned = re.sub(r'-+', '-', cleaned)
        cleaned = cleaned.strip('-')
        
        return cleaned
    
    def validate_link(self, url: str) -> bool:
        """Validate if the generated link is properly formatted"""
        
        try:
            parsed = urllib.parse.urlparse(url)
            
            # Check if it's a valid Betfury URL
            if not parsed.netloc.endswith('betfury.io'):
                return False
            
            # Check if URL is properly formatted
            if not parsed.scheme in ['http', 'https']:
                return False
            
            return True
            
        except Exception:
            return False
    
    def create_telegram_message_with_links(self, opportunity: Dict[str, Any]) -> str:
        """Create Telegram message with Betfury betting links"""
        
        # Generate betting links
        links = self.generate_multiple_links(opportunity)
        
        # Create message with embedded links
        message_parts = []
        
        # Main betting link
        main_link = links.get('main', self.base_url)
        message_parts.append(f"🎰 **[BET NOW ON BETFURY.IO]({main_link})**")
        
        # Market-specific links
        market_links = []
        
        if 'Match Winner' in links:
            market_links.append(f"💰 [Match Winner]({links['Match Winner']})")
        
        if 'Over Under' in links:
            market_links.append(f"📊 [Over/Under]({links['Over Under']})")
        
        if 'Both Teams Score' in links:
            market_links.append(f"⚽ [Both Teams Score]({links['Both Teams Score']})")
        
        if 'Asian Handicap' in links:
            market_links.append(f"🎯 [Asian Handicap]({links['Asian Handicap']})")
        
        if market_links:
            message_parts.append("**Quick Markets:**")
            message_parts.extend(market_links)
        
        return '\n'.join(message_parts)
    
    def get_betfury_info(self) -> Dict[str, Any]:
        """Get information about Betfury platform"""
        
        return {
            'platform': 'Betfury.io',
            'description': 'Crypto betting platform with competitive odds',
            'features': [
                'Cryptocurrency betting',
                'Live betting available',
                'Competitive odds',
                'Multiple sports coverage',
                'Mobile-friendly interface'
            ],
            'supported_sports': list(self.sport_urls.keys()),
            'base_url': self.base_url,
            'affiliate_enabled': bool(self.affiliate_code)
        }

def main():
    """Test Betfury integration"""
    print("🎰 BETFURY.IO INTEGRATION TEST")
    print("=" * 40)
    
    # Initialize integration
    betfury = BetfuryIntegration(affiliate_code="tennisbot_2025")
    
    # Test match data
    test_match = {
        'home_team': 'Manchester City',
        'away_team': 'Arsenal',
        'sport': 'football',
        'league': 'Premier League'
    }
    
    print(f"🏆 Test Match: {test_match['home_team']} vs {test_match['away_team']}")
    print(f"🏟️ League: {test_match['league']}")
    
    # Test 1: Generate main match link
    print(f"\n🔗 Test 1: Main match link")
    main_link = betfury.generate_match_link(
        test_match['home_team'], 
        test_match['away_team'], 
        test_match['sport'], 
        test_match['league']
    )
    print(f"✅ Main Link: {main_link}")
    
    # Test 2: Generate market-specific links
    print(f"\n💰 Test 2: Market-specific links")
    markets = ['match_winner', 'over_under', 'both_teams_score']
    
    for market in markets:
        market_link = betfury.generate_market_link(
            test_match['home_team'],
            test_match['away_team'],
            test_match['sport'],
            market,
            test_match['league']
        )
        print(f"• {market.replace('_', ' ').title()}: {market_link}")
    
    # Test 3: Generate multiple links
    print(f"\n🎯 Test 3: Multiple links")
    all_links = betfury.generate_multiple_links(test_match)
    
    for link_type, url in all_links.items():
        print(f"• {link_type}: {url}")
    
    # Test 4: Create betting buttons
    print(f"\n📱 Test 4: Betting buttons for Telegram")
    buttons = betfury.create_betting_buttons(test_match)
    
    for button in buttons:
        print(f"• {button['text']}: {button['url']}")
    
    # Test 5: Create Telegram message with links
    print(f"\n📨 Test 5: Telegram message with links")
    
    opportunity = {
        'home_team': 'Manchester City',
        'away_team': 'Arsenal',
        'sport': 'football',
        'league': 'Premier League',
        'win_probability': 0.75,
        'expected_roi': 18.5
    }
    
    telegram_message = betfury.create_telegram_message_with_links(opportunity)
    print(telegram_message)
    
    # Test 6: Platform info
    print(f"\n📊 Test 6: Platform information")
    info = betfury.get_betfury_info()
    print(f"Platform: {info['platform']}")
    print(f"Supported Sports: {len(info['supported_sports'])}")
    print(f"Affiliate Enabled: {info['affiliate_enabled']}")
    
    print(f"\n✅ Betfury.io integration test completed!")

if __name__ == "__main__":
    main()
