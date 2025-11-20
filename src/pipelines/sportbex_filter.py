#!/usr/bin/env python3
"""
Sportbex Match Filter
=====================

Filters tennis matches from Sportbex API based on criteria:
- Tournaments: ITF W15, W25, W35, ATP Challenger
- Odds range: 1.40-1.80
- Ranking delta: 20-80 places (Sprint 1 placeholder)
- Time window: Next 48 hours

Output: 5-20 candidates for human review
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from src.scrapers.sportbex_client import SportbexMatch

logger = logging.getLogger(__name__)


@dataclass
class TennisCandidate:
    """Represents a filtered tennis candidate for review"""
    match: SportbexMatch
    selected_player: str  # Player 1 or Player 2
    selected_odds: float
    ranking_delta: Optional[int] = None
    confidence_score: float = 0.0  # 0.0-1.0, higher is better
    filter_reason: str = ""  # Why this match was selected


class SportbexFilter:
    """Filters tennis matches based on criteria"""
    
    def __init__(self, 
                 min_odds: float = 1.40,
                 max_odds: float = 1.80,
                 min_ranking_delta: int = 20,
                 max_ranking_delta: int = 80,
                 allowed_tournaments: Optional[List[str]] = None,
                 min_candidates: int = 5,
                 max_candidates: int = 20):
        """
        Initialize filter
        
        Args:
            min_odds: Minimum odds (default: 1.40)
            max_odds: Maximum odds (default: 1.80)
            min_ranking_delta: Minimum ranking difference (default: 20)
            max_ranking_delta: Maximum ranking difference (default: 80)
            allowed_tournaments: List of allowed tournament types (default: ITF W15/W25/W35, ATP Challenger)
            min_candidates: Minimum candidates to return (default: 5)
            max_candidates: Maximum candidates to return (default: 20)
        """
        self.min_odds = min_odds
        self.max_odds = max_odds
        self.min_ranking_delta = min_ranking_delta
        self.max_ranking_delta = max_ranking_delta
        self.min_candidates = min_candidates
        self.max_candidates = max_candidates
        
        # Default allowed tournaments
        if allowed_tournaments is None:
            self.allowed_tournaments = ['W15', 'W25', 'W35', 'ATP Challenger', 'CHALLENGER']
        else:
            self.allowed_tournaments = allowed_tournaments
    
    def filter_matches(self, matches: List[SportbexMatch]) -> List[TennisCandidate]:
        """
        Filter matches based on criteria
        
        Args:
            matches: List of SportbexMatch objects
            
        Returns:
            List of TennisCandidate objects (5-20 candidates)
        """
        logger.info(f"Filtering {len(matches)} matches...")
        
        candidates = []
        
        for match in matches:
            # Check tournament type
            if not self._is_allowed_tournament(match):
                continue
            
            # Check time window (next 48 hours)
            if not self._is_within_time_window(match, hours=48):
                continue
            
            # Check odds for both players
            candidate1 = self._check_player_odds(match, match.player1, match.player1_odds, match.player2_odds)
            candidate2 = self._check_player_odds(match, match.player2, match.player2_odds, match.player1_odds)
            
            if candidate1:
                candidates.append(candidate1)
            if candidate2:
                candidates.append(candidate2)
        
        # Sort by confidence score (higher is better)
        candidates.sort(key=lambda x: x.confidence_score, reverse=True)
        
        # Limit to max_candidates
        candidates = candidates[:self.max_candidates]
        
        # If we have fewer than min_candidates, log warning but return what we have
        if len(candidates) < self.min_candidates:
            logger.warning(f"Only found {len(candidates)} candidates (minimum: {self.min_candidates})")
        
        logger.info(f"✅ Filtered to {len(candidates)} candidates")
        
        return candidates
    
    def _is_allowed_tournament(self, match: SportbexMatch) -> bool:
        """Check if tournament is in allowed list"""
        tournament_upper = match.tournament.upper()
        tier_upper = (match.tournament_tier or '').upper()
        
        for allowed in self.allowed_tournaments:
            if allowed.upper() in tournament_upper or allowed.upper() in tier_upper:
                return True
        
        return False
    
    def _is_within_time_window(self, match: SportbexMatch, hours: int = 48) -> bool:
        """Check if match is within time window"""
        if not match.commence_time:
            # If no time, assume it's valid (will be filtered later if needed)
            return True
        
        now = datetime.now()
        cutoff = now + timedelta(hours=hours)
        
        # Match should be in the future but within window
        return now < match.commence_time <= cutoff
    
    def _check_player_odds(self, 
                          match: SportbexMatch, 
                          player: str, 
                          player_odds: Optional[float],
                          opponent_odds: Optional[float]) -> Optional[TennisCandidate]:
        """
        Check if player odds meet criteria
        
        Args:
            match: SportbexMatch object
            player: Player name
            player_odds: Player's odds
            opponent_odds: Opponent's odds
            
        Returns:
            TennisCandidate if criteria met, None otherwise
        """
        if not player_odds:
            return None
        
        # Check odds range
        if not (self.min_odds <= player_odds <= self.max_odds):
            return None
        
        # Calculate ranking delta if available
        ranking_delta = None
        if match.player1_ranking and match.player2_ranking:
            if player == match.player1:
                ranking_delta = abs(match.player1_ranking - match.player2_ranking)
            else:
                ranking_delta = abs(match.player2_ranking - match.player1_ranking)
        
        # Check ranking delta (if available)
        if ranking_delta is not None:
            if not (self.min_ranking_delta <= ranking_delta <= self.max_ranking_delta):
                # In Sprint 1, we're lenient - log but don't reject
                logger.debug(f"Ranking delta {ranking_delta} outside range {self.min_ranking_delta}-{self.max_ranking_delta}, but allowing (Sprint 1 placeholder)")
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            player_odds, 
            opponent_odds, 
            ranking_delta,
            match.tournament_tier
        )
        
        # Build filter reason
        filter_reason = f"Odds {player_odds:.2f} in range {self.min_odds}-{self.max_odds}"
        if ranking_delta:
            filter_reason += f", ranking delta {ranking_delta}"
        if match.tournament_tier:
            filter_reason += f", tournament {match.tournament_tier}"
        
        return TennisCandidate(
            match=match,
            selected_player=player,
            selected_odds=player_odds,
            ranking_delta=ranking_delta,
            confidence_score=confidence_score,
            filter_reason=filter_reason
        )
    
    def _calculate_confidence_score(self,
                                   player_odds: float,
                                   opponent_odds: Optional[float],
                                   ranking_delta: Optional[int],
                                   tournament_tier: Optional[str]) -> float:
        """
        Calculate confidence score (0.0-1.0)
        
        Higher score = better candidate
        """
        score = 0.5  # Base score
        
        # Odds closer to middle of range (1.55-1.65) get higher score
        ideal_odds = (self.min_odds + self.max_odds) / 2
        odds_distance = abs(player_odds - ideal_odds)
        max_distance = (self.max_odds - self.min_odds) / 2
        odds_score = 1.0 - (odds_distance / max_distance) if max_distance > 0 else 0.5
        score += odds_score * 0.3
        
        # Ranking delta in sweet spot (40-60) gets higher score
        if ranking_delta:
            if 40 <= ranking_delta <= 60:
                score += 0.2
            elif 20 <= ranking_delta < 40 or 60 < ranking_delta <= 80:
                score += 0.1
        
        # Tournament tier preference (W15 > W25 > W35 > Challenger)
        if tournament_tier:
            tier_scores = {
                'W15': 0.1,
                'W25': 0.08,
                'W35': 0.05,
                'ATP Challenger': 0.03
            }
            score += tier_scores.get(tournament_tier, 0)
        
        # Clamp to 0.0-1.0
        return max(0.0, min(1.0, score))


def filter_sportbex_matches(matches: List[SportbexMatch],
                           min_odds: float = 1.40,
                           max_odds: float = 1.80,
                           min_candidates: int = 5,
                           max_candidates: int = 20) -> List[TennisCandidate]:
    """
    Convenience function to filter matches
    
    Args:
        matches: List of SportbexMatch objects
        min_odds: Minimum odds
        max_odds: Maximum odds
        min_candidates: Minimum candidates to return
        max_candidates: Maximum candidates to return
        
    Returns:
        List of TennisCandidate objects
    """
    filter_obj = SportbexFilter(
        min_odds=min_odds,
        max_odds=max_odds,
        min_candidates=min_candidates,
        max_candidates=max_candidates
    )
    
    return filter_obj.filter_matches(matches)


if __name__ == "__main__":
    # Test filter
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create sample matches
    from src.scrapers.sportbex_client import SportbexMatch
    
    sample_matches = [
        SportbexMatch(
            match_id="1",
            tournament="ITF W15 Antalya",
            player1="Player A",
            player2="Player B",
            player1_odds=1.65,
            player2_odds=2.20,
            commence_time=datetime.now() + timedelta(hours=24),
            tournament_tier="W15",
            player1_ranking=250,
            player2_ranking=290
        ),
        SportbexMatch(
            match_id="2",
            tournament="ATP Challenger",
            player1="Player C",
            player2="Player D",
            player1_odds=1.50,
            player2_odds=2.50,
            commence_time=datetime.now() + timedelta(hours=36),
            tournament_tier="ATP Challenger",
            player1_ranking=180,
            player2_ranking=220
        ),
    ]
    
    filter_obj = SportbexFilter()
    candidates = filter_obj.filter_matches(sample_matches)
    
    print(f"\n✅ Filtered to {len(candidates)} candidates:")
    for i, candidate in enumerate(candidates, 1):
        print(f"\n{i}. {candidate.selected_player} (odds: {candidate.selected_odds:.2f})")
        print(f"   vs {candidate.match.player2 if candidate.selected_player == candidate.match.player1 else candidate.match.player1}")
        print(f"   Tournament: {candidate.match.tournament}")
        print(f"   Confidence: {candidate.confidence_score:.2f}")
        print(f"   Reason: {candidate.filter_reason}")

