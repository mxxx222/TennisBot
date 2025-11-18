#!/usr/bin/env python3
"""
🎾 LIVE BETTING SCRAPER WITH ANTI-DETECTION
==========================================

Enhanced live betting scraper with comprehensive anti-detection measures,
error handling, and integration with TennisBot infrastructure.

Features:
- Live and upcoming match scraping
- Anti-detection with proxy rotation and headless browsers
- Real-time odds monitoring
- Data validation and cleaning
- Comprehensive error handling and logging
- Integration with existing TennisBot systems

Author: TennisBot Advanced Analytics
Version: 1.0.0
"""

import asyncio
import time
import logging
import pandas as pd
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import random

# Import existing TennisBot utilities
try:
    from scraping_utils import (
        AntiDetectionSession, ProxyPool, ProxyConfig,
        UndetectedChromeDriver, DataValidator,
        RateLimiter, ScrapingMetrics
    )
except ImportError:
    # Fallback imports if utilities not available
    print("⚠️ Warning: Advanced scraping utilities not available. Using basic functionality.")
    AntiDetectionSession = None
    UndetectedChromeDriver = None
    DataValidator = None
    RateLimiter = None
    ScrapingMetrics = None

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    from bs4 import BeautifulSoup
    import requests
except ImportError as e:
    print(f"❌ Missing required packages: {e}")
    print("Please ensure all packages are installed in your virtual environment")
    raise

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/herbspotturku/sportsbot/TennisBot/data/scraping.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class LiveMatch:
    """Enhanced live match data structure"""
    match_id: str
    sport: str
    league: str
    home_team: str
    away_team: str
    
    # Match details
    status: str = "scheduled"  # scheduled, live, finished
    start_time: str = ""
    venue: Optional[str] = None
    
    # Odds data
    home_odds: Optional[float] = None
    away_odds: Optional[float] = None
    draw_odds: Optional[float] = None
    
    # Live data
    score: Optional[str] = None
    minute: Optional[str] = None
    
    # Metadata
    source: str = ""
    last_updated: str = ""
    confidence_score: float = 0.0
    
    def __post_init__(self):
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()
        if not self.match_id:
            self.match_id = self._generate_match_id()
    
    def _generate_match_id(self) -> str:
        """Generate unique match ID"""
        content = f"{self.home_team}{self.away_team}{self.start_time}{self.sport}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

class LiveBettingScraper:
    """Enhanced live betting scraper with anti-detection"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.driver = None
        self.session = None
        self.validator = DataValidator() if DataValidator else None
        self.metrics = ScrapingMetrics() if ScrapingMetrics else None
        self.rate_limiter = RateLimiter() if RateLimiter else None
        
        # Scraping targets
        self.targets = {
            'live_betting': [
                'https://www.flashscore.com/tennis/',
                'https://www.sofascore.com/tennis',
                'https://www.livescore.com/tennis'
            ],
            'upcoming_matches': [
                'https://www.atptour.com/en/scores/current',
                'https://www.flashscore.com/tennis/fixtures/',
                'https://www.tennisexplorer.com/matches/'
            ]
        }
        
        # Initialize data storage
        self.data_dir = Path('/Users/herbspotturku/sportsbot/TennisBot/data')
        self.data_dir.mkdir(exist_ok=True)
        
        logger.info("🎾 LiveBettingScraper initialized")
    
    def __enter__(self):
        """Context manager entry"""
        self.setup_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
    
    def setup_driver(self):
        """Setup Chrome WebDriver with anti-detection"""
        try:
            # Use UndetectedChromeDriver if available
            if UndetectedChromeDriver:
                logger.info("🔧 Setting up undetected Chrome driver...")
                self.driver = UndetectedChromeDriver(headless=True)
                self.driver.start_driver()
                self.driver = self.driver.driver  # Get the actual driver instance
            else:
                # Fallback to regular Chrome driver
                logger.info("🔧 Setting up regular Chrome driver...")
                options = Options()
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_argument('--disable-extensions')
                options.add_argument('--disable-plugins')
                options.add_argument('--disable-images')
                
                # Randomize viewport
                width = random.randint(1024, 1920)
                height = random.randint(768, 1080)
                options.add_argument(f'--window-size={width},{height}')
                
                # Random user agent
                user_agents = [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                ]
                options.add_argument(f'--user-agent={random.choice(user_agents)}')
                
                self.driver = webdriver.Chrome(options=options)
            
            logger.info("✅ WebDriver setup complete")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup WebDriver: {e}")
            raise
    
    def cleanup(self):
        """Cleanup resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("🧹 WebDriver cleaned up")
            except Exception as e:
                logger.warning(f"⚠️ Error during cleanup: {e}")
    
    def human_like_delay(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """Add human-like delay between requests"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def scrape_live_matches(self, max_matches: int = 50) -> List[LiveMatch]:
        """
        Scrape live matches from multiple sources
        
        Args:
            max_matches: Maximum number of matches to scrape
            
        Returns:
            List of live matches
        """
        logger.info("🔴 Starting live matches scraping...")
        
        all_matches = []
        
        for url in self.targets['live_betting']:
            try:
                logger.info(f"📊 Scraping live matches from {url}")
                matches = self._scrape_site_live_matches(url)
                
                if matches:
                    all_matches.extend(matches)
                    logger.info(f"✅ Found {len(matches)} live matches from {url}")
                
                # Respect rate limits
                self.human_like_delay(2, 4)
                
                if len(all_matches) >= max_matches:
                    break
                    
            except Exception as e:
                logger.error(f"❌ Error scraping {url}: {e}")
                continue
        
        # Remove duplicates and validate
        unique_matches = self._deduplicate_matches(all_matches)
        validated_matches = [m for m in unique_matches if self._validate_match(m)]
        
        logger.info(f"✅ Scraped {len(validated_matches)} validated live matches")
        return validated_matches[:max_matches]
    
    def scrape_upcoming_matches(self, max_matches: int = 100) -> List[LiveMatch]:
        """
        Scrape upcoming matches from multiple sources
        
        Args:
            max_matches: Maximum number of matches to scrape
            
        Returns:
            List of upcoming matches
        """
        logger.info("⏰ Starting upcoming matches scraping...")
        
        all_matches = []
        
        for url in self.targets['upcoming_matches']:
            try:
                logger.info(f"📊 Scraping upcoming matches from {url}")
                matches = self._scrape_site_upcoming_matches(url)
                
                if matches:
                    all_matches.extend(matches)
                    logger.info(f"✅ Found {len(matches)} upcoming matches from {url}")
                
                # Respect rate limits
                self.human_like_delay(2, 4)
                
                if len(all_matches) >= max_matches:
                    break
                    
            except Exception as e:
                logger.error(f"❌ Error scraping {url}: {e}")
                continue
        
        # Remove duplicates and validate
        unique_matches = self._deduplicate_matches(all_matches)
        validated_matches = [m for m in unique_matches if self._validate_match(m)]
        
        logger.info(f"✅ Scraped {len(validated_matches)} validated upcoming matches")
        return validated_matches[:max_matches]
    
    def _scrape_site_live_matches(self, url: str) -> List[LiveMatch]:
        """Scrape live matches from a specific site"""
        matches = []
        
        try:
            # Navigate to the page
            self.driver.get(url)
            self.human_like_delay(3, 5)  # Wait for page to load
            
            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Site-specific parsing logic
            if 'flashscore' in url:
                matches = self._parse_flashscore_live(soup)
            elif 'sofascore' in url:
                matches = self._parse_sofascore_live(soup)
            elif 'livescore' in url:
                matches = self._parse_livescore_live(soup)
            else:
                # Generic parsing
                matches = self._parse_generic_live(soup, url)
            
        except TimeoutException:
            logger.warning(f"⏰ Timeout loading {url}")
        except WebDriverException as e:
            logger.error(f"🌐 WebDriver error for {url}: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error scraping {url}: {e}")
        
        return matches
    
    def _scrape_site_upcoming_matches(self, url: str) -> List[LiveMatch]:
        """Scrape upcoming matches from a specific site"""
        matches = []
        
        try:
            # Navigate to the page
            self.driver.get(url)
            self.human_like_delay(3, 5)  # Wait for page to load
            
            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Site-specific parsing logic
            if 'atptour' in url:
                matches = self._parse_atp_upcoming(soup)
            elif 'flashscore' in url:
                matches = self._parse_flashscore_upcoming(soup)
            elif 'tennisexplorer' in url:
                matches = self._parse_tennisexplorer_upcoming(soup)
            else:
                # Generic parsing
                matches = self._parse_generic_upcoming(soup, url)
            
        except TimeoutException:
            logger.warning(f"⏰ Timeout loading {url}")
        except WebDriverException as e:
            logger.error(f"🌐 WebDriver error for {url}: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error scraping {url}: {e}")
        
        return matches
    
    def _parse_flashscore_live(self, soup: BeautifulSoup) -> List[LiveMatch]:
        """Parse live matches from Flashscore"""
        matches = []
        
        try:
            # Look for match containers
            match_containers = soup.find_all('div', class_=['event__match', 'event', 'match'])
            
            for container in match_containers[:20]:  # Limit for performance
                try:
                    match = self._extract_flashscore_match(container, 'live')
                    if match:
                        matches.append(match)
                except Exception as e:
                    logger.debug(f"Error parsing Flashscore match: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error parsing Flashscore live matches: {e}")
        
        return matches
    
    def _parse_flashscore_upcoming(self, soup: BeautifulSoup) -> List[LiveMatch]:
        """Parse upcoming matches from Flashscore"""
        matches = []
        
        try:
            # Look for fixture containers
            fixture_containers = soup.find_all('div', class_=['event__match', 'fixture', 'match'])
            
            for container in fixture_containers[:30]:  # More upcoming matches
                try:
                    match = self._extract_flashscore_match(container, 'scheduled')
                    if match:
                        matches.append(match)
                except Exception as e:
                    logger.debug(f"Error parsing Flashscore fixture: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error parsing Flashscore upcoming matches: {e}")
        
        return matches
    
    def _extract_flashscore_match(self, container, status: str) -> Optional[LiveMatch]:
        """Extract match data from Flashscore container"""
        try:
            # Extract team names
            team_elements = container.find_all(['span', 'div'], class_=['event__participant', 'participant', 'team'])
            
            if len(team_elements) < 2:
                return None
            
            home_team = self._clean_team_name(team_elements[0].get_text(strip=True))
            away_team = self._clean_team_name(team_elements[1].get_text(strip=True))
            
            if not home_team or not away_team:
                return None
            
            # Extract score if available
            score_element = container.find(['span', 'div'], class_=['event__score', 'score'])
            score = score_element.get_text(strip=True) if score_element else None
            
            # Extract time
            time_element = container.find(['span', 'div'], class_=['event__time', 'time'])
            start_time = time_element.get_text(strip=True) if time_element else ""
            
            # Extract odds if available
            odds_elements = container.find_all(['span', 'div'], class_=['odds', 'odd'])
            home_odds = None
            away_odds = None
            
            if len(odds_elements) >= 2:
                try:
                    home_odds = float(odds_elements[0].get_text(strip=True))
                    away_odds = float(odds_elements[1].get_text(strip=True))
                except (ValueError, IndexError):
                    pass
            
            match = LiveMatch(
                match_id="",  # Will be generated in __post_init__
                sport="tennis",
                league="ATP/WTA",
                home_team=home_team,
                away_team=away_team,
                status=status,
                start_time=start_time,
                score=score,
                home_odds=home_odds,
                away_odds=away_odds,
                source="flashscore.com"
            )
            
            return match
            
        except Exception as e:
            logger.debug(f"Error extracting Flashscore match: {e}")
            return None
    
    def _parse_atp_upcoming(self, soup: BeautifulSoup) -> List[LiveMatch]:
        """Parse upcoming matches from ATP Tour"""
        matches = []
        
        try:
            # Look for match containers
            match_containers = soup.find_all(['div', 'tr'], class_=['match', 'scores-results-content'])
            
            for container in match_containers[:25]:
                try:
                    match = self._extract_atp_match(container)
                    if match:
                        matches.append(match)
                except Exception as e:
                    logger.debug(f"Error parsing ATP match: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error parsing ATP upcoming matches: {e}")
        
        return matches
    
    def _extract_atp_match(self, container) -> Optional[LiveMatch]:
        """Extract match data from ATP container"""
        try:
            # Extract player names
            player_elements = container.find_all(['a', 'span'], class_=['player-name', 'player'])
            
            if len(player_elements) < 2:
                return None
            
            home_team = self._clean_team_name(player_elements[0].get_text(strip=True))
            away_team = self._clean_team_name(player_elements[1].get_text(strip=True))
            
            if not home_team or not away_team:
                return None
            
            # Extract tournament
            tournament_element = container.find(['span', 'div'], class_=['tournament', 'event-name'])
            league = tournament_element.get_text(strip=True) if tournament_element else "ATP Tour"
            
            # Extract time
            time_element = container.find(['span', 'div'], class_=['time', 'match-time'])
            start_time = time_element.get_text(strip=True) if time_element else ""
            
            match = LiveMatch(
                match_id="",  # Will be generated in __post_init__
                sport="tennis",
                league=league,
                home_team=home_team,
                away_team=away_team,
                status="scheduled",
                start_time=start_time,
                source="atptour.com"
            )
            
            return match
            
        except Exception as e:
            logger.debug(f"Error extracting ATP match: {e}")
            return None
    def _parse_tennisexplorer_upcoming(self, soup: BeautifulSoup) -> List[LiveMatch]:
        """Parse upcoming matches from TennisExplorer"""
        matches = []

        try:
            # Look for match containers - TennisExplorer typically uses table rows
            match_containers = soup.find_all(['tr', 'div'], class_=['match', 'fixture', 'game'])

            for container in match_containers[:25]:
                try:
                    match = self._extract_tennisexplorer_match(container)
                    if match:
                        matches.append(match)
                except Exception as e:
                    logger.debug(f"Error parsing TennisExplorer match: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error parsing TennisExplorer upcoming matches: {e}")

        return matches

    def _extract_tennisexplorer_match(self, container) -> Optional[LiveMatch]:
        """Extract match data from TennisExplorer container"""
        try:
            # Extract player names - TennisExplorer often uses links or spans
            player_elements = container.find_all(['a', 'span'], class_=['player', 'participant'])

            if len(player_elements) < 2:
                return None

            home_team = self._clean_team_name(player_elements[0].get_text(strip=True))
            away_team = self._clean_team_name(player_elements[1].get_text(strip=True))

            if not home_team or not away_team:
                return None

            # Extract tournament/league
            tournament_element = container.find(['span', 'div'], class_=['tournament', 'event'])
            league = tournament_element.get_text(strip=True) if tournament_element else "TennisExplorer"

            # Extract time/date
            time_element = container.find(['span', 'div'], class_=['time', 'date'])
            start_time = time_element.get_text(strip=True) if time_element else ""

            match = LiveMatch(
                match_id="",  # Will be generated in __post_init__
                sport="tennis",
                league=league,
                home_team=home_team,
                away_team=away_team,
                status="scheduled",
                start_time=start_time,
                source="tennisexplorer.com"
            )

            return match

        except Exception as e:
            logger.debug(f"Error extracting TennisExplorer match: {e}")
            return None
    
    def _parse_generic_live(self, soup: BeautifulSoup, url: str) -> List[LiveMatch]:
        """Generic parser for live matches"""
        matches = []
        
        try:
            # Look for common match patterns
            match_patterns = [
                {'tag': 'div', 'class': 'match'},
                {'tag': 'tr', 'class': 'match'},
                {'tag': 'div', 'class': 'event'},
                {'tag': 'div', 'class': 'game'}
            ]
            
            for pattern in match_patterns:
                containers = soup.find_all(pattern['tag'], class_=pattern['class'])
                
                for container in containers[:15]:
                    try:
                        match = self._extract_generic_match(container, 'live', url)
                        if match:
                            matches.append(match)
                    except Exception as e:
                        logger.debug(f"Error parsing generic match: {e}")
                        continue
                
                if matches:  # Stop if we found matches with this pattern
                    break
            
        except Exception as e:
            logger.error(f"Error in generic live parsing: {e}")
        
        return matches
    
    def _parse_generic_upcoming(self, soup: BeautifulSoup, url: str) -> List[LiveMatch]:
        """Generic parser for upcoming matches"""
        matches = []
        
        try:
            # Look for common fixture patterns
            fixture_patterns = [
                {'tag': 'div', 'class': 'fixture'},
                {'tag': 'tr', 'class': 'fixture'},
                {'tag': 'div', 'class': 'upcoming'},
                {'tag': 'div', 'class': 'scheduled'}
            ]
            
            for pattern in fixture_patterns:
                containers = soup.find_all(pattern['tag'], class_=pattern['class'])
                
                for container in containers[:20]:
                    try:
                        match = self._extract_generic_match(container, 'scheduled', url)
                        if match:
                            matches.append(match)
                    except Exception as e:
                        logger.debug(f"Error parsing generic fixture: {e}")
                        continue
                
                if matches:  # Stop if we found matches with this pattern
                    break
            
        except Exception as e:
            logger.error(f"Error in generic upcoming parsing: {e}")
        
        return matches
    
    def _extract_generic_match(self, container, status: str, source: str) -> Optional[LiveMatch]:
        """Generic match data extraction"""
        try:
            # Try to find team names using various selectors
            team_selectors = [
                'span.team', 'div.team', 'a.team',
                'span.player', 'div.player', 'a.player',
                'span.participant', 'div.participant', 'a.participant'
            ]
            
            teams = []
            for selector in team_selectors:
                elements = container.select(selector)
                if len(elements) >= 2:
                    teams = [self._clean_team_name(elem.get_text(strip=True)) for elem in elements[:2]]
                    break
            
            if len(teams) < 2 or not all(teams):
                return None
            
            home_team, away_team = teams[0], teams[1]
            
            # Try to extract odds
            odds_selectors = ['span.odds', 'div.odds', 'span.odd', 'div.odd']
            odds = []
            
            for selector in odds_selectors:
                elements = container.select(selector)
                if elements:
                    for elem in elements[:2]:
                        try:
                            odds.append(float(elem.get_text(strip=True)))
                        except (ValueError, TypeError):
                            continue
                    break
            
            home_odds = odds[0] if len(odds) > 0 else None
            away_odds = odds[1] if len(odds) > 1 else None
            
            # Extract score for live matches
            score = None
            if status == 'live':
                score_selectors = ['span.score', 'div.score', 'span.result', 'div.result']
                for selector in score_selectors:
                    score_elem = container.select_one(selector)
                    if score_elem:
                        score = score_elem.get_text(strip=True)
                        break
            
            match = LiveMatch(
                match_id="",  # Will be generated in __post_init__
                sport="tennis",
                league="Various",
                home_team=home_team,
                away_team=away_team,
                status=status,
                score=score,
                home_odds=home_odds,
                away_odds=away_odds,
                source=source
            )
            
            return match
            
        except Exception as e:
            logger.debug(f"Error in generic match extraction: {e}")
            return None
    
    def _clean_team_name(self, name: str) -> str:
        """Clean and standardize team/player names"""
        if not name:
            return ""
        
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Remove special characters but keep hyphens and apostrophes
        import re
        name = re.sub(r'[^\w\s\-\']', '', name)
        
        return name.strip()
    
    def _validate_match(self, match: LiveMatch) -> bool:
        """Validate match data quality"""
        try:
            # Basic validation
            if not match.home_team or not match.away_team:
                return False
            
            if len(match.home_team) < 2 or len(match.away_team) < 2:
                return False
            
            # Validate odds if present
            if match.home_odds and (match.home_odds < 1.01 or match.home_odds > 100):
                return False
            
            if match.away_odds and (match.away_odds < 1.01 or match.away_odds > 100):
                return False
            
            return True
            
        except Exception as e:
            logger.debug(f"Error validating match: {e}")
            return False
    
    def _deduplicate_matches(self, matches: List[LiveMatch]) -> List[LiveMatch]:
        """Remove duplicate matches"""
        seen = set()
        unique_matches = []
        
        for match in matches:
            # Create a key for deduplication
            key = f"{match.home_team.lower()}|{match.away_team.lower()}|{match.status}"
            
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)
        
        logger.info(f"🔄 Deduplicated: {len(matches)} -> {len(unique_matches)} matches")
        return unique_matches
    
    def save_to_csv(self, matches: List[LiveMatch], filename: str = None) -> str:
        """Save matches to CSV file"""
        if not matches:
            logger.warning("⚠️ No matches to save")
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"tennis_matches_{timestamp}.csv"
        
        # Convert to DataFrame
        data = [match.to_dict() for match in matches]
        df = pd.DataFrame(data)
        
        # Save to CSV
        filepath = self.data_dir / filename
        df.to_csv(filepath, index=False)
        
        logger.info(f"💾 Saved {len(matches)} matches to {filepath}")
        return str(filepath)
    
    def save_to_json(self, matches: List[LiveMatch], filename: str = None) -> str:
        """Save matches to JSON file"""
        if not matches:
            logger.warning("⚠️ No matches to save")
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"tennis_matches_{timestamp}.json"
        
        # Prepare data
        data = {
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'total_matches': len(matches),
                'scraper_version': '1.0.0'
            },
            'matches': [match.to_dict() for match in matches]
        }
        
        # Save to JSON
        filepath = self.data_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"💾 Saved {len(matches)} matches to {filepath}")
        return str(filepath)
    
    def get_summary_stats(self, matches: List[LiveMatch]) -> Dict[str, Any]:
        """Get summary statistics of scraped matches"""
        if not matches:
            return {}
        
        stats = {
            'total_matches': len(matches),
            'live_matches': len([m for m in matches if m.status == 'live']),
            'upcoming_matches': len([m for m in matches if m.status == 'scheduled']),
            'matches_with_odds': len([m for m in matches if m.home_odds and m.away_odds]),
            'unique_sources': len(set(m.source for m in matches)),
            'leagues': list(set(m.league for m in matches)),
            'avg_home_odds': sum(m.home_odds for m in matches if m.home_odds) / len([m for m in matches if m.home_odds]) if any(m.home_odds for m in matches) else 0,
            'avg_away_odds': sum(m.away_odds for m in matches if m.away_odds) / len([m for m in matches if m.away_odds]) if any(m.away_odds for m in matches) else 0
        }
        
        return stats

# Convenience functions
def scrape_live_tennis_matches(max_matches: int = 50) -> List[LiveMatch]:
    """Convenience function to scrape live tennis matches"""
    with LiveBettingScraper() as scraper:
        return scraper.scrape_live_matches(max_matches)

def scrape_upcoming_tennis_matches(max_matches: int = 100) -> List[LiveMatch]:
    """Convenience function to scrape upcoming tennis matches"""
    with LiveBettingScraper() as scraper:
        return scraper.scrape_upcoming_matches(max_matches)

def main():
    """Main function for testing the scraper"""
    print("🎾 LIVE BETTING SCRAPER TEST")
    print("=" * 50)
    
    try:
        with LiveBettingScraper() as scraper:
            # Test live matches scraping
            print("\n🔴 Testing live matches scraping...")
            live_matches = scraper.scrape_live_matches(max_matches=20)
            
            if live_matches:
                print(f"✅ Found {len(live_matches)} live matches")
                
                # Show sample match
                sample_match = live_matches[0]
                print(f"\n📊 Sample live match:")
                print(f"   🏆 {sample_match.home_team} vs {sample_match.away_team}")
                print(f"   📈 Odds: {sample_match.home_odds} / {sample_match.away_odds}")
                print(f"   ⚡ Score: {sample_match.score}")
                print(f"   🌐 Source: {sample_match.source}")
                
                # Save data
                csv_file = scraper.save_to_csv(live_matches, "live_matches_test.csv")
                json_file = scraper.save_to_json(live_matches, "live_matches_test.json")
                
                print(f"\n💾 Data saved:")
                print(f"   📄 CSV: {csv_file}")
                print(f"   📄 JSON: {json_file}")
                
                # Show stats
                stats = scraper.get_summary_stats(live_matches)
                print(f"\n📊 Summary Statistics:")
                for key, value in stats.items():
                    print(f"   {key}: {value}")
            
            else:
                print("❌ No live matches found")
            
            # Test upcoming matches scraping
            print("\n⏰ Testing upcoming matches scraping...")
            upcoming_matches = scraper.scrape_upcoming_matches(max_matches=30)
            
            if upcoming_matches:
                print(f"✅ Found {len(upcoming_matches)} upcoming matches")
                
                # Show sample match
                sample_match = upcoming_matches[0]
                print(f"\n📊 Sample upcoming match:")
                print(f"   🏆 {sample_match.home_team} vs {sample_match.away_team}")
                print(f"   📅 Time: {sample_match.start_time}")
                print(f"   🏟️ League: {sample_match.league}")
                print(f"   🌐 Source: {sample_match.source}")
                
                # Save data
                csv_file = scraper.save_to_csv(upcoming_matches, "upcoming_matches_test.csv")
                
                print(f"\n💾 Upcoming matches saved to: {csv_file}")
            
            else:
                print("❌ No upcoming matches found")
    
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
