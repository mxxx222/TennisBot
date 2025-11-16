"""
Configuration management for BetFlow Pro
"""
import os
from dotenv import load_dotenv

load_dotenv()

# NOTION
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB_MATCHES = os.getenv("NOTION_DB_MATCHES")
NOTION_DB_ANALYSIS = os.getenv("NOTION_DB_ANALYSIS")
NOTION_DB_BETS = os.getenv("NOTION_DB_BETS")
NOTION_DB_ARBITRAGE = os.getenv("NOTION_DB_ARBITRAGE")
NOTION_DB_CONTROL_PANEL = os.getenv("NOTION_DB_CONTROL_PANEL")

# BOOKMAKERS
PINNACLE_API_KEY = os.getenv("PINNACLE_API_KEY")
BET365_API_KEY = os.getenv("BET365_API_KEY")
PINNACLE_USERNAME = os.getenv("PINNACLE_USERNAME")
PINNACLE_PASSWORD = os.getenv("PINNACLE_PASSWORD")

# SETTINGS
BANKROLL = float(os.getenv("BANKROLL", "5000"))
MIN_EDGE_PERCENT = float(os.getenv("MIN_EDGE_PERCENT", "4.0"))
KELLY_SCALE = float(os.getenv("KELLY_SCALE", "0.5"))
MAX_STAKE_PERCENT = float(os.getenv("MAX_STAKE_PERCENT", "3.0"))
MAX_DRAWDOWN_TOLERANCE = float(os.getenv("MAX_DRAWDOWN_TOLERANCE", "15.0"))

# ALERTS
ALERT_EMAIL = os.getenv("ALERT_EMAIL")
ALERT_PHONE = os.getenv("ALERT_PHONE")
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")

# API SETTINGS
USE_MOCK_APIS = os.getenv("USE_MOCK_APIS", "true").lower() == "true"
API_RATE_LIMIT_DELAY = float(os.getenv("API_RATE_LIMIT_DELAY", "1.0"))

