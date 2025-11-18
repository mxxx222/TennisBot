#!/usr/bin/env python3
"""
🔗 SMART VALUE DETECTOR - DATA INTEGRATION
==========================================

Integroi Smart Value Detector olemassa oleviin data-lähteisiin:
- The Odds API
- Live Betting Scraper
- Multi-Sport Scraper
- Betfury Integration

EI TARVITSE UUSIA API:ITA - käyttää olemassa olevia!

Author: TennisBot Advanced Analytics
Version: 1.0.0
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from src.smart_value_detector import MatchData, PlayerStats
from src.high_roi_scraper import HighROIScraper, BookmakerOdds

logger = logging.getLogger(__name__)


class SVDDataIntegration:
    """
    Integroi SVD olemassa oleviin data-lähteisiin
    """
    
    def __init__(self):
        """Initialize data integration"""
        self.odds_api = None
        self.live_scraper = None
        self.multi_sport_scraper = None
        
        # Try to import existing integrations
        self._load_integrations()
        
        logger.info("🔗 SVD Data Integration initialized")
    
    def _load_integrations(self):
        """Load existing data source integrations"""
        try:
            from src.odds_api_integration import OddsAPIIntegration
            self.odds_api = OddsAPIIntegration()
            logger.info("✅ The Odds API loaded")
        except Exception as e:
            logger.warning(f"⚠️ Odds API not available: {e}")
        
        try:
            from src.scrapers.live_betting_scraper import LiveBettingScraper
            self.live_scraper = LiveBettingScraper()
            logger.info("✅ Live Betting Scraper loaded")
        except Exception as e:
            logger.warning(f"⚠️ Live Betting Scraper not available: {e}")
        
        try:
            from src.multi_sport_prematch_scraper import MultiSportPrematchScraper
            self.multi_sport_scraper = MultiSportPrematchScraper()
            logger.info("✅ Multi-Sport Scraper loaded")
        except Exception as e:
            logger.warning(f"⚠️ Multi-Sport Scraper not available: {e}")
    
    async def get_tennis_matches(self) -> List[MatchData]:
        """
        Hae tennis-ottelut kaikista saatavilla olevista lähteistä
        """
        matches = []
        
        # Source 1: The Odds API
        if self.odds_api:
            try:
                odds_data = await self.odds_api.get_live_odds(
                    sports=['tennis_atp', 'tennis_wta'],
                    markets=['h2h']
                )
                
                for odds in odds_data:
                    match = self._convert_odds_api_to_match_data(odds)
                    if match:
                        matches.append(match)
                
                logger.info(f"✅ Odds API: {len(odds_data)} matches")
            except Exception as e:
                logger.error(f"❌ Odds API error: {e}")
        
        # Source 2: Live Betting Scraper
        if self.live_scraper:
            try:
                live_matches = await self.live_scraper.scrape_live_matches()
                upcoming_matches = await self.live_scraper.scrape_upcoming_matches()
                
                all_scraped = live_matches + upcoming_matches
                
                for scraped_match in all_scraped:
                    match = self._convert_scraped_to_match_data(scraped_match)
                    if match:
                        matches.append(match)
                
                logger.info(f"✅ Live Scraper: {len(all_scraped)} matches")
            except Exception as e:
                logger.error(f"❌ Live Scraper error: {e}")
        
        # Source 3: Multi-Sport Scraper
        if self.multi_sport_scraper:
            try:
                scraped_matches = await self.multi_sport_scraper.scrape_tennis_matches()
                
                for scraped_match in scraped_matches:
                    match = self._convert_scraped_to_match_data(scraped_match)
                    if match:
                        matches.append(match)
                
                logger.info(f"✅ Multi-Sport Scraper: {len(scraped_matches)} matches")
            except Exception as e:
                logger.error(f"❌ Multi-Sport Scraper error: {e}")
        
        # Remove duplicates
        unique_matches = self._deduplicate_matches(matches)
        
        logger.info(f"📊 Total unique matches: {len(unique_matches)}")
        
        return unique_matches
    
    def _convert_odds_api_to_match_data(self, odds_data: Any) -> Optional[MatchData]:
        """
        Muunna Odds API data MatchData-muotoon
        """
        try:
            # Extract player names from teams
            # Odds API uses 'home_team' and 'away_team' for tennis
            player1_name = odds_data.home_team
            player2_name = odds_data.away_team
            
            # Create PlayerStats (simplified - would need real data)
            player1 = PlayerStats(
                id=f"p1_{player1_name.replace(' ', '_')}",
                name=player1_name,
                elo=1500.0,  # Would fetch from real data
                surface_stats={'hard': 0.50, 'clay': 0.50, 'grass': 0.50},
                recent_form=[0.5] * 5
            )
            
            player2 = PlayerStats(
                id=f"p2_{player2_name.replace(' ', '_')}",
                name=player2_name,
                elo=1500.0,  # Would fetch from real data
                surface_stats={'hard': 0.50, 'clay': 0.50, 'grass': 0.50},
                recent_form=[0.5] * 5
            )
            
            # Extract odds
            market_odds = {}
            if odds_data.bookmakers:
                # Get best odds
                best_home = max([b['markets'][0]['outcomes'][0]['price'] 
                               for b in odds_data.bookmakers 
                               if b['markets'] and b['markets'][0]['outcomes']])
                best_away = max([b['markets'][0]['outcomes'][1]['price'] 
                               for b in odds_data.bookmakers 
                               if b['markets'] and b['markets'][0]['outcomes']])
                
                market_odds = {
                    'player1': best_home,
                    'player2': best_away,
                    'bookmaker': odds_data.bookmakers[0]['key'] if odds_data.bookmakers else 'unknown'
                }
            
            match = MatchData(
                match_id=f"odds_api_{odds_data.id}",
                player1=player1,
                player2=player2,
                surface="hard",  # Would detect from tournament data
                tournament=odds_data.sport_title or "Unknown",
                round="Unknown",
                date=datetime.fromisoformat(odds_data.commence_time) if hasattr(odds_data, 'commence_time') else datetime.now(),
                market_odds=market_odds
            )
            
            return match
            
        except Exception as e:
            logger.error(f"❌ Error converting Odds API data: {e}")
            return None
    
    def _convert_scraped_to_match_data(self, scraped_match: Any) -> Optional[MatchData]:
        """
        Muunna scraped match data MatchData-muotoon
        """
        try:
            # Extract data from scraped match
            # This depends on the actual structure of scraped_match
            if hasattr(scraped_match, 'home_team'):
                player1_name = scraped_match.home_team
                player2_name = scraped_match.away_team
            elif isinstance(scraped_match, dict):
                player1_name = scraped_match.get('home_team', scraped_match.get('player1', 'Unknown'))
                player2_name = scraped_match.get('away_team', scraped_match.get('player2', 'Unknown'))
            else:
                return None
            
            # Create PlayerStats
            player1 = PlayerStats(
                id=f"p1_{player1_name.replace(' ', '_')}",
                name=player1_name,
                elo=1500.0,
                surface_stats={'hard': 0.50, 'clay': 0.50, 'grass': 0.50},
                recent_form=[0.5] * 5
            )
            
            player2 = PlayerStats(
                id=f"p2_{player2_name.replace(' ', '_')}",
                name=player2_name,
                elo=1500.0,
                surface_stats={'hard': 0.50, 'clay': 0.50, 'grass': 0.50},
                recent_form=[0.5] * 5
            )
            
            # Extract odds
            market_odds = {}
            if hasattr(scraped_match, 'home_odds'):
                market_odds = {
                    'player1': scraped_match.home_odds,
                    'player2': scraped_match.away_odds,
                    'bookmaker': getattr(scraped_match, 'source', 'scraper')
                }
            elif isinstance(scraped_match, dict):
                market_odds = {
                    'player1': scraped_match.get('home_odds', scraped_match.get('player1_odds')),
                    'player2': scraped_match.get('away_odds', scraped_match.get('player2_odds')),
                    'bookmaker': scraped_match.get('source', 'scraper')
                }
            
            match = MatchData(
                match_id=f"scraped_{hash(str(scraped_match))}",
                player1=player1,
                player2=player2,
                surface="hard",
                tournament=getattr(scraped_match, 'league', 'Unknown') if hasattr(scraped_match, 'league') else scraped_match.get('league', 'Unknown') if isinstance(scraped_match, dict) else 'Unknown',
                round="Unknown",
                date=datetime.now(),
                market_odds=market_odds if market_odds else None
            )
            
            return match
            
        except Exception as e:
            logger.error(f"❌ Error converting scraped data: {e}")
            return None
    
    def _deduplicate_matches(self, matches: List[MatchData]) -> List[MatchData]:
        """Remove duplicate matches"""
        seen = set()
        unique = []
        
        for match in matches:
            # Create unique key from player names
            key = tuple(sorted([match.player1.name.lower(), match.player2.name.lower()]))
            
            if key not in seen:
                seen.add(key)
                unique.append(match)
        
        return unique
    
    async def enrich_match_data(self, match: MatchData) -> MatchData:
        """
        Rikastuta match data lisätiedoilla (ELO, H2H, Surface stats)
        Tämä käyttäisi olemassa olevia scraping-järjestelmiä
        """
        # TODO: Implement enrichment using existing scrapers
        # - Fetch ELO ratings
        # - Fetch H2H records
        # - Fetch surface-specific stats
        # - Fetch recent form
        
        return match
    
    async def get_odds_from_multiple_sources(self, match: MatchData) -> Dict[str, BookmakerOdds]:
        """
        Hae kertoimet useista lähteistä käyttäen olemassa olevia järjestelmiä
        """
        odds_sources = {}
        
        # Use High ROI Scraper
        scraper = HighROIScraper()
        
        match_ids = [match.match_id]
        all_odds = await scraper.scrape_all_bookmakers(match_ids)
        
        if match.match_id in all_odds:
            odds_list = all_odds[match.match_id]
            for odds in odds_list:
                odds_sources[odds.bookmaker] = odds
        
        # Also use Odds API if available
        if self.odds_api:
            try:
                # Would need to match match to Odds API format
                # This is simplified
                pass
            except Exception as e:
                logger.error(f"❌ Error getting Odds API odds: {e}")
        
        return odds_sources


if __name__ == "__main__":
    print("🔗 SVD Data Integration - Test")
    print("=" * 50)
    
    integration = SVDDataIntegration()
    
    async def test():
        matches = await integration.get_tennis_matches()
        print(f"✅ Found {len(matches)} matches")
        
        if matches:
            print("\n📊 Sample matches:")
            for match in matches[:3]:
                print(f"  - {match.player1.name} vs {match.player2.name}")
                if match.market_odds:
                    print(f"    Odds: {match.market_odds}")
    
    asyncio.run(test())

