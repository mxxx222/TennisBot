# Vercel Cron Job for ITF Scraper (Python)
# Runs 2x per day at 08:00 and 20:00 EET (06:00 and 18:00 UTC)
# Vercel Cron will call this endpoint automatically

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipelines.itf_notion_pipeline import ITFNotionPipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def handler(req):
    """Vercel serverless function handler"""
    # Verify this is called by Vercel Cron (optional security)
    auth_header = req.headers.get('authorization', '')
    cron_secret = os.getenv('CRON_SECRET') or os.getenv('VERCEL_CRON_SECRET')
    
    if cron_secret and auth_header != f'Bearer {cron_secret}':
        return {
            'statusCode': 401,
            'body': {'error': 'Unauthorized'}
        }
    
    logging.info('🚀 ITF Scraper Cron started')
    
    try:
        # Run ITF pipeline
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
            logging.info(f"✅ Pipeline completed: {result['matches_created']} matches created")
            return {
                'statusCode': 200,
                'body': {
                    'success': True,
                    'timestamp': result.get('timestamp'),
                    'matches_scraped': result.get('matches_scraped', 0),
                    'matches_created': result.get('matches_created', 0),
                    'matches_duplicates': result.get('matches_duplicates', 0),
                    'matches_errors': result.get('matches_errors', 0),
                }
            }
        else:
            logging.error(f"❌ Pipeline failed: {result.get('error')}")
            return {
                'statusCode': 500,
                'body': {
                    'success': False,
                    'error': result.get('error'),
                    'timestamp': result.get('timestamp'),
                }
            }
    except Exception as e:
        logging.error(f'❌ ITF Scraper Cron Error: {e}', exc_info=True)
        return {
            'statusCode': 500,
            'body': {
                'success': False,
                'error': str(e),
            }
        }

# Vercel Python runtime expects this
def main(req):
    """Main entry point for Vercel"""
    return asyncio.run(handler(req))

