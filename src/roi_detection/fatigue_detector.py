#!/usr/bin/env python3
"""
😴 FATIGUE RISK DETECTOR
========================

Detects fatigue opportunities when opponent has played multiple matches recently.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.roi_detection.momentum_detector import ROIOpportunity

logger = logging.getLogger(__name__)


class FatigueDetector:
    """
    Fatigue risk detector
    
    Identifies when opponent has high fatigue risk
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize fatigue detector
        
        Args:
            config: Configuration dict
        """
        self.config = config or {}
        self.high_risk_hours = self.config.get('high_risk_hours', 12)
        self.medium_risk_hours = self.config.get('medium_risk_hours', 24)
        
        logger.info("😴 Fatigue Detector initialized")
    
    def detect_opportunity(self, match_data: Dict) -> Optional[ROIOpportunity]:
        """
        Detect fatigue opportunity
        
        Args:
            match_data: Dictionary with match information including:
                - match_id
                - player_a, player_b
                - player_a_fatigue_risk, player_b_fatigue_risk
                - player_a_days_since_match, player_b_days_since_match
                
        Returns:
            ROIOpportunity object or None
        """
        logger.debug(f"🔍 Analyzing fatigue for match {match_data.get('match_id')}")
        
        player_a_fatigue = match_data.get('player_a_fatigue_risk', 0)
        player_b_fatigue = match_data.get('player_b_fatigue_risk', 0)
        
        # Check if either player has high fatigue risk
        if player_a_fatigue >= 70:
            # Player A has high fatigue, favor Player B
            return self._create_fatigue_opportunity(match_data, 'player_b', 'player_a', player_a_fatigue)
        elif player_b_fatigue >= 70:
            # Player B has high fatigue, favor Player A
            return self._create_fatigue_opportunity(match_data, 'player_a', 'player_b', player_b_fatigue)
        
        return None
    
    def _create_fatigue_opportunity(self, match_data: Dict, favored_player: str, 
                                   fatigued_player: str, fatigue_score: int) -> Optional[ROIOpportunity]:
        """
        Create fatigue opportunity
        
        Args:
            match_data: Match data dictionary
            favored_player: Player to favor ('player_a' or 'player_b')
            fatigued_player: Player with fatigue ('player_a' or 'player_b')
            fatigue_score: Fatigue risk score
            
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
        
        # Calculate expected value (simplified)
        # Fatigue adds edge to opponent
        fatigue_edge = min(fatigue_score / 100.0 * 0.15, 0.15)  # Max 15% edge
        base_prob = 1.0 / current_odds
        adjusted_prob = base_prob + fatigue_edge
        
        ev_pct = (current_odds * adjusted_prob - 1) * 100
        
        if ev_pct < 5:  # Minimum 5% EV
            return None
        
        # Calculate confidence
        confidence = min(fatigue_score / 100.0, 0.85)  # Cap at 85%
        
        # Generate reasoning
        fatigued_name = match_data.get(fatigued_player.replace('player_', 'player_'))
        reasoning = (
            f"{fatigued_name} has high fatigue risk ({fatigue_score}/100) "
            f"indicating potential advantage for {player_name}."
        )
        
        opportunity = ROIOpportunity(
            match_id=match_data.get('match_id'),
            opportunity_type='fatigue_exploit',
            strategy='Fatigue Exploit',
            expected_value_pct=ev_pct,
            kelly_stake_pct=0.0,
            confidence_score=confidence,
            reasoning=reasoning
        )
        
        logger.info(f"✅ Fatigue opportunity detected: {player_name} vs {fatigued_name} (EV: {ev_pct:.1f}%)")
        return opportunity

