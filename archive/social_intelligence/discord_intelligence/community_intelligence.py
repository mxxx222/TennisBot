"""
Community Intelligence

Aggregate community wisdom from Discord discussions
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CommunityConsensus:
    """Community consensus on a match"""
    match_id: str
    home_team: str
    away_team: str
    home_votes: int
    away_votes: int
    draw_votes: int
    total_votes: int
    confidence: float
    timestamp: str

class CommunityIntelligence:
    """Aggregate community intelligence from Discord"""
    
    def __init__(self):
        self.match_mentions = defaultdict(lambda: {
            'home_votes': 0,
            'away_votes': 0,
            'draw_votes': 0,
            'total_mentions': 0,
            'last_updated': None
        })
        
        logger.info("✅ Community Intelligence initialized")
    
    def process_message(
        self,
        message: Dict[str, Any],
        match_info: Optional[Dict[str, str]] = None
    ):
        """Process a message for community intelligence"""
        if not match_info:
            return
        
        match_key = f"{match_info.get('home_team', '')}_{match_info.get('away_team', '')}"
        
        content = message.get('content', '').lower()
        
        # Detect sentiment/vote
        home_team = match_info.get('home_team', '').lower()
        away_team = match_info.get('away_team', '').lower()
        
        if home_team in content:
            # Check if positive sentiment for home
            if any(word in content for word in ['win', 'take', 'pick', 'bet', 'lock']):
                self.match_mentions[match_key]['home_votes'] += 1
        
        if away_team in content:
            # Check if positive sentiment for away
            if any(word in content for word in ['win', 'take', 'pick', 'bet', 'lock']):
                self.match_mentions[match_key]['away_votes'] += 1
        
        if 'draw' in content or 'tie' in content:
            self.match_mentions[match_key]['draw_votes'] += 1
        
        self.match_mentions[match_key]['total_mentions'] += 1
        self.match_mentions[match_key]['last_updated'] = datetime.now().isoformat()
    
    def get_consensus(
        self,
        home_team: str,
        away_team: str
    ) -> Optional[CommunityConsensus]:
        """Get community consensus for a match"""
        match_key = f"{home_team}_{away_team}"
        
        if match_key not in self.match_mentions:
            return None
        
        data = self.match_mentions[match_key]
        
        total_votes = data['home_votes'] + data['away_votes'] + data['draw_votes']
        
        if total_votes == 0:
            return None
        
        # Calculate confidence based on vote distribution
        max_votes = max(data['home_votes'], data['away_votes'], data['draw_votes'])
        confidence = max_votes / total_votes if total_votes > 0 else 0.0
        
        return CommunityConsensus(
            match_id=match_key,
            home_team=home_team,
            away_team=away_team,
            home_votes=data['home_votes'],
            away_votes=data['away_votes'],
            draw_votes=data['draw_votes'],
            total_votes=total_votes,
            confidence=confidence,
            timestamp=data['last_updated'] or datetime.now().isoformat()
        )
    
    def enhance_prediction_with_consensus(
        self,
        prediction: Dict[str, Any],
        consensus: Optional[CommunityConsensus]
    ) -> Dict[str, Any]:
        """Enhance prediction with community consensus"""
        if not consensus:
            return prediction
        
        enhanced = prediction.copy()
        original_confidence = enhanced.get('confidence_score', 0.5)
        
        # Check if consensus aligns with prediction
        our_selection = enhanced.get('recommended_bet', '').lower()
        
        aligns_with_home = (
            home_team.lower() in our_selection or
            'home' in our_selection
        ) if 'home_team' in enhanced.get('match_info', {}) else False
        
        aligns_with_away = (
            away_team.lower() in our_selection or
            'away' in our_selection
        ) if 'away_team' in enhanced.get('match_info', {}) else False
        
        # Apply consensus boost
        from config.discord_config import DiscordConfig
        
        if consensus.confidence > 0.6:  # Strong consensus
            if (aligns_with_home and consensus.home_votes > consensus.away_votes) or \
               (aligns_with_away and consensus.away_votes > consensus.home_votes):
                # Consensus aligns with our prediction
                enhanced['confidence_score'] = min(
                    1.0,
                    original_confidence * DiscordConfig.COMMUNITY_CONSENSUS_BOOST
                )
                enhanced['community_consensus'] = {
                    'total_votes': consensus.total_votes,
                    'confidence': consensus.confidence,
                    'alignment': 'aligned'
                }
        
        return enhanced

