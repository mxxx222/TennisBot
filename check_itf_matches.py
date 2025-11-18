#!/usr/bin/env python3
"""
🎾 ITF WOMEN MATCH CHECKER
==========================
Tarkistaa FlashScore:sta ITF Women -ottelut ja suodattaa ne validoitujen kriteerien mukaan.

Kriteerit (VALIDATED +17.81% ROI):
- ITF W15, W25, W60, W80, W100 turnaukset
- Odds range: 1.51-2.00 (tarkistetaan manuaalisesti Bet365:llä)
- Pelaajat rankingilla 100-800 (tarkistetaan manuaalisesti)
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, quote
import sys
from pathlib import Path

# Add src to path for importing scrapers
sys.path.insert(0, str(Path(__file__).parent / 'src'))

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
    logger.warning("⚠️ Selenium not available - using basic HTML parsing only")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ITFMatchChecker:
    """ITF Women -ottelujen tarkistaja"""
    
    def __init__(self):
        self.base_url = "https://www.flashscore.com"
        self.session = None
        
        # ITF Women tournament patterns
        self.itf_patterns = [
            r'ITF W15',
            r'ITF W25',
            r'ITF W60',
            r'ITF W80',
            r'ITF W100',
            r'ITF.*Women',
            r'W15',
            r'W25',
            r'W60',
            r'W80',
            r'W100'
        ]
        
        # Target date range (today + next 3 days)
        self.target_dates = [
            datetime.now().date(),
            (datetime.now() + timedelta(days=1)).date(),
            (datetime.now() + timedelta(days=2)).date(),
            (datetime.now() + timedelta(days=3)).date()
        ]
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def fetch_tennis_page(self) -> Optional[str]:
        """Hae FlashScore tennis-sivu - käytä Seleniumia jos saatavilla"""
        try:
            url = f"{self.base_url}/tennis/"
            logger.info(f"🔍 Fetching: {url}")
            
            # Try Selenium first for dynamic content
            if SELENIUM_AVAILABLE:
                try:
                    return await self._fetch_with_selenium(url)
                except Exception as e:
                    logger.warning(f"⚠️ Selenium fetch failed: {e}, falling back to requests")
            
            # Fallback to regular HTTP request
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"⚠️ Status {response.status} for {url}")
                    return None
        except Exception as e:
            logger.error(f"❌ Error fetching tennis page: {e}")
            return None
    
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
    
    def is_itf_women_tournament(self, tournament_name: str) -> bool:
        """Tarkista onko turnaus ITF Women"""
        tournament_upper = tournament_name.upper()
        
        # EXCLUDE Men tournaments explicitly
        if re.search(r'\bM\d+\b', tournament_upper) or ' MEN' in tournament_upper or tournament_upper.endswith(' MEN'):
            return False
        
        # Check for ITF Women patterns (W15, W25, W60, W80, W100)
        # Priority: Direct W pattern matches
        if re.search(r'\bW\d+\b', tournament_upper):
            return True
        
        # Check for "ITF W" patterns
        if re.search(r'ITF\s+W\d+', tournament_upper):
            return True
        
        # Check for "WOMEN" keyword
        if 'WOMEN' in tournament_upper and 'ITF' in tournament_upper:
            return True
        
        # Check for common ITF Women locations (only if ITF present and not Men)
        itf_locations = [
            'ANTALYA', 'CAIRO', 'MONASTIR', 'SHARM', 'HERAKLION',
            'TUNISIA', 'KAZAKHSTAN', 'EGYPT', 'TURKEY', 'GREECE',
            'PHAN THIET', 'LOUSADA', 'ALCALA', 'HUA HIN'
        ]
        
        # If tournament name contains ITF and location, likely ITF Women
        if 'ITF' in tournament_upper and 'MEN' not in tournament_upper:
            for location in itf_locations:
                if location in tournament_upper:
                    return True
        
        return False
    
    async def parse_tennis_matches(self, html: str) -> List[Dict]:
        """Parse tennis matches from HTML - Enhanced with better scraping"""
        matches = []

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # FlashScore uses JavaScript for dynamic content
            # Try to find tournament names and extract from text
            all_text = soup.get_text(separator='\n', strip=True)

            # Look for ITF patterns in text
            itf_pattern = re.compile(r'(ITF\s+W\d+|ITF\s+Women|W15|W25|W60|W80|W100)', re.I)
            itf_matches_text = itf_pattern.findall(all_text)

            logger.info(f"📊 Found {len(itf_matches_text)} ITF mentions in text")

            # Try to find tournament sections
            tournament_sections = soup.find_all(['div', 'span', 'a', 'td', 'th'], 
                string=re.compile(r'ITF|W15|W25|W60|W80|W100', re.I))
            
            logger.info(f"📊 Found {len(tournament_sections)} tournament elements")
            
            # Try to find actual match elements with player names
            # FlashScore match structure: event__match, event__participant
            match_containers = soup.find_all(['div', 'tr', 'li'], 
                class_=re.compile(r'event__match|match|participant', re.I))
            
            logger.info(f"📊 Found {len(match_containers)} potential match containers")
            
            # Try to extract matches from containers
            for container in match_containers[:50]:  # Limit to first 50
                match_data = self._extract_match_from_container(container)
                if match_data:
                    matches.append(match_data)
            
            # Extract tournament names
            found_tournaments = set()
            for section in tournament_sections[:50]:
                text = section.get_text(strip=True)
                # Check if it's ITF Women (not Men)
                if 'ITF' in text.upper() and 'WOMEN' in text.upper():
                    found_tournaments.add(text)
                elif re.search(r'ITF\s+W\d+', text, re.I) and not re.search(r'\bM\d+\b', text.upper()):
                    found_tournaments.add(text)
                elif self.is_itf_women_tournament(text):
                    found_tournaments.add(text)
                
                # Try to find nearby player names
                parent = section.find_parent(['div', 'tr', 'table', 'li'])
                if parent:
                    parent_text = parent.get_text(separator=' ', strip=True)
                    # Look for player patterns
                    player_pattern = re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+(?:vs|v|–|-)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', re.I)
                    player_match = player_pattern.search(parent_text)
                    if player_match and self.is_itf_women_tournament(text):
                        matches.append({
                            'player1': player_match.group(1),
                            'player2': player_match.group(2),
                            'tournament': text,
                            'time': 'TBD',
                            'source': 'FlashScore'
                        })
            
            # If we found tournaments but no matches, create placeholder entries
            if found_tournaments and not matches:
                # Filter to only Women tournaments
                women_tournaments = [t for t in found_tournaments if self.is_itf_women_tournament(t)]
                for tournament in women_tournaments[:10]:
                    matches.append({
                        'player1': 'Check FlashScore',
                        'player2': 'for matches',
                        'tournament': tournament,
                        'time': 'TBD',
                        'source': 'FlashScore (tournament found, check manually)'
                    })
            
            # Remove duplicates
            unique_matches = []
            seen = set()
            for match in matches:
                key = (match.get('player1', ''), match.get('player2', ''), match.get('tournament', ''))
                if key not in seen and match.get('player1') != 'Check FlashScore':
                    seen.add(key)
                    unique_matches.append(match)

            logger.info(f"✅ Parsed {len(unique_matches)} unique matches")
            return unique_matches

        except Exception as e:
            logger.error(f"❌ Error parsing matches: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_match_from_container(self, container) -> Optional[Dict]:
        """Extract match data from container element - Enhanced parsing"""
        try:
            # Get all text from container
            container_text = container.get_text(separator=' ', strip=True)
            
            # Skip if too short or doesn't look like a match
            if len(container_text) < 10:
                return None
            
            # Pattern 1: FlashScore format - look for participant names
            # Try multiple class patterns
            player_selectors = [
                (By.CLASS_NAME, "participant__participantName"),
                (By.CLASS_NAME, "event__participant"),
                (By.CLASS_NAME, "participant"),
                (By.CSS_SELECTOR, "[class*='participant']"),
                (By.CSS_SELECTOR, "[class*='player']"),
            ]
            
            player1 = None
            player2 = None
            
            # Try to find player names using BeautifulSoup
            player_elements = container.find_all(['span', 'div', 'a', 'td'], 
                class_=re.compile(r'participant|player|name', re.I))
            
            # Also try text-based extraction
            text = container.get_text(separator=' ', strip=True)
            
            # Pattern: "Player1 vs Player2" or "Player1 - Player2"
            vs_patterns = [
                re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+(?:vs|v|–|-)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', re.I),
                re.compile(r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:vs|v|–|-)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)', re.I),
            ]
            
            for pattern in vs_patterns:
                match = pattern.search(text)
                if match:
                    p1 = match.group(1).strip()
                    p2 = match.group(2).strip()
                    if (len(p1) > 3 and len(p2) > 3 and 
                        p1 != p2 and
                        not any(x in p1.lower() for x in ['check', 'flashscore', 'for', 'matches', 'vs', 'v']) and
                        not any(x in p2.lower() for x in ['check', 'flashscore', 'for', 'matches', 'vs', 'v'])):
                        player1 = p1
                        player2 = p2
                        break
            
            # If found via elements
            if not player1 and len(player_elements) >= 2:
                p1 = player_elements[0].get_text(strip=True)
                p2 = player_elements[1].get_text(strip=True)
                if (len(p1) > 3 and len(p2) > 3 and p1 != p2):
                    player1 = p1
                    player2 = p2
            
            if not player1 or not player2:
                return None
            
            # Find tournament name
            tournament = self._find_tournament_nearby(container)
            if not tournament:
                # Try to find in container text
                itf_match = re.search(r'(ITF\s+W\d+\s+[^,\.]+|ITF\s+[^,\.]+Women)', text, re.I)
                if itf_match:
                    tournament = itf_match.group(1).strip()
            
            # Only return if it's ITF Women
            if tournament and not self.is_itf_women_tournament(tournament):
                return None
            
            # Find time
            time_str = "TBD"
            time_elements = container.find_all(['span', 'div'], 
                class_=re.compile(r'time|date|start|clock', re.I))
            
            if time_elements:
                time_text = time_elements[0].get_text(strip=True)
                if time_text and len(time_text) < 20:  # Valid time format
                    time_str = time_text
            
            return {
                'player1': player1,
                'player2': player2,
                'tournament': tournament or 'ITF Women',
                'time': time_str,
                'source': 'FlashScore'
            }
            
        except Exception as e:
            logger.debug(f"Error extracting match: {e}")
            return None
    
    def _find_tournament_nearby(self, element) -> Optional[str]:
        """Find tournament name near element"""
        try:
            # Check parent elements
            for parent in [element] + list(element.parents)[:5]:
                text = parent.get_text(separator=' ', strip=True)
                
                # Look for ITF Women patterns
                itf_match = re.search(r'(ITF\s+W\d+\s+[^,]+|ITF\s+[^,]+Women)', text, re.I)
                if itf_match:
                    tournament = itf_match.group(1).strip()
                    if self.is_itf_women_tournament(tournament):
                        return tournament
            
            return None
        except:
            return None
    
    def _extract_match_from_element(self, element) -> Optional[Dict]:
        """Extract match information from HTML element"""
        try:
            # Try to find player names
            player_elements = element.find_all(['span', 'div', 'a'], 
                class_=re.compile(r'participant|player|name', re.I))
            
            if not player_elements:
                # Try text-based extraction
                text = element.get_text(separator=' ', strip=True)
                # Look for patterns like "Player1 vs Player2" or "Player1 - Player2"
                match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:vs|v|–|-)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text)
                if match:
                    player1 = match.group(1).strip()
                    player2 = match.group(2).strip()
                else:
                    return None
            else:
                if len(player_elements) >= 2:
                    player1 = player_elements[0].get_text(strip=True)
                    player2 = player_elements[1].get_text(strip=True)
                else:
                    return None
            
            # Try to find tournament name
            tournament = "Unknown Tournament"
            tournament_elements = element.find_all(['span', 'div', 'a'], 
                class_=re.compile(r'tournament|league|event', re.I))
            
            if tournament_elements:
                tournament = tournament_elements[0].get_text(strip=True)
            else:
                # Look in parent elements
                parent = element.find_parent(['div', 'tr'])
                if parent:
                    tournament_text = parent.get_text(separator=' ', strip=True)
                    # Look for ITF patterns
                    itf_match = re.search(r'(ITF\s+[W\d]+[^a-z]*)', tournament_text, re.I)
                    if itf_match:
                        tournament = itf_match.group(1).strip()
            
            # Try to find time
            time_str = "TBD"
            time_elements = element.find_all(['span', 'div'], 
                class_=re.compile(r'time|date|start', re.I))
            
            if time_elements:
                time_str = time_elements[0].get_text(strip=True)
            
            return {
                'player1': player1,
                'player2': player2,
                'tournament': tournament,
                'time': time_str,
                'source': 'FlashScore'
            }
            
        except Exception as e:
            logger.debug(f"Error extracting match: {e}")
            return None
    
    def filter_itf_women_matches(self, matches: List[Dict]) -> List[Dict]:
        """Suodata ITF Women -ottelut"""
        filtered = []
        
        for match in matches:
            tournament = match.get('tournament', '')
            player1 = match.get('player1', '')
            player2 = match.get('player2', '')
            
            # Check tournament name
            if self.is_itf_women_tournament(tournament):
                # Additional check: exclude obvious men's matches
                # (This is a heuristic - in production would check actual gender data)
                if not any(x in player1.lower() for x in ['m.', 'men', 'atp']) and \
                   not any(x in player2.lower() for x in ['m.', 'men', 'atp']):
                    filtered.append(match)
        
        return filtered
    
    def get_tournament_level(self, tournament: str) -> str:
        """Hae turnauksen taso"""
        tournament_upper = tournament.upper()
        if re.search(r'W15', tournament_upper):
            return 'W15'
        elif re.search(r'W25', tournament_upper):
            return 'W25'
        elif re.search(r'W35', tournament_upper):
            return 'W35'
        elif re.search(r'W50', tournament_upper):
            return 'W50'
        elif re.search(r'W60', tournament_upper):
            return 'W60'
        elif re.search(r'W75', tournament_upper):
            return 'W75'
        elif re.search(r'W80', tournament_upper):
            return 'W80'
        elif re.search(r'W100', tournament_upper):
            return 'W100'
        return 'Unknown'
    
    def get_flashscore_link(self, tournament: str) -> str:
        """Generoi FlashScore-linkki turnaukselle"""
        # Yksinkertaistettu linkki - käyttäjä voi etsiä turnauksen FlashScore:sta
        tournament_clean = tournament.replace(' ', '-').replace(',', '').lower()
        return f"https://www.flashscore.com/tennis/"
    
    def get_bet365_link(self, player1: str, player2: str) -> str:
        """Generoi Bet365-linkki ottelulle"""
        # Bet365 käyttää hakua, joten annetaan suora linkki tennis-sivulle
        return "https://www.bet365.com/#/AC/B1/C1/D13/E2/F2/"
    
    def get_wta_ranking_link(self, player: str) -> str:
        """Generoi WTA ranking -linkki pelaajalle"""
        player_clean = player.replace(' ', '-').lower()
        return f"https://www.wtatennis.com/rankings"
    
    def display_matches(self, matches: List[Dict]):
        """Näytä ottelut terminaalissa workflow-muodossa"""
        if not matches:
            print("\n" + "="*80)
            print("⚠️  EI ITF WOMEN -OTTELUITA LÖYDETTY")
            print("="*80)
            print("\n💡 Vinkit:")
            print("   1. Tarkista FlashScore.com/tennis manuaalisesti")
            print("   2. ITF Women -turnauksia voi olla vähemmän marraskuussa")
            print("   3. Kausi alkaa uudelleen tammikuussa")
            print("   4. Tarkista myös ITF-sivut: https://www.itftennis.com")
            print()
            return
        
        # Ryhmittele turnaukset tasojen mukaan
        w15_matches = [m for m in matches if 'W15' in m.get('tournament', '').upper()]
        w25_matches = [m for m in matches if 'W25' in m.get('tournament', '').upper()]
        w35_matches = [m for m in matches if 'W35' in m.get('tournament', '').upper()]
        other_matches = [m for m in matches if m not in w15_matches + w25_matches + w35_matches]
        
        print("\n" + "="*80)
        print(f"🎾 ITF WOMEN -TURNAUKSET LÖYDETTY: {len(matches)} kpl")
        print("="*80)
        print("\n📋 VALIDOIDUT KRIITEERIT:")
        print("   ✅ ITF W15, W25, W60, W80, W100")
        print("   ✅ Odds range: 1.51-2.00 (tarkista Bet365:llä)")
        print("   ✅ Pelaajat rankingilla 100-800")
        print("   ✅ SINGLE bets only")
        print()
        
        # Näytä W15-turnaukset ensin (parhaiten kriteereihin sopivia)
        if w15_matches:
            print("="*80)
            print(f"✅ W15-TURNAUKSET ({len(w15_matches)} kpl) - PARHAITEN KRIITEEREIHIN SOPIVIA")
            print("="*80)
            print()
            
            for i, match in enumerate(w15_matches, 1):
                tournament = match.get('tournament', 'N/A')
                print(f"{'─'*80}")
                print(f"🎾 TURNAUS {i}/{len(w15_matches)}: {tournament}")
                print(f"{'─'*80}")
                print()
                print("📋 WORKFLOW:")
                print()
                print("1️⃣  FLASHSCORE → Ottelut + aikataulut")
                print(f"   🔗 {self.get_flashscore_link(tournament)}")
                print(f"   💡 Etsi: '{tournament}' FlashScore:sta")
                print()
                print("2️⃣  BET365 → Odds-validointi (1.51-2.00)")
                print(f"   🔗 {self.get_bet365_link('', '')}")
                print(f"   💡 Etsi ottelut ja tarkista odds")
                print(f"   ✅ Kriteeri: Odds 1.51-2.00")
                print()
                print("3️⃣  WTA → Ranking-tarkistus (100-800)")
                print(f"   🔗 {self.get_wta_ranking_link('')}")
                print(f"   💡 Tarkista pelaajien WTA-rankingit")
                print(f"   ✅ Kriteeri: Ranking 100-800")
                print()
                print("4️⃣  KIRJAUS → Bets database (Notion)")
                print(f"   📝 Käytä: BETTING_LOG_TEMPLATE.md")
                print(f"   🔗 Automaattinen kirjaus: python notion_bet_logger.py")
                print(f"   ✅ Jos kaikki kriteerit täyttyvät → SINGLE bet")
                print()
        
        # Näytä muut turnaukset (jos pelaajat löytyivät)
        other_tournaments = w25_matches + w35_matches + other_matches
        if other_tournaments:
            print("="*80)
            print(f"📊 MUUT TURNAUKSET ({len(other_tournaments)} kpl)")
            print("="*80)
            print()
            
            # Check if we have actual player data
            has_players = any(m.get('player1') and m.get('player1') != 'Check FlashScore' for m in other_tournaments)
            
            if has_players:
                # Show matches with players
                for i, match in enumerate(other_tournaments, 1):
                    player1 = match.get('player1', 'N/A')
                    player2 = match.get('player2', 'N/A')
                    tournament = match.get('tournament', 'N/A')
                    time = match.get('time', 'TBD')
                    level = self.get_tournament_level(tournament)
                    
                    print(f"────────────────────────────────────────────────────────────────────────────────")
                    print(f"🎾 OTTELU {i}/{len(other_tournaments)}")
                    print(f"────────────────────────────────────────────────────────────────────────────────")
                    print(f"👤 {player1} vs {player2}")
                    print(f"🏆 {tournament} ({level})")
                    print(f"⏰ {time}")
                    print()
                    print("📋 WORKFLOW:")
                    print()
                    print("1️⃣  FLASHSCORE → Tarkista ottelu")
                    print(f"   🔗 https://www.flashscore.com/tennis/")
                    print()
                    print("2️⃣  BET365 → Odds-validointi (1.51-2.00)")
                    print(f"   🔗 https://www.bet365.com/#/AC/B1/C1/D13/E2/F2/")
                    print(f"   💡 Etsi: {player1} vs {player2}")
                    print(f"   ✅ Kriteeri: Odds 1.51-2.00")
                    print()
                    print("3️⃣  WTA → Ranking-tarkistus (100-800)")
                    print(f"   🔗 https://www.wtatennis.com/rankings")
                    print(f"   💡 Tarkista: {player1} ja {player2}")
                    print(f"   ✅ Kriteeri: Ranking 100-800")
                    print()
                    print("4️⃣  KIRJAUS → Bets database (Notion)")
                    print(f"   📝 Käytä: BETTING_LOG_TEMPLATE.md")
                    print(f"   ✅ Jos kaikki kriteerit täyttyvät → SINGLE bet")
                    print()
            else:
                # Show just tournaments
                for i, match in enumerate(other_tournaments, 1):
                    tournament = match.get('tournament', 'N/A')
                    level = self.get_tournament_level(tournament)
                    print(f"   {i}. {tournament} ({level})")
                
                print()
                print("💡 Huomio: W35/W50/W75 ovat korkeampia, mutta silti ITF Women")
                print("💡 Tarkista FlashScore:sta ottelut näistä turnauksista")
                print()
        
        print("="*80)
        print("📊 YHTEENVETO")
        print("="*80)
        print(f"✅ W15-turnaukset: {len(w15_matches)} kpl (parhaiten kriteereihin sopivia)")
        print(f"📊 Muut turnaukset: {len(other_tournaments)} kpl")
        print(f"📈 Yhteensä: {len(matches)} turnausta")
        print()
        print("💡 MUISTA:")
        print("   - Tarkista aina odds Bet365:llä (1.51-2.00)")
        print("   - Tarkista pelaajien rankingit WTA:sta (100-800)")
        print("   - Käytä SINGLE bets only")
        print("   - Kirjaa kaikki betit Notioniin")
        print()

async def main():
    """Pääfunktio"""
    print("\n" + "="*80)
    print("🎾 ITF WOMEN MATCH CHECKER")
    print("="*80)
    print("\n🔍 Tarkistetaan FlashScore:sta ITF Women -ottelut...")
    print("📋 Kriteerit: ITF W15/W25/W60/W80/W100, odds 1.51-2.00")
    print()
    
    # Initialize Notion logger (optional)
    notion_logger = None
    try:
        from notion_bet_logger import NotionBetLogger
        notion_logger = NotionBetLogger()
        if notion_logger.client and notion_logger.database_id:
            print("✅ Notion Bet Logger ready - bets can be logged automatically")
        else:
            print("ℹ️  Notion Bet Logger not configured - manual logging required")
    except ImportError:
        print("ℹ️  Notion Bet Logger not available - install: pip install notion-client")
    except Exception as e:
        print(f"ℹ️  Notion Bet Logger: {e}")
    
    print()
    
    async with ITFMatchChecker() as checker:
        # Fetch tennis page
        html = await checker.fetch_tennis_page()
        
        if not html:
            print("❌ Ei voitu hakea FlashScore-sivua")
            print("💡 Yritä manuaalisesti: https://www.flashscore.com/tennis/")
            return
        
        # Parse matches
        all_matches = await checker.parse_tennis_matches(html)
        
        # Filter ITF Women matches
        itf_matches = checker.filter_itf_women_matches(all_matches)
        
        # Display results
        checker.display_matches(itf_matches)
        
        # Additional info
        if itf_matches:
            print("💡 MUISTA:")
            print("   - Tarkista odds manuaalisesti Bet365:llä")
            print("   - Varmista että odds ovat 1.51-2.00")
            print("   - Tarkista pelaajien rankingit")
            print("   - Käytä SINGLE bets only")
            if notion_logger and notion_logger.client and notion_logger.database_id:
                print("   - Betit voidaan kirjata automaattisesti Notioniin")
            else:
                print("   - Kirjaa betit manuaalisesti Notioniin")
            print()
        else:
            print("💡 Jos ei löydy otteluita:")
            print("   1. Tarkista FlashScore manuaalisesti: https://www.flashscore.com/tennis/")
            print("   2. ITF Women -turnauksia voi olla vähemmän marraskuussa")
            print("   3. Kausi alkaa uudelleen tammikuussa")
            print("   4. Tarkista myös: https://www.itftennis.com")
            print()
            print("🔗 HYÖDYLLISET LINKIT:")
            print("   • FlashScore Tennis: https://www.flashscore.com/tennis/")
            print("   • ITF Calendar: https://www.itftennis.com/en/tournaments/")
            print("   • Bet365 Tennis: https://www.bet365.com/#/AC/B1/C1/D13/E2/F2/")
            print("   • WTA Schedule: https://www.wtatennis.com/tournaments")
            print()
            print("📋 MANUAALINEN TARKISTUS:")
            print("   1. Avaa FlashScore.com/tennis")
            print("   2. Etsi 'ITF' tai 'W15/W25/W60' turnauksia")
            print("   3. Tarkista ottelut ja pelaajat")
            print("   4. Tarkista odds Bet365:llä (1.51-2.00)")
            print("   5. Jos kriteerit täyttyvät → SINGLE bet")
            print()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Hei hei!\n")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

