"""
FlashScore Scraper - Ultra-Fast Live Score Updates
=================================================

Specializes in:
- Fastest live score updates
- Match events (goals, cards, subs)
- Minute-by-minute updates
- Real-time score changes
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Optional, Any
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re

logger = logging.getLogger(__name__)

class FlashScoreScraper:
    """
    FlashScore scraper for ultra-fast live updates
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = "https://www.flashscore.com"
        self.session = None
        
        # Mobile user agent for better API access
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.flashscore.com/'
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def scrape_match(self, match_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Main method to scrape FlashScore data for a match
        """
        match_id = match_info.get('id')
        if not match_id:
            logger.error("❌ No match ID provided for FlashScore")
            return None
        
        try:
            # Try multiple approaches
            data = await self.scrape_with_driver(match_info)
            if data:
                return data
            
            # Fallback to direct API
            data = await self.scrape_direct_api(match_info)
            if data:
                return data
            
            logger.warning("⚠️ FlashScore: All scraping methods failed")
            return None
            
        except Exception as e:
            logger.error(f"💥 FlashScore scraping error: {e}")
            return None
    
    async def scrape_with_driver(self, match_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Use Selenium with network monitoring for fastest updates
        """
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-images')
        options.add_argument('--disable-css')
        options.add_argument('--disable-javascript')  # Faster loading
        options.add_argument('--enable-logging')
        
        # Enable performance logging
        caps = webdriver.DesiredCapabilities.CHROME
        caps['goog:loggingPrefs'] = {'performance': 'ALL'}
        
        driver = None
        try:
            driver = webdriver.Chrome(options=options, desired_capabilities=caps)
            
            # Build match URL
            home_team = match_info.get('home_team', '').replace(' ', '-').lower()
            away_team = match_info.get('away_team', '').replace(' ', '-').lower()
            match_url = f"{self.base_url}/match/{match_id}"
            
            driver.get(match_url)
            
            # Wait for page to load
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait a bit for dynamic content
            await asyncio.sleep(2)
            
            # Parse page content
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Extract data
            data = self.parse_flashscore_page(soup)
            
            # Get network logs for API calls
            network_data = self.extract_network_calls(driver)
            if network_data:
                data.update(network_data)
            
            return data
            
        except Exception as e:
            logger.error(f"❌ FlashScore driver scraping error: {e}")
            return None
        finally:
            if driver:
                driver.quit()
    
    def parse_flashscore_page(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Parse FlashScore page content
        """
        try:
            # Extract basic match info
            score_elem = soup.find('div', class_='matchScore')
            if not score_elem:
                score_elem = soup.find('div', class_='detailScore')
            
            minute_elem = soup.find('div', class_='matchDetailHeader')
            if not minute_elem:
                minute_elem = soup.find('div', class_='time')
            
            # Parse score
            score = self.parse_score(score_elem)
            
            # Parse minute
            minute = self.parse_minute(minute_elem)
            
            # Parse events
            events = self.parse_events(soup)
            
            # Parse match status
            status = self.parse_status(soup)
            
            return {
                'score': score,
                'minute': minute,
                'status': status,
                'events': events,
                'last_update': time.time()
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing FlashScore page: {e}")
            return {}
    
    def parse_score(self, score_elem) -> Dict[str, int]:
        """
        Parse score from page element
        """
        if not score_elem:
            return {'home': 0, 'away': 0}
        
        # Try different score formats
        score_text = score_elem.get_text(strip=True)
        
        # Format: "0 - 0" or "0:0"
        score_match = re.search(r'(\d+)\s*[-:]\s*(\d+)', score_text)
        if score_match:
            return {
                'home': int(score_match.group(1)),
                'away': int(score_match.group(2))
            }
        
        # Try to extract from individual elements
        home_score = score_elem.find('span', class_='home')
        away_score = score_elem.find('span', class_='away')
        
        if home_score and away_score:
            try:
                return {
                    'home': int(home_score.get_text(strip=True)),
                    'away': int(away_score.get_text(strip=True))
                }
            except ValueError:
                pass
        
        return {'home': 0, 'away': 0}
    
    def parse_minute(self, minute_elem) -> int:
        """
        Parse current minute from page element
        """
        if not minute_elem:
            return 0
        
        minute_text = minute_elem.get_text(strip=True)
        
        # Extract minute number
        minute_match = re.search(r'(\d+)\'', minute_text)
        if minute_match:
            return int(minute_match.group(1))
        
        # Try other formats
        if 'HT' in minute_text:
            return 45  # Half time
        elif 'FT' in minute_text:
            return 90  # Full time
        elif 'ET' in minute_text:
            return 105  # Extra time
        
        return 0
    
    def parse_status(self, soup: BeautifulSoup) -> str:
        """
        Parse match status
        """
        # Look for status indicators
        status_indicators = [
            'div[class*="status"]',
            'div[class*="live"]',
            'span[class*="time"]'
        ]
        
        for selector in status_indicators:
            elem = soup.select_one(selector)
            if elem:
                status_text = elem.get_text(strip=True).lower()
                
                if 'live' in status_text:
                    return 'LIVE'
                elif 'half' in status_text:
                    return 'HT'
                elif 'full' in status_text or 'finished' in status_text:
                    return 'FT'
                elif 'extra' in status_text:
                    return 'ET'
                else:
                    return 'LIVE'  # Default for unknown
        
        return 'UNKNOWN'
    
    def parse_events(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Parse match events (goals, cards, substitutions)
        """
        events = []
        
        # Look for event containers
        event_containers = soup.find_all('div', class_=re.compile(r'event|incident|matchEvent'))
        
        for container in event_containers:
            try:
                event = self.parse_single_event(container)
                if event:
                    events.append(event)
            except Exception as e:
                logger.debug(f"⚠️ Error parsing single event: {e}")
                continue
        
        # Sort events by minute
        events.sort(key=lambda x: x.get('minute', 0))
        
        return events
    
    def parse_single_event(self, container) -> Optional[Dict[str, Any]]:
        """
        Parse single event from container
        """
        try:
            # Extract event type
            event_type = self.determine_event_type(container)
            if not event_type:
                return None
            
            # Extract minute
            minute_elem = container.find('div', class_=re.compile(r'time|minute'))
            minute = self.parse_minute(minute_elem) if minute_elem else 0
            
            # Extract player
            player_elem = container.find('div', class_=re.compile(r'participant|player'))
            player = player_elem.get_text(strip=True) if player_elem else ''
            
            # Extract team info
            team = self.extract_team_info(container)
            
            return {
                'type': event_type,
                'minute': minute,
                'player': player,
                'team': team,
                'description': container.get_text(strip=True)
            }
            
        except Exception as e:
            logger.debug(f"⚠️ Error parsing single event container: {e}")
            return None
    
    def determine_event_type(self, container) -> Optional[str]:
        """
        Determine event type from container
        """
        class_names = container.get('class', [])
        text_content = container.get_text().lower()
        
        # Goal indicators
        if any('goal' in cls.lower() for cls in class_names) or 'goal' in text_content:
            return 'goal'
        
        # Yellow card indicators
        if any('yellow' in cls.lower() for cls in class_names) or 'yellow' in text_content:
            return 'yellow_card'
        
        # Red card indicators
        if any('red' in cls.lower() for cls in class_names) or 'red' in text_content:
            return 'red_card'
        
        # Substitution indicators
        if any('sub' in cls.lower() for cls in class_names) or 'substitution' in text_content:
            return 'substitution'
        
        # Corner indicators
        if any('corner' in cls.lower() for cls in class_names) or 'corner' in text_content:
            return 'corner'
        
        # Penalty indicators
        if any('penalty' in cls.lower() for cls in class_names) or 'penalty' in text_content:
            return 'penalty'
        
        return None
    
    def extract_team_info(self, container) -> str:
        """
        Extract team information from event container
        """
        # This is a simplified implementation
        # Real implementation would need team-specific parsing
        
        parent = container.parent
        if parent:
            # Look for team indicators in parent
            team_text = parent.get_text().lower()
            if 'home' in team_text or 'team1' in team_text:
                return 'home'
            elif 'away' in team_text or 'team2' in team_text:
                return 'away'
        
        return 'unknown'
    
    def extract_network_calls(self, driver) -> Dict[str, Any]:
        """
        Extract API calls from network logs
        """
        try:
            logs = driver.get_log('performance')
            api_data = {}
            
            for entry in logs:
                message = json.loads(entry['message'])['message']
                
                if message.get('method') == 'Network.responseReceived':
                    url = message['params']['response'].get('url', '')
                    
                    # Look for FlashScore API patterns
                    if any(pattern in url for pattern in ['detail', 'feed', 'live', 'event']):
                        # Extract useful data from API response
                        # This would require more complex implementation
                        pass
            
            return api_data
            
        except Exception as e:
            logger.debug(f"⚠️ Error extracting network calls: {e}")
            return {}
    
    async def scrape_direct_api(self, match_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Try direct API scraping
        """
        try:
            # FlashScore doesn't have a documented public API
            # But we can try common patterns
            
            match_id = match_info.get('id')
            
            # Try different API patterns
            api_patterns = [
                f"https://d.flashscore.com/api/live_score/match/{match_id}",
                f"https://api.flashscore.com/live/match/{match_id}",
                f"https://www.flashscore.com/api/live/{match_id}"
            ]
            
            for api_url in api_patterns:
                try:
                    async with self.session.get(api_url, headers=self.headers, timeout=5) as response:
                        if response.status == 200:
                            data = await response.json()
                            return self.parse_api_response(data)
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"❌ FlashScore direct API error: {e}")
            return None
    
    def parse_api_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse direct API response (if available)
        """
        # This would depend on the actual API structure
        # For now, return a placeholder
        
        return {
            'score': {'home': 0, 'away': 0},
            'minute': 0,
            'status': 'LIVE',
            'events': [],
            'source': 'api'
        }
    
    async def monitor_live_updates(self, match_id: str, callback: callable, interval: int = 10):
        """
        Monitor live updates for a specific match
        """
        last_data = {}
        
        while True:
            try:
                match_info = {'id': match_id}
                current_data = await self.scrape_match(match_info)
                
                if current_data and current_data != last_data:
                    # Data has changed, call callback
                    await callback(current_data)
                    last_data = current_data
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"❌ Live monitoring error: {e}")
                await asyncio.sleep(interval * 2)  # Back off on error
    
    def get_live_matches(self) -> List[Dict[str, Any]]:
        """
        Get list of currently live matches (simplified implementation)
        """
        # This would require more complex implementation
        # For now, return empty list
        return []
    
    async def quick_score_update(self, match_id: str) -> Optional[Dict[str, Any]]:
        """
        Get quick score update for a match
        """
        try:
            match_url = f"{self.base_url}/match/{match_id}"
            
            async with self.session.get(match_url, headers=self.headers, timeout=5) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Quick score extraction
                    score_data = self.parse_flashscore_page(soup)
                    score_data['match_id'] = match_id
                    
                    return score_data
                    
                return None
                
        except Exception as e:
            logger.debug(f"⚠️ Quick score update failed: {e}")
            return None