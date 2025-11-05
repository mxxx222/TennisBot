#!/usr/bin/env python3
"""
API Football Integration Scraper
================================

Integrates with API Football (RapidAPI) for:
- Base match statistics and metadata
- Prematch data and team information
- League standings and fixtures
- Player statistics and injuries
- Historical data and form analysis

This serves as the foundation data source that can be enhanced
with real-time data from other scrapers.
"""

import asyncio
import aiohttp
import time
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import logging
from urllib.parse import quote
import hashlib
import random

logger = logging.getLogger(__name__)

class APIFootballScraper:
    """
    API Football integration for comprehensive football data
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = "https://api-football-v1.p.rapidapi.com"
        self.api_key = config.get('api_key', '')
        self.host = "api-football-v1.p.rapidapi.com"
        
        # Rate limiting
        self.rate_limit = config.get('rate_limit', 10)  # requests per minute
        self.request_timestamps = []
        
        # Session
        self.session = None
        
        # Headers
        self.headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': self.host,
            'Content-Type': 'application/json'
        }
        
        # Cache
        self.cache = {}
        self.cache_timeout = config.get('cache_timeout', 300)  # 5 minutes
        
        # Supported leagues
        self.league_mapping = {
            'premier_league': 39,
            'la_liga': 140,
            'serie_a': 135,
            'bundesliga': 78,
            'ligue_1': 61,
            'champions_league': 2,
            'europa_league': 3,
            'world_cup': 1,
            'euros': 4
        }
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers=self.headers
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def scrape_match(self, match_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive match data from API Football
        """
        try:
            match_id = match_info.get('id')
            home_team = match_info.get('home_team', '')
            away_team = match_info.get('away_team', '')
            
            logger.info(f"🔍 Fetching API Football data: {home_team} vs {away_team}")
            
            # Get basic match information
            match_data = await self.get_match_details(match_id)
            
            if not match_data:
                logger.warning(f"⚠️ No API Football data found for match {match_id}")
                return None
            
            # Enrich with additional data
            enriched_data = await self.enrich_match_data(match_data, match_info)
            
            return enriched_data
            
        except Exception as e:
            logger.error(f"💥 Error scraping API Football: {e}")
            return None
    
    async def get_match_details(self, match_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed match information from API Football
        """
        try:
            # Check cache first
            cache_key = f"match_{match_id}"
            if cache_key in self.cache:
                cache_time, cached_data = self.cache[cache_key]
                if time.time() - cache_time < self.cache_timeout:
                    return cached_data
            
            # Make API request with rate limiting
            await self.rate_limit_request()
            
            url = f"{self.base_url}/v3/fixtures"
            params = {
                'id': match_id,
                'timezone': 'Europe/London'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data['response']:
                        match_data = data['response'][0]
                        
                        # Cache the result
                        self.cache[cache_key] = (time.time(), match_data)
                        return match_data
                        
                elif response.status == 429:
                    logger.warning("⏰ Rate limit exceeded, waiting...")
                    await asyncio.sleep(60)
                    return await self.get_match_details(match_id)
                else:
                    logger.warning(f"⚠️ API request failed: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"💥 Error getting match details: {e}")
            return None
    
    async def rate_limit_request(self):
        """
        Implement rate limiting for API requests
        """
        now = time.time()
        
        # Remove timestamps older than 1 minute
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if now - ts < 60
        ]
        
        # Check if we're at the limit
        if len(self.request_timestamps) >= self.rate_limit:
            sleep_time = 60 - (now - self.request_timestamps[0])
            if sleep_time > 0:
                logger.debug(f"🕐 Rate limit: sleeping {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
        
        # Add current timestamp
        self.request_timestamps.append(now)
    
    async def enrich_match_data(self, match_data: Dict[str, Any], original_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich match data with additional API Football information
        """
        try:
            enriched = {
                'match_id': match_data['fixture']['id'],
                'league': match_data['league']['name'],
                'home_team': match_data['teams']['home']['name'],
                'away_team': match_data['teams']['away']['name'],
                'home_logo': match_data['teams']['home']['logo'],
                'away_logo': match_data['teams']['away']['logo'],
                'status': match_data['fixture']['status']['short'],
                'minute': match_data['fixture']['status'].get('elapsed'),
                'timestamp': match_data['fixture']['timestamp'],
                'venue': {
                    'name': match_data['fixture']['venue']['name'],
                    'city': match_data['fixture']['venue']['city']
                },
                'referee': match_data['fixture'].get('referee', ''),
                'score': {
                    'home': match_data['goals']['home'] or 0,
                    'away': match_data['goals']['away'] or 0,
                    'halftime': {
                        'home': match_data['score']['halftime']['home'] or 0,
                        'away': match_data['score']['halftime']['away'] or 0
                    },
                    'fulltime': {
                        'home': match_data['score']['fulltime']['home'] or 0,
                        'away': match_data['score']['fulltime']['away'] or 0
                    },
                    'extratime': {
                        'home': match_data['score']['extratime']['home'],
                        'away': match_data['score']['extratime']['away']
                    },
                    'penalty': {
                        'home': match_data['score']['penalty']['home'],
                        'away': match_data['score']['penalty']['away']
                    }
                },
                'statistics': [],
                'lineups': [],
                'events': [],
                'players': [],
                'team_statistics': {}
            }
            
            # Get detailed statistics if match is live or finished
            if enriched['status'] in ['1H', '2H', 'HT', 'FT', 'AET', 'PEN', 'CANC', 'SUSP', 'INT']:
                await self.add_detailed_statistics(enriched, match_data['fixture']['id'])
            
            # Get team lineups
            await self.add_lineups(enriched, match_data['fixture']['id'])
            
            # Get match events
            await self.add_events(enriched, match_data['fixture']['id'])
            
            # Get player statistics
            await self.add_player_statistics(enriched, match_data['fixture']['id'])
            
            # Calculate form and additional metrics
            await self.add_team_form(enriched, match_data)
            
            return enriched
            
        except Exception as e:
            logger.error(f"💥 Error enriching match data: {e}")
            return {
                'match_id': original_info.get('id'),
                'home_team': original_info.get('home_team', ''),
                'away_team': original_info.get('away_team', ''),
                'status': 'UNKNOWN',
                'score': {'home': 0, 'away': 0}
            }
    
    async def add_detailed_statistics(self, match_data: Dict[str, Any], fixture_id: str):
        """
        Add detailed match statistics
        """
        try:
            await self.rate_limit_request()
            
            url = f"{self.base_url}/v3/fixtures/statistics"
            params = {'fixture': fixture_id}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data['response']:
                        for team_stat in data['response']:
                            team_name = team_stat['team']['name']
                            
                            team_statistics = {
                                'team': team_name,
                                'statistics': {}
                            }
                            
                            for stat in team_stat['statistics']:
                                stat_name = stat['type']
                                value = stat['value']
                                
                                # Parse numeric values
                                if value and isinstance(value, str):
                                    try:
                                        # Extract numbers from strings like "65%"
                                        numeric_value = re.findall(r'\d+', value.replace('%', ''))
                                        if numeric_value:
                                            value = float(numeric_value[0])
                                        else:
                                            value = 0
                                    except (ValueError, AttributeError):
                                        pass
                                
                                team_statistics['statistics'][stat_name] = value
                            
                            match_data['statistics'].append(team_statistics)
                            
        except Exception as e:
            logger.error(f"💥 Error adding detailed statistics: {e}")
    
    async def add_lineups(self, match_data: Dict[str, Any], fixture_id: str):
        """
        Add team lineups and formations
        """
        try:
            await self.rate_limit_request()
            
            url = f"{self.base_url}/v3/fixtures/lineups"
            params = {'fixture': fixture_id}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data['response']:
                        for lineup in data['response']:
                            team_lineup = {
                                'team': lineup['team']['name'],
                                'formation': lineup['formation'],
                                'start_xi': lineup['startXI'],
                                'substitutes': lineup['substitutes'],
                                'coach': lineup.get('coach', {})
                            }
                            
                            match_data['lineups'].append(team_lineup)
                            
        except Exception as e:
            logger.error(f"💥 Error adding lineups: {e}")
    
    async def add_events(self, match_data: Dict[str, Any], fixture_id: str):
        """
        Add match events (goals, cards, substitutions, etc.)
        """
        try:
            await self.rate_limit_request()
            
            url = f"{self.base_url}/v3/fixtures/events"
            params = {'fixture': fixture_id}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data['response']:
                        for event in data['response']:
                            event_data = {
                                'time': {
                                    'elapsed': event['time']['elapsed'],
                                    'extra': event['time'].get('extra')
                                },
                                'team': event['team']['name'],
                                'player': event['player']['name'],
                                'assist': event.get('assist', {}).get('name', ''),
                                'type': event['type'],
                                'detail': event['detail'],
                                'comments': event.get('comments', '')
                            }
                            
                            match_data['events'].append(event_data)
                        
                        # Sort events by time
                        match_data['events'].sort(key=lambda x: x['time']['elapsed'])
                            
        except Exception as e:
            logger.error(f"💥 Error adding events: {e}")
    
    async def add_player_statistics(self, match_data: Dict[str, Any], fixture_id: str):
        """
        Add player statistics for the match
        """
        try:
            await self.rate_limit_request()
            
            url = f"{self.base_url}/v3/fixtures/players"
            params = {'fixture': fixture_id}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data['response']:
                        for team_players in data['response']:
                            team_name = team_players['team']['name']
                            
                            for player in team_players['players']:
                                if player['statistics']:
                                    player_stats = {
                                        'team': team_name,
                                        'player': player['player']['name'],
                                        'number': player['player']['number'],
                                        'position': player['player']['pos'],
                                        'statistics': {}
                                    }
                                    
                                    for stat in player['statistics']:
                                        if stat['statistics']:
                                            for stat_detail in stat['statistics']:
                                                stat_name = stat_detail['type']
                                                value = stat_detail['value']
                                                player_stats['statistics'][stat_name] = value
                                    
                                    match_data['players'].append(player_stats)
                            
        except Exception as e:
            logger.error(f"💥 Error adding player statistics: {e}")
    
    async def add_team_form(self, match_data: Dict[str, Any], match_info: Dict[str, Any]):
        """
        Add team form and additional metrics
        """
        try:
            # Get league ID
            league_id = self.get_league_id(match_info.get('league', ''))
            
            if league_id:
                # Get recent form for both teams
                home_form = await self.get_team_recent_form(
                    match_data['home_team'], 
                    league_id, 
                    season=2023
                )
                
                away_form = await self.get_team_recent_form(
                    match_data['away_team'], 
                    league_id, 
                    season=2023
                )
                
                match_data['team_form'] = {
                    'home': home_form,
                    'away': away_form
                }
                
                # Calculate form strength
                match_data['form_strength'] = {
                    'home': self.calculate_form_strength(home_form),
                    'away': self.calculate_form_strength(away_form)
                }
                
        except Exception as e:
            logger.error(f"💥 Error adding team form: {e}")
    
    async def get_team_recent_form(self, team_name: str, league_id: int, season: int = 2023, matches: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent form for a team
        """
        try:
            # Get team ID
            team_id = await self.get_team_id(team_name, league_id, season)
            
            if not team_id:
                return []
            
            await self.rate_limit_request()
            
            # Get recent fixtures
            url = f"{self.base_url}/v3/fixtures"
            params = {
                'team': team_id,
                'league': league_id,
                'season': season,
                'status': 'FT',
                'from': '2023-08-01',
                'to': '2024-05-31'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data['response']:
                        recent_fixtures = data['response'][-matches:]
                        
                        form_data = []
                        for fixture in recent_fixtures:
                            home_team = fixture['teams']['home']['name']
                            away_team = fixture['teams']['away']['name']
                            home_goals = fixture['goals']['home'] or 0
                            away_goals = fixture['goals']['away'] or 0
                            
                            # Determine result
                            if home_goals > away_goals:
                                result = 'W' if home_team == team_name else 'L'
                            elif away_goals > home_goals:
                                result = 'L' if home_team == team_name else 'W'
                            else:
                                result = 'D'
                            
                            form_data.append({
                                'date': fixture['fixture']['date'],
                                'opponent': away_team if home_team == team_name else home_team,
                                'home': home_team == team_name,
                                'goals_for': home_goals if home_team == team_name else away_goals,
                                'goals_against': away_goals if home_team == team_name else home_goals,
                                'result': result
                            })
                        
                        return form_data
                        
            return []
            
        except Exception as e:
            logger.error(f"💥 Error getting team form: {e}")
            return []
    
    async def get_team_id(self, team_name: str, league_id: int, season: int) -> Optional[int]:
        """
        Get team ID from team name
        """
        try:
            await self.rate_limit_request()
            
            url = f"{self.base_url}/v3/teams"
            params = {
                'search': team_name,
                'league': league_id,
                'season': season
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data['response']:
                        for team in data['response']:
                            if team_name.lower() in team['team']['name'].lower():
                                return team['team']['id']
                        
            return None
            
        except Exception as e:
            logger.error(f"💥 Error getting team ID: {e}")
            return None
    
    def get_league_id(self, league_name: str) -> Optional[int]:
        """
        Get league ID from league name
        """
        league_lower = league_name.lower()
        
        # Direct mapping
        for key, league_id in self.league_mapping.items():
            if key.replace('_', ' ') in league_lower or key in league_lower:
                return league_id
        
        # Partial matches
        if 'premier' in league_lower or 'epl' in league_lower:
            return 39
        elif 'la liga' in league_lower or 'primera' in league_lower:
            return 140
        elif 'serie' in league_lower:
            return 135
        elif 'bundesliga' in league_lower:
            return 78
        elif 'ligue' in league_lower or 'l1' in league_lower:
            return 61
        elif 'champions' in league_lower:
            return 2
        elif 'europa' in league_lower:
            return 3
        
        return None
    
    def calculate_form_strength(self, form_data: List[Dict[str, Any]]) -> float:
        """
        Calculate form strength from recent results
        """
        try:
            if not form_data:
                return 5.0  # Neutral strength
            
            # Points system: W=3, D=1, L=0
            points = 0
            total_games = len(form_data)
            
            for match in form_data:
                if match['result'] == 'W':
                    points += 3
                elif match['result'] == 'D':
                    points += 1
            
            # Return average points per game (0-10 scale)
            return (points / (total_games * 3)) * 10
            
        except Exception as e:
            logger.error(f"💥 Error calculating form strength: {e}")
            return 5.0
    
    async def get_live_fixtures(self, leagues: List[int] = None) -> List[Dict[str, Any]]:
        """
        Get live fixtures across specified leagues
        """
        try:
            if not leagues:
                leagues = list(self.league_mapping.values())
            
            live_fixtures = []
            
            for league_id in leagues[:5]:  # Limit to 5 leagues to avoid rate limits
                await self.rate_limit_request()
                
                url = f"{self.base_url}/v3/fixtures"
                params = {
                    'league': league_id,
                    'season': 2023,
                    'live': 'all'
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data['response']:
                            for fixture in data['response']:
                                live_fixtures.append({
                                    'id': fixture['fixture']['id'],
                                    'home_team': fixture['teams']['home']['name'],
                                    'away_team': fixture['teams']['away']['name'],
                                    'league': fixture['league']['name'],
                                    'status': fixture['fixture']['status']['short'],
                                    'minute': fixture['fixture']['status'].get('elapsed'),
                                    'score': {
                                        'home': fixture['goals']['home'] or 0,
                                        'away': fixture['goals']['away'] or 0
                                    },
                                    'timestamp': fixture['fixture']['timestamp']
                                })
            
            return live_fixtures
            
        except Exception as e:
            logger.error(f"💥 Error getting live fixtures: {e}")
            return []
    
    async def get_team_statistics(self, team_name: str, league_id: int, season: int = 2023) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive team statistics
        """
        try:
            team_id = await self.get_team_id(team_name, league_id, season)
            
            if not team_id:
                return None
            
            await self.rate_limit_request()
            
            url = f"{self.base_url}/v3/teams/statistics"
            params = {
                'team': team_id,
                'league': league_id,
                'season': season
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data['response']:
                        return data['response']
            
            return None
            
        except Exception as e:
            logger.error(f"💥 Error getting team statistics: {e}")
            return None
    
    def get_base_statistics(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract base statistics for the multi-source system
        """
        try:
            base_stats = {
                'shots': {'home': 0, 'away': 0},
                'shots_on_target': {'home': 0, 'away': 0},
                'possession': {'home': 50.0, 'away': 50.0},
                'corners': {'home': 0, 'away': 0},
                'fouls': {'home': 0, 'away': 0},
                'yellow_cards': {'home': 0, 'away': 0},
                'red_cards': {'home': 0, 'away': 0},
                'passes': {'home': 0, 'away': 0},
                'pass_accuracy': {'home': 0, 'away': 0},
                'offsides': {'home': 0, 'away': 0}
            }
            
            # Extract from statistics array
            for team_stat in match_data.get('statistics', []):
                team = team_stat['team']
                is_home = team == match_data.get('home_team', '')
                team_dict = 'home' if is_home else 'away'
                
                stats = team_stat['statistics']
                
                # Map API Football statistics to our format
                mappings = {
                    'Ball Possession': 'possession',
                    'Total Shots': 'shots',
                    'Shots on Target': 'shots_on_target',
                    'Corner Kicks': 'corners',
                    'Fouls': 'fouls',
                    'Yellow Cards': 'yellow_cards',
                    'Red Cards': 'red_cards',
                    'Total passes': 'passes',
                    'Passes %': 'pass_accuracy',
                    'Offsides': 'offsides'
                }
                
                for api_name, our_name in mappings.items():
                    value = stats.get(api_name, 0)
                    if isinstance(value, (int, float)):
                        base_stats[our_name][team_dict] = value
                    elif isinstance(value, str) and '%' in value:
                        try:
                            base_stats[our_name][team_dict] = float(value.replace('%', ''))
                        except ValueError:
                            pass
            
            return base_stats
            
        except Exception as e:
            logger.error(f"💥 Error extracting base statistics: {e}")
            return {
                'shots': {'home': 0, 'away': 0},
                'shots_on_target': {'home': 0, 'away': 0},
                'possession': {'home': 50.0, 'away': 50.0},
                'corners': {'home': 0, 'away': 0}
            }