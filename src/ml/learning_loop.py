#!/usr/bin/env python3
"""
Learning Loop
=============

Daily learning orchestrator (runs at 21:00).
Fetches results from completed matches.
Updates training dataset.
Triggers incremental learning.

This is part of Layer 5: Continuous Learning.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ml.notion_sync import NotionToSQLiteSync
from src.ml.incremental_learner import IncrementalLearner
from src.ml.data_collector import MatchResultsDB

logger = logging.getLogger(__name__)


class LearningLoop:
    """Orchestrates daily learning process"""
    
    def __init__(self, api_key: Optional[str] = None, db_path: Optional[str] = None):
        """
        Initialize learning loop
        
        Args:
            api_key: Sportbex API key (not used anymore, kept for compatibility)
            db_path: Path to Match Results database
        """
        self.syncer = NotionToSQLiteSync(db_path=db_path)
        self.incremental_learner = IncrementalLearner(db_path=db_path)
        self.db = MatchResultsDB(db_path=db_path)
        
        logger.info("✅ Learning Loop initialized")
    
    async def run_daily_learning(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Run daily learning process
        
        Args:
            days_back: Number of days to look back for results
            
        Returns:
            Dictionary with learning results
        """
        logger.info("=" * 80)
        logger.info("🚀 STARTING DAILY LEARNING LOOP")
        logger.info("=" * 80)
        logger.info(f"📅 Date: {datetime.now().isoformat()}")
        
        start_time = datetime.now()
        
        try:
            # Step 1: Sync Notion → SQLite (single source of truth)
            logger.info("\n🔄 Step 1: Syncing Notion Match Results DB → SQLite...")
            sync_result = self.syncer.sync(full_sync=False)  # Incremental sync
            
            if not sync_result.get('success'):
                logger.warning(f"⚠️ Sync had issues: {sync_result.get('error')}")
                # Continue anyway - might have existing data
            
            synced_count = sync_result.get('synced', 0)
            logger.info(f"✅ Synced {synced_count} matches from Notion")
            
            # Step 2: Get matches with results for training
            logger.info("\n🔧 Step 2: Getting matches with results for training...")
            matches_with_results = self.db.get_training_data(limit=None)
            logger.info(f"✅ Found {len(matches_with_results)} matches with results")
            
            # Step 3: Incremental learning
            logger.info("\n🧠 Step 3: Running incremental learning...")
            learning_result = self.incremental_learner.learn_from_new_data(
                days_back=days_back
            )
            
            if not learning_result.get('success'):
                logger.warning(f"⚠️ Incremental learning had issues: {learning_result.get('error')}")
            
            # Step 4: Update model accuracies (for meta-learner weights)
            logger.info("\n⚖️ Step 4: Updating model accuracies...")
            accuracy_result = self.incremental_learner.update_model_accuracies()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Summary
            logger.info("=" * 80)
            logger.info("✅ DAILY LEARNING LOOP COMPLETED")
            logger.info("=" * 80)
            logger.info(f"🔄 Matches synced from Notion: {synced_count}")
            logger.info(f"📈 Matches with results: {len(matches_with_results)}")
            logger.info(f"🧠 Incremental learning: {'✅ Success' if learning_result.get('success') else '⚠️ Issues'}")
            logger.info(f"⚖️ Accuracy update: {'✅ Success' if accuracy_result.get('success') else '⚠️ Issues'}")
            logger.info(f"⏱️ Duration: {duration:.1f}s")
            logger.info("=" * 80)
            
            return {
                'success': True,
                'timestamp': end_time.isoformat(),
                'duration_seconds': duration,
                'matches_synced': synced_count,
                'matches_with_results': len(matches_with_results),
                'incremental_learning': learning_result,
                'accuracy_update': accuracy_result
            }
            
        except Exception as e:
            logger.error(f"❌ Learning loop failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """
        Get learning statistics
        
        Returns:
            Dictionary with statistics
        """
        total_matches = self.db.count_matches()
        total_results = self.db.count_results()
        
        return {
            'total_matches': total_matches,
            'total_results': total_results,
            'coverage': total_results / max(total_matches, 1),
            'last_updated': datetime.now().isoformat()
        }


async def main():
    """Main entry point for daily learning"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Daily Learning Loop')
    parser.add_argument('--days-back', type=int, default=7, help='Days to look back')
    parser.add_argument('--api-key', type=str, help='Sportbex API key')
    parser.add_argument('--stats', action='store_true', help='Show learning statistics')
    
    args = parser.parse_args()
    
    loop = LearningLoop(api_key=args.api_key)
    
    if args.stats:
        stats = loop.get_learning_stats()
        print("\n📊 Learning Statistics:")
        print(f"   Total Matches: {stats['total_matches']}")
        print(f"   Total Results: {stats['total_results']}")
        print(f"   Coverage: {stats['coverage']:.1%}")
    else:
        result = await loop.run_daily_learning(days_back=args.days_back)
        
        if result.get('success'):
            print("\n✅ Daily learning completed!")
            print(f"   Results found: {result['results_found']}")
        else:
            print(f"\n❌ Learning failed: {result.get('error')}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())

