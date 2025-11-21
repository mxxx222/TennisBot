#!/usr/bin/env python3
"""
Update Match Results
====================

Queries matches with Status="Predicted" or "Pending Results",
fetches actual results from Sportbex or other sources,
and updates Match Results DB with final results.
"""

import os
import sys
from datetime import datetime, timedelta
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

# Import logger
from src.notion.match_results_logger import MatchResultsLogger
from scripts.tennis_ai.sportbex_client_simple import SportbexClient


class MatchResultsUpdater:
    """Updates match results in Match Results DB"""
    
    def __init__(self):
        self.logger = MatchResultsLogger()
        self.sportbex = SportbexClient()
        self.notion = None
        
        if NOTION_AVAILABLE:
            notion_token = os.getenv('NOTION_API_KEY') or os.getenv('NOTION_TOKEN')
            if notion_token:
                self.notion = Client(auth=notion_token)
    
    def get_pending_results(self, days_back: int = 7) -> List[Dict]:
        """
        Get matches that need result updates
        
        Args:
            days_back: How many days back to check
            
        Returns:
            List of match pages
        """
        if not self.notion or not self.logger.database_id:
            return []
        
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        try:
            # Query matches with Status="Predicted" or matches past their match date
            response = self.notion.databases.query(
                database_id=self.logger.database_id,
                filter={
                    "or": [
                        {"property": "Status", "select": {"equals": "Predicted"}},
                        {"property": "Status", "select": {"equals": "Pending Results"}}
                    ]
                },
                sorts=[{"property": "Match Date", "direction": "ascending"}]
            )
            
            matches = []
            for page in response['results']:
                match_date = self._get_date_property(page['properties'].get('Match Date'))
                if match_date and match_date < datetime.now():
                    matches.append(page)
            
            return matches
        
        except Exception as e:
            print(f"❌ Error fetching pending results: {e}")
            return []
    
    def _get_date_property(self, prop) -> Optional[datetime]:
        """Extract date from Notion property"""
        if prop and prop.get('date'):
            date_str = prop['date']['start']
            try:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                return None
        return None
    
    def fetch_result_from_sportbex(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch match result from Sportbex API
        
        Args:
            event_id: Sportbex event ID
            
        Returns:
            Dictionary with result data or None
        """
        try:
            # This is a placeholder - actual implementation depends on Sportbex API
            # You may need to use the async SportbexClient or implement result fetching
            print(f"  🔍 Fetching result for event {event_id}...")
            
            # Placeholder: In production, implement actual API call
            # result = await self.sportbex.get_match_result(event_id)
            
            return None
        
        except Exception as e:
            print(f"  ⚠️ Error fetching result: {e}")
            return None
    
    def update_match_result(self, page_id: str, result_data: Dict[str, Any]) -> bool:
        """
        Update match with result data
        
        Args:
            page_id: Notion page ID
            result_data: Dictionary with result information
            
        Returns:
            True if successful
        """
        updates = {
            'actual_winner': result_data.get('winner'),
            'actual_score': result_data.get('score'),
            'result_date': result_data.get('result_date', datetime.now().isoformat()),
            'status': 'Resulted',
        }
        
        # Add closing odds if available
        if 'closing_odds_a' in result_data:
            updates['closing_odds_a'] = result_data['closing_odds_a']
        if 'closing_odds_b' in result_data:
            updates['closing_odds_b'] = result_data['closing_odds_b']
        
        # Calculate PnL if bet was placed
        if result_data.get('bet_placed'):
            bet_side = result_data.get('bet_side')
            bet_odds = result_data.get('bet_odds')
            stake_eur = result_data.get('stake_eur', 0)
            winner = result_data.get('winner')
            
            if bet_side and bet_odds and winner:
                # Calculate PnL
                if (bet_side == 'Player A' and winner == 'Player A') or \
                   (bet_side == 'Player B' and winner == 'Player B'):
                    pnl = (bet_odds - 1) * stake_eur
                else:
                    pnl = -stake_eur
                
                updates['pnl_eur'] = pnl
                
                # Calculate CLV if closing odds available
                if 'closing_odds_a' in result_data and bet_side == 'Player A':
                    closing_odds = result_data['closing_odds_a']
                    clv = ((bet_odds - closing_odds) / closing_odds) * 100
                    updates['clv_pct'] = clv
                elif 'closing_odds_b' in result_data and bet_side == 'Player B':
                    closing_odds = result_data['closing_odds_b']
                    clv = ((bet_odds - closing_odds) / closing_odds) * 100
                    updates['clv_pct'] = clv
        
        return self.logger.update_match(page_id, updates)
    
    def run_update_cycle(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Run complete update cycle
        
        Args:
            days_back: How many days back to check for results
            
        Returns:
            Dictionary with update results
        """
        print("🔄 Match Results Updater - Starting update cycle...")
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        start_time = datetime.now()
        
        try:
            # Get pending matches
            print("\n📋 Fetching pending matches...")
            pending_matches = self.get_pending_results(days_back=days_back)
            
            if not pending_matches:
                print("✅ No matches need result updates")
                return {
                    'success': True,
                    'matches_checked': 0,
                    'matches_updated': 0,
                    'timestamp': datetime.now().isoformat()
                }
            
            print(f"✅ Found {len(pending_matches)} matches needing updates")
            
            # Update each match
            updated_count = 0
            error_count = 0
            
            for page in pending_matches:
                try:
                    props = page['properties']
                    event_id = self._get_text_property(props.get('Event ID'))
                    match_name = self._get_title_property(props.get('Match Name'))
                    
                    print(f"\n🔍 Processing: {match_name}")
                    
                    # Try to fetch result
                    if event_id:
                        result_data = self.fetch_result_from_sportbex(event_id)
                    else:
                        result_data = None
                    
                    # If result fetched, update
                    if result_data:
                        if self.update_match_result(page['id'], result_data):
                            updated_count += 1
                            print(f"  ✅ Updated with result")
                        else:
                            error_count += 1
                            print(f"  ❌ Failed to update")
                    else:
                        print(f"  ⚠️ Result not available yet")
                
                except Exception as e:
                    print(f"  ❌ Error processing match: {e}")
                    error_count += 1
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print("\n" + "="*60)
            print("✅ UPDATE CYCLE COMPLETED")
            print("="*60)
            print(f"📊 Matches checked: {len(pending_matches)}")
            print(f"✅ Matches updated: {updated_count}")
            print(f"❌ Errors: {error_count}")
            print(f"⏱️ Duration: {duration:.1f}s")
            print("="*60)
            
            return {
                'success': True,
                'timestamp': end_time.isoformat(),
                'duration_seconds': duration,
                'matches_checked': len(pending_matches),
                'matches_updated': updated_count,
                'errors': error_count
            }
        
        except Exception as e:
            print(f"❌ Error in update cycle: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_title_property(self, prop) -> str:
        """Extract title from Notion property"""
        if prop and prop.get('title'):
            return prop['title'][0]['text']['content'] if prop['title'] else ''
        return ''
    
    def _get_text_property(self, prop) -> str:
        """Extract text from Notion property"""
        if prop and prop.get('rich_text'):
            return prop['rich_text'][0]['text']['content'] if prop['rich_text'] else ''
        return ''


def main():
    """Main entry point"""
    updater = MatchResultsUpdater()
    result = updater.run_update_cycle(days_back=7)
    
    if result.get('success'):
        print("\n✅ Match results update completed!")
        print(f"   Matches updated: {result.get('matches_updated', 0)}")
        sys.exit(0)
    else:
        print(f"\n❌ Match results update failed: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()

