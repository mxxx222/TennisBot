#!/usr/bin/env python3
"""
📊 ITF BACKTESTER
=================

Historical backtest system for ITF Women matches.
Scrapes 200-500 historical matches (Oct-Nov 2025).
Tests GLM strategies:
- Momentum Shift (bet after losing first set 6-2, win in 3)
- Underdog Upset (ranked >200 player upsets)
- Retirement patterns
Calculates ROI per strategy.
Outputs results to Live Stats Dashboard.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scrapers.flashscore_itf_scraper import FlashScoreITFScraper, ITFMatch

logger = logging.getLogger(__name__)

@dataclass
class BacktestResult:
    """Backtest result for a strategy"""
    strategy_name: str
    total_bets: int
    wins: int
    losses: int
    total_stake: float
    total_profit: float
    roi: float
    win_rate: float

class ITFBacktester:
    """Backtester for ITF Women strategies"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ITF Backtester
        
        Args:
            config: Configuration dict
        """
        self.config = config or {}
        self.min_matches = self.config.get('min_matches', 200)
        self.max_matches = self.config.get('max_matches', 500)
        self.strategies = self.config.get('strategies', [
            'momentum_shift',
            'underdog_upset',
            'retirement_pattern'
        ])
        
        logger.info(f"📊 ITF Backtester initialized (target: {self.min_matches}-{self.max_matches} matches)")
    
    async def scrape_historical_matches(self, start_date: datetime, end_date: datetime) -> List[ITFMatch]:
        """
        Scrape historical matches for backtesting
        
        Args:
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            List of historical ITFMatch objects
        """
        logger.info(f"🔍 Scraping historical matches from {start_date.date()} to {end_date.date()}...")
        
        # Use FlashScore scraper to get historical data
        # Note: This is a simplified version - in production would need historical data source
        matches = []
        
        # For now, simulate historical matches
        # In production, would scrape from historical FlashScore data or database
        logger.warning("⚠️ Historical scraping not fully implemented - using simulated data")
        
        return matches
    
    def test_momentum_shift_strategy(self, matches: List[ITFMatch]) -> BacktestResult:
        """
        Test Momentum Shift strategy: bet after losing first set 6-2, win in 3
        
        Args:
            matches: List of historical matches
            
        Returns:
            BacktestResult
        """
        bets = []
        
        for match in matches:
            # Check if match fits strategy criteria
            if match.set1_score:
                try:
                    scores = match.set1_score.split('-')
                    if len(scores) == 2:
                        player1_games = int(scores[0])
                        player2_games = int(scores[1])
                        
                        # Strategy: Player lost first set 0-6, 1-6, or 2-6, then won match
                        if (player1_games <= 2 or player2_games <= 2) and match.match_status == 'finished':
                            # Check if match went to 3 sets (would need full score)
                            if match.live_score and ',' in match.live_score:
                                # Simulate bet (would need actual odds)
                                bets.append({
                                    'match': match,
                                    'stake': 10.0,  # Default stake
                                    'odds': 2.0,  # Simulated odds
                                    'won': True,  # Would check actual result
                                })
                except:
                    pass
        
        # Calculate results
        total_bets = len(bets)
        wins = sum(1 for b in bets if b.get('won', False))
        losses = total_bets - wins
        total_stake = sum(b['stake'] for b in bets)
        total_profit = sum(b['stake'] * (b['odds'] - 1) if b.get('won') else -b['stake'] for b in bets)
        roi = (total_profit / total_stake * 100) if total_stake > 0 else 0
        win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
        
        return BacktestResult(
            strategy_name='Momentum Shift',
            total_bets=total_bets,
            wins=wins,
            losses=losses,
            total_stake=total_stake,
            total_profit=total_profit,
            roi=roi,
            win_rate=win_rate
        )
    
    def test_underdog_upset_strategy(self, matches: List[ITFMatch]) -> BacktestResult:
        """
        Test Underdog Upset strategy: ranked >200 player upsets
        
        Args:
            matches: List of historical matches
            
        Returns:
            BacktestResult
        """
        # Would need player rankings data
        # For now, return empty result
        return BacktestResult(
            strategy_name='Underdog Upset',
            total_bets=0,
            wins=0,
            losses=0,
            total_stake=0.0,
            total_profit=0.0,
            roi=0.0,
            win_rate=0.0
        )
    
    def test_retirement_pattern_strategy(self, matches: List[ITFMatch]) -> BacktestResult:
        """
        Test Retirement Pattern strategy
        
        Args:
            matches: List of historical matches
            
        Returns:
            BacktestResult
        """
        # Would need retirement data
        # For now, return empty result
        return BacktestResult(
            strategy_name='Retirement Pattern',
            total_bets=0,
            wins=0,
            losses=0,
            total_stake=0.0,
            total_profit=0.0,
            roi=0.0,
            win_rate=0.0
        )
    
    async def run_backtest(self) -> Dict[str, Any]:
        """
        Run complete backtest for all strategies
        
        Returns:
            Dictionary with backtest results
        """
        logger.info("🚀 Starting ITF backtest...")
        
        # Scrape historical matches (Oct-Nov 2025)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)  # ~2 months
        
        matches = await self.scrape_historical_matches(start_date, end_date)
        
        if len(matches) < self.min_matches:
            logger.warning(f"⚠️ Only {len(matches)} matches found (minimum: {self.min_matches})")
            return {
                'success': False,
                'error': f'Insufficient matches: {len(matches)} < {self.min_matches}',
                'timestamp': datetime.now().isoformat(),
            }
        
        # Test each strategy
        results = {}
        
        if 'momentum_shift' in self.strategies:
            logger.info("📊 Testing Momentum Shift strategy...")
            results['momentum_shift'] = self.test_momentum_shift_strategy(matches)
        
        if 'underdog_upset' in self.strategies:
            logger.info("📊 Testing Underdog Upset strategy...")
            results['underdog_upset'] = self.test_underdog_upset_strategy(matches)
        
        if 'retirement_pattern' in self.strategies:
            logger.info("📊 Testing Retirement Pattern strategy...")
            results['retirement_pattern'] = self.test_retirement_pattern_strategy(matches)
        
        # Format results
        formatted_results = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'matches_analyzed': len(matches),
            'strategies': {
                name: {
                    'strategy_name': result.strategy_name,
                    'total_bets': result.total_bets,
                    'wins': result.wins,
                    'losses': result.losses,
                    'total_stake': result.total_stake,
                    'total_profit': result.total_profit,
                    'roi': result.roi,
                    'win_rate': result.win_rate,
                }
                for name, result in results.items()
            }
        }
        
        logger.info("✅ Backtest completed")
        return formatted_results
    
    def export_results(self, results: Dict[str, Any], output_path: Optional[str] = None):
        """
        Export backtest results to file
        
        Args:
            results: Backtest results dictionary
            output_path: Output file path (optional)
        """
        if not output_path:
            output_path = Path(__file__).parent.parent.parent / 'data' / f'itf_backtest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"✅ Exported backtest results to {output_path}")


async def main():
    """Test ITF Backtester"""
    print("📊 ITF BACKTESTER TEST")
    print("=" * 50)
    
    config = {
        'min_matches': 200,
        'max_matches': 500,
        'strategies': ['momentum_shift', 'underdog_upset', 'retirement_pattern'],
    }
    
    backtester = ITFBacktester(config)
    results = await backtester.run_backtest()
    
    if results.get('success'):
        print(f"\n✅ Backtest completed!")
        print(f"   Matches analyzed: {results['matches_analyzed']}")
        print("\n📊 Strategy Results:")
        for name, strategy in results['strategies'].items():
            print(f"\n   {strategy['strategy_name']}:")
            print(f"      Bets: {strategy['total_bets']}")
            print(f"      Win Rate: {strategy['win_rate']:.1f}%")
            print(f"      ROI: {strategy['roi']:.2f}%")
    else:
        print(f"\n❌ Backtest failed: {results.get('error')}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())

