#!/usr/bin/env python3
"""
💰 HIGH ROI SCRAPER - OPTIMOITU KERTOIMIEN KERÄYS
==================================================

Erikoistunut scraper joka kerää kertoimia useista vedonvälittäjistä
korkeimman ROI:n saavuttamiseksi.

Keskeiset ominaisuudet:
- Useiden vedonvälittäjien kerrointen aggregaatio
- Arbitraasi-mahdollisuuksien tunnistus
- Reaaliaikainen kerroinmuutosten seuranta
- Likviditeetin analyysi

Author: TennisBot Advanced Analytics
Version: 1.0.0
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import json
import logging
from pathlib import Path
import time
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class BookmakerOdds:
    """Vedonvälittäjän kertoimet"""
    bookmaker: str
    match_id: str
    player1_odds: float
    player2_odds: float
    draw_odds: Optional[float] = None
    timestamp: str = None
    liquidity: Optional[float] = None  # Likviditeetti
    market_type: str = "match_winner"
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class AggregatedOdds:
    """Aggregoitu kertoimet useista lähteistä"""
    match_id: str
    match_name: str
    best_player1_odds: float
    best_player1_bookmaker: str
    best_player2_odds: float
    best_player2_bookmaker: str
    arbitrage_multiplier: float
    arbitrage_profit_pct: float
    has_arbitrage: bool
    odds_sources: List[BookmakerOdds]
    timestamp: str


class HighROIScraper:
    """
    Korkean ROI:n saavuttamiseksi optimoitu scraper
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize High ROI Scraper
        
        Args:
            config: Konfiguraatio
        """
        self.config = config or {}
        
        # Bookmaker sources (public APIs or scraping targets)
        self.bookmakers = self.config.get('bookmakers', [
            'bet365',
            'betfair',
            'pinnacle',
            'smarkets',
            'unibet',
            'william_hill',
            'ladbrokes'
        ])
        
        # Rate limiting
        self.request_delay = self.config.get('request_delay', 2.0)
        self.max_concurrent = self.config.get('max_concurrent', 5)
        
        # Data storage
        self.data_dir = Path('data/odds')
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache
        self.odds_cache: Dict[str, List[BookmakerOdds]] = {}
        self.cache_ttl = timedelta(minutes=5)
        
        logger.info(f"💰 High ROI Scraper initialized with {len(self.bookmakers)} bookmakers")
    
    async def scrape_all_bookmakers(self, match_ids: List[str]) -> Dict[str, List[BookmakerOdds]]:
        """
        Scrape kertoimet kaikista vedonvälittäjistä
        
        Args:
            match_ids: Lista ottelun ID:itä
            
        Returns:
            Dictionary: {match_id: [BookmakerOdds]}
        """
        logger.info(f"🔍 Scraping odds for {len(match_ids)} matches from {len(self.bookmakers)} bookmakers")
        
        all_odds = defaultdict(list)
        
        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Scrape each bookmaker
        tasks = []
        for bookmaker in self.bookmakers:
            for match_id in match_ids:
                task = self._scrape_bookmaker_odds(semaphore, bookmaker, match_id)
                tasks.append(task)
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error scraping: {result}")
                continue
            
            if result:
                match_id = result.match_id
                all_odds[match_id].append(result)
        
        logger.info(f"✅ Scraped odds for {len(all_odds)} matches")
        
        return dict(all_odds)
    
    async def _scrape_bookmaker_odds(self, semaphore: asyncio.Semaphore,
                                     bookmaker: str, match_id: str) -> Optional[BookmakerOdds]:
        """
        Scrape kertoimet yhdeltä vedonvälittäjältä
        
        NOTE: Tämä on simulaatio. Todellisessa toteutuksessa tämä
        tekisi HTTP-pyyntöjä tai käyttäisi API:a.
        """
        async with semaphore:
            try:
                # Simulate API call delay
                await asyncio.sleep(self.request_delay)
                
                # TODO: Replace with actual scraping/API call
                # For now, simulate odds
                odds = self._simulate_odds(bookmaker, match_id)
                
                if odds:
                    logger.debug(f"✅ Got odds from {bookmaker} for match {match_id}")
                    return odds
                
            except Exception as e:
                logger.error(f"❌ Error scraping {bookmaker} for {match_id}: {e}")
            
            return None
    
    def _simulate_odds(self, bookmaker: str, match_id: str) -> Optional[BookmakerOdds]:
        """
        Simulate odds (replace with real scraping)
        """
        # This would be replaced with actual scraping logic
        # For now, return simulated data
        
        import random
        
        # Base odds with some variation
        base_player1 = 2.0 + random.uniform(-0.3, 0.3)
        base_player2 = 1.8 + random.uniform(-0.3, 0.3)
        
        # Bookmaker-specific adjustments
        adjustments = {
            'bet365': {'p1': 0.95, 'p2': 0.95},
            'betfair': {'p1': 1.0, 'p2': 1.0},
            'pinnacle': {'p1': 1.02, 'p2': 1.02},  # Sharp bookmaker
            'smarkets': {'p1': 0.98, 'p2': 0.98},
            'unibet': {'p1': 0.97, 'p2': 0.97},
        }
        
        adj = adjustments.get(bookmaker, {'p1': 1.0, 'p2': 1.0})
        
        return BookmakerOdds(
            bookmaker=bookmaker,
            match_id=match_id,
            player1_odds=base_player1 * adj['p1'],
            player2_odds=base_player2 * adj['p2'],
            liquidity=random.uniform(1000, 10000)
        )
    
    def aggregate_odds(self, match_id: str, 
                       odds_list: List[BookmakerOdds]) -> AggregatedOdds:
        """
        Agregoi kertoimet useista vedonvälittäjistä
        """
        if not odds_list:
            raise ValueError(f"No odds found for match {match_id}")
        
        # Find best odds for each player
        best_player1 = max(odds_list, key=lambda x: x.player1_odds)
        best_player2 = max(odds_list, key=lambda x: x.player2_odds)
        
        # Calculate arbitrage multiplier
        arb_multiplier = 1 / (1/best_player1.player1_odds + 1/best_player2.player2_odds)
        arb_profit_pct = (arb_multiplier - 1) * 100
        
        # Check if arbitrage exists (>1% profit)
        has_arbitrage = arb_profit_pct > 1.0
        
        return AggregatedOdds(
            match_id=match_id,
            match_name=f"Match {match_id}",  # Would get from match data
            best_player1_odds=best_player1.player1_odds,
            best_player1_bookmaker=best_player1.bookmaker,
            best_player2_odds=best_player2.player2_odds,
            best_player2_bookmaker=best_player2.bookmaker,
            arbitrage_multiplier=arb_multiplier,
            arbitrage_profit_pct=arb_profit_pct,
            has_arbitrage=has_arbitrage,
            odds_sources=odds_list,
            timestamp=datetime.now().isoformat()
        )
    
    def find_arbitrage_opportunities(self, aggregated_odds: List[AggregatedOdds]) -> List[AggregatedOdds]:
        """
        Etsi arbitraasi-mahdollisuudet
        """
        arbitrage_opps = [
            agg for agg in aggregated_odds
            if agg.has_arbitrage
        ]
        
        # Sort by profit percentage
        arbitrage_opps.sort(key=lambda x: x.arbitrage_profit_pct, reverse=True)
        
        logger.info(f"💰 Found {len(arbitrage_opps)} arbitrage opportunities")
        
        return arbitrage_opps
    
    def track_odds_movement(self, match_id: str, 
                           current_odds: AggregatedOdds,
                           historical_odds: List[AggregatedOdds]) -> Dict[str, Any]:
        """
        Seuraa kerroinmuutoksia
        
        Hyödyllinen tunnistamaan:
        - Sharp money (ammattilaisten raha)
        - Line movement
        - Value opportunities
        """
        if not historical_odds:
            return {
                'movement_detected': False,
                'trend': 'no_data'
            }
        
        # Compare with most recent historical
        latest_historical = historical_odds[-1]
        
        # Calculate movement
        player1_movement = current_odds.best_player1_odds - latest_historical.best_player1_odds
        player2_movement = current_odds.best_player2_odds - latest_historical.best_player2_odds
        
        # Determine trend
        if abs(player1_movement) > 0.1 or abs(player2_movement) > 0.1:
            movement_detected = True
            
            if player1_movement < 0:
                trend = 'player1_shortening'  # Odds shortening = more likely
            elif player1_movement > 0:
                trend = 'player1_lengthening'  # Odds lengthening = less likely
            else:
                trend = 'stable'
        else:
            movement_detected = False
            trend = 'stable'
        
        return {
            'movement_detected': movement_detected,
            'trend': trend,
            'player1_movement': player1_movement,
            'player2_movement': player2_movement,
            'movement_pct': {
                'player1': (player1_movement / latest_historical.best_player1_odds) * 100,
                'player2': (player2_movement / latest_historical.best_player2_odds) * 100
            }
        }
    
    def calculate_value_score(self, aggregated_odds: AggregatedOdds,
                            true_probability: float) -> Dict[str, Any]:
        """
        Laske arvoscore kertoimille
        
        Ottaa huomioon:
        - Edge (true prob vs market prob)
        - Likviditeetti
        - Arbitraasi-mahdollisuus
        - Kerroinmuutokset
        """
        # Market probability from best odds
        market_prob_player1 = 1 / aggregated_odds.best_player1_odds
        market_prob_player2 = 1 / aggregated_odds.best_player2_odds
        
        # Edge
        edge_player1 = true_probability - market_prob_player1
        edge_player2 = (1 - true_probability) - market_prob_player2
        
        # Expected value
        ev_player1 = (true_probability * aggregated_odds.best_player1_odds) - 1
        ev_player2 = ((1 - true_probability) * aggregated_odds.best_player2_odds) - 1
        
        # Value score (weighted)
        value_score = max(ev_player1, ev_player2) * 100
        
        # Arbitrage bonus
        if aggregated_odds.has_arbitrage:
            value_score += aggregated_odds.arbitrage_profit_pct * 0.5
        
        return {
            'value_score': value_score,
            'edge_player1': edge_player1,
            'edge_player2': edge_player2,
            'ev_player1': ev_player1,
            'ev_player2': ev_player2,
            'best_value_player': 'player1' if ev_player1 > ev_player2 else 'player2',
            'arbitrage_bonus': aggregated_odds.arbitrage_profit_pct if aggregated_odds.has_arbitrage else 0
        }
    
    async def continuous_monitoring(self, match_ids: List[str], 
                                   interval_seconds: int = 60):
        """
        Jatkuva seuranta kertoimien muutoksille
        """
        logger.info(f"🔄 Starting continuous monitoring for {len(match_ids)} matches")
        
        historical_data: Dict[str, List[AggregatedOdds]] = defaultdict(list)
        
        while True:
            try:
                # Scrape current odds
                all_odds = await self.scrape_all_bookmakers(match_ids)
                
                # Aggregate for each match
                for match_id, odds_list in all_odds.items():
                    if not odds_list:
                        continue
                    
                    aggregated = self.aggregate_odds(match_id, odds_list)
                    historical_data[match_id].append(aggregated)
                    
                    # Track movement
                    movement = self.track_odds_movement(
                        match_id,
                        aggregated,
                        historical_data[match_id][:-1]  # Exclude current
                    )
                    
                    # Log significant movements
                    if movement['movement_detected']:
                        logger.info(f"📊 Odds movement detected for {match_id}: {movement['trend']}")
                
                # Wait before next iteration
                await asyncio.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("🛑 Stopping continuous monitoring")
                break
            except Exception as e:
                logger.error(f"❌ Error in continuous monitoring: {e}")
                await asyncio.sleep(interval_seconds)
    
    def save_odds_data(self, aggregated_odds: List[AggregatedOdds], 
                      filename: Optional[str] = None):
        """Save odds data to JSON"""
        if filename is None:
            filename = f"odds_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.data_dir / filename
        
        data = [asdict(agg) for agg in aggregated_odds]
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"💾 Saved odds data to {filepath}")


if __name__ == "__main__":
    # Example usage
    print("💰 High ROI Scraper - Test")
    print("=" * 50)
    
    scraper = HighROIScraper()
    
    # Test with sample match IDs
    match_ids = ['match1', 'match2', 'match3']
    
    async def test():
        # Scrape odds
        all_odds = await scraper.scrape_all_bookmakers(match_ids)
        
        # Aggregate
        aggregated = []
        for match_id, odds_list in all_odds.items():
            if odds_list:
                agg = scraper.aggregate_odds(match_id, odds_list)
                aggregated.append(agg)
                
                print(f"\nMatch: {agg.match_name}")
                print(f"Best Player1 Odds: {agg.best_player1_odds:.2f} ({agg.best_player1_bookmaker})")
                print(f"Best Player2 Odds: {agg.best_player2_odds:.2f} ({agg.best_player2_bookmaker})")
                print(f"Arbitrage Multiplier: {agg.arbitrage_multiplier:.4f}")
                print(f"Arbitrage Profit: {agg.arbitrage_profit_pct:.2f}%")
                print(f"Has Arbitrage: {agg.has_arbitrage}")
        
        # Find arbitrage
        arb_opps = scraper.find_arbitrage_opportunities(aggregated)
        print(f"\n💰 Found {len(arb_opps)} arbitrage opportunities")
    
    asyncio.run(test())

