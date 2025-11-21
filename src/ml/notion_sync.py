#!/usr/bin/env python3
"""
Notion to SQLite Sync
=====================

Synchronizes match data from Notion Match Results DB to SQLite for ML training.
Extracts only the 24 properties needed for ML (excludes AI predictions, betting info).
"""

import os
import sys
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / 'telegram_secrets.env'
if env_path.exists():
    load_dotenv(env_path)

# Notion API
try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    print("⚠️ notion-client not installed. Install with: pip install notion-client")

# Import SQLite DB
from src.ml.data_collector import MatchResultsDB
from src.scrapers.sportbex_client import SportbexMatch

logger = logging.getLogger(__name__)


class NotionToSQLiteSync:
    """Syncs match data from Notion to SQLite for ML training"""
    
    def __init__(self, database_id: Optional[str] = None, db_path: Optional[str] = None):
        """
        Initialize Notion client and SQLite connection.
        
        Args:
            database_id: Notion Match Results database ID (optional, from env)
            db_path: Path to SQLite database (optional)
        """
        self.notion = None
        self.notion_db_id = database_id or os.getenv('NOTION_MATCH_RESULTS_DB_ID')
        
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / 'data' / 'match_results.db'
        self.db_path = Path(db_path)
        
        self.sqlite_db = MatchResultsDB(db_path=str(self.db_path))
        
        if NOTION_AVAILABLE:
            notion_token = os.getenv('NOTION_API_KEY') or os.getenv('NOTION_TOKEN')
            if notion_token:
                self.notion = Client(auth=notion_token)
            else:
                logger.warning("⚠️ NOTION_API_KEY not set")
        else:
            logger.warning("⚠️ notion-client not available")
        
        if not self.notion_db_id:
            logger.warning("⚠️ NOTION_MATCH_RESULTS_DB_ID not set")
        
    def sync(self, full_sync: bool = False) -> Dict[str, Any]:
        """
        Main sync method - syncs Notion → SQLite
        
        Args:
            full_sync: If True, sync all pages. If False, only sync recent changes.
            
        Returns:
            Dictionary with sync results
        """
        return self.sync_recent_matches(days_back=7 if not full_sync else 365)
    
    def sync_recent_matches(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Sync recent matches from Notion to SQLite
        
        Args:
            days_back: How many days back to sync
            
        Returns:
            Dictionary with sync results
        """
        if not self.notion or not self.notion_db_id:
            logger.error("❌ Notion client or DB ID not available")
            return {
                'success': False,
                'error': 'Notion client or DB ID not available'
            }
        
        logger.info(f"🔄 Syncing matches from last {days_back} days...")
        
        try:
            # Query Notion for recent matches
            from datetime import timedelta
            cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            response = self.notion.databases.query(
                database_id=self.notion_db_id,
                filter={
                    "property": "Scan Date",
                    "date": {"on_or_after": cutoff_date}
                },
                sorts=[{"property": "Match Date", "direction": "descending"}]
            )
            
            matches = response.get('results', [])
            logger.info(f"📊 Found {len(matches)} matches in Notion")
            
            synced_count = 0
            skipped_count = 0
            error_count = 0
            
            for page in matches:
                try:
                    match_data = self._parse_notion_page(page)
                    sportbex_match = self._convert_to_sportbex_match(match_data)
                    
                    if sportbex_match:
                        # Insert into SQLite
                        if self.sqlite_db.insert_match(sportbex_match):
                            synced_count += 1
                            
                            # If result available, insert result too
                            if match_data.get('actual_winner'):
                                self._insert_result(match_data)
                        else:
                            skipped_count += 1
                    else:
                        skipped_count += 1
                
                except Exception as e:
                    logger.error(f"❌ Error syncing match: {e}")
                    error_count += 1
            
            logger.info(f"✅ Sync complete: {synced_count} synced, {skipped_count} skipped, {error_count} errors")
            
            return {
                'success': True,
                'synced': synced_count,
                'skipped': skipped_count,
                'errors': error_count,
                'total': len(matches)
            }
            
        except Exception as e:
            logger.error(f"❌ Sync failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_notion_page(self, page: Dict) -> Dict[str, Any]:
        """Parse Notion page to match data dictionary"""
        props = page.get('properties', {})
        
        return {
            'match_id': self._get_text_property(props.get('Match ID')) or self._get_text_property(props.get('Event ID')),
            'match_name': self._get_title_property(props.get('Match Name')),
            'player_a': self._get_text_property(props.get('Player A')),
            'player_b': self._get_text_property(props.get('Player B')),
            'tournament': self._get_text_property(props.get('Tournament')),
            'tournament_tier': self._get_select_property(props.get('Tournament Tier')),
            'surface': self._get_select_property(props.get('Surface')),
            'match_date': self._get_date_property(props.get('Match Date')),
            'player1_ranking': self._get_number_property(props.get('Rank A')),
            'player2_ranking': self._get_number_property(props.get('Rank B')),
            'player1_odds': self._get_number_property(props.get('Opening Odds A')),
            'player2_odds': self._get_number_property(props.get('Opening Odds B')),
            'actual_winner': self._get_select_property(props.get('Actual Winner')),
            'actual_score': self._get_text_property(props.get('Actual Score')),
            'result_date': self._get_date_property(props.get('Result Date')),
        }
    
    def _convert_to_sportbex_match(self, match_data: Dict[str, Any]) -> Optional[SportbexMatch]:
        """Convert match data to SportbexMatch object"""
        try:
            # Generate match_id if not available
            match_id = match_data.get('match_id')
            if not match_id:
                match_name = match_data.get('match_name', '')
                if match_name:
                    import hashlib
                    match_id = hashlib.md5(match_name.encode()).hexdigest()[:12]
                else:
                    return None
            
            # Parse match date
            match_date = match_data.get('match_date')
            if isinstance(match_date, str):
                try:
                    match_date = datetime.fromisoformat(match_date.replace('Z', '+00:00'))
                except:
                    match_date = None
            
            return SportbexMatch(
                match_id=match_id,
                tournament=match_data.get('tournament', ''),
                player1=match_data.get('player_a', ''),
                player2=match_data.get('player_b', ''),
                player1_ranking=match_data.get('player1_ranking'),
                player2_ranking=match_data.get('player2_ranking'),
                player1_odds=match_data.get('player1_odds'),
                player2_odds=match_data.get('player2_odds'),
                commence_time=match_date,
                surface=match_data.get('surface'),
                tournament_tier=match_data.get('tournament_tier')
            )
        
        except Exception as e:
            logger.error(f"Error converting to SportbexMatch: {e}")
            return None
    
    def _insert_result(self, match_data: Dict[str, Any]):
        """Insert match result into SQLite"""
        try:
            match_id = match_data.get('match_id')
            if not match_id:
                return
            
            winner = match_data.get('actual_winner')
            score = match_data.get('actual_score', '')
            result_date = match_data.get('result_date')
            
            if not winner:
                return
            
            # Determine player1_won
            player1_won = None
            if winner == 'Player A':
                player1_won = True
            elif winner == 'Player B':
                player1_won = False
            
            # Parse result_date
            if isinstance(result_date, str):
                try:
                    result_date = datetime.fromisoformat(result_date.replace('Z', '+00:00'))
                except:
                    result_date = datetime.now()
            elif result_date is None:
                result_date = datetime.now()
            
            # Insert result
            import sqlite3
            conn = sqlite3.connect(str(self.sqlite_db.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO results (
                    match_id, winner, score, result_date, player1_won, player2_won
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                match_id,
                winner,
                score,
                result_date.isoformat() if isinstance(result_date, datetime) else result_date,
                player1_won,
                not player1_won if player1_won is not None else None
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error inserting result: {e}")
            if 'conn' in locals():
                conn.close()
    
    # Helper methods for Notion properties
    def _get_title_property(self, prop) -> str:
        if prop and prop.get('title'):
            return prop['title'][0]['text']['content'] if prop['title'] else ''
        return ''
    
    def _get_text_property(self, prop) -> str:
        if prop and prop.get('rich_text'):
            return prop['rich_text'][0]['text']['content'] if prop['rich_text'] else ''
        return ''
    
    def _get_select_property(self, prop) -> Optional[str]:
        if prop and prop.get('select'):
            return prop['select']['name']
        return None
    
    def _get_number_property(self, prop) -> Optional[float]:
        if prop and 'number' in prop:
            return prop['number']
        return None
    
    def _get_date_property(self, prop) -> Optional[str]:
        if prop and prop.get('date'):
            return prop['date']['start']
        return None


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sync Notion Match Results DB to SQLite')
    parser.add_argument('--full', action='store_true', help='Full sync (all pages)')
    parser.add_argument('--days', type=int, default=7, help='Days back to sync (default: 7, ignored if --full)')
    parser.add_argument('--stats', action='store_true', help='Show database stats')
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    sync = NotionToSQLiteSync()
    
    if args.stats:
        # Show stats
        stats = sync.sqlite_db
        total = stats.count_matches()
        results = stats.count_results()
        print(f"\n📊 SQLite Database Stats")
        print(f"   Total matches: {total}")
        print(f"   With results: {results}")
    else:
        result = sync.sync(full_sync=args.full)
        
        if result.get('success'):
            print(f"\n✅ Sync completed!")
            print(f"   Synced: {result.get('synced', 0)}")
            print(f"   Skipped: {result.get('skipped', 0)}")
            print(f"   Errors: {result.get('errors', 0)}")
            sys.exit(0)
        else:
            print(f"\n❌ Sync failed: {result.get('error')}")
            sys.exit(1)


if __name__ == "__main__":
    main()
