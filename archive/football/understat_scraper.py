#!/usr/bin/env python3
"""
Understat Advanced Analytics Scraper
===================================

Scrapes Understat for:
- Advanced xG models and shot quality
- Expected assists (xA) data
- Shot maps and location analysis
- Team performance metrics
- Player-level expected statistics

Understat provides some of the most sophisticated football analytics
available publicly, including detailed shot quality models.
"""

import asyncio
import aiohttp
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import logging
from urllib.parse import quote
import hashlib

logger = logging.getLogger(__name__)

class UnderstatScraper:
    """
    Advanced analytics scraper for Understat
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = "https://understat.com"
        self.api_url = "https://understat.com/plotA"
        
        self.session = None
        self.driver = None
        
        # Headers to mimic browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://understat.com/',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        # Cache for API data
        self.api_cache = {}
        self.cache_timeout = 300  # 5 minutes
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        if self.driver:
            self.driver.quit()
    
    async def scrape_match(self, match_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Scrape advanced analytics for a match
        """
        try:
            match_id = match_info.get('id')
            home_team = match_info.get('home_team', '')
            away_team = match_info.get('away_team', '')
            
            logger.info(f"🏥 Scraping Understat analytics: {home_team} vs {away_team}")
            
            # Get match data from Understat API
            match_data = await self.get_match_analytics(match_id)
            
            if not match_data:
                logger.warning(f"⚠️ No Understat data found for match {match_id}")
                return None
            
            # Parse and structure the data
            structured_data = await self.parse_match_data(match_data)
            
            return structured_data
            
        except Exception as e:
            logger.error(f"💥 Error scraping Understat: {e}")
            return None
    
    async def get_match_analytics(self, match_id: str) -> Optional[Dict[str, Any]]:
        """
        Get match analytics from Understat API
        """
        try:
            # Check cache first
            cache_key = f"match_{match_id}"
            if cache_key in self.api_cache:
                cache_time, cached_data = self.api_cache[cache_key]
                if time.time() - cache_time < self.cache_timeout:
                    return cached_data
            
            # Try direct API approach first
            api_data = await self.fetch_understat_api_data(match_id)
            
            if api_data:
                # Cache the result
                self.api_cache[cache_key] = (time.time(), api_data)
                return api_data
            
            # Fallback to web scraping
            web_data = await self.scrape_via_web(match_id)
            
            if web_data:
                self.api_cache[cache_key] = (time.time(), web_data)
                return web_data
            
            return None
            
        except Exception as e:
            logger.error(f"💥 Error getting Understat analytics: {e}")
            return None
    
    async def fetch_understat_api_data(self, match_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch data from Understat's internal API endpoints
        """
        try:
            # Understat uses JSONP endpoints - extract from main page first
            match_page = await self.fetch_match_page(match_id)
            
            if not match_page:
                return None
            
            # Extract JSON data from script tags
            json_data = self.extract_json_from_page(match_page)
            
            if json_data:
                return self.parse_understat_json(json_data)
            
            return None
            
        except Exception as e:
            logger.error(f"💥 Error fetching Understat API data: {e}")
            return None
    
    async def fetch_match_page(self, match_id: str) -> Optional[str]:
        """
        Fetch the main match page to extract API endpoints
        """
        try:
            # Search for match by teams first
            search_url = f"{self.base_url}/"
            
            async with self.session.get(search_url, headers=self.headers, timeout=10) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Extract league and match information from page
                    match_data = self.extract_match_from_page(content, match_id)
                    
                    if match_data:
                        # Now get the specific match page
                        match_url = f"{self.base_url}/match/{match_data.get('understat_id')}"
                        
                        async with self.session.get(match_url, headers=self.headers, timeout=10) as match_response:
                            if match_response.status == 200:
                                return await match_response.text()
            
            return None
            
        except Exception as e:
            logger.error(f"💥 Error fetching match page: {e}")
            return None
    
    def extract_match_from_page(self, content: str, match_id: str) -> Optional[Dict[str, Any]]:
        """
        Extract match information from Understat home page
        """
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for JSON data in script tags
            scripts = soup.find_all('script')
            
            for script in scripts:
                if script.string and 'xG' in script.string:
                    # Extract JSON data
                    json_match = re.search(r'JSON\.parse\("(.+?)"\)', script.string)
                    if json_match:
                        try:
                            # Decode escaped JSON
                            json_str = json_match.group(1).replace('\\"', '"')
                            data = json.loads(json_str)
                            
                            # Look for our match
                            for league in data.get('data', {}).values():
                                if isinstance(league, list):
                                    for match in league:
                                        if str(match.get('id')) == str(match_id):
                                            return {
                                                'understat_id': match.get('id'),
                                                'home_team': match.get('h'),
                                                'away_team': match.get('a'),
                                                'home_goals': match.get('hg'),
                                                'away_goals': match.get('ag'),
                                                'home_xg': match.get('hx'),
                                                'away_xg': match.get('ax')
                                            }
                        except json.JSONDecodeError:
                            continue
            
            return None
            
        except Exception as e:
            logger.error(f"💥 Error extracting match from page: {e}")
            return None
    
    def extract_json_from_page(self, content: str) -> Optional[str]:
        """
        Extract JSON data from Understat match page
        """
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for JSON data in script tags
            scripts = soup.find_all('script')
            
            for script in scripts:
                if script.string:
                    # Try to find JSON data
                    json_matches = re.findall(r'JSON\.parse\("(.+?)"\)', script.string)
                    
                    for json_str in json_matches:
                        try:
                            # Decode escaped JSON
                            decoded = json_str.replace('\\"', '"')
                            data = json.loads(decoded)
                            
                            # Check if this contains match data
                            if isinstance(data, dict) and ('shotsData' in data or 'rosterData' in data):
                                return decoded
                                
                        except json.JSONDecodeError:
                            continue
            
            return None
            
        except Exception as e:
            logger.error(f"💥 Error extracting JSON from page: {e}")
            return None
    
    def parse_understat_json(self, json_data: str) -> Dict[str, Any]:
        """
        Parse JSON data from Understat
        """
        try:
            data = json.loads(json_data)
            
            parsed_data = {
                'shots_data': [],
                'roster_data': [],
                'match_stats': {},
                'team_stats': {}
            }
            
            # Extract shots data
            if 'shotsData' in data:
                parsed_data['shots_data'] = data['shotsData']
            
            # Extract roster data
            if 'rosterData' in data:
                parsed_data['roster_data'] = data['rosterData']
            
            # Extract match statistics
            if 'matchData' in data:
                parsed_data['match_stats'] = data['matchData']
            
            return parsed_data
            
        except json.JSONDecodeError as e:
            logger.error(f"💥 Error parsing Understat JSON: {e}")
            return {}
    
    async def scrape_via_web(self, match_id: str) -> Optional[Dict[str, Any]]:
        """
        Fallback: Scrape using Selenium
        """
        try:
            if not self.driver:
                options = Options()
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                
                self.driver = webdriver.Chrome(options=options)
            
            # Search for match
            search_url = f"{self.base_url}/"
            self.driver.get(search_url)
            
            # Wait for page to load
            await asyncio.sleep(2)
            
            # Extract data from page
            page_source = self.driver.page_source
            return self.parse_understat_page(page_source)
            
        except Exception as e:
            logger.error(f"💥 Error scraping Understat via web: {e}")
            return None
    
    def parse_understat_page(self, content: str) -> Dict[str, Any]:
        """
        Parse Understat page content
        """
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract basic match information
            match_data = {
                'home_team': '',
                'away_team': '',
                'score': '',
                'shots': {'home': 0, 'away': 0},
                'shots_on_target': {'home': 0, 'away': 0},
                'xg': {'home': 0.0, 'away': 0.0},
                'xA': {'home': 0.0, 'away': 0.0}
            }
            
            # Try to extract xG data from script tags
            scripts = soup.find_all('script')
            
            for script in scripts:
                if script.string and 'xG' in script.string:
                    # Parse xG data
                    xg_data = self.parse_xg_from_script(script.string)
                    if xg_data:
                        match_data.update(xg_data)
            
            return match_data
            
        except Exception as e:
            logger.error(f"💥 Error parsing Understat page: {e}")
            return {}
    
    def parse_xg_from_script(self, script_content: str) -> Optional[Dict[str, Any]]:
        """
        Extract xG data from script content
        """
        try:
            # Look for xG data patterns
            xg_pattern = r'"xG":\s*\[([^\]]+)\]'
            xa_pattern = r'"xA":\s*\[([^\]]+)\]'
            
            xg_match = re.search(xg_pattern, script_content)
            xa_match = re.search(xa_pattern, script_content)
            
            xg_data = {}
            if xg_match:
                xg_values = [float(x) for x in xg_match.group(1).split(',')]
                if len(xg_values) >= 2:
                    xg_data['xg'] = {'home': xg_values[0], 'away': xg_values[1]}
            
            if xa_match:
                xa_values = [float(x) for x in xa_match.group(1).split(',')]
                if len(xa_values) >= 2:
                    xg_data['xA'] = {'home': xa_values[0], 'away': xa_values[1]}
            
            return xg_data if xg_data else None
            
        except Exception as e:
            logger.error(f"💥 Error parsing xG from script: {e}")
            return None
    
    async def parse_match_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and structure match data
        """
        try:
            structured_data = {
                'xG': {'home': 0.0, 'away': 0.0},
                'xA': {'home': 0.0, 'away': 0.0},
                'shots': {'home': 0, 'away': 0},
                'shots_on_target': {'home': 0, 'away': 0},
                'shot_locations': {'home': [], 'away': []},
                'shot_quality': {'home': [], 'away': []},
                'expected_points': {'home': 0.0, 'away': 0.0},
                'ppda': {'home': 0.0, 'away': 0.0},  # Passes allowed per defensive action
                'team_strength': {'home': 0.0, 'away': 0.0}
            }
            
            # Parse shots data
            if 'shots_data' in raw_data and raw_data['shots_data']:
                shots_data = raw_data['shots_data']
                
                home_shots = []
                away_shots = []
                
                for shot in shots_data:
                    try:
                        shot_info = {
                            'x': float(shot.get('X', 0)),
                            'y': float(shot.get('Y', 0)),
                            'xg': float(shot.get('xG', 0)),
                            'outcome': shot.get('result', 'Unknown'),
                            'player': shot.get('player', ''),
                            'assisted_by': shot.get('assisted_by', ''),
                            'minute': int(shot.get('minute', 0)),
                            'h_a': shot.get('h_a', ''),  # home or away
                            'type': shot.get('type', 'Open Play')
                        }
                        
                        if shot_info['h_a'] == 'h':
                            home_shots.append(shot_info)
                        else:
                            away_shots.append(shot_info)
                            
                    except (ValueError, TypeError) as e:
                        logger.warning(f"⚠️ Error parsing shot: {e}")
                        continue
                
                # Calculate aggregated stats
                structured_data['shots']['home'] = len(home_shots)
                structured_data['shots']['away'] = len(away_shots)
                structured_data['shots_on_target']['home'] = len([s for s in home_shots if s['outcome'] in ['Goal', 'Saved']])
                structured_data['shots_on_target']['away'] = len([s for s in away_shots if s['outcome'] in ['Goal', 'Saved']])
                
                # Total xG
                structured_data['xG']['home'] = sum(s['xg'] for s in home_shots)
                structured_data['xG']['away'] = sum(s['xg'] for s in away_shots)
                
                # Shot locations
                structured_data['shot_locations']['home'] = [(s['x'], s['y']) for s in home_shots]
                structured_data['shot_locations']['away'] = [(s['x'], s['y']) for s in away_shots]
                
                # Shot quality metrics
                structured_data['shot_quality']['home'] = [s['xg'] for s in home_shots]
                structured_data['shot_quality']['away'] = [s['xg'] for s in away_shots]
            
            # Parse roster data for xA and player ratings
            if 'roster_data' in raw_data and raw_data['roster_data']:
                roster_data = raw_data['roster_data']
                
                # Calculate xA from player data
                if isinstance(roster_data, list):
                    for team_data in roster_data:
                        try:
                            team_side = team_data.get('side', '').lower()
                            players = team_data.get('players', [])
                            
                            total_xa = 0.0
                            total_minutes = 0
                            
                            for player in players:
                                if isinstance(player, dict):
                                    player_xa = float(player.get('xA', 0))
                                    player_minutes = float(player.get('minutes', 0))
                                    
                                    total_xa += player_xa
                                    total_minutes += player_minutes
                            
                            if team_side == 'h' or team_side == 'home':
                                structured_data['xA']['home'] = total_xa
                            elif team_side == 'a' or team_side == 'away':
                                structured_data['xA']['away'] = total_xa
                                
                        except (ValueError, TypeError) as e:
                            logger.warning(f"⚠️ Error parsing roster data: {e}")
                            continue
            
            # Calculate derived metrics
            structured_data = self.calculate_derived_metrics(structured_data)
            
            return structured_data
            
        except Exception as e:
            logger.error(f"💥 Error parsing match data: {e}")
            return {
                'xG': {'home': 0.0, 'away': 0.0},
                'xA': {'home': 0.0, 'away': 0.0},
                'shots': {'home': 0, 'away': 0},
                'shots_on_target': {'home': 0, 'away': 0}
            }
    
    def calculate_derived_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate advanced metrics from Understat data
        """
        try:
            # Expected Points (xP) calculation
            home_xg = data['xG']['home']
            away_xg = data['xG']['away']
            
            # Simple xP calculation based on xG difference
            xg_diff = home_xg - away_xg
            data['expected_points']['home'] = 1.0 + (xg_diff * 0.5)  # Rough approximation
            data['expected_points']['away'] = 3.0 - data['expected_points']['home']
            
            # Shot quality metrics
            home_shots = data['shots']['home']
            away_shots = data['shots']['away']
            
            if home_shots > 0:
                data['avg_shot_xg'] = data['xG']['home'] / home_shots
            else:
                data['avg_shot_xg'] = 0.0
                
            if away_shots > 0:
                data['avg_shot_xg_away'] = data['xG']['away'] / away_shots
            else:
                data['avg_shot_xg_away'] = 0.0
            
            # Shot efficiency
            home_goals_est = data['xG']['home']
            away_goals_est = data['xG']['away']
            
            data['shot_efficiency'] = {
                'home': home_goals_est,
                'away': away_goals_est
            }
            
            return data
            
        except Exception as e:
            logger.error(f"💥 Error calculating derived metrics: {e}")
            return data
    
    async def get_team_season_data(self, team_name: str, league: str, season: str) -> Optional[Dict[str, Any]]:
        """
        Get team season statistics from Understat
        """
        try:
            # Search for team data
            search_url = f"{self.base_url}/"
            
            async with self.session.get(search_url, headers=self.headers) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Extract team data from page
                    team_data = self.extract_team_from_page(content, team_name, league, season)
                    
                    return team_data
            
            return None
            
        except Exception as e:
            logger.error(f"💥 Error getting team season data: {e}")
            return None
    
    def extract_team_from_page(self, content: str, team_name: str, league: str, season: str) -> Optional[Dict[str, Any]]:
        """
        Extract team data from Understat page
        """
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for JSON data containing team statistics
            scripts = soup.find_all('script')
            
            for script in scripts:
                if script.string and team_name.lower() in script.string.lower():
                    # Try to extract team data
                    json_match = re.search(r'JSON\.parse\("(.+?)"\)', script.string)
                    if json_match:
                        try:
                            json_str = json_match.group(1).replace('\\"', '"')
                            data = json.loads(json_str)
                            
                            # Search for team in the data
                            return self.find_team_in_data(data, team_name, league, season)
                            
                        except json.JSONDecodeError:
                            continue
            
            return None
            
        except Exception as e:
            logger.error(f"💥 Error extracting team from page: {e}")
            return None
    
    def find_team_in_data(self, data: Any, team_name: str, league: str, season: str) -> Optional[Dict[str, Any]]:
        """
        Find team data in the parsed JSON
        """
        try:
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                # Check if this is our team
                                if (str(item.get('team', '')).lower() == team_name.lower() or
                                    team_name.lower() in str(item.get('team', '')).lower()):
                                    
                                    return {
                                        'team': item.get('team', ''),
                                        'goals': item.get('goals', 0),
                                        'xGA': item.get('xGA', 0),
                                        'xG': item.get('xG', 0),
                                        'ppda': item.get('ppda', 0),
                                        'matches': item.get('matches', 0)
                                    }
                    
                    # Recursive search
                    result = self.find_team_in_data(value, team_name, league, season)
                    if result:
                        return result
            
            elif isinstance(data, list):
                for item in data:
                    result = self.find_team_in_data(item, team_name, league, season)
                    if result:
                        return result
            
            return None
            
        except Exception as e:
            logger.error(f"💥 Error finding team in data: {e}")
            return None
    
    def get_shot_quality_analysis(self, shot_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze shot quality from Understat data
        """
        try:
            if not shot_data:
                return {'quality_score': 0, 'big_chances': 0, 'average_xg': 0}
            
            # Calculate quality metrics
            total_xg = sum(shot.get('xg', 0) for shot in shot_data)
            avg_xg = total_xg / len(shot_data)
            
            # Count big chances (high xG shots)
            big_chances = len([s for s in shot_data if s.get('xg', 0) > 0.3])
            
            # Quality score based on average xG and big chances
            quality_score = (avg_xg * 10) + (big_chances * 2)
            
            return {
                'quality_score': quality_score,
                'big_chances': big_chances,
                'average_xg': avg_xg,
                'total_shots': len(shot_data),
                'total_xg': total_xg
            }
            
        except Exception as e:
            logger.error(f"💥 Error analyzing shot quality: {e}")
            return {'quality_score': 0, 'big_chances': 0, 'average_xg': 0}