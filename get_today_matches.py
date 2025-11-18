#!/usr/bin/env python3
"""
📅 HAE PÄIVÄN OTTELUT - 24H SISÄLLÄ
===================================

Hakee päivän ottelut seuraavista 5 lajista 24h sisällä:
1. Tennis (ATP/WTA)
2. Jalkapallo (Football)
3. Koripallo (Basketball)
4. Jääkiekko (Ice Hockey)
5. Jalkapallo (Soccer) - eri liigat

Käyttää olemassa olevia scraping-järjestelmiä.

Author: TennisBot Advanced Analytics
Version: 1.0.0
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path
from dataclasses import dataclass, asdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Match:
    """Ottelun tiedot"""
    match_id: str
    sport: str
    league: str
    home_team: str
    away_team: str
    start_time: str
    status: str  # scheduled, live, finished
    odds: Dict[str, float] = None
    source: str = ""
    
    def __post_init__(self):
        if self.odds is None:
            self.odds = {}


class TodayMatchesFetcher:
    """
    Hakee päivän ottelut 24h sisällä 5 lajista
    """
    
    def __init__(self):
        """Initialize fetcher"""
        self.matches: List[Match] = []
        self.sports = {
            'tennis': 'Tennis',
            'football': 'Jalkapallo',
            'basketball': 'Koripallo',
            'ice_hockey': 'Jääkiekko',
            'soccer': 'Jalkapallo (Soccer)'
        }
        
        logger.info("📅 Today Matches Fetcher initialized")
    
    async def fetch_all_matches(self) -> List[Match]:
        """
        Hae kaikki ottelut 24h sisällä kaikista 5 lajista
        """
        logger.info("🔍 Fetching today's matches from 5 sports...")
        
        # Calculate time range (now to +24 hours)
        now = datetime.now()
        end_time = now + timedelta(hours=24)
        
        all_matches = []
        
        # 1. TENNIS
        logger.info("🎾 Fetching Tennis matches...")
        tennis_matches = await self._fetch_tennis_matches(now, end_time)
        all_matches.extend(tennis_matches)
        logger.info(f"✅ Tennis: {len(tennis_matches)} matches")
        
        # 2. JALKAPALLO (FOOTBALL)
        logger.info("⚽ Fetching Football matches...")
        football_matches = await self._fetch_football_matches(now, end_time)
        all_matches.extend(football_matches)
        logger.info(f"✅ Football: {len(football_matches)} matches")
        
        # 3. KORIPALLO (BASKETBALL)
        logger.info("🏀 Fetching Basketball matches...")
        basketball_matches = await self._fetch_basketball_matches(now, end_time)
        all_matches.extend(basketball_matches)
        logger.info(f"✅ Basketball: {len(basketball_matches)} matches")
        
        # 4. JÄÄKIEKKO (ICE HOCKEY)
        logger.info("🏒 Fetching Ice Hockey matches...")
        ice_hockey_matches = await self._fetch_ice_hockey_matches(now, end_time)
        all_matches.extend(ice_hockey_matches)
        logger.info(f"✅ Ice Hockey: {len(ice_hockey_matches)} matches")
        
        # 5. SOCCER (ERI LIIGAT)
        logger.info("🌍 Fetching Soccer matches (various leagues)...")
        soccer_matches = await self._fetch_soccer_matches(now, end_time)
        all_matches.extend(soccer_matches)
        logger.info(f"✅ Soccer: {len(soccer_matches)} matches")
        
        # Remove duplicates
        unique_matches = self._deduplicate_matches(all_matches)
        
        # Sort by start time
        unique_matches.sort(key=lambda x: x.start_time)
        
        self.matches = unique_matches
        
        logger.info(f"📊 Total unique matches: {len(unique_matches)}")
        
        return unique_matches
    
    async def _fetch_tennis_matches(self, start_time: datetime, end_time: datetime) -> List[Match]:
        """Hae tennis-ottelut"""
        matches = []
        
        try:
            # Source 1: Live Betting Scraper
            from src.scrapers.live_betting_scraper import LiveBettingScraper
            
            scraper = LiveBettingScraper()
            live_matches = await scraper.scrape_live_matches()
            upcoming_matches = await scraper.scrape_upcoming_matches()
            
            all_tennis = live_matches + upcoming_matches
            
            for match_data in all_tennis:
                if match_data.sport.lower() == 'tennis':
                    match_time = datetime.fromisoformat(match_data.start_time) if match_data.start_time else datetime.now()
                    
                    if start_time <= match_time <= end_time:
                        match = Match(
                            match_id=f"tennis_{match_data.match_id}",
                            sport='tennis',
                            league=match_data.league or 'ATP/WTA',
                            home_team=match_data.home_team or match_data.player1 or 'Unknown',
                            away_team=match_data.away_team or match_data.player2 or 'Unknown',
                            start_time=match_data.start_time or match_time.isoformat(),
                            status=match_data.status or 'scheduled',
                            odds={
                                'home': match_data.home_odds,
                                'away': match_data.away_odds
                            } if match_data.home_odds else {},
                            source='live_scraper'
                        )
                        matches.append(match)
        
        except Exception as e:
            logger.error(f"❌ Error fetching tennis matches: {e}")
        
        try:
            # Source 2: Odds API
            from src.odds_api_integration import OddsAPIIntegration
            
            odds_api = OddsAPIIntegration()
            odds_data = await odds_api.get_live_odds(
                sports=['tennis_atp', 'tennis_wta'],
                markets=['h2h']
            )
            
            for odds in odds_data:
                commence_time = datetime.fromisoformat(odds.commence_time.replace('Z', '+00:00'))
                
                if start_time <= commence_time <= end_time:
                    match = Match(
                        match_id=f"odds_api_{odds.id}",
                        sport='tennis',
                        league=odds.sport_title or 'ATP/WTA',
                        home_team=odds.home_team,
                        away_team=odds.away_team,
                        start_time=odds.commence_time,
                        status='scheduled',
                        odds={
                            'home': odds.best_odds.get('h2h', {}).get('home', 0),
                            'away': odds.best_odds.get('h2h', {}).get('away', 0)
                        } if odds.best_odds else {},
                        source='odds_api'
                    )
                    matches.append(match)
        
        except Exception as e:
            logger.warning(f"⚠️ Odds API not available: {e}")
        
        return matches
    
    async def _fetch_football_matches(self, start_time: datetime, end_time: datetime) -> List[Match]:
        """Hae jalkapallo-ottelut"""
        matches = []
        
        try:
            # Source: Odds API
            from src.odds_api_integration import OddsAPIIntegration
            
            odds_api = OddsAPIIntegration()
            odds_data = await odds_api.get_live_odds(
                sports=['soccer_epl', 'soccer_spain_la_liga', 'soccer_germany_bundesliga', 
                       'soccer_italy_serie_a', 'soccer_france_ligue_one'],
                markets=['h2h']
            )
            
            for odds in odds_data:
                commence_time = datetime.fromisoformat(odds.commence_time.replace('Z', '+00:00'))
                
                if start_time <= commence_time <= end_time:
                    match = Match(
                        match_id=f"football_{odds.id}",
                        sport='football',
                        league=odds.sport_title or 'Football',
                        home_team=odds.home_team,
                        away_team=odds.away_team,
                        start_time=odds.commence_time,
                        status='scheduled',
                        odds={
                            'home': odds.best_odds.get('h2h', {}).get('home', 0),
                            'away': odds.best_odds.get('h2h', {}).get('away', 0),
                            'draw': odds.best_odds.get('h2h', {}).get('draw', 0)
                        } if odds.best_odds else {},
                        source='odds_api'
                    )
                    matches.append(match)
        
        except Exception as e:
            logger.warning(f"⚠️ Error fetching football matches: {e}")
        
        return matches
    
    async def _fetch_basketball_matches(self, start_time: datetime, end_time: datetime) -> List[Match]:
        """Hae koripallo-ottelut"""
        matches = []
        
        try:
            # Source: Odds API
            from src.odds_api_integration import OddsAPIIntegration
            
            odds_api = OddsAPIIntegration()
            odds_data = await odds_api.get_live_odds(
                sports=['basketball_nba'],
                markets=['h2h']
            )
            
            for odds in odds_data:
                commence_time = datetime.fromisoformat(odds.commence_time.replace('Z', '+00:00'))
                
                if start_time <= commence_time <= end_time:
                    match = Match(
                        match_id=f"basketball_{odds.id}",
                        sport='basketball',
                        league=odds.sport_title or 'NBA',
                        home_team=odds.home_team,
                        away_team=odds.away_team,
                        start_time=odds.commence_time,
                        status='scheduled',
                        odds={
                            'home': odds.best_odds.get('h2h', {}).get('home', 0),
                            'away': odds.best_odds.get('h2h', {}).get('away', 0)
                        } if odds.best_odds else {},
                        source='odds_api'
                    )
                    matches.append(match)
        
        except Exception as e:
            logger.warning(f"⚠️ Error fetching basketball matches: {e}")
        
        return matches
    
    async def _fetch_ice_hockey_matches(self, start_time: datetime, end_time: datetime) -> List[Match]:
        """Hae jääkiekko-ottelut"""
        matches = []
        
        try:
            # Source: Odds API
            from src.odds_api_integration import OddsAPIIntegration
            
            odds_api = OddsAPIIntegration()
            odds_data = await odds_api.get_live_odds(
                sports=['icehockey_nhl'],
                markets=['h2h']
            )
            
            for odds in odds_data:
                commence_time = datetime.fromisoformat(odds.commence_time.replace('Z', '+00:00'))
                
                if start_time <= commence_time <= end_time:
                    match = Match(
                        match_id=f"ice_hockey_{odds.id}",
                        sport='ice_hockey',
                        league=odds.sport_title or 'NHL',
                        home_team=odds.home_team,
                        away_team=odds.away_team,
                        start_time=odds.commence_time,
                        status='scheduled',
                        odds={
                            'home': odds.best_odds.get('h2h', {}).get('home', 0),
                            'away': odds.best_odds.get('h2h', {}).get('away', 0)
                        } if odds.best_odds else {},
                        source='odds_api'
                    )
                    matches.append(match)
        
        except Exception as e:
            logger.warning(f"⚠️ Error fetching ice hockey matches: {e}")
        
        return matches
    
    async def _fetch_soccer_matches(self, start_time: datetime, end_time: datetime) -> List[Match]:
        """Hae soccer-ottelut (eri liigat)"""
        matches = []
        
        try:
            # Source: Odds API - use different soccer leagues
            from src.odds_api_integration import OddsAPIIntegration
            
            odds_api = OddsAPIIntegration()
            
            # Fetch from multiple soccer leagues
            soccer_leagues = [
                'soccer_uefa_champs_league',
                'soccer_uefa_europa_league',
                'soccer_england_championship',
                'soccer_spain_segunda_division'
            ]
            
            for league in soccer_leagues:
                try:
                    odds_data = await odds_api.get_live_odds(
                        sports=[league],
                        markets=['h2h']
                    )
                    
                    for odds in odds_data:
                        commence_time = datetime.fromisoformat(odds.commence_time.replace('Z', '+00:00'))
                        
                        if start_time <= commence_time <= end_time:
                            match = Match(
                                match_id=f"soccer_{league}_{odds.id}",
                                sport='soccer',
                                league=odds.sport_title or league,
                                home_team=odds.home_team,
                                away_team=odds.away_team,
                                start_time=odds.commence_time,
                                status='scheduled',
                                odds={
                                    'home': odds.best_odds.get('h2h', {}).get('home', 0),
                                    'away': odds.best_odds.get('h2h', {}).get('away', 0),
                                    'draw': odds.best_odds.get('h2h', {}).get('draw', 0)
                                } if odds.best_odds else {},
                                source='odds_api'
                            )
                            matches.append(match)
                    
                    await asyncio.sleep(1)  # Rate limiting
                
                except Exception as e:
                    logger.warning(f"⚠️ Error fetching {league}: {e}")
                    continue
        
        except Exception as e:
            logger.warning(f"⚠️ Error fetching soccer matches: {e}")
        
        return matches
    
    def _deduplicate_matches(self, matches: List[Match]) -> List[Match]:
        """Poista duplikaatit"""
        seen = set()
        unique = []
        
        for match in matches:
            # Create unique key
            key = (
                match.sport,
                match.home_team.lower(),
                match.away_team.lower(),
                match.start_time[:10]  # Date only
            )
            
            if key not in seen:
                seen.add(key)
                unique.append(match)
        
        return unique
    
    def print_summary(self):
        """Tulosta yhteenveto"""
        print("\n" + "="*70)
        print("📅 PÄIVÄN OTTELUT - 24H SISÄLLÄ")
        print("="*70)
        
        # Group by sport
        by_sport = {}
        for match in self.matches:
            sport_name = self.sports.get(match.sport, match.sport)
            if sport_name not in by_sport:
                by_sport[sport_name] = []
            by_sport[sport_name].append(match)
        
        # Print summary
        total = len(self.matches)
        print(f"\n📊 YHTEENVETO:")
        print(f"   Kaikki ottelut: {total}")
        print(f"   Lajeja: {len(by_sport)}")
        
        print(f"\n📋 OTTELUT LAJITTAIN:")
        for sport_name, sport_matches in sorted(by_sport.items()):
            print(f"\n   {sport_name}: {len(sport_matches)} ottelua")
            for match in sport_matches[:5]:  # Show first 5
                start_time = datetime.fromisoformat(match.start_time.replace('Z', '+00:00'))
                time_str = start_time.strftime('%H:%M')
                print(f"      • {match.home_team} vs {match.away_team} - {time_str} ({match.league})")
            
            if len(sport_matches) > 5:
                print(f"      ... ja {len(sport_matches) - 5} muuta")
        
        print("\n" + "="*70)
    
    def save_to_json(self, filename: str = None):
        """Tallenna JSON-tiedostoon"""
        if filename is None:
            filename = f"today_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data_dir = Path('data/today_matches')
        data_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = data_dir / filename
        
        data = {
            'fetched_at': datetime.now().isoformat(),
            'total_matches': len(self.matches),
            'matches': [asdict(match) for match in self.matches]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"💾 Saved to {filepath}")
        return filepath
    
    def save_to_csv(self, filename: str = None):
        """Tallenna CSV-tiedostoon"""
        import pandas as pd
        
        if filename is None:
            filename = f"today_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        data_dir = Path('data/today_matches')
        data_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = data_dir / filename
        
        # Convert to DataFrame
        df_data = []
        for match in self.matches:
            df_data.append({
                'Sport': self.sports.get(match.sport, match.sport),
                'League': match.league,
                'Home Team': match.home_team,
                'Away Team': match.away_team,
                'Start Time': match.start_time,
                'Status': match.status,
                'Home Odds': match.odds.get('home', ''),
                'Away Odds': match.odds.get('away', ''),
                'Draw Odds': match.odds.get('draw', ''),
                'Source': match.source
            })
        
        df = pd.DataFrame(df_data)
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        logger.info(f"💾 Saved to {filepath}")
        return filepath


async def main():
    """Main function"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║  📅 HAE PÄIVÄN OTTELUT - 24H SISÄLLÄ                        ║
║  ==========================================================  ║
║                                                              ║
║  Hakee ottelut seuraavista 5 lajista:                      ║
║  1. 🎾 Tennis (ATP/WTA)                                     ║
║  2. ⚽ Jalkapallo (Football)                                ║
║  3. 🏀 Koripallo (Basketball)                               ║
║  4. 🏒 Jääkiekko (Ice Hockey)                               ║
║  5. 🌍 Jalkapallo (Soccer - eri liigat)                    ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    fetcher = TodayMatchesFetcher()
    
    try:
        # Fetch all matches
        matches = await fetcher.fetch_all_matches()
        
        # Print summary
        fetcher.print_summary()
        
        # Save to files
        json_file = fetcher.save_to_json()
        csv_file = fetcher.save_to_csv()
        
        print(f"\n✅ Valmis!")
        print(f"   📄 JSON: {json_file}")
        print(f"   📊 CSV: {csv_file}")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        print(f"\n❌ Virhe: {e}")


if __name__ == "__main__":
    asyncio.run(main())

