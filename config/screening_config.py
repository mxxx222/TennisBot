"""
Configuration settings for Tennis ITF Screening System
Based on proven edge analysis from single_bets.csv (+17.81% ROI)
"""

import os
from typing import Dict, List, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv('telegram_secrets.env')

class ScreeningConfig:
    """Configuration for Tennis ITF screening system"""
    
    # API Configuration
    ODDS_API_KEY = os.getenv('ODDS_API_KEY', '1108325cf70df63e93c3d2aa09813f63')
    ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4"
    
    # Tennis-specific settings
    SPORT = "tennis_itf_women"  # Focus on ITF Women (proven edge)
    REGIONS = "eu"  # European bookmakers
    MARKETS = "h2h"  # Head-to-head (winner) markets
    ODDS_FORMAT = "decimal"
    DATE_FORMAT = "iso"
    
    # Proven filtering criteria from single_bets.csv analysis
    MIN_ODDS = 1.30  # Sweet spot lower bound
    MAX_ODDS = 1.80  # Sweet spot upper bound
    MAX_DAILY_PICKS = 3  # Limit to top 3 opportunities per day
    
    # Bet sizing configuration
    DEFAULT_BANKROLL = 1000.0  # $1000 starting bankroll
    BASE_UNIT_PERCENTAGE = 0.01  # 1% of bankroll per bet
    MAX_STAKE = 15.0  # Safety cap at $15 per bet
    
    # Bet sizing by odds range (from analysis)
    STAKE_MULTIPLIERS = {
        (1.25, 1.50): 1.0,   # Full unit for low odds
        (1.51, 2.00): 0.8,   # 0.8 units for medium odds  
        (2.01, 2.50): 0.5,   # 0.5 units for higher odds
    }
    
    # Telegram configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # Notion configuration (if available)
    NOTION_API_KEY = os.getenv('NOTION_API_KEY', '')
    NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID', '')
    
    # Scheduling
    EXECUTION_TIME = "08:00"  # Daily execution at 08:00 EET
    TIMEZONE = "Europe/Helsinki"
    
    # Rate limiting
    MAX_REQUESTS_PER_DAY = 30  # Well under free tier limit of 500/month
    REQUEST_DELAY = 1.0  # 1 second between requests
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FILE = "tennis_itf_screener.log"
    
    # Error handling
    MAX_RETRIES = 3
    RETRY_DELAY = 5.0  # 5 seconds between retries
    
    @classmethod
    def get_stake_multiplier(cls, odds: float) -> float:
        """Get stake multiplier based on odds range"""
        for (min_odds, max_odds), multiplier in cls.STAKE_MULTIPLIERS.items():
            if min_odds <= odds <= max_odds:
                return multiplier
        return 0.0  # No bet if outside range
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that required configuration is present"""
        required_vars = [
            cls.ODDS_API_KEY,
            cls.TELEGRAM_BOT_TOKEN, 
            cls.TELEGRAM_CHAT_ID
        ]
        
        missing = [var for var in required_vars if not var or var == 'your_api_key_here']
        
        if missing:
            print(f"Missing required configuration: {missing}")
            return False
            
        return True

# Tournament filtering (focus on ITF/Challenger level)
ALLOWED_TOURNAMENTS = [
    "ITF",
    "Challenger", 
    "W15",
    "W25", 
    "W50",
    "W75",
    "W100",
    "M15",
    "M25"
]

# Exclude high-level tournaments (too efficient markets)
EXCLUDED_TOURNAMENTS = [
    "WTA",
    "ATP",
    "Grand Slam",
    "Masters",
    "Premier"
]
