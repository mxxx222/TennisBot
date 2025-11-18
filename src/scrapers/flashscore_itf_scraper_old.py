#!/usr/bin/env python3
"""
🎾 FLASHSCORE ITF WOMEN SCRAPER
================================

Enhanced FlashScore scraper specifically for ITF Women's Singles tournaments.
Targets W15, W35, W50 tournaments (prioritizes W15/W35 for volatility).

Features:
- Scrapes tournament data: name, tier (W15/W35/W50), surface, players, live score, match status, round
- Uses Selenium for dynamic content (FlashScore uses JavaScript)
- Rate limiting (10-minute intervals)
- User-agent rotation to avoid blocking
- Error handling and retry logic
"""

import asyncio
import aiohttp
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from bs4 import BeautifulSoup
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Try to import Selenium for dynamic content
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

# User agent rotation
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

logger = logging.getLogger(__name__)

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

class FlashScoreITFScraper:
    """FlashScore scraper for ITF Women tournaments"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize FlashScore ITF scraper
        
        Args:
            config: Configuration dict with rate_limit, target_tournaments, etc.
        """
        self.config = config or {}
        self.base_url = "https://www.flashscore.com"
        self.session = None
        
        # Target tournaments (prioritize W15/W35 for volatility)
        self.target_tournaments = self.config.get('target_tournaments', ['W15', 'W35', 'W50'])
        self.rate_limit = self.config.get('rate_limit', 2.5)  # seconds between requests
        
        # User agent rotation
        self.current_user_agent_index = 0
        
        # Match tracking
        self.scraped_matches: Dict[str, ITFMatch] = {}
        self.last_scrape_time: Optional[datetime] = None
        
        # Performance metrics
        self.scrapes_count = 0
        self.errors_count = 0
        
        logger.info(f"🎾 FlashScore ITF Scraper initialized (target: {self.target_tournaments})")
    
    def _get_user_agent(self) -> str:
        """Get next user agent in rotation"""
        agent = USER_AGENTS[self.current_user_agent_index]
        self.current_user_agent_index = (self.current_user_agent_index + 1) % len(USER_AGENTS)
        return agent
    
    async def __aenter__(self):
        """Async context manager entry"""
        headers = {
            'User-Agent': self._get_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers=headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def detect_tournament_tier(self, tournament_name: str) -> Optional[str]:
        """
        Identify tournament tier (W15/W35/W50/W75/W100)
        
        Args:
            tournament_name: Tournament name from FlashScore
            
        Returns:
            Tournament tier or None if not ITF Women
        """
        tournament_upper = tournament_name.upper()
        
        # EXCLUDE Men tournaments explicitly
        if re.search(r'\bM\d+\b', tournament_upper) or ' MEN' in tournament_upper:
            return None
        
        # Check for W15, W25, W35, W50, W60, W75, W80, W100 patterns
        tier_patterns = {
            'W15': r'\bW15\b',
            'W25': r'\bW25\b',
            'W35': r'\bW35\b',
            'W50': r'\bW50\b',
            'W60': r'\bW60\b',
            'W75': r'\bW75\b',
            'W80': r'\bW80\b',
            'W100': r'\bW100\b',
        }
        
        for tier, pattern in tier_patterns.items():
            if re.search(pattern, tournament_upper):
                return tier
        
        # Check for "ITF W" patterns
        itf_w_pattern = re.search(r'ITF\s+W(\d+)', tournament_upper)
        if itf_w_pattern:
            tier_num = itf_w_pattern.group(1)
            return f"W{tier_num}"
        
        # Check for "WOMEN" keyword with ITF
        if 'WOMEN' in tournament_upper and 'ITF' in tournament_upper:
            # Try to extract tier from context
            tier_match = re.search(r'(\d+)', tournament_upper)
            if tier_match:
                tier_num = tier_match.group(1)
                return f"W{tier_num}"
        
        return None
    
    def is_itf_women_tournament(self, tournament_name: str) -> bool:
        """Check if tournament is ITF Women"""
        tier = self.detect_tournament_tier(tournament_name)
        return tier is not None and tier in self.target_tournaments
    
    async def scrape_itf_tournaments(self) -> List[Dict[str, Any]]:
        """
        Get active ITF Women tournaments
        
        Returns:
            List of tournament dictionaries with id, name, tier, surface, etc.
        """
        tournaments = []
        
        try:
            url = f"{self.base_url}/tennis/"
            logger.info(f"🔍 Fetching ITF tournaments from: {url}")
            
            # Try Selenium first for dynamic content
            html = None
            if SELENIUM_AVAILABLE:
                try:
                    html = await self._fetch_with_selenium(url)
                except Exception as e:
                    logger.warning(f"⚠️ Selenium fetch failed: {e}, falling back to HTTP")
            
            # Fallback to HTTP request
            if not html and self.session:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                    else:
                        logger.warning(f"⚠️ Status {response.status} for {url}")
                        return []
            
            if not html:
                logger.error("❌ Could not fetch FlashScore page")
                return []
            
            # Parse tournaments from HTML
            tournaments = await self._parse_tournaments(html)
            
            # Filter to target tournaments
            filtered = [t for t in tournaments if t.get('tier') in self.target_tournaments]
            
            logger.info(f"✅ Found {len(filtered)} target ITF tournaments ({self.target_tournaments})")
            return filtered
            
        except Exception as e:
            logger.error(f"❌ Error scraping ITF tournaments: {e}")
            self.errors_count += 1
            import traceback
            traceback.print_exc()
            return []
    
    async def _fetch_with_selenium(self, url: str) -> Optional[str]:
        """Fetch page with Selenium for dynamic content"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument(f'user-agent={self._get_user_agent()}')
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)
            
            # Wait for content to load
            await asyncio.sleep(3)
            
            # Try to wait for match elements
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "event__match"))
                )
            except TimeoutException:
                logger.info("⏳ Waiting for FlashScore content to load...")
                await asyncio.sleep(2)
            
            html = driver.page_source
            driver.quit()
            
            logger.info("✅ Fetched FlashScore page with Selenium")
            return html
            
        except Exception as e:
            logger.error(f"❌ Selenium error: {e}")
            return None
    
    async def _parse_tournaments(self, html: str) -> List[Dict[str, Any]]:
        """Parse tournament data from HTML"""
        tournaments = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find tournament sections
            # FlashScore uses various class names for tournaments
            tournament_selectors = [
                {'class': re.compile(r'tournament|league|event', re.I)},
                {'class': re.compile(r'event__header', re.I)},
            ]
            
            found_tournaments = set()
            
            # Search for ITF patterns in text
            all_text = soup.get_text(separator='\n', strip=True)
            itf_pattern = re.compile(r'(ITF\s+W\d+\s+[^\n]+|ITF\s+[^\n]+Women)', re.I)
            itf_matches = itf_pattern.findall(all_text)
            
            for match_text in itf_matches:
                tier = self.detect_tournament_tier(match_text)
                if tier and tier in self.target_tournaments:
                    # Extract tournament name
                    tournament_name = match_text.strip()
                    
                    # Try to extract surface and location
                    surface = self._extract_surface(tournament_name)
                    location = self._extract_location(tournament_name)
                    
                    tournament_id = f"itf_{tier.lower()}_{location.lower().replace(' ', '_')}" if location else f"itf_{tier.lower()}_{hash(tournament_name) % 10000}"
                    
                    if tournament_id not in found_tournaments:
                        tournaments.append({
                            'tournament_id': tournament_id,
                            'name': tournament_name,
                            'tier': tier,
                            'surface': surface,
                            'location': location,
                            'status': 'active',
                        })
                        found_tournaments.add(tournament_id)
            
            # Also search in HTML elements
            tournament_elements = soup.find_all(['div', 'span', 'a', 'td', 'th'], 
                string=re.compile(r'ITF|W15|W25|W35|W50|W60|W75|W80|W100', re.I))
            
            for element in tournament_elements[:100]:  # Limit search
                text = element.get_text(strip=True)
                tier = self.detect_tournament_tier(text)
                
                if tier and tier in self.target_tournaments:
                    surface = self._extract_surface(text)
                    location = self._extract_location(text)
                    tournament_id = f"itf_{tier.lower()}_{location.lower().replace(' ', '_')}" if location else f"itf_{tier.lower()}_{hash(text) % 10000}"
                    
                    if tournament_id not in found_tournaments:
                        tournaments.append({
                            'tournament_id': tournament_id,
                            'name': text,
                            'tier': tier,
                            'surface': surface,
                            'location': location,
                            'status': 'active',
                        })
                        found_tournaments.add(tournament_id)
            
            logger.info(f"📊 Parsed {len(tournaments)} ITF tournaments from HTML")
            return tournaments
            
        except Exception as e:
            logger.error(f"❌ Error parsing tournaments: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_surface(self, text: str) -> Optional[str]:
        """Extract surface type from tournament text"""
        text_upper = text.upper()
        if 'HARD' in text_upper or 'HARDCOURT' in text_upper:
            return 'Hard'
        elif 'CLAY' in text_upper:
            return 'Clay'
        elif 'GRASS' in text_upper:
            return 'Grass'
        return None
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location from tournament text"""
        # Common ITF locations
        locations = [
            'ANTALYA', 'CAIRO', 'MONASTIR', 'SHARM', 'HERAKLION',
            'TUNISIA', 'KAZAKHSTAN', 'EGYPT', 'TURKEY', 'GREECE',
            'PHAN THIET', 'LOUSADA', 'ALCALA', 'HUA HIN', 'SHARM EL SHEIKH'
        ]
        
        text_upper = text.upper()
        for location in locations:
            if location in text_upper:
                return location.title()
        
        return None
    
    async def scrape_tournament_matches(self, tournament_id: str, tournament_name: str) -> List[ITFMatch]:
        """
        Get matches for specific tournament
        
        Args:
            tournament_id: Tournament identifier
            tournament_name: Tournament name
            
        Returns:
            List of ITFMatch objects
        """
        matches = []
        
        try:
            # FlashScore tournament URL pattern (approximate)
            # In production, would need to find actual tournament URLs
            url = f"{self.base_url}/tennis/"
            
            logger.info(f"🔍 Fetching matches for tournament: {tournament_name}")
            
            # Fetch page
            html = None
            if SELENIUM_AVAILABLE:
                try:
                    html = await self._fetch_with_selenium(url)
                except Exception as e:
                    logger.warning(f"⚠️ Selenium fetch failed: {e}")
            
            if not html and self.session:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
            
            if not html:
                logger.warning(f"⚠️ Could not fetch matches for {tournament_name}")
                return []
            
            # Parse matches
            matches = await self._parse_match_data(html, tournament_id, tournament_name)
            
            logger.info(f"✅ Found {len(matches)} matches for {tournament_name}")
            return matches
            
        except Exception as e:
            logger.error(f"❌ Error scraping matches for {tournament_id}: {e}")
            self.errors_count += 1
            return []
    
    async def _parse_match_data(self, html: str, tournament_id: str, tournament_name: str) -> List[ITFMatch]:
        """Extract match data from HTML"""
        matches = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find match elements
            # FlashScore uses event__match class
            match_containers = soup.find_all(['div', 'tr', 'li'], 
                class_=re.compile(r'event__match|match', re.I))
            
            tier = self.detect_tournament_tier(tournament_name)
            surface = self._extract_surface(tournament_name)
            
            for container in match_containers[:50]:  # Limit to first 50
                match_data = self._extract_match_from_container(container, tournament_id, tournament_name, tier, surface)
                if match_data:
                    matches.append(match_data)
            
            logger.info(f"📊 Parsed {len(matches)} matches from HTML")
            return matches
            
        except Exception as e:
            logger.error(f"❌ Error parsing match data: {e}")
            return []
    
    def _extract_match_from_container(self, container, tournament_id: str, tournament_name: str, tier: Optional[str], surface: Optional[str]) -> Optional[ITFMatch]:
        """Extract match data from container element"""
        try:
            text = container.get_text(separator=' ', strip=True)
            
            # Extract player names - pattern: "Player1 vs Player2" or "Player1 - Player2"
            player_patterns = [
                re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+(?:vs|v|–|-)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', re.I),
                re.compile(r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:vs|v|–|-)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)', re.I),
            ]
            
            player1 = None
            player2 = None
            
            for pattern in player_patterns:
                match = pattern.search(text)
                if match:
                    p1 = match.group(1).strip()
                    p2 = match.group(2).strip()
                    if (len(p1) > 3 and len(p2) > 3 and p1 != p2 and
                        not any(x in p1.lower() for x in ['check', 'flashscore', 'for', 'matches']) and
                        not any(x in p2.lower() for x in ['check', 'flashscore', 'for', 'matches'])):
                        player1 = p1
                        player2 = p2
                        break
            
            if not player1 or not player2:
                return None
            
            # Extract round
            round_match = re.search(r'\b(R\d+|QF|SF|F|FINAL)\b', text, re.I)
            round_str = round_match.group(1) if round_match else None
            
            # Extract match status
            status = 'not_started'
            if 'LIVE' in text.upper() or 'IN PROGRESS' in text.upper():
                status = 'live'
            elif 'FINISHED' in text.upper() or 'COMPLETED' in text.upper():
                status = 'finished'
            
            # Extract live score
            live_score = None
            set1_score = None
            if status == 'live' or status == 'finished':
                # Pattern: "6-4, 3-2" or "6-4"
                score_pattern = re.search(r'(\d+-\d+(?:\s*,\s*\d+-\d+)*)', text)
                if score_pattern:
                    live_score = score_pattern.group(1)
                    # Extract first set
                    set1_match = re.search(r'(\d+-\d+)', live_score)
                    if set1_match:
                        set1_score = set1_match.group(1)
            
            # Generate match ID
            match_id = f"{tournament_id}_{player1}_{player2}_{hash(text) % 10000}"
            
            return ITFMatch(
                match_id=match_id,
                tournament=tournament_name,
                tournament_tier=tier or 'Unknown',
                surface=surface,
                player1=player1,
                player2=player2,
                round=round_str,
                match_status=status,
                live_score=live_score,
                set1_score=set1_score,
                scheduled_time=None,  # Would need more parsing for this
                match_url=None,
                scraped_at=datetime.now()
            )
            
        except Exception as e:
            logger.debug(f"Error extracting match: {e}")
            return None
    
    async def run_scrape(self) -> Dict[str, Any]:
        """
        Run complete scrape cycle
        
        Returns:
            Dictionary with tournaments and matches
        """
        logger.info("🚀 Starting FlashScore ITF scrape cycle...")
        
        start_time = datetime.now()
        
        # Rate limiting
        if self.last_scrape_time:
            time_since_last = (start_time - self.last_scrape_time).total_seconds()
            if time_since_last < self.rate_limit:
                wait_time = self.rate_limit - time_since_last
                logger.info(f"⏳ Rate limiting: waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
        
        try:
            # Step 1: Get tournaments
            tournaments = await self.scrape_itf_tournaments()
            
            # Step 2: Get matches for each tournament
            all_matches = []
            for tournament in tournaments:
                tournament_matches = await self.scrape_tournament_matches(
                    tournament['tournament_id'],
                    tournament['name']
                )
                all_matches.extend(tournament_matches)
                
                # Rate limiting between tournaments
                await asyncio.sleep(self.rate_limit)
            
            # Update tracking
            for match in all_matches:
                self.scraped_matches[match.match_id] = match
            
            self.last_scrape_time = datetime.now()
            self.scrapes_count += 1
            
            result = {
                'success': True,
                'timestamp': self.last_scrape_time.isoformat(),
                'tournaments_found': len(tournaments),
                'matches_found': len(all_matches),
                'tournaments': tournaments,
                'matches': [self._match_to_dict(m) for m in all_matches],
            }
            
            logger.info(f"✅ Scrape completed: {len(tournaments)} tournaments, {len(all_matches)} matches")
            return result
            
        except Exception as e:
            logger.error(f"❌ Scrape cycle failed: {e}")
            self.errors_count += 1
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
            }
    
    def _match_to_dict(self, match: ITFMatch) -> Dict[str, Any]:
        """Convert ITFMatch to dictionary"""
        return {
            'match_id': match.match_id,
            'tournament': match.tournament,
            'tournament_tier': match.tournament_tier,
            'surface': match.surface,
            'player1': match.player1,
            'player2': match.player2,
            'round': match.round,
            'match_status': match.match_status,
            'live_score': match.live_score,
            'set1_score': match.set1_score,
            'scheduled_time': match.scheduled_time.isoformat() if match.scheduled_time else None,
            'scraped_at': match.scraped_at.isoformat(),
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            'scrapes_count': self.scrapes_count,
            'errors_count': self.errors_count,
            'tracked_matches': len(self.scraped_matches),
            'last_scrape_time': self.last_scrape_time.isoformat() if self.last_scrape_time else None,
            'success_rate': (self.scrapes_count / (self.scrapes_count + self.errors_count) * 100) if (self.scrapes_count + self.errors_count) > 0 else 0,
        }


async def main():
    """Test FlashScore ITF scraper"""
    print("🎾 FLASHSCORE ITF SCRAPER TEST")
    print("=" * 50)
    
    config = {
        'target_tournaments': ['W15', 'W35', 'W50'],
        'rate_limit': 2.5,
    }
    
    async with FlashScoreITFScraper(config) as scraper:
        result = await scraper.run_scrape()
        
        if result['success']:
            print(f"\n✅ Scrape successful!")
            print(f"   Tournaments: {result['tournaments_found']}")
            print(f"   Matches: {result['matches_found']}")
            
            if result['matches']:
                print("\n📊 Sample matches:")
                for match in result['matches'][:5]:
                    print(f"   {match['player1']} vs {match['player2']} ({match['tournament']})")
        else:
            print(f"\n❌ Scrape failed: {result.get('error')}")
        
        stats = scraper.get_performance_stats()
        print(f"\n📈 Performance Stats:")
        print(f"   Scrapes: {stats['scrapes_count']}")
        print(f"   Errors: {stats['errors_count']}")
        print(f"   Success Rate: {stats['success_rate']:.1f}%")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())

