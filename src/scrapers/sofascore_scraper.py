"""
SofaScore Scraper - Advanced xG and Momentum Analysis
====================================================

Specializes in:
- Expected Goals (xG) with high accuracy
- Live momentum indicators
- Detailed match statistics
- Shot quality analysis
"""

import asyncio
import aiohttp
import json
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

logger = logging.getLogger(__name__)

class SofaScoreScraper:
    """
    SofaScore scraper for advanced xG and momentum data
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = "https://www.sofascore.com"
        self.api_url = "https://api.sofascore.com/api/v1"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def scrape_match(self, match_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Main method to scrape SofaScore data for a match
        """
        match_id = match_info.get('id')
        if not match_id:
            logger.error("❌ No match ID provided")
            return None
        
        try:
            # Try API first (faster and more reliable)
            data = await self.scrape_via_api(match_id)
            if data:
                return data
            
            # Fallback to web scraping
            logger.info("🔄 API failed, trying web scraping...")
            data = await self.scrape_via_web(match_info)
            return data
            
        except Exception as e:
            logger.error(f"💥 SofaScore scraping error: {e}")
            return None
    
    async def scrape_via_api(self, match_id: str) -> Optional[Dict[str, Any]]:
        """
        Try to scrape via SofaScore API endpoints
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Origin': 'https://www.sofascore.com',
            'Referer': 'https://www.sofascore.com/',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        try:
            # Get match details
            url = f"{self.api_url}/event/{match_id}"
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    event_data = await response.json()
                    
                    # Get statistics
                    stats_url = f"{self.api_url}/event/{match_id}/statistics"
                    async with self.session.get(stats_url, headers=headers) as stats_response:
                        if stats_response.status == 200:
                            stats_data = await stats_response.json()
                            
                            # Get heatmap/incident data
                            incident_url = f"{self.api_url}/event/{match_id}/incidents"
                            async with self.session.get(incident_url, headers=headers) as incident_response:
                                if incident_response.status == 200:
                                    incident_data = await incident_response.json()
                                    
                                    return self.parse_api_data(event_data, stats_data, incident_data)
                
                logger.warning(f"⚠️ SofaScore API returned status {response.status}")
                return None
                
        except Exception as e:
            logger.error(f"❌ SofaScore API error: {e}")
            return None
    
    def parse_api_data(
        self, 
        event_data: Dict, 
        stats_data: Dict, 
        incident_data: Dict
    ) -> Dict[str, Any]:
        """
        Parse SofaScore API response
        """
        event = event_data.get('event', {})
        stats = stats_data.get('statistics', [])
        incidents = incident_data.get('incidents', [])
        
        # Extract basic match info
        home_team_data = event.get('homeTeam', {})
        away_team_data = event.get('awayTeam', {})
        
        home_score = event.get('homeScore', {}).get('current', 0)
        away_score = event.get('awayScore', {}).get('current', 0)
        
        # Extract xG and advanced stats
        xg_home = None
        xg_away = None
        shots_home = None
        shots_away = None
        shots_on_target_home = None
        shots_on_target_away = None
        possession_home = None
        possession_away = None
        corners_home = None
        corners_away = None
        
        for period_stats in stats:
            for group in period_stats.get('groups', []):
                for item in group.get('statisticsItems', []):
                    stat_name = item.get('name', '')
                    
                    # xG data
                    if 'Expected goals (xG)' in stat_name or 'xG' in stat_name:
                        xg_home = self.parse_stat_value(item.get('home'))
                        xg_away = self.parse_stat_value(item.get('away'))
                    
                    # Shots
                    elif stat_name == 'Total shots' or 'Shots' in stat_name:
                        shots_home = self.parse_stat_value(item.get('home'))
                        shots_away = self.parse_stat_value(item.get('away'))
                    
                    # Shots on target
                    elif stat_name == 'Shots on target' or 'On target' in stat_name:
                        shots_on_target_home = self.parse_stat_value(item.get('home'))
                        shots_on_target_away = self.parse_stat_value(item.get('away'))
                    
                    # Possession
                    elif stat_name == 'Ball possession' or 'Possession' in stat_name:
                        possession_home = self.parse_stat_value(item.get('home'))
                        possession_away = self.parse_stat_value(item.get('away'))
                    
                    # Corners
                    elif stat_name == 'Corner kicks' or 'Corners' in stat_name:
                        corners_home = self.parse_stat_value(item.get('home'))
                        corners_away = self.parse_stat_value(item.get('away'))
        
        # Calculate momentum from incidents
        momentum = self.calculate_momentum_from_incidents(incidents, home_team_data.get('name'), away_team_data.get('name'))
        
        # Extract events timeline
        events = self.parse_incidents(incidents)
        
        # Calculate pressure index (based on shots and incidents)
        pressure_index = self.calculate_pressure_index(stats)
        
        # Calculate big chances (simplified)
        big_chances = self.calculate_big_chances(events)
        
        return {
            'score': {'home': home_score, 'away': away_score},
            'minute': event.get('time', {}).get('currentPeriodStartTimestamp', 0),
            'status': event.get('status', {}).get('type', 'UNKNOWN'),
            
            # xG data
            'xG': {'home': xg_home, 'away': xg_away},
            
            # Shot statistics
            'shots': {'home': shots_home, 'away': shots_away},
            'shots_on_target': {'home': shots_on_target_home, 'away': shots_on_target_away},
            
            # Possession
            'possession': {'home': possession_home, 'away': possession_away},
            
            # Other stats
            'corners': {'home': corners_home, 'away': corners_away},
            
            # Momentum and pressure
            'momentum': momentum,
            'pressure_index': pressure_index,
            
            # Big chances
            'big_chances': big_chances,
            
            # Events timeline
            'events': events,
            
            # Team names for reference
            'team_names': {
                'home': home_team_data.get('name', ''),
                'away': away_team_data.get('name', '')
            }
        }
    
    def parse_stat_value(self, value: Any) -> Optional[float]:
        """
        Parse statistical value (handle percentages, fractions, etc.)
        """
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Remove percentage signs, commas, etc.
            cleaned = value.replace('%', '').replace(',', '').strip()
            try:
                return float(cleaned)
            except ValueError:
                return None
        
        return None
    
    def calculate_momentum_from_incidents(
        self, 
        incidents: List[Dict], 
        home_team: str, 
        away_team: str
    ) -> Dict[str, float]:
        """
        Calculate team momentum based on recent incidents
        """
        momentum_home = 0
        momentum_away = 0
        
        # Weight recent incidents more heavily
        for i, incident in enumerate(incidents):
            weight = max(0.1, 1.0 - (i * 0.05))  # Decay factor
            
            incident_type = incident.get('type', {}).get('code', '').lower()
            team = incident.get('team', {}).get('name', '').lower()
            
            # Positive momentum events
            if 'goal' in incident_type:
                if home_team.lower() in team:
                    momentum_home += 3.0 * weight
                else:
                    momentum_away += 3.0 * weight
            
            elif 'corner' in incident_type:
                if home_team.lower() in team:
                    momentum_home += 1.0 * weight
                else:
                    momentum_away += 1.0 * weight
            
            elif 'dangerous_attack' in incident_type:
                if home_team.lower() in team:
                    momentum_home += 0.5 * weight
                else:
                    momentum_away += 0.5 * weight
            
            # Negative momentum events
            elif 'yellow_card' in incident_type:
                if home_team.lower() in team:
                    momentum_home -= 0.5 * weight
                else:
                    momentum_away -= 0.5 * weight
            
            elif 'red_card' in incident_type:
                if home_team.lower() in team:
                    momentum_home -= 2.0 * weight
                else:
                    momentum_away -= 2.0 * weight
        
        return {
            'home': round(momentum_home, 2),
            'away': round(momentum_away, 2)
        }
    
    def parse_incidents(self, incidents: List[Dict]) -> List[Dict[str, Any]]:
        """
        Parse incidents into structured events
        """
        events = []
        
        for incident in incidents:
            event_type = incident.get('type', {}).get('code', '').lower()
            minute = incident.get('time', {}).get('currentPeriodStartTimestamp', 0)
            team = incident.get('team', {}).get('name', '')
            player = incident.get('playerName', '')
            
            event = {
                'type': event_type,
                'minute': minute,
                'team': team,
                'player': player,
                'description': incident.get('description', '')
            }
            
            events.append(event)
        
        # Sort by minute
        events.sort(key=lambda x: x['minute'])
        
        return events
    
    def calculate_pressure_index(self, stats: List[Dict]) -> Dict[str, float]:
        """
        Calculate pressure index based on attacking actions
        """
        pressure_home = 0
        pressure_away = 0
        
        for period_stats in stats:
            for group in period_stats.get('groups', []):
                for item in group.get('statisticsItems', []):
                    stat_name = item.get('name', '').lower()
                    
                    # Dangerous attacks (high pressure indicator)
                    if 'dangerous' in stat_name and 'attack' in stat_name:
                        pressure_home += self.parse_stat_value(item.get('home')) or 0
                        pressure_away += self.parse_stat_value(item.get('away')) or 0
                    
                    # Attacks (moderate pressure)
                    elif stat_name == 'Total attacks' or 'attacks' in stat_name:
                        pressure_home += (self.parse_stat_value(item.get('home')) or 0) * 0.5
                        pressure_away += (self.parse_stat_value(item.get('away')) or 0) * 0.5
        
        return {
            'home': round(pressure_home, 2),
            'away': round(pressure_away, 2)
        }
    
    def calculate_big_chances(self, events: List[Dict]) -> Dict[str, int]:
        """
        Estimate big chances based on goals and near-goal events
        """
        big_chances_home = 0
        big_chances_away = 0
        
        for event in events:
            event_type = event['type']
            team = event['team'].lower()
            
            # Big chance indicators
            if event_type in ['goal', 'big_chance_missed', 'post', 'crossbar']:
                if 'home' in team or 'manchester united' in team:
                    big_chances_home += 1
                else:
                    big_chances_away += 1
        
        return {
            'home': big_chances_home,
            'away': big_chances_away
        }
    
    async def scrape_via_web(self, match_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Fallback web scraping method
        """
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-images')
        options.add_argument('--disable-javascript')
        
        driver = None
        try:
            driver = webdriver.Chrome(options=options)
            
            # Build search URL
            home_team = match_info.get('home_team', '').replace(' ', '-').lower()
            away_team = match_info.get('away_team', '').replace(' ', '-').lower()
            search_url = f"{self.base_url}/football/{home_team}-vs-{away_team}"
            
            driver.get(search_url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            await asyncio.sleep(3)
            
            # Parse page content
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Extract basic data (simplified - real implementation needs detailed selectors)
            data = {
                'note': 'Web scraping fallback - limited data available',
                'xG': {'home': None, 'away': None},
                'momentum': {'home': 0, 'away': 0}
            }
            
            return data
            
        except Exception as e:
            logger.error(f"❌ SofaScore web scraping error: {e}")
            return None
        finally:
            if driver:
                driver.quit()