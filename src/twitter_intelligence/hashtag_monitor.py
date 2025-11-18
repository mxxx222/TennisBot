"""
Hashtag Monitor

Monitor betting-related hashtags for opportunities
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import re

from .twitter_client import TwitterIntelligenceClient

logger = logging.getLogger(__name__)

@dataclass
class HashtagOpportunity:
    """Opportunity found via hashtag"""
    opportunity_id: str
    hashtag: str
    tweet_id: str
    tweet_text: str
    author: str
    opportunity_type: str  # 'arbitrage', 'tip', 'news'
    match_info: Optional[Dict[str, str]]
    engagement_score: float
    timestamp: str

class HashtagMonitor:
    """Monitor betting hashtags for opportunities"""
    
    def __init__(self):
        self.client = TwitterIntelligenceClient()
        
        logger.info("✅ Hashtag Monitor initialized")
    
    async def monitor_hashtags(
        self,
        hashtags: List[str]
    ) -> List[HashtagOpportunity]:
        """Monitor hashtags for opportunities"""
        if not self.client.is_available:
            return []
        
        logger.info("🔍 Monitoring betting hashtags...")
        
        all_opportunities = []
        
        for hashtag in hashtags:
            try:
                tweets = self.client.search_hashtag(
                    hashtag=hashtag,
                    limit=50,
                    hours_back=6
                )
                
                for tweet in tweets:
                    opportunity = self._extract_opportunity(tweet, hashtag)
                    
                    if opportunity:
                        all_opportunities.append(opportunity)
                
            except Exception as e:
                logger.error(f"❌ Error monitoring {hashtag}: {e}")
                continue
        
        # Sort by engagement score
        all_opportunities.sort(key=lambda x: x.engagement_score, reverse=True)
        
        logger.info(f"✅ Found {len(all_opportunities)} opportunities from hashtags")
        return all_opportunities
    
    def _extract_opportunity(
        self,
        tweet: Dict[str, Any],
        hashtag: str
    ) -> Optional[HashtagOpportunity]:
        """Extract opportunity from tweet"""
        text = tweet.get('text', '')
        
        # Determine opportunity type
        opportunity_type = self._detect_opportunity_type(text, hashtag)
        
        if not opportunity_type:
            return None
        
        # Extract match info
        match_info = self._extract_match_info(text)
        
        # Calculate engagement score
        likes = tweet.get('likes', 0)
        retweets = tweet.get('retweets', 0)
        engagement_score = (likes * 1.0 + retweets * 2.0) / 100.0  # Normalized
        
        opportunity_id = f"hashtag_{hashtag}_{tweet.get('id', 0)}"
        
        return HashtagOpportunity(
            opportunity_id=opportunity_id,
            hashtag=hashtag,
            tweet_id=str(tweet.get('id', '')),
            tweet_text=text[:280],
            author=tweet.get('author', 'unknown'),
            opportunity_type=opportunity_type,
            match_info=match_info,
            engagement_score=engagement_score,
            timestamp=tweet.get('created_at', datetime.now().isoformat())
        )
    
    def _detect_opportunity_type(self, text: str, hashtag: str) -> Optional[str]:
        """Detect type of opportunity"""
        text_lower = text.lower()
        
        if hashtag.lower() == '#arbitrage':
            if any(keyword in text_lower for keyword in ['arbitrage', 'arb', 'sure bet', 'guaranteed']):
                return 'arbitrage'
        
        if any(keyword in text_lower for keyword in ['bet', 'pick', 'lock', 'tip']):
            return 'tip'
        
        if any(keyword in text_lower for keyword in ['injury', 'out', 'lineup', 'news']):
            return 'news'
        
        return None
    
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

