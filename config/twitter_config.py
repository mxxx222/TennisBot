"""
Twitter Intelligence Configuration

Stores Twitter API configuration and credentials.
"""

import os
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

class TwitterConfig:
    """Twitter Intelligence configuration"""
    
    # Twitter API v2 Credentials
    BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN', '')
    API_KEY = os.getenv('TWITTER_API_KEY', '')
    API_SECRET = os.getenv('TWITTER_API_SECRET', '')
    ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN', '')
    ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET', '')
    
    # Verified Cappers (accounts to track)
    VERIFIED_CAPPERS = [
        '@TheSharpSide',
        '@BettingPros',
        '@OddsChecker',
        '@ArbitrageAlert',
        '@LineMovementLive',
        '@InjuryReport',
        '@WeatherSports'
    ]
    
    # Hashtags to monitor
    HASHTAGS = [
        '#BettingTips',
        '#Arbitrage',
        '#ValueBet',
        '#SharpMoney',
        '#SportsBetting'
    ]
    
    # Scan frequencies (in seconds)
    CAPPER_SCAN_INTERVAL = 300  # 5 minutes
    HASHTAG_SCAN_INTERVAL = 180  # 3 minutes
    
    # Rate limiting
    MAX_TWEETS_PER_USER = 20
    MAX_TWEETS_PER_HASHTAG = 50
    
    # Performance tracking
    MIN_WIN_RATE = 0.55  # 55% minimum win rate
    MIN_ENGAGEMENT_RATE = 0.05  # 5% minimum engagement
    TRACKING_WINDOW_DAYS = 30
    
    # Confidence boosting
    VERIFIED_CAPPER_BOOST = 1.20  # 20% boost for verified cappers
    HIGH_ENGAGEMENT_BOOST = 1.15  # 15% boost for high engagement
    
    @classmethod
    def is_configured(cls) -> bool:
        """Check if Twitter API is properly configured"""
        return bool(cls.BEARER_TOKEN or (cls.API_KEY and cls.API_SECRET))
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return {
            'bearer_token': cls.BEARER_TOKEN,
            'verified_cappers': cls.VERIFIED_CAPPERS,
            'hashtags': cls.HASHTAGS,
            'capper_scan_interval': cls.CAPPER_SCAN_INTERVAL,
            'hashtag_scan_interval': cls.HASHTAG_SCAN_INTERVAL,
        }

