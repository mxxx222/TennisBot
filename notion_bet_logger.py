#!/usr/bin/env python3
"""
📝 NOTION BET LOGGER - Automaattinen betin kirjaus
===================================================

Kirjaa ITF Women -betit suoraan Notion Bets-tietokantaan.
Integroitu check_itf_matches.py -skriptiin.

Käyttö:
    from notion_bet_logger import NotionBetLogger
    
    logger = NotionBetLogger()
    logger.log_bet(
        tournament="ITF W15 Sharm ElSheikh 20 Women",
        player1="Maria Garcia",
        player2="Anna Smith",
        selected_player="Maria Garcia",
        odds=1.75,
        stake=10.00,
        player1_ranking=245,
        player2_ranking=312,
        surface="Hard",
        bookmaker="Bet365"
    )
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), 'telegram_secrets.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

# Notion API
try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    print("⚠️ notion-client not installed. Install with: pip install notion-client")

logger = logging.getLogger(__name__)


class NotionBetLogger:
    """Notion bet logger - kirjaa betit Bets-tietokantaan"""
    
    def __init__(self, database_id: Optional[str] = None):
        """
        Initialize Notion bet logger
        
        Args:
            database_id: Notion Bets database ID (optional, can be set via env or config)
        """
        # Try to use existing NotionMCPIntegration first
        self.notion_mcp = None
        try:
            import sys
            src_path = Path(__file__).parent / 'src'
            if src_path.exists():
                sys.path.insert(0, str(src_path))
            from notion_mcp_integration import NotionMCPIntegration
            # Initialize without token - it will load from env/config
            self.notion_mcp = NotionMCPIntegration()
            # Initialize client if token available (try multiple sources)
            token = (
                self.notion_mcp.notion_token or
                os.getenv('NOTION_TOKEN') or
                os.getenv('NOTION_API_KEY') or
                self._load_from_config()
            )
            if token:
                self.notion_mcp.initialize_notion_client(token)
            if self.notion_mcp.notion_client:
                self.client = self.notion_mcp.notion_client
                logger.info("✅ Using existing NotionMCPIntegration")
                # Try to get database ID from MCP integration
                if not database_id:
                    self.database_id = self._get_database_id_from_mcp()
                else:
                    self.database_id = database_id
                return
        except ImportError as e:
            logger.debug(f"NotionMCPIntegration not available: {e}")
        except Exception as e:
            logger.debug(f"Could not use NotionMCPIntegration: {e}")
        
        # Fallback to direct client initialization
        # Try multiple sources for Notion token
        self.notion_token = (
            os.getenv('NOTION_API_KEY') or 
            os.getenv('NOTION_TOKEN') or
            self._load_from_config()
        )
        
        # Try multiple sources for database ID
        self.database_id = (
            database_id or 
            os.getenv('NOTION_BETS_DATABASE_ID') or
            self._load_database_id_from_config()
        )
        
        if not NOTION_AVAILABLE:
            logger.warning("⚠️ notion-client not available")
            self.client = None
            return
        
        if not self.notion_token:
            logger.warning("⚠️ Notion token not found")
            logger.info("💡 Try: NOTION_API_KEY, NOTION_TOKEN, or config/notion_config.json")
            self.client = None
            return
        
        try:
            self.client = Client(auth=self.notion_token)
            logger.info("✅ Notion Bet Logger initialized (direct client)")
        except Exception as e:
            logger.error(f"❌ Error initializing Notion client: {e}")
            self.client = None
    
    def _get_database_id_from_mcp(self) -> Optional[str]:
        """Hae database ID NotionMCPIntegration:sta"""
        if not self.notion_mcp:
            return None
        
        # Check if MCP has database IDs stored
        if hasattr(self.notion_mcp, 'database_ids') and self.notion_mcp.database_ids:
            # Try to find Bets database
            return (
                self.notion_mcp.database_ids.get('bets') or
                self.notion_mcp.database_ids.get('Bets') or
                self.notion_mcp.database_ids.get('tennis') or
                self.notion_mcp.database_ids.get('Tennis')
            )
        return None
    
    def _load_from_config(self) -> Optional[str]:
        """Lataa Notion token config-tiedostosta"""
        try:
            config_path = Path(__file__).parent / 'config' / 'notion_config.json'
            if config_path.exists():
                import json
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    token = config.get('notion_token') or config.get('token')
                    if token and token != "PASTE_YOUR_TOKEN_HERE":
                        logger.info("✅ Loaded Notion token from config/notion_config.json")
                        return token
        except Exception as e:
            logger.debug(f"Could not load from config: {e}")
        return None
    
    def _load_database_id_from_config(self) -> Optional[str]:
        """Lataa Bets database ID config-tiedostosta"""
        try:
            config_path = Path(__file__).parent / 'config' / 'notion_config.json'
            if config_path.exists():
                import json
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    databases = config.get('databases', {})
                    # Try different database name variations
                    db_id = (
                        databases.get('bets') or
                        databases.get('Bets') or
                        databases.get('BETS') or
                        databases.get('tennis_bets') or
                        config.get('bets_database_id')
                    )
                    if db_id:
                        logger.info("✅ Loaded Bets database ID from config/notion_config.json")
                        return db_id
        except Exception as e:
            logger.debug(f"Could not load database ID from config: {e}")
        return None
    
    def log_bet(self,
                tournament: str,
                player1: str,
                player2: str,
                selected_player: str,
                odds: float,
                stake: float,
                player1_ranking: Optional[int] = None,
                player2_ranking: Optional[int] = None,
                surface: Optional[str] = None,
                bookmaker: str = "Bet365",
                notes: Optional[str] = None) -> Optional[str]:
        """
        Kirjaa betin Notioniin
        
        Args:
            tournament: Turnaus (esim. "ITF W15 Sharm ElSheikh 20 Women")
            player1: Pelaaja 1 nimi
            player2: Pelaaja 2 nimi
            selected_player: Valittu pelaaja (player1 tai player2)
            odds: Kertoimet
            stake: Panos ($)
            player1_ranking: Pelaaja 1 ranking (optional)
            player2_ranking: Pelaaja 2 ranking (optional)
            surface: Kenttäpinta (Hard/Clay/Grass, optional)
            bookmaker: Vedonlyöntisivusto (default: Bet365)
            notes: Lisähuomiot (optional)
            
        Returns:
            Notion page ID jos onnistui, None jos epäonnistui
        """
        if not self.client:
            logger.warning("⚠️ Notion client not available - bet not logged")
            return None
        
        if not self.database_id:
            logger.warning("⚠️ NOTION_BETS_DATABASE_ID not set - bet not logged")
            logger.info("💡 Set NOTION_BETS_DATABASE_ID in telegram_secrets.env")
            return None
        
        try:
            # Determine tournament level
            tournament_level = self._get_tournament_level(tournament)
            
            # Create match title
            match_title = f"{player1} vs {player2}"
            
            # Prepare properties according to BETTING_LOG_TEMPLATE.md
            properties = {
                "Date & Time": {
                    "date": {
                        "start": datetime.now().isoformat()
                    }
                },
                "Tournament": {
                    "rich_text": [{"text": {"content": tournament}}]
                },
                "Player 1": {
                    "rich_text": [{"text": {"content": player1}}]
                },
                "Player 2": {
                    "rich_text": [{"text": {"content": player2}}]
                },
                "Selected Player": {
                    "select": {
                        "name": selected_player
                    }
                },
                "Odds": {
                    "number": odds
                },
                "Stake": {
                    "number": stake
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
                        "name": bookmaker
                    }
                }
            }
            
            # Add optional fields
            if player1_ranking:
                properties["Player 1 Ranking"] = {
                    "number": player1_ranking
                }
            
            if player2_ranking:
                properties["Player 2 Ranking"] = {
                    "number": player2_ranking
                }
            
            if surface:
                properties["Surface"] = {
                    "select": {
                        "name": surface
                    }
                }
            
            if notes:
                properties["Notes"] = {
                    "rich_text": [{"text": {"content": notes}}]
                }
            
            # Create page in Notion
            page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            logger.info(f"✅ Bet logged to Notion: {match_title}")
            logger.info(f"📄 Page ID: {page['id']}")
            
            return page['id']
            
        except Exception as e:
            logger.error(f"❌ Error logging bet to Notion: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_tournament_level(self, tournament: str) -> str:
        """Hae turnauksen taso"""
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
        elif 'W75' in tournament_upper:
            return 'ITF W75'
        elif 'W80' in tournament_upper:
            return 'ITF W80'
        elif 'W100' in tournament_upper:
            return 'ITF W100'
        else:
            return 'ITF Challenger'
    
    def update_bet_result(self, page_id: str, result: str, profit_loss: Optional[float] = None):
        """
        Päivitä betin tulos
        
        Args:
            page_id: Notion page ID
            result: "Win" tai "Loss"
            profit_loss: Voitto/tappio ($)
        """
        if not self.client:
            return
        
        try:
            properties = {
                "Result": {
                    "select": {
                        "name": result
                    }
                }
            }
            
            if profit_loss is not None:
                properties["Profit/Loss"] = {
                    "number": profit_loss
                }
            
            self.client.pages.update(
                page_id=page_id,
                properties=properties
            )
            
            logger.info(f"✅ Bet result updated: {result}")
            
        except Exception as e:
            logger.error(f"❌ Error updating bet result: {e}")


def test_logger():
    """Testaa bet logger"""
    print("\n" + "="*80)
    print("🧪 TESTING NOTION BET LOGGER")
    print("="*80)
    
    logger_instance = NotionBetLogger()
    
    if not logger_instance.client:
        print("❌ Notion client not available")
        print("\n💡 Setup:")
        print("1. Install: pip install notion-client")
        print("2. Get Notion API key: https://www.notion.so/my-integrations")
        print("3. Add to telegram_secrets.env: NOTION_API_KEY=your_key")
        print("4. Get Bets database ID from Notion")
        print("5. Add to telegram_secrets.env: NOTION_BETS_DATABASE_ID=your_db_id")
        return
    
    if not logger_instance.database_id:
        print("⚠️ NOTION_BETS_DATABASE_ID not set")
        print("\n💡 Get database ID:")
        print("1. Open your Bets database in Notion")
        print("2. Copy database ID from URL")
        print("3. Add to telegram_secrets.env: NOTION_BETS_DATABASE_ID=your_db_id")
        return
    
    # Test bet
    print("\n📝 Testing bet log...")
    page_id = logger_instance.log_bet(
        tournament="ITF W15 Sharm ElSheikh 20 Women",
        player1="Maria Garcia",
        player2="Anna Smith",
        selected_player="Maria Garcia",
        odds=1.75,
        stake=10.00,
        player1_ranking=245,
        player2_ranking=312,
        surface="Hard",
        bookmaker="Bet365",
        notes="Test bet from notion_bet_logger.py"
    )
    
    if page_id:
        print(f"✅ Test bet logged successfully!")
        print(f"📄 Page ID: {page_id}")
        print(f"🔗 View in Notion: https://www.notion.so/{page_id.replace('-', '')}")
    else:
        print("❌ Failed to log test bet")


if __name__ == "__main__":
    test_logger()

