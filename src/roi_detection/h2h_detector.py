#!/usr/bin/env python3
"""
🎯 H2H EXPLOIT DETECTOR
=======================

Detects H2H imbalance opportunities when one player dominates.
"""

import logging
from typing import Dict, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.roi_detection.momentum_detector import ROIOpportunity

logger = logging.getLogger(__name__)


class H2HDetector:
    """
    H2H exploit detector
    
    Identifies when one player has strong H2H dominance
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize H2H detector
        
        Args:
            config: Configuration dict
        """
        self.config = config or {}
        self.min_dominance = self.config.get('min_dominance', 4)  # Min wins with 0 losses
        self.min_win_rate = self.config.get('min_win_rate', 0.75)  # 75% win rate
        
        logger.info("🎯 H2H Detector initialized")
    
    def detect_opportunity(self, match_data: Dict) -> Optional[ROIOpportunity]:
        """
        Detect H2H exploit opportunity
        
        Args:
            match_data: Dictionary with match information including:
                - match_id
                - player_a, player_b
                - surface
                - h2h_overall: {'wins_a': X, 'wins_b': Y}
                - h2h_surface: {'hard': {'wins_a': X, 'wins_b': Y}, ...}
                
        Returns:
            ROIOpportunity object or None
        """
        logger.debug(f"🔍 Analyzing H2H for match {match_data.get('match_id')}")
        
        surface = match_data.get('surface', '').lower()
        
        # Get surface-specific H2H if available
        h2h_surface = match_data.get('h2h_surface', {})
        if surface in h2h_surface:
            h2h = h2h_surface[surface]
        else:
            # Fall back to overall H2H
            h2h = match_data.get('h2h_overall', {})
        
        wins_a = h2h.get('wins_a', 0)
        wins_b = h2h.get('wins_b', 0)
        
        if wins_a == 0 and wins_b == 0:
            return None  # No H2H data
        
        # Check for dominance
        if wins_a >= self.min_dominance and wins_b == 0:
            # Player A dominates
            return self._create_h2h_opportunity(match_data, 'player_a', wins_a, wins_b, surface)
        elif wins_b >= self.min_dominance and wins_a == 0:
            # Player B dominates
            return self._create_h2h_opportunity(match_data, 'player_b', wins_b, wins_a, surface)
        
        # Check for high win rate
        total_matches = wins_a + wins_b
        if total_matches >= 3:
            if wins_a / total_matches >= self.min_win_rate:
                return self._create_h2h_opportunity(match_data, 'player_a', wins_a, wins_b, surface)
            elif wins_b / total_matches >= self.min_win_rate:
                return self._create_h2h_opportunity(match_data, 'player_b', wins_b, wins_a, surface)
        
        return None
    
    def _create_h2h_opportunity(self, match_data: Dict, favored_player: str, 
                               wins: int, losses: int, surface: str) -> Optional[ROIOpportunity]:
        """
        Create H2H opportunity
        
        Args:
            match_data: Match data dictionary
            favored_player: Player to favor ('player_a' or 'player_b')
            wins: Wins for favored player
            losses: Losses for favored player
            surface: Surface type
            
        Returns:
            ROIOpportunity object or None
        """
        # Get odds for favored player
        if favored_player == 'player_a':
            current_odds = match_data.get('current_odds_a')
            player_name = match_data.get('player_a')
        else:
            current_odds = match_data.get('current_odds_b')
            player_name = match_data.get('player_b')
        
        if not current_odds:
            return None
        
        # Calculate expected value
        win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0.5
        ev_pct = (current_odds * win_rate - 1) * 100
        
        if ev_pct < 5:  # Minimum 5% EV
            return None
        
        # Calculate confidence (based on sample size and win rate)
        sample_size_factor = min((wins + losses) / 10.0, 1.0)  # More matches = higher confidence
        win_rate_factor = win_rate
        confidence = (sample_size_factor * 0.5 + win_rate_factor * 0.5)
        
        # Generate reasoning
        surface_text = f" on {surface}" if surface else ""
        reasoning = (
            f"{player_name} dominates H2H{surface_text} ({wins}-{losses}). "
            f"Historical edge suggests value at current odds."
        )
        
        opportunity = ROIOpportunity(
            match_id=match_data.get('match_id'),
            opportunity_type='h2h_imbalance',
            strategy='H2H Exploit',
            expected_value_pct=ev_pct,
            kelly_stake_pct=0.0,
            confidence_score=confidence,
            reasoning=reasoning
        )
        
        logger.info(f"✅ H2H opportunity detected: {player_name} ({wins}-{losses}) (EV: {ev_pct:.1f}%)")
        return opportunity

