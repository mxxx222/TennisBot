#!/usr/bin/env python3
"""
🧪 TEST TENNIS ABSTRACT ELO SCRAPER
===================================

Test script for ELO scraper - tests with 5 top WTA players
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / 'telegram_secrets.env'
if env_path.exists():
    load_dotenv(env_path)

from scripts.tennis_abstract_elo_scraper import TennisAbstractELOScraper, PlayerCardsELOUpdater

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Test ELO scraper with 5 top WTA players"""
    
    # Test players (top WTA players)
    test_players = [
        "Iga Swiatek",
        "Aryna Sabalenka", 
        "Coco Gauff",
        "Elena Rybakina",
        "Jessica Pegula"
    ]
    
    logger.info("🧪 Testing Tennis Abstract ELO Scraper")
    logger.info(f"📊 Testing with {len(test_players)} players")
    logger.info("")
    
    # Initialize scraper and updater
    scraper = TennisAbstractELOScraper()
    updater = PlayerCardsELOUpdater()
    
    if not updater.client or not updater.database_id:
        logger.error("❌ Notion client or database ID not configured")
        logger.error("   Set NOTION_TOKEN and PLAYER_CARDS_DB_ID environment variables")
        return
    
    logger.info(f"✅ Connected to Player Cards DB: {updater.database_id[:8]}...")
    logger.info("")
    
    # Test scraping
    results = {}
    for i, player_name in enumerate(test_players, 1):
        logger.info(f"[{i}/{len(test_players)}] Testing {player_name}...")
        
        # Scrape ELO
        elo = scraper.scrape_player_elo(player_name)
        
        if elo:
            logger.info(f"   ✅ Found ELO:")
            logger.info(f"      Overall: {elo.overall_elo}")
            logger.info(f"      Hard: {elo.hard_elo}")
            logger.info(f"      Clay: {elo.clay_elo}")
            logger.info(f"      Grass: {elo.grass_elo}")
            
            # Try to find player card
            player_card_id = updater.find_player_card(player_name)
            if player_card_id:
                logger.info(f"   ✅ Found Player Card: {player_card_id[:8]}...")
                
                # Test update (optional - comment out to avoid actual updates)
                # if updater.update_player_elo(player_name, elo):
                #     logger.info(f"   ✅ Updated Player Card")
                # else:
                #     logger.warning(f"   ⚠️ Failed to update")
            else:
                logger.warning(f"   ⚠️ Player Card not found in database")
        else:
            logger.warning(f"   ⚠️ ELO not found on Tennis Abstract")
        
        results[player_name] = elo
        logger.info("")
    
    # Summary
    found_count = sum(1 for v in results.values() if v is not None)
    logger.info("=" * 50)
    logger.info(f"✅ Test complete!")
    logger.info(f"   Players tested: {len(test_players)}")
    logger.info(f"   ELO found: {found_count}")
    logger.info(f"   Success rate: {found_count/len(test_players)*100:.1f}%")


if __name__ == "__main__":
    main()

