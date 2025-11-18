#!/usr/bin/env python3
"""
👤 ITF PLAYER SCRAPER
=====================

Scrapes ITF player data from itftennis.com for top 200 players.
Extracts surface statistics, recent form, rankings.
Updates Player Profiles database weekly.
"""

import asyncio
import aiohttp
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from bs4 import BeautifulSoup
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class ITFPlayerScraper:
    """Scraper for ITF player data from itftennis.com"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ITF Player Scraper
        
        Args:
            config: Configuration dict
        """
        self.config = config or {}
        self.base_url = "https://www.itftennis.com"
        self.session = None
        self.target_players = self.config.get('target_players', 200)
        self.rate_limit = self.config.get('rate_limit', 2.0)
        
        logger.info(f"👤 ITF Player Scraper initialized (target: {self.target_players} players)")
    
    async def __aenter__(self):
        """Async context manager entry"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
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
    
    async def scrape_player_rankings(self) -> List[Dict[str, Any]]:
        """
        Scrape top ITF player rankings
        
        Returns:
            List of player dictionaries with name and ranking
        """
        players = []
        
        try:
            # ITF rankings URL (approximate - may need adjustment)
            url = f"{self.base_url}/en/rankings/womens-rankings/"
            
            logger.info(f"🔍 Fetching ITF rankings from: {url}")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    players = self._parse_rankings(html)
                else:
                    logger.warning(f"⚠️ Status {response.status} for {url}")
            
            # Limit to target number
            players = players[:self.target_players]
            
            logger.info(f"✅ Scraped {len(players)} player rankings")
            return players
            
        except Exception as e:
            logger.error(f"❌ Error scraping rankings: {e}")
            return []
    
    def _parse_rankings(self, html: str) -> List[Dict[str, Any]]:
        """Parse player rankings from HTML"""
        players = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find ranking table (structure may vary)
            # Look for table rows with player data
            rows = soup.find_all('tr')
            
            for row in rows[:self.target_players + 50]:  # Get extra for filtering
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:
                    # Try to extract player name and ranking
                    text = row.get_text(strip=True)
                    
                    # Pattern: ranking number, player name
                    match = re.search(r'(\d+)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', text)
                    if match:
                        ranking = int(match.group(1))
                        name = match.group(2).strip()
                        
                        if name and ranking <= self.target_players:
                            players.append({
                                'name': name,
                                'itf_ranking': ranking,
                                'wta_ranking': None,  # Would need separate scrape
                            })
            
            logger.info(f"📊 Parsed {len(players)} players from rankings")
            return players
            
        except Exception as e:
            logger.error(f"❌ Error parsing rankings: {e}")
            return []
    
    async def scrape_player_stats(self, player_name: str) -> Optional[Dict[str, Any]]:
        """
        Scrape detailed stats for a specific player
        
        Args:
            player_name: Player name
            
        Returns:
            Player statistics dictionary
        """
        try:
            # Search for player page (URL structure may vary)
            search_url = f"{self.base_url}/en/players/{player_name.lower().replace(' ', '-')}/"
            
            async with self.session.get(search_url) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_player_stats(html, player_name)
                else:
                    logger.debug(f"⚠️ Could not fetch player page for {player_name}")
                    return None
            
        except Exception as e:
            logger.debug(f"Error scraping player stats for {player_name}: {e}")
            return None
    
    def _parse_player_stats(self, html: str, player_name: str) -> Dict[str, Any]:
        """Parse player statistics from HTML"""
        stats = {
            'name': player_name,
            'surface_win_hard': None,
            'surface_win_clay': None,
            'surface_win_grass': None,
            'avg_games_per_set': None,
            'retirement_rate': None,
            'recent_form': None,
        }
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            
            # Extract surface win percentages (patterns may vary)
            # Hard surface
            hard_match = re.search(r'Hard.*?(\d+\.?\d*)%', text, re.I)
            if hard_match:
                stats['surface_win_hard'] = float(hard_match.group(1)) / 100
            
            # Clay surface
            clay_match = re.search(r'Clay.*?(\d+\.?\d*)%', text, re.I)
            if clay_match:
                stats['surface_win_clay'] = float(clay_match.group(1)) / 100
            
            # Grass surface
            grass_match = re.search(r'Grass.*?(\d+\.?\d*)%', text, re.I)
            if grass_match:
                stats['surface_win_grass'] = float(grass_match.group(1)) / 100
            
            # Extract recent form (W-L-W-L pattern)
            form_match = re.search(r'([WL\-]+)', text)
            if form_match:
                form_str = form_match.group(1)
                if len(form_str) >= 5:
                    stats['recent_form'] = form_str[:10]  # Last 5 matches
            
            return stats
            
        except Exception as e:
            logger.debug(f"Error parsing player stats: {e}")
            return stats
    
    async def scrape_all_players(self) -> List[Dict[str, Any]]:
        """
        Scrape all target players with their statistics
        
        Returns:
            List of complete player data dictionaries
        """
        logger.info(f"🚀 Starting player scrape for {self.target_players} players...")
        
        # Step 1: Get rankings
        players = await self.scrape_player_rankings()
        
        if not players:
            logger.warning("⚠️ No players found in rankings")
            return []
        
        # Step 2: Scrape detailed stats for each player
        complete_players = []
        
        for i, player in enumerate(players[:self.target_players], 1):
            logger.info(f"📊 Scraping stats for {player['name']} ({i}/{min(len(players), self.target_players)})...")
            
            stats = await self.scrape_player_stats(player['name'])
            
            if stats:
                # Merge ranking data with stats
                complete_player = {**player, **stats}
                complete_players.append(complete_player)
            else:
                # Use basic data if stats unavailable
                complete_players.append(player)
            
            # Rate limiting
            await asyncio.sleep(self.rate_limit)
        
        logger.info(f"✅ Scraped {len(complete_players)} complete player profiles")
        return complete_players


async def main():
    """Test ITF Player Scraper"""
    print("👤 ITF PLAYER SCRAPER TEST")
    print("=" * 50)
    
    config = {
        'target_players': 10,  # Test with 10 players
        'rate_limit': 2.0,
    }
    
    async with ITFPlayerScraper(config) as scraper:
        players = await scraper.scrape_all_players()
        
        if players:
            print(f"\n✅ Scraped {len(players)} players")
            print("\n📊 Sample players:")
            for player in players[:5]:
                print(f"   {player.get('name')} - ITF Rank: {player.get('itf_ranking', 'N/A')}")
        else:
            print("\n⚠️ No players scraped")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())

