"""
Reddit Tips Validator

Phase 3: Validate Reddit tips against our AI predictions
Compare Reddit tips to our models and boost confidence when aligned
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from .reddit_client import RedditClient
from .tip_extractor import TipExtractor, RedditTip
from .reddit_utils import is_recent_post, calculate_text_similarity
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.reddit_config import RedditConfig

logger = logging.getLogger(__name__)

@dataclass
class TipValidationResult:
    """Result of validating a Reddit tip against our prediction"""
    tip: RedditTip
    our_prediction: Dict[str, Any]
    agreement_score: float  # 0-100, how much they agree
    alignment: str  # 'aligned', 'opposed', 'neutral', 'unclear'
    confidence_boost: float  # Confidence multiplier to apply
    validation_note: str
    timestamp: str

class RedditTipsValidator:
    """Validate Reddit tips against our AI predictions"""
    
    def __init__(self, config: Optional[RedditConfig] = None):
        self.config = config or RedditConfig
        self.reddit_client = RedditClient(self.config)
        self.tip_extractor = TipExtractor()
        self.tip_history = []  # Track tip accuracy over time
        
        logger.info("✅ Reddit Tips Validator initialized")
    
    async def get_recent_tips(
        self,
        max_posts_per_subreddit: int = 50
    ) -> List[RedditTip]:
        """
        Get recent betting tips from Reddit
        
        Args:
            max_posts_per_subreddit: Maximum posts to scan per subreddit
        
        Returns:
            List of extracted tips
        """
        if not self.reddit_client.is_available:
            logger.warning("Reddit API not available for tips extraction")
            return []
        
        logger.info("🔍 Extracting betting tips from Reddit...")
        
        all_tips = []
        
        for subreddit_name in self.config.TIPS_SUBREDDITS:
            try:
                # Get recent posts
                posts = self.reddit_client.get_subreddit_posts(
                    subreddit_name=subreddit_name,
                    limit=max_posts_per_subreddit,
                    sort='new',
                    time_filter='day'
                )
                
                # Extract tips from each post
                for post in posts:
                    if is_recent_post(post, max_age_hours=24):
                        tips = self.tip_extractor.extract_tips_from_post(post, subreddit_name)
                        all_tips.extend(tips)
                
                logger.info(f"✅ Extracted {len([t for t in all_tips if t.subreddit == subreddit_name])} tips from r/{subreddit_name}")
                
            except Exception as e:
                logger.error(f"❌ Error extracting tips from r/{subreddit_name}: {e}")
                continue
        
        logger.info(f"💰 Total tips extracted: {len(all_tips)}")
        return all_tips
    
    def validate_tip_against_prediction(
        self,
        tip: RedditTip,
        our_prediction: Dict[str, Any]
    ) -> TipValidationResult:
        """
        Validate a Reddit tip against our AI prediction
        
        Args:
            tip: Reddit tip to validate
            our_prediction: Our AI prediction dictionary
        
        Returns:
            TipValidationResult with agreement score and alignment
        """
        try:
            # Extract our selection
            our_selection = our_prediction.get('recommended_bet', '').lower()
            our_match = our_prediction.get('match_info', {})
            our_home = our_match.get('home_team', '').lower() if isinstance(our_match, dict) else ''
            our_away = our_match.get('away_team', '').lower() if isinstance(our_match, dict) else ''
            
            # Extract tip selection
            tip_selection = tip.selection.lower()
            tip_match = tip.match_info or {}
            tip_home = tip_match.get('home_team', '').lower()
            tip_away = tip_match.get('away_team', '').lower()
            
            # Check if matches are the same
            match_alignment = self._check_match_alignment(
                our_home, our_away, tip_home, tip_away
            )
            
            if not match_alignment:
                return TipValidationResult(
                    tip=tip,
                    our_prediction=our_prediction,
                    agreement_score=0.0,
                    alignment='unclear',
                    confidence_boost=1.0,
                    validation_note="Matches don't align",
                    timestamp=datetime.now().isoformat()
                )
            
            # Check selection alignment
            selection_alignment = self._check_selection_alignment(
                our_selection, tip_selection, tip_home, tip_away
            )
            
            # Calculate agreement score
            agreement_score = self._calculate_agreement_score(
                selection_alignment, tip, our_prediction
            )
            
            # Determine alignment
            if agreement_score >= self.config.TIPS_AGREEMENT_THRESHOLD * 100:
                alignment = 'aligned'
                confidence_boost = 1.25  # 25% boost when strongly aligned
                validation_note = "Reddit tip strongly aligns with our prediction"
            elif agreement_score >= 50:
                alignment = 'aligned'
                confidence_boost = 1.15  # 15% boost when moderately aligned
                validation_note = "Reddit tip aligns with our prediction"
            elif agreement_score >= 20:
                alignment = 'neutral'
                confidence_boost = 1.0  # No change
                validation_note = "Reddit tip partially aligns"
            else:
                alignment = 'opposed'
                confidence_boost = 0.9  # 10% reduction when opposed
                validation_note = "Reddit tip differs from our prediction - investigate"
            
            return TipValidationResult(
                tip=tip,
                our_prediction=our_prediction,
                agreement_score=round(agreement_score, 1),
                alignment=alignment,
                confidence_boost=confidence_boost,
                validation_note=validation_note,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error validating tip: {e}")
            return TipValidationResult(
                tip=tip,
                our_prediction=our_prediction,
                agreement_score=0.0,
                alignment='unclear',
                confidence_boost=1.0,
                validation_note=f"Validation error: {str(e)}",
                timestamp=datetime.now().isoformat()
            )
    
    def _check_match_alignment(
        self,
        our_home: str,
        our_away: str,
        tip_home: str,
        tip_away: str
    ) -> bool:
        """Check if matches are the same"""
        if not (our_home and our_away and tip_home and tip_away):
            return False
        
        # Check if team names match (fuzzy matching)
        our_teams = {our_home, our_away}
        tip_teams = {tip_home, tip_away}
        
        # Check for overlap
        if our_teams.intersection(tip_teams):
            return True
        
        # Check similarity
        for our_team in our_teams:
            for tip_team in tip_teams:
                similarity = calculate_text_similarity(our_team, tip_team)
                if similarity > 0.7:  # 70% similarity threshold
                    return True
        
        return False
    
    def _check_selection_alignment(
        self,
        our_selection: str,
        tip_selection: str,
        tip_home: str,
        tip_away: str
    ) -> float:
        """Check if selections align (0-1 score)"""
        if not our_selection or not tip_selection:
            return 0.0
        
        # Direct match
        if tip_selection in our_selection or our_selection in tip_selection:
            return 1.0
        
        # Check if tip selection matches home/away
        if tip_home and tip_home in tip_selection:
            if tip_home in our_selection or 'home' in our_selection:
                return 1.0
        
        if tip_away and tip_away in tip_selection:
            if tip_away in our_selection or 'away' in our_selection:
                return 1.0
        
        # Similarity check
        similarity = calculate_text_similarity(our_selection, tip_selection)
        return similarity
    
    def _calculate_agreement_score(
        self,
        selection_alignment: float,
        tip: RedditTip,
        our_prediction: Dict[str, Any]
    ) -> float:
        """Calculate overall agreement score (0-100)"""
        base_score = selection_alignment * 100
        
        # Bonus for tip confidence indicators
        if tip.confidence_indicators:
            base_score += len(tip.confidence_indicators) * 5
        
        # Bonus for post score (upvotes)
        if tip.post_score > 5:
            base_score += min(10, tip.post_score / 2)
        
        # Bonus for odds alignment (if both have odds)
        if tip.odds and 'odds' in our_prediction:
            our_odds = our_prediction.get('odds', 0)
            if our_odds > 0:
                odds_diff = abs(tip.odds - our_odds) / our_odds
                if odds_diff < 0.1:  # Within 10%
                    base_score += 10
        
        return min(100.0, base_score)
    
    async def validate_tips_against_predictions(
        self,
        tips: List[RedditTip],
        our_predictions: List[Dict[str, Any]]
    ) -> List[TipValidationResult]:
        """
        Validate multiple tips against multiple predictions
        
        Args:
            tips: List of Reddit tips
            our_predictions: List of our AI predictions
        
        Returns:
            List of validation results
        """
        validation_results = []
        
        for tip in tips:
            # Find matching prediction
            matching_prediction = self._find_matching_prediction(tip, our_predictions)
            
            if matching_prediction:
                result = self.validate_tip_against_prediction(tip, matching_prediction)
                validation_results.append(result)
        
        return validation_results
    
    def _find_matching_prediction(
        self,
        tip: RedditTip,
        predictions: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Find prediction that matches the tip's match"""
        tip_match = tip.match_info or {}
        tip_home = tip_match.get('home_team', '').lower()
        tip_away = tip_match.get('away_team', '').lower()
        
        for prediction in predictions:
            pred_match = prediction.get('match_info', {})
            if isinstance(pred_match, dict):
                pred_home = pred_match.get('home_team', '').lower()
                pred_away = pred_match.get('away_team', '').lower()
                
                if self._check_match_alignment(pred_home, pred_away, tip_home, tip_away):
                    return prediction
        
        return None
    
    def enhance_prediction_with_tip_validation(
        self,
        prediction: Dict[str, Any],
        validation_result: TipValidationResult
    ) -> Dict[str, Any]:
        """Enhance prediction based on tip validation result"""
        enhanced = prediction.copy()
        
        if validation_result.alignment == 'aligned':
            # Boost confidence
            original_confidence = enhanced.get('confidence_score', 0.5)
            enhanced['confidence_score'] = min(1.0, original_confidence * validation_result.confidence_boost)
            enhanced['reddit_tip_validation'] = {
                'agreement_score': validation_result.agreement_score,
                'alignment': validation_result.alignment,
                'validation_note': validation_result.validation_note
            }
        elif validation_result.alignment == 'opposed':
            # Reduce confidence slightly
            original_confidence = enhanced.get('confidence_score', 0.5)
            enhanced['confidence_score'] = max(0.0, original_confidence * validation_result.confidence_boost)
            enhanced['reddit_tip_validation'] = {
                'agreement_score': validation_result.agreement_score,
                'alignment': validation_result.alignment,
                'validation_note': validation_result.validation_note,
                'warning': 'Reddit tip differs from prediction'
            }
        
        return enhanced

