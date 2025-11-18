#!/usr/bin/env python3
"""
Tennis ITF Screening System - Main Script

Automates the proven Tennis ITF betting edge (+17.81% ROI) by:
- Fetching daily ITF Women's tennis matches
- Filtering odds in the 1.30-1.80 sweet spot
- Calculating optimal bet sizes using Kelly Criterion
- Sending Telegram alerts and logging to Notion

Based on analysis of 98 single bets showing consistent profitability
in ITF Women's tennis with specific odds ranges.

Usage:
    python tennis_itf_screener.py [--test] [--bankroll AMOUNT]
    
Examples:
    python tennis_itf_screener.py                    # Normal daily run
    python tennis_itf_screener.py --test             # Test mode (no notifications)
    python tennis_itf_screener.py --bankroll 500     # Custom bankroll
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

from config.screening_config import ScreeningConfig
from utils.odds_fetcher import OddsFetcher, TennisMatch
from utils.bet_calculator import BetCalculator, BettingOpportunity
from utils.notifiers import NotificationManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tennis_itf_screener.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class TennisITFScreener:
    """Main screening system orchestrator"""
    
    def __init__(self, bankroll: float = None, test_mode: bool = False):
        self.config = ScreeningConfig()
        self.test_mode = test_mode
        
        # Initialize components
        self.odds_fetcher = OddsFetcher()
        self.bet_calculator = BetCalculator(bankroll)
        self.notification_manager = NotificationManager()
        
        logger.info(f"Initialized Tennis ITF Screener (test_mode={test_mode})")
        logger.info(f"Bankroll: ${self.bet_calculator.bankroll:.2f}")
        logger.info(f"Base unit: ${self.bet_calculator.base_unit:.2f}")
    
    async def run_screening(self) -> Dict:
        """
        Run the complete screening process
        
        Returns:
            Dictionary with screening results and statistics
        """
        logger.info("Starting Tennis ITF screening process...")
        
        try:
            # Step 1: Validate configuration
            if not self.config.validate_config():
                raise ValueError("Invalid configuration - check API keys and credentials")
            
            # Step 2: Fetch tennis matches
            logger.info("Fetching ITF Women's tennis matches...")
            async with self.odds_fetcher as fetcher:
                matches = await fetcher.fetch_tennis_matches(hours_ahead=48)
            
            if not matches:
                logger.warning("No ITF tennis matches found")
                return self._create_empty_result()
            
            logger.info(f"Found {len(matches)} ITF tennis matches")
            
            # Step 3: Filter and calculate bet sizes
            logger.info("Analyzing opportunities and calculating bet sizes...")
            opportunities = self.bet_calculator.filter_and_size_opportunities(matches)
            
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
            
            logger.info("Screening process completed successfully")
            self._log_summary(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Screening process failed: {e}")
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
        """Convert BettingOpportunity to dictionary for JSON serialization"""
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
            logger.info("=== SCREENING SUMMARY ===")
            logger.info(f"Opportunities found: {result['opportunities_found']}")
            logger.info(f"Total recommended stake: ${result['summary']['total_stake']}")
            logger.info(f"Average odds: {result['summary']['avg_odds']}")
            logger.info(f"Average edge: +{result['summary']['avg_edge']}%")
            logger.info(f"Risk percentage: {result['summary']['risk_percentage']}%")
            
            logger.info("--- OPPORTUNITIES ---")
            for i, opp in enumerate(result['opportunities'], 1):
                logger.info(f"{i}. {opp['player']} @ {opp['odds']} "
                           f"(${opp['recommended_stake']}, {opp['confidence']})")
        else:
            logger.info("No qualified opportunities found today")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Tennis ITF Screening System')
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
    screener = TennisITFScreener(
        bankroll=args.bankroll,
        test_mode=args.test
    )
    
    # Run screening
    try:
        result = asyncio.run(screener.run_screening())
        
        if result['success']:
            print(f"\n✅ Screening completed successfully!")
            print(f"Found {result['opportunities_found']} opportunities")
            
            if result['opportunities_found'] > 0:
                print(f"Total stake: ${result['summary']['total_stake']}")
                print(f"Average edge: +{result['summary']['avg_edge']}%")
                
                if not args.test:
                    notifications = result['notifications']
                    print(f"Telegram alerts: {'✅' if notifications['telegram_alerts'] else '❌'}")
                    print(f"Notion logging: {'✅' if notifications['notion_logging'] else '❌'}")
                else:
                    print("(Test mode - no notifications sent)")
            
            sys.exit(0)
        else:
            print(f"\n❌ Screening failed: {result['error']}")
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
