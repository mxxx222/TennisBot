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
    config = {
        'scraper': {
            'target_tournaments': ['W15', 'W35', 'W50'],
            'rate_limit': 2.5,
        },
        'notion': {
            'tennis_prematch_db_id': None,  # Will load from env
        }
    }
    
    pipeline = ITFNotionPipeline(config)
    result = await pipeline.run_pipeline()
    
    if result.get('success'):
        print(f"✅ Pipeline completed: {result['matches_created']} matches created")
        sys.exit(0)
    else:
        print(f"❌ Pipeline failed: {result.get('error')}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
