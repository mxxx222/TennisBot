#!/usr/bin/env python3
"""
🔄 BETEXPLORER NOTION PIPELINE
==============================

Transforms scraped BetExplorer data and pushes to Tennis Prematch database.
Handles duplicate detection and batch updates (max 3 req/s per Notion API limits).

Data Flow:
BetExplorer Scraper → Data Transformer → Notion API → Tennis Prematch Database
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scrapers.betexplorer_scraper import BetExplorerScraper
from src.notion.itf_database_updater import ITFDatabaseUpdater
from src.notion.raw_match_feed_updater import RawMatchFeedUpdater

logger = logging.getLogger(__name__)


class BetExplorerNotionPipeline:
    """Pipeline to transform and push BetExplorer match data to Notion"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize BetExplorer Notion Pipeline
        
        Args:
            config: Configuration dict with database IDs, rate limits, etc.
        """
        self.config = config or {}
        
        # Initialize components
        scraper_config = self.config.get('scraper', {})
        self.scraper = BetExplorerScraper(scraper_config, use_selenium=True)
        
        # Raw Match Feed updater (primary target)
        self.raw_feed_updater = RawMatchFeedUpdater(
            database_id=self.config.get('notion', {}).get('raw_match_feed_db_id')
        )
        
        # Tennis Prematch updater (for parallel write mode during migration)
        self.notion_updater = ITFDatabaseUpdater(
            database_id=self.config.get('notion', {}).get('tennis_prematch_db_id')
        )
        
        # Migration mode: parallel_write writes to both DBs (Phase 1)
        self.parallel_write = self.config.get('notion', {}).get('parallel_write', False)
        
        # Duplicate tracking (with caching)
        self.processed_match_ids: set = set()
        self.duplicate_cache: Dict[str, bool] = {}  # Cache for duplicate checks
        
        # Batch update settings (optimized for concurrent processing)
        self.batch_size = self.config.get('notion', {}).get('batch_size', 3)  # Max 3 req/s per Notion API
        self.batch_delay = self.config.get('notion', {}).get('batch_delay', 1.0)  # 1 second between batches
        
        logger.info(f"🔄 BetExplorer Notion Pipeline initialized (parallel_write: {self.parallel_write})")
    
    def transform_match_to_notion(self, match: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform BetExplorer match dictionary to Notion page properties
        
        Maps scraper data to Notion database schema:
        - Tournament → Turnaus (rich_text)
        - Player 1/2 → Pelaaja A nimi / Pelaaja B nimi (rich_text)
        - Best Odds P1/P2 → Best Odds P1 / Best Odds P2 (number)
        - Bookmaker P1/P2 → Bookmaker P1 / Bookmaker P2 (select)
        - Surface → Kenttä (select)
        - Tier → Tournament Tier (select)
        - Data Source → Data Source (select: "BetExplorer")
        
        Args:
            match: Match dictionary from BetExplorer scraper
            
        Returns:
            Dictionary with title, properties, and match_id
        """
        # Normalize surface to match Notion Kenttä options (Hard, Clay, Grass, Carpet)
        surface_mapping = {
            'hard': 'Hard',
            'clay': 'Clay',
            'grass': 'Grass',
            'carpet': 'Carpet',
            'indoor': 'Hard',  # Indoor usually means indoor hard
            'indoor hard': 'Hard',
            'outdoor hard': 'Hard',
        }
        notion_surface = None
        if match.get('surface'):
            surface_lower = match.get('surface', '').lower().strip()
            notion_surface = surface_mapping.get(surface_lower, match.get('surface', 'Hard').title())
            # Ensure it's one of the valid options for Kenttä field
            valid_surfaces = ['Hard', 'Clay', 'Grass', 'Carpet']
            if notion_surface not in valid_surfaces:
                notion_surface = 'Hard'  # Default to Hard
        
        # Use match_time if available, otherwise use scraped_at or now
        date_value = match.get('match_time')
        if date_value:
            # Try to parse date if it's a string
            if isinstance(date_value, str):
                try:
                    # Try to parse common date formats
                    date_value = datetime.fromisoformat(date_value)
                except:
                    # If parsing fails, use current time
                    date_value = datetime.now()
            elif not isinstance(date_value, datetime):
                date_value = datetime.now()
        else:
            date_value = datetime.now()
        
        # Create match title (Name field in Notion)
        match_title = f"{match.get('player1', 'Unknown')} vs {match.get('player2', 'Unknown')}"
        
        # Build Notion properties
        properties = {
            "Turnaus": {
                "rich_text": [{"text": {"content": match.get('tournament', 'Unknown Tournament')}}]
            },
            "Pelaaja A nimi": {
                "rich_text": [{"text": {"content": match.get('player1', '')}}]
            },
            "Pelaaja B nimi": {
                "rich_text": [{"text": {"content": match.get('player2', '')}}]
            },
            "Päivämäärä": {
                "date": {
                    "start": date_value.isoformat()
                }
            },
            "Match Status": {
                "select": {
                    "name": "Upcoming"  # BetExplorer matches are typically upcoming
                }
            },
        }
        
        # Add Kenttä (Surface) if available
        if notion_surface:
            properties["Kenttä"] = {
                "select": {
                    "name": notion_surface
                }
            }
        
        # Add Tournament Tier if available
        if match.get('tier'):
            properties["Tournament Tier"] = {
                "select": {
                    "name": match.get('tier')
                }
            }
        
        # Add Best Odds P1 if available
        if match.get('best_odds_p1'):
            properties["Best Odds P1"] = {
                "number": match.get('best_odds_p1')
            }
        
        # Add Bookmaker P1 if available
        if match.get('bookmaker_p1'):
            properties["Bookmaker P1"] = {
                "select": {
                    "name": match.get('bookmaker_p1')
                }
            }
        
        # Add Best Odds P2 if available
        if match.get('best_odds_p2'):
            properties["Best Odds P2"] = {
                "number": match.get('best_odds_p2')
            }
        
        # Add Bookmaker P2 if available
        if match.get('bookmaker_p2'):
            properties["Bookmaker P2"] = {
                "select": {
                    "name": match.get('bookmaker_p2')
                }
            }
        
        # Add Data Source
        properties["Data Source"] = {
            "select": {
                "name": match.get('data_source', 'BetExplorer')
            }
        }
        
        # Add optional fields
        if match.get('location'):
            properties["Location"] = {
                "rich_text": [{"text": {"content": match.get('location')}}]
            }
        
        return {
            'title': match_title,
            'properties': properties,
            'match_id': match.get('match_id', f"betexplorer_{hash(str(match)) % 100000}"),
        }
    
    async def check_duplicate(self, match_id: str) -> bool:
        """
        Check if match already exists in Notion database (with caching)
        
        Args:
            match_id: Match identifier
            
        Returns:
            True if duplicate exists
        """
        # Check local cache first (fastest)
        if match_id in self.processed_match_ids:
            return True
        
        # Check duplicate cache (for batch operations)
        if match_id in self.duplicate_cache:
            return self.duplicate_cache[match_id]
        
        # TODO: Query Notion database to check for existing match
        # For now, use local cache only
        is_duplicate = False
        self.duplicate_cache[match_id] = is_duplicate
        return is_duplicate
    
    async def create_match_page(self, notion_data: Dict[str, Any]) -> Optional[str]:
        """
        Create new match page in Notion database
        
        Args:
            notion_data: Transformed match data for Notion
            
        Returns:
            Notion page ID if successful, None otherwise
        """
        if not self.notion_updater.client or not self.notion_updater.database_id:
            logger.warning("⚠️ Notion client or database ID not available")
            return None
        
        try:
            # Create page
            page = self.notion_updater.client.pages.create(
                parent={"database_id": self.notion_updater.database_id},
                properties=notion_data['properties']
            )
            
            page_id = page['id']
            logger.info(f"✅ Created match page: {notion_data['title']} ({page_id[:8]}...)")
            
            # Add to processed cache
            self.processed_match_ids.add(notion_data['match_id'])
            
            return page_id
            
        except Exception as e:
            logger.error(f"❌ Error creating match page: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def process_matches_batch(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a batch of matches with optimized concurrent processing
        
        Args:
            matches: List of match dictionaries from scraper
            
        Returns:
            Dictionary with processing results
        """
        results = {
            'created': 0,
            'duplicates': 0,
            'errors': 0,
            'page_ids': []
        }
        
        # Filter duplicates first (batch duplicate check)
        valid_matches = []
        for match in matches:
            match_id = match.get('match_id', f"betexplorer_{hash(str(match)) % 100000}")
            if await self.check_duplicate(match_id):
                logger.debug(f"⏭️ Skipping duplicate match: {match_id}")
                results['duplicates'] += 1
                continue
            valid_matches.append(match)
        
        if not valid_matches:
            return results
        
        # Process matches in concurrent batches (respecting Notion API limits)
        # Notion API allows 3 req/s, so we process up to 3 concurrently
        semaphore = asyncio.Semaphore(self.batch_size)
        
        async def process_single_match(match: Dict[str, Any]):
            """Process a single match with semaphore limiting"""
            async with semaphore:
                try:
                    # Write to Raw Match Feed (primary target)
                    raw_feed_page_id = None
                    if self.raw_feed_updater.client and self.raw_feed_updater.database_id:
                        raw_feed_page_id = self.raw_feed_updater.create_match(match, match_type="betexplorer")
                        if raw_feed_page_id:
                            results['created'] += 1
                            results['page_ids'].append(raw_feed_page_id)
                    
                    # Parallel write mode: also write to Tennis Prematch DB (migration Phase 1)
                    if self.parallel_write:
                        notion_data = self.transform_match_to_notion(match)
                        prematch_page_id = await self.create_match_page(notion_data)
                        if prematch_page_id and not raw_feed_page_id:
                            # Only count if Raw Feed write failed
                            results['created'] += 1
                    
                    if not raw_feed_page_id and not self.parallel_write:
                        results['errors'] += 1
                    
                    # Rate limiting: wait between batches (not individual requests)
                    await asyncio.sleep(self.batch_delay / self.batch_size)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing match {match.get('match_id')}: {e}")
                    results['errors'] += 1
        
        # Process all matches concurrently (with semaphore limiting)
        tasks = [process_single_match(match) for match in valid_matches]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return results
    
    async def run_pipeline(self) -> Dict[str, Any]:
        """
        Run complete pipeline: scrape → transform → push to Notion
        
        Returns:
            Dictionary with pipeline results
        """
        logger.info("🚀 Starting BetExplorer Notion Pipeline...")
        
        start_time = datetime.now()
        
        try:
            # Step 1: Scrape matches
            logger.info("📥 Step 1: Scraping ITF matches from BetExplorer...")
            
            # Get target tiers from config (now writes ALL tiers, no filtering)
            # For migration: remove tier filtering to write all matches to Raw Feed
            target_tiers = self.config.get('scraper', {}).get('target_tiers', ['W15', 'W25', 'W35', 'W50'])
            
            # Scrape matches (synchronous operation) - now includes all tiers
            matches_list = self.scraper.scrape(tiers=target_tiers)
            
            logger.info(f"✅ Scraped {len(matches_list)} matches")
            
            # Step 2: Transform and push to Notion
            if not matches_list:
                logger.info("ℹ️ No matches to process")
                return {
                    'success': True,
                    'matches_processed': 0,
                    'timestamp': datetime.now().isoformat(),
                }
            
            logger.info("📤 Step 2: Pushing matches to Notion...")
            
            # Process in batches
            batch_results = await self.process_matches_batch(matches_list)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = {
                'success': True,
                'timestamp': end_time.isoformat(),
                'duration_seconds': duration,
                'matches_scraped': len(matches_list),
                'matches_created': batch_results['created'],
                'matches_duplicates': batch_results['duplicates'],
                'matches_errors': batch_results['errors'],
                'page_ids': batch_results['page_ids'],
            }
            
            logger.info(f"✅ Pipeline completed: {batch_results['created']} created, {batch_results['duplicates']} duplicates, {batch_results['errors']} errors")
            return result
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
            }


async def main():
    """Test BetExplorer Notion Pipeline"""
    print("🔄 BETEXPLORER NOTION PIPELINE TEST")
    print("=" * 50)
    
    config = {
        'scraper': {
            'target_tiers': ['W15', 'W25'],
            'request_delay': 2.0,
            'max_retries': 3,
            'timeout': 30,
        },
        'notion': {
            'tennis_prematch_db_id': None,  # Will try to load from env/config
            'batch_size': 3,
            'batch_delay': 1.0,
        }
    }
    
    pipeline = BetExplorerNotionPipeline(config)
    
    result = await pipeline.run_pipeline()
    
    if result['success']:
        print(f"\n✅ Pipeline successful!")
        print(f"   Matches scraped: {result['matches_scraped']}")
        print(f"   Matches created: {result['matches_created']}")
        print(f"   Duplicates: {result['matches_duplicates']}")
        print(f"   Errors: {result['matches_errors']}")
        print(f"   Duration: {result['duration_seconds']:.1f}s")
    else:
        print(f"\n❌ Pipeline failed: {result.get('error')}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())

