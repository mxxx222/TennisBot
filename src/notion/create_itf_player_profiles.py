#!/usr/bin/env python3
"""
👥 CREATE ITF PLAYER PROFILES DATABASE
======================================

Creates new Notion database for ITF Player Profiles with:
- Player Name (Title)
- Surface Win % Hard/Clay/Grass (Number)
- Avg Games Per Set (Number)
- Retirement Rate (Number)
- Recent Form (Text)
- WTA Ranking (Number)
- ITF Ranking (Number)
- Relation → Link to Tennis Prematch database
"""

import os
import logging
from typing import Optional, Dict, Any
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


class ITFPlayerProfilesCreator:
    """Creates ITF Player Profiles Notion database"""
    
    def __init__(self, parent_page_id: Optional[str] = None):
        """
        Initialize ITF Player Profiles Creator
        
        Args:
            parent_page_id: Notion page ID where database will be created (optional)
        """
        # Try to get Notion token
        self.notion_token = (
            os.getenv('NOTION_API_KEY') or
            os.getenv('NOTION_TOKEN') or
            self._load_from_config()
        )
        
        self.parent_page_id = parent_page_id or os.getenv('NOTION_PARENT_PAGE_ID')
        
        if not NOTION_AVAILABLE:
            logger.warning("⚠️ notion-client not available")
            self.client = None
            return
        
        if not self.notion_token:
            logger.warning("⚠️ Notion token not found")
            self.client = None
            return
        
        try:
            self.client = Client(auth=self.notion_token)
            logger.info("✅ ITF Player Profiles Creator initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing Notion client: {e}")
            self.client = None
    
    def _load_from_config(self) -> Optional[str]:
        """Load Notion token from config"""
        try:
            config_path = Path(__file__).parent.parent.parent / 'config' / 'notion_config.json'
            if config_path.exists():
                import json
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    token = config.get('notion_token') or config.get('token')
                    if token and token != "PASTE_YOUR_TOKEN_HERE":
                        return token
        except Exception as e:
            logger.debug(f"Could not load from config: {e}")
        return None
    
    def create_database(self, database_title: str = "ITF Player Profiles") -> Optional[str]:
        """
        Create ITF Player Profiles database in Notion
        
        Args:
            database_title: Title for the database
            
        Returns:
            Database ID if successful, None otherwise
        """
        if not self.client:
            logger.error("❌ Notion client not available")
            return None
        
        if not self.parent_page_id:
            logger.error("❌ Parent page ID not set")
            logger.info("💡 Set NOTION_PARENT_PAGE_ID in environment or config")
            return None
        
        try:
            # Create database with all properties
            database = self.client.databases.create(
                parent={
                    "type": "page_id",
                    "page_id": self.parent_page_id
                },
                title=[
                    {
                        "type": "text",
                        "text": {
                            "content": database_title
                        }
                    }
                ],
                properties={
                    "Player Name": {
                        "title": {}
                    },
                    "Surface Win % Hard": {
                        "number": {
                            "format": "percent"
                        }
                    },
                    "Surface Win % Clay": {
                        "number": {
                            "format": "percent"
                        }
                    },
                    "Surface Win % Grass": {
                        "number": {
                            "format": "percent"
                        }
                    },
                    "Avg Games Per Set": {
                        "number": {
                            "format": "number"
                        }
                    },
                    "Retirement Rate": {
                        "number": {
                            "format": "percent"
                        }
                    },
                    "Recent Form": {
                        "rich_text": {}
                    },
                    "WTA Ranking": {
                        "number": {
                            "format": "number"
                        }
                    },
                    "ITF Ranking": {
                        "number": {
                            "format": "number"
                        }
                    },
                    "Tennis Prematch Matches": {
                        "relation": {
                            "database_id": os.getenv('NOTION_TENNIS_PREMATCH_DB_ID', ''),
                            "type": "single_property",
                            "single_property": {}
                        }
                    } if os.getenv('NOTION_TENNIS_PREMATCH_DB_ID') else None,
                }
            )
            
            # Remove None properties
            if database.get('properties', {}).get('Tennis Prematch Matches') is None:
                # Update database to remove relation if parent DB not set
                self.client.databases.update(
                    database_id=database['id'],
                    properties={
                        "Tennis Prematch Matches": None
                    }
                )
            
            database_id = database['id']
            logger.info(f"✅ Created ITF Player Profiles database: {database_id}")
            
            return database_id
            
        except Exception as e:
            logger.error(f"❌ Error creating database: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def create_player_page(self, database_id: str, player_data: Dict[str, Any]) -> Optional[str]:
        """
        Create player page in database
        
        Args:
            database_id: Database ID
            player_data: Player data dictionary
            
        Returns:
            Page ID if successful, None otherwise
        """
        if not self.client:
            return None
        
        try:
            properties = {
                "Player Name": {
                    "title": [
                        {
                            "text": {
                                "content": player_data.get('name', 'Unknown Player')
                            }
                        }
                    ]
                }
            }
            
            # Add optional number fields
            if 'surface_win_hard' in player_data:
                properties["Surface Win % Hard"] = {
                    "number": player_data['surface_win_hard']
                }
            
            if 'surface_win_clay' in player_data:
                properties["Surface Win % Clay"] = {
                    "number": player_data['surface_win_clay']
                }
            
            if 'surface_win_grass' in player_data:
                properties["Surface Win % Grass"] = {
                    "number": player_data['surface_win_grass']
                }
            
            if 'avg_games_per_set' in player_data:
                properties["Avg Games Per Set"] = {
                    "number": player_data['avg_games_per_set']
                }
            
            if 'retirement_rate' in player_data:
                properties["Retirement Rate"] = {
                    "number": player_data['retirement_rate']
                }
            
            if 'recent_form' in player_data:
                properties["Recent Form"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": player_data['recent_form']
                            }
                        }
                    ]
                }
            
            if 'wta_ranking' in player_data:
                properties["WTA Ranking"] = {
                    "number": player_data['wta_ranking']
                }
            
            if 'itf_ranking' in player_data:
                properties["ITF Ranking"] = {
                    "number": player_data['itf_ranking']
                }
            
            page = self.client.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )
            
            logger.info(f"✅ Created player page: {player_data.get('name')} ({page['id'][:8]}...)")
            return page['id']
            
        except Exception as e:
            logger.error(f"❌ Error creating player page: {e}")
            return None


def main():
    """Test ITF Player Profiles Creator"""
    print("👥 ITF PLAYER PROFILES CREATOR TEST")
    print("=" * 50)
    
    creator = ITFPlayerProfilesCreator()
    
    if not creator.client:
        print("❌ Notion client not available")
        print("\n💡 Setup:")
        print("1. Install: pip install notion-client")
        print("2. Get Notion API key: https://www.notion.so/my-integrations")
        print("3. Add to telegram_secrets.env: NOTION_API_KEY=your_key")
        print("4. Add parent page ID: NOTION_PARENT_PAGE_ID=your_page_id")
        return
    
    if not creator.parent_page_id:
        print("⚠️ Parent page ID not set")
        print("\n💡 Get parent page ID:")
        print("1. Create or open a Notion page where you want the database")
        print("2. Copy page ID from URL")
        print("3. Add to telegram_secrets.env: NOTION_PARENT_PAGE_ID=your_page_id")
        return
    
    print(f"✅ Connected to Notion")
    print(f"✅ Parent page: {creator.parent_page_id[:8]}...")
    print("\n🚀 Creating database...")
    
    database_id = creator.create_database()
    
    if database_id:
        print(f"\n✅ Database created successfully!")
        print(f"   Database ID: {database_id}")
        print(f"   View in Notion: https://www.notion.so/{database_id.replace('-', '')}")
        
        # Test creating a sample player
        print("\n🧪 Creating sample player...")
        sample_player = {
            'name': 'Test Player',
            'surface_win_hard': 0.65,
            'surface_win_clay': 0.55,
            'surface_win_grass': 0.60,
            'avg_games_per_set': 10.5,
            'retirement_rate': 0.02,
            'recent_form': 'W-L-W-W-L',
            'wta_ranking': 250,
            'itf_ranking': 150,
        }
        
        page_id = creator.create_player_page(database_id, sample_player)
        if page_id:
            print(f"✅ Sample player created: {page_id[:8]}...")
    else:
        print("\n❌ Failed to create database")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()

