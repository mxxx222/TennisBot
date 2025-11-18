#!/usr/bin/env python3
"""
🧪 Test ITF Notion Pipeline
Testaa päivitettyä pipelinea uusilla Notion-kentillä
"""

import asyncio
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables
env_path = Path(__file__).parent / 'telegram_secrets.env'
if env_path.exists():
    load_dotenv(env_path)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.pipelines.itf_notion_pipeline import ITFNotionPipeline
from src.scrapers.flashscore_itf_scraper import ITFMatch
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def test_pipeline():
    """Testaa ITF Notion Pipelinea"""
    print("\n" + "="*80)
    print("🧪 TESTING ITF NOTION PIPELINE")
    print("="*80)
    
    # Check credentials
    notion_token = os.getenv('NOTION_API_KEY') or os.getenv('NOTION_TOKEN')
    db_id = os.getenv('NOTION_TENNIS_PREMATCH_DB_ID')
    
    if not notion_token:
        print("❌ Notion token not found!")
        print("   Set NOTION_API_KEY or NOTION_TOKEN in telegram_secrets.env")
        return False
    
    if not db_id:
        print("❌ Tennis Prematch database ID not found!")
        print("   Set NOTION_TENNIS_PREMATCH_DB_ID in telegram_secrets.env")
        return False
    
    print(f"✅ Token found: {notion_token[:20]}...")
    print(f"✅ Database ID: {db_id[:20]}...")
    
    # Initialize pipeline
    config = {
        'scraper': {
            'target_tournaments': ['W15'],  # Test with just W15
            'rate_limit': 2.5,
        },
        'notion': {
            'tennis_prematch_db_id': db_id,
        }
    }
    
    print("\n🔄 Initializing pipeline...")
    pipeline = ITFNotionPipeline(config)
    
    # Test transform function with sample data
    print("\n📝 Testing data transformation...")
    sample_match = ITFMatch(
        match_id="test_match_001",
        tournament="ITF W15 Sharm ElSheikh 20 Women",
        tournament_tier="W15",
        surface="Hard",
        player1="Maria Garcia",
        player2="Anna Smith",
        round="R32",
        match_status="not_started",
        live_score=None,
        set1_score=None,
        scheduled_time=datetime.now(),
        match_url=None,
        scraped_at=datetime.now()
    )
    
    notion_data = pipeline.transform_match_to_notion(sample_match)
    
    print("\n📊 Transformed data:")
    print(f"   Title: {notion_data['title']}")
    print("\n   Properties:")
    for key, value in notion_data['properties'].items():
        if isinstance(value, dict):
            if 'select' in value:
                print(f"      {key}: {value['select']['name']}")
            elif 'rich_text' in value:
                print(f"      {key}: {value['rich_text'][0]['text']['content']}")
            elif 'date' in value:
                print(f"      {key}: {value['date']['start']}")
    
    # Check required fields
    required_fields = ['Turnaus', 'Pelaaja 1', 'Pelaaja 2', 'Päivämäärä', 'Scraper Source', 'Status']
    missing_fields = [f for f in required_fields if f not in notion_data['properties']]
    
    if missing_fields:
        print(f"\n⚠️ Missing required fields: {missing_fields}")
        return False
    
    print("\n✅ All required fields present!")
    print("\n💡 To run full pipeline:")
    print("   python3 src/pipelines/itf_notion_pipeline.py")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_pipeline())
    sys.exit(0 if success else 1)

