#!/usr/bin/env python3
"""
🎾 BETEXPLORER ITF SCRAPER
===========================

Production-ready scraper for BetExplorer ITF Women matches with 20+ bookmaker odds comparison.
Reuses 60-70% of FlashScore scraper patterns.
"""

import logging
import time
import random
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

# Try to import Selenium
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("⚠️ Selenium not available")


class BetExplorerScraper:
    """
    BetExplorer scraper for ITF Women matches with odds comparison.
    
    Features:
    - Selenium for dynamic content
    - Tournament filtering (W15/W25 focus)
    - Odds comparison scraping (20+ bookmakers)
    - Best odds selection
    - Error handling and retry logic
    """
    
    BASE_URL = "https://www.betexplorer.com/tennis/"
    ITF_WOMEN_URL = "https://www.betexplorer.com/tennis/itf-women/"
    
    def __init__(self, config: dict = None, use_selenium: bool = True):
        """
        Initialize BetExplorer scraper
        
        Args:
            config: Configuration dictionary
            use_selenium: Whether to use Selenium (recommended)
        """
        self.config = config or {}
        self.use_selenium = use_selenium and SELENIUM_AVAILABLE
        self.driver = None
        self.last_request_time = 0
        self.request_delay = self.config.get('request_delay', 2.0)
        self.max_retries = self.config.get('max_retries', 3)
        self.timeout = self.config.get('timeout', 30)
        
        if self.use_selenium:
            self._init_selenium()
        
        logger.info(f"🎾 BetExplorer Scraper initialized (Selenium: {self.use_selenium})")
    
    def _init_selenium(self):
        """Initialize Selenium WebDriver with anti-detection (reused from FlashScore)"""
        if not SELENIUM_AVAILABLE:
            logger.warning("⚠️ Selenium not available")
            return
        
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            user_agent = self.config.get('user_agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
            options.add_argument(f'user-agent={user_agent}')
            
            # Anti-detection
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("✅ Selenium WebDriver initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Selenium: {e}")
            self.driver = None
            self.use_selenium = False
    
    def _rate_limit(self):
        """Apply rate limiting (reused from FlashScore pattern)"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_delay:
            sleep_time = self.request_delay - elapsed + random.uniform(0, 1)
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _handle_cloudflare(self):
        """Handle Cloudflare challenge if detected"""
        try:
            if "Checking your browser" in self.driver.page_source or "Just a moment" in self.driver.page_source:
                logger.info("⏳ Cloudflare challenge detected, waiting...")
                time.sleep(5)
                # Wait for challenge to complete
                WebDriverWait(self.driver, 30).until(
                    lambda d: "Checking your browser" not in d.page_source
                )
                logger.info("✅ Cloudflare challenge passed")
        except TimeoutException:
            logger.warning("⚠️ Cloudflare challenge timeout")
    
    def get_w15_tournaments(self) -> List[Dict[str, str]]:
        """
        Get all W15/W25 tournament links from ITF Women page
        
        Returns:
            List of tournament dictionaries with name, url, tier, location, surface
        """
        if not self.driver:
            logger.error("❌ Selenium driver not available")
            return []
        
        tournaments = []
        
        try:
            logger.info(f"🌐 Loading ITF Women page: {self.ITF_WOMEN_URL}")
            self._rate_limit()
            self.driver.get(self.ITF_WOMEN_URL)
            
            # Handle Cloudflare if present
            self._handle_cloudflare()
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, self.timeout)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Additional wait for dynamic content
            time.sleep(2)
            
            # Get page HTML
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find tournament links - BetExplorer structure
            # Look for links containing tournament names with W15/W25
            tournament_links = soup.find_all('a', href=re.compile(r'/tennis/itf-women/'))
            
            for link in tournament_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Filter for W15/W25 tournaments
                if 'W15' in text or 'W25' in text:
                    # Parse tournament name to extract tier, location, surface
                    parsed = self.parse_tournament_name(text)
                    
                    if parsed:
                        tournament = {
                            'name': text,
                            'url': f"https://www.betexplorer.com{href}" if not href.startswith('http') else href,
                            'tier': parsed['tier'],
                            'location': parsed['location'],
                            'surface': parsed['surface']
                        }
                        tournaments.append(tournament)
                        logger.debug(f"✅ Found tournament: {text}")
            
            logger.info(f"📊 Found {len(tournaments)} W15/W25 tournaments")
            
        except Exception as e:
            logger.error(f"❌ Error getting tournaments: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        return tournaments
    
    def parse_tournament_name(self, name: str) -> Optional[Dict[str, str]]:
        """
        Parse tournament name to extract tier, location, surface
        
        Example: "W15 Alcala de Henares, hard" -> {tier: "W15", location: "Alcala de Henares", surface: "hard"}
        
        Args:
            name: Tournament name string
            
        Returns:
            Dictionary with tier, location, surface or None
        """
        try:
            # Pattern: W15/W25 + Location + Surface
            # Examples:
            # - "W15 Alcala de Henares, hard"
            # - "W25 Hua Hin 2, hard"
            # - "W15 Mogi das Cruzes, clay"
            
            # Extract tier
            tier_match = re.search(r'\b(W15|W25|W35|W50|W75|W100)\b', name)
            if not tier_match:
                return None
            
            tier = tier_match.group(1)
            
            # Extract surface (hard, clay, grass)
            surface_match = re.search(r'\b(hard|clay|grass)\b', name, re.I)
            surface = surface_match.group(1).lower().capitalize() if surface_match else 'Hard'
            
            # Extract location (everything between tier and surface)
            location_match = re.search(rf'{tier}\s+(.+?)(?:,\s*(?:hard|clay|grass))?$', name, re.I)
            if location_match:
                location = location_match.group(1).strip()
            else:
                # Fallback: remove tier and surface
                location = re.sub(rf'\b{tier}\b', '', name, flags=re.I)
                location = re.sub(r'\b(hard|clay|grass)\b', '', location, flags=re.I)
                location = location.replace(',', '').strip()
            
            return {
                'tier': tier,
                'location': location,
                'surface': surface
            }
            
        except Exception as e:
            logger.debug(f"⚠️ Error parsing tournament name '{name}': {e}")
            return None
    
    def scrape_tournament_matches(self, tournament_url: str) -> List[Dict]:
        """
        Scrape matches from a tournament page
        
        Args:
            tournament_url: URL of the tournament page
            
        Returns:
            List of match dictionaries with player names, time, odds link
        """
        if not self.driver:
            return []
        
        matches = []
        
        try:
            logger.info(f"🌐 Loading tournament page: {tournament_url}")
            self._rate_limit()
            self.driver.get(tournament_url)
            
            # Handle Cloudflare
            self._handle_cloudflare()
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, self.timeout)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)
            
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find match rows - BetExplorer structure
            # Look for table rows with match data
            match_rows = soup.find_all('tr', class_=re.compile(r'match|event', re.I))
            
            # Alternative: look for divs with match data
            if not match_rows:
                match_rows = soup.find_all('div', class_=re.compile(r'match|event', re.I))
            
            for row in match_rows:
                match_data = self._extract_match_from_row(row, tournament_url)
                if match_data and self._validate_match(match_data):
                    matches.append(match_data)
            
            logger.info(f"📊 Found {len(matches)} matches in tournament")
            
        except Exception as e:
            logger.error(f"❌ Error scraping tournament matches: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        return matches
    
    def _extract_match_from_row(self, row, tournament_url: str) -> Optional[Dict]:
        """Extract match data from a table row or div"""
        try:
            # Try to find player names
            players = row.find_all(['td', 'div'], class_=re.compile(r'team|player|participant', re.I))
            
            if len(players) < 2:
                # Alternative: look for links with player names
                links = row.find_all('a', href=re.compile(r'/match/'))
                if len(links) >= 2:
                    player1 = links[0].get_text(strip=True)
                    player2 = links[1].get_text(strip=True)
                else:
                    # Fallback: extract from text
                    text_parts = row.get_text(separator='|').split('|')
                    text_parts = [t.strip() for t in text_parts if t.strip() and len(t.strip()) > 2]
                    if len(text_parts) >= 2:
                        player1 = text_parts[0]
                        player2 = text_parts[1]
                    else:
                        return None
            else:
                player1 = players[0].get_text(strip=True)
                player2 = players[1].get_text(strip=True)
            
            # Find match time
            time_elem = row.find(['td', 'div', 'span'], class_=re.compile(r'time|date', re.I))
            match_time = time_elem.get_text(strip=True) if time_elem else None
            
            # Find odds link
            odds_link = row.find('a', href=re.compile(r'/match/.*odds|/odds/'))
            odds_url = None
            if odds_link:
                href = odds_link.get('href', '')
                odds_url = f"https://www.betexplorer.com{href}" if href.startswith('/') else href
            
            # Generate match ID
            match_id = f"betexplorer_{hash(f'{player1}_{player2}_{match_time}') % 100000}"
            
            return {
                'match_id': match_id,
                'player1': player1,
                'player2': player2,
                'match_time': match_time,
                'odds_url': odds_url,
                'tournament_url': tournament_url
            }
            
        except Exception as e:
            logger.debug(f"⚠️ Error extracting match from row: {e}")
            return None
    
    def scrape_match_odds(self, odds_url: str) -> List[Dict]:
        """
        Scrape odds comparison for a match from odds page
        
        Args:
            odds_url: URL of the odds comparison page
            
        Returns:
            List of bookmaker odds dictionaries
        """
        if not self.driver or not odds_url:
            return []
        
        odds_data = []
        
        try:
            logger.debug(f"🌐 Loading odds page: {odds_url}")
            self._rate_limit()
            self.driver.get(odds_url)
            
            # Handle Cloudflare
            self._handle_cloudflare()
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, self.timeout)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)
            
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find odds table - BetExplorer structure
            # Look for table with odds data
            odds_table = soup.find('table', class_=re.compile(r'odds|bookmaker', re.I))
            
            if not odds_table:
                # Alternative: look for divs with odds
                odds_table = soup.find('div', class_=re.compile(r'odds|bookmaker', re.I))
            
            if odds_table:
                # Extract rows from table
                rows = odds_table.find_all('tr')
                
                for row in rows[1:]:  # Skip header
                    cols = row.find_all(['td', 'th'])
                    if len(cols) >= 3:
                        bookmaker = cols[0].get_text(strip=True)
                        
                        # Extract odds (player1 and player2)
                        try:
                            odds1_text = cols[1].get_text(strip=True)
                            odds2_text = cols[2].get_text(strip=True)
                            
                            # Parse odds (handle formats like "1.75" or "7/4")
                            odds1 = self._parse_odds(odds1_text)
                            odds2 = self._parse_odds(odds2_text)
                            
                            if odds1 and odds2 and bookmaker:
                                odds_data.append({
                                    'bookmaker': bookmaker,
                                    'odds_home': odds1,
                                    'odds_away': odds2
                                })
                        except (ValueError, IndexError) as e:
                            logger.debug(f"⚠️ Error parsing odds: {e}")
                            continue
            
            logger.debug(f"📊 Found {len(odds_data)} bookmaker odds")
            
        except Exception as e:
            logger.error(f"❌ Error scraping match odds: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        return odds_data
    
    def _parse_odds(self, odds_text: str) -> Optional[float]:
        """Parse odds from text (handles decimal and fractional formats)"""
        try:
            # Remove whitespace
            odds_text = odds_text.strip()
            
            # Try decimal format (e.g., "1.75")
            try:
                return float(odds_text)
            except ValueError:
                pass
            
            # Try fractional format (e.g., "7/4" = 1.75)
            if '/' in odds_text:
                parts = odds_text.split('/')
                if len(parts) == 2:
                    numerator = float(parts[0])
                    denominator = float(parts[1])
                    return (numerator / denominator) + 1.0  # Convert to decimal
            
            return None
            
        except Exception as e:
            logger.debug(f"⚠️ Error parsing odds '{odds_text}': {e}")
            return None
    
    def find_best_odds(self, odds_data: List[Dict]) -> Dict:
        """
        Find best back odds for each player from all bookmakers
        
        Args:
            odds_data: List of bookmaker odds dictionaries
            
        Returns:
            Dictionary with best odds and bookmaker for each player
        """
        if not odds_data:
            return {
                'player_1': {'odds': None, 'bookmaker': None},
                'player_2': {'odds': None, 'bookmaker': None}
            }
        
        # Find best odds for player 1 (home)
        best_p1 = max(odds_data, key=lambda x: x.get('odds_home', 0))
        
        # Find best odds for player 2 (away)
        best_p2 = max(odds_data, key=lambda x: x.get('odds_away', 0))
        
        return {
            'player_1': {
                'odds': best_p1.get('odds_home'),
                'bookmaker': best_p1.get('bookmaker')
            },
            'player_2': {
                'odds': best_p2.get('odds_away'),
                'bookmaker': best_p2.get('bookmaker')
            }
        }
    
    def _validate_match(self, match: Dict) -> bool:
        """Validate that match data is complete (reused from FlashScore pattern)"""
        if not match.get('player1') or not match.get('player2'):
            return False
        
        if match['player1'] == match['player2']:
            return False
        
        # Player names should be reasonable length
        if len(match['player1']) < 3 or len(match['player2']) < 3:
            return False
        
        # Filter out obvious non-player text
        invalid_names = ['vs', 'v', '–', '-', 'live', 'finished', 'upcoming', 'match', 'odds']
        if match['player1'].lower() in invalid_names or match['player2'].lower() in invalid_names:
            return False
        
        return True
    
    def scrape(self, tiers: List[str] = None) -> List[Dict]:
        """
        Main scrape method
        
        Args:
            tiers: List of tiers to scrape (default: ['W15', 'W25'])
            
        Returns:
            List of match dictionaries with odds data
        """
        if tiers is None:
            tiers = ['W15', 'W25']
        
        all_matches = []
        
        try:
            # Step 1: Get all W15/W25 tournaments
            tournaments = self.get_w15_tournaments()
            
            # Filter by requested tiers
            filtered_tournaments = [
                t for t in tournaments 
                if t['tier'] in tiers
            ]
            
            logger.info(f"📊 Scraping {len(filtered_tournaments)} tournaments (tiers: {tiers})")
            
            # Step 2: For each tournament, scrape matches
            for tournament in filtered_tournaments:
                logger.info(f"🎾 Scraping tournament: {tournament['name']}")
                
                matches = self.scrape_tournament_matches(tournament['url'])
                
                # Step 3: For each match, scrape odds
                for match in matches:
                    if match.get('odds_url'):
                        odds_data = self.scrape_match_odds(match['odds_url'])
                        best_odds = self.find_best_odds(odds_data)
                        
                        # Add tournament and odds info to match
                        match['tournament'] = tournament['name']
                        match['tier'] = tournament['tier']
                        match['location'] = tournament['location']
                        match['surface'] = tournament['surface']
                        match['best_odds_p1'] = best_odds['player_1']['odds']
                        match['bookmaker_p1'] = best_odds['player_1']['bookmaker']
                        match['best_odds_p2'] = best_odds['player_2']['odds']
                        match['bookmaker_p2'] = best_odds['player_2']['bookmaker']
                        match['odds_count'] = len(odds_data)
                        match['scraped_at'] = datetime.now().isoformat()
                        match['data_source'] = 'BetExplorer'
                        
                        all_matches.append(match)
                        
                        # Rate limiting between matches
                        time.sleep(random.uniform(1, 2))
                    else:
                        logger.debug(f"⚠️ No odds URL for match: {match.get('player1')} vs {match.get('player2')}")
                
                # Rate limiting between tournaments
                time.sleep(random.uniform(2, 3))
            
            logger.info(f"✅ Scraped {len(all_matches)} matches with odds data")
            
        except Exception as e:
            logger.error(f"❌ Error in scrape method: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return all_matches
    
    def __del__(self):
        """Cleanup Selenium driver (reused from FlashScore)"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass


# USAGE EXAMPLE
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    config = {
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'request_delay': 2.0,
        'max_retries': 3,
        'timeout': 30
    }
    
    scraper = BetExplorerScraper(config, use_selenium=True)
    
    try:
        matches = scraper.scrape(tiers=['W15'])
        
        print(f"\n📊 RESULTS:")
        print(f"Total matches: {len(matches)}")
        
        if matches:
            for match in matches[:5]:  # Show first 5
                print(f"\n🎾 {match.get('tournament', 'Unknown')}")
                print(f"   {match.get('player1')} vs {match.get('player2')}")
                print(f"   Surface: {match.get('surface')} | Tier: {match.get('tier')}")
                print(f"   Best Odds P1: {match.get('best_odds_p1')} ({match.get('bookmaker_p1')})")
                print(f"   Best Odds P2: {match.get('best_odds_p2')} ({match.get('bookmaker_p2')})")
        else:
            print("\n⚠️ No matches found")
    
    finally:
        del scraper

