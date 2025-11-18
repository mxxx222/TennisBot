"""
FotMob Scraper - Lineups, Injuries, and Form Analysis
====================================================

Specializes in:
- Team lineups with player details
- Injury and suspension tracking
- Recent form analysis
- Player ratings and positions
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
import logging
from bs4 import BeautifulSoup
import re
import hashlib

logger = logging.getLogger(__name__)

class FotMobScraper:
    """
    FotMob scraper for lineups, injuries, and form
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = "https://www.fotmob.com"
        self.api_url = "https://www.fotmob.com/api"
        self.session = None
        
        # Headers for API requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)',
            'Accept': 'application/json',
            'x-fm-req': 'eyJib2R5Ijp7ImNvZGUiOjE1Nzg1MDB9fQ==',  # Sample token
            'Referer': 'https://www.fotmob.com/'
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def scrape_match(self, match_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Main method to scrape FotMob data for a match
        """
        match_id = match_info.get('id')
        if not match_id:
            logger.error("❌ No match ID provided for FotMob")
            return None
        
        try:
            # Try API first
            data = await self.scrape_via_api(match_id)
            if data:
                return data
            
            # Fallback to web scraping
            logger.info("🔄 FotMob API failed, trying web scraping...")
            data = await self.scrape_via_web(match_info)
            return data
            
        except Exception as e:
            logger.error(f"💥 FotMob scraping error: {e}")
            return None
    
    async def scrape_via_api(self, match_id: str) -> Optional[Dict[str, Any]]:
        """
        Scrape via FotMob API
        """
        try:
            # Get match details
            url = f"{self.api_url}/matchDetails?matchId={match_id}"
            
            async with self.session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.parse_fotmob_api_data(data)
                else:
                    logger.warning(f"⚠️ FotMob API returned status {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ FotMob API error: {e}")
            return None
    
    def parse_fotmob_api_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse FotMob API response
        """
        content = data.get('content', {})
        league = content.get('match', {}).get('league', {})
        home_team = content.get('homeTeam', {})
        away_team = content.get('awayTeam', {})
        
        # Parse lineups
        home_lineup = self.parse_lineup_data(home_team)
        away_lineup = self.parse_lineup_data(away_team)
        
        # Parse team news
        team_news = content.get('teamNews', {})
        home_injuries = self.parse_injuries(team_news.get('homeTeam', {}))
        away_injuries = self.parse_injuries(team_news.get('awayTeam', {}))
        
        # Parse form data
        home_form = self.parse_form_data(home_team)
        away_form = self.parse_form_data(away_team)
        
        # Parse recent results
        recent_results = self.parse_recent_results(content)
        
        # Calculate missing key players
        key_players_missing = {
            'home': self.identify_key_absences(home_injuries, home_lineup),
            'away': self.identify_key_absences(away_injuries, away_lineup)
        }
        
        # Calculate form strength
        form_strength = self.calculate_form_strength(home_form, away_form)
        
        return {
            # Lineups
            'lineups': {
                'home': home_lineup,
                'away': away_lineup
            },
            
            # Injuries and suspensions
            'injuries': {
                'home': home_injuries,
                'away': away_injuries
            },
            
            # Form data
            'form': {
                'home': home_form,
                'away': away_form
            },
            
            # Key player absences
            'key_players_missing': key_players_missing,
            
            # Form strength
            'form_strength': form_strength,
            
            # Recent results
            'recent_results': recent_results,
            
            # Team data for reference
            'team_data': {
                'home': {
                    'name': home_team.get('name', ''),
                    'id': home_team.get('id', 0),
                    'logo': home_team.get('imageUrl', '')
                },
                'away': {
                    'name': away_team.get('name', ''),
                    'id': away_team.get('id', 0),
                    'logo': away_team.get('imageUrl', '')
                }
            },
            
            # League info
            'league_info': {
                'name': league.get('name', ''),
                'country': league.get('country', '')
            }
        }
    
    def parse_lineup_data(self, team_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse team lineup from FotMob data
        """
        lineup = []
        
        # Try different lineup data structures
        lineup_data = team_data.get('lineup', {})
        players_data = team_data.get('players', [])
        
        if players_data:
            # New format with players array
            for player in players_data:
                player_info = {
                    'name': player.get('name', {}).get('fullName', ''),
                    'short_name': player.get('name', {}).get('shortName', ''),
                    'position': player.get('position'),
                    'rating': player.get('rating', {}).get('num') if player.get('rating') else None,
                    'shirt_number': player.get('shirtNumber'),
                    'is_captain': player.get('isCaptain', False),
                    'is_substitute': player.get('isSubstitute', False),
                    'age': player.get('age'),
                    'height': player.get('height'),
                    'nationality': player.get('nationality', [])
                }
                lineup.append(player_info)
        
        elif lineup_data:
            # Legacy format
            for player in lineup_data.get('players', []):
                player_info = {
                    'name': player.get('name', {}).get('fullName', ''),
                    'position': player.get('position'),
                    'rating': player.get('rating'),
                    'shirt_number': player.get('shirtNumber'),
                    'is_captain': player.get('isCaptain', False)
                }
                lineup.append(player_info)
        
        return lineup
    
    def parse_injuries(self, team_news: Dict[str, Any]) -> List[str]:
        """
        Parse injuries and suspensions from team news
        """
        unavailable_players = []
        
        # Check different injury data structures
        unavailable = team_news.get('unavailable', [])
        injured = team_news.get('injured', [])
        suspended = team_news.get('suspended', [])
        
        # Process unavailable players
        for player in unavailable:
            if isinstance(player, dict):
                name = player.get('name', {}).get('fullName', '')
                reason = player.get('reason', '')
                if name:
                    unavailable_players.append(f"{name} ({reason})")
            elif isinstance(player, str):
                unavailable_players.append(player)
        
        # Add injured players
        for player in injured:
            if isinstance(player, dict):
                name = player.get('name', {}).get('fullName', '')
                if name:
                    unavailable_players.append(f"{name} (injured)")
            elif isinstance(player, str):
                unavailable_players.append(f"{player} (injured)")
        
        # Add suspended players
        for player in suspended:
            if isinstance(player, dict):
                name = player.get('name', {}).get('fullName', '')
                reason = player.get('reason', '')
                if name:
                    unavailable_players.append(f"{name} ({reason})")
            elif isinstance(player, str):
                unavailable_players.append(f"{player} (suspended)")
        
        return unavailable_players
    
    def parse_form_data(self, team_data: Dict[str, Any]) -> List[str]:
        """
        Parse recent form data
        """
        recent_form = []
        
        # Try different form data structures
        form_data = team_data.get('recentForm', [])
        if not form_data:
            form_data = team_data.get('form', [])
        
        for result in form_data:
            if isinstance(result, dict):
                match_result = result.get('result', '')
                date = result.get('date', '')
                opponent = result.get('opponent', '')
                
                if match_result and date:
                    recent_form.append(f"{match_result} vs {opponent} ({date})")
            elif isinstance(result, str):
                recent_form.append(result)
        
        return recent_form[-5:]  # Last 5 matches
    
    def parse_recent_results(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse recent match results
        """
        results = []
        matches = content.get('matches', [])
        
        for match in matches[-5:]:  # Last 5 matches
            if isinstance(match, dict):
                result = {
                    'date': match.get('utcTime', ''),
                    'home_team': match.get('homeTeam', {}).get('name', ''),
                    'away_team': match.get('awayTeam', {}).get('name', ''),
                    'home_score': match.get('homeScore', {}).get('fullTime', 0),
                    'away_score': match.get('awayScore', {}).get('fullTime', 0),
                    'status': match.get('status', {}).get('utcTimeMillis', 0)
                }
                results.append(result)
        
        return results
    
    def identify_key_absences(self, injuries: List[str], lineup: List[Dict[str, Any]]) -> List[str]:
        """
        Identify key players who are missing due to injuries/suspensions
        """
        key_absences = []
        
        # Get player names from lineup
        player_names = {player['name'].lower() for player in lineup if player['name']}
        
        # Check for key player absences
        key_positions = ['GK', 'ST', 'CB', 'CM', 'LB', 'RB']  # Key positions
        injury_details = injuries.copy()
        
        for injury in injuries:
            # Extract player name from injury text
            name_match = re.match(r'^([^)]+)', injury)
            if name_match:
                player_name = name_match.group(1).strip().lower()
                
                # Check if this is a key player
                for player in lineup:
                    if player['name'].lower() == player_name:
                        position = player.get('position', '')
                        if position in key_positions:
                            key_absences.append(f"{player['name']} ({position}) - {injury}")
                        break
        
        return key_absences
    
    def calculate_form_strength(self, home_form: List[str], away_form: List[str]) -> Dict[str, float]:
        """
        Calculate form strength score for both teams
        """
        def form_score(form_list):
            score = 0
            matches = 0
            
            for result in form_list:
                if 'W' in result:  # Win
                    score += 3
                elif 'D' in result:  # Draw
                    score += 1
                elif 'L' in result:  # Loss
                    score += 0
                matches += 1
            
            return score / (matches * 3) if matches > 0 else 0.5  # Normalize to 0-1
        
        return {
            'home': form_score(home_form),
            'away': form_score(away_form)
        }
    
    async def scrape_via_web(self, match_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Fallback web scraping method
        """
        try:
            # Build match URL
            home_team = match_info.get('home_team', '').replace(' ', '-').lower()
            away_team = match_info.get('away_team', '').replace(' ', '-').lower()
            
            # FotMob uses matchId for URLs
            match_id = match_info.get('id', '')
            match_url = f"{self.base_url}/match/{match_id}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            async with self.session.get(match_url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Parse HTML for lineup information
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract basic lineup info (simplified)
                    home_players = []
                    away_players = []
                    
                    # This is a simplified implementation
                    # Real implementation would need detailed CSS selectors
                    
                    return {
                        'lineups': {
                            'home': home_players,
                            'away': away_players
                        },
                        'injuries': {
                            'home': [],
                            'away': []
                        },
                        'form': {
                            'home': [],
                            'away': []
                        },
                        'note': 'Web scraping fallback - limited data'
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"❌ FotMob web scraping error: {e}")
            return None