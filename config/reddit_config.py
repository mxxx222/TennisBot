"""
Reddit API Configuration

Stores Reddit API credentials and configuration.
Loads from environment variables for security.
"""

import os
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

class RedditConfig:
    """Reddit API configuration and credentials"""
    
    # Reddit API Credentials (from environment variables)
    CLIENT_ID = os.getenv('REDDIT_CLIENT_ID', '')
    CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET', '')
    USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'TennisBot/1.0 by /u/YourUsername')
    USERNAME = os.getenv('REDDIT_USERNAME', '')
    PASSWORD = os.getenv('REDDIT_PASSWORD', '')
    
    # Subreddits to monitor
    ARBITRAGE_SUBREDDITS = [
        'sportsbook',
        'sportsbetting',
        'gambling'
    ]
    
    SENTIMENT_SUBREDDITS = [
        'sportsbook',
        'sportsbetting',
        'tennis',
        'soccer',
        'nba',
        'nhl'
    ]
    
    TIPS_SUBREDDITS = [
        'sportsbook',
        'sportsbetting',
        'gambling'
    ]
    
    # Scan frequencies (in seconds)
    ARBITRAGE_SCAN_INTERVAL = 300  # 5 minutes
    SENTIMENT_SCAN_INTERVAL = 900  # 15 minutes
    TIPS_SCAN_INTERVAL = 1800  # 30 minutes
    
    # Rate limiting (Reddit allows 60 requests/minute)
    RATE_LIMIT_REQUESTS = 60
    RATE_LIMIT_WINDOW = 60  # seconds
    
    # Arbitrage keywords
    ARBITRAGE_KEYWORDS = [
        'arbitrage',
        'arb',
        'sure bet',
        'guaranteed profit',
        'guaranteed',
        'odds difference',
        'different odds',
        'line shopping',
        'bookmaker comparison',
        'risk free',
        'free money'
    ]
    
    # Minimum arbitrage margin from Reddit (1.5%)
    MIN_REDDIT_ARB_MARGIN = 0.015
    
    # ROI thresholds
    SENTIMENT_CONFIDENCE_BOOST = 0.15  # 15% boost when aligned
    SENTIMENT_CONFIDENCE_REDUCTION = 0.10  # 10% reduction when negative
    CONTRARIAN_OPPORTUNITY_BOOST = 0.20  # 20% boost when betting against hype
    CONTRARIAN_THRESHOLD = 0.75  # 75% public favor = contrarian opportunity
    TIPS_AGREEMENT_THRESHOLD = 0.80  # 80% agreement for confidence boost
    
    @classmethod
    def is_configured(cls) -> bool:
        """Check if Reddit API is properly configured"""
        return bool(
            cls.CLIENT_ID and
            cls.CLIENT_SECRET and
            cls.USER_AGENT and
            (cls.USERNAME or cls.USER_AGENT)  # Username optional for read-only
        )
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return {
            'client_id': cls.CLIENT_ID,
            'client_secret': cls.CLIENT_SECRET,
            'user_agent': cls.USER_AGENT,
            'username': cls.USERNAME,
            'password': cls.PASSWORD,
            'arbitrage_subreddits': cls.ARBITRAGE_SUBREDDITS,
            'sentiment_subreddits': cls.SENTIMENT_SUBREDDITS,
            'tips_subreddits': cls.TIPS_SUBREDDITS,
            'arbitrage_scan_interval': cls.ARBITRAGE_SCAN_INTERVAL,
            'sentiment_scan_interval': cls.SENTIMENT_SCAN_INTERVAL,
            'tips_scan_interval': cls.TIPS_SCAN_INTERVAL,
            'rate_limit_requests': cls.RATE_LIMIT_REQUESTS,
            'rate_limit_window': cls.RATE_LIMIT_WINDOW,
            'arbitrage_keywords': cls.ARBITRAGE_KEYWORDS,
            'min_reddit_arb_margin': cls.MIN_REDDIT_ARB_MARGIN,
        }

