#!/usr/bin/env python3
"""
ITF Scraper Runner
Runs the ITF Notion pipeline
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.pipelines.itf_notion_pipeline import ITFNotionPipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def main():
    """Run ITF pipeline"""
    import os
    config = {
        'scraper': {
            'target_tournaments': ['W15', 'W25', 'W35', 'W50', 'W75', 'W100'],  # All tiers for Raw Feed
            'rate_limit': 2.5,
            'fetch_odds': False,
        },
        'notion': {
            'raw_match_feed_db_id': os.getenv('RAW_MATCH_FEED_DB_ID'),
            'tennis_prematch_db_id': None,  # Will load from env
            # Migration mode: parallel_write=True for Phase 1 (writes to both DBs)
            'parallel_write': os.getenv('PARALLEL_WRITE', 'false').lower() == 'true',
        }
    }
    
    pipeline = ITFNotionPipeline(config)
    result = await pipeline.run_pipeline()
    
    if result.get('success'):
        matches_created = result.get('matches_created', 0)
        print(f"✅ Pipeline completed: {matches_created} matches created")
        sys.exit(0)
    else:
        print(f"❌ Pipeline failed: {result.get('error')}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
