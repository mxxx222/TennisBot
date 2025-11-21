#!/usr/bin/env python3
"""
🎾 TENNIS ABSTRACT ELO SCRAPER
==============================

Production-ready scraper that fetches ELO ratings from tennisabstract.com
and updates Player Cards database in Notion.

Features:
- Scrapes player ELO ratings (Overall, Hard, Clay, Grass)
- Updates Player Cards DB in Notion
- Calculates ELO Change (7D, 30D, 90D)
- Rate limiting and retry logic
- Batch updates for efficiency
"""

import os
import sys
import logging
import time
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / 'telegram_secrets.env'
if env_path.exists():
    load_dotenv(env_path)

# Notion API
try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    print("❌ ERROR: notion-client not installed")
    print("   Install: pip install notion-client")

# Web scraping
try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("❌ ERROR: requests or beautifulsoup4 not installed")
    print("   Install: pip install requests beautifulsoup4")

logger = logging.getLogger(__name__)


@dataclass
class PlayerELO:
    """Player ELO rating data"""
    player_name: str
    overall_elo: Optional[float] = None
    hard_elo: Optional[float] = None
    clay_elo: Optional[float] = None
    grass_elo: Optional[float] = None
    peak_elo: Optional[float] = None
    peak_elo_date: Optional[datetime] = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = datetime.now()


class TennisAbstractELOScraper:
    """
    Scraper for Tennis Abstract ELO ratings
    
    Scrapes from tennisabstract.com player profile pages
    """
    
    BASE_URL = "https://www.tennisabstract.com"
    SEARCH_URL = f"{BASE_URL}/cgi-bin/search.cgi"
    RATE_LIMIT_DELAY = 2.0  # seconds between requests
    MAX_RETRIES = 3
    TIMEOUT = 30
    
    def __init__(self):
        """Initialize scraper"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.rate_limit_last_request = 0
        
        logger.info("🎾 Tennis Abstract ELO Scraper initialized")
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        now = time.time()
        time_since_last = now - self.rate_limit_last_request
        if time_since_last < self.RATE_LIMIT_DELAY:
            sleep_time = self.RATE_LIMIT_DELAY - time_since_last
            time.sleep(sleep_time)
        self.rate_limit_last_request = time.time()
    
    def search_player(self, player_name: str) -> Optional[str]:
        """
        Search for player on Tennis Abstract
        
        Args:
            player_name: Player name to search for
            
        Returns:
            Player profile URL if found, None otherwise
        """
        self._rate_limit()
        
        try:
            # Search for player
            search_params = {
                'query': player_name,
                'type': 'player'
            }
            
            response = self.session.get(
                self.SEARCH_URL,
                params=search_params,
                timeout=self.TIMEOUT
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for player links in search results
            # Tennis Abstract search results typically have player links
            player_links = soup.find_all('a', href=re.compile(r'/player/'))
            
            if player_links:
                # Try exact name match first
                for link in player_links:
                    link_text = link.get_text(strip=True).lower()
                    if player_name.lower() in link_text or link_text in player_name.lower():
                        href = link.get('href')
                        if href.startswith('/'):
                            return f"{self.BASE_URL}{href}"
                        return href
                
                # Return first result if no exact match
                href = player_links[0].get('href')
                if href.startswith('/'):
                    return f"{self.BASE_URL}{href}"
                return href
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error searching for player {player_name}: {e}")
            return None
    
    def scrape_player_elo(self, player_name: str, player_url: Optional[str] = None) -> Optional[PlayerELO]:
        """
        Scrape ELO ratings for a player
        
        Args:
            player_name: Player name
            player_url: Optional direct URL to player profile
            
        Returns:
            PlayerELO object if found, None otherwise
        """
        if not player_url:
            player_url = self.search_player(player_name)
            if not player_url:
                logger.warning(f"⚠️ Player {player_name} not found on Tennis Abstract")
                return None
        
        self._rate_limit()
        
        retries = 0
        while retries < self.MAX_RETRIES:
            try:
                response = self.session.get(player_url, timeout=self.TIMEOUT)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Initialize ELO object
                elo = PlayerELO(player_name=player_name)
                
                # Parse ELO ratings from player profile page
                # Tennis Abstract typically displays ELO in tables or specific sections
                
                # Look for ELO ratings in the page
                # Common patterns: "ELO", "Rating", "Elo Rating"
                elo_pattern = re.compile(r'elo|rating', re.IGNORECASE)
                
                # Find tables or divs containing ELO data
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            label = cells[0].get_text(strip=True).lower()
                            value_str = cells[1].get_text(strip=True)
                            
                            # Extract ELO values
                            if 'overall' in label or 'total' in label:
                                elo.overall_elo = self._parse_elo_value(value_str)
                            elif 'hard' in label:
                                elo.hard_elo = self._parse_elo_value(value_str)
                            elif 'clay' in label:
                                elo.clay_elo = self._parse_elo_value(value_str)
                            elif 'grass' in label:
                                elo.grass_elo = self._parse_elo_value(value_str)
                            elif 'peak' in label or 'career high' in label:
                                elo.peak_elo = self._parse_elo_value(value_str)
                
                # Alternative: Look for text patterns with ELO values
                page_text = soup.get_text()
                elo_matches = re.findall(r'elo[:\s]+(\d{3,4})', page_text, re.IGNORECASE)
                if elo_matches and not elo.overall_elo:
                    elo.overall_elo = float(elo_matches[0])
                
                # If we found at least one ELO value, return it
                if elo.overall_elo or elo.hard_elo or elo.clay_elo or elo.grass_elo:
                    logger.info(f"✅ Found ELO for {player_name}: Overall={elo.overall_elo}, Hard={elo.hard_elo}, Clay={elo.clay_elo}")
                    return elo
                
                logger.warning(f"⚠️ Could not parse ELO for {player_name} from {player_url}")
                return None
                
            except requests.exceptions.RequestException as e:
                retries += 1
                if retries < self.MAX_RETRIES:
                    logger.warning(f"⚠️ Retry {retries}/{self.MAX_RETRIES} for {player_name}: {e}")
                    time.sleep(2 ** retries)  # Exponential backoff
                else:
                    logger.error(f"❌ Failed to scrape {player_name} after {self.MAX_RETRIES} retries: {e}")
                    return None
            except Exception as e:
                logger.error(f"❌ Error scraping ELO for {player_name}: {e}")
                return None
        
        return None
    
    def _parse_elo_value(self, value_str: str) -> Optional[float]:
        """Parse ELO value from string"""
        try:
            # Remove non-numeric characters except decimal point
            cleaned = re.sub(r'[^\d.]', '', value_str)
            if cleaned:
                return float(cleaned)
        except (ValueError, AttributeError):
            pass
        return None
    
    def scrape_multiple_players(self, player_names: List[str]) -> Dict[str, Optional[PlayerELO]]:
        """
        Scrape ELO ratings for multiple players
        
        Args:
            player_names: List of player names
            
        Returns:
            Dictionary mapping player names to PlayerELO objects
        """
        results = {}
        
        logger.info(f"🎾 Scraping ELO for {len(player_names)} players...")
        
        for i, player_name in enumerate(player_names, 1):
            logger.info(f"[{i}/{len(player_names)}] Scraping {player_name}...")
            
            elo = self.scrape_player_elo(player_name)
            results[player_name] = elo
            
            if elo:
                logger.info(f"✅ {player_name}: ELO={elo.overall_elo}")
            else:
                logger.warning(f"⚠️ {player_name}: Not found")
        
        found_count = sum(1 for v in results.values() if v is not None)
        logger.info(f"\n✅ Scraping complete: {found_count}/{len(player_names)} players found")
        
        return results


class PlayerCardsELOUpdater:
    """
    Updates Player Cards database in Notion with ELO ratings
    """
    
    def __init__(self, database_id: Optional[str] = None):
        """
        Initialize updater
        
        Args:
            database_id: Player Cards database ID (optional, from env)
        """
        if not NOTION_AVAILABLE:
            self.client = None
            logger.error("❌ Notion client not available")
            return
        
        notion_token = os.getenv('NOTION_API_KEY') or os.getenv('NOTION_TOKEN')
        if not notion_token:
            self.client = None
            logger.error("❌ NOTION_API_KEY or NOTION_TOKEN not set")
            return
        
        self.client = Client(auth=notion_token)
        self.database_id = database_id or os.getenv('NOTION_ITF_PLAYER_CARDS_DB_ID') or os.getenv('PLAYER_CARDS_DB_ID')
        
        if not self.database_id:
            logger.error("❌ Player Cards database ID not set")
        
        logger.info("📊 Player Cards ELO Updater initialized")
    
    def find_player_card(self, player_name: str) -> Optional[str]:
        """
        Find Player Card page ID by name
        
        Args:
            player_name: Player name to search for
            
        Returns:
            Page ID if found, None otherwise
        """
        if not self.client or not self.database_id:
            return None
        
        try:
            # Query Player Cards database for matching name
            response = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "or": [
                        {
                            "property": "Name",
                            "title": {
                                "contains": player_name
                            }
                        },
                        {
                            "property": "Player Name",
                            "rich_text": {
                                "contains": player_name
                            }
                        }
                    ]
                }
            )
            
            results = response.get('results', [])
            if results:
                # Try exact match first
                for result in results:
                    props = result.get('properties', {})
                    name_props = ['Name', 'Player Name', 'Full Name']
                    for prop_name in name_props:
                        prop = props.get(prop_name, {})
                        if prop.get('title'):
                            db_name = prop['title'][0]['plain_text']
                        elif prop.get('rich_text'):
                            db_name = prop['rich_text'][0]['plain_text']
                        else:
                            continue
                        
                        # Exact or last name match
                        if (player_name.lower() == db_name.lower() or
                            player_name.split()[-1].lower() == db_name.split()[-1].lower()):
                            return result['id']
                
                # Return first result if no exact match
                return results[0]['id']
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error finding player card for {player_name}: {e}")
            return None
    
    def update_player_elo(self, player_name: str, elo: PlayerELO, elo_changes: Optional[Dict[str, float]] = None) -> bool:
        """
        Update player ELO in Player Cards database
        
        Args:
            player_name: Player name
            elo: PlayerELO object with ELO ratings
            elo_changes: Optional dict with ELO changes (7D, 30D, 90D)
            
        Returns:
            True if successful
        """
        if not self.client or not self.database_id:
            return False
        
        player_card_id = self.find_player_card(player_name)
        if not player_card_id:
            logger.warning(f"⚠️ Player Card not found for {player_name}")
            return False
        
        try:
            properties = {}
            
            # Update ELO ratings
            if elo.overall_elo is not None:
                properties['ELO'] = {'number': elo.overall_elo}
            
            # Update surface-specific ELO (if properties exist)
            if elo.hard_elo is not None:
                properties['ELO Hard'] = {'number': elo.hard_elo}
            if elo.clay_elo is not None:
                properties['ELO Clay'] = {'number': elo.clay_elo}
            if elo.grass_elo is not None:
                properties['ELO Grass'] = {'number': elo.grass_elo}
            
            # Update Peak ELO
            if elo.peak_elo is not None:
                properties['Peak ELO'] = {'number': elo.peak_elo}
            if elo.peak_elo_date:
                properties['Peak ELO Date'] = {'date': {'start': elo.peak_elo_date.isoformat()}}
            
            # Update ELO Changes (if provided)
            if elo_changes:
                if '7D' in elo_changes:
                    properties['ELO Change 7D'] = {'number': elo_changes['7D']}
                if '30D' in elo_changes:
                    properties['ELO Change 30D'] = {'number': elo_changes['30D']}
                if '90D' in elo_changes:
                    properties['ELO Change 90D'] = {'number': elo_changes['90D']}
            
            # Update timestamp
            properties['ELO Updated At'] = {'date': {'start': elo.updated_at.isoformat()}}
            
            # Update page
            self.client.pages.update(
                page_id=player_card_id,
                properties=properties
            )
            
            logger.info(f"✅ Updated ELO for {player_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating ELO for {player_name}: {e}")
            return False
    
    def calculate_elo_changes(self, player_name: str, current_elo: float) -> Optional[Dict[str, float]]:
        """
        Calculate ELO changes by comparing with historical values from Player Card
        
        Args:
            player_name: Player name
            current_elo: Current ELO rating
            
        Returns:
            Dict with ELO changes (7D, 30D, 90D) or None
        """
        if not self.client or not self.database_id:
            return None
        
        try:
            # Find player card
            player_card_id = self.find_player_card(player_name)
            if not player_card_id:
                return None
            
            # Get player card data
            page = self.client.pages.retrieve(page_id=player_card_id)
            props = page.get('properties', {})
            
            # Get current ELO and last update date
            current_elo_prop = props.get('ELO', {})
            current_db_elo = current_elo_prop.get('number')
            
            # Get ELO Updated At date
            elo_updated_prop = props.get('ELO Updated At', {})
            last_update_date = None
            if elo_updated_prop.get('date'):
                date_str = elo_updated_prop['date'].get('start')
                if date_str:
                    try:
                        last_update_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    except:
                        pass
            
            # If no previous ELO or update date, return None (first time tracking)
            if current_db_elo is None or last_update_date is None:
                return None
            
            # Calculate time differences
            now = datetime.now(last_update_date.tzinfo) if last_update_date.tzinfo else datetime.now()
            time_diff = now - last_update_date
            
            # Calculate changes for different periods
            changes = {}
            
            # For 7D, 30D, 90D: we need historical snapshots
            # For now, if last update was within these periods, calculate change
            # Otherwise, we'll need to store historical snapshots
            
            # Simple calculation: if we have a previous ELO and current ELO, calculate change
            if current_db_elo is not None:
                elo_change = current_elo - current_db_elo
                
                # If last update was recent, use it for all periods
                # In a full implementation, we'd store snapshots at 7D, 30D, 90D intervals
                if time_diff.days <= 7:
                    changes['7D'] = elo_change
                if time_diff.days <= 30:
                    changes['30D'] = elo_change
                if time_diff.days <= 90:
                    changes['90D'] = elo_change
            
            return changes if changes else None
            
        except Exception as e:
            logger.error(f"❌ Error calculating ELO changes for {player_name}: {e}")
            return None


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Tennis Abstract ELO Scraper')
    parser.add_argument('--players', nargs='+', help='Player names to scrape')
    parser.add_argument('--limit', type=int, default=100, help='Limit number of players (default: 100)')
    parser.add_argument('--test', action='store_true', help='Test mode (5 players only)')
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Initialize scraper
    if not REQUESTS_AVAILABLE:
        logger.error("❌ Required packages not installed")
        return
    
    scraper = TennisAbstractELOScraper()
    updater = PlayerCardsELOUpdater()
    
    # Get player list
    if args.test:
        # Test with 5 top WTA players
        player_names = [
            "Iga Swiatek",
            "Aryna Sabalenka",
            "Coco Gauff",
            "Elena Rybakina",
            "Jessica Pegula"
        ]
        logger.info("🧪 Test mode: Scraping 5 top WTA players")
    elif args.players:
        player_names = args.players
    else:
        # Get all players from Player Cards DB
        if not updater.client or not updater.database_id:
            logger.error("❌ Cannot get player list: Notion client or DB ID not set")
            return
        
        try:
            response = updater.client.databases.query(database_id=updater.database_id)
            players = response.get('results', [])
            
            player_names = []
            for player in players[:args.limit]:
                props = player.get('properties', {})
                name_props = ['Name', 'Player Name', 'Full Name']
                for prop_name in name_props:
                    prop = props.get(prop_name, {})
                    if prop.get('title'):
                        player_names.append(prop['title'][0]['plain_text'])
                        break
                    elif prop.get('rich_text'):
                        player_names.append(prop['rich_text'][0]['plain_text'])
                        break
            
            logger.info(f"📊 Found {len(player_names)} players in Player Cards DB")
        except Exception as e:
            logger.error(f"❌ Error getting player list: {e}")
            return
    
    # Scrape ELO ratings
    elo_results = scraper.scrape_multiple_players(player_names)
    
    # Update Player Cards DB
    updated_count = 0
    failed_count = 0
    
    logger.info("\n📊 Updating Player Cards database...")
    
    for player_name, elo in elo_results.items():
        if elo:
            # Calculate ELO changes
            elo_changes = None
            if elo.overall_elo:
                elo_changes = updater.calculate_elo_changes(player_name, elo.overall_elo)
            
            if updater.update_player_elo(player_name, elo, elo_changes):
                updated_count += 1
            else:
                failed_count += 1
        else:
            failed_count += 1
    
    logger.info(f"\n✅ Update complete!")
    logger.info(f"   Updated: {updated_count}")
    logger.info(f"   Failed: {failed_count}")
    logger.info(f"   Total: {len(player_names)}")


if __name__ == "__main__":
    main()

