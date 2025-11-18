"""
Bet sizing calculator for Tennis ITF screening system
Implements Kelly Criterion and proven sizing strategies from single_bets.csv analysis
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from config.screening_config import ScreeningConfig

logger = logging.getLogger(__name__)

@dataclass
class BettingOpportunity:
    """Represents a qualified betting opportunity"""
    match_id: str
    player: str
    opponent: str
    odds: float
    commence_time: datetime
    tournament: str
    side: str  # 'home' or 'away'
    recommended_stake: float
    confidence: str  # 'High', 'Medium', 'Low'
    edge_estimate: float
    kelly_fraction: float

class BetCalculator:
    """Calculates optimal bet sizes based on proven strategies"""
    
    def __init__(self, bankroll: float = None):
        self.config = ScreeningConfig()
        self.bankroll = bankroll or self.config.DEFAULT_BANKROLL
        self.base_unit = self.bankroll * self.config.BASE_UNIT_PERCENTAGE
        
    def calculate_implied_probability(self, odds: float) -> float:
        """Calculate implied probability from decimal odds"""
        return 1.0 / odds if odds > 0 else 0.0
    
    def estimate_true_probability(self, odds: float) -> float:
        """
        Estimate true probability based on historical analysis
        
        From single_bets.csv analysis:
        - Odds 1.30-1.80 range shows +17.81% ROI
        - This suggests bookmaker odds are slightly undervaluing these outcomes
        """
        implied_prob = self.calculate_implied_probability(odds)
        
        # Based on +17.81% ROI, we estimate true probability is higher
        # Conservative edge estimate: 2-5% above implied probability
        if 1.30 <= odds <= 1.50:
            # Higher confidence for lower odds
            edge_factor = 1.04  # 4% edge
        elif 1.51 <= odds <= 1.80:
            # Medium confidence for mid-range odds
            edge_factor = 1.03  # 3% edge
        else:
            # No edge outside proven range
            edge_factor = 1.0
            
        return min(implied_prob * edge_factor, 0.95)  # Cap at 95%
    
    def calculate_kelly_fraction(self, odds: float, true_prob: float) -> float:
        """
        Calculate Kelly Criterion fraction
        
        Kelly = (bp - q) / b
        where:
        - b = odds - 1 (net odds)
        - p = true probability of winning
        - q = probability of losing (1 - p)
        """
        if odds <= 1.0 or true_prob <= 0:
            return 0.0
            
        b = odds - 1.0  # Net odds
        p = true_prob
        q = 1.0 - p
        
        kelly = (b * p - q) / b
        
        # Apply fractional Kelly (25% of full Kelly for safety)
        return max(0.0, kelly * 0.25)
    
    def calculate_stake(self, odds: float) -> Tuple[float, str, float]:
        """
        Calculate recommended stake based on odds and proven strategies
        
        Returns:
            (stake_amount, confidence_level, edge_estimate)
        """
        # Check if odds are in proven range
        if not (self.config.MIN_ODDS <= odds <= self.config.MAX_ODDS):
            return 0.0, "None", 0.0
        
        # Get stake multiplier from config
        multiplier = self.config.get_stake_multiplier(odds)
        if multiplier == 0.0:
            return 0.0, "None", 0.0
        
        # Calculate base stake
        base_stake = self.base_unit * multiplier
        
        # Apply Kelly Criterion for fine-tuning
        true_prob = self.estimate_true_probability(odds)
        kelly_fraction = self.calculate_kelly_fraction(odds, true_prob)
        
        # Use Kelly if it suggests a smaller bet (risk management)
        kelly_stake = self.bankroll * kelly_fraction
        
        # Take the smaller of the two approaches (conservative)
        recommended_stake = min(base_stake, kelly_stake)
        
        # Apply safety cap
        recommended_stake = min(recommended_stake, self.config.MAX_STAKE)
        
        # Determine confidence level
        if odds <= 1.50:
            confidence = "High"
        elif odds <= 1.65:
            confidence = "Medium"
        else:
            confidence = "Low"
        
        # Calculate edge estimate
        implied_prob = self.calculate_implied_probability(odds)
        edge_estimate = (true_prob - implied_prob) * 100  # As percentage
        
        return round(recommended_stake, 2), confidence, round(edge_estimate, 2)
    
    def filter_and_size_opportunities(self, matches: List) -> List[BettingOpportunity]:
        """
        Filter matches and calculate bet sizes for qualified opportunities
        
        Args:
            matches: List of TennisMatch objects from odds_fetcher
            
        Returns:
            List of BettingOpportunity objects, sorted by edge potential
        """
        opportunities = []
        
        for match in matches:
            home_odds, away_odds = match.get_best_odds()
            
            # Check home player opportunity
            if self.config.MIN_ODDS <= home_odds <= self.config.MAX_ODDS:
                stake, confidence, edge = self.calculate_stake(home_odds)
                if stake > 0:
                    true_prob = self.estimate_true_probability(home_odds)
                    kelly = self.calculate_kelly_fraction(home_odds, true_prob)
                    
                    opportunities.append(BettingOpportunity(
                        match_id=match.id,
                        player=match.home_team,
                        opponent=match.away_team,
                        odds=home_odds,
                        commence_time=match.commence_time,
                        tournament=match.sport_title,
                        side='home',
                        recommended_stake=stake,
                        confidence=confidence,
                        edge_estimate=edge,
                        kelly_fraction=kelly
                    ))
            
            # Check away player opportunity
            if self.config.MIN_ODDS <= away_odds <= self.config.MAX_ODDS:
                stake, confidence, edge = self.calculate_stake(away_odds)
                if stake > 0:
                    true_prob = self.estimate_true_probability(away_odds)
                    kelly = self.calculate_kelly_fraction(away_odds, true_prob)
                    
                    opportunities.append(BettingOpportunity(
                        match_id=match.id,
                        player=match.away_team,
                        opponent=match.home_team,
                        odds=away_odds,
                        commence_time=match.commence_time,
                        tournament=match.sport_title,
                        side='away',
                        recommended_stake=stake,
                        confidence=confidence,
                        edge_estimate=edge,
                        kelly_fraction=kelly
                    ))
        
        # Sort by edge potential (highest edge first)
        opportunities.sort(key=lambda x: x.edge_estimate, reverse=True)
        
        # Limit to max daily picks
        top_opportunities = opportunities[:self.config.MAX_DAILY_PICKS]
        
        logger.info(f"Found {len(opportunities)} total opportunities, "
                   f"selected top {len(top_opportunities)} for today")
        
        return top_opportunities
    
    def update_bankroll(self, new_bankroll: float):
        """Update bankroll and recalculate base unit"""
        self.bankroll = new_bankroll
        self.base_unit = self.bankroll * self.config.BASE_UNIT_PERCENTAGE
        logger.info(f"Updated bankroll to ${new_bankroll:.2f}, base unit: ${self.base_unit:.2f}")
    
    def get_betting_summary(self, opportunities: List[BettingOpportunity]) -> Dict:
        """Generate summary statistics for the day's opportunities"""
        if not opportunities:
            return {
                'total_opportunities': 0,
                'total_stake': 0.0,
                'avg_odds': 0.0,
                'avg_edge': 0.0,
                'confidence_breakdown': {},
                'risk_percentage': 0.0
            }
        
        total_stake = sum(opp.recommended_stake for opp in opportunities)
        avg_odds = sum(opp.odds for opp in opportunities) / len(opportunities)
        avg_edge = sum(opp.edge_estimate for opp in opportunities) / len(opportunities)
        
        confidence_counts = {}
        for opp in opportunities:
            confidence_counts[opp.confidence] = confidence_counts.get(opp.confidence, 0) + 1
        
        risk_percentage = (total_stake / self.bankroll) * 100
        
        return {
            'total_opportunities': len(opportunities),
            'total_stake': round(total_stake, 2),
            'avg_odds': round(avg_odds, 2),
            'avg_edge': round(avg_edge, 2),
            'confidence_breakdown': confidence_counts,
            'risk_percentage': round(risk_percentage, 2),
            'bankroll': self.bankroll,
            'base_unit': round(self.base_unit, 2)
        }
