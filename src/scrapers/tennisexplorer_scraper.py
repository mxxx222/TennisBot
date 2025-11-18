#!/usr/bin/env python3
"""
🎾 TENNISEXPLORER SCRAPER
=========================

Production-ready scraper for TennisExplorer.com that complements FlashScore scraper.
Focuses on H2H data, recent form, odds comparison, and tournament history.

Endpoints:
- /live-tennis/ - Live matches with scores and odds
- /player-vs-player/ - H2H overall + surface-specific
- /player/ - Recent form (last 10 matches)
- /odds-comparison/?id={match_id} - Multi-bookmaker odds
- Tournament pages - Tournament history at venue
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import logging
import time
import re
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Try to import Selenium
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("⚠️ Selenium not available")

# Try to import requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("⚠️ Requests not available")


@dataclass
class TennisExplorerMatch:
    """TennisExplorer match data structure"""
    match_id: str
    player_a: str
    player_b: str
    tournament: str
    tournament_tier: str
    surface: str
    current_score: Optional[str] = None
    live_odds_a: Optional[float] = None
    live_odds_b: Optional[float] = None
    h2h_overall: Optional[Dict[str, int]] = None  # {'wins_a': 2, 'wins_b': 1}
    h2h_surface: Optional[Dict[str, Dict[str, int]]] = None  # {'hard': {'wins_a': 1, 'wins_b': 0}}
    recent_form_a: Optional[Dict[str, Any]] = None  # {'last_5': '4-1', 'last_10': '7-3'}
    recent_form_b: Optional[Dict[str, Any]] = None
    tournament_history: Optional[List[Dict]] = None  # Previous years at this venue
    match_url: Optional[str] = None
    scraped_at: datetime = None
    
    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.now()


@dataclass
class H2HRecord:
    """Head-to-head record"""
    player_a: str
    player_b: str
    overall: Dict[str, int]  # {'wins_a': 2, 'wins_b': 1}
    by_surface: Dict[str, Dict[str, int]]  # {'hard': {'wins_a': 1, 'wins_b': 0}}
    last_meetings: List[Dict]  # Last 5 meetings with scores


@dataclass
class PlayerForm:
    """Player recent form"""
    player_name: str
    last_5_wins: int
    last_5_losses: int
    last_10_wins: int
    last_10_losses: int
    surface_specific: Optional[Dict[str, Dict[str, int]]] = None  # {'hard': {'wins': 3, 'losses': 1}}


class TennisExplorerScraper:
    """
    TennisExplorer scraper with multiple endpoint support
    
    Features:
    - Selenium for dynamic content
    - BeautifulSoup for parsing
    - Rate limiting and anti-detection
    - Multiple fallback strategies
    """
    
    BASE_URL = "https://www.tennisexplorer.com"
    
    # Endpoints
    LIVE_TENNIS = f"{BASE_URL}/live-tennis/"
    NEXT_MATCHES_WTA = f"{BASE_URL}/next-matches-wta-women/"
    NEXT_MATCHES_ATP = f"{BASE_URL}/next-matches-atp-men/"
    
    def __init__(self, config: dict = None, use_selenium: bool = True):
        """
        Initialize TennisExplorer scraper
        
        Args:
            config: Configuration dictionary
            use_selenium: Whether to use Selenium (recommended)
        """
        self.config = config or {}
        self.use_selenium = use_selenium and SELENIUM_AVAILABLE
        self.driver = None
        self.session = None
        
        # Rate limiting
        self.request_delay = self.config.get('request_delay', 2.0)
        self.last_request_time = 0
        
        # User agent rotation
        try:
            from fake_useragent import UserAgent
            self.ua = UserAgent()
        except ImportError:
            self.ua = None
        
        if self.use_selenium:
            self._init_selenium()
        elif REQUESTS_AVAILABLE:
            self._init_requests()
        
        logger.info(f"🎾 TennisExplorer Scraper initialized (Selenium: {self.use_selenium})")
    
    def _init_selenium(self):
        """Initialize Selenium WebDriver"""
        if not SELENIUM_AVAILABLE:
            return
        
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            user_agent = self.config.get('user_agent')
            if not user_agent and self.ua:
                user_agent = self.ua.random
            if user_agent:
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
    
    def _init_requests(self):
        """Initialize requests session"""
        if not REQUESTS_AVAILABLE:
            return
        
        self.session = requests.Session()
        
        # Set default headers
        headers = {
            'User-Agent': self.config.get('user_agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        self.session.headers.update(headers)
    
    def _rate_limit(self):
        """Apply rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        self.last_request_time = time.time()
    
    def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Get page content with rate limiting
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None
        """
        self._rate_limit()
        
        try:
            if self.use_selenium and self.driver:
                logger.debug(f"🌐 Fetching with Selenium: {url}")
                self.driver.get(url)
                time.sleep(5)  # Wait longer for JS to load
                html = self.driver.page_source
                logger.debug(f"Page loaded, HTML length: {len(html)}")
            elif self.session:
                logger.debug(f"🌐 Fetching with requests: {url}")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                html = response.text
            else:
                logger.error("❌ No method available to fetch page")
                return None
            
            return BeautifulSoup(html, 'html.parser')
            
        except Exception as e:
            logger.error(f"❌ Error fetching {url}: {e}")
            return None
    
    def scrape_live_matches(self) -> List[TennisExplorerMatch]:
        """
        Scrape live matches from /live-tennis/ and today's matches
        
        Returns:
            List of TennisExplorerMatch objects
        """
        logger.info("📊 Scraping live matches from TennisExplorer...")
        
        matches = []
        
        # First try live matches page
        soup_live = self._get_page(self.LIVE_TENNIS)
        if soup_live:
            matches.extend(self._parse_matches_from_page(soup_live, is_live=True))
        
        # Also check today's matches (ATP singles)
        today_url = f"{self.BASE_URL}/matches/?type=atp-single"
        soup_today = self._get_page(today_url)
        if soup_today:
            matches.extend(self._parse_matches_from_page(soup_today, is_live=False))
        
        # Also check WTA
        today_wta_url = f"{self.BASE_URL}/matches/?type=wta-single"
        soup_wta = self._get_page(today_wta_url)
        if soup_wta:
            matches.extend(self._parse_matches_from_page(soup_wta, is_live=False))
        
        logger.info(f"✅ Found {len(matches)} matches total")
        return matches
    
    def _parse_matches_from_page(self, soup, is_live: bool = False) -> List[TennisExplorerMatch]:
        """Parse matches from a page"""
        matches = []
        
        try:
            # Find all match detail links
            match_links = soup.find_all('a', href=lambda x: x and 'match-detail' in str(x).lower())
            logger.info(f"Found {len(match_links)} match detail links on page")
            
            # Group by match ID (each match appears multiple times)
            seen_match_ids = set()
            
            for link in match_links:
                href = link.get('href', '')
                if not href:
                    continue
                
                # Extract match ID from URL: /match-detail/?id=3074806
                match_id = None
                if 'id=' in href:
                    match_id = href.split('id=')[-1].split('&')[0]
                elif '/' in href:
                    match_id = href.split('/')[-1].split('?')[0]
                
                if not match_id or match_id in seen_match_ids:
                    continue
                
                # Find parent TR
                tr_parent = link.find_parent('tr')
                if not tr_parent:
                    continue
                
                # Check if this TR has rowspan="2" (first player row)
                # rowspan can be string "2" or number 2
                rowspan_td = None
                for td in tr_parent.find_all('td'):
                    rowspan_attr = td.get('rowspan')
                    if rowspan_attr and (str(rowspan_attr) == '2' or rowspan_attr == 2):
                        rowspan_td = td
                        break
                has_rowspan = bool(rowspan_td)
                
                player_a = None
                player_b = None
                
                if has_rowspan:
                    # This is the first row - get first player
                    player_links_current = tr_parent.find_all('a', href=lambda x: x and '/player/' in str(x))
                    if player_links_current:
                        player_a = player_links_current[0].get_text(strip=True)
                        logger.debug(f"Match {match_id}: Found player_a={player_a} in rowspan row")
                    
                    # Second player is in next sibling TR
                    next_tr = tr_parent.find_next_sibling('tr')
                    if next_tr:
                        player_links_next = next_tr.find_all('a', href=lambda x: x and '/player/' in str(x))
                        if player_links_next:
                            player_b = player_links_next[0].get_text(strip=True)
                            logger.debug(f"Match {match_id}: Found player_b={player_b} in next row")
                        else:
                            logger.debug(f"Match {match_id}: No player links in next TR")
                    else:
                        logger.debug(f"Match {match_id}: No next sibling TR found")
                else:
                    # This might be second row - check previous sibling
                    prev_tr = tr_parent.find_previous_sibling('tr')
                    if prev_tr and (prev_tr.find('td', rowspan='2') or prev_tr.find('td', attrs={'rowspan': '2'})):
                        # Previous row is first player
                        player_links_prev = prev_tr.find_all('a', href=lambda x: x and '/player/' in str(x))
                        if player_links_prev:
                            player_a = player_links_prev[0].get_text(strip=True)
                        
                        # Current row is second player
                        player_links_current = tr_parent.find_all('a', href=lambda x: x and '/player/' in str(x))
                        if player_links_current:
                            player_b = player_links_current[0].get_text(strip=True)
                
                # If we have both players, create match
                if player_a and player_b and player_a != player_b:
                    # Use the rowspan row as container
                    container = tr_parent if has_rowspan else (prev_tr if 'prev_tr' in locals() and prev_tr else tr_parent)
                    match = self._parse_match_from_container(container, player_a, player_b, match_id, is_live)
                    if match:
                        matches.append(match)
                        seen_match_ids.add(match_id)
                        logger.debug(f"✅ Added match {match_id}: {player_a} vs {player_b}")
                    else:
                        logger.debug(f"⚠️  Failed to create match {match_id}: {player_a} vs {player_b}")
                elif match_id not in seen_match_ids and len(seen_match_ids) < 5:
                    # Debug: log first few failures
                    logger.debug(f"Match {match_id}: player_a={player_a}, player_b={player_b}, has_rowspan={has_rowspan}")
            
            # Fallback: if no matches found via links, try table rows directly
            if not matches:
                logger.debug("Trying fallback: parsing table rows directly")
                rows = soup.find_all('tr')
                for row in rows:
                    player_links = row.find_all('a', href=lambda x: x and '/player/' in str(x))
                    if len(player_links) >= 2:
                        player_a = player_links[0].get_text(strip=True)
                        player_b = player_links[1].get_text(strip=True)
                        
                        # Try to find match ID in this row
                        match_link = row.find('a', href=lambda x: x and 'match-detail' in str(x).lower())
                        if match_link:
                            href = match_link.get('href', '')
                            if 'id=' in href:
                                match_id = href.split('id=')[-1].split('&')[0]
                            else:
                                match_id = f"{player_a}_{player_b}_{hash(row)}"
                        else:
                            match_id = f"{player_a}_{player_b}_{hash(row)}"
                        
                        if player_a and player_b and player_a != player_b:
                            match = self._parse_match_from_container(row, player_a, player_b, match_id, is_live)
                            if match:
                                matches.append(match)
            
            logger.info(f"Parsed {len(matches)} matches from page")
            return matches[:100]  # Limit to 100 matches
            
        except Exception as e:
            logger.error(f"❌ Error parsing matches: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return []
    
    def _parse_match_from_container(self, container, player_a: str, player_b: str, match_id: str, is_live: bool) -> Optional[TennisExplorerMatch]:
        """Parse a match from container with known players"""
        try:
            # Extract tournament
            tournament_elem = container.find('a', href=lambda x: x and '/tournament/' in str(x))
            tournament = tournament_elem.get_text(strip=True) if tournament_elem else "Unknown"
            
            # Extract score (only for live matches)
            score = None
            if is_live:
                score_elem = container.find(['td', 'div', 'span'], class_=lambda x: x and ('score' in str(x).lower() or 'result' in str(x).lower()))
                if not score_elem:
                    # Try to find score in text
                    text = container.get_text()
                    score_match = re.search(r'\d+[-:]\d+', text)
                    if score_match:
                        score = score_match.group()
                else:
                    score = score_elem.get_text(strip=True)
            
            # Extract surface (from tournament or match info)
            surface = "Hard"  # Default
            surface_elem = container.find(string=re.compile(r'(Hard|Clay|Grass|Indoor)', re.I))
            if surface_elem:
                surface = surface_elem.strip()
            
            # Extract tournament tier (default)
            tournament_tier = "Unknown"
            
            # Create match URL
            match_url = f"{self.BASE_URL}/match-detail/?id={match_id}"
            
            return TennisExplorerMatch(
                match_id=match_id,
                player_a=player_a,
                player_b=player_b,
                tournament=tournament,
                tournament_tier=tournament_tier,
                surface=surface,
                current_score=score if is_live else None,
                match_url=match_url
            )
            
        except Exception as e:
            logger.error(f"Error parsing match container: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    def _parse_live_match(self, container) -> Optional[TennisExplorerMatch]:
        """Parse a single live match from container"""
        try:
            # Extract player names
            players = container.find_all(['a', 'span'], class_=lambda x: x and 'player' in str(x).lower())
            if len(players) < 2:
                # Try alternative selectors
                players = container.find_all('a', href=re.compile(r'/player/'))
            
            if len(players) < 2:
                return None
            
            player_a = players[0].get_text(strip=True)
            player_b = players[1].get_text(strip=True)
            
            if not player_a or not player_b:
                return None
            
            # Extract tournament
            tournament_elem = container.find(['a', 'span'], href=re.compile(r'/tournament/'))
            tournament = tournament_elem.get_text(strip=True) if tournament_elem else "Unknown"
            
            # Extract score
            score_elem = container.find(['td', 'div'], class_=lambda x: x and 'score' in str(x).lower())
            score = score_elem.get_text(strip=True) if score_elem else None
            
            # Extract surface (from tournament or match info)
            surface = self._extract_surface(container, tournament)
            
            # Extract tournament tier
            tier = self._extract_tournament_tier(tournament)
            
            # Generate match ID
            match_id = f"te_{hash(f'{player_a}_{player_b}_{tournament}') % 100000}"
            
            # Extract match URL
            match_url_elem = container.find('a', href=re.compile(r'/match-detail/'))
            match_url = f"{self.BASE_URL}{match_url_elem['href']}" if match_url_elem else None
            
            return TennisExplorerMatch(
                match_id=match_id,
                player_a=player_a,
                player_b=player_b,
                tournament=tournament,
                tournament_tier=tier,
                surface=surface,
                current_score=score,
                match_url=match_url,
                scraped_at=datetime.now()
            )
            
        except Exception as e:
            logger.debug(f"⚠️ Error parsing match: {e}")
            return None
    
    def scrape_h2h(self, player_a: str, player_b: str) -> Optional[H2HRecord]:
        """
        Scrape H2H record from /player-vs-player/ endpoint
        
        Args:
            player_a: First player name
            player_b: Second player name
            
        Returns:
            H2HRecord object or None
        """
        logger.info(f"📊 Scraping H2H: {player_a} vs {player_b}")
        
        # TennisExplorer H2H URL format
        # Need to normalize player names for URL
        player_a_slug = self._name_to_slug(player_a)
        player_b_slug = self._name_to_slug(player_b)
        
        url = f"{self.BASE_URL}/player-vs-player/{player_a_slug}/{player_b_slug}/"
        
        soup = self._get_page(url)
        if not soup:
            return None
        
        try:
            # Parse overall H2H
            overall = self._parse_h2h_overall(soup)
            
            # Parse surface-specific H2H
            by_surface = self._parse_h2h_by_surface(soup)
            
            # Parse last meetings
            last_meetings = self._parse_last_meetings(soup)
            
            return H2HRecord(
                player_a=player_a,
                player_b=player_b,
                overall=overall,
                by_surface=by_surface,
                last_meetings=last_meetings
            )
            
        except Exception as e:
            logger.error(f"❌ Error parsing H2H: {e}")
            return None
    
    def _parse_h2h_overall(self, soup: BeautifulSoup) -> Dict[str, int]:
        """Parse overall H2H record"""
        wins_a = 0
        wins_b = 0
        
        # Look for H2H summary table
        h2h_table = soup.find('table', class_=lambda x: x and 'h2h' in str(x).lower())
        if not h2h_table:
            # Try alternative selectors
            h2h_table = soup.find('div', class_=lambda x: x and 'h2h' in str(x).lower())
        
        if h2h_table:
            # Extract win counts
            wins = h2h_table.find_all(['td', 'span'], text=re.compile(r'\d+'))
            if len(wins) >= 2:
                try:
                    wins_a = int(wins[0].get_text(strip=True))
                    wins_b = int(wins[1].get_text(strip=True))
                except ValueError:
                    pass
        
        return {'wins_a': wins_a, 'wins_b': wins_b}
    
    def _parse_h2h_by_surface(self, soup: BeautifulSoup) -> Dict[str, Dict[str, int]]:
        """Parse surface-specific H2H records"""
        by_surface = {}
        
        # Look for surface breakdown
        surface_sections = soup.find_all(['div', 'table'], class_=lambda x: x and 'surface' in str(x).lower())
        
        for section in surface_sections:
            surface_name = None
            # Extract surface name (hard, clay, grass)
            surface_elem = section.find(text=re.compile(r'(hard|clay|grass)', re.I))
            if surface_elem:
                surface_name = surface_elem.strip().lower()
            
            if surface_name:
                wins_a = 0
                wins_b = 0
                
                # Extract wins
                wins = section.find_all(text=re.compile(r'^\d+$'))
                if len(wins) >= 2:
                    try:
                        wins_a = int(wins[0].strip())
                        wins_b = int(wins[1].strip())
                    except ValueError:
                        pass
                
                by_surface[surface_name] = {'wins_a': wins_a, 'wins_b': wins_b}
        
        return by_surface
    
    def _parse_last_meetings(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse last 5 meetings with scores"""
        meetings = []
        
        # Look for recent matches table
        matches_table = soup.find('table', class_=lambda x: x and ('match' in str(x).lower() or 'result' in str(x).lower()))
        
        if matches_table:
            rows = matches_table.find_all('tr')[1:6]  # Skip header, get first 5
            
            for row in rows:
                try:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:
                        date = cells[0].get_text(strip=True)
                        tournament = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                        score = cells[-1].get_text(strip=True)
                        
                        meetings.append({
                            'date': date,
                            'tournament': tournament,
                            'score': score
                        })
                except Exception:
                    continue
        
        return meetings
    
    def scrape_player_form(self, player_name: str, surface: Optional[str] = None) -> Optional[PlayerForm]:
        """
        Scrape recent form from /player/ endpoint
        
        Args:
            player_name: Player name
            surface: Optional surface filter
            
        Returns:
            PlayerForm object or None
        """
        logger.info(f"📊 Scraping form for {player_name}")
        
        player_slug = self._name_to_slug(player_name)
        url = f"{self.BASE_URL}/player/{player_slug}/"
        
        soup = self._get_page(url)
        if not soup:
            return None
        
        try:
            # Parse last 5 and last 10 matches
            last_5_wins, last_5_losses = self._parse_form_period(soup, period=5)
            last_10_wins, last_10_losses = self._parse_form_period(soup, period=10)
            
            # Parse surface-specific form if requested
            surface_specific = None
            if surface:
                surface_specific = self._parse_surface_form(soup, surface)
            
            return PlayerForm(
                player_name=player_name,
                last_5_wins=last_5_wins,
                last_5_losses=last_5_losses,
                last_10_wins=last_10_wins,
                last_10_losses=last_10_losses,
                surface_specific=surface_specific
            )
            
        except Exception as e:
            logger.error(f"❌ Error parsing player form: {e}")
            return None
    
    def _parse_form_period(self, soup: BeautifulSoup, period: int) -> Tuple[int, int]:
        """Parse wins/losses for a specific period"""
        wins = 0
        losses = 0
        
        # Look for recent matches section
        matches_section = soup.find(['div', 'table'], class_=lambda x: x and 'match' in str(x).lower())
        
        if matches_section:
            matches = matches_section.find_all('tr', limit=period + 1)[1:]  # Skip header
            
            for match in matches:
                # Check if win or loss (usually indicated by class or text)
                result_elem = match.find(['td', 'span'], class_=lambda x: x and ('win' in str(x).lower() or 'loss' in str(x).lower()))
                if result_elem:
                    if 'win' in str(result_elem.get('class', [])).lower():
                        wins += 1
                    elif 'loss' in str(result_elem.get('class', [])).lower():
                        losses += 1
        
        return wins, losses
    
    def _parse_surface_form(self, soup: BeautifulSoup, surface: str) -> Optional[Dict[str, Dict[str, int]]]:
        """Parse surface-specific form"""
        # This would need to filter matches by surface
        # Implementation depends on TennisExplorer structure
        return None
    
    def scrape_odds_comparison(self, match_id: str, match_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Scrape odds comparison from /odds-comparison/ endpoint
        
        Args:
            match_id: Match ID
            match_url: Optional match URL (if available)
            
        Returns:
            Dictionary with odds from multiple bookmakers
        """
        if not match_url:
            logger.warning(f"⚠️ No match URL provided for odds comparison: {match_id}")
            return {}
        
        # Extract match ID from URL if needed
        if '/match-detail/' in match_url:
            odds_url = match_url.replace('/match-detail/', '/odds-comparison/')
        else:
            odds_url = f"{self.BASE_URL}/odds-comparison/?id={match_id}"
        
        logger.info(f"📊 Scraping odds comparison: {odds_url}")
        
        soup = self._get_page(odds_url)
        if not soup:
            return {}
        
        try:
            odds_data = {}
            
            # Look for odds table
            odds_table = soup.find('table', class_=lambda x: x and 'odds' in str(x).lower())
            
            if odds_table:
                rows = odds_table.find_all('tr')[1:]  # Skip header
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:
                        bookmaker = cells[0].get_text(strip=True)
                        odds_a = self._parse_odds(cells[1].get_text(strip=True))
                        odds_b = self._parse_odds(cells[2].get_text(strip=True))
                        
                        if bookmaker and odds_a and odds_b:
                            odds_data[bookmaker] = {
                                'odds_a': odds_a,
                                'odds_b': odds_b
                            }
            
            return odds_data
            
        except Exception as e:
            logger.error(f"❌ Error parsing odds: {e}")
            return {}
    
    def _parse_odds(self, odds_str: str) -> Optional[float]:
        """Parse odds string to float"""
        try:
            # Remove any non-numeric characters except decimal point
            odds_str = re.sub(r'[^\d.]', '', odds_str)
            return float(odds_str) if odds_str else None
        except ValueError:
            return None
    
    def scrape_tournament_history(self, player_name: str, tournament: str) -> List[Dict]:
        """
        Scrape tournament history for a player at a specific venue
        
        Args:
            player_name: Player name
            tournament: Tournament name
            
        Returns:
            List of previous year results
        """
        logger.info(f"📊 Scraping tournament history: {player_name} at {tournament}")
        
        player_slug = self._name_to_slug(player_name)
        url = f"{self.BASE_URL}/player/{player_slug}/"
        
        soup = self._get_page(url)
        if not soup:
            return []
        
        try:
            history = []
            
            # Look for tournament results in player profile
            # Filter by tournament name
            matches = soup.find_all(['tr', 'div'], class_=lambda x: x and 'match' in str(x).lower())
            
            for match in matches:
                tournament_elem = match.find(text=re.compile(tournament, re.I))
                if tournament_elem:
                    # Extract year and result
                    year_elem = match.find(text=re.compile(r'20\d{2}'))
                    result_elem = match.find(['td', 'span'], class_=lambda x: x and 'result' in str(x).lower())
                    
                    if year_elem and result_elem:
                        history.append({
                            'year': year_elem.strip(),
                            'result': result_elem.get_text(strip=True),
                            'tournament': tournament
                        })
            
            return history
            
        except Exception as e:
            logger.error(f"❌ Error parsing tournament history: {e}")
            return []
    
    def _name_to_slug(self, name: str) -> str:
        """Convert player name to URL slug"""
        # TennisExplorer uses lowercase, hyphens
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        return slug
    
    def _extract_surface(self, container, tournament: str) -> str:
        """Extract surface from container or tournament name"""
        text = (tournament + " " + container.get_text()).lower()
        
        if 'hard' in text or 'hardcourt' in text:
            return 'Hard'
        elif 'clay' in text:
            return 'Clay'
        elif 'grass' in text:
            return 'Grass'
        
        return 'Hard'  # Default
    
    def _extract_tournament_tier(self, tournament: str) -> str:
        """Extract tournament tier from tournament name"""
        tournament_upper = tournament.upper()
        
        # ITF Women
        if 'W15' in tournament_upper:
            return 'W15'
        elif 'W25' in tournament_upper:
            return 'W25'
        elif 'W35' in tournament_upper:
            return 'W35'
        elif 'W50' in tournament_upper:
            return 'W50'
        elif 'W75' in tournament_upper:
            return 'W75'
        elif 'W100' in tournament_upper:
            return 'W100'
        
        # ITF Men
        if 'M15' in tournament_upper:
            return 'M15'
        elif 'M25' in tournament_upper:
            return 'M25'
        elif 'M35' in tournament_upper:
            return 'M35'
        
        # Challenger
        if 'CHALLENGER' in tournament_upper:
            return 'Challenger'
        
        return 'Unknown'
    
    def __del__(self):
        """Cleanup"""
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
        'request_delay': 2.0,
    }
    
    scraper = TennisExplorerScraper(config, use_selenium=True)
    
    try:
        # Test live matches
        matches = scraper.scrape_live_matches()
        print(f"\n📊 Live Matches: {len(matches)}")
        
        if matches:
            for match in matches[:5]:
                print(f"\n🎾 {match.tournament}")
                print(f"   {match.player_a} vs {match.player_b}")
                print(f"   Surface: {match.surface} | Score: {match.current_score}")
        
        # Test H2H (example)
        # h2h = scraper.scrape_h2h("Player A", "Player B")
        # if h2h:
        #     print(f"\n📊 H2H: {h2h.overall}")
    
    finally:
        del scraper

