#!/usr/bin/env python3
"""
📊 MATCH HISTORY CALCULATOR
===========================

Calculates Last 10 match history, Win Streak, and L10 Win % for players
by querying Tennis Prematch database and updating Player Cards.

Features:
- Queries Tennis Prematch DB for player matches (via Player A/B Card relations)
- Calculates Last 10 match string (e.g., "W-L-W-W-L-W-L-W-W-L")
- Calculates Win Streak (current winning streak)
- Calculates L10 Win % (win percentage of last 10 matches)
- Updates Player Cards DB in Notion
"""

import os
import sys
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
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
    print("❌ ERROR: notion-client not installed")
    print("   Install: pip install notion-client")

logger = logging.getLogger(__name__)


class MatchHistoryCalculator:
    """
    Calculates match history statistics for players
    """
    
    def __init__(self, 
                 prematch_db_id: Optional[str] = None,
                 player_cards_db_id: Optional[str] = None):
        """
        Initialize calculator
        
        Args:
            prematch_db_id: Tennis Prematch database ID (optional, from env)
            player_cards_db_id: Player Cards database ID (optional, from env)
        """
        if not NOTION_AVAILABLE:
            self.client = None
            logger.error("❌ Notion client not available")
            return
        
        notion_token = os.getenv('NOTION_API_KEY') or os.getenv('NOTION_TOKEN')
        if not notion_token:
            self.client = None
            logger.error("❌ NOTION_API_KEY or NOTION_TOKEN not set")
            return
        
        self.client = Client(auth=notion_token)
        self.prematch_db_id = (
            prematch_db_id or 
            os.getenv('NOTION_TENNIS_PREMATCH_DB_ID') or 
            os.getenv('NOTION_PREMATCH_DB_ID')
        )
        self.player_cards_db_id = (
            player_cards_db_id or 
            os.getenv('NOTION_ITF_PLAYER_CARDS_DB_ID') or 
            os.getenv('PLAYER_CARDS_DB_ID')
        )
        
        if not self.prematch_db_id:
            logger.error("❌ Tennis Prematch database ID not set")
        if not self.player_cards_db_id:
            logger.error("❌ Player Cards database ID not set")
        
        logger.info("📊 Match History Calculator initialized")
    
    def get_player_matches(self, player_card_id: str) -> List[Dict[str, Any]]:
        """
        Get all matches for a player from Tennis Prematch DB
        
        Args:
            player_card_id: Player Card page ID
            
        Returns:
            List of match dictionaries sorted by date (newest first)
        """
        if not self.client or not self.prematch_db_id:
            return []
        
        try:
            matches = []
            
            # Query matches where player is Player A
            response_a = self.client.databases.query(
                database_id=self.prematch_db_id,
                filter={
                    "property": "Player A Card",
                    "relation": {
                        "contains": player_card_id
                    }
                },
                sorts=[{"property": "Päivämäärä", "direction": "descending"}]
            )
            
            for page in response_a.get('results', []):
                match_data = self._parse_match_page(page, is_player_a=True)
                if match_data:
                    matches.append(match_data)
            
            # Query matches where player is Player B
            response_b = self.client.databases.query(
                database_id=self.prematch_db_id,
                filter={
                    "property": "Player B Card",
                    "relation": {
                        "contains": player_card_id
                    }
                },
                sorts=[{"property": "Päivämäärä", "direction": "descending"}]
            )
            
            for page in response_b.get('results', []):
                match_data = self._parse_match_page(page, is_player_a=False)
                if match_data:
                    matches.append(match_data)
            
            # Sort by date (newest first)
            matches.sort(key=lambda x: x.get('date', datetime.min), reverse=True)
            
            return matches
            
        except Exception as e:
            logger.error(f"❌ Error getting matches for player {player_card_id}: {e}")
            return []
    
    def _parse_match_page(self, page: Dict, is_player_a: bool) -> Optional[Dict[str, Any]]:
        """
        Parse Notion match page to match data
        
        Args:
            page: Notion page object
            is_player_a: True if player is Player A, False if Player B
            
        Returns:
            Match dictionary or None
        """
        try:
            props = page.get('properties', {})
            
            # Get date
            date_prop = props.get('Päivämäärä', {})
            match_date = None
            if date_prop.get('date'):
                date_str = date_prop['date'].get('start')
                if date_str:
                    try:
                        match_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    except:
                        pass
            
            # Get actual winner
            winner_prop = props.get('Actual Winner', {})
            actual_winner = None
            if winner_prop.get('select'):
                actual_winner = winner_prop['select'].get('name')
            
            # Determine if player won
            # Winner options: "Player A", "Player B", "A", "B", etc.
            won = None
            if actual_winner:
                winner_lower = actual_winner.lower()
                if 'a' in winner_lower:
                    won = is_player_a
                elif 'b' in winner_lower:
                    won = not is_player_a
            
            return {
                'id': page.get('id'),
                'date': match_date or datetime.min,
                'won': won,
                'actual_winner': actual_winner,
                'is_player_a': is_player_a
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing match page: {e}")
            return None
    
    def calculate_last_10(self, matches: List[Dict[str, Any]]) -> Tuple[str, int, float]:
        """
        Calculate Last 10 match string, Win Streak, and L10 Win %
        
        Args:
            matches: List of match dictionaries (sorted newest first)
            
        Returns:
            Tuple of (last_10_string, win_streak, win_percentage)
        """
        # Filter matches with results
        matches_with_results = [m for m in matches if m.get('won') is not None]
        
        # Get last 10 matches
        last_10 = matches_with_results[:10]
        
        # Generate last 10 string
        last_10_string = ""
        for match in last_10:
            if match['won']:
                last_10_string += "W"
            else:
                last_10_string += "L"
        
        # If less than 10 matches, pad with "-"
        while len(last_10_string) < 10:
            last_10_string += "-"
        
        # Calculate win streak (from newest match)
        win_streak = 0
        for match in matches_with_results:
            if match['won']:
                win_streak += 1
            else:
                break
        
        # Calculate win percentage
        if last_10:
            wins = sum(1 for m in last_10 if m.get('won'))
            win_percentage = (wins / len(last_10)) * 100.0
        else:
            win_percentage = 0.0
        
        return last_10_string, win_streak, win_percentage
    
    def update_player_history(self, player_card_id: str) -> bool:
        """
        Calculate and update match history for a player
        
        Args:
            player_card_id: Player Card page ID
            
        Returns:
            True if successful
        """
        if not self.client or not self.player_cards_db_id:
            return False
        
        try:
            # Get matches
            matches = self.get_player_matches(player_card_id)
            
            if not matches:
                logger.debug(f"No matches found for player {player_card_id[:8]}...")
                return False
            
            # Calculate statistics
            last_10_string, win_streak, win_percentage = self.calculate_last_10(matches)
            
            # Update Player Card
            properties = {
                'Last 10': {
                    'rich_text': [{'text': {'content': last_10_string}}]
                },
                'Win Streak': {
                    'number': win_streak
                },
                'L10 Win %': {
                    'number': round(win_percentage, 1)
                }
            }
            
            self.client.pages.update(
                page_id=player_card_id,
                properties=properties
            )
            
            logger.debug(f"✅ Updated history for {player_card_id[:8]}...: {last_10_string}, Streak={win_streak}, Win%={win_percentage:.1f}%")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating history for {player_card_id}: {e}")
            return False
    
    def update_all_players(self, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Update match history for all players in Player Cards DB
        
        Args:
            limit: Optional limit on number of players to process
            
        Returns:
            Dictionary with counts
        """
        if not self.client or not self.player_cards_db_id:
            return {'updated': 0, 'failed': 0, 'total': 0}
        
        try:
            # Get all players
            response = self.client.databases.query(database_id=self.player_cards_db_id)
            players = response.get('results', [])
            
            if limit:
                players = players[:limit]
            
            logger.info(f"📊 Updating match history for {len(players)} players...")
            
            updated_count = 0
            failed_count = 0
            
            for i, player in enumerate(players, 1):
                player_id = player.get('id')
                logger.info(f"[{i}/{len(players)}] Processing player {player_id[:8]}...")
                
                # Rate limiting (3 req/s max)
                if i % 3 == 0:
                    time.sleep(1)
                
                if self.update_player_history(player_id):
                    updated_count += 1
                else:
                    failed_count += 1
            
            logger.info(f"\n✅ Update complete!")
            logger.info(f"   Updated: {updated_count}")
            logger.info(f"   Failed: {failed_count}")
            logger.info(f"   Total: {len(players)}")
            
            return {
                'updated': updated_count,
                'failed': failed_count,
                'total': len(players)
            }
            
        except Exception as e:
            logger.error(f"❌ Error updating all players: {e}")
            return {'updated': 0, 'failed': 0, 'total': 0}


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Match History Calculator')
    parser.add_argument('--player-id', help='Specific player card ID to update')
    parser.add_argument('--limit', type=int, help='Limit number of players')
    parser.add_argument('--all', action='store_true', help='Update all players')
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    calculator = MatchHistoryCalculator()
    
    if not calculator.client:
        logger.error("❌ Calculator not initialized")
        return
    
    if args.player_id:
        # Update specific player
        calculator.update_player_history(args.player_id)
    elif args.all:
        # Update all players
        calculator.update_all_players(limit=args.limit)
    else:
        logger.info("ℹ️ Use --player-id to update specific player or --all to update all players")


if __name__ == "__main__":
    main()

