#!/usr/bin/env python3
"""
📈 MOMENTUM SHIFT DETECTOR
==========================

Detects momentum shift opportunities in live matches.
Logic: Favorite lost Set 1, odds moved, strong 3-set win rate.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


@dataclass
class ROIOpportunity:
    """ROI opportunity detected"""
    match_id: str
    opportunity_type: str  # 'momentum_shift', 'fatigue_exploit', 'h2h_imbalance'
    strategy: str
    expected_value_pct: float
    kelly_stake_pct: float
    confidence_score: float
    reasoning: str
    detected_at: datetime = None
    
    def __post_init__(self):
        if self.detected_at is None:
            self.detected_at = datetime.now()


class MomentumDetector:
    """
    Momentum shift detector
    
    Detects when favorite lost Set 1 but has strong recovery potential
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize momentum detector
        
        Args:
            config: Configuration dict
        """
        self.config = config or {}
        self.favorite_odds_threshold = self.config.get('favorite_odds_threshold', 1.50)
        self.value_odds_threshold = self.config.get('value_odds_threshold', 1.80)
        self.min_3set_win_rate = self.config.get('min_3set_win_rate', 0.70)
        
        logger.info("📈 Momentum Detector initialized")
    
    def detect_opportunity(self, match_data: Dict) -> Optional[ROIOpportunity]:
        """
        Detect momentum shift opportunity
        
        Args:
            match_data: Dictionary with match information including:
                - match_id
                - player_a, player_b
                - current_score
                - initial_odds_a, initial_odds_b
                - current_odds_a, current_odds_b
                - player_a_3set_win_rate, player_b_3set_win_rate
                
        Returns:
            ROIOpportunity object or None
        """
        logger.debug(f"🔍 Analyzing momentum for match {match_data.get('match_id')}")
        
        # Check if match is live and has score
        current_score = match_data.get('current_score', '')
        if not current_score or ',' not in current_score:
            return None  # Not live or no score yet
        
        # Parse score
        sets = current_score.split(',')
        if len(sets) < 2:
            return None  # Need at least 2 sets
        
        # Check if Set 1 is complete
        set1_score = sets[0].strip()
        set1_winner = self._parse_set_winner(set1_score, match_data.get('player_a'), match_data.get('player_b'))
        
        if not set1_winner:
            return None  # Set 1 not complete or couldn't parse
        
        # Determine initial favorite
        initial_odds_a = match_data.get('initial_odds_a')
        initial_odds_b = match_data.get('initial_odds_b')
        
        if not initial_odds_a or not initial_odds_b:
            return None
        
        # Check if there was a favorite
        was_favorite_a = initial_odds_a < self.favorite_odds_threshold
        was_favorite_b = initial_odds_b < self.favorite_odds_threshold
        
        if not (was_favorite_a or was_favorite_b):
            return None  # No clear favorite
        
        # Check if favorite lost Set 1
        favorite_lost_set1 = False
        favorite_player = None
        favorite_3set_rate = None
        
        if was_favorite_a and set1_winner == 'player_b':
            favorite_lost_set1 = True
            favorite_player = match_data.get('player_a')
            favorite_3set_rate = match_data.get('player_a_3set_win_rate', 0)
        elif was_favorite_b and set1_winner == 'player_a':
            favorite_lost_set1 = True
            favorite_player = match_data.get('player_b')
            favorite_3set_rate = match_data.get('player_b_3set_win_rate', 0)
        
        if not favorite_lost_set1:
            return None  # Favorite didn't lose Set 1
        
        # Check current odds (should have moved in favor of underdog)
        current_odds_a = match_data.get('current_odds_a')
        current_odds_b = match_data.get('current_odds_b')
        
        if not current_odds_a or not current_odds_b:
            return None
        
        # Check if odds moved to value territory
        if was_favorite_a:
            current_favorite_odds = current_odds_a
        else:
            current_favorite_odds = current_odds_b
        
        if current_favorite_odds < self.value_odds_threshold:
            return None  # Odds haven't moved enough
        
        # Check 3-set win rate
        if not favorite_3set_rate or favorite_3set_rate < self.min_3set_win_rate:
            return None  # Not strong enough in 3-set matches
        
        # Calculate expected value (simplified)
        # This would use a more sophisticated model in production
        ev_pct = self._calculate_ev(current_favorite_odds, favorite_3set_rate)
        
        if ev_pct < 10:  # Minimum 10% EV
            return None
        
        # Calculate confidence
        confidence = self._calculate_confidence(favorite_3set_rate, current_favorite_odds, initial_odds_a if was_favorite_a else initial_odds_b)
        
        # Generate reasoning
        reasoning = (
            f"{favorite_player} was favorite (odds {initial_odds_a if was_favorite_a else initial_odds_b:.2f}) "
            f"but lost Set 1. Current odds {current_favorite_odds:.2f} represent value given "
            f"strong 3-set record ({favorite_3set_rate*100:.1f}%)."
        )
        
        opportunity = ROIOpportunity(
            match_id=match_data.get('match_id'),
            opportunity_type='momentum_shift',
            strategy='First Set Recovery',
            expected_value_pct=ev_pct,
            kelly_stake_pct=0.0,  # Will be calculated by Kelly calculator
            confidence_score=confidence,
            reasoning=reasoning
        )
        
        logger.info(f"✅ Momentum opportunity detected: {favorite_player} (EV: {ev_pct:.1f}%)")
        return opportunity
    
    def _parse_set_winner(self, set_score: str, player_a: str, player_b: str) -> Optional[str]:
        """
        Parse set score to determine winner
        
        Args:
            set_score: Set score string (e.g., "6-4")
            player_a: Player A name
            player_b: Player B name
            
        Returns:
            'player_a', 'player_b', or None
        """
        try:
            scores = set_score.split('-')
            if len(scores) != 2:
                return None
            
            score_a = int(scores[0].strip())
            score_b = int(scores[1].strip())
            
            if score_a > score_b and score_a >= 6:
                return 'player_a'
            elif score_b > score_a and score_b >= 6:
                return 'player_b'
            
            return None
            
        except (ValueError, IndexError):
            return None
    
    def _calculate_ev(self, odds: float, win_probability: float) -> float:
        """
        Calculate expected value percentage
        
        Args:
            odds: Current odds
            win_probability: Probability of winning (0-1)
            
        Returns:
            Expected value percentage
        """
        # EV = (odds * probability - 1) * 100
        ev = (odds * win_probability - 1) * 100
        return max(0, ev)
    
    def _calculate_confidence(self, win_rate: float, current_odds: float, initial_odds: float) -> float:
        """
        Calculate confidence score (0-1)
        
        Args:
            win_rate: 3-set win rate
            current_odds: Current odds
            initial_odds: Initial odds
            
        Returns:
            Confidence score (0-1)
        """
        # Base confidence from win rate
        base_confidence = win_rate
        
        # Adjust for odds movement (larger movement = higher confidence)
        odds_movement = (initial_odds - current_odds) / initial_odds
        movement_bonus = min(odds_movement * 0.2, 0.2)  # Max 20% bonus
        
        confidence = min(base_confidence + movement_bonus, 1.0)
        return confidence

