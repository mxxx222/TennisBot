"""
Mock odds generator for testing and development
"""
import random
from typing import Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MockOddsGenerator:
    """Generate realistic mock odds for testing"""

    @staticmethod
    def generate_match_odds(match_id: str, 
                           home_team: str, 
                           away_team: str,
                           bet_type: str = "1X2") -> Dict:
        """
        Generate mock odds for a match
        
        Args:
            match_id: Unique match identifier
            home_team: Home team name
            away_team: Away team name
            bet_type: Type of bet (1X2, OU2.5, BTTS, etc.)
        
        Returns:
            Dict with odds data
        """
        if bet_type == "1X2":
            # Generate realistic 1X2 odds
            home_prob = random.uniform(0.30, 0.60)
            draw_prob = random.uniform(0.20, 0.35)
            away_prob = 1 - home_prob - draw_prob
            
            # Add margin (bookmaker profit)
            margin = 0.05
            home_odds = 1 / (home_prob * (1 + margin))
            draw_odds = 1 / (draw_prob * (1 + margin))
            away_odds = 1 / (away_prob * (1 + margin))
            
            return {
                "match_id": match_id,
                "home_team": home_team,
                "away_team": away_team,
                "bet_type": bet_type,
                "home_odds": round(home_odds, 2),
                "draw_odds": round(draw_odds, 2),
                "away_odds": round(away_odds, 2),
                "timestamp": datetime.now().isoformat()
            }
        
        elif bet_type == "OU2.5":
            over_prob = random.uniform(0.40, 0.60)
            margin = 0.05
            over_odds = 1 / (over_prob * (1 + margin))
            under_odds = 1 / ((1 - over_prob) * (1 + margin))
            
            return {
                "match_id": match_id,
                "bet_type": bet_type,
                "over_odds": round(over_odds, 2),
                "under_odds": round(under_odds, 2),
                "timestamp": datetime.now().isoformat()
            }
        
        elif bet_type == "BTTS":
            yes_prob = random.uniform(0.45, 0.65)
            margin = 0.05
            yes_odds = 1 / (yes_prob * (1 + margin))
            no_odds = 1 / ((1 - yes_prob) * (1 + margin))
            
            return {
                "match_id": match_id,
                "bet_type": bet_type,
                "yes_odds": round(yes_odds, 2),
                "no_odds": round(no_odds, 2),
                "timestamp": datetime.now().isoformat()
            }
        
        else:
            # Generic odds
            prob = random.uniform(0.40, 0.60)
            margin = 0.05
            odds = 1 / (prob * (1 + margin))
            
            return {
                "match_id": match_id,
                "bet_type": bet_type,
                "odds": round(odds, 2),
                "timestamp": datetime.now().isoformat()
            }

    @staticmethod
    def generate_odds_with_variation(base_odds: float, 
                                    variation_percent: float = 0.05) -> float:
        """
        Generate odds with small random variation
        
        Args:
            base_odds: Base odds value
            variation_percent: Maximum variation percentage
        
        Returns:
            Adjusted odds
        """
        variation = random.uniform(-variation_percent, variation_percent)
        new_odds = base_odds * (1 + variation)
        return round(new_odds, 2)

