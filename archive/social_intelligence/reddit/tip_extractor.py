"""
Tip Extractor

Extract betting tips from Reddit posts using NLP
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

from .reddit_utils import extract_match_info, extract_odds_from_text, extract_bookmaker_names

logger = logging.getLogger(__name__)

@dataclass
class RedditTip:
    """Betting tip extracted from Reddit"""
    tip_id: str
    post_id: str
    post_title: str
    post_url: str
    subreddit: str
    match_info: Optional[Dict[str, str]]
    selection: str  # Team/player to bet on
    market: str  # Market type (moneyline, over/under, etc.)
    odds: Optional[float]
    reasoning: str
    confidence_indicators: List[str]  # Keywords indicating confidence
    author: str
    post_score: int
    timestamp: str

class TipExtractor:
    """Extract betting tips from Reddit posts"""
    
    def __init__(self):
        # Market keywords
        self.market_keywords = {
            'moneyline': ['moneyline', 'ml', 'win', 'winner', 'to win', 'victory'],
            'over_under': ['over', 'under', 'o/u', 'total', 'goals', 'points'],
            'spread': ['spread', 'handicap', 'line', 'cover'],
            'both_teams_score': ['btts', 'both teams', 'both teams score'],
            'first_goal': ['first goal', 'fg', 'first to score'],
            'draw': ['draw', 'tie', 'x']
        }
        
        # Confidence indicators
        self.confidence_keywords = [
            'lock', 'guaranteed', 'sure thing', 'easy money', 'free money',
            'confident', 'certain', 'definitely', 'absolutely', '100%',
            'strong', 'very likely', 'highly likely'
        ]
        
        logger.info("✅ Tip Extractor initialized")
    
    def extract_tips_from_post(
        self,
        post: Dict[str, Any],
        subreddit_name: str
    ) -> List[RedditTip]:
        """
        Extract betting tips from a Reddit post
        
        Args:
            post: Reddit post data
            subreddit_name: Name of subreddit
        
        Returns:
            List of extracted tips
        """
        tips = []
        
        try:
            title = post.get('title', '')
            text = post.get('selftext', '')
            combined_text = f"{title} {text}"
            
            # Check if post contains betting language
            if not self._contains_betting_language(combined_text):
                return tips
            
            # Extract match information
            match_info = extract_match_info(combined_text)
            
            # Extract market type
            market = self._extract_market_type(combined_text)
            
            # Extract selection (team/player to bet on)
            selections = self._extract_selections(combined_text, match_info)
            
            # Extract odds
            odds_list = extract_odds_from_text(combined_text)
            odds = odds_list[0]['odds'] if odds_list and isinstance(odds_list[0]['odds'], (int, float)) else None
            
            # Extract reasoning
            reasoning = self._extract_reasoning(text)
            
            # Extract confidence indicators
            confidence_indicators = self._extract_confidence_indicators(combined_text)
            
            # Create tip for each selection
            for selection in selections:
                tip_id = f"{post.get('id', 'unknown')}_{selection}_{market}"
                
                tip = RedditTip(
                    tip_id=tip_id,
                    post_id=post.get('id', ''),
                    post_title=title[:200],
                    post_url=f"https://reddit.com{post.get('permalink', '')}",
                    subreddit=subreddit_name,
                    match_info=match_info,
                    selection=selection,
                    market=market,
                    odds=odds,
                    reasoning=reasoning,
                    confidence_indicators=confidence_indicators,
                    author=str(post.get('author', '[deleted]')),
                    post_score=post.get('score', 0),
                    timestamp=datetime.now().isoformat()
                )
                
                tips.append(tip)
            
            # If no selections found but match info exists, create generic tip
            if not selections and match_info:
                tip_id = f"{post.get('id', 'unknown')}_generic"
                tip = RedditTip(
                    tip_id=tip_id,
                    post_id=post.get('id', ''),
                    post_title=title[:200],
                    post_url=f"https://reddit.com{post.get('permalink', '')}",
                    subreddit=subreddit_name,
                    match_info=match_info,
                    selection='unknown',
                    market=market or 'moneyline',
                    odds=odds,
                    reasoning=reasoning,
                    confidence_indicators=confidence_indicators,
                    author=str(post.get('author', '[deleted]')),
                    post_score=post.get('score', 0),
                    timestamp=datetime.now().isoformat()
                )
                tips.append(tip)
            
        except Exception as e:
            logger.debug(f"Error extracting tips from post {post.get('id', 'unknown')}: {e}")
        
        return tips
    
    def _contains_betting_language(self, text: str) -> bool:
        """Check if text contains betting-related language"""
        betting_keywords = [
            'bet', 'pick', 'tip', 'play', 'lock', 'fade', 'take',
            'moneyline', 'over', 'under', 'spread', 'odds',
            'win', 'lose', 'cover', 'push'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in betting_keywords)
    
    def _extract_market_type(self, text: str) -> str:
        """Extract market type from text"""
        text_lower = text.lower()
        
        for market, keywords in self.market_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return market
        
        return 'moneyline'  # Default
    
    def _extract_selections(
        self,
        text: str,
        match_info: Optional[Dict[str, str]]
    ) -> List[str]:
        """Extract betting selections (teams/players) from text"""
        selections = []
        text_lower = text.lower()
        
        if match_info:
            home_team = match_info.get('home_team', '').lower()
            away_team = match_info.get('away_team', '').lower()
            
            # Check for explicit mentions
            if home_team and home_team in text_lower:
                # Check context - is it positive or negative?
                home_context = self._get_context_around(text, home_team, window=50)
                if self._is_positive_selection(home_context):
                    selections.append(match_info['home_team'])
            
            if away_team and away_team in text_lower:
                away_context = self._get_context_around(text, away_team, window=50)
                if self._is_positive_selection(away_context):
                    selections.append(match_info['away_team'])
        
        # Try to extract using patterns
        selection_patterns = [
            r'bet\s+(?:on\s+)?([A-Z][a-zA-Z\s]+)',
            r'pick\s+(?:is\s+)?([A-Z][a-zA-Z\s]+)',
            r'take\s+([A-Z][a-zA-Z\s]+)',
            r'([A-Z][a-zA-Z\s]+)\s+(?:to\s+)?win',
        ]
        
        for pattern in selection_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                selection = match.group(1).strip()
                if len(selection) > 2 and selection not in selections:
                    selections.append(selection)
        
        return selections[:3]  # Limit to 3 selections
    
    def _get_context_around(self, text: str, keyword: str, window: int = 50) -> str:
        """Get context around a keyword"""
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        
        if keyword_lower not in text_lower:
            return ""
        
        index = text_lower.find(keyword_lower)
        start = max(0, index - window)
        end = min(len(text), index + len(keyword) + window)
        
        return text[start:end]
    
    def _is_positive_selection(self, context: str) -> bool:
        """Check if context indicates positive selection (betting on)"""
        positive_indicators = [
            'bet on', 'take', 'pick', 'lock', 'play', 'fade', 'against',
            'win', 'will win', 'going to win', 'should win'
        ]
        
        negative_indicators = [
            'fade', 'against', 'lose', 'will lose', 'going to lose'
        ]
        
        context_lower = context.lower()
        
        # Check for negative indicators first
        if any(indicator in context_lower for indicator in negative_indicators):
            return False
        
        # Check for positive indicators
        return any(indicator in context_lower for indicator in positive_indicators)
    
    def _extract_reasoning(self, text: str) -> str:
        """Extract reasoning/analysis from text"""
        # Look for common reasoning patterns
        reasoning_patterns = [
            r'because\s+(.+?)(?:\.|$)',
            r'reason\s+(?:is\s+)?(.+?)(?:\.|$)',
            r'analysis[:\s]+(.+?)(?:\.|$)',
        ]
        
        reasoning_parts = []
        
        for pattern in reasoning_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                reasoning = match.group(1).strip()
                if len(reasoning) > 10:
                    reasoning_parts.append(reasoning)
        
        if reasoning_parts:
            return ' '.join(reasoning_parts[:2])  # First 2 reasoning parts
        
        # Fallback: return first 200 characters of text
        return text[:200] if text else ""
    
    def _extract_confidence_indicators(self, text: str) -> List[str]:
        """Extract confidence indicators from text"""
        found_indicators = []
        text_lower = text.lower()
        
        for indicator in self.confidence_keywords:
            if indicator in text_lower:
                found_indicators.append(indicator)
        
        return found_indicators

