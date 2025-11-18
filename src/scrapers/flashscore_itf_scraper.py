#!/usr/bin/env python3
"""
🎾 ENHANCED FLASHSCORE ITF SCRAPER
==================================

Production-ready scraper that finds BOTH tournaments AND matches.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class ITFMatch:
    """ITF Women match data structure"""
    match_id: str
    tournament: str
    tournament_tier: str  # W15, W35, W50, W75, W100
    surface: Optional[str]  # Hard, Clay, Grass
    player1: str
    player2: str
    round: Optional[str]  # R32, R16, QF, SF, F
    match_status: str  # not_started, live, finished
    live_score: Optional[str]  # "6-4, 3-2" for live matches
    set1_score: Optional[str]  # "6-4" for first set
    scheduled_time: Optional[datetime]
    match_url: Optional[str]
    scraped_at: datetime
    player1_odds: Optional[float] = None  # Odds for player1
    player2_odds: Optional[float] = None  # Odds for player2


"""
Multi-strategy approach:
- Selenium for dynamic content
- Multiple CSS selector strategies
- Fallback mechanisms
- Extensive logging
- Match validation
"""

import asyncio
import logging
import time
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
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("⚠️ Selenium not available")

# Try to import requests for fallback
try:
    import aiohttp
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class FlashScoreITFScraperEnhanced:
    """
    Enhanced scraper with:
    - Selenium for dynamic content
    - Multiple CSS selector strategies
    - Fallback mechanisms
    - Extensive logging
    - Match validation
    """
    
    BASE_URLS = {
        'W15': 'https://www.flashscore.com/tennis/',
        'W25': 'https://www.flashscore.com/tennis/',
        'W35': 'https://www.flashscore.com/tennis/',
        'W50': 'https://www.flashscore.com/tennis/'
    }
    
    # FlashScore uses JavaScript to load tournaments, so we scrape from main tennis page
    # and filter for ITF Women tournaments
    
    def __init__(self, config: dict = None, use_selenium: bool = True):
        """
        Initialize enhanced scraper
        
        Args:
            config: Configuration dictionary
            use_selenium: Whether to use Selenium (recommended)
        """
        self.config = config or {}
        self.use_selenium = use_selenium and SELENIUM_AVAILABLE
        self.driver = None
        
        if self.use_selenium:
            self._init_selenium()
        
        logger.info(f"🎾 Enhanced FlashScore Scraper initialized (Selenium: {self.use_selenium})")
    
    def _init_selenium(self):
        """Initialize Selenium WebDriver with anti-detection"""
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
    
    def scrape_with_selenium(self, url: str, tier: str) -> List[Dict]:
        """
        Scrape with Selenium (wait for JS to load)
        
        FlashScore loads matches dynamically via JavaScript.
        Strategy:
        1. Load main tennis page
        2. Filter for ITF Women tournaments
        3. Wait for match rows to appear
        4. Scroll down (lazy loading)
        5. Extract HTML
        6. Parse with BeautifulSoup
        """
        if not self.driver:
            logger.error("❌ Selenium driver not available")
            return []
        
        logger.info(f"🌐 Loading tennis page with Selenium: {url}")
        logger.info(f"   Filtering for {tier} tournaments...")
        
        try:
            self.driver.get(url)
            
            # Wait for page to load using WebDriverWait instead of blocking sleep
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Try to find and click ITF Women filter if available
            try:
                # Look for ITF Women link/button with wait
                itf_link = wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "ITF")))
                if itf_link:
                    itf_link.click()
                    # Wait for filter to apply (non-blocking wait)
                    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            except:
                logger.debug("Could not find ITF filter, continuing...")
            
            # Wait for matches to load (max 15s) - already initialized above
            
            # Multiple selector strategies
            selectors = [
                (By.CLASS_NAME, "event__match"),
                (By.CSS_SELECTOR, "div[id^='g_1']"),  # FlashScore match rows
                (By.CSS_SELECTOR, ".event__match"),
                (By.XPATH, "//div[contains(@class, 'event__match')]"),
                (By.CSS_SELECTOR, "[class*='event']")
            ]
            
            found = False
            for by, selector in selectors:
                try:
                    wait.until(EC.presence_of_element_located((by, selector)))
                    logger.info(f"✅ Found matches with selector: {selector}")
                    found = True
                    break
                except:
                    continue
            
            if not found:
                logger.warning("⚠️ No matches found with standard selectors, trying fallback...")
                # Wait for content to load using explicit wait instead of blocking sleep
                wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            
            # Scroll to load lazy content - optimized with async-like waits
            for i in range(5):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                # Use WebDriverWait for shorter, non-blocking waits
                WebDriverWait(self.driver, 1).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
            
            # Get rendered HTML
            html = self.driver.page_source
            
            # Save for debugging (optional)
            if self.config.get('save_debug_html'):
                debug_path = Path(__file__).parent.parent.parent / 'data' / f'debug_{tier}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
                debug_path.parent.mkdir(parents=True, exist_ok=True)
                with open(debug_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                logger.info(f"💾 Saved debug HTML to {debug_path}")
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Parse matches and filter by tier
            all_matches = self._parse_matches_enhanced(soup, tier)
            
            # Filter matches by tier AND exclude Men tournaments
            matches = []
            for m in all_matches:
                tournament = m.get('tournament', '').upper()
                
                # Exclude Men tournaments explicitly
                if 'MEN' in tournament and 'WOMEN' not in tournament:
                    continue
                if ' M15' in tournament or ' M25' in tournament or ' M35' in tournament:
                    continue
                
                # Check for ITF Women with specific tier (W15, W25, W35, W50)
                # Must have: ITF + WOMEN + tier number
                has_itf = 'ITF' in tournament
                has_women = 'WOMEN' in tournament
                has_tier = tier in tournament or f'W{tier[1:]}' in tournament
                
                if has_itf and has_women and has_tier:
                    matches.append(m)
            
            logger.info(f"📊 {tier}: Found {len(matches)} ITF Women matches (from {len(all_matches)} total)")
            return matches
            
        except Exception as e:
            logger.error(f"❌ Selenium scrape failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_matches_enhanced(self, soup: BeautifulSoup, tier: str) -> List[Dict]:
        """
        Enhanced match parsing with multiple strategies
        
        FlashScore HTML patterns (as of 2025):
        
        Pattern 1: div.event__match (common)
        Pattern 2: div[id^='g_1_'] (alternative)
        Pattern 3: Nested structure (fallback)
        """
        matches = []
        
        # STRATEGY 1: Standard event__match
        match_rows = soup.find_all('div', class_='event__match')
        logger.info(f"Strategy 1: Found {len(match_rows)} match rows")
        
        if not match_rows:
            # STRATEGY 2: ID-based selection
            match_rows = soup.find_all('div', id=lambda x: x and x.startswith('g_1_'))
            logger.info(f"Strategy 2: Found {len(match_rows)} match rows")
        
        if not match_rows:
            # STRATEGY 3: Fallback - find all divs with event classes
            match_rows = soup.find_all('div', class_=lambda x: x and 'event' in str(x).lower())
            logger.info(f"Strategy 3: Found {len(match_rows)} potential match rows")
        
        if not match_rows:
            # STRATEGY 4: Find by data attributes
            match_rows = soup.find_all('div', attrs={'data-testid': lambda x: x and 'match' in str(x).lower()})
            logger.info(f"Strategy 4: Found {len(match_rows)} potential match rows")
        
        for row in match_rows:
            match = self._extract_match_data(row, tier)
            
            if match and self._validate_match(match):
                matches.append(match)
        
        return matches
    
    def _extract_match_data(self, row, tier: str) -> Optional[Dict]:
        """
        Extract match data from row element
        
        Try multiple extraction strategies
        """
        try:
            # Extract tournament (look up in DOM tree)
            tournament = self._find_tournament_name(row)
            
            # Extract players
            player_a, player_b = self._extract_players(row)
            
            if not player_a or not player_b:
                logger.debug(f"⚠️ Skipping row: players not found")
                return None
            
            # Extract score
            score = self._extract_score(row)
            
            # Extract status
            status = self._extract_status(row)
            
            # Extract time
            match_time = self._extract_time(row)
            
            # Extract surface (from tournament name or separate field)
            surface = self._extract_surface(tournament, row)
            
            # Extract round
            round_str = self._extract_round(row)
            
            return {
                'match_id': f"{tier}_{player_a}_{player_b}_{hash(str(row)) % 10000}",
                'tournament': tournament,
                'tier': tier,
                'surface': surface,
                'player_a': player_a,
                'player_b': player_b,
                'live_score': score,
                'match_status': status,
                'match_time': match_time,
                'round': round_str,
                'scraped_at': datetime.now().isoformat(),
                'source': 'FlashScore'
            }
            
        except Exception as e:
            logger.debug(f"⚠️ Extract failed: {e}")
            return None
    
    def _extract_players(self, row) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract player names with multiple strategies
        
        Patterns:
        1. div.event__participant (standard)
        2. span.participant-name (alternative)
        3. Nested divs with data-player attribute
        """
        # Strategy 1: Standard FlashScore pattern
        participants = row.find_all('div', class_='event__participant')
        if len(participants) >= 2:
            p1 = participants[0].get_text(strip=True)
            p2 = participants[1].get_text(strip=True)
            if p1 and p2 and len(p1) > 2 and len(p2) > 2:
                return p1, p2
        
        # Strategy 2: Alternative class names
        participants = row.find_all('span', class_='participant-name')
        if len(participants) >= 2:
            p1 = participants[0].get_text(strip=True)
            p2 = participants[1].get_text(strip=True)
            if p1 and p2 and len(p1) > 2 and len(p2) > 2:
                return p1, p2
        
        # Strategy 3: Find by data attributes
        participants = row.find_all('div', attrs={'data-participant': True})
        if len(participants) >= 2:
            p1 = participants[0].get_text(strip=True)
            p2 = participants[1].get_text(strip=True)
            if p1 and p2 and len(p1) > 2 and len(p2) > 2:
                return p1, p2
        
        # Strategy 4: Find all text elements and filter
        text_elems = row.find_all(text=True, recursive=True)
        # Filter out empty, short, and common words
        names = [t.strip() for t in text_elems 
                if t.strip() and len(t.strip()) > 3 
                and t.strip() not in ['vs', 'v', '–', '-', 'Live', 'Finished', 'Upcoming']]
        
        if len(names) >= 2:
            # First two reasonable-length strings are usually players
            return names[0], names[1]
        
        return None, None
    
    def _extract_score(self, row) -> str:
        """Extract current score"""
        # Try multiple selectors
        selectors = [
            ('div', 'event__score'),
            ('div', 'event__scores'),
            ('span', 'score'),
            ('div', 'event__result'),
        ]
        
        for tag, class_name in selectors:
            score_elem = row.find(tag, class_=class_name)
            if score_elem:
                score_text = score_elem.get_text(strip=True)
                if score_text:
                    return score_text
        
        # Fallback: look for score-like patterns in text
        text = row.get_text()
        import re
        score_pattern = re.search(r'(\d+-\d+(?:\s*,\s*\d+-\d+)*)', text)
        if score_pattern:
            return score_pattern.group(1)
        
        return ""
    
    def _extract_status(self, row) -> str:
        """
        Extract match status
        
        Possible values:
        - Upcoming (no status shown)
        - Live (status shows "Live" or current set)
        - Completed (status shows "Fin" or "Finished")
        """
        # Check for live indicator
        if row.find('div', class_='live-icon') or row.find('span', class_='live-icon'):
            return 'Live'
        
        status_elem = row.find('div', class_=lambda x: x and 'event__stage' in str(x).lower())
        
        if not status_elem:
            # Check text content for status indicators
            text = row.get_text().lower()
            if 'live' in text or 'set' in text:
                return 'Live'
            return 'Upcoming'
        
        status_text = status_elem.get_text(strip=True).lower()
        
        if any(x in status_text for x in ['fin', 'finished', 'ended', 'completed']):
            return 'Completed'
        elif any(x in status_text for x in ['live', 'set']):
            return 'Live'
        elif 'postponed' in status_text:
            return 'Postponed'
        elif 'cancelled' in status_text:
            return 'Cancelled'
        
        return 'Upcoming'
    
    def _extract_time(self, row) -> str:
        """Extract match time"""
        time_elem = row.find('div', class_=lambda x: x and 'event__time' in str(x).lower())
        if time_elem:
            return time_elem.get_text(strip=True)
        
        # Fallback: look for time patterns
        text = row.get_text()
        import re
        time_pattern = re.search(r'(\d{1,2}:\d{2})', text)
        if time_pattern:
            return time_pattern.group(1)
        
        return ""
    
    def _extract_round(self, row) -> Optional[str]:
        """Extract round information"""
        round_elem = row.find('div', class_=lambda x: x and 'round' in str(x).lower())
        if round_elem:
            return round_elem.get_text(strip=True)
        
        # Check text for round patterns
        text = row.get_text()
        import re
        round_pattern = re.search(r'\b(R\d+|QF|SF|F|FINAL|Quarter|Semi|Final)\b', text, re.I)
        if round_pattern:
            return round_pattern.group(1)
        
        return None
    
    def _find_tournament_name(self, row) -> str:
        """
        Find tournament name (look up in DOM tree)
        
        FlashScore uses headerLeague divs for tournament headers
        """
        # Strategy 1: Look for previous headerLeague (FlashScore structure)
        # Find the CLOSEST previous headerLeague (not just any previous)
        header_league = None
        current = row
        for _ in range(20):  # Check up to 20 levels back
            prev = current.find_previous('div', class_='headerLeague')
            if prev:
                # Check if this is closer than previous find
                if header_league is None:
                    header_league = prev
                else:
                    # Use the one that appears later in document (closer to match)
                    if prev.sourceline and header_league.sourceline:
                        if prev.sourceline > header_league.sourceline:
                            header_league = prev
                    break
            current = current.parent
            if not current:
                break
        
        if header_league:
            # Get tournament name - try multiple strategies
            name_span = header_league.find('span', class_='headerLeague__name')
            category_span = header_league.find('span', class_='headerLeague__category')
            
            # Strategy 1: Use name span
            name = ""
            if name_span:
                name = name_span.get_text(strip=True)
            
            # Strategy 2: Extract from link (FlashScore stores tournament name in link)
            link = header_league.find('a')
            if link:
                link_text = link.get_text(strip=True)
                if link_text and len(link_text) > 3:
                    name = link_text
            
            # Strategy 3: Extract from all text (filter out category)
            if not name or len(name) < 3:
                all_text = header_league.get_text(separator=' ', strip=True)
                # Remove category text
                if category_span:
                    cat_text = category_span.get_text(strip=True)
                    all_text = all_text.replace(cat_text, '').strip()
                # Remove colon and extra spaces
                all_text = all_text.replace(':', '').strip()
                # Take first reasonable chunk (tournament name is usually first)
                words = all_text.split()
                if words:
                    # Find where tournament name ends (usually before location)
                    name_parts = []
                    for word in words:
                        if word.lower() in ['hard', 'clay', 'grass'] or '(' in word:
                            break
                        name_parts.append(word)
                    if name_parts:
                        name = ' '.join(name_parts)
            
            category = category_span.get_text(strip=True) if category_span else ""
            
            # Combine name and category
            if name and category:
                full_name = f"{name} - {category}"
            elif name:
                full_name = name
            elif category:
                full_name = category
            else:
                full_name = ""
            
            if full_name and len(full_name) > 3:
                return full_name
        
        # Strategy 2: Look for previous sibling with event__header class
        current = row
        for _ in range(15):  # Max 15 levels up
            # Check previous siblings
            prev_sibling = current.find_previous_sibling()
            if prev_sibling:
                classes = prev_sibling.get('class', [])
                if classes and 'event__header' in str(classes):
                    title = prev_sibling.find('span', class_='event__title')
                    if title:
                        name = title.get_text(strip=True)
                        if name and len(name) > 3:
                            return name
                    
                    # Alternative: look for any text in header
                    header_text = prev_sibling.get_text(strip=True)
                    if header_text and len(header_text) > 3:
                        # Filter out common non-tournament text
                        if header_text not in ['Live', 'Finished', 'Upcoming']:
                            return header_text
            
            # Check parent
            current = current.parent
            if not current:
                break
            
            # Check if parent has tournament info
            if current.name == 'div':
                classes = current.get('class', [])
                if classes and 'event__header' in str(classes):
                    title = current.find('span', class_='event__title')
                    if title:
                        name = title.get_text(strip=True)
                        if name and len(name) > 3:
                            return name
        
        # Strategy 3: Look backwards for headerLeague
        all_headers = row.find_all_previous('div', class_='headerLeague', limit=5)
        for header in all_headers:
            name_span = header.find('span', class_='headerLeague__name')
            if name_span:
                name = name_span.get_text(strip=True)
                if name and len(name) > 3:
                    return name
        
        # Strategy 4: Extract from nearby text containing ITF
        import re
        parent_text = row.find_parent().get_text() if row.find_parent() else ""
        itf_match = re.search(r'(ITF[^\.\n]{5,80})', parent_text, re.I)
        if itf_match:
            return itf_match.group(1).strip()
        
        return "Unknown Tournament"
    
    def _extract_surface(self, tournament_name: str, row) -> str:
        """Extract court surface from tournament name or row"""
        text = (tournament_name + " " + row.get_text()).lower()
        
        if 'hard' in text or 'hardcourt' in text:
            return 'Hard'
        elif 'clay' in text:
            return 'Clay'
        elif 'grass' in text:
            return 'Grass'
        
        return 'Hard'  # Default
    
    def _validate_match(self, match: Dict) -> bool:
        """
        Validate that match data is complete
        
        Required fields:
        - player_a (non-empty)
        - player_b (non-empty)
        - Different players (not same name)
        - Tournament is ITF Women (not Men)
        """
        if not match.get('player_a') or not match.get('player_b'):
            return False
        
        if match['player_a'] == match['player_b']:
            return False
        
        # Player names should be reasonable length
        if len(match['player_a']) < 3 or len(match['player_b']) < 3:
            return False
        
        # Filter out obvious non-player text
        invalid_names = ['vs', 'v', '–', '-', 'live', 'finished', 'upcoming', 'match']
        if match['player_a'].lower() in invalid_names or match['player_b'].lower() in invalid_names:
            return False
        
        # Exclude Men tournaments (but allow Women)
        tournament = match.get('tournament', '').upper()
        if tournament != "UNKNOWN TOURNAMENT":  # Only filter if we know the tournament
            if 'MEN' in tournament and 'WOMEN' not in tournament:
                return False
            if ' M15' in tournament or ' M25' in tournament or ' M35' in tournament:
                return False
        
        return True
    
    async def fetch_odds_for_matches(self, matches: List[Dict]) -> List[Dict]:
        """
        Fetch odds for scraped matches using Odds API
        
        Args:
            matches: List of match dictionaries from scraper
        
        Returns:
            List of matches with odds added
        """
        try:
            # Try to import OddsFetcher
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from utils.odds_fetcher import OddsFetcher
            
            async with OddsFetcher() as fetcher:
                # Fetch tennis matches from Odds API
                odds_matches = await fetcher.fetch_tennis_matches(hours_ahead=48)
                
                if not odds_matches:
                    logger.warning("⚠️ No odds matches found from Odds API")
                    return matches
                
                logger.info(f"📊 Fetched {len(odds_matches)} matches from Odds API")
                
                # Match scraped matches with odds matches by player names
                for match in matches:
                    player_a = match.get('player_a', '').strip()
                    player_b = match.get('player_b', '').strip()
                    
                    if not player_a or not player_b:
                        continue
                    
                    # Try to find matching odds match
                    best_match = None
                    best_score = 0.0
                    
                    for odds_match in odds_matches:
                        home_team = odds_match.home_team.strip()
                        away_team = odds_match.away_team.strip()
                        
                        # Calculate name similarity score
                        score = 0.0
                        
                        # Exact match
                        if (player_a.lower() == home_team.lower() and 
                            player_b.lower() == away_team.lower()):
                            score = 1.0
                        elif (player_a.lower() == away_team.lower() and 
                              player_b.lower() == home_team.lower()):
                            score = 1.0
                        # Partial match (last name)
                        elif (player_a.split()[-1].lower() == home_team.split()[-1].lower() and
                              player_b.split()[-1].lower() == away_team.split()[-1].lower()):
                            score = 0.8
                        elif (player_a.split()[-1].lower() == away_team.split()[-1].lower() and
                              player_b.split()[-1].lower() == home_team.split()[-1].lower()):
                            score = 0.8
                        
                        if score > best_score:
                            best_score = score
                            best_match = odds_match
                    
                    # If we found a good match, add odds
                    if best_match and best_score >= 0.8:
                        player_a_odds, player_b_odds = best_match.get_best_odds()
                        
                        # Determine which player corresponds to which odds
                        home_team = best_match.home_team.strip()
                        away_team = best_match.away_team.strip()
                        
                        if player_a.lower() == home_team.lower():
                            match['player_a_odds'] = player_a_odds
                            match['player_b_odds'] = player_b_odds
                        elif player_a.lower() == away_team.lower():
                            match['player_a_odds'] = player_b_odds
                            match['player_b_odds'] = player_a_odds
                        else:
                            # Default: assume player_a is home
                            match['player_a_odds'] = player_a_odds
                            match['player_b_odds'] = player_b_odds
                        
                        logger.debug(f"✅ Matched odds for {player_a} vs {player_b}: {match.get('player_a_odds')} / {match.get('player_b_odds')}")
                
                matched_count = sum(1 for m in matches if m.get('player_a_odds'))
                logger.info(f"✅ Matched odds for {matched_count}/{len(matches)} matches")
                
        except ImportError:
            logger.warning("⚠️ OddsFetcher not available, skipping odds fetching")
        except Exception as e:
            logger.error(f"❌ Error fetching odds: {e}")
            import traceback
            traceback.print_exc()
        
        return matches
    
    def scrape(self, tiers: List[str] = None, fetch_odds: bool = False) -> List[Dict]:
        """
        Main scrape method
        
        Args:
            tiers: List of tiers to scrape (W15, W35, W50)
            fetch_odds: Whether to fetch odds from Odds API (async operation)
        
        Returns:
            List of match dictionaries
        """
        if tiers is None:
            tiers = ['W15', 'W35', 'W50']
        
        all_matches = []
        
        for tier in tiers:
            url = self.BASE_URLS.get(tier)
            if not url:
                logger.warning(f"⚠️ Unknown tier: {tier}")
                continue
            
            logger.info(f"📊 Scraping {tier}...")
            
            if self.use_selenium:
                matches = self.scrape_with_selenium(url, tier)
            else:
                # Fallback to requests (less reliable)
                matches = self.scrape_with_requests(url, tier)
            
            logger.info(f"✅ {tier}: {len(matches)} matches found")
            all_matches.extend(matches)
            
            # Rate limiting - only wait if needed (configurable)
            request_delay = self.config.get('request_delay', 2)
            if request_delay > 0:
                time.sleep(request_delay)
        
        # Fetch odds if requested (async)
        if fetch_odds and all_matches:
            try:
                # Run async odds fetching
                all_matches = asyncio.run(self.fetch_odds_for_matches(all_matches))
            except Exception as e:
                logger.error(f"❌ Error fetching odds: {e}")
        
        return all_matches
    
    def scrape_with_requests(self, url: str, tier: str) -> List[Dict]:
        """Fallback scraping with requests (less reliable for dynamic content)"""
        logger.warning("⚠️ Using requests fallback (may not work for dynamic content)")
        # This would need aiohttp implementation
        return []
    
    def __del__(self):
        """Cleanup Selenium driver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass


# USAGE EXAMPLE:

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    config = {
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'request_delay': 2,
        'save_debug_html': True  # Save HTML for debugging
    }
    
    scraper = FlashScoreITFScraperEnhanced(config, use_selenium=True)
    
    try:
        matches = scraper.scrape(tiers=['W15'])
        
        print(f"\n📊 RESULTS:")
        print(f"Total matches: {len(matches)}")
        
        if matches:
            for match in matches[:5]:  # Show first 5
                print(f"\n🎾 {match['tournament']}")
                print(f"   {match['player_a']} vs {match['player_b']}")
                print(f"   Surface: {match['surface']} | Status: {match['match_status']}")
                if match['live_score']:
                    print(f"   Score: {match['live_score']}")
        else:
            print("\n⚠️ No matches found")
            print("💡 Check debug HTML files in data/ directory")
            print("💡 Inspect FlashScore page structure in Chrome DevTools")
    
    finally:
        del scraper

