#!/usr/bin/env python3
"""
BetExplorer Scraper Runner
Runs the BetExplorer Notion pipeline
"""

import asyncio
import sys
import logging
import yaml
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.pipelines.betexplorer_notion_pipeline import BetExplorerNotionPipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def load_config() -> dict:
    """Load configuration from YAML file"""
    config_path = Path(__file__).parent / 'config' / 'betexplorer_config.yaml'
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logging.warning(f"⚠️ Could not load config file: {e}")
    return {}


async def main():
    """Run BetExplorer pipeline"""
    # Load config
    config = load_config()
    
    # Set defaults if not in config
    if 'scraper' not in config:
        config['scraper'] = {}
    if 'notion' not in config:
        config['notion'] = {}
    
    # Set default values
    config['scraper'].setdefault('target_tiers', ['W15', 'W25'])
    config['scraper'].setdefault('request_delay', 2.0)
    config['scraper'].setdefault('max_retries', 3)
    config['scraper'].setdefault('timeout', 30)
    config['scraper'].setdefault('use_selenium', True)
    
    config['notion'].setdefault('tennis_prematch_db_id', None)  # Will load from env
    config['notion'].setdefault('batch_size', 3)
    config['notion'].setdefault('batch_delay', 1.0)
    
    pipeline = BetExplorerNotionPipeline(config)
    result = await pipeline.run_pipeline()
    
    if result.get('success'):
        matches_created = result.get('matches_created', 0)
        matches_scraped = result.get('matches_scraped', 0)
        print(f"✅ Pipeline completed: {matches_created}/{matches_scraped} matches created")
        sys.exit(0)
    else:
        print(f"❌ Pipeline failed: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

