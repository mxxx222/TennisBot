#!/usr/bin/env python3
"""
🔗 LINK EXISTING MATCHES TO PLAYER CARDS
========================================

Links existing Tennis Prematch matches to Player Cards and Scraper relations.
This script should be run once to link all existing matches, then the pipeline
will automatically link new matches.

Usage:
    python scripts/tennis_ai/link_existing_matches.py
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / 'telegram_secrets.env'
if env_path.exists():
    load_dotenv(env_path)

# Notion API
try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    print("❌ ERROR: notion-client not installed")
    exit(1)

logger = logging.getLogger(__name__)

# CONFIG
NOTION_API_KEY = os.getenv('NOTION_API_KEY') or os.getenv('NOTION_TOKEN')
TENNIS_PREMATCH_DB_ID = (
    os.getenv('NOTION_TENNIS_PREMATCH_DB_ID') or
    os.getenv('NOTION_PREMATCH_DB_ID')
)
PLAYER_CARDS_DB_ID = os.getenv('NOTION_ITF_PLAYER_CARDS_DB_ID')
SCRAPING_TARGETS_DB_ID = os.getenv('NOTION_ROI_SCRAPING_TARGETS_DB_ID')

if not NOTION_API_KEY:
    logger.error("❌ ERROR: NOTION_API_KEY not set")
    exit(1)

if not TENNIS_PREMATCH_DB_ID:
    logger.error("❌ ERROR: NOTION_TENNIS_PREMATCH_DB_ID not set")
    exit(1)

notion_client = Client(auth=NOTION_API_KEY)


def find_player_card_by_name(player_name: str) -> Optional[str]:
    """
    Find Player Card page ID by player name
    
    Args:
        player_name: Player name to search for
    
    Returns:
        Page ID if found, None otherwise
    """
    if not PLAYER_CARDS_DB_ID:
        return None
    
    try:
        # Query Player Cards database for matching name
        response = notion_client.databases.query(
            database_id=PLAYER_CARDS_DB_ID,
            filter={
                "or": [
                    {
                        "property": "Name",
                        "title": {
                            "contains": player_name
                        }
                    },
                    {
                        "property": "Player Name",
                        "rich_text": {
                            "contains": player_name
                        }
                    }
                ]
            }
        )
        
        results = response.get('results', [])
        if results:
            # Try exact match first
            for result in results:
                props = result.get('properties', {})
                # Check various name property formats
                name_props = ['Name', 'Player Name', 'Full Name']
                for prop_name in name_props:
                    prop = props.get(prop_name, {})
                    if prop.get('title'):
                        db_name = prop['title'][0]['plain_text']
                    elif prop.get('rich_text'):
                        db_name = prop['rich_text'][0]['plain_text']
                    else:
                        continue
                    
                    # Exact or last name match
                    if (player_name.lower() == db_name.lower() or
                        player_name.split()[-1].lower() == db_name.split()[-1].lower()):
                        return result['id']
            
            # Return first result if no exact match
            return results[0]['id']
        
    except Exception as e:
        logger.error(f"❌ Error finding player card for {player_name}: {e}")
    
    return None


def find_scraper_page(scraper_name: str = "FlashScore ITF Women") -> Optional[str]:
    """
    Find scraper page ID in ROI Scraping Targets database
    
    Args:
        scraper_name: Name of the scraper to find
    
    Returns:
        Page ID if found, None otherwise
    """
    if not SCRAPING_TARGETS_DB_ID:
        return None
    
    try:
        response = notion_client.databases.query(
            database_id=SCRAPING_TARGETS_DB_ID,
            filter={
                "property": "Name",
                "title": {
                    "contains": scraper_name
                }
            }
        )
        
        results = response.get('results', [])
        if results:
            return results[0]['id']
        
    except Exception as e:
        logger.error(f"❌ Error finding scraper page: {e}")
    
    return None


def link_match_relations(match_id: str, 
                         player_a_name: str,
                         player_b_name: str,
                         scraper_page_id: Optional[str] = None) -> bool:
    """
    Link match to Player Cards and Scraper
    
    Args:
        match_id: Notion match page ID
        player_a_name: Player A name
        player_b_name: Player B name
        scraper_page_id: Scraper page ID (optional)
    
    Returns:
        True if successful
    """
    try:
        properties = {}
        
        # Find and link Player A Card
        player_a_card_id = find_player_card_by_name(player_a_name)
        if player_a_card_id:
            properties['Player A Card'] = {
                'relation': [{'id': player_a_card_id}]
            }
            logger.debug(f"✅ Linked Player A Card for {player_a_name}")
        else:
            logger.warning(f"⚠️ Could not find Player A Card for {player_a_name}")
        
        # Find and link Player B Card
        player_b_card_id = find_player_card_by_name(player_b_name)
        if player_b_card_id:
            properties['Player B Card'] = {
                'relation': [{'id': player_b_card_id}]
            }
            logger.debug(f"✅ Linked Player B Card for {player_b_name}")
        else:
            logger.warning(f"⚠️ Could not find Player B Card for {player_b_name}")
        
        # Link Data Source Scraper
        if scraper_page_id:
            properties['Data Source Scraper'] = {
                'relation': [{'id': scraper_page_id}]
            }
            logger.debug(f"✅ Linked Data Source Scraper")
        
        if properties:
            notion_client.pages.update(
                page_id=match_id,
                properties=properties
            )
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Error linking relations for match {match_id}: {e}")
        return False


def main():
    """Main function to link existing matches"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger.info("🚀 Starting Match Relations Linker...")
    
    # Find scraper page
    scraper_page_id = find_scraper_page()
    if scraper_page_id:
        logger.info(f"✅ Found scraper page: {scraper_page_id[:8]}...")
    else:
        logger.warning("⚠️ Scraper page not found, will skip scraper linking")
    
    # Get all matches without relations
    try:
        response = notion_client.databases.query(
            database_id=TENNIS_PREMATCH_DB_ID,
            filter={
                "or": [
                    {
                        "property": "Player A Card",
                        "relation": {
                            "is_empty": True
                        }
                    },
                    {
                        "property": "Data Source Scraper",
                        "relation": {
                            "is_empty": True
                        }
                    }
                ]
            }
        )
        
        matches = response.get('results', [])
        logger.info(f"📊 Found {len(matches)} matches to link")
        
        if not matches:
            logger.info("ℹ️ All matches already linked")
            return
        
        linked_count = 0
        failed_count = 0
        
        for match in matches:
            try:
                props = match.get('properties', {})
                
                # Get player names
                player_a_prop = props.get('Pelaaja A nimi', {})
                player_b_prop = props.get('Pelaaja B nimi', {})
                
                if not player_a_prop.get('rich_text') or not player_b_prop.get('rich_text'):
                    logger.warning(f"⚠️ Match {match['id'][:8]}... missing player names, skipping")
                    failed_count += 1
                    continue
                
                player_a_name = player_a_prop['rich_text'][0]['plain_text']
                player_b_name = player_b_prop['rich_text'][0]['plain_text']
                
                # Link relations
                if link_match_relations(match['id'], player_a_name, player_b_name, scraper_page_id):
                    linked_count += 1
                    logger.info(f"✅ Linked match: {player_a_name} vs {player_b_name}")
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"❌ Error processing match {match.get('id', 'unknown')}: {e}")
                failed_count += 1
        
        logger.info(f"\n✅ Linking complete!")
        logger.info(f"   Linked: {linked_count}")
        logger.info(f"   Failed: {failed_count}")
        
    except Exception as e:
        logger.error(f"❌ Error querying matches: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

