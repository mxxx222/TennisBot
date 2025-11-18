#!/usr/bin/env python3
"""
Soccer Screening System - Adapted from Tennis ITF System

Applies your proven betting edge (+17.81% ROI) to lower-tier soccer leagues:
- Championship, League 1, League 2 (similar to ITF level)
- Same 1.30-1.80 odds filtering
- Same Kelly Criterion bet sizing
- Same Telegram alerts and automation

Usage:
    python soccer_screener.py [--test] [--bankroll AMOUNT]
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

from config.soccer_screening_config import SoccerScreeningConfig, TIER_1_LEAGUES, TIER_2_LEAGUES, TIER_3_LEAGUES
from utils.bet_calculator import BetCalculator, BettingOpportunity
from utils.notifiers import NotificationManager
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('soccer_screener.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class SoccerMatch:
    """Represents a soccer match with odds data"""
    
    def __init__(self, match_data: Dict, league: str):
        self.id = match_data.get('id', '')
        self.home_team = match_data.get('home_team', '')
        self.away_team = match_data.get('away_team', '')
        self.commence_time = datetime.fromisoformat(
            match_data['commence_time'].replace('Z', '+00:00')
        )
        self.league = league
        self.bookmakers = match_data.get('bookmakers', [])
    
    def get_best_odds(self) -> tuple[float, float]:
        """Get best available odds for home and away teams"""
        best_home = 0.0
        best_away = 0.0
        
        for bookmaker in self.bookmakers:
            markets = bookmaker.get('markets', [])
            for market in markets:
                if market.get('key') != 'h2h':
                    continue
                    
                outcomes = market.get('outcomes', [])
                for outcome in outcomes:
                    if outcome.get('name') == self.home_team:
                        best_home = max(best_home, outcome.get('price', 0))
                    elif outcome.get('name') == self.away_team:
                        best_away = max(best_away, outcome.get('price', 0))
        
        return best_home, best_away
    
    def get_league_tier(self) -> int:
        """Get league tier (1=best, 3=most inefficient)"""
        if self.league in TIER_1_LEAGUES:
            return 1
        elif self.league in TIER_2_LEAGUES:
            return 2
        elif self.league in TIER_3_LEAGUES:
            return 3
        return 2  # Default to tier 2

class SoccerScreener:
    """Main soccer screening system"""
    
    def __init__(self, bankroll: float = None, test_mode: bool = False):
        self.config = SoccerScreeningConfig()
        self.test_mode = test_mode
        
        # Initialize components (reuse from tennis system)
        self.bet_calculator = BetCalculator(bankroll)
        self.notification_manager = NotificationManager()
        
        logger.info(f"Initialized Soccer Screener (test_mode={test_mode})")
        logger.info(f"Target leagues: {len(self.config.TARGET_LEAGUES)}")
        logger.info(f"Bankroll: ${self.bet_calculator.bankroll:.2f}")
    
    async def fetch_league_matches(self, session: aiohttp.ClientSession, league: str) -> List[SoccerMatch]:
        """Fetch matches for a specific league"""
        url = f"{self.config.ODDS_API_BASE_URL}/sports/{league}/odds"
        
        params = {
            'apiKey': self.config.ODDS_API_KEY,
            'regions': self.config.REGIONS,
            'markets': self.config.MARKETS,
            'oddsFormat': self.config.ODDS_FORMAT,
            'dateFormat': self.config.DATE_FORMAT,
        }
        
        try:
            await asyncio.sleep(self.config.REQUEST_DELAY)  # Rate limiting
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    matches = [SoccerMatch(match_data, league) for match_data in data]
                    logger.info(f"Fetched {len(matches)} matches from {league}")
                    return matches
                else:
                    logger.warning(f"Failed to fetch {league}: status {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching {league}: {e}")
            return []
    
    async def fetch_all_matches(self) -> List[SoccerMatch]:
        """Fetch matches from all target leagues"""
        all_matches = []
        
        async with aiohttp.ClientSession() as session:
            # Fetch matches from all target leagues
            tasks = [
                self.fetch_league_matches(session, league) 
                for league in self.config.TARGET_LEAGUES
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_matches.extend(result)
                else:
                    logger.error(f"League fetch failed: {result}")
        
        logger.info(f"Total matches fetched: {len(all_matches)}")
        return all_matches
    
    def filter_and_size_opportunities(self, matches: List[SoccerMatch]) -> List[BettingOpportunity]:
        """Filter matches and calculate bet sizes (adapted from tennis system)"""
        opportunities = []
        
        for match in matches:
            home_odds, away_odds = match.get_best_odds()
            
            # Check home team opportunity
            if self.config.MIN_ODDS <= home_odds <= self.config.MAX_ODDS:
                stake, confidence, edge = self.bet_calculator.calculate_stake(home_odds)
                if stake > 0:
                    # Adjust confidence based on league tier
                    tier = match.get_league_tier()
                    if tier == 3:  # Lower tier = higher confidence in inefficiencies
                        confidence = self._boost_confidence(confidence)
                    
                    opportunities.append(BettingOpportunity(
                        match_id=match.id,
                        player=match.home_team,
                        opponent=match.away_team,
                        odds=home_odds,
                        commence_time=match.commence_time,
                        tournament=f"Soccer - {match.league}",
                        side='home',
                        recommended_stake=stake,
                        confidence=confidence,
                        edge_estimate=edge,
                        kelly_fraction=self.bet_calculator.calculate_kelly_fraction(
                            home_odds, self.bet_calculator.estimate_true_probability(home_odds)
                        )
                    ))
            
            # Check away team opportunity
            if self.config.MIN_ODDS <= away_odds <= self.config.MAX_ODDS:
                stake, confidence, edge = self.bet_calculator.calculate_stake(away_odds)
                if stake > 0:
                    tier = match.get_league_tier()
                    if tier == 3:
                        confidence = self._boost_confidence(confidence)
                    
                    opportunities.append(BettingOpportunity(
                        match_id=match.id,
                        player=match.away_team,
                        opponent=match.home_team,
                        odds=away_odds,
                        commence_time=match.commence_time,
                        tournament=f"Soccer - {match.league}",
                        side='away',
                        recommended_stake=stake,
                        confidence=confidence,
                        edge_estimate=edge,
                        kelly_fraction=self.bet_calculator.calculate_kelly_fraction(
                            away_odds, self.bet_calculator.estimate_true_probability(away_odds)
                        )
                    ))
        
        # Sort by edge potential and league tier
        opportunities.sort(key=lambda x: (x.edge_estimate, self._get_tier_score(x.tournament)), reverse=True)
        
        # Limit to max daily picks
        top_opportunities = opportunities[:self.config.MAX_DAILY_PICKS]
        
        logger.info(f"Found {len(opportunities)} total opportunities, "
                   f"selected top {len(top_opportunities)} for today")
        
        return top_opportunities
    
    def _boost_confidence(self, confidence: str) -> str:
        """Boost confidence for lower-tier leagues (more inefficient markets)"""
        if confidence == "Low":
            return "Medium"
        elif confidence == "Medium":
            return "High"
        return confidence
    
    def _get_tier_score(self, tournament: str) -> int:
        """Get scoring bonus for league tier"""
        if any(tier1 in tournament for tier1 in TIER_1_LEAGUES):
            return 1
        elif any(tier2 in tournament for tier2 in TIER_2_LEAGUES):
            return 2
        elif any(tier3 in tournament for tier3 in TIER_3_LEAGUES):
            return 3
        return 2
    
    async def run_screening(self) -> Dict:
        """Run the complete soccer screening process"""
        logger.info("Starting Soccer screening process...")
        
        try:
            # Step 1: Validate configuration
            if not self.config.validate_config():
                raise ValueError("Invalid configuration - check API keys and credentials")
            
            # Step 2: Fetch soccer matches
            logger.info("Fetching soccer matches from target leagues...")
            matches = await self.fetch_all_matches()
            
            if not matches:
                logger.warning("No soccer matches found")
                return self._create_empty_result()
            
            # Step 3: Filter and calculate bet sizes
            logger.info("Analyzing opportunities and calculating bet sizes...")
            opportunities = self.filter_and_size_opportunities(matches)
            
            if not opportunities:
                logger.info("No qualified betting opportunities found today")
                return self._create_empty_result()
            
            logger.info(f"Found {len(opportunities)} qualified opportunities")
            
            # Step 4: Generate summary
            summary = self.bet_calculator.get_betting_summary(opportunities)
            
            # Step 5: Send notifications (unless in test mode)
            notification_results = {}
            if not self.test_mode:
                logger.info("Sending notifications...")
                notification_results = await self.notification_manager.send_opportunities(
                    opportunities, summary
                )
            else:
                logger.info("Test mode - skipping notifications")
                notification_results = {
                    'telegram_alerts': True,
                    'telegram_summary': True, 
                    'notion_logging': True
                }
            
            # Step 6: Compile results
            result = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'matches_found': len(matches),
                'opportunities_found': len(opportunities),
                'opportunities': [self._opportunity_to_dict(opp) for opp in opportunities],
                'summary': summary,
                'notifications': notification_results,
                'test_mode': self.test_mode
            }
            
            logger.info("Soccer screening process completed successfully")
            self._log_summary(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Soccer screening process failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'test_mode': self.test_mode
            }
    
    def _create_empty_result(self) -> Dict:
        """Create result structure for when no opportunities are found"""
        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'matches_found': 0,
            'opportunities_found': 0,
            'opportunities': [],
            'summary': self.bet_calculator.get_betting_summary([]),
            'notifications': {'telegram_alerts': True, 'telegram_summary': True, 'notion_logging': True},
            'test_mode': self.test_mode
        }
    
    def _opportunity_to_dict(self, opp: BettingOpportunity) -> Dict:
        """Convert BettingOpportunity to dictionary"""
        return {
            'match_id': opp.match_id,
            'player': opp.player,
            'opponent': opp.opponent,
            'odds': opp.odds,
            'commence_time': opp.commence_time.isoformat(),
            'tournament': opp.tournament,
            'side': opp.side,
            'recommended_stake': opp.recommended_stake,
            'confidence': opp.confidence,
            'edge_estimate': opp.edge_estimate,
            'kelly_fraction': opp.kelly_fraction
        }
    
    def _log_summary(self, result: Dict):
        """Log summary of screening results"""
        if result['opportunities_found'] > 0:
            logger.info("=== SOCCER SCREENING SUMMARY ===")
            logger.info(f"Opportunities found: {result['opportunities_found']}")
            logger.info(f"Total recommended stake: ${result['summary']['total_stake']}")
            logger.info(f"Average odds: {result['summary']['avg_odds']}")
            logger.info(f"Average edge: +{result['summary']['avg_edge']}%")
            
            logger.info("--- OPPORTUNITIES ---")
            for i, opp in enumerate(result['opportunities'], 1):
                logger.info(f"{i}. {opp['player']} @ {opp['odds']} "
                           f"(${opp['recommended_stake']}, {opp['confidence']})")
        else:
            logger.info("No qualified opportunities found today")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Soccer Screening System')
    parser.add_argument('--test', action='store_true', 
                       help='Run in test mode (no notifications sent)')
    parser.add_argument('--bankroll', type=float, 
                       help='Custom bankroll amount (default: $1000)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize screener
    screener = SoccerScreener(
        bankroll=args.bankroll,
        test_mode=args.test
    )
    
    # Run screening
    try:
        result = asyncio.run(screener.run_screening())
        
        if result['success']:
            print(f"\n✅ Soccer screening completed successfully!")
            print(f"Found {result['opportunities_found']} opportunities")
            
            if result['opportunities_found'] > 0:
                print(f"Total stake: ${result['summary']['total_stake']}")
                print(f"Average edge: +{result['summary']['avg_edge']}%")
                
                if not args.test:
                    notifications = result['notifications']
                    print(f"Telegram alerts: {'✅' if notifications['telegram_alerts'] else '❌'}")
                else:
                    print("(Test mode - no notifications sent)")
            
            sys.exit(0)
        else:
            print(f"\n❌ Soccer screening failed: {result['error']}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Screening interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        logger.exception("Unexpected error in main")
        sys.exit(1)

if __name__ == "__main__":
    main()
