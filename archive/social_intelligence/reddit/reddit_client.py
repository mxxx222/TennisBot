"""
Reddit API Client

Reddit API wrapper with rate limiting and error handling
"""

import praw
import time
import logging
from typing import Dict, List, Optional, Any, Iterator
from datetime import datetime, timedelta
from collections import deque
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.reddit_config import RedditConfig

logger = logging.getLogger(__name__)

class RedditClient:
    """Reddit API client with rate limiting"""
    
    def __init__(self, config: Optional[RedditConfig] = None):
        self.config = config or RedditConfig
        
        if not self.config.is_configured():
            logger.warning("⚠️ Reddit API not configured. Set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, and REDDIT_USER_AGENT environment variables.")
            self.reddit = None
            self.is_available = False
        else:
            try:
                self.reddit = praw.Reddit(
                    client_id=self.config.CLIENT_ID,
                    client_secret=self.config.CLIENT_SECRET,
                    user_agent=self.config.USER_AGENT,
                    username=self.config.USERNAME if self.config.USERNAME else None,
                    password=self.config.PASSWORD if self.config.PASSWORD else None
                )
                # Test connection
                self.reddit.user.me() if self.config.USERNAME else None
                self.is_available = True
                logger.info("✅ Reddit API client initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Reddit API: {e}")
                self.reddit = None
                self.is_available = False
        
        # Rate limiting
        self.request_times = deque()
        self.rate_limit_requests = self.config.RATE_LIMIT_REQUESTS
        self.rate_limit_window = self.config.RATE_LIMIT_WINDOW
        
        # Cache for recent requests
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes cache
    
    def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        now = time.time()
        
        # Remove old requests outside the window
        while self.request_times and self.request_times[0] < now - self.rate_limit_window:
            self.request_times.popleft()
        
        # If at limit, wait
        if len(self.request_times) >= self.rate_limit_requests:
            sleep_time = self.rate_limit_window - (now - self.request_times[0])
            if sleep_time > 0:
                logger.debug(f"Rate limit reached, sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)
                # Clean up again after sleep
                while self.request_times and self.request_times[0] < now - self.rate_limit_window:
                    self.request_times.popleft()
        
        # Record this request
        self.request_times.append(time.time())
    
    def _get_cached(self, cache_key: str) -> Optional[Any]:
        """Get cached data if still valid"""
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return data
            else:
                del self.cache[cache_key]
        return None
    
    def _set_cache(self, cache_key: str, data: Any):
        """Cache data with timestamp"""
        self.cache[cache_key] = (data, time.time())
    
    def get_subreddit_posts(
        self,
        subreddit_name: str,
        limit: int = 25,
        sort: str = 'new',
        time_filter: str = 'day'
    ) -> List[Dict[str, Any]]:
        """
        Get posts from a subreddit
        
        Args:
            subreddit_name: Name of subreddit (without r/)
            limit: Number of posts to retrieve
            sort: Sort method ('new', 'hot', 'top')
            time_filter: Time filter for 'top' sort ('hour', 'day', 'week', 'month', 'year', 'all')
        
        Returns:
            List of post dictionaries
        """
        if not self.is_available:
            logger.warning("Reddit API not available")
            return []
        
        cache_key = f"subreddit_{subreddit_name}_{sort}_{time_filter}_{limit}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            self._check_rate_limit()
            
            subreddit = self.reddit.subreddit(subreddit_name)
            
            if sort == 'new':
                posts = subreddit.new(limit=limit)
            elif sort == 'hot':
                posts = subreddit.hot(limit=limit)
            elif sort == 'top':
                posts = subreddit.top(limit=limit, time_filter=time_filter)
            else:
                posts = subreddit.new(limit=limit)
            
            post_list = []
            for post in posts:
                try:
                    post_data = {
                        'id': post.id,
                        'title': post.title,
                        'selftext': post.selftext,
                        'author': str(post.author) if post.author else '[deleted]',
                        'score': post.score,
                        'upvote_ratio': post.upvote_ratio,
                        'num_comments': post.num_comments,
                        'created_utc': post.created_utc,
                        'url': post.url,
                        'permalink': post.permalink,
                        'subreddit': str(post.subreddit),
                        'is_self': post.is_self,
                        'link_flair_text': post.link_flair_text,
                    }
                    post_list.append(post_data)
                except Exception as e:
                    logger.debug(f"Error processing post {post.id}: {e}")
                    continue
            
            self._set_cache(cache_key, post_list)
            logger.info(f"✅ Retrieved {len(post_list)} posts from r/{subreddit_name}")
            return post_list
            
        except Exception as e:
            logger.error(f"❌ Error getting posts from r/{subreddit_name}: {e}")
            return []
    
    def get_post_comments(
        self,
        post_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get comments from a post"""
        if not self.is_available:
            return []
        
        cache_key = f"comments_{post_id}_{limit}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            self._check_rate_limit()
            
            submission = self.reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)  # Remove "more comments" placeholders
            
            comments = []
            for comment in submission.comments.list()[:limit]:
                try:
                    comment_data = {
                        'id': comment.id,
                        'body': comment.body,
                        'author': str(comment.author) if comment.author else '[deleted]',
                        'score': comment.score,
                        'created_utc': comment.created_utc,
                        'parent_id': comment.parent_id,
                        'is_submitter': comment.is_submitter,
                    }
                    comments.append(comment_data)
                except Exception as e:
                    logger.debug(f"Error processing comment {comment.id}: {e}")
                    continue
            
            self._set_cache(cache_key, comments)
            return comments
            
        except Exception as e:
            logger.error(f"❌ Error getting comments for post {post_id}: {e}")
            return []
    
    def search_subreddit(
        self,
        subreddit_name: str,
        query: str,
        limit: int = 25,
        sort: str = 'new',
        time_filter: str = 'day'
    ) -> List[Dict[str, Any]]:
        """Search subreddit for posts matching query"""
        if not self.is_available:
            return []
        
        cache_key = f"search_{subreddit_name}_{query}_{sort}_{limit}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            self._check_rate_limit()
            
            subreddit = self.reddit.subreddit(subreddit_name)
            posts = subreddit.search(query, sort=sort, time_filter=time_filter, limit=limit)
            
            post_list = []
            for post in posts:
                try:
                    post_data = {
                        'id': post.id,
                        'title': post.title,
                        'selftext': post.selftext,
                        'author': str(post.author) if post.author else '[deleted]',
                        'score': post.score,
                        'created_utc': post.created_utc,
                        'subreddit': str(post.subreddit),
                    }
                    post_list.append(post_data)
                except Exception as e:
                    logger.debug(f"Error processing search result {post.id}: {e}")
                    continue
            
            self._set_cache(cache_key, post_list)
            return post_list
            
        except Exception as e:
            logger.error(f"❌ Error searching r/{subreddit_name}: {e}")
            return []

