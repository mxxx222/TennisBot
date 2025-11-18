#!/usr/bin/env python3
"""
💰 KELLY CRITERION CALCULATOR
=============================

Calculates optimal stake using Kelly Criterion.
Formula: Kelly % = (p_model * odds - 1) / (odds - 1)
"""

import logging
from typing import Dict, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class KellyCalculator:
    """
    Kelly Criterion calculator
    
    Calculates optimal stake percentage based on edge
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Kelly calculator
        
        Args:
            config: Configuration dict
        """
        self.config = config or {}
        self.kelly_fraction = self.config.get('kelly_fraction', 0.25)  # Fractional Kelly (25%)
        self.max_stake_pct = self.config.get('max_stake_pct', 5.0)  # Max 5% of bankroll
        self.min_stake_pct = self.config.get('min_stake_pct', 0.5)  # Min 0.5% of bankroll
        
        logger.info("💰 Kelly Calculator initialized")
    
    def calculate_stake(self, odds: float, model_probability: float, 
                       implied_probability: Optional[float] = None) -> Dict[str, float]:
        """
        Calculate Kelly stake percentage
        
        Args:
            odds: Current odds (decimal)
            model_probability: Model's probability estimate (0-1)
            implied_probability: Market's implied probability (0-1), optional
            
        Returns:
            Dictionary with:
                - kelly_pct: Full Kelly percentage
                - safe_kelly_pct: Fractional Kelly percentage (recommended)
                - ev_pct: Expected value percentage
                - implied_prob: Implied probability from odds
        """
        if odds <= 1.0:
            logger.warning(f"⚠️ Invalid odds: {odds}")
            return {
                'kelly_pct': 0.0,
                'safe_kelly_pct': 0.0,
                'ev_pct': 0.0,
                'implied_prob': 0.0
            }
        
        # Calculate implied probability (vig-free)
        if implied_probability is None:
            implied_prob = 1.0 / odds
        else:
            implied_prob = implied_probability
        
        # Calculate expected value
        ev = odds * model_probability - 1
        ev_pct = ev * 100
        
        # Calculate full Kelly
        # Kelly % = (p * odds - 1) / (odds - 1)
        kelly_pct = (model_probability * odds - 1) / (odds - 1)
        
        # Apply fractional Kelly
        safe_kelly_pct = kelly_pct * self.kelly_fraction
        
        # Apply limits
        safe_kelly_pct = max(self.min_stake_pct, min(safe_kelly_pct, self.max_stake_pct))
        
        # If negative edge, return 0
        if safe_kelly_pct < 0:
            safe_kelly_pct = 0.0
        
        result = {
            'kelly_pct': round(kelly_pct * 100, 2),
            'safe_kelly_pct': round(safe_kelly_pct, 2),
            'ev_pct': round(ev_pct, 2),
            'implied_prob': round(implied_prob * 100, 2),
            'model_prob': round(model_probability * 100, 2)
        }
        
        logger.debug(f"💰 Kelly calculation: odds={odds:.2f}, model_prob={model_probability:.2%}, "
                    f"stake={safe_kelly_pct:.2f}%")
        
        return result
    
    def calculate_from_opportunity(self, opportunity: Dict) -> Dict[str, float]:
        """
        Calculate Kelly stake from ROI opportunity
        
        Args:
            opportunity: ROIOpportunity dictionary with:
                - expected_value_pct
                - current_odds (or odds_a/odds_b)
                - model_probability (optional)
                
        Returns:
            Dictionary with Kelly calculations
        """
        # Extract odds
        odds = opportunity.get('current_odds')
        if not odds:
            odds_a = opportunity.get('odds_a')
            odds_b = opportunity.get('odds_b')
            # Use the odds for the favored player (would need to determine from opportunity)
            odds = odds_a or odds_b
        
        if not odds:
            return {
                'kelly_pct': 0.0,
                'safe_kelly_pct': 0.0,
                'ev_pct': 0.0,
                'implied_prob': 0.0
            }
        
        # Estimate model probability from EV
        # EV = (odds * p_model - 1) * 100
        # p_model = (EV/100 + 1) / odds
        ev_pct = opportunity.get('expected_value_pct', 0)
        model_prob = (ev_pct / 100.0 + 1.0) / odds
        
        return self.calculate_stake(odds, model_prob)

