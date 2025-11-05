"""
API Football Data Scraper - Educational Framework
Comprehensive data collection for betting pattern analysis

⚠️ EDUCATIONAL USE ONLY - NO REAL MONEY BETTING ⚠️
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import time
import random

class APIFootballScraper:
    """
    API Football.com data scraper for educational analysis
    
    Features:
    - Team statistics and form analysis
    - Head-to-head data
    - Live match data
    - League standings and ratings
    - Player availability data
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://v3.football.api-sports.io"
        self.session = None
        self.rate_limit_calls = 100  # Free tier daily limit
        self.rate_limit_remaining = self.rate_limit_calls
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting
        self.last_request_time = 0
        self.min_interval = 0.6  # 10 requests per minute max
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.init_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def init_session(self):
        """Initialize aiohttp session with proper headers"""
        headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': 'v3.football.api-sports.io'
        }
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        
        self.logger.info("API Football session initialized")
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make rate-limited API request"""
        
        # Rate limiting
        now = time.time()
        time_since_last = now - self.last_request_time
        if time_since_last < self.min_interval:
            await asyncio.sleep(self.min_interval - time_since_last)
        
        self.last_request_time = time.time()
        
        if self.rate_limit_remaining <= 0:
            self.logger.warning("API rate limit reached")
            return None
        
        try:
            url = f"{self.base_url}/{endpoint}"
            async with self.session.get(url, params=params) as response:
                self.rate_limit_remaining -= 1
                
                if response.status == 200:
                    data = await response.json()
                    self.logger.debug(f"API request successful: {endpoint}")
                    return data
                else:
                    self.logger.error(f"API request failed: {response.status} - {endpoint}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"API request error: {e}")
            return None
    
    async def get_live_fixtures(self) -> List[Dict]:
        """Get currently live matches with detailed data"""
        
        # Get today's live fixtures
        today = datetime.now().strftime("%Y-%m-%d")
        
        params = {
            'live': 'all',
            'date': today
        }
        
        data = await self._make_request('fixtures', params)
        
        if not data or 'response' not in data:
            return []
        
        fixtures = data['response']
        enriched_fixtures = []
        
        for fixture in fixtures:
            fixture_id = fixture['fixture']['id']
            
            # Get detailed statistics
            stats = await self.get_fixture_statistics(fixture_id)
            
            # Get events (goals, cards, etc.)
            events = await self.get_fixture_events(fixture_id)
            
            # Get lineups
            lineups = await self.get_fixture_lineups(fixture_id)
            
            enriched_fixture = {
                'fixture_id': fixture_id,
                'league': fixture['league']['name'],
                'league_id': fixture['league']['id'],
                'home_team': fixture['teams']['home']['name'],
                'home_team_id': fixture['teams']['home']['id'],
                'away_team': fixture['teams']['away']['name'],
                'away_team_id': fixture['teams']['away']['id'],
                'home_score': fixture['goals']['home'],
                'away_score': fixture['goals']['away'],
                'status': fixture['fixture']['status']['short'],
                'minute': fixture['fixture']['status']['elapsed'],
                'venue': fixture['fixture']['venue']['name'],
                'referee': fixture['fixture']['referee'],
                'statistics': stats,
                'events': events,
                'lineups': lineups,
                'timestamp': datetime.now().isoformat()
            }
            
            enriched_fixtures.append(enriched_fixture)
            
            # Add small delay to respect rate limits
            await asyncio.sleep(0.5)
        
        self.logger.info(f"Retrieved {len(enriched_fixtures)} live fixtures")
        return enriched_fixtures
    
    async def get_team_form(self, team_id: int, games: int = 5) -> Dict:
        """Get team's recent form (last N games)"""
        
        params = {
            'team': team_id,
            'season': 2024,
            'last': games
        }
        
        data = await self._make_request('fixtures', params)
        
        if not data or 'response' not in data:
            return {}
        
        fixtures = data['response']
        
        # Analyze form
        wins = losses = draws = goals_for = goals_against = 0
        home_wins = away_wins = 0
        
        for fixture in fixtures:
            home_goals = fixture['goals']['home']
            away_goals = fixture['goals']['away']
            
            if home_goals is None or away_goals is None:
                continue
            
            goals_for += home_goals + away_goals
            goals_against += fixture['goals']['home'] + fixture['goals']['away']
            
            # Win/Loss/Draw
            if home_goals > away_goals:
                wins += 1
                if fixture['teams']['home']['id'] == team_id:
                    home_wins += 1
            elif home_goals < away_goals:
                losses += 1
            else:
                draws += 1
        
        total_games = len(fixtures)
        
        return {
            'games_analyzed': total_games,
            'wins': wins,
            'losses': losses,
            'draws': draws,
            'win_rate': wins / total_games if total_games > 0 else 0,
            'avg_goals_for': goals_for / total_games if total_games > 0 else 0,
            'avg_goals_against': goals_against / total_games if total_games > 0 else 0,
            'home_wins': home_wins,
            'clean_sheets': 0  # Would need detailed stats
        }
    
    async def get_head_to_head(self, home_team_id: int, away_team_id: int, limit: int = 10) -> Dict:
        """Get head-to-head history between two teams"""
        
        params = {
            'team1': home_team_id,
            'team2': away_team_id,
            'season': 2024,
            'limit': limit
        }
        
        data = await self._make_request('fixtures/headtohead', params)
        
        if not data or 'response' not in data:
            return {}
        
        fixtures = data['response']
        
        # Analyze H2H
        team1_wins = team2_wins = draws = 0
        total_goals = 0
        
        for fixture in fixtures:
            home_goals = fixture['goals']['home']
            away_goals = fixture['goals']['away']
            
            if home_goals is None or away_goals is None:
                continue
            
            total_goals += home_goals + away_goals
            
            if home_goals > away_goals:
                team1_wins += 1
            elif home_goals < away_goals:
                team2_wins += 1
            else:
                draws += 1
        
        total_matches = len(fixtures)
        
        return {
            'total_matches': total_matches,
            'team1_wins': team1_wins,
            'team2_wins': team2_wins,
            'draws': draws,
            'team1_win_rate': team1_wins / total_matches if total_matches > 0 else 0,
            'avg_goals': total_goals / total_matches if total_matches > 0 else 0,
            'over_2_5_rate': 0.75 if total_goals / total_matches > 2.5 else 0.25,  # Approximation
            'under_2_5_rate': 0.25 if total_goals / total_matches > 2.5 else 0.75
        }
    
    async def get_team_elo_rating(self, team_id: int) -> float:
        """
        Calculate/estimate ELO rating for team
        This is a simplified version - real ELO is more complex
        """
        # Get team's recent performance
        form = await self.get_team_form(team_id)
        
        if not form:
            return 1500  # Default rating
        
        # Simplified ELO calculation
        base_rating = 1500
        form_bonus = (form['win_rate'] - 0.5) * 200  # ±100 points based on win rate
        goal_difference = (form['avg_goals_for'] - form['avg_goals_against']) * 20
        
        return max(1000, min(2500, base_rating + form_bonus + goal_difference))
    
    async def get_fixture_statistics(self, fixture_id: int) -> Dict:
        """Get detailed statistics for a fixture"""
        
        params = {'fixture': fixture_id}
        
        data = await self._make_request('fixtures/statistics', params)
        
        if not data or 'response' not in data:
            return {}
        
        stats = data['response'][0]  # First team statistics
        
        # Parse statistics
        home_stats = {}
        away_stats = {}
        
        for team_stats in stats['statistics']:
            team = team_stats['team']['name']
            
            for stat in team_stats['statistics']:
                stat_name = stat['type']
                stat_value = stat['value']
                
                if team == stats['teams']['home']['name']:
                    home_stats[stat_name] = stat_value
                else:
                    away_stats[stat_name] = stat_value
        
        return {
            'home_stats': home_stats,
            'away_stats': away_stats,
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_fixture_events(self, fixture_id: int) -> List[Dict]:
        """Get events (goals, cards, substitutions) for a fixture"""
        
        params = {'fixture': fixture_id}
        
        data = await self._make_request('fixtures/events', params)
        
        if not data or 'response' not in data:
            return []
        
        return data['response']
    
    async def get_fixture_lineups(self, fixture_id: int) -> Dict:
        """Get starting lineups and formation information"""
        
        params = {'fixture': fixture_id}
        
        data = await self._make_request('fixtures/lineups', params)
        
        if not data or 'response' not in data:
            return {}
        
        lineups = {}
        
        for team_lineup in data['response']:
            team_name = team_lineup['team']['name']
            lineups[team_name] = {
                'formation': team_lineup['formation'],
                'startXI': team_lineup['startXI'],
                'substitutes': team_lineup['substitutes']
            }
        
        return lineups
    
    async def get_league_standings(self, league_id: int, season: int = 2024) -> List[Dict]:
        """Get league standings for analysis"""
        
        params = {
            'league': league_id,
            'season': season
        }
        
        data = await self._make_request('standings', params)
        
        if not data or 'response' not in data:
            return []
        
        return data['response'][0]['league']['standings'][0]  # First table
    
    async def get_team_ratings(self, team_id: int) -> Dict:
        """Get comprehensive team ratings"""
        
        # Get team form
        form = await self.get_team_form(team_id)
        
        # Get recent fixtures for additional analysis
        params = {
            'team': team_id,
            'season': 2024,
            'last': 10
        }
        
        data = await self._make_request('fixtures', params)
        
        if not data or 'response' not in data:
            return {}
        
        # Calculate attack/defense ratings
        total_goals_for = 0
        total_goals_against = 0
        clean_sheets = 0
        
        for fixture in data['response']:
            home_goals = fixture['goals']['home']
            away_goals = fixture['goals']['away']
            
            if home_goals is None or away_goals is None:
                continue
            
            if fixture['teams']['home']['id'] == team_id:
                total_goals_for += home_goals
                total_goals_against += away_goals
                if away_goals == 0:
                    clean_sheets += 1
            else:
                total_goals_for += away_goals
                total_goals_against += home_goals
                if home_goals == 0:
                    clean_sheets += 1
        
        games = len(data['response'])
        
        return {
            'attack_rating': (total_goals_for / games * 10) if games > 0 else 5.0,
            'defense_rating': (10 - (total_goals_against / games * 10)) if games > 0 else 5.0,
            'clean_sheet_rate': clean_sheets / games if games > 0 else 0,
            'avg_goals_for': total_goals_for / games if games > 0 else 0,
            'avg_goals_against': total_goals_against / games if games > 0 else 0
        }
    
    async def enrich_live_matches(self, live_matches: List[Dict]) -> List[Dict]:
        """Enrich live matches with prematch data"""
        
        enriched_matches = []
        
        for match in live_matches:
            try:
                # Get prematch data
                home_team_id = match['home_team_id']
                away_team_id = match['away_team_id']
                league_id = match['league_id']
                
                # Fetch all prematch data
                home_form = await self.get_team_form(home_team_id)
                away_form = await self.get_team_form(away_team_id)
                h2h_data = await self.get_head_to_head(home_team_id, away_team_id)
                home_elo = await self.get_team_elo_rating(home_team_id)
                away_elo = await self.get_team_elo_rating(away_team_id)
                home_ratings = await self.get_team_ratings(home_team_id)
                away_ratings = await self.get_team_ratings(away_team_id)
                
                enriched_match = {
                    **match,
                    'prematch_data': {
                        'home_form': home_form,
                        'away_form': away_form,
                        'head_to_head': h2h_data,
                        'home_elo': home_elo,
                        'away_elo': away_elo,
                        'elo_difference': home_elo - away_elo,
                        'home_ratings': home_ratings,
                        'away_ratings': away_ratings,
                        'team_strength_diff': (home_ratings['attack_rating'] + home_ratings['defense_rating']) - 
                                             (away_ratings['attack_rating'] + away_ratings['defense_rating'])
                    }
                }
                
                enriched_matches.append(enriched_match)
                
                # Rate limiting delay
                await asyncio.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Error enriching match {match.get('fixture_id', 'unknown')}: {e}")
                continue
        
        self.logger.info(f"Enriched {len(enriched_matches)} matches with prematch data")
        return enriched_matches
    
    def save_data_to_csv(self, data: List[Dict], filename: str):
        """Save data to CSV for analysis"""
        if not data:
            return
        
        df = pd.json_normalize(data)
        df.to_csv(filename, index=False)
        self.logger.info(f"Data saved to {filename}")
    
    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'session') and self.session:
            asyncio.create_task(self.session.close())