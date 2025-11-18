#!/usr/bin/env python3
"""
🔄 ITF NOTION PIPELINE
======================

Transforms scraped FlashScore data and pushes to Tennis Prematch database.
Handles duplicate detection and batch updates (max 3 req/s per Notion API limits).

Data Flow:
FlashScore Scraper → Data Transformer → Notion API → Tennis Prematch Database
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys
from functools import lru_cache

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Use enhanced scraper (now the default)
from src.scrapers.flashscore_itf_scraper import FlashScoreITFScraperEnhanced, ITFMatch
ENHANCED_SCRAPER_AVAILABLE = True
from src.notion.itf_database_updater import ITFDatabaseUpdater

logger = logging.getLogger(__name__)


class ITFNotionPipeline:
    """Pipeline to transform and push ITF match data to Notion"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ITF Notion Pipeline
        
        Args:
            config: Configuration dict with database IDs, rate limits, etc.
        """
        self.config = config or {}
        
        # Initialize components - use enhanced scraper if available
        scraper_config = config.get('scraper', {})
        if ENHANCED_SCRAPER_AVAILABLE:
            self.scraper = FlashScoreITFScraperEnhanced(scraper_config, use_selenium=True)
        else:
            from src.scrapers.flashscore_itf_scraper import FlashScoreITFScraper
            self.scraper = FlashScoreITFScraper(scraper_config)
        
        self.notion_updater = ITFDatabaseUpdater(
            database_id=self.config.get('notion', {}).get('tennis_prematch_db_id')
        )
        
        # Duplicate tracking (with caching)
        self.processed_match_ids: set = set()
        self.duplicate_cache: Dict[str, bool] = {}  # Cache for duplicate checks
        
        # Batch update settings (optimized for concurrent processing)
        self.batch_size = 3  # Max 3 req/s per Notion API
        self.batch_delay = 1.0  # 1 second between batches (distributed across batch)
        
        logger.info("🔄 ITF Notion Pipeline initialized")
    
    def transform_match_to_notion(self, match: ITFMatch) -> Dict[str, Any]:
        """
        Transform ITFMatch to Notion page properties
        
        Maps scraper data to updated Notion database schema:
        - Pelaaja 1, Pelaaja 2 (text)
        - Scraper Source (select) - FlashScore
        - Alusta (select) - Hard, Clay, Grass, Indoor
        - Status (select) - Scheduled, Live, Finished, Postponed, Cancelled
        - Päivämäärä (date)
        
        Args:
            match: ITFMatch object from scraper
            
        Returns:
            Dictionary of Notion properties
        """
        # Map match_status to Notion Match Status values
        # Match Status field options: Upcoming, Live, Completed, Postponed, Cancelled
        status_mapping = {
            'not_started': 'Upcoming',
            'scheduled': 'Upcoming',
            'upcoming': 'Upcoming',
            'live': 'Live',
            'finished': 'Completed',
            'completed': 'Completed',
            'postponed': 'Postponed',
            'cancelled': 'Cancelled',
        }
        notion_status = status_mapping.get(match.match_status.lower(), 'Upcoming')
        
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
        if match.surface:
            surface_lower = match.surface.lower().strip()
            notion_surface = surface_mapping.get(surface_lower, match.surface.title())
            # Ensure it's one of the valid options for Kenttä field
            valid_surfaces = ['Hard', 'Clay', 'Grass', 'Carpet']
            if notion_surface not in valid_surfaces:
                notion_surface = 'Hard'  # Default to Hard
        
        # Use scheduled_time if available, otherwise use scraped_at
        date_value = match.scheduled_time if match.scheduled_time else match.scraped_at
        
        # Create match title (Name field in Notion)
        match_title = f"{match.player1} vs {match.player2}"
        
        # Build Notion properties using correct property names from database 81a70fea5de140d384c77abee225436d
        # Correct property names: Pelaaja A nimi, Pelaaja B nimi, Kenttä, Match Status
        properties = {
            "Turnaus": {
                "rich_text": [{"text": {"content": match.tournament}}]
            },
            "Pelaaja A nimi": {
                "rich_text": [{"text": {"content": match.player1}}]
            },
            "Pelaaja B nimi": {
                "rich_text": [{"text": {"content": match.player2}}]
            },
            "Päivämäärä": {
                "date": {
                    "start": date_value.isoformat()
                }
            },
            "Match Status": {
                "select": {
                    "name": notion_status
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
        if match.tournament_tier:
            properties["Tournament Tier"] = {
                "select": {
                    "name": match.tournament_tier
                }
            }
        
        # Add optional fields (keep for backward compatibility)
        if match.round:
            properties["Round"] = {
                "rich_text": [{"text": {"content": match.round}}]
            }
        
        if match.live_score:
            properties["Live Score"] = {
                "rich_text": [{"text": {"content": match.live_score}}]
            }
        
        # Add Player A Odds if available
        if hasattr(match, 'player1_odds') and match.player1_odds:
            properties["Player A Odds"] = {
                "number": match.player1_odds
            }
        
        # Add Player B Odds if available
        if hasattr(match, 'player2_odds') and match.player2_odds:
            properties["Player B Odds"] = {
                "number": match.player2_odds
            }
        
        # Note: Relations (Data Source Scraper, Player A Card, Player B Card) 
        # should be linked separately using link_existing_matches.py script
        # This is because we need to:
        # 1. Find the scraper page ID in ROI Scraping Targets DB
        # 2. Find Player A/B Card page IDs in ITF Player Cards DB by name matching
        
        return {
            'title': match_title,
            'properties': properties,
            'match_id': match.match_id,
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
    
    async def process_matches_batch(self, matches: List[ITFMatch]) -> Dict[str, Any]:
        """
        Process a batch of matches with optimized concurrent processing
        
        Args:
            matches: List of ITFMatch objects
            
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
            if await self.check_duplicate(match.match_id):
                logger.debug(f"⏭️ Skipping duplicate match: {match.match_id}")
                results['duplicates'] += 1
                continue
            valid_matches.append(match)
        
        if not valid_matches:
            return results
        
        # Process matches in concurrent batches (respecting Notion API limits)
        # Notion API allows 3 req/s, so we process up to 3 concurrently
        semaphore = asyncio.Semaphore(self.batch_size)
        
        async def process_single_match(match: ITFMatch):
            """Process a single match with semaphore limiting"""
            async with semaphore:
                try:
                    # Transform to Notion format
                    notion_data = self.transform_match_to_notion(match)
                    
                    # Create page
                    page_id = await self.create_match_page(notion_data)
                    
                    if page_id:
                        results['created'] += 1
                        results['page_ids'].append(page_id)
                    else:
                        results['errors'] += 1
                    
                    # Rate limiting: wait between batches (not individual requests)
                    await asyncio.sleep(self.batch_delay / self.batch_size)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing match {match.match_id}: {e}")
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
        logger.info("🚀 Starting ITF Notion Pipeline...")
        
        start_time = datetime.now()
        
        try:
            # Step 1: Scrape matches
            logger.info("📥 Step 1: Scraping ITF matches from FlashScore...")
            
            # Use enhanced scraper (synchronous) or async scraper
            if ENHANCED_SCRAPER_AVAILABLE:
                # Enhanced scraper is synchronous
                # Enable odds fetching if configured
                fetch_odds = self.config.get('scraper', {}).get('fetch_odds', False)
                matches_list = self.scraper.scrape(tiers=['W15', 'W35', 'W50'], fetch_odds=fetch_odds)
                
                # Convert to ITFMatch format
                matches_data = []
                for match_dict in matches_list:
                    match = ITFMatch(
                        match_id=match_dict.get('match_id', f"match_{hash(str(match_dict)) % 100000}"),
                        tournament=match_dict.get('tournament', 'Unknown'),
                        tournament_tier=match_dict.get('tier', 'W15'),
                        surface=match_dict.get('surface'),
                        player1=match_dict.get('player_a', ''),
                        player2=match_dict.get('player_b', ''),
                        round=match_dict.get('round'),
                        match_status=match_dict.get('match_status', 'not_started'),
                        live_score=match_dict.get('live_score'),
                        set1_score=None,  # Would need to parse from live_score
                        scheduled_time=None,
                        match_url=None,
                        scraped_at=datetime.fromisoformat(match_dict.get('scraped_at', datetime.now().isoformat())),
                        player1_odds=match_dict.get('player_a_odds'),
                        player2_odds=match_dict.get('player_b_odds')
                    )
                    matches_data.append(match)
                
                logger.info(f"✅ Scraped {len(matches_data)} matches")
            else:
                # Use async scraper (original)
                async with self.scraper:
                    scrape_result = await self.scraper.run_scrape()
                
                if not scrape_result.get('success'):
                    logger.error(f"❌ Scraping failed: {scrape_result.get('error')}")
                    return {
                        'success': False,
                        'error': scrape_result.get('error'),
                        'timestamp': datetime.now().isoformat(),
                    }
                
                matches_data_raw = scrape_result.get('matches', [])
                # Convert dict to ITFMatch objects
                matches_data = []
                for match_dict in matches_data_raw:
                    match = ITFMatch(
                        match_id=match_dict['match_id'],
                        tournament=match_dict['tournament'],
                        tournament_tier=match_dict['tournament_tier'],
                        surface=match_dict.get('surface'),
                        player1=match_dict['player1'],
                        player2=match_dict['player2'],
                        round=match_dict.get('round'),
                        match_status=match_dict['match_status'],
                        live_score=match_dict.get('live_score'),
                        set1_score=match_dict.get('set1_score'),
                        scheduled_time=datetime.fromisoformat(match_dict['scheduled_time']) if match_dict.get('scheduled_time') else None,
                        match_url=None,
                        scraped_at=datetime.fromisoformat(match_dict['scraped_at'])
                    )
                    matches_data.append(match)
                
                logger.info(f"✅ Scraped {len(matches_data)} matches")
            
            # Step 2: Transform and push to Notion
            if not matches_data:
                logger.info("ℹ️ No matches to process")
                return {
                    'success': True,
                    'matches_processed': 0,
                    'timestamp': datetime.now().isoformat(),
                }
            
            logger.info("📤 Step 2: Pushing matches to Notion...")
            
            # matches_data is already ITFMatch objects if using enhanced scraper
            matches = matches_data
            
            # Process in batches
            batch_results = await self.process_matches_batch(matches)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = {
                'success': True,
                'timestamp': end_time.isoformat(),
                'duration_seconds': duration,
                'matches_scraped': len(matches_data),
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
    """Test ITF Notion Pipeline"""
    print("🔄 ITF NOTION PIPELINE TEST")
    print("=" * 50)
    
    config = {
        'scraper': {
            'target_tournaments': ['W15', 'W35', 'W50'],
            'rate_limit': 2.5,
        },
        'notion': {
            'tennis_prematch_db_id': None,  # Will try to load from env/config
        }
    }
    
    pipeline = ITFNotionPipeline(config)
    
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

