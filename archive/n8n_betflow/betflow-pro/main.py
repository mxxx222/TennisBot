"""
Main orchestrator for BetFlow Pro ROI maximization
"""
import schedule
import time
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from edge_detection import EdgeDetectionEngine
from kelly_criterion import KellyCriterion
from bookmaker_optimizer import BookmakerOptimizer
from notion_sync import NotionSync
from alerts import AlertSystem
from config import (
    BANKROLL, MIN_EDGE_PERCENT, KELLY_SCALE, 
    MAX_STAKE_PERCENT, MAX_DRAWDOWN_TOLERANCE
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BetFlowProEngine:
    """Main orchestrator for ROI maximization"""

    def __init__(self, historical_data: Optional[pd.DataFrame] = None):
        """
        Initialize BetFlow Pro engine
        
        Args:
            historical_data: Historical match data for ML training (optional)
        """
        logger.info("🚀 Initializing BetFlow Pro Engine...")
        
        self.edge_engine = EdgeDetectionEngine(historical_data)
        self.kelly = KellyCriterion()
        self.bookmakers = BookmakerOptimizer()
        self.notion = NotionSync()
        self.alerts = AlertSystem()
        
        self.bankroll = BANKROLL
        self.peak_bankroll = BANKROLL
        self.current_drawdown = 0.0
        
        logger.info("✅ BetFlow Pro Engine initialized")

    def analyze_match(self, match: Dict) -> Dict:
        """
        Full analysis pipeline for single match

        Args:
            match: Dict with match information:
                {
                    'id': 'match123',
                    'home_team': 'Team A',
                    'away_team': 'Team B',
                    'my_probability': 0.55,
                    'market_probability': 0.50,
                    'opening_odds': 2.0,
                    'current_odds': 2.05,
                    'hours_to_match': 24,
                    'bet_type': '1X2',
                    'xg_diff': 0.5,
                    'form_diff': 0.2,
                    'h2h_win_pct': 60,
                    'recent_goals_diff': 1.0,
                    'injury_count_diff': 0,
                    'data_points': 15
                }

        Returns:
            Dict with complete analysis
        """
        match_id = match.get('id') or match.get('match_id')
        if not match_id:
            logger.warning("Match ID missing")
            return {}

        # 1. BASE EDGE
        my_prob = match.get('my_probability', 0.5)
        market_prob = match.get('market_probability', 0.5)
        base_edge = self.edge_engine.calculate_base_edge(my_prob, market_prob)

        # 2. LINE MOVEMENT EDGE
        opening_odds = match.get('opening_odds', match.get('current_odds', 2.0))
        current_odds = match.get('current_odds', opening_odds)
        time_hours = match.get('hours_to_match', 24)
        
        movement_data = self.edge_engine.detect_line_movement(
            opening_odds, current_odds, time_hours
        )
        movement_edge = movement_data.get('edge_opportunity', 0)

        # 3. ARBITRAGE EDGE
        bet_type = match.get('bet_type', '1X2')
        best_odds = self.bookmakers.get_best_odds(match_id, bet_type)
        arb_edge = self._calculate_arb_edge_for_match(best_odds)

        # 4. ML PROBABILITY
        ml_probability = self.edge_engine.predict_probability_ml({
            'xg_diff': match.get('xg_diff', 0),
            'form_diff': match.get('form_diff', 0),
            'h2h_win_pct': match.get('h2h_win_pct', 50),
            'home_advantage': 0.55,
            'recent_goals_diff': match.get('recent_goals_diff', 0),
            'injury_count_diff': match.get('injury_count_diff', 0)
        })

        # 5. COMPOSITE EDGE
        total_edge = self.edge_engine.calculate_composite_edge(
            base_edge=base_edge,
            arb_edge=arb_edge,
            movement_edge=movement_edge,
            ml_probability=ml_probability,
            market_probability=market_prob
        )

        # 6. CONFIDENCE SCORE
        agreement_level = self._calculate_agreement(base_edge, movement_edge, arb_edge)
        confidence = self.edge_engine.get_confidence_score(
            agreement_level=agreement_level,
            data_points=match.get('data_points', 10),
            time_to_match=time_hours
        )

        # 7. KELLY CALCULATION
        best_odds_value = best_odds.get('best_odds', {})
        if isinstance(best_odds_value, dict):
            # For 1X2, use home odds as default
            odds_for_kelly = best_odds_value.get('home', current_odds)
        else:
            odds_for_kelly = best_odds_value if best_odds_value else current_odds

        kelly_base = self.kelly.calculate_optimal_kelly(
            edge_percent=total_edge,
            odds=odds_for_kelly
        )

        kelly_scaled = self.kelly.scale_kelly(kelly_base, KELLY_SCALE)
        
        # Apply drawdown adjustment
        kelly_scaled = self.kelly.drawdown_adjusted_kelly(
            kelly_scaled,
            self.current_drawdown,
            MAX_DRAWDOWN_TOLERANCE
        )

        # 8. STAKE CALCULATION
        stake = self.kelly.calculate_stake(
            bankroll=self.bankroll,
            kelly_percent=kelly_scaled * 100,
            max_percent_per_bet=MAX_STAKE_PERCENT
        )

        potential_win = stake * (odds_for_kelly - 1) if stake > 0 else 0

        recommendation = "PLAY" if total_edge > MIN_EDGE_PERCENT and confidence >= 6 else "WAIT"

        analysis = {
            "match_id": match_id,
            "match_name": f"{match.get('home_team', 'Home')} vs {match.get('away_team', 'Away')}",
            "base_edge": round(base_edge, 2),
            "arb_edge": round(arb_edge, 2),
            "movement_edge": round(movement_edge, 2),
            "ml_edge": round(((ml_probability - market_prob) / market_prob * 100) if market_prob > 0 else 0, 2),
            "total_edge": round(total_edge, 2),
            "confidence": confidence,
            "best_book": best_odds.get('best_book', 'Pinnacle'),
            "best_odds": odds_for_kelly,
            "kelly_percent": round(kelly_scaled * 100, 2),
            "stake": round(stake, 2),
            "potential_win": round(potential_win, 2),
            "recommendation": recommendation
        }

        return analysis

    def daily_routine(self):
        """Run every morning 06:00"""
        logger.info("🎯 Starting daily routine...")

        # 1. Fetch today's matches (mock implementation)
        matches = self._fetch_matches_today()

        # 2. Analyze each match
        analyses = []
        plays = []

        for match in matches:
            try:
                analysis = self.analyze_match(match)
                if analysis:
                    analyses.append(analysis)

                    # 3. Update Notion with analysis
                    self.notion.update_analysis(match.get('id'), analysis)

                    # 4. Identify plays
                    if analysis['recommendation'] == 'PLAY':
                        plays.append(analysis)

            except Exception as e:
                logger.error(f"Error analyzing match {match.get('id')}: {e}")
                continue

        # 5. Send alerts for high-confidence plays
        for play in sorted(plays, key=lambda x: x['total_edge'], reverse=True)[:5]:
            if play['total_edge'] > 10 and play['confidence'] >= 8:
                self.alerts.alert_high_confidence_play(play)

        logger.info(f"✅ Found {len(plays)} plays out of {len(analyses)} matches")

        # 6. Display high-confidence plays
        for play in plays[:5]:
            logger.info(
                f"🎯 {play['match_id']}: {play['total_edge']:.1f}% edge, "
                f"€{play['stake']:.0f} @ {play['best_odds']:.2f} ({play['best_book']})"
            )

    def check_arbitrage(self):
        """Check for arbitrage opportunities"""
        logger.info("🔍 Checking for arbitrage opportunities...")

        matches = self._fetch_matches_today()
        arbs = self.bookmakers.detect_arbitrage(matches)

        for arb in arbs[:10]:  # Top 10 arbitrage opportunities
            logger.info(
                f"⚡ Arbitrage: {arb['match_name']} - {arb['arbitrage_percent']:.2f}% "
                f"({arb['book_a']} @ {arb['odds_a']:.2f} vs {arb['book_b']} @ {arb['odds_b']:.2f})"
            )
            
            # Log to Notion
            self.notion.log_arbitrage(arb)
            
            # Send alert
            if arb['arbitrage_percent'] > 2.0:
                self.alerts.alert_arbitrage(arb)

    def check_line_movements(self):
        """Check for line movement opportunities"""
        logger.info("📈 Checking line movements...")
        
        # This would track odds over time in a real implementation
        # For now, this is a placeholder
        pass

    def update_results(self):
        """Update bet results and bankroll"""
        logger.info("📊 Updating results...")

        pending_bets = self.notion.fetch_pending_bets()
        
        # In a real implementation, this would check bet status
        # and update bankroll accordingly
        logger.info(f"Found {len(pending_bets)} pending bets")

    def _fetch_matches_today(self) -> List[Dict]:
        """
        Fetch today's matches (mock implementation)
        
        In production, this would fetch from a data source
        """
        # Mock matches for testing
        return [
            {
                'id': 'match001',
                'home_team': 'Team A',
                'away_team': 'Team B',
                'my_probability': 0.55,
                'market_probability': 0.50,
                'opening_odds': 2.0,
                'current_odds': 2.05,
                'hours_to_match': 24,
                'bet_type': '1X2',
                'xg_diff': 0.5,
                'form_diff': 0.2,
                'h2h_win_pct': 60,
                'recent_goals_diff': 1.0,
                'injury_count_diff': 0,
                'data_points': 15
            }
        ]

    def _calculate_arb_edge_for_match(self, odds_data: Dict) -> float:
        """Extract arbitrage edge from odds comparison"""
        all_odds = odds_data.get('all_odds', {})
        
        if len(all_odds) < 2:
            return 0.0

        # Calculate arbitrage potential
        odds_list = []
        for book_odds in all_odds.values():
            if isinstance(book_odds, dict):
                for key in ['home_odds', 'away_odds', 'odds']:
                    if key in book_odds:
                        odds_list.append(book_odds[key])
                        break
            else:
                odds_list.append(book_odds)

        if len(odds_list) < 2:
            return 0.0

        # Simple arbitrage calculation
        min_odds = min(odds_list)
        max_odds = max(odds_list)
        
        if min_odds > 0:
            arb_value = 1/min_odds + 1/max_odds
            if arb_value < 1:
                return (1 - arb_value) * 100

        return 0.0

    def _calculate_agreement(self, *edges) -> float:
        """Agreement between different edge detection methods"""
        if not edges or all(e == 0 for e in edges):
            return 0.0

        non_zero_edges = [e for e in edges if e != 0]
        if not non_zero_edges:
            return 0.0

        mean_edge = sum(non_zero_edges) / len(non_zero_edges)
        variance = sum((e - mean_edge)**2 for e in non_zero_edges) / len(non_zero_edges)

        # Lower variance = higher agreement
        agreement = 1 - min(1, variance / 100)
        return agreement


def main():
    """Main entry point"""
    engine = BetFlowProEngine()

    # Schedule tasks
    schedule.every().day.at("06:00").do(engine.daily_routine)
    schedule.every().day.at("14:00").do(engine.check_line_movements)
    schedule.every().day.at("20:00").do(engine.update_results)
    schedule.every(30).minutes.do(engine.check_arbitrage)

    logger.info("🚀 BetFlow Pro Engine started")
    logger.info("Scheduled tasks:")
    logger.info("  - 06:00 Daily analysis routine")
    logger.info("  - 14:00 Line movement check")
    logger.info("  - 20:00 Results update")
    logger.info("  - Every 30 minutes: Arbitrage check")

    # Run once immediately for testing
    engine.daily_routine()
    engine.check_arbitrage()

    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()

