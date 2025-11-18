"""
Twitter Intelligence Client

Twitter API wrapper for intelligence gathering
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.twitter_config import TwitterConfig

try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False
    tweepy = None

logger = logging.getLogger(__name__)

class TwitterIntelligenceClient:
    """Twitter client for intelligence gathering"""
    
    def __init__(self, config: Optional[TwitterConfig] = None):
        self.config = config or TwitterConfig
        
        if not self.config.is_configured():
            logger.warning("⚠️ Twitter API not configured. Set TWITTER_BEARER_TOKEN or API credentials.")
            self.client = None
            self.api = None
            self.is_available = False
        elif not TWEEPY_AVAILABLE:
            logger.warning("⚠️ tweepy not available. Install with: pip install tweepy")
            self.client = None
            self.api = None
            self.is_available = False
        else:
            try:
                # Use Bearer Token for read-only access
                if self.config.BEARER_TOKEN:
                    self.client = tweepy.Client(
                        bearer_token=self.config.BEARER_TOKEN,
                        wait_on_rate_limit=True
                    )
                else:
                    # Use OAuth 1.0a for full access
                    auth = tweepy.OAuthHandler(
                        self.config.API_KEY,
                        self.config.API_SECRET
                    )
                    auth.set_access_token(
                        self.config.ACCESS_TOKEN,
                        self.config.ACCESS_TOKEN_SECRET
                    )
                    self.api = tweepy.API(auth, wait_on_rate_limit=True)
                    self.client = None
                
                self.is_available = True
                logger.info("✅ Twitter Intelligence Client initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Twitter client: {e}")
                self.client = None
                self.api = None
                self.is_available = False
    
    def get_user_tweets(
        self,
        username: str,
        limit: int = 20,
        hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get recent tweets from a user
        
        Args:
            username: Twitter username (with or without @)
            limit: Maximum number of tweets
            hours_back: How many hours back to look
        
        Returns:
            List of tweet dictionaries
        """
        if not self.is_available:
            return []
        
        try:
            # Remove @ if present
            username = username.lstrip('@')
            
            tweets = []
            
            if self.client:
                # Use Twitter API v2
                user = self.client.get_user(username=username)
                if not user.data:
                    return []
                
                user_id = user.data.id
                
                # Get tweets
                response = self.client.get_users_tweets(
                    id=user_id,
                    max_results=min(limit, 100),
                    tweet_fields=['created_at', 'public_metrics', 'author_id']
                )
                
                if response.data:
                    cutoff_time = datetime.now() - timedelta(hours=hours_back)
                    
                    for tweet in response.data:
                        if tweet.created_at >= cutoff_time:
                            tweet_data = {
                                'id': tweet.id,
                                'text': tweet.text,
                                'created_at': tweet.created_at.isoformat(),
                                'author': username,
                                'likes': tweet.public_metrics.get('like_count', 0) if hasattr(tweet, 'public_metrics') else 0,
                                'retweets': tweet.public_metrics.get('retweet_count', 0) if hasattr(tweet, 'public_metrics') else 0,
                                'replies': tweet.public_metrics.get('reply_count', 0) if hasattr(tweet, 'public_metrics') else 0,
                            }
                            tweets.append(tweet_data)
            
            elif self.api:
                # Use Twitter API v1.1
                cutoff_time = datetime.now() - timedelta(hours=hours_back)
                
                for tweet in tweepy.Cursor(
                    self.api.user_timeline,
                    screen_name=username,
                    count=limit,
                    tweet_mode='extended'
                ).items(limit):
                    if tweet.created_at >= cutoff_time:
                        tweet_data = {
                            'id': tweet.id,
                            'text': tweet.full_text,
                            'created_at': tweet.created_at.isoformat(),
                            'author': username,
                            'likes': tweet.favorite_count,
                            'retweets': tweet.retweet_count,
                            'replies': tweet.reply_count if hasattr(tweet, 'reply_count') else 0,
                        }
                        tweets.append(tweet_data)
            
            logger.info(f"✅ Retrieved {len(tweets)} tweets from @{username}")
            return tweets
            
        except Exception as e:
            logger.error(f"❌ Error getting tweets from @{username}: {e}")
            return []
    
    def search_hashtag(
        self,
        hashtag: str,
        limit: int = 50,
        hours_back: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Search tweets by hashtag
        
        Args:
            hashtag: Hashtag to search (with or without #)
            limit: Maximum number of tweets
            hours_back: How many hours back to look
        
        Returns:
            List of tweet dictionaries
        """
        if not self.is_available:
            return []
        
        try:
            # Add # if not present
            if not hashtag.startswith('#'):
                hashtag = f"#{hashtag}"
            
            tweets = []
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            if self.client:
                # Use Twitter API v2
                query = f"{hashtag} -is:retweet lang:en"
                
                response = self.client.search_recent_tweets(
                    query=query,
                    max_results=min(limit, 100),
                    tweet_fields=['created_at', 'public_metrics', 'author_id']
                )
                
                if response.data:
                    for tweet in response.data:
                        if tweet.created_at >= cutoff_time:
                            tweet_data = {
                                'id': tweet.id,
                                'text': tweet.text,
                                'created_at': tweet.created_at.isoformat(),
                                'hashtag': hashtag,
                                'likes': tweet.public_metrics.get('like_count', 0) if hasattr(tweet, 'public_metrics') else 0,
                                'retweets': tweet.public_metrics.get('retweet_count', 0) if hasattr(tweet, 'public_metrics') else 0,
                            }
                            tweets.append(tweet_data)
            
            elif self.api:
                # Use Twitter API v1.1
                for tweet in tweepy.Cursor(
                    self.api.search_tweets,
                    q=hashtag,
                    count=limit,
                    tweet_mode='extended',
                    lang='en'
                ).items(limit):
                    if tweet.created_at >= cutoff_time:
                        tweet_data = {
                            'id': tweet.id,
                            'text': tweet.full_text,
                            'created_at': tweet.created_at.isoformat(),
                            'hashtag': hashtag,
                            'likes': tweet.favorite_count,
                            'retweets': tweet.retweet_count,
                        }
                        tweets.append(tweet_data)
            
            logger.info(f"✅ Retrieved {len(tweets)} tweets for {hashtag}")
            return tweets
            
        except Exception as e:
            logger.error(f"❌ Error searching hashtag {hashtag}: {e}")
            return []
    
    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get information about a Twitter user"""
        if not self.is_available:
            return None
        
        try:
            username = username.lstrip('@')
            
            if self.client:
                user = self.client.get_user(username=username)
                if user.data:
                    return {
                        'id': user.data.id,
                        'username': user.data.username,
                        'name': user.data.name,
                        'verified': user.data.verified if hasattr(user.data, 'verified') else False,
                        'followers_count': user.data.public_metrics.get('followers_count', 0) if hasattr(user.data, 'public_metrics') else 0,
                    }
            
            elif self.api:
                user = self.api.get_user(screen_name=username)
                return {
                    'id': user.id,
                    'username': user.screen_name,
                    'name': user.name,
                    'verified': user.verified,
                    'followers_count': user.followers_count,
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting user info for @{username}: {e}")
            return None

