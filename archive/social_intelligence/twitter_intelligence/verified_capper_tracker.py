"""
Verified Capper Tracker

Track verified profitable betting accounts
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import re

from .twitter_client import TwitterIntelligenceClient
from .performance_tracker import PerformanceTracker

logger = logging.getLogger(__name__)

@dataclass
class CapperPick:
    """Pick from a verified capper"""
    pick_id: str
    username: str
    tweet_id: str
    match_info: Dict[str, str]
    selection: str
    odds: Optional[float]
    engagement_rate: float
    timestamp: str

class VerifiedCapperTracker:
    """Track picks from verified cappers"""
    
    def __init__(self):
        self.client = TwitterIntelligenceClient()
        self.performance_tracker = PerformanceTracker()
        
        logger.info("✅ Verified Capper Tracker initialized")
    
    async def track_verified_cappers(
        self,
        usernames: List[str]
    ) -> List[CapperPick]:
        """Track picks from verified cappers"""
        if not self.client.is_available:
            return []
        
        logger.info("🔍 Tracking verified cappers...")
        
        all_picks = []
        
        for username in usernames:
            try:
                # Get user info
                user_info = self.client.get_user_info(username)
                if not user_info:
                    continue
                
                # Only track verified or high-follower accounts
                if not user_info.get('verified') and user_info.get('followers_count', 0) < 10000:
                    continue
                
                # Get recent tweets
                tweets = self.client.get_user_tweets(
                    username=username,
                    limit=20,
                    hours_back=24
                )
                
                for tweet in tweets:
                    # Extract betting pick
                    pick = self._extract_pick(tweet, username, user_info)
                    
                    if pick:
                        # Record pick for performance tracking
                        self.performance_tracker.record_pick(username, pick.__dict__)
                        
                        # Only include if from profitable capper
                        if self.performance_tracker.is_profitable_capper(username):
                            all_picks.append(pick)
                
            except Exception as e:
                logger.error(f"❌ Error tracking @{username}: {e}")
                continue
        
        logger.info(f"✅ Found {len(all_picks)} picks from verified cappers")
        return all_picks
    
    def _extract_pick(
        self,
        tweet: Dict[str, Any],
        username: str,
        user_info: Dict[str, Any]
    ) -> Optional[CapperPick]:
        """Extract betting pick from tweet"""
        text = tweet.get('text', '')
        
        # Check if contains betting language
        betting_keywords = ['bet', 'pick', 'lock', 'take', 'play', 'odds']
        if not any(keyword in text.lower() for keyword in betting_keywords):
            return None
        
        # Extract match info
        match_info = self._extract_match_info(text)
        if not match_info:
            return None
        
        # Extract selection
        selection = self._extract_selection(text, match_info)
        if not selection:
            return None
        
        # Extract odds
        odds = self._extract_odds(text)
        
        # Calculate engagement rate
        likes = tweet.get('likes', 0)
        retweets = tweet.get('retweets', 0)
        followers = user_info.get('followers_count', 1)
        engagement_rate = (likes + retweets) / followers if followers > 0 else 0.0
        
        pick_id = f"twitter_{username}_{tweet.get('id', 0)}"
        
        return CapperPick(
            pick_id=pick_id,
            username=username,
            tweet_id=str(tweet.get('id', '')),
            match_info=match_info,
            selection=selection,
            odds=odds,
            engagement_rate=engagement_rate,
            timestamp=tweet.get('created_at', datetime.now().isoformat())
        )
    
    def _extract_match_info(self, text: str) -> Optional[Dict[str, str]]:
        """Extract match information from text"""
        vs_patterns = [
            r'([A-Z][a-zA-Z\s]+)\s+vs\s+([A-Z][a-zA-Z\s]+)',
            r'([A-Z][a-zA-Z\s]+)\s+@\s+([A-Z][a-zA-Z\s]+)',
        ]
        
        for pattern in vs_patterns:
            match = re.search(pattern, text)
            if match:
                home_team = match.group(1).strip()
                away_team = match.group(2).strip()
                
                if len(home_team) > 2 and len(away_team) > 2:
                    return {
                        'home_team': home_team,
                        'away_team': away_team
                    }
        
        return None
    
    def _extract_selection(
        self,
        text: str,
        match_info: Dict[str, str]
    ) -> Optional[str]:
        """Extract betting selection from text"""
        home_team = match_info.get('home_team', '').lower()
        away_team = match_info.get('away_team', '').lower()
        text_lower = text.lower()
        
        if home_team in text_lower:
            if any(word in text_lower for word in ['win', 'take', 'pick', 'bet']):
                return match_info['home_team']
        
        if away_team in text_lower:
            if any(word in text_lower for word in ['win', 'take', 'pick', 'bet']):
                return match_info['away_team']
        
        return None
    
    def _extract_odds(self, text: str) -> Optional[float]:
        """Extract odds from text"""
        odds_patterns = [
            r'(\d+\.\d+)\s*(?:odds|@)',
            r'odds?\s*(?:of|are|at)?\s*(\d+\.\d+)',
            r'@\s*(\d+\.\d+)',
        ]
        
        for pattern in odds_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    odds = float(match.group(1))
                    if 1.01 <= odds <= 100:
                        return odds
                except ValueError:
                    continue
        
        return None

