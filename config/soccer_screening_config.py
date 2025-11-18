"""
Soccer Screening Configuration - Adapted from Tennis ITF System
Focuses on lower-tier soccer leagues with similar inefficiencies to ITF tennis
"""

import os
from typing import Dict, List, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv('telegram_secrets.env')

class SoccerScreeningConfig:
    """Configuration for Soccer screening system - adapted from Tennis ITF"""
    
    # API Configuration
    ODDS_API_KEY = os.getenv('ODDS_API_KEY', '225ec0328df7dd366c0eb42b25f99a13')
    ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4"
    
    # Soccer-specific settings (similar to ITF tennis approach)
    TARGET_LEAGUES = [
        "soccer_efl_champ",           # Championship (English 2nd tier)
        "soccer_england_league1",     # League 1 (English 3rd tier)  
        "soccer_england_league2",     # League 2 (English 4th tier)
        "soccer_germany_bundesliga2", # Bundesliga 2 (German 2nd tier)
        "soccer_spain_segunda_division", # La Liga 2 (Spanish 2nd tier)
        "soccer_italy_serie_b",       # Serie B (Italian 2nd tier)
        "soccer_france_ligue_two",    # Ligue 2 (French 2nd tier)
    ]
    
    REGIONS = "eu"  # European bookmakers
    MARKETS = "h2h"  # Head-to-head (winner) markets
    ODDS_FORMAT = "decimal"
    DATE_FORMAT = "iso"
    
    # Same proven filtering criteria from tennis analysis
    MIN_ODDS = 1.30  # Sweet spot lower bound (same as tennis)
    MAX_ODDS = 1.80  # Sweet spot upper bound (same as tennis)
    MAX_DAILY_PICKS = 5  # Slightly higher for soccer (more matches)
    
    # Same bet sizing configuration
    DEFAULT_BANKROLL = 1000.0  # $1000 starting bankroll
    BASE_UNIT_PERCENTAGE = 0.01  # 1% of bankroll per bet
    MAX_STAKE = 15.0  # Safety cap at $15 per bet
    
    # Same bet sizing by odds range (proven from tennis analysis)
    STAKE_MULTIPLIERS = {
        (1.25, 1.50): 1.0,   # Full unit for low odds
        (1.51, 2.00): 0.8,   # 0.8 units for medium odds  
        (2.01, 2.50): 0.5,   # 0.5 units for higher odds
    }
    
    # Telegram configuration (same as tennis)
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # Notion configuration (same as tennis)
    NOTION_API_KEY = os.getenv('NOTION_API_KEY', '')
    NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID', '')
    
    # Scheduling (same as tennis)
    EXECUTION_TIME = "08:00"  # Daily execution at 08:00 EET
    TIMEZONE = "Europe/Helsinki"
    
    # Rate limiting (paid API has higher limits)
    MAX_REQUESTS_PER_DAY = 100  # Higher for paid tier
    REQUEST_DELAY = 0.5  # Faster requests for paid tier
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FILE = "soccer_screener.log"
    
    # Error handling
    MAX_RETRIES = 3
    RETRY_DELAY = 5.0
    
    @classmethod
    def get_stake_multiplier(cls, odds: float) -> float:
        """Get stake multiplier based on odds range (same as tennis)"""
        for (min_odds, max_odds), multiplier in cls.STAKE_MULTIPLIERS.items():
            if min_odds <= odds <= max_odds:
                return multiplier
        return 0.0
    
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

# League quality tiers (similar to tennis tournament levels)
TIER_1_LEAGUES = [
    "soccer_efl_champ",           # Championship - best lower tier
    "soccer_germany_bundesliga2", # Bundesliga 2 - high quality
]

TIER_2_LEAGUES = [
    "soccer_england_league1",     # League 1 - good opportunities
    "soccer_spain_segunda_division", # La Liga 2 - decent level
    "soccer_italy_serie_b",       # Serie B - reasonable quality
]

TIER_3_LEAGUES = [
    "soccer_england_league2",     # League 2 - more inefficient
    "soccer_france_ligue_two",    # Ligue 2 - good value
]

# Exclude high-level leagues (too efficient, like WTA/ATP in tennis)
EXCLUDED_LEAGUES = [
    "soccer_epl",                 # Premier League
    "soccer_germany_bundesliga",  # Bundesliga  
    "soccer_spain_la_liga",       # La Liga
    "soccer_italy_serie_a",       # Serie A
    "soccer_france_ligue_one",    # Ligue 1
    "soccer_uefa_champs_league",  # Champions League
]
