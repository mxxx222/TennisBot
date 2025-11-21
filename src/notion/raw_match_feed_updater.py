#!/usr/bin/env python3
"""
📥 RAW MATCH FEED DATABASE UPDATER
===================================

Helper class for writing matches to Raw Match Feed DB.
Transforms match data from scrapers (ITFMatch, BetExplorer) to Raw Match Feed schema.

Raw Match Feed Schema:
- Match ID (Title)
- Player A Name (Rich Text)
- Player B Name (Rich Text)
- Tournament (Rich Text)
- Tournament Tier (Select: ITF W15, ITF W25, ITF W35, ITF W50, etc.)
- Surface (Select: Hard, Clay, Grass, Carpet)
- Round (Select: R32, R16, QF, SF, F)
- Player A Odds (Number)
- Player B Odds (Number)
- Best Odds A (Number) - Optional
- Best Odds B (Number) - Optional
- Bookmaker (Select) - Optional
- Match Date (Date)
- Match Status (Select: Upcoming, Live, Completed, Postponed, Cancelled)
- Data Source (Select: FlashScore, BetExplorer, etc.)
- Scraped At (Date)
- Raw Data Quality (Select: Complete, Partial, Missing Data)
- AI Processed (Checkbox) - Default: false
- AI Approved (Checkbox) - Default: unset
- AI Score (Number) - Default: unset
- AI Notes (Rich Text) - Default: unset
"""

import os
import logging
from typing import Optional, Dict, Any, Union
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(Path(__file__).parent.parent.parent, 'telegram_secrets.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

# Notion API
try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False

logger = logging.getLogger(__name__)


class RawMatchFeedUpdater:
    """Helper class for writing matches to Raw Match Feed DB"""
    
    def __init__(self, database_id: Optional[str] = None):
        """
        Initialize Raw Match Feed Updater
        
        Args:
            database_id: Raw Match Feed database ID (optional, from env)
        """
        if not NOTION_AVAILABLE:
            logger.error("❌ notion-client not installed")
            self.client = None
        else:
            notion_token = os.getenv('NOTION_API_KEY') or os.getenv('NOTION_TOKEN')
            if notion_token:
                self.client = Client(auth=notion_token)
            else:
                logger.error("❌ NOTION_TOKEN not set")
                self.client = None
        
        # Get database ID
        self.database_id = (
            database_id or
            os.getenv('RAW_MATCH_FEED_DB_ID') or
            os.getenv('NOTION_RAW_MATCH_FEED_DB_ID')
        )
        
        if not self.database_id:
            logger.warning("⚠️ Raw Match Feed database ID not set")
        
        logger.info("📥 Raw Match Feed Updater initialized")
    
    def transform_itf_match(self, match: Any) -> Dict[str, Any]:
        """
        Transform ITFMatch object to Raw Match Feed properties
        
        Args:
            match: ITFMatch dataclass object
            
        Returns:
            Dictionary of Notion properties
        """
        # Generate match ID if not present
        match_id = getattr(match, 'match_id', None)
        if not match_id:
            match_id = f"itf_{hash(f'{match.player1}_{match.player2}_{match.tournament}') % 10000000}"
        
        # Map tournament tier
        tier = getattr(match, 'tournament_tier', '')
        if tier:
            # Ensure format: "ITF W15", "ITF W25", etc.
            if not tier.startswith('ITF'):
                tier = f"ITF {tier}"
        else:
            tier = None
        
        # Map surface
        surface = getattr(match, 'surface', None)
        if surface:
            surface_mapping = {
                'hard': 'Hard',
                'clay': 'Clay',
                'grass': 'Grass',
                'carpet': 'Carpet',
                'indoor': 'Hard',
                'indoor hard': 'Hard',
                'outdoor hard': 'Hard',
            }
            surface = surface_mapping.get(surface.lower(), surface.title())
        
        # Map match status
        match_status = getattr(match, 'match_status', 'not_started')
        status_mapping = {
            'not_started': 'Upcoming',
            'scheduled': 'Upcoming',
            'upcoming': 'Upcoming',
            'live': 'Live',
            'finished': 'Completed',
            'completed': 'Completed',
            'postponed': 'Postponed',
            'cancelled': 'Cancelled',
        }
        notion_status = status_mapping.get(match_status.lower(), 'Upcoming')
        
        # Determine data quality
        quality = "Complete"
        if not getattr(match, 'player1', None) or not getattr(match, 'player2', None):
            quality = "Missing Data"
        elif not getattr(match, 'tournament_tier', None):
            quality = "Partial"
        elif not getattr(match, 'player1_odds', None) or not getattr(match, 'player2_odds', None):
            quality = "Partial"
        
        # Build properties
        properties = {
            "Match ID": {
                "title": [{"text": {"content": match_id}}]
            },
            "Player A Name": {
                "rich_text": [{"text": {"content": getattr(match, 'player1', '')}}]
            },
            "Player B Name": {
                "rich_text": [{"text": {"content": getattr(match, 'player2', '')}}]
            },
            "Tournament": {
                "rich_text": [{"text": {"content": getattr(match, 'tournament', 'Unknown Tournament')}}]
            },
            "Match Status": {
                "select": {"name": notion_status}
            },
            "Data Source": {
                "select": {"name": "FlashScore"}
            },
            "Raw Data Quality": {
                "select": {"name": quality}
            },
            "AI Processed": {
                "checkbox": False
            }
        }
        
        # Add optional fields
        if tier:
            properties["Tournament Tier"] = {
                "select": {"name": tier}
            }
        
        if surface:
            properties["Surface"] = {
                "select": {"name": surface}
            }
        
        round_name = getattr(match, 'round', None)
        if round_name:
            properties["Round"] = {
                "select": {"name": round_name}
            }
        
        # Add odds
        player1_odds = getattr(match, 'player1_odds', None)
        if player1_odds:
            properties["Player A Odds"] = {
                "number": float(player1_odds)
            }
        
        player2_odds = getattr(match, 'player2_odds', None)
        if player2_odds:
            properties["Player B Odds"] = {
                "number": float(player2_odds)
            }
        
        # Add match date
        scheduled_time = getattr(match, 'scheduled_time', None)
        if scheduled_time:
            if isinstance(scheduled_time, datetime):
                properties["Match Date"] = {
                    "date": {"start": scheduled_time.isoformat()}
                }
            elif isinstance(scheduled_time, str):
                properties["Match Date"] = {
                    "date": {"start": scheduled_time}
                }
        
        # Add scraped at
        scraped_at = getattr(match, 'scraped_at', datetime.now())
        if isinstance(scraped_at, datetime):
            properties["Scraped At"] = {
                "date": {"start": scraped_at.isoformat()}
            }
        else:
            properties["Scraped At"] = {
                "date": {"start": datetime.now().isoformat()}
            }
        
        return properties
    
    def transform_betexplorer_match(self, match: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform BetExplorer match dictionary to Raw Match Feed properties
        
        Args:
            match: Match dictionary from BetExplorer scraper
            
        Returns:
            Dictionary of Notion properties
        """
        # Generate match ID
        match_id = match.get('match_id', f"betexplorer_{hash(str(match)) % 10000000}")
        
        # Map tournament tier
        tier = match.get('tier', '')
        if tier:
            if not tier.startswith('ITF'):
                tier = f"ITF {tier}"
        else:
            tier = None
        
        # Map surface
        surface = match.get('surface', None)
        if surface:
            surface_mapping = {
                'hard': 'Hard',
                'clay': 'Clay',
                'grass': 'Grass',
                'carpet': 'Carpet',
            }
            surface = surface_mapping.get(surface.lower(), surface.title())
        
        # Determine data quality
        quality = "Complete"
        if not match.get('player1') or not match.get('player2'):
            quality = "Missing Data"
        elif not match.get('tier'):
            quality = "Partial"
        elif not match.get('best_odds_p1') or not match.get('best_odds_p2'):
            quality = "Partial"
        
        # Build properties
        properties = {
            "Match ID": {
                "title": [{"text": {"content": match_id}}]
            },
            "Player A Name": {
                "rich_text": [{"text": {"content": match.get('player1', '')}}]
            },
            "Player B Name": {
                "rich_text": [{"text": {"content": match.get('player2', '')}}]
            },
            "Tournament": {
                "rich_text": [{"text": {"content": match.get('tournament', 'Unknown Tournament')}}]
            },
            "Match Status": {
                "select": {"name": "Upcoming"}
            },
            "Data Source": {
                "select": {"name": match.get('data_source', 'BetExplorer')}
            },
            "Raw Data Quality": {
                "select": {"name": quality}
            },
            "AI Processed": {
                "checkbox": False
            }
        }
        
        # Add optional fields
        if tier:
            properties["Tournament Tier"] = {
                "select": {"name": tier}
            }
        
        if surface:
            properties["Surface"] = {
                "select": {"name": surface}
            }
        
        # Add odds (BetExplorer has best odds from multiple bookmakers)
        if match.get('best_odds_p1'):
            properties["Player A Odds"] = {
                "number": float(match['best_odds_p1'])
            }
            properties["Best Odds A"] = {
                "number": float(match['best_odds_p1'])
            }
        
        if match.get('best_odds_p2'):
            properties["Player B Odds"] = {
                "number": float(match['best_odds_p2'])
            }
            properties["Best Odds B"] = {
                "number": float(match['best_odds_p2'])
            }
        
        # Add bookmaker
        bookmaker = match.get('bookmaker_p1') or match.get('bookmaker_p2')
        if bookmaker:
            properties["Bookmaker"] = {
                "select": {"name": bookmaker}
            }
        
        # Add match date
        match_time = match.get('match_time')
        if match_time:
            if isinstance(match_time, datetime):
                properties["Match Date"] = {
                    "date": {"start": match_time.isoformat()}
                }
            elif isinstance(match_time, str):
                try:
                    # Try to parse
                    dt = datetime.fromisoformat(match_time)
                    properties["Match Date"] = {
                        "date": {"start": dt.isoformat()}
                    }
                except:
                    properties["Match Date"] = {
                        "date": {"start": match_time}
                    }
        
        # Add scraped at
        scraped_at = match.get('scraped_at', datetime.now().isoformat())
        if isinstance(scraped_at, str):
            properties["Scraped At"] = {
                "date": {"start": scraped_at}
            }
        else:
            properties["Scraped At"] = {
                "date": {"start": datetime.now().isoformat()}
            }
        
        return properties
    
    def check_duplicate(self, match_id: str) -> bool:
        """
        Check if match already exists in Raw Match Feed DB
        
        Args:
            match_id: Match identifier
            
        Returns:
            True if duplicate exists
        """
        if not self.client or not self.database_id:
            return False
        
        try:
            response = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Match ID",
                    "title": {
                        "equals": match_id
                    }
                }
            )
            
            return len(response.get("results", [])) > 0
            
        except Exception as e:
            logger.error(f"❌ Error checking duplicate: {e}")
            return False
    
    def create_match(self, match: Union[Any, Dict[str, Any]], match_type: str = "itf") -> Optional[str]:
        """
        Create match in Raw Match Feed DB
        
        Args:
            match: ITFMatch object or BetExplorer match dictionary
            match_type: "itf" or "betexplorer"
            
        Returns:
            Notion page ID if successful, None otherwise
        """
        if not self.client or not self.database_id:
            logger.error("❌ Notion client or database ID not available")
            return None
        
        try:
            # Transform match to properties
            if match_type == "itf":
                properties = self.transform_itf_match(match)
                match_id = properties["Match ID"]["title"][0]["text"]["content"]
            elif match_type == "betexplorer":
                properties = self.transform_betexplorer_match(match)
                match_id = properties["Match ID"]["title"][0]["text"]["content"]
            else:
                logger.error(f"❌ Unknown match type: {match_type}")
                return None
            
            # Check for duplicates
            if self.check_duplicate(match_id):
                logger.debug(f"⏭️ Skipping duplicate match: {match_id}")
                return None
            
            # Create page
            page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            page_id = page['id']
            logger.info(f"✅ Created match in Raw Match Feed: {match_id} ({page_id[:8]}...)")
            
            return page_id
            
        except Exception as e:
            logger.error(f"❌ Error creating match: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    def create_matches_batch(self, matches: list, match_type: str = "itf") -> Dict[str, Any]:
        """
        Create multiple matches in batch
        
        Args:
            matches: List of ITFMatch objects or BetExplorer match dictionaries
            match_type: "itf" or "betexplorer"
            
        Returns:
            Dictionary with results: created, duplicates, errors
        """
        results = {
            'created': 0,
            'duplicates': 0,
            'errors': 0,
            'page_ids': []
        }
        
        for match in matches:
            try:
                # Check duplicate first
                if match_type == "itf":
                    match_id = getattr(match, 'match_id', None) or f"itf_{hash(f'{match.player1}_{match.player2}_{match.tournament}') % 10000000}"
                else:
                    match_id = match.get('match_id', f"betexplorer_{hash(str(match)) % 10000000}")
                
                if self.check_duplicate(match_id):
                    results['duplicates'] += 1
                    continue
                
                # Create match
                page_id = self.create_match(match, match_type)
                if page_id:
                    results['created'] += 1
                    results['page_ids'].append(page_id)
                else:
                    results['errors'] += 1
                    
            except Exception as e:
                logger.error(f"❌ Error processing match in batch: {e}")
                results['errors'] += 1
        
        logger.info(f"📊 Batch results: {results['created']} created, {results['duplicates']} duplicates, {results['errors']} errors")
        
        return results


def main():
    """Test Raw Match Feed Updater"""
    print("📥 RAW MATCH FEED UPDATER TEST")
    print("=" * 50)
    
    updater = RawMatchFeedUpdater()
    
    if not updater.client:
        print("❌ Notion client not available")
        print("\n💡 Setup:")
        print("1. Install: pip install notion-client")
        print("2. Get Notion API key: https://www.notion.so/my-integrations")
        print("3. Add to telegram_secrets.env: NOTION_TOKEN=your_key")
        return
    
    if not updater.database_id:
        print("⚠️ Raw Match Feed database ID not set")
        print("\n💡 Get database ID:")
        print("1. Open your Raw Match Feed database in Notion")
        print("2. Copy database ID from URL")
        print("3. Add to telegram_secrets.env: RAW_MATCH_FEED_DB_ID=your_db_id")
        return
    
    print(f"✅ Connected to database: {updater.database_id[:8]}...")
    print("\n✅ Raw Match Feed Updater ready!")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()


