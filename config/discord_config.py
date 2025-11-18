"""
Discord Intelligence Configuration

Stores Discord server configuration and credentials.
"""

import os
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

class DiscordConfig:
    """Discord Intelligence configuration"""
    
    # Discord Bot Token (from environment variables)
    BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN', '')
    
    # Premium Servers (paid Discord servers)
    PREMIUM_SERVERS = [
        'Sharp Bettors Only',      # $100/month
        'Arbitrage Hunters',       # $50/month
        'Sports Analytics Pro',    # $75/month
        'Line Shopping Network',   # $25/month
        'Insider Betting Info'    # $150/month
    ]
    
    # Community Servers (free but valuable)
    COMMUNITY_SERVERS = [
        'Sports Betting Community',
        'Betting Strategy Hub',
        'Arbitrage Alerts',
        'Sharp Money Tracker'
    ]
    
    # Channels to monitor in each server
    MONITORED_CHANNELS = [
        'general',
        'picks',
        'arbitrage',
        'sharp-money',
        'line-movement',
        'discussions'
    ]
    
    # Scan frequencies (in seconds)
    PREMIUM_SCAN_INTERVAL = 120  # 2 minutes for premium servers
    COMMUNITY_SCAN_INTERVAL = 600  # 10 minutes for community servers
    
    # Rate limiting
    MAX_MESSAGES_PER_CHANNEL = 100
    RATE_LIMIT_DELAY = 2.0  # Delay between channel scans
    
    # Sharp bettor tracking
    MIN_WIN_RATE = 0.55  # 55% minimum win rate
    MIN_ROI = 0.10  # 10% minimum ROI
    TRACKING_WINDOW_DAYS = 30
    
    # Confidence boosting
    SHARP_AGREEMENT_BOOST = 1.30  # 30% boost when sharp agrees
    COMMUNITY_CONSENSUS_BOOST = 1.15  # 15% boost for community consensus
    
    @classmethod
    def is_configured(cls) -> bool:
        """Check if Discord is properly configured"""
        return bool(cls.BOT_TOKEN)
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return {
            'bot_token': cls.BOT_TOKEN,
            'premium_servers': cls.PREMIUM_SERVERS,
            'community_servers': cls.COMMUNITY_SERVERS,
            'monitored_channels': cls.MONITORED_CHANNELS,
            'premium_scan_interval': cls.PREMIUM_SCAN_INTERVAL,
            'community_scan_interval': cls.COMMUNITY_SCAN_INTERVAL,
        }

