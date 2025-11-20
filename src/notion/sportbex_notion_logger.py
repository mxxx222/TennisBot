#!/usr/bin/env python3
"""
Sportbex Notion Logger
======================

Logs tennis candidates from Sportbex API to Notion master database.
Uses Status field for workflow: Review → Approved → Pending → Won/Lost

Extends existing notion_bet_logger.py pattern.
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / 'telegram_secrets.env'
if env_path.exists():
    load_dotenv(env_path)

# Notion API
try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    print("⚠️ notion-client not installed. Install with: pip install notion-client")

# Import parent class
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from notion_bet_logger import NotionBetLogger

from src.pipelines.sportbex_filter import TennisCandidate

logger = logging.getLogger(__name__)


class SportbexNotionLogger(NotionBetLogger):
    """Notion logger for Sportbex candidates"""
    
    def __init__(self, database_id: Optional[str] = None):
        """
        Initialize Sportbex Notion logger
        
        Args:
            database_id: Notion master database ID (optional, can be set via env or config)
        """
        super().__init__(database_id)
        
        # Try to get master database ID if not provided
        # Use existing NOTION_BETS_DATABASE_ID from telegram_secrets.env (master database)
        if not self.database_id:
            self.database_id = (
                os.getenv('NOTION_MASTER_DB_ID') or
                os.getenv('NOTION_BETS_DATABASE_ID') or  # Master database (from telegram_secrets.env)
                self._load_master_db_id_from_config()
            )
        
        logger.info("📊 Sportbex Notion Logger initialized")
    
    def _load_master_db_id_from_config(self) -> Optional[str]:
        """Load master database ID from config"""
        try:
            config_path = Path(__file__).parent.parent.parent / 'config' / 'notion_config.json'
            if config_path.exists():
                import json
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    databases = config.get('databases', {})
                    # Try different database name variations
                    db_id = (
                        databases.get('master') or
                        databases.get('Master') or
                        databases.get('bets') or
                        databases.get('Bets') or
                        databases.get('BETS') or
                        config.get('master_database_id') or
                        config.get('bets_database_id')
                    )
                    if db_id:
                        logger.info("✅ Loaded master database ID from config")
                        return db_id
        except Exception as e:
            logger.debug(f"Could not load database ID from config: {e}")
        return None
    
    def log_candidate(self, candidate: TennisCandidate) -> Optional[str]:
        """
        Log candidate to Notion with Status="Review"
        
        Args:
            candidate: TennisCandidate object
            
        Returns:
            Notion page ID if successful, None otherwise
        """
        if not self.client:
            logger.warning("⚠️ Notion client not available - candidate not logged")
            return None
        
        if not self.database_id:
            logger.warning("⚠️ NOTION_MASTER_DB_ID not set - candidate not logged")
            logger.info("💡 Set NOTION_MASTER_DB_ID in telegram_secrets.env")
            return None
        
        try:
            match = candidate.match
            
            # Check for duplicates (by match ID or player names + date)
            if self._is_duplicate(match):
                logger.debug(f"⏭️ Skipping duplicate match: {match.player1} vs {match.player2}")
                return None
            
            # Determine tournament level
            tournament_level = self._get_tournament_level(match.tournament, match.tournament_tier)
            
            # Create match title
            match_title = f"{match.player1} vs {match.player2}"
            
            # Prepare properties according to BETTING_LOG_TEMPLATE.md
            # Status field: Review (default for candidates)
            properties = {
                "Date & Time": {
                    "date": {
                        "start": (match.commence_time or datetime.now()).isoformat()
                    }
                },
                "Tournament": {
                    "rich_text": [{"text": {"content": match.tournament}}]
                },
                "Player 1": {
                    "rich_text": [{"text": {"content": match.player1}}]
                },
                "Player 2": {
                    "rich_text": [{"text": {"content": match.player2}}]
                },
                "Selected Player": {
                    "select": {
                        "name": candidate.selected_player
                    }
                },
                "Odds": {
                    "number": candidate.selected_odds
                },
                "Bet Type": {
                    "select": {
                        "name": "SINGLE"
                    }
                },
                "Result": {
                    "select": {
                        "name": "Pending"
                    }
                },
                "Tournament Level": {
                    "select": {
                        "name": tournament_level
                    }
                },
                "Bookmaker": {
                    "select": {
                        "name": "Sportbex"
                    }
                }
            }
            
            # Add Status field (Review for candidates)
            # Note: Status field may need to be created manually in Notion if it doesn't exist
            # Options: Review, Approved, Pending, Won, Lost
            try:
                properties["Status"] = {
                    "select": {
                        "name": "Review"
                    }
                }
            except Exception as e:
                logger.debug(f"Status field may not exist in database: {e}")
            
            # Add Player 1 Odds if available
            if match.player1_odds:
                properties["Player 1 Ranking"] = {
                    "number": match.player1_ranking
                } if match.player1_ranking else {}
                # Note: We'll add odds in a separate field if the schema supports it
            
            # Add Player 2 Odds if available
            if match.player2_odds:
                properties["Player 2 Ranking"] = {
                    "number": match.player2_ranking
                } if match.player2_ranking else {}
            
            # Add Surface if available
            if match.surface:
                properties["Surface"] = {
                    "select": {
                        "name": match.surface.title()
                    }
                }
            
            # Add Notes field (empty, for AI analysis later)
            properties["Notes"] = {
                "rich_text": [{"text": {"content": f"Candidate from Sportbex API. {candidate.filter_reason}"}}]
            }
            
            # Add Stake field (empty for now, will be filled when approved)
            # Note: Stake will be set manually when bet is placed
            
            # Create page in Notion
            page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            logger.info(f"✅ Candidate logged to Notion: {match_title} (Status: Review)")
            logger.info(f"📄 Page ID: {page['id']}")
            
            return page['id']
            
        except Exception as e:
            logger.error(f"❌ Error logging candidate to Notion: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def log_candidates_batch(self, candidates: List[TennisCandidate]) -> Dict[str, Any]:
        """
        Log multiple candidates to Notion
        
        Args:
            candidates: List of TennisCandidate objects
            
        Returns:
            Dictionary with results
        """
        results = {
            'created': 0,
            'duplicates': 0,
            'errors': 0,
            'page_ids': []
        }
        
        for candidate in candidates:
            page_id = self.log_candidate(candidate)
            
            if page_id:
                results['created'] += 1
                results['page_ids'].append(page_id)
            elif page_id is None and self.client:
                # Likely a duplicate
                results['duplicates'] += 1
            else:
                results['errors'] += 1
        
        logger.info(f"✅ Logged {results['created']} candidates, {results['duplicates']} duplicates, {results['errors']} errors")
        
        return results
    
    def _is_duplicate(self, match) -> bool:
        """
        Check if match already exists in Notion
        
        Args:
            match: SportbexMatch object
            
        Returns:
            True if duplicate exists
        """
        if not self.client or not self.database_id:
            return False
        
        try:
            # Query Notion database for existing matches
            # Check by player names and date
            query = {
                "filter": {
                    "and": [
                        {
                            "property": "Player 1",
                            "rich_text": {
                                "equals": match.player1
                            }
                        },
                        {
                            "property": "Player 2",
                            "rich_text": {
                                "equals": match.player2
                            }
                        }
                    ]
                }
            }
            
            results = self.client.databases.query(
                database_id=self.database_id,
                **query
            )
            
            # Check if any results match the date (within same day)
            if match.commence_time:
                match_date = match.commence_time.date()
                for page in results.get('results', []):
                    props = page.get('properties', {})
                    date_prop = props.get('Date & Time', {})
                    if date_prop.get('date'):
                        page_date_str = date_prop['date']['start']
                        page_date = datetime.fromisoformat(page_date_str.split('T')[0]).date()
                        if page_date == match_date:
                            return True
            
            return len(results.get('results', [])) > 0
            
        except Exception as e:
            logger.debug(f"Error checking duplicate: {e}")
            # If query fails, assume not duplicate (safer to create than skip)
            return False
    
    def _get_tournament_level(self, tournament: str, tournament_tier: Optional[str] = None) -> str:
        """Get tournament level for Notion"""
        if tournament_tier:
            if tournament_tier.startswith('W'):
                return f'ITF {tournament_tier}'
            elif 'CHALLENGER' in tournament_tier.upper():
                return 'ATP Challenger'
            return tournament_tier
        
        tournament_upper = tournament.upper()
        
        if 'W15' in tournament_upper:
            return 'ITF W15'
        elif 'W25' in tournament_upper:
            return 'ITF W25'
        elif 'W35' in tournament_upper:
            return 'ITF W35'
        elif 'W50' in tournament_upper:
            return 'ITF W50'
        elif 'W60' in tournament_upper:
            return 'ITF W60'
        elif 'W80' in tournament_upper:
            return 'ITF W80'
        elif 'W100' in tournament_upper:
            return 'ITF W100'
        elif 'CHALLENGER' in tournament_upper:
            return 'ATP Challenger'
        else:
            return 'ITF Challenger'
    
    def update_status(self, page_id: str, status: str) -> bool:
        """
        Update candidate status
        
        Args:
            page_id: Notion page ID
            status: New status (Review, Approved, Pending, Won, Lost)
            
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        valid_statuses = ['Review', 'Approved', 'Pending', 'Won', 'Lost']
        if status not in valid_statuses:
            logger.warning(f"Invalid status: {status}. Valid: {valid_statuses}")
            return False
        
        try:
            self.client.pages.update(
                page_id=page_id,
                properties={
                    "Status": {
                        "select": {
                            "name": status
                        }
                    }
                }
            )
            
            logger.info(f"✅ Updated status to: {status}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating status: {e}")
            return False


def test_logger():
    """Test Sportbex Notion logger"""
    print("\n" + "="*80)
    print("🧪 TESTING SPORTBEX NOTION LOGGER")
    print("="*80)
    
    logger_instance = SportbexNotionLogger()
    
    if not logger_instance.client:
        print("❌ Notion client not available")
        print("\n💡 Setup:")
        print("1. Install: pip install notion-client")
        print("2. Get Notion API key: https://www.notion.so/my-integrations")
        print("3. Add to telegram_secrets.env: NOTION_API_KEY=your_key")
        print("4. Add master database ID: NOTION_MASTER_DB_ID=your_db_id")
        return
    
    if not logger_instance.database_id:
        print("⚠️ NOTION_MASTER_DB_ID not set")
        print("\n💡 Get database ID:")
        print("1. Open your master database in Notion")
        print("2. Copy database ID from URL")
        print("3. Add to telegram_secrets.env: NOTION_MASTER_DB_ID=your_db_id")
        return
    
    # Create test candidate
    from src.scrapers.sportbex_client import SportbexMatch
    from src.pipelines.sportbex_filter import TennisCandidate
    
    test_match = SportbexMatch(
        match_id="test_1",
        tournament="ITF W15 Test Tournament",
        player1="Test Player A",
        player2="Test Player B",
        player1_odds=1.65,
        player2_odds=2.20,
        commence_time=datetime.now(),
        tournament_tier="W15"
    )
    
    test_candidate = TennisCandidate(
        match=test_match,
        selected_player="Test Player A",
        selected_odds=1.65,
        filter_reason="Test candidate"
    )
    
    print("\n📝 Testing candidate log...")
    page_id = logger_instance.log_candidate(test_candidate)
    
    if page_id:
        print(f"✅ Test candidate logged successfully!")
        print(f"📄 Page ID: {page_id}")
        print(f"🔗 View in Notion: https://www.notion.so/{page_id.replace('-', '')}")
    else:
        print("❌ Failed to log test candidate")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    test_logger()

