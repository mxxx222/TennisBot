#!/usr/bin/env python3
"""
Sportbex Daily Candidates Pipeline
===================================

Main orchestrator for daily candidate screening:
1. Fetch matches from Sportbex API
2. Apply filters (odds 1.40-1.80, tournaments, ranking delta)
3. Select 5-20 candidates
4. Log to Notion master database with Status="Review"

No Telegram alerts - candidates go to Notion for manual review.
"""

import asyncio
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scrapers.sportbex_client import SportbexClient
from src.pipelines.sportbex_filter import SportbexFilter, TennisCandidate
from src.notion.sportbex_notion_logger import SportbexNotionLogger

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SportbexDailyCandidatesPipeline:
    """Main pipeline for daily candidate screening"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize pipeline
        
        Args:
            config: Configuration dict (optional)
        """
        self.config = config or {}
        
        # Initialize components
        api_key = self.config.get('api_key') or None
        self.client = SportbexClient(api_key)
        self.filter = SportbexFilter(
            min_odds=self.config.get('min_odds', 1.40),
            max_odds=self.config.get('max_odds', 1.80),
            min_ranking_delta=self.config.get('min_ranking_delta', 20),
            max_ranking_delta=self.config.get('max_ranking_delta', 80),
            min_candidates=self.config.get('min_candidates', 5),
            max_candidates=self.config.get('max_candidates', 20)
        )
        self.notion_logger = SportbexNotionLogger()
    
    async def run(self) -> Dict[str, Any]:
        """
        Run complete pipeline
        
        Returns:
            Dictionary with pipeline results
        """
        logger.info("🚀 Starting Sportbex Daily Candidates Pipeline...")
        start_time = datetime.now()
        
        try:
            # Step 1: Fetch matches from Sportbex API
            logger.info("📥 Step 1: Fetching matches from Sportbex API...")
            
            async with self.client:
                matches = await self.client.get_matches(
                    days_ahead=self.config.get('days_ahead', 2),
                    tournament_types=self.config.get('tournament_types')
                )
            
            if not matches:
                logger.warning("⚠️ No matches found from Sportbex API")
                return {
                    'success': False,
                    'error': 'No matches found',
                    'timestamp': datetime.now().isoformat(),
                    'candidates_created': 0
                }
            
            logger.info(f"✅ Fetched {len(matches)} matches from Sportbex API")
            
            # Step 2: Filter matches
            logger.info("🔍 Step 2: Filtering matches...")
            candidates = self.filter.filter_matches(matches)
            
            if not candidates:
                logger.warning("⚠️ No candidates found after filtering")
                return {
                    'success': True,
                    'timestamp': datetime.now().isoformat(),
                    'matches_fetched': len(matches),
                    'candidates_created': 0,
                    'message': 'No candidates met criteria'
                }
            
            logger.info(f"✅ Filtered to {len(candidates)} candidates")
            
            # Step 3: Log to Notion
            logger.info("📤 Step 3: Logging candidates to Notion...")
            results = self.notion_logger.log_candidates_batch(candidates)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Summary
            logger.info("=" * 80)
            logger.info("✅ PIPELINE COMPLETED")
            logger.info("=" * 80)
            logger.info(f"📊 Matches fetched: {len(matches)}")
            logger.info(f"🎯 Candidates filtered: {len(candidates)}")
            logger.info(f"📝 Candidates created in Notion: {results['created']}")
            logger.info(f"⏭️ Duplicates skipped: {results['duplicates']}")
            logger.info(f"❌ Errors: {results['errors']}")
            logger.info(f"⏱️ Duration: {duration:.1f}s")
            logger.info("=" * 80)
            
            return {
                'success': True,
                'timestamp': end_time.isoformat(),
                'duration_seconds': duration,
                'matches_fetched': len(matches),
                'candidates_filtered': len(candidates),
                'candidates_created': results['created'],
                'candidates_duplicates': results['duplicates'],
                'candidates_errors': results['errors'],
                'page_ids': results['page_ids']
            }
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sportbex Daily Candidates Pipeline')
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    parser.add_argument('--api-key', type=str, help='Sportbex API key')
    parser.add_argument('--min-odds', type=float, default=1.40, help='Minimum odds')
    parser.add_argument('--max-odds', type=float, default=1.80, help='Maximum odds')
    parser.add_argument('--min-candidates', type=int, default=5, help='Minimum candidates')
    parser.add_argument('--max-candidates', type=int, default=20, help='Maximum candidates')
    parser.add_argument('--days-ahead', type=int, default=2, help='Days ahead to fetch')
    
    args = parser.parse_args()
    
    config = {
        'api_key': args.api_key,
        'min_odds': args.min_odds,
        'max_odds': args.max_odds,
        'min_candidates': args.min_candidates,
        'max_candidates': args.max_candidates,
        'days_ahead': args.days_ahead
    }
    
    if args.test:
        logger.info("🧪 Running in TEST mode")
        config['max_candidates'] = 3  # Limit for testing
    
    pipeline = SportbexDailyCandidatesPipeline(config)
    result = await pipeline.run()
    
    if result.get('success'):
        print("\n✅ Pipeline completed successfully!")
        print(f"   Candidates created: {result.get('candidates_created', 0)}")
        sys.exit(0)
    else:
        print(f"\n❌ Pipeline failed: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

