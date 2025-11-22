#!/usr/bin/env python3
"""
🏆 ITF RANKINGS SCRAPER
=======================

Scrapes ITF women's rankings from itftennis.com using Playwright.
Updates Player Cards database with ITF Rank.

Schedule: Daily at 08:00 EET (06:00 UTC)
"""

import os
import sys
import logging
import re
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path)
fallback_env = project_root / 'telegram_secrets.env'
if fallback_env.exists():
    load_dotenv(fallback_env, override=True)

# Notion API
try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    print("❌ ERROR: notion-client not installed")
    print("   Install: pip install notion-client")

# Playwright
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("❌ ERROR: playwright not installed")
    print("   Install: pip install playwright && playwright install chromium")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
NOTION_TOKEN = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
PLAYER_CARDS_DB_ID = os.getenv("PLAYER_CARDS_DB_ID", "d0a33cbc-31dd-43be-8c76-804f72c08e91")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
MAX_RANKINGS = 200  # Top 200 players


def scrape_itf_rankings() -> List[Dict[str, any]]:
    """
    Scrape ITF women's rankings from itftennis.com
    
    Returns:
        List of dictionaries with 'rank' and 'name'
    """
    if not PLAYWRIGHT_AVAILABLE:
        logger.error("❌ Playwright not available")
        return []
    
    rankings = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=HEADLESS,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                ],
                timeout=30000
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            context.set_default_timeout(30000)
            
            page = context.new_page()
            
            url = "https://www.itftennis.com/en/rankings/singles-women/"
            logger.info(f"🔍 Loading: {url}")
            
            try:
                page.goto(url, timeout=30000, wait_until='domcontentloaded')
                
                # Wait for rankings table to load
                # Try multiple selector strategies
                selectors = [
                    '.rankings-table',
                    'table',
                    '[class*="ranking"]',
                    '[class*="table"]'
                ]
                
                found = False
                for selector in selectors:
                    try:
                        page.wait_for_selector(selector, timeout=10000)
                        logger.info(f"✅ Found rankings with selector: {selector}")
                        found = True
                        break
                    except PlaywrightTimeout:
                        continue
                
                if not found:
                    logger.warning("⚠️ Rankings table not found, trying to parse anyway")
                
                # Get page HTML and parse with BeautifulSoup
                html = page.content()
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find ranking rows - try multiple patterns
                rows = soup.find_all('tr')
                
                for row in rows[:MAX_RANKINGS + 50]:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        # Try to extract rank and name
                        text = row.get_text(strip=True)
                        
                        # Pattern: number followed by name
                        match = re.search(r'^(\d+)\s+(.+?)(?:\s+\d+|\s*$)', text)
                        if match:
                            rank = int(match.group(1))
                            name = match.group(2).strip()
                            
                            # Clean name (remove extra whitespace, country codes, etc.)
                            name = re.sub(r'\s+', ' ', name)
                            name = re.sub(r'\s*\([^)]+\)\s*', '', name)  # Remove parentheses
                            
                            if name and 1 <= rank <= MAX_RANKINGS:
                                rankings.append({
                                    'rank': rank,
                                    'name': name
                                })
                
                # If BeautifulSoup parsing didn't work, try Playwright locators
                if len(rankings) < 10:
                    logger.info("Trying Playwright locators...")
                    try:
                        # Look for any elements that might contain rankings
                        rank_elements = page.locator('[class*="rank"], [class*="position"], td:first-child').all()
                        name_elements = page.locator('[class*="name"], [class*="player"], td:nth-child(2)').all()
                        
                        for i in range(min(len(rank_elements), len(name_elements), MAX_RANKINGS)):
                            try:
                                rank_text = rank_elements[i].text_content(timeout=2000)
                                name_text = name_elements[i].text_content(timeout=2000)
                                
                                rank_match = re.search(r'(\d+)', rank_text or '')
                                if rank_match and name_text:
                                    rank = int(rank_match.group(1))
                                    name = name_text.strip()
                                    if name and 1 <= rank <= MAX_RANKINGS:
                                        rankings.append({'rank': rank, 'name': name})
                            except:
                                continue
                    except Exception as e:
                        logger.debug(f"Playwright locator fallback failed: {e}")
                
                browser.close()
                
                # Remove duplicates and sort by rank
                seen = set()
                unique_rankings = []
                for r in rankings:
                    key = (r['rank'], r['name'].lower())
                    if key not in seen:
                        seen.add(key)
                        unique_rankings.append(r)
                
                unique_rankings.sort(key=lambda x: x['rank'])
                unique_rankings = unique_rankings[:MAX_RANKINGS]
                
                logger.info(f"✅ Scraped {len(unique_rankings)} ITF rankings")
                return unique_rankings
                
            except PlaywrightTimeout:
                logger.error("⏱️ Timeout loading ITF rankings page")
                browser.close()
                return []
            except Exception as e:
                logger.error(f"❌ Error scraping rankings: {e}")
                browser.close()
                return []
                
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return []


def update_player_cards(rankings: List[Dict[str, any]], notion_client: Client, database_id: str):
    """
    Update Player Cards with ITF Rank
    
    Args:
        rankings: List of ranking dictionaries
        notion_client: Notion API client
        database_id: Player Cards database ID
    """
    if not notion_client or not database_id:
        logger.error("❌ Notion client or database ID not available")
        return
    
    updated_count = 0
    not_found_count = 0
    
    for ranking_data in rankings:
        player_name = ranking_data['name']
        itf_rank = ranking_data['rank']
        
        try:
            # Search for player by name (try exact match first, then last name)
            response = notion_client.databases.query(
                database_id=database_id,
                filter={
                    "property": "Player Name",
                    "title": {
                        "contains": player_name.split()[-1]  # Search by last name
                    }
                }
            )
            
            results = response.get('results', [])
            if not results:
                not_found_count += 1
                continue
            
            # Find exact match
            page_id = None
            for result in results:
                props = result.get('properties', {})
                name_prop = props.get('Player Name', {})
                if name_prop.get('title'):
                    db_name = name_prop['title'][0]['plain_text']
                    # Exact match or last name match
                    if (player_name.lower() == db_name.lower() or 
                        player_name.split()[-1].lower() == db_name.split()[-1].lower()):
                        page_id = result['id']
                        break
            
            if not page_id and results:
                # Use first result if no exact match
                page_id = results[0]['id']
            
            if page_id:
                # Update ITF Rank
                notion_client.pages.update(
                    page_id=page_id,
                    properties={
                        "ITF Rank": {
                            "number": itf_rank
                        }
                    }
                )
                updated_count += 1
                logger.debug(f"✅ Updated: {player_name} → Rank {itf_rank}")
            else:
                not_found_count += 1
                
        except Exception as e:
            logger.error(f"❌ Error updating {player_name}: {e}")
            continue
    
    logger.info(f"📊 Update summary: {updated_count} updated, {not_found_count} not found")


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("🏆 ITF RANKINGS SCRAPER")
    print("="*80 + "\n")
    
    if not PLAYWRIGHT_AVAILABLE:
        logger.error("❌ Playwright not available")
        logger.info("💡 Install: pip install playwright && playwright install chromium")
        return
    
    if not NOTION_AVAILABLE:
        logger.error("❌ Notion client not available")
        logger.info("💡 Install: pip install notion-client")
        return
    
    if not NOTION_TOKEN:
        logger.error("❌ NOTION_API_KEY not set")
        logger.info("💡 Add to .env: NOTION_API_KEY=your_token")
        return
    
    if not PLAYER_CARDS_DB_ID:
        logger.error("❌ PLAYER_CARDS_DB_ID not set")
        logger.info("💡 Add to .env: PLAYER_CARDS_DB_ID=your_db_id")
        return
    
    # Initialize Notion client
    try:
        notion = Client(auth=NOTION_TOKEN)
        logger.info("✅ Notion client initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Notion client: {e}")
        return
    
    # Scrape rankings
    logger.info("🔍 Scraping ITF rankings...")
    rankings = scrape_itf_rankings()
    
    if not rankings:
        logger.warning("⚠️ No rankings found")
        return
    
    # Update Player Cards
    logger.info(f"📊 Updating {len(rankings)} Player Cards...")
    update_player_cards(rankings, notion, PLAYER_CARDS_DB_ID)
    
    print("\n" + "="*80)
    print("✅ ITF RANKINGS UPDATE COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

