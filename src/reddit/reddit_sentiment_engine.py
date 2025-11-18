"""
Reddit Sentiment Engine

Phase 2: Sentiment analysis for matches from Reddit discussions
Enhances predictions with crowd wisdom and contrarian opportunities
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from .reddit_client import RedditClient
from .sentiment_analyzer import SentimentAnalyzer
from .reddit_utils import extract_match_info, is_recent_post, clean_reddit_text
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.reddit_config import RedditConfig

logger = logging.getLogger(__name__)

@dataclass
class MatchSentiment:
    """Sentiment analysis for a match"""
    match_id: str
    home_team: str
    away_team: str
    sport: str
    home_sentiment: float
    away_sentiment: float
    home_percentage: float
    away_percentage: float
    neutral_percentage: float
    total_mentions: int
    confidence: float
    contrarian_opportunity: bool
    sentiment_label: str  # 'home_favored', 'away_favored', 'neutral', 'contrarian'
    timestamp: str

class RedditSentimentEngine:
    """Analyze sentiment from Reddit for match predictions"""
    
    def __init__(self, config: Optional[RedditConfig] = None):
        self.config = config or RedditConfig
        self.reddit_client = RedditClient(self.config)
        self.sentiment_analyzer = SentimentAnalyzer()
        self.sentiment_cache = {}  # Cache sentiment results
        
        logger.info("✅ Reddit Sentiment Engine initialized")
    
    async def get_match_sentiment(
        self,
        home_team: str,
        away_team: str,
        sport: Optional[str] = None,
        use_cache: bool = True
    ) -> Optional[MatchSentiment]:
        """
        Get sentiment analysis for a specific match
        
        Args:
            home_team: Home team name
            away_team: Away team name
            sport: Sport type (tennis, football, etc.)
            use_cache: Whether to use cached results
        
        Returns:
            MatchSentiment object or None
        """
        if not self.reddit_client.is_available:
            logger.debug("Reddit API not available for sentiment analysis")
            return None
        
        # Check cache
        cache_key = f"{home_team}_{away_team}_{sport or 'any'}"
        if use_cache and cache_key in self.sentiment_cache:
            cached_result, cached_time = self.sentiment_cache[cache_key]
            # Use cache if less than 15 minutes old
            if (datetime.now() - cached_time).total_seconds() < 900:
                return cached_result
        
        try:
            # Determine which subreddits to search
            subreddits = self._get_subreddits_for_sport(sport)
            
            all_posts = []
            
            # Search in relevant subreddits
            for subreddit_name in subreddits:
                # Get recent posts
                posts = self.reddit_client.get_subreddit_posts(
                    subreddit_name=subreddit_name,
                    limit=50,
                    sort='new',
                    time_filter='day'
                )
                
                # Filter posts that mention the match
                for post in posts:
                    if is_recent_post(post, max_age_hours=24):
                        text = f"{post.get('title', '')} {post.get('selftext', '')}".lower()
                        if (home_team.lower() in text or away_team.lower() in text):
                            all_posts.append(post)
                
                # Also search for team names
                for team_name in [home_team, away_team]:
                    search_posts = self.reddit_client.search_subreddit(
                        subreddit_name=subreddit_name,
                        query=team_name,
                        limit=25,
                        sort='new',
                        time_filter='day'
                    )
                    # Filter for posts mentioning both teams
                    for post in search_posts:
                        text = f"{post.get('title', '')} {post.get('selftext', '')}".lower()
                        if (home_team.lower() in text and away_team.lower() in text):
                            if post['id'] not in [p['id'] for p in all_posts]:
                                all_posts.append(post)
            
            if not all_posts:
                logger.debug(f"No Reddit posts found for {home_team} vs {away_team}")
                return None
            
            # Analyze sentiment
            sentiment_data = self.sentiment_analyzer.analyze_match_sentiment(
                all_posts, home_team, away_team
            )
            
            # Determine sentiment label and contrarian opportunity
            home_pct = sentiment_data['home_percentage']
            away_pct = sentiment_data['away_percentage']
            contrarian = False
            sentiment_label = 'neutral'
            
            if home_pct >= self.config.CONTRARIAN_THRESHOLD * 100:
                sentiment_label = 'home_favored'
                contrarian = True  # Public heavily favors home = contrarian opportunity
            elif away_pct >= self.config.CONTRARIAN_THRESHOLD * 100:
                sentiment_label = 'away_favored'
                contrarian = True  # Public heavily favors away = contrarian opportunity
            elif home_pct > away_pct + 10:
                sentiment_label = 'home_favored'
            elif away_pct > home_pct + 10:
                sentiment_label = 'away_favored'
            else:
                sentiment_label = 'neutral'
            
            # Generate match ID
            match_id = f"{home_team}_{away_team}_{datetime.now().strftime('%Y%m%d')}"
            
            match_sentiment = MatchSentiment(
                match_id=match_id,
                home_team=home_team,
                away_team=away_team,
                sport=sport or 'unknown',
                home_sentiment=sentiment_data['home_sentiment'],
                away_sentiment=sentiment_data['away_sentiment'],
                home_percentage=sentiment_data['home_percentage'],
                away_percentage=sentiment_data['away_percentage'],
                neutral_percentage=sentiment_data['neutral_percentage'],
                total_mentions=sentiment_data['total_mentions'],
                confidence=sentiment_data['confidence'],
                contrarian_opportunity=contrarian,
                sentiment_label=sentiment_label,
                timestamp=datetime.now().isoformat()
            )
            
            # Cache result
            self.sentiment_cache[cache_key] = (match_sentiment, datetime.now())
            
            logger.info(f"✅ Analyzed sentiment for {home_team} vs {away_team}: {sentiment_label}")
            
            return match_sentiment
            
        except Exception as e:
            logger.error(f"❌ Error getting match sentiment: {e}")
            return None
    
    def enhance_prediction_with_sentiment(
        self,
        prediction: Dict[str, Any],
        match_sentiment: Optional[MatchSentiment]
    ) -> Dict[str, Any]:
        """
        Enhance prediction with Reddit sentiment data
        
        Args:
            prediction: Original prediction dictionary
            match_sentiment: MatchSentiment object from Reddit
        
        Returns:
            Enhanced prediction dictionary
        """
        if not match_sentiment:
            return prediction
        
        enhanced = prediction.copy()
        original_confidence = enhanced.get('confidence_score', 0.5)
        
        # Determine if sentiment aligns with our prediction
        our_selection = enhanced.get('recommended_bet', '').lower()
        sentiment_label = match_sentiment.sentiment_label
        
        # Check alignment
        aligns_with_home = (
            'home' in our_selection or 
            match_sentiment.home_team.lower() in our_selection
        )
        aligns_with_away = (
            'away' in our_selection or 
            match_sentiment.away_team.lower() in our_selection
        )
        
        sentiment_aligns = False
        if sentiment_label == 'home_favored' and aligns_with_home:
            sentiment_aligns = True
        elif sentiment_label == 'away_favored' and aligns_with_away:
            sentiment_aligns = True
        
        # Apply sentiment adjustments
        if match_sentiment.contrarian_opportunity:
            # Contrarian opportunity - betting against public
            confidence_boost = self.config.CONTRARIAN_OPPORTUNITY_BOOST
            enhanced['confidence_score'] = min(1.0, original_confidence * (1 + confidence_boost))
            enhanced['contrarian_opportunity'] = True
            enhanced['sentiment_note'] = f"Public heavily favors {sentiment_label.replace('_favored', '')} - contrarian opportunity"
        
        elif sentiment_aligns:
            # Sentiment aligns with our prediction
            confidence_boost = self.config.SENTIMENT_CONFIDENCE_BOOST
            enhanced['confidence_score'] = min(1.0, original_confidence * (1 + confidence_boost))
            enhanced['sentiment_note'] = "Reddit sentiment aligns with prediction"
        
        else:
            # Sentiment doesn't align - reduce confidence slightly
            confidence_reduction = self.config.SENTIMENT_CONFIDENCE_REDUCTION
            enhanced['confidence_score'] = max(0.0, original_confidence * (1 - confidence_reduction))
            enhanced['sentiment_note'] = "Reddit sentiment differs from prediction"
        
        # Add sentiment metadata
        enhanced['reddit_sentiment'] = {
            'home_percentage': match_sentiment.home_percentage,
            'away_percentage': match_sentiment.away_percentage,
            'sentiment_label': match_sentiment.sentiment_label,
            'confidence': match_sentiment.confidence,
            'total_mentions': match_sentiment.total_mentions
        }
        
        return enhanced
    
    def _get_subreddits_for_sport(self, sport: Optional[str]) -> List[str]:
        """Get relevant subreddits for a sport"""
        if not sport:
            return self.config.SENTIMENT_SUBREDDITS
        
        sport_subreddits = {
            'tennis': ['tennis', 'sportsbook', 'sportsbetting'],
            'football': ['soccer', 'sportsbook', 'sportsbetting'],
            'basketball': ['nba', 'sportsbook', 'sportsbetting'],
            'ice_hockey': ['nhl', 'sportsbook', 'sportsbetting'],
        }
        
        base_subreddits = sport_subreddits.get(sport.lower(), self.config.SENTIMENT_SUBREDDITS)
        
        # Always include general betting subreddits
        all_subreddits = list(base_subreddits)
        for sub in ['sportsbook', 'sportsbetting']:
            if sub not in all_subreddits:
                all_subreddits.append(sub)
        
        return all_subreddits

