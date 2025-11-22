#!/usr/bin/env python3
"""
📊 MATCH HISTORY SCRAPER
========================

Scrapes player match history from FlashScore using Playwright.
Calculates Win Rate, Recent Form, and Total Matches.
Updates Player Cards database with match statistics.

Schedule: Daily at 09:00 EET (07:00 UTC)
"""

import os
import sys
import logging
import time
import re
from typing import Dict, List, Optional
from datetime import datetime, timedelta
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

# Sentry error tracking
try:
    from utils.sentry_config import init_sentry, capture_exception, capture_message, set_sentry_tags, add_breadcrumb
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    def capture_exception(*args, **kwargs): pass
    def capture_message(*args, **kwargs): pass
    def set_sentry_tags(*args, **kwargs): pass
    def add_breadcrumb(*args, **kwargs): pass

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
MAX_PLAYERS_PER_RUN = 20  # Limit to avoid rate limiting
RATE_LIMIT_DELAY = 3.0  # seconds between players


def scrape_player_history(page, player_name: str) -> Optional[Dict[str, any]]:
    """
    Scrape player's last 10-30 matches from FlashScore KZ mirror
    
    Args:
        page: Playwright page object
        player_name: Player name to search for
        
    Returns:
        Dictionary with wins, losses, win_rate, recent_form, total_matches
    """
    # Use KZ mirror - no rate limiting
    BASE_URL = "https://www.flashscore.kz"
    
    try:
        # Extract last name for better search results
        # "Hewitt D." -> "Hewitt"
        search_name = player_name.split()[0] if player_name.split() else player_name
        if len(player_name.split()) > 1:
            # Use last name (usually more unique)
            search_name = player_name.split()[-1].replace('.', '').strip()
        
        # Search for player
        search_url = f"{BASE_URL}/search/?q={search_name.replace(' ', '+')}"
        logger.debug(f"Searching: {search_url} (original: {player_name})")
        
        page.goto(search_url, timeout=30000, wait_until='domcontentloaded')
        time.sleep(2)  # Wait for search results
        
        # Click first player result - try multiple selectors
        try:
            # Wait for search results - try multiple selectors
            selectors = [
                '.event__participant',
                '[class*="participant"]',
                'a[href*="/player/"]',
                '.searchResult',
                'a[href*="tennis"]'
            ]
            
            found = False
            for selector in selectors:
                try:
                    page.wait_for_selector(selector, timeout=5000)
                    found = True
                    break
                except:
                    continue
            
            if not found:
                # Check if page has any tennis-related links
                page.wait_for_load_state('networkidle', timeout=5000)
                time.sleep(2)
            
            # Try to find and click player link
            player_link = None
            for selector in selectors:
                links = page.locator(selector).all()
                if len(links) > 0:
                    # Look for tennis player link
                    for link in links[:5]:  # Check first 5 results
                        try:
                            text = link.text_content(timeout=1000) or ""
                            href = link.get_attribute('href') or ""
                            if player_name.split()[-1].lower() in text.lower() or '/player/' in href or '/tennis/' in href:
                                player_link = link
                                break
                        except:
                            continue
                    if player_link:
                        break
            
            if player_link:
                player_link.click()
                time.sleep(3)  # Wait for player page to load
            else:
                logger.warning(f"⚠️ Player not found: {player_name}")
                return None
        except Exception as e:
            logger.warning(f"⚠️ Could not click player link for {player_name}: {e}")
            return None
        
        # Navigate to Results tab if available
        try:
            # Try multiple selectors for Results tab
            results_selectors = [
                'text=Results',
                'a[href*="results"]',
                'button:has-text("Results")',
                '[class*="results"]',
                '[class*="tab"][class*="results"]'
            ]
            
            for selector in results_selectors:
                try:
                    results_tab = page.locator(selector).first
                    if results_tab.count() > 0:
                        results_tab.click()
                        time.sleep(3)
                        logger.debug(f"Clicked Results tab with selector: {selector}")
                        break
                except:
                    continue
        except:
            logger.debug("Results tab not found or already on results page")
        
        # Get matches - wait for tennis matches to load
        try:
            page.wait_for_selector('.sportName.tennis, [class*="tennis"]', timeout=10000)
        except:
            logger.debug("Tennis selector not found, trying anyway")
        
        # Get match rows
        matches = page.locator('.sportName.tennis .event__match, [class*="tennis"] .event__match').all()[:10]
        
        if not matches:
            # Fallback: try without sport filter
            matches = page.locator('.event__match').all()[:10]
        
        if not matches:
            logger.warning(f"⚠️ No matches found for {player_name}")
            return None
        
        # Parse matches to determine W/L
        wins = 0
        losses = 0
        recent_form = []
        
        for match in matches:
            try:
                # Get player names
                home_elem = match.locator('.event__participant--home').first
                away_elem = match.locator('.event__participant--away').first
                
                home_text = home_elem.text_content(timeout=2000) or ""
                away_text = away_elem.text_content(timeout=2000) or ""
                
                # Check if player is in this match
                player_last_name = player_name.split()[-1].lower()
                is_home = player_last_name in home_text.lower()
                is_away = player_last_name in away_text.lower()
                
                if not (is_home or is_away):
                    continue
                
                # Check winner class - KZ mirror marks winner with class
                try:
                    home_class = home_elem.get_attribute('class') or ""
                    has_winner_class = 'event__participant--winner' in home_class
                    
                    # Determine if player won
                    if is_home:
                        won = has_winner_class
                    else:  # is_away
                        won = not has_winner_class
                except:
                    # Fallback: if no winner class, skip this match
                    logger.debug("No winner class found, skipping match")
                    continue
                
                if won:
                    wins += 1
                    recent_form.append('W')
                else:
                    losses += 1
                    recent_form.append('L')
                    
            except Exception as e:
                logger.debug(f"Error parsing match: {e}")
                continue
        
        total_matches = wins + losses
        
        if total_matches == 0:
            logger.warning(f"⚠️ No valid matches found for {player_name}")
            return None
        
        win_rate = round((wins / total_matches) * 100, 1)
        recent_form_str = ''.join(recent_form[:10])  # Last 10 matches
        
        return {
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'recent_form': recent_form_str,
            'total_matches': total_matches
        }
        
    except PlaywrightTimeout:
        logger.error(f"⏱️ Timeout scraping {player_name}")
        if SENTRY_AVAILABLE:
            capture_exception(
                PlaywrightTimeout(f"Timeout scraping {player_name}"),
                component='match_history_scraper',
                stage='scrape_player_history',
                player_name=player_name
            )
        return None
    except Exception as e:
        logger.error(f"❌ Error scraping {player_name}: {e}")
        if SENTRY_AVAILABLE:
            capture_exception(
                e,
                component='match_history_scraper',
                stage='scrape_player_history',
                player_name=player_name
            )
        import traceback
        logger.debug(traceback.format_exc())
        return None


def get_players_to_update(notion_client: Client, database_id: str, limit: int = MAX_PLAYERS_PER_RUN) -> List[Dict[str, str]]:
    """
    Get Player Cards that need match history updates
    
    Args:
        notion_client: Notion API client
        database_id: Player Cards database ID
        limit: Maximum number of players to process
        
    Returns:
        List of player dictionaries with page_id and name
    """
    if not notion_client or not database_id:
        return []
    
    try:
        # Get players where Win Rate is empty or Last Updated is older than 7 days
        from datetime import timedelta
        cutoff_date = (datetime.now() - timedelta(days=7)).isoformat()
        
        response = notion_client.databases.query(
            database_id=database_id,
            filter={
                "or": [
                    {
                        "property": "Win Rate",
                        "number": {
                            "is_empty": True
                        }
                    },
                    {
                        "property": "Last Updated",
                        "date": {
                            "before": cutoff_date
                        }
                    }
                ]
            },
            page_size=limit
        )
        
        players = []
        for page in response.get('results', []):
            props = page.get('properties', {})
            name_prop = props.get('Player Name', {})
            
            if name_prop.get('title'):
                name = name_prop['title'][0].get('plain_text', '')
                if name:
                    players.append({
                        'page_id': page['id'],
                        'name': name
                    })
        
        logger.info(f"📋 Found {len(players)} players to update")
        return players[:limit]
        
    except Exception as e:
        logger.error(f"❌ Error getting players: {e}")
        if SENTRY_AVAILABLE:
            capture_exception(
                e,
                component='match_history_scraper',
                stage='get_players_to_update',
                database_id=database_id
            )
        import traceback
        logger.debug(traceback.format_exc())
        return []


def update_player_card(notion_client: Client, page_id: str, history: Dict[str, any]):
    """
    Update Player Card with match history data
    
    Args:
        notion_client: Notion API client
        page_id: Player Card page ID
        history: Match history dictionary
    """
    try:
        properties = {
            "Win Rate": {
                "number": history['win_rate']
            },
            "Total Matches": {
                "number": history['total_matches']
            }
        }
        
        # Add Recent Form if field exists
        if history.get('recent_form'):
            properties["Recent Form"] = {
                "rich_text": [{"text": {"content": history['recent_form']}}]
            }
        
        # Update Last Updated (correct property format)
        properties["Last Updated"] = {
            "date": {"start": datetime.now().isoformat()}
        }
        
        notion_client.pages.update(
            page_id=page_id,
            properties=properties
        )
        
        logger.info(f"✅ Updated: Win Rate={history['win_rate']}%, Form={history['recent_form']}, Matches={history['total_matches']}")
        
    except Exception as e:
        logger.error(f"❌ Error updating player card: {e}")
        if SENTRY_AVAILABLE:
            capture_exception(
                e,
                component='match_history_scraper',
                stage='update_player_card',
                page_id=page_id
            )
        import traceback
        logger.debug(traceback.format_exc())


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("📊 MATCH HISTORY SCRAPER")
    print("="*80 + "\n")
    
    # Initialize Sentry
    if SENTRY_AVAILABLE:
        init_sentry(environment='production' if (project_root / '.env').exists() else 'development')
        set_sentry_tags(component='match_history_scraper')
        add_breadcrumb(
            message="Match History Scraper started",
            category="scraper",
            level="info"
        )
    
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
    
    # Get players to update
    players = get_players_to_update(notion, PLAYER_CARDS_DB_ID)
    
    if not players:
        logger.info("✅ No players need updates")
        if SENTRY_AVAILABLE:
            add_breadcrumb(
                message="No players need updates",
                category="scraper",
                level="info"
            )
        return
    
    # Scrape match history for each player
    updated_count = 0
    failed_count = 0
    
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
        
        for i, player in enumerate(players, 1):
            print(f"\n[{i}/{len(players)}] 👤 Processing: {player['name']}")
            
            if SENTRY_AVAILABLE:
                add_breadcrumb(
                    message=f"Processing player {i}/{len(players)}: {player['name']}",
                    category="scraper",
                    level="info",
                    data={"player_name": player['name'], "player_index": i}
                )
            
            history = scrape_player_history(page, player['name'])
            
            if history:
                if SENTRY_AVAILABLE:
                    add_breadcrumb(
                        message=f"Successfully scraped history for {player['name']}",
                        category="scraper",
                        level="info",
                        data={
                            "player_name": player['name'],
                            "win_rate": history.get('win_rate'),
                            "total_matches": history.get('total_matches')
                        }
                    )
                update_player_card(notion, player['page_id'], history)
                updated_count += 1
            else:
                failed_count += 1
                logger.warning(f"⚠️ Could not get history for {player['name']}")
                if SENTRY_AVAILABLE:
                    add_breadcrumb(
                        message=f"Failed to get history for {player['name']}",
                        category="scraper",
                        level="warning",
                        data={"player_name": player['name']}
                    )
            
            # Rate limiting
            if i < len(players):
                time.sleep(RATE_LIMIT_DELAY)
        
        browser.close()
    
    # Summary
    print("\n" + "="*80)
    print("✅ MATCH HISTORY UPDATE COMPLETE")
    print("="*80)
    print(f"   Updated: {updated_count}/{len(players)}")
    print(f"   Failed: {failed_count}/{len(players)}")
    print("="*80 + "\n")
    
    if SENTRY_AVAILABLE:
        add_breadcrumb(
            message="Match History Scraper completed",
            category="scraper",
            level="info",
            data={
                "updated_count": updated_count,
                "failed_count": failed_count,
                "total_players": len(players)
            }
        )
        if updated_count > 0:
            capture_message(
                f"Match History Scraper completed: {updated_count}/{len(players)} players updated",
                level="info",
                updated_count=updated_count,
                failed_count=failed_count,
                total_players=len(players)
            )


if __name__ == "__main__":
    main()

