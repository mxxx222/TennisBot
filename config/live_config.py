"""
Live Odds Monitoring Configuration
Professional-grade real-time monitoring for 50% equity optimization
"""

import os
from typing import Dict, List, Set
from dotenv import load_dotenv

# Load environment variables
load_dotenv('telegram_secrets.env')

class LiveMonitoringConfig:
    """Configuration for live odds monitoring system"""
    
    # API Configuration
    ODDS_API_KEY = os.getenv('ODDS_API_KEY', '225ec0328df7dd366c0eb42b25f99a13')
    ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4"
    
    # Live monitoring settings
    REFRESH_INTERVAL = 30  # seconds between updates
    WEBSOCKET_TIMEOUT = 60  # seconds before reconnection
    MAX_CONCURRENT_REQUESTS = 10  # parallel league monitoring
    
    # Target leagues for live monitoring (same as soccer screener)
    TARGET_LEAGUES = [
        "soccer_efl_champ",           # Championship (English 2nd tier)
        "soccer_england_league1",     # League 1 (English 3rd tier)  
        "soccer_england_league2",     # League 2 (English 4th tier)
        "soccer_germany_bundesliga2", # Bundesliga 2 (German 2nd tier)
        "soccer_spain_segunda_division", # La Liga 2 (Spanish 2nd tier)
        "soccer_italy_serie_b",       # Serie B (Italian 2nd tier)
        "soccer_france_ligue_two",    # Ligue 2 (French 2nd tier)
    ]
    
    # Proven value range (same as tennis analysis)
    MIN_ODDS = 1.30  # Sweet spot lower bound
    MAX_ODDS = 1.80  # Sweet spot upper bound
    
    # Movement detection thresholds
    MIN_ODDS_CHANGE = 0.05  # Minimum change to trigger alert
    SIGNIFICANT_CHANGE = 0.10  # Large movement threshold
    CRITICAL_CHANGE = 0.15  # Critical movement threshold
    
    # Value window detection
    VALUE_ENTRY_THRESHOLD = 0.02  # How close to range boundary to alert
    VALUE_EXIT_THRESHOLD = 0.03   # How far from range to stop monitoring
    
    # Alert frequency limits
    MAX_ALERTS_PER_MATCH = 3  # Prevent spam for same match
    ALERT_COOLDOWN = 300  # 5 minutes between same match alerts
    MAX_DAILY_ALERTS = 50  # Daily alert limit
    
    # Performance optimization
    BATCH_SIZE = 5  # Matches to process in parallel
    CACHE_DURATION = 10  # seconds to cache odds data
    CLEANUP_INTERVAL = 3600  # 1 hour cleanup cycle
    
    # Database settings
    DATABASE_PATH = "live_odds.db"
    MAX_HISTORY_DAYS = 30  # Keep 30 days of historical data
    BACKUP_INTERVAL = 86400  # 24 hours between backups
    
    # Telegram configuration (enhanced for live alerts)
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # Enhanced alert settings
    PRIORITY_LEAGUES = [
        "soccer_efl_champ",           # Highest priority
        "soccer_germany_bundesliga2", # High quality
    ]
    
    URGENCY_LEVELS = {
        'LOW': '🟢',      # Normal value opportunity
        'MEDIUM': '🟡',   # Good value, act soon
        'HIGH': '🟠',     # Excellent value, act now
        'CRITICAL': '🔴'  # Exceptional value, act immediately
    }
    
    # League quality tiers (affects alert priority)
    LEAGUE_TIERS = {
        # Tier 1: Highest quality, most reliable
        "soccer_efl_champ": 1,
        "soccer_germany_bundesliga2": 1,
        
        # Tier 2: Good quality, reliable
        "soccer_england_league1": 2,
        "soccer_spain_segunda_division": 2,
        "soccer_italy_serie_b": 2,
        
        # Tier 3: Lower quality, more volatile
        "soccer_england_league2": 3,
        "soccer_france_ligue_two": 3,
    }
    
    # Time-based monitoring (when to be most active)
    PEAK_HOURS = [
        (14, 17),  # 14:00-17:00 (afternoon matches)
        (19, 22),  # 19:00-22:00 (evening matches)
    ]
    
    # Weekend vs weekday different monitoring intensity
    WEEKEND_MULTIPLIER = 1.5  # More active on weekends
    
    # Logging configuration
    LOG_LEVEL = "INFO"
    LOG_FILE = "live_monitor.log"
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Error handling and reliability
    MAX_RETRIES = 3
    RETRY_DELAY = 5.0  # seconds
    CIRCUIT_BREAKER_THRESHOLD = 10  # failures before circuit break
    CIRCUIT_BREAKER_TIMEOUT = 300  # 5 minutes circuit break
    
    # Performance monitoring
    PERFORMANCE_LOG_INTERVAL = 300  # 5 minutes
    LATENCY_THRESHOLD = 5.0  # seconds - alert if slower
    MEMORY_THRESHOLD = 500  # MB - alert if higher
    
    @classmethod
    def get_league_tier(cls, league: str) -> int:
        """Get league tier (1=highest quality, 3=lowest)"""
        return cls.LEAGUE_TIERS.get(league, 2)
    
    @classmethod
    def get_urgency_emoji(cls, urgency: str) -> str:
        """Get emoji for urgency level"""
        return cls.URGENCY_LEVELS.get(urgency.upper(), '⚪')
    
    @classmethod
    def is_peak_hour(cls, hour: int) -> bool:
        """Check if current hour is peak monitoring time"""
        return any(start <= hour <= end for start, end in cls.PEAK_HOURS)
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that required configuration is present"""
        required_vars = [
            cls.ODDS_API_KEY,
            cls.TELEGRAM_BOT_TOKEN,
            cls.TELEGRAM_CHAT_ID
        ]
        
        missing = [var for var in required_vars if not var]
        
        if missing:
            print(f"Missing required configuration: {missing}")
            return False
            
        return True

# Movement patterns for enhanced detection
MOVEMENT_PATTERNS = {
    'ENTERING_RANGE': 'odds_moved_into_profitable_range',
    'EXITING_RANGE': 'odds_moved_out_of_range', 
    'SIGNIFICANT_DROP': 'large_odds_decrease',
    'SIGNIFICANT_RISE': 'large_odds_increase',
    'VOLATILITY': 'high_odds_volatility',
    'STABILIZING': 'odds_stabilizing_in_range'
}

# Bookmaker reliability scores (for future multi-bookmaker integration)
BOOKMAKER_RELIABILITY = {
    'bet365': 0.95,
    'pinnacle': 0.98,
    'betfair': 0.90,
    'william_hill': 0.85,
    'ladbrokes': 0.80,
    'default': 0.75
}

# Alert message templates
ALERT_TEMPLATES = {
    'VALUE_ENTRY': """🚨 LIVE VALUE ALERT

{emoji} **{home_team} vs {away_team}**

📊 **Odds Movement**: {old_odds} → {new_odds} {direction}
💰 **Stake**: ${stake}
🎯 **Confidence**: {confidence}
📈 **Edge**: +{edge}%

⏰ **Match Time**: {match_time}
🏆 **League**: {league}
⚡ **Urgency**: {urgency}

_Value window detected - Act fast!_""",

    'SIGNIFICANT_MOVEMENT': """📈 ODDS MOVEMENT ALERT

{emoji} **{home_team} vs {away_team}**

📊 **Movement**: {old_odds} → {new_odds} ({change:+.2f})
🎯 **Status**: {status}

⏰ **Time**: {match_time}
🏆 **League**: {league}

_Monitoring for value entry..._""",

    'DAILY_SUMMARY': """📊 **Live Monitoring Summary**

✅ **Alerts Sent**: {total_alerts}
🎯 **Value Opportunities**: {value_opportunities}
📈 **Average Edge**: +{avg_edge}%
⚡ **Response Time**: {avg_response_time}s

🏆 **Top Leagues**:
{league_breakdown}

_Live monitoring active 24/7_"""
}
