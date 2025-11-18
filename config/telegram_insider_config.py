"""
Telegram Insider Channels Configuration

Stores Telegram channel configuration and credentials.
Loads from environment variables for security.
"""

import os
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

class TelegramInsiderConfig:
    """Telegram Insider Channels configuration"""
    
    # Telegram API Credentials (from environment variables)
    API_ID = os.getenv('TELEGRAM_API_ID', '')
    API_HASH = os.getenv('TELEGRAM_API_HASH', '')
    PHONE_NUMBER = os.getenv('TELEGRAM_PHONE_NUMBER', '')
    SESSION_NAME = os.getenv('TELEGRAM_SESSION_NAME', 'telegram_insider')
    
    # Premium Channels (paid tipster channels)
    PREMIUM_CHANNELS = [
        '@BettingProInsider',      # €50/month, 65% win rate
        '@ArbitrageAlerts',        # €30/month, instant arb alerts
        '@SharpMoneyMoves',        # €100/month, sharp betting intel
        '@OddsMovementTracker',    # €25/month, line movement alerts
        '@InsiderSportsInfo'       # €75/month, injury/lineup leaks
    ]
    
    # Free but valuable channels
    FREE_CHANNELS = [
        '@BettingTipsChannel',     # Free tips, filter for quality
        '@SureWinBets',           # Occasional arb opportunities
        '@SportsBettingGroup',    # Community intel
        '@OddsComparisonBot'      # Real-time odds comparison
    ]
    
    # Scan frequencies (in seconds)
    PREMIUM_SCAN_INTERVAL = 60  # 1 minute for premium channels
    FREE_SCAN_INTERVAL = 300  # 5 minutes for free channels
    
    # Rate limiting
    MAX_MESSAGES_PER_CHANNEL = 50  # Max messages to fetch per scan
    RATE_LIMIT_DELAY = 1.0  # Delay between channel scans (seconds)
    
    # Intel filtering
    MIN_CONFIDENCE_THRESHOLD = 0.75  # 75% minimum confidence for premium tips
    ARBITRAGE_MIN_MARGIN = 0.015  # 1.5% minimum arbitrage margin
    CONFIDENCE_BOOST_MULTIPLIER = 1.25  # 25% boost when premium tipsters agree
    
    # Performance tracking
    TRACK_PERFORMANCE = True
    MIN_WIN_RATE = 0.55  # 55% minimum win rate to follow tipster
    PERFORMANCE_WINDOW_DAYS = 30  # Track last 30 days
    
    @classmethod
    def is_configured(cls) -> bool:
        """Check if Telegram API is properly configured"""
        return bool(
            cls.API_ID and
            cls.API_HASH and
            cls.PHONE_NUMBER
        )
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return {
            'api_id': cls.API_ID,
            'api_hash': cls.API_HASH,
            'phone_number': cls.PHONE_NUMBER,
            'session_name': cls.SESSION_NAME,
            'premium_channels': cls.PREMIUM_CHANNELS,
            'free_channels': cls.FREE_CHANNELS,
            'premium_scan_interval': cls.PREMIUM_SCAN_INTERVAL,
            'free_scan_interval': cls.FREE_SCAN_INTERVAL,
            'max_messages_per_channel': cls.MAX_MESSAGES_PER_CHANNEL,
            'rate_limit_delay': cls.RATE_LIMIT_DELAY,
            'min_confidence_threshold': cls.MIN_CONFIDENCE_THRESHOLD,
            'arbitrage_min_margin': cls.ARBITRAGE_MIN_MARGIN,
            'confidence_boost_multiplier': cls.CONFIDENCE_BOOST_MULTIPLIER,
        }

