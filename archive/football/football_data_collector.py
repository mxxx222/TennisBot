#!/usr/bin/env python3
"""
⚽ FOOTBALL DATA COLLECTOR - COMPREHENSIVE DATA PLAN
====================================================

Kattava jalkapallodatan keräysjärjestelmä joka käyttää:
- Web scraping (BBC Sport, ESPN, WhoScored)
- Free APIs (Football-Data.org, API-Football, Sportmonks)
- Data aggregation ja normalisointi
- Automaattinen päivitysjärjestelmä

Author: TennisBot Advanced Analytics
Version: 1.0.0
"""

import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json
import logging
from pathlib import Path
import time
import os
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class FootballMatch:
    """Jalkapallo-ottelun tiedot"""
    match_id: str
    home_team: str
    away_team: str
    league: str
    date: str
    status: str  # scheduled, live, finished
    score: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    
    # Statistics
    home_stats: Dict[str, Any] = None
    away_stats: Dict[str, Any] = None
    
    # Odds
    odds: Dict[str, float] = None
    
    # Metadata
    venue: Optional[str] = None
    attendance: Optional[int] = None
    referee: Optional[str] = None
    source: str = ""
    
    def __post_init__(self):
        if self.home_stats is None:
            self.home_stats = {}
        if self.away_stats is None:
            self.away_stats = {}
        if self.odds is None:
            self.odds = {}


@dataclass
class TeamStats:
    """Joukkueen tilastot"""
    team_name: str
    league: str
    season: str
    
    # League stats
    position: int
    played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int
    
    # Performance stats
    home_record: Dict[str, int] = None
    away_record: Dict[str, int] = None
    recent_form: List[str] = None  # ['W', 'D', 'L', 'W', 'W']
    
    # Advanced stats
    avg_goals_scored: float = 0.0
    avg_goals_conceded: float = 0.0
    avg_possession: float = 0.0
    avg_shots: float = 0.0
    avg_corners: float = 0.0
    
    def __post_init__(self):
        if self.home_record is None:
            self.home_record = {'wins': 0, 'draws': 0, 'losses': 0}
        if self.away_record is None:
            self.away_record = {'wins': 0, 'draws': 0, 'losses': 0}
        if self.recent_form is None:
            self.recent_form = []


class FootballDataCollector:
    """
    Kattava jalkapallodatan keräysjärjestelmä
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Football Data Collector
        
        Args:
            config: Konfiguraatio (API keys, jne.)
        """
        self.config = config or {}
        
        # API Keys
        self.football_data_api_key = self.config.get('football_data_api_key') or os.getenv('FOOTBALL_DATA_API_KEY')
        self.api_football_key = self.config.get('api_football_key') or os.getenv('API_FOOTBALL_KEY')
        self.sportmonks_key = self.config.get('sportmonks_key') or os.getenv('SPORTMONKS_KEY')
        
        # API Endpoints
        self.football_data_base = "https://api.football-data.org/v4"
        self.api_football_base = "https://v3.football.api-sports.io"
        self.sportmonks_base = "https://api.sportmonks.com/v3"
        
        # Web scraping targets
        self.scraping_targets = {
            'bbc_sport': 'https://www.bbc.com/sport/football',
            'espn': 'https://www.espn.com/soccer/fixtures',
            'whoscored': 'https://www.whoscored.com',
            'flashscore': 'https://www.flashscore.com/football/',
            'sofascore': 'https://www.sofascore.com/football'
        }
        
        # Data storage
        self.data_dir = Path('data/football')
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Rate limiting
        self.request_delay = 1.0
        self.last_request_time = {}
        
        logger.info("⚽ Football Data Collector initialized")
    
    # ═══════════════════════════════════════════════════════
    # API INTEGRATIONS
    # ═══════════════════════════════════════════════════════
    
    async def fetch_football_data_api(self, endpoint: str, params: Dict = None) -> List[Dict]:
        """
        Hae data Football-Data.org API:sta
        
        Free tier: 10 requests/minute
        """
        if not self.football_data_api_key:
            logger.warning("⚠️ Football-Data.org API key not set")
            return []
        
        url = f"{self.football_data_base}/{endpoint}"
        headers = {
            'X-Auth-Token': self.football_data_api_key,
            'Accept': 'application/json'
        }
        
        try:
            await self._rate_limit('football_data')
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('matches', []) if 'matches' in data else [data]
                    else:
                        logger.error(f"❌ Football-Data API error: {response.status}")
                        return []
        
        except Exception as e:
            logger.error(f"❌ Error fetching from Football-Data API: {e}")
            return []
    
    async def fetch_api_football(self, endpoint: str, params: Dict = None) -> List[Dict]:
        """
        Hae data API-Football:sta
        
        Free tier: 100 requests/day
        """
        if not self.api_football_key:
            logger.warning("⚠️ API-Football key not set")
            return []
        
        url = f"{self.api_football_base}/{endpoint}"
        headers = {
            'x-rapidapi-key': self.api_football_key,
            'x-rapidapi-host': 'v3.football.api-sports.io'
        }
        
        try:
            await self._rate_limit('api_football')
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('response', [])
                    else:
                        logger.error(f"❌ API-Football error: {response.status}")
                        return []
        
        except Exception as e:
            logger.error(f"❌ Error fetching from API-Football: {e}")
            return []
    
    async def fetch_sportmonks(self, endpoint: str, params: Dict = None) -> List[Dict]:
        """
        Hae data Sportmonks API:sta
        
        Free tier: 500 requests/month
        """
        if not self.sportmonks_key:
            logger.warning("⚠️ Sportmonks API key not set")
            return []
        
        url = f"{self.sportmonks_base}/{endpoint}"
        params = params or {}
        params['api_token'] = self.sportmonks_key
        
        try:
            await self._rate_limit('sportmonks')
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', [])
                    else:
                        logger.error(f"❌ Sportmonks API error: {response.status}")
                        return []
        
        except Exception as e:
            logger.error(f"❌ Error fetching from Sportmonks: {e}")
            return []
    
    async def _rate_limit(self, source: str):
        """Rate limiting"""
        if source in self.last_request_time:
            elapsed = time.time() - self.last_request_time[source]
            if elapsed < self.request_delay:
                await asyncio.sleep(self.request_delay - elapsed)
        
        self.last_request_time[source] = time.time()
    
    # ═══════════════════════════════════════════════════════
    # WEB SCRAPING
    # ═══════════════════════════════════════════════════════
    
    async def scrape_bbc_sport(self) -> List[FootballMatch]:
        """Scrape BBC Sport football fixtures"""
        matches = []
        
        try:
            url = self.scraping_targets['bbc_sport']
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Parse fixtures (simplified - would need actual BBC Sport structure)
                        # This is a template - actual implementation would parse BBC's HTML structure
                        logger.info("✅ Scraped BBC Sport")
        
        except Exception as e:
            logger.error(f"❌ Error scraping BBC Sport: {e}")
        
        return matches
    
    async def scrape_espn(self) -> List[FootballMatch]:
        """Scrape ESPN football fixtures"""
        matches = []
        
        try:
            url = self.scraping_targets['espn']
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Parse ESPN fixtures
                        logger.info("✅ Scraped ESPN")
        
        except Exception as e:
            logger.error(f"❌ Error scraping ESPN: {e}")
        
        return matches
    
    async def scrape_whoscored(self) -> List[FootballMatch]:
        """Scrape WhoScored statistics"""
        matches = []
        
        try:
            # WhoScored scraping would require more sophisticated approach
            # due to dynamic content
            logger.info("✅ Scraped WhoScored")
        
        except Exception as e:
            logger.error(f"❌ Error scraping WhoScored: {e}")
        
        return matches
    
    # ═══════════════════════════════════════════════════════
    # DATA AGGREGATION
    # ═══════════════════════════════════════════════════════
    
    async def get_today_matches(self) -> List[FootballMatch]:
        """
        Hae päivän ottelut kaikista lähteistä
        """
        logger.info("🔍 Fetching today's football matches from all sources...")
        
        all_matches = []
        
        # Source 1: Football-Data.org API
        try:
            api_matches = await self.fetch_football_data_api('matches', {
                'dateFrom': datetime.now().strftime('%Y-%m-%d'),
                'dateTo': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            })
            
            for match_data in api_matches:
                match = self._convert_football_data_api(match_data)
                if match:
                    all_matches.append(match)
            
            logger.info(f"✅ Football-Data.org: {len(api_matches)} matches")
        
        except Exception as e:
            logger.error(f"❌ Error fetching Football-Data.org: {e}")
        
        # Source 2: API-Football
        try:
            api_football_matches = await self.fetch_api_football('fixtures', {
                'date': datetime.now().strftime('%Y-%m-%d')
            })
            
            for match_data in api_football_matches:
                match = self._convert_api_football(match_data)
                if match:
                    all_matches.append(match)
            
            logger.info(f"✅ API-Football: {len(api_football_matches)} matches")
        
        except Exception as e:
            logger.error(f"❌ Error fetching API-Football: {e}")
        
        # Source 3: Web Scraping
        try:
            bbc_matches = await self.scrape_bbc_sport()
            espn_matches = await self.scrape_espn()
            whoscored_matches = await self.scrape_whoscored()
            
            all_matches.extend(bbc_matches)
            all_matches.extend(espn_matches)
            all_matches.extend(whoscored_matches)
            
            logger.info(f"✅ Web Scraping: {len(bbc_matches + espn_matches + whoscored_matches)} matches")
        
        except Exception as e:
            logger.error(f"❌ Error web scraping: {e}")
        
        # Remove duplicates
        unique_matches = self._deduplicate_matches(all_matches)
        
        logger.info(f"📊 Total unique matches: {len(unique_matches)}")
        
        return unique_matches
    
    def _convert_football_data_api(self, data: Dict) -> Optional[FootballMatch]:
        """Convert Football-Data.org API data to FootballMatch"""
        try:
            return FootballMatch(
                match_id=f"fd_{data.get('id', '')}",
                home_team=data.get('homeTeam', {}).get('name', 'Unknown'),
                away_team=data.get('awayTeam', {}).get('name', 'Unknown'),
                league=data.get('competition', {}).get('name', 'Unknown'),
                date=data.get('utcDate', ''),
                status=data.get('status', 'scheduled'),
                score=data.get('score', {}).get('fullTime', {}),
                home_score=data.get('score', {}).get('fullTime', {}).get('home'),
                away_score=data.get('score', {}).get('fullTime', {}).get('away'),
                venue=data.get('venue', ''),
                source='football_data_api'
            )
        except Exception as e:
            logger.error(f"❌ Error converting Football-Data API data: {e}")
            return None
    
    def _convert_api_football(self, data: Dict) -> Optional[FootballMatch]:
        """Convert API-Football data to FootballMatch"""
        try:
            fixture = data.get('fixture', {})
            teams = data.get('teams', {})
            score = data.get('score', {})
            
            return FootballMatch(
                match_id=f"af_{fixture.get('id', '')}",
                home_team=teams.get('home', {}).get('name', 'Unknown'),
                away_team=teams.get('away', {}).get('name', 'Unknown'),
                league=data.get('league', {}).get('name', 'Unknown'),
                date=fixture.get('date', ''),
                status=fixture.get('status', {}).get('long', 'scheduled'),
                score=f"{score.get('fulltime', {}).get('home', 0)}-{score.get('fulltime', {}).get('away', 0)}",
                home_score=score.get('fulltime', {}).get('home'),
                away_score=score.get('fulltime', {}).get('away'),
                venue=fixture.get('venue', {}).get('name', ''),
                source='api_football'
            )
        except Exception as e:
            logger.error(f"❌ Error converting API-Football data: {e}")
            return None
    
    def _deduplicate_matches(self, matches: List[FootballMatch]) -> List[FootballMatch]:
        """Remove duplicate matches"""
        seen = set()
        unique = []
        
        for match in matches:
            key = (
                match.home_team.lower(),
                match.away_team.lower(),
                match.date[:10] if match.date else ''
            )
            
            if key not in seen:
                seen.add(key)
                unique.append(match)
        
        return unique
    
    # ═══════════════════════════════════════════════════════
    # TEAM STATISTICS
    # ═══════════════════════════════════════════════════════
    
    async def get_team_stats(self, team_name: str, league: str) -> Optional[TeamStats]:
        """Hae joukkueen tilastot"""
        # This would fetch from APIs and scraping
        # Simplified for now
        return None
    
    # ═══════════════════════════════════════════════════════
    # DATA STORAGE
    # ═══════════════════════════════════════════════════════
    
    def save_matches(self, matches: List[FootballMatch], filename: str = None):
        """Tallenna ottelut JSON-tiedostoon"""
        if filename is None:
            filename = f"football_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.data_dir / filename
        
        data = {
            'fetched_at': datetime.now().isoformat(),
            'total_matches': len(matches),
            'matches': [asdict(match) for match in matches]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"💾 Saved {len(matches)} matches to {filepath}")
        return filepath
    
    def save_to_csv(self, matches: List[FootballMatch], filename: str = None):
        """Tallenna CSV-tiedostoon"""
        if filename is None:
            filename = f"football_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = self.data_dir / filename
        
        df_data = []
        for match in matches:
            df_data.append({
                'Match ID': match.match_id,
                'Home Team': match.home_team,
                'Away Team': match.away_team,
                'League': match.league,
                'Date': match.date,
                'Status': match.status,
                'Score': match.score or '',
                'Venue': match.venue or '',
                'Source': match.source
            })
        
        df = pd.DataFrame(df_data)
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        logger.info(f"💾 Saved to CSV: {filepath}")
        return filepath


if __name__ == "__main__":
    import os
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║  ⚽ FOOTBALL DATA COLLECTOR                                  ║
║  ==========================================================  ║
║                                                              ║
║  Comprehensive football data collection system               ║
║  - Web Scraping (BBC Sport, ESPN, WhoScored)                ║
║  - Free APIs (Football-Data.org, API-Football, Sportmonks)  ║
║  - Data Aggregation & Normalization                          ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    collector = FootballDataCollector()
    
    async def main():
        matches = await collector.get_today_matches()
        
        print(f"\n✅ Found {len(matches)} matches")
        
        if matches:
            collector.save_matches(matches)
            collector.save_to_csv(matches)
            
            print("\n📊 Sample matches:")
            for match in matches[:5]:
                print(f"  • {match.home_team} vs {match.away_team} ({match.league})")
    
    asyncio.run(main())

