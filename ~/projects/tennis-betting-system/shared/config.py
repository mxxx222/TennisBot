#!/usr/bin/env python3
"""
Shared configuration for all scrapers.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Centralized configuration"""

    # Notion
    NOTION_TOKEN = os.getenv("NOTION_TOKEN")

    # Production Databases
    TENNIS_MASTER_DB_ID = os.getenv("TENNIS_MASTER_DB_ID")
    TENNIS_PLAYERS_DB_ID = os.getenv("TENNIS_PLAYERS_DB_ID")
    H2H_RECORDS_DB_ID = os.getenv("H2H_RECORDS_DB_ID")
    ODDS_TRACKING_DB_ID = os.getenv("ODDS_TRACKING_DB_ID")

    # Monitoring Databases
    SCRAPER_RUNS_DB_ID = os.getenv("SCRAPER_RUNS_DB_ID")
    SCRAPER_ERRORS_DB_ID = os.getenv("SCRAPER_ERRORS_DB_ID")
    DATA_QUALITY_DB_ID = os.getenv("DATA_QUALITY_DB_ID")

    # External APIs
    ODDS_API_KEY = os.getenv("ODDS_API_KEY")
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

    # Scraping
    FLASHSCORE_USER_AGENT = os.getenv(
        "FLASHSCORE_USER_AGENT",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    )
    SCRAPER_DELAY_SECONDS = int(os.getenv("SCRAPER_DELAY_SECONDS", "2"))

    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> bool:
        """Validate required env vars are set"""
        required = [
            "NOTION_TOKEN",
            "TENNIS_MASTER_DB_ID",
            "SCRAPER_RUNS_DB_ID",
        ]
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing required env vars: {missing}")
        return True


# Validate on import
if Config.NOTION_TOKEN:  # Only validate if token is set
    Config.validate()

