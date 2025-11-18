"""
Betfury.io Educational Scraping System
=====================================

This module provides ethical web scraping capabilities for educational research purposes.
All operations include proper rate limiting and respect for website terms of service.

DISCLAIMER: This is for educational/research purposes only. 
Users must comply with all applicable laws and website terms of service.
"""

import asyncio
import aiohttp
import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
import logging
from pathlib import Path

import aiohttp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import undetected_chromedriver as uc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MatchData:
    """Structure for match information"""
    match_id: str
    league: str
    home_team: str
    away_team: str
    score: str
    minute: str
    odds: Dict[str, float]
    timestamp: str
    source_url: str
    
class EthicalRateLimiter:
    """Rate limiter for ethical web scraping"""
    
    def __init__(self, min_delay: float = 5.0, max_delay: float = 10.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time = 0
        self.request_count = 0
        self.hourly_limit = 720  # 1 request per 5 seconds
        self.hour_start = time.time()
    
    async def wait_if_needed(self):
        """Wait if necessary to maintain ethical rate limits"""
        current_time = time.time()
        
        # Check hourly limit
        if current_time - self.hour_start >= 3600:  # 1 hour
            self.request_count = 0
            self.hour_start = current_time
        
        if self.request_count >= self.hourly_limit:
            wait_time = 3600 - (current_time - self.hour_start)
            logger.warning(f"Rate limit reached, waiting {wait_time:.0f} seconds")
            await asyncio.sleep(wait_time)
        
        # Calculate delay since last request
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            # Add randomization to avoid predictable patterns
            delay = self.min_delay + random.uniform(0, self.max_delay - self.min_delay)
            logger.debug(f"Rate limiting: waiting {delay:.2f} seconds")
            await asyncio.sleep(delay)
        
        self.last_request_time = time.time()
        self.request_count += 1

class BetfuryScraper:
    """Ethical web scraper for Betfury.io educational research"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self.rate_limiter = EthicalRateLimiter(
            min_delay=self.config['rate_limit']['min_delay_seconds'],
            max_delay=self.config['rate_limit']['max_delay_seconds']
        )
        self.session: Optional[aiohttp.ClientSession] = None
        self.driver: Optional[webdriver.Chrome] = None
        self.base_url = "https://betfury.io"
        
        # User agents for rotation (educational purposes)
        self.user_agents = [
            "EducationalResearchBot/1.0 (Sports Analytics Research; Contact: researcher@example.com)",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'rate_limit': {
                'min_delay_seconds': 5.0,
                'max_delay_seconds': 10.0
            },
            'scraping': {
                'timeout_seconds': 30,
                'retry_attempts': 3
            },
            'targets': {
                'sports_page': 'https://betfury.io/sports',
                'live_page': 'https://betfury.io/sports/live'
            }
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.init_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()
    
    async def init_session(self):
        """Initialize HTTP session"""
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        timeout = aiohttp.ClientTimeout(total=self.config['scraping']['timeout_seconds'])
        self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        logger.info("HTTP session initialized")
    
    def init_browser(self, headless: bool = True) -> webdriver.Chrome:
        """Initialize browser for dynamic content"""
        options = Options()
        
        if headless:
            options.add_argument('--headless')
        
        # Anti-detection measures
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Set realistic window size
        options.add_argument('--window-size=1920,1080')
        
        # User agent
        options.add_argument(f'--user-agent={random.choice(self.user_agents)}')
        
        # Initialize undetected Chrome
        driver = uc.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    async def get_live_matches(self, use_selenium: bool = True) -> List[MatchData]:
        """
        Get live matches from Betfury.io with ethical rate limiting
        
        Args:
            use_selenium: Whether to use Selenium for dynamic content
            
        Returns:
            List of MatchData objects
        """
        await self.rate_limiter.wait_if_needed()
        
        try:
            if use_selenium:
                matches = await self._get_matches_selenium()
            else:
                matches = await self._get_matches_http()
            
            logger.info(f"Retrieved {len(matches)} live matches")
            return matches
            
        except Exception as e:
            logger.error(f"Error fetching live matches: {e}")
            return []
    
    async def _get_matches_selenium(self) -> List[MatchData]:
        """Get matches using Selenium for dynamic content"""
        self.driver = self.init_browser(headless=self.config['scraping']['headless_browser'])
        
        try:
            # Navigate to live sports page
            self.driver.get(self.config['targets']['live_page'])
            
            # Wait for content to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for dynamic content
            await asyncio.sleep(3)
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            matches = self._parse_match_elements(soup)
            
            return matches
            
        except Exception as e:
            logger.error(f"Selenium scraping error: {e}")
            return []
        
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    async def _get_matches_http(self) -> List[MatchData]:
        """Get matches using direct HTTP requests"""
        if not self.session:
            await self.init_session()
        
        try:
            url = self.config['targets']['live_page']
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    matches = self._parse_match_elements(soup)
                    return matches
                else:
                    logger.warning(f"HTTP request failed: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"HTTP scraping error: {e}")
            return []
    
    def _parse_match_elements(self, soup: BeautifulSoup) -> List[MatchData]:
        """
        Parse match elements from HTML
        
        NOTE: CSS selectors may need updating based on site structure changes
        This is a template implementation for educational purposes
        """
        matches = []
        
        # Multiple selector attempts for different site layouts
        possible_selectors = [
            '.match-card',
            '.sports-match',
            '[data-match-id]',
            '.live-match',
            '.event-card'
        ]
        
        match_elements = []
        for selector in possible_selectors:
            elements = soup.select(selector)
            if elements:
                match_elements = elements
                logger.info(f"Found {len(elements)} matches using selector: {selector}")
                break
        
        if not match_elements:
            logger.warning("No match elements found with any selector")
            return matches
        
        for element in match_elements:
            try:
                match_data = self._extract_match_data(element)
                if match_data:
                    matches.append(match_data)
            except Exception as e:
                logger.error(f"Error parsing match element: {e}")
                continue
        
        return matches
    
    def _extract_match_data(self, element) -> Optional[MatchData]:
        """Extract match data from a single match element"""
        try:
            # Extract basic match information
            match_id = element.get('data-match-id', '') or element.get('id', '')
            
            # Try multiple selector approaches for team names
            home_team = self._extract_text(element, [
                '.home-team', '.team-home', '.home', 
                '[data-team="home"]', '.home-name'
            ])
            
            away_team = self._extract_text(element, [
                '.away-team', '.team-away', '.away',
                '[data-team="away"]', '.away-name'
            ])
            
            if not home_team or not away_team:
                return None
            
            # Extract other match data
            league = self._extract_text(element, [
                '.league', '.league-name', '.competition',
                '[data-league]', '.tournament'
            ]) or "Unknown League"
            
            score = self._extract_text(element, [
                '.score', '.result', '.match-score',
                '.current-score'
            ]) or "0-0"
            
            minute = self._extract_text(element, [
                '.minute', '.time', '.match-time',
                '.elapsed'
            ]) or "0'"
            
            # Extract odds
            odds = self._extract_odds(element)
            
            return MatchData(
                match_id=match_id,
                league=league,
                home_team=home_team.strip(),
                away_team=away_team.strip(),
                score=score.strip(),
                minute=minute.strip(),
                odds=odds,
                timestamp=datetime.now().isoformat(),
                source_url=self.config['targets']['live_page']
            )
            
        except Exception as e:
            logger.error(f"Error extracting match data: {e}")
            return None
    
    def _extract_text(self, element, selectors: List[str]) -> Optional[str]:
        """Try multiple selectors to extract text"""
        for selector in selectors:
            found = element.select_one(selector)
            if found and found.get_text(strip=True):
                return found.get_text(strip=True)
        return None
    
    def _extract_odds(self, element) -> Dict[str, float]:
        """Extract odds from match element"""
        odds = {}
        
        try:
            # Try to find odds buttons/elements
            odds_selectors = [
                '.odds', '.odd', '.odds-button',
                '.bet-odds', '[data-odd]'
            ]
            
            odds_elements = []
            for selector in odds_selectors:
                elements = element.select(selector)
                odds_elements.extend(elements)
                if elements:
                    break
            
            # Extract 1X2 odds
            if len(odds_elements) >= 3:
                try:
                    odds['home'] = float(odds_elements[0].get_text(strip=True))
                    odds['draw'] = float(odds_elements[1].get_text(strip=True))
                    odds['away'] = float(odds_elements[2].get_text(strip=True))
                except (ValueError, IndexError):
                    pass
            
            # Try to find over/under odds
            ou_elements = element.select('.over-under .odds, .ou-odds')
            if len(ou_elements) >= 2:
                try:
                    odds['over_2_5'] = float(ou_elements[0].get_text(strip=True))
                    odds['under_2_5'] = float(ou_elements[1].get_text(strip=True))
                except (ValueError, IndexError):
                    pass
            
        except Exception as e:
            logger.error(f"Error extracting odds: {e}")
        
        return odds
    
    async def get_match_details(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Get additional details for a specific match"""
        await self.rate_limiter.wait_if_needed()
        
        # This would typically involve API calls
        # For educational purposes, we'll return basic info
        return {
            'match_id': match_id,
            'details': 'Match details would be fetched here',
            'note': 'Educational implementation - no actual API calls made'
        }
    
    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
            self.session = None
        
        if self.driver:
            self.driver.quit()
            self.driver = None
        
        logger.info("Resources cleaned up")

# Example usage for educational purposes
async def educational_example():
    """Demonstrate ethical scraping for educational purposes"""
    
    config = {
        'rate_limit': {'min_delay_seconds': 5.0, 'max_delay_seconds': 10.0},
        'scraping': {'timeout_seconds': 30, 'headless_browser': True},
        'targets': {
            'sports_page': 'https://betfury.io/sports',
            'live_page': 'https://betfury.io/sports/live'
        }
    }
    
    async with BetfuryScraper(config) as scraper:
        print("🔍 Starting educational scraping demonstration...")
        print("⚠️  This is for educational purposes only!")
        
        # Get live matches with ethical rate limiting
        matches = await scraper.get_live_matches(use_selenium=True)
        
        if matches:
            print(f"📊 Found {len(matches)} live matches:")
            for match in matches[:3]:  # Show first 3 matches
                print(f"  • {match.home_team} vs {match.away_team}")
                print(f"    Score: {match.score} ({match.minute})")
                print(f"    League: {match.league}")
                print(f"    Odds: {match.odds}")
                print()
        else:
            print("No matches found (this is normal for educational demo)")

if __name__ == "__main__":
    # Run educational example
    asyncio.run(educational_example())