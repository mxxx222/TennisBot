#!/usr/bin/env python3
"""
📊 NOTION ITF DATABASE UPDATER
===============================

Adds new properties to existing Tennis Prematch database:
- Tournament Tier (Select: W15, W35, W50, W75, W100)
- Set 1 Deficit (Checkbox) - Flag if player lost first set badly
- Comeback % Historical (Number) - Historical comeback percentage per player

Extends existing NotionBetLogger functionality.
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

# Import existing NotionBetLogger
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from notion_bet_logger import NotionBetLogger

logger = logging.getLogger(__name__)


class ITFDatabaseUpdater(NotionBetLogger):
    """Extends NotionBetLogger to add ITF-specific properties to Tennis Prematch database"""
    
    def __init__(self, database_id: Optional[str] = None):
        """
        Initialize ITF Database Updater
        
        Args:
            database_id: Tennis Prematch database ID (optional, can be set via env or config)
        """
        super().__init__(database_id)
        
        # Try to get Tennis Prematch database ID
        if not self.database_id:
            self.database_id = (
                os.getenv('NOTION_TENNIS_PREMATCH_DB_ID') or
                os.getenv('NOTION_PREMATCH_DB_ID') or
                self._load_prematch_db_id_from_config()
            )
        
        logger.info("📊 ITF Database Updater initialized")
    
    def _load_prematch_db_id_from_config(self) -> Optional[str]:
        """Load Tennis Prematch database ID from config"""
        try:
            config_path = Path(__file__).parent.parent.parent / 'config' / 'notion_config.json'
            if config_path.exists():
                import json
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    databases = config.get('databases', {})
                    # Try different database name variations
                    db_id = (
                        databases.get('tennis_prematch') or
                        databases.get('Tennis Prematch') or
                        databases.get('prematch') or
                        databases.get('tennis') or
                        config.get('tennis_prematch_db_id')
                    )
                    if db_id:
                        logger.info("✅ Loaded Tennis Prematch database ID from config")
                        return db_id
        except Exception as e:
            logger.debug(f"Could not load database ID from config: {e}")
        return None
    
    def add_tournament_tier_property(self) -> bool:
        """
        Add Tournament Tier property to Tennis Prematch database
        
        Returns:
            True if successful
        """
        if not self.client or not self.database_id:
            logger.error("❌ Notion client or database ID not available")
            return False
        
        try:
            # Get current database schema
            database = self.client.databases.retrieve(database_id=self.database_id)
            
            # Check if property already exists
            properties = database.get('properties', {})
            if 'Tournament Tier' in properties:
                logger.info("✅ Tournament Tier property already exists")
                return True
            
            # Add Tournament Tier property (Select type)
            self.client.databases.update(
                database_id=self.database_id,
                properties={
                    'Tournament Tier': {
                        'select': {
                            'options': [
                                {'name': 'W15', 'color': 'blue'},
                                {'name': 'W25', 'color': 'green'},
                                {'name': 'W35', 'color': 'yellow'},
                                {'name': 'W50', 'color': 'orange'},
                                {'name': 'W60', 'color': 'red'},
                                {'name': 'W75', 'color': 'purple'},
                                {'name': 'W80', 'color': 'pink'},
                                {'name': 'W100', 'color': 'brown'},
                            ]
                        }
                    }
                }
            )
            
            logger.info("✅ Added Tournament Tier property to Tennis Prematch database")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error adding Tournament Tier property: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def add_set1_deficit_property(self) -> bool:
        """
        Add Set 1 Deficit property to Tennis Prematch database
        
        Returns:
            True if successful
        """
        if not self.client or not self.database_id:
            logger.error("❌ Notion client or database ID not available")
            return False
        
        try:
            # Get current database schema
            database = self.client.databases.retrieve(database_id=self.database_id)
            
            # Check if property already exists
            properties = database.get('properties', {})
            if 'Set 1 Deficit' in properties:
                logger.info("✅ Set 1 Deficit property already exists")
                return True
            
            # Add Set 1 Deficit property (Checkbox type)
            self.client.databases.update(
                database_id=self.database_id,
                properties={
                    'Set 1 Deficit': {
                        'checkbox': {}
                    }
                }
            )
            
            logger.info("✅ Added Set 1 Deficit property to Tennis Prematch database")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error adding Set 1 Deficit property: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def add_comeback_percent_property(self) -> bool:
        """
        Add Comeback % Historical property to Tennis Prematch database
        
        Returns:
            True if successful
        """
        if not self.client or not self.database_id:
            logger.error("❌ Notion client or database ID not available")
            return False
        
        try:
            # Get current database schema
            database = self.client.databases.retrieve(database_id=self.database_id)
            
            # Check if property already exists
            properties = database.get('properties', {})
            if 'Comeback % Historical' in properties:
                logger.info("✅ Comeback % Historical property already exists")
                return True
            
            # Add Comeback % Historical property (Number type)
            self.client.databases.update(
                database_id=self.database_id,
                properties={
                    'Comeback % Historical': {
                        'number': {
                            'format': 'percent'
                        }
                    }
                }
            )
            
            logger.info("✅ Added Comeback % Historical property to Tennis Prematch database")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error adding Comeback % Historical property: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def add_player_odds_properties(self) -> Dict[str, bool]:
        """
        Add Player A and Player B Odds properties
        
        Returns:
            Dictionary with success status for each property
        """
        if not self.client or not self.database_id:
            logger.error("❌ Notion client or database ID not available")
            return {'player_a_odds': False, 'player_b_odds': False}
        
        results = {'player_a_odds': False, 'player_b_odds': False}
        
        try:
            database = self.client.databases.retrieve(database_id=self.database_id)
            properties = database.get('properties', {})
            
            # Add Player A Odds
            if 'Player A Odds' not in properties:
                self.client.databases.update(
                    database_id=self.database_id,
                    properties={
                        'Player A Odds': {
                            'number': {}
                        }
                    }
                )
                logger.info("✅ Added Player A Odds property")
                results['player_a_odds'] = True
            else:
                logger.info("✅ Player A Odds property already exists")
                results['player_a_odds'] = True
            
            # Add Player B Odds
            if 'Player B Odds' not in properties:
                self.client.databases.update(
                    database_id=self.database_id,
                    properties={
                        'Player B Odds': {
                            'number': {}
                        }
                    }
                )
                logger.info("✅ Added Player B Odds property")
                results['player_b_odds'] = True
            else:
                logger.info("✅ Player B Odds property already exists")
                results['player_b_odds'] = True
                
        except Exception as e:
            logger.error(f"❌ Error adding odds properties: {e}")
            import traceback
            traceback.print_exc()
        
        return results
    
    def add_relation_properties(self, 
                                player_cards_db_id: Optional[str] = None,
                                scraping_targets_db_id: Optional[str] = None) -> Dict[str, bool]:
        """
        Add relation properties: Data Source Scraper, Player A Card, Player B Card
        
        Args:
            player_cards_db_id: ITF Player Cards database ID (optional, from env)
            scraping_targets_db_id: ROI Scraping Targets database ID (optional, from env)
        
        Returns:
            Dictionary with success status for each property
        """
        if not self.client or not self.database_id:
            logger.error("❌ Notion client or database ID not available")
            return {'data_source_scraper': False, 'player_a_card': False, 'player_b_card': False}
        
        # Try to get database IDs from env if not provided
        if not player_cards_db_id:
            player_cards_db_id = os.getenv('NOTION_ITF_PLAYER_CARDS_DB_ID')
        if not scraping_targets_db_id:
            scraping_targets_db_id = os.getenv('NOTION_ROI_SCRAPING_TARGETS_DB_ID')
        
        results = {'data_source_scraper': False, 'player_a_card': False, 'player_b_card': False}
        
        try:
            database = self.client.databases.retrieve(database_id=self.database_id)
            properties = database.get('properties', {})
            
            # Add Data Source Scraper relation
            if 'Data Source Scraper' not in properties:
                if scraping_targets_db_id:
                    self.client.databases.update(
                        database_id=self.database_id,
                        properties={
                            'Data Source Scraper': {
                                'relation': {
                                    'database_id': scraping_targets_db_id,
                                    'type': 'single_property',
                                    'single_property': {}
                                }
                            }
                        }
                    )
                    logger.info("✅ Added Data Source Scraper relation")
                    results['data_source_scraper'] = True
                else:
                    logger.warning("⚠️ ROI Scraping Targets DB ID not provided, skipping Data Source Scraper relation")
            else:
                logger.info("✅ Data Source Scraper relation already exists")
                results['data_source_scraper'] = True
            
            # Add Player A Card relation
            if 'Player A Card' not in properties:
                if player_cards_db_id:
                    self.client.databases.update(
                        database_id=self.database_id,
                        properties={
                            'Player A Card': {
                                'relation': {
                                    'database_id': player_cards_db_id,
                                    'type': 'single_property',
                                    'single_property': {}
                                }
                            }
                        }
                    )
                    logger.info("✅ Added Player A Card relation")
                    results['player_a_card'] = True
                else:
                    logger.warning("⚠️ ITF Player Cards DB ID not provided, skipping Player A Card relation")
            else:
                logger.info("✅ Player A Card relation already exists")
                results['player_a_card'] = True
            
            # Add Player B Card relation
            if 'Player B Card' not in properties:
                if player_cards_db_id:
                    self.client.databases.update(
                        database_id=self.database_id,
                        properties={
                            'Player B Card': {
                                'relation': {
                                    'database_id': player_cards_db_id,
                                    'type': 'single_property',
                                    'single_property': {}
                                }
                            }
                        }
                    )
                    logger.info("✅ Added Player B Card relation")
                    results['player_b_card'] = True
                else:
                    logger.warning("⚠️ ITF Player Cards DB ID not provided, skipping Player B Card relation")
            else:
                logger.info("✅ Player B Card relation already exists")
                results['player_b_card'] = True
                
        except Exception as e:
            logger.error(f"❌ Error adding relation properties: {e}")
            import traceback
            traceback.print_exc()
        
        return results
    
    def add_screening_formula_property(self) -> bool:
        """
        Add Screening formula property that auto-calculates if match is interesting
        
        Formula logic:
        - Tournament Tier: W15 or W35
        - Player A Odds: 1.30-1.80
        - Ranking gap: <= 150 (using rollups from Player Cards)
        - Surface Win%: > 55% (using rollup from Player Cards)
        
        Returns:
            True if successful
        """
        if not self.client or not self.database_id:
            logger.error("❌ Notion client or database ID not available")
            return False
        
        try:
            database = self.client.databases.retrieve(database_id=self.database_id)
            properties = database.get('properties', {})
            
            if 'Screening' in properties:
                logger.info("✅ Screening formula property already exists")
                return True
            
            # Note: Notion API doesn't support creating formula properties directly
            # This needs to be done manually in Notion UI or via a different method
            # We'll log instructions instead
            logger.warning("⚠️ Formula properties cannot be created via API")
            logger.info("📝 Please add Screening formula manually in Notion:")
            logger.info("   1. Go to Tennis Prematch database")
            logger.info("   2. Add new property: 'Screening' (Formula type)")
            logger.info("   3. Use this formula:")
            logger.info("")
            logger.info("   if(")
            logger.info("     and(")
            logger.info("       or(prop(\"Tournament Tier\") == \"W15\", prop(\"Tournament Tier\") == \"W35\"),")
            logger.info("       prop(\"Player A Odds\") >= 1.30,")
            logger.info("       prop(\"Player A Odds\") <= 1.80,")
            logger.info("       abs(prop(\"Player A Rank\") - prop(\"Player B Rank\")) <= 150,")
            logger.info("       prop(\"Player A Surface Win%\") > 55")
            logger.info("     ),")
            logger.info("     \"🟢 KIINNOSTAVA\",")
            logger.info("     \"⚪ Skip\"")
            logger.info("   )")
            logger.info("")
            logger.info("   Note: Player A Rank, Player B Rank, and Player A Surface Win%")
            logger.info("   should be Rollup properties from Player A/B Card relations")
            
            return False  # Cannot be done via API
            
        except Exception as e:
            logger.error(f"❌ Error adding Screening formula: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def add_ai_analysis_properties(self) -> Dict[str, bool]:
        """
        Add properties for AI analysis results
        
        Returns:
            Dictionary with success status for each property
        """
        if not self.client or not self.database_id:
            logger.error("❌ Notion client or database ID not available")
            return {'ai_recommendation': False, 'ai_confidence': False, 'ai_reasoning': False, 'analysis_cost': False}
        
        results = {
            'ai_recommendation': False,
            'ai_confidence': False,
            'ai_reasoning': False,
            'analysis_cost': False,
            'analyzed_at': False
        }
        
        try:
            database = self.client.databases.retrieve(database_id=self.database_id)
            properties = database.get('properties', {})
            
            # Add AI Recommendation (Select)
            if 'AI Recommendation' not in properties:
                self.client.databases.update(
                    database_id=self.database_id,
                    properties={
                        'AI Recommendation': {
                            'select': {
                                'options': [
                                    {'name': 'Bet', 'color': 'green'},
                                    {'name': 'Skip', 'color': 'gray'},
                                    {'name': 'Monitor', 'color': 'yellow'}
                                ]
                            }
                        }
                    }
                )
                logger.info("✅ Added AI Recommendation property")
                results['ai_recommendation'] = True
            else:
                logger.info("✅ AI Recommendation property already exists")
                results['ai_recommendation'] = True
            
            # Add AI Confidence (Number)
            if 'AI Confidence' not in properties:
                self.client.databases.update(
                    database_id=self.database_id,
                    properties={
                        'AI Confidence': {
                            'number': {
                                'format': 'number'
                            }
                        }
                    }
                )
                logger.info("✅ Added AI Confidence property")
                results['ai_confidence'] = True
            else:
                logger.info("✅ AI Confidence property already exists")
                results['ai_confidence'] = True
            
            # Add AI Reasoning (Text)
            if 'AI Reasoning' not in properties:
                self.client.databases.update(
                    database_id=self.database_id,
                    properties={
                        'AI Reasoning': {
                            'rich_text': {}
                        }
                    }
                )
                logger.info("✅ Added AI Reasoning property")
                results['ai_reasoning'] = True
            else:
                logger.info("✅ AI Reasoning property already exists")
                results['ai_reasoning'] = True
            
            # Add Analysis Cost (Number)
            if 'Analysis Cost' not in properties:
                self.client.databases.update(
                    database_id=self.database_id,
                    properties={
                        'Analysis Cost': {
                            'number': {
                                'format': 'dollar'
                            }
                        }
                    }
                )
                logger.info("✅ Added Analysis Cost property")
                results['analysis_cost'] = True
            else:
                logger.info("✅ Analysis Cost property already exists")
                results['analysis_cost'] = True
            
            # Add Analyzed At (Date)
            if 'Analyzed At' not in properties:
                self.client.databases.update(
                    database_id=self.database_id,
                    properties={
                        'Analyzed At': {
                            'date': {}
                        }
                    }
                )
                logger.info("✅ Added Analyzed At property")
                results['analyzed_at'] = True
            else:
                logger.info("✅ Analyzed At property already exists")
                results['analyzed_at'] = True
                
        except Exception as e:
            logger.error(f"❌ Error adding AI analysis properties: {e}")
            import traceback
            traceback.print_exc()
        
        return results
    
    def update_all_properties(self) -> Dict[str, Any]:
        """
        Update all ITF properties at once (including new filtering properties)
        
        Returns:
            Dictionary with success status for each property group
        """
        logger.info("🚀 Updating all ITF properties in Tennis Prematch database...")
        
        results = {
            'tournament_tier': self.add_tournament_tier_property(),
            'set1_deficit': self.add_set1_deficit_property(),
            'comeback_percent': self.add_comeback_percent_property(),
            'odds': self.add_player_odds_properties(),
            'relations': self.add_relation_properties(),
            'screening': self.add_screening_formula_property(),
            'ai_analysis': self.add_ai_analysis_properties(),
        }
        
        success_count = sum(
            1 for v in results.values() 
            if (isinstance(v, bool) and v) or (isinstance(v, dict) and any(v.values()))
        )
        total_properties = sum(
            len(v) if isinstance(v, dict) else 1 
            for v in results.values()
        )
        
        logger.info(f"✅ Updated {success_count}/{total_properties} property groups successfully")
        
        return results
    
    def update_match_with_tier(self, page_id: str, tournament_tier: str) -> bool:
        """
        Update existing match page with tournament tier
        
        Args:
            page_id: Notion page ID
            tournament_tier: Tournament tier (W15, W35, W50, etc.)
            
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        try:
            self.client.pages.update(
                page_id=page_id,
                properties={
                    'Tournament Tier': {
                        'select': {
                            'name': tournament_tier
                        }
                    }
                }
            )
            logger.info(f"✅ Updated match {page_id} with tournament tier: {tournament_tier}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating match with tier: {e}")
            return False
    
    def update_match_with_set1_deficit(self, page_id: str, has_deficit: bool) -> bool:
        """
        Update existing match page with Set 1 Deficit flag
        
        Args:
            page_id: Notion page ID
            has_deficit: True if player lost first set badly
            
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        try:
            self.client.pages.update(
                page_id=page_id,
                properties={
                    'Set 1 Deficit': {
                        'checkbox': has_deficit
                    }
                }
            )
            logger.info(f"✅ Updated match {page_id} with Set 1 Deficit: {has_deficit}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating match with Set 1 Deficit: {e}")
            return False
    
    def update_match_with_comeback_percent(self, page_id: str, comeback_percent: float) -> bool:
        """
        Update existing match page with comeback percentage
        
        Args:
            page_id: Notion page ID
            comeback_percent: Historical comeback percentage (0.0-1.0)
            
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        try:
            self.client.pages.update(
                page_id=page_id,
                properties={
                    'Comeback % Historical': {
                        'number': comeback_percent
                    }
                }
            )
            logger.info(f"✅ Updated match {page_id} with comeback %: {comeback_percent:.2%}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating match with comeback %: {e}")
            return False


def main():
    """Test ITF Database Updater"""
    print("📊 ITF DATABASE UPDATER TEST")
    print("=" * 50)
    
    updater = ITFDatabaseUpdater()
    
    if not updater.client:
        print("❌ Notion client not available")
        print("\n💡 Setup:")
        print("1. Install: pip install notion-client")
        print("2. Get Notion API key: https://www.notion.so/my-integrations")
        print("3. Add to telegram_secrets.env: NOTION_API_KEY=your_key")
        print("4. Add Tennis Prematch database ID: NOTION_TENNIS_PREMATCH_DB_ID=your_db_id")
        return
    
    if not updater.database_id:
        print("⚠️ Tennis Prematch database ID not set")
        print("\n💡 Get database ID:")
        print("1. Open your Tennis Prematch database in Notion")
        print("2. Copy database ID from URL")
        print("3. Add to telegram_secrets.env: NOTION_TENNIS_PREMATCH_DB_ID=your_db_id")
        return
    
    print(f"✅ Connected to database: {updater.database_id[:8]}...")
    print("\n🚀 Updating properties...")
    
    results = updater.update_all_properties()
    
    print("\n📊 Results:")
    for prop, success in results.items():
        status = "✅" if success else "❌"
        print(f"   {status} {prop}: {'Success' if success else 'Failed'}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()

