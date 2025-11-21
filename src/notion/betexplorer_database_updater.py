#!/usr/bin/env python3
"""
📊 NOTION BETEXPLORER DATABASE UPDATER
======================================

Adds BetExplorer-specific properties to Tennis Prematch database:
- Best Odds P1 (number) - Best back odds for player 1
- Bookmaker P1 (select) - Bookmaker with best odds for player 1
- Best Odds P2 (number) - Best back odds for player 2
- Bookmaker P2 (select) - Bookmaker with best odds for player 2
- Odds Advantage % (formula) - Manual creation required
- Data Source (select) - "BetExplorer" / "FlashScore" / "Both"

Extends ITFDatabaseUpdater functionality.
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

# Import ITFDatabaseUpdater
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.notion.itf_database_updater import ITFDatabaseUpdater

logger = logging.getLogger(__name__)


class BetExplorerDatabaseUpdater(ITFDatabaseUpdater):
    """Extends ITFDatabaseUpdater to add BetExplorer-specific properties"""
    
    def __init__(self, database_id: Optional[str] = None):
        """
        Initialize BetExplorer Database Updater
        
        Args:
            database_id: Tennis Prematch database ID (optional, can be set via env or config)
        """
        super().__init__(database_id)
        logger.info("📊 BetExplorer Database Updater initialized")
    
    def add_best_odds_properties(self) -> Dict[str, bool]:
        """
        Add Best Odds P1/P2 and Bookmaker P1/P2 properties
        
        Returns:
            Dictionary with success status for each property
        """
        if not self.client or not self.database_id:
            logger.error("❌ Notion client or database ID not available")
            return {
                'best_odds_p1': False,
                'bookmaker_p1': False,
                'best_odds_p2': False,
                'bookmaker_p2': False
            }
        
        results = {
            'best_odds_p1': False,
            'bookmaker_p1': False,
            'best_odds_p2': False,
            'bookmaker_p2': False
        }
        
        try:
            database = self.client.databases.retrieve(database_id=self.database_id)
            properties = database.get('properties', {})
            
            # Add Best Odds P1
            if 'Best Odds P1' not in properties:
                self.client.databases.update(
                    database_id=self.database_id,
                    properties={
                        'Best Odds P1': {
                            'number': {}
                        }
                    }
                )
                logger.info("✅ Added Best Odds P1 property")
                results['best_odds_p1'] = True
            else:
                logger.info("✅ Best Odds P1 property already exists")
                results['best_odds_p1'] = True
            
            # Add Bookmaker P1 (select with common bookmakers)
            if 'Bookmaker P1' not in properties:
                # Common bookmakers list
                bookmaker_options = [
                    {'name': 'Bet365', 'color': 'blue'},
                    {'name': 'Pinnacle', 'color': 'green'},
                    {'name': 'Unibet', 'color': 'yellow'},
                    {'name': 'Betfair', 'color': 'orange'},
                    {'name': 'William Hill', 'color': 'red'},
                    {'name': 'Ladbrokes', 'color': 'purple'},
                    {'name': 'Coral', 'color': 'pink'},
                    {'name': 'Betway', 'color': 'brown'},
                    {'name': '888sport', 'color': 'gray'},
                    {'name': 'BetVictor', 'color': 'default'},
                    {'name': 'Other', 'color': 'default'},
                ]
                
                self.client.databases.update(
                    database_id=self.database_id,
                    properties={
                        'Bookmaker P1': {
                            'select': {
                                'options': bookmaker_options
                            }
                        }
                    }
                )
                logger.info("✅ Added Bookmaker P1 property")
                results['bookmaker_p1'] = True
            else:
                logger.info("✅ Bookmaker P1 property already exists")
                results['bookmaker_p1'] = True
            
            # Add Best Odds P2
            if 'Best Odds P2' not in properties:
                self.client.databases.update(
                    database_id=self.database_id,
                    properties={
                        'Best Odds P2': {
                            'number': {}
                        }
                    }
                )
                logger.info("✅ Added Best Odds P2 property")
                results['best_odds_p2'] = True
            else:
                logger.info("✅ Best Odds P2 property already exists")
                results['best_odds_p2'] = True
            
            # Add Bookmaker P2 (select with same bookmakers)
            if 'Bookmaker P2' not in properties:
                bookmaker_options = [
                    {'name': 'Bet365', 'color': 'blue'},
                    {'name': 'Pinnacle', 'color': 'green'},
                    {'name': 'Unibet', 'color': 'yellow'},
                    {'name': 'Betfair', 'color': 'orange'},
                    {'name': 'William Hill', 'color': 'red'},
                    {'name': 'Ladbrokes', 'color': 'purple'},
                    {'name': 'Coral', 'color': 'pink'},
                    {'name': 'Betway', 'color': 'brown'},
                    {'name': '888sport', 'color': 'gray'},
                    {'name': 'BetVictor', 'color': 'default'},
                    {'name': 'Other', 'color': 'default'},
                ]
                
                self.client.databases.update(
                    database_id=self.database_id,
                    properties={
                        'Bookmaker P2': {
                            'select': {
                                'options': bookmaker_options
                            }
                        }
                    }
                )
                logger.info("✅ Added Bookmaker P2 property")
                results['bookmaker_p2'] = True
            else:
                logger.info("✅ Bookmaker P2 property already exists")
                results['bookmaker_p2'] = True
                
        except Exception as e:
            logger.error(f"❌ Error adding best odds properties: {e}")
            import traceback
            traceback.print_exc()
        
        return results
    
    def add_data_source_property(self) -> bool:
        """
        Add Data Source property to track scraper source
        
        Returns:
            True if successful
        """
        if not self.client or not self.database_id:
            logger.error("❌ Notion client or database ID not available")
            return False
        
        try:
            database = self.client.databases.retrieve(database_id=self.database_id)
            properties = database.get('properties', {})
            
            if 'Data Source' not in properties:
                self.client.databases.update(
                    database_id=self.database_id,
                    properties={
                        'Data Source': {
                            'select': {
                                'options': [
                                    {'name': 'BetExplorer', 'color': 'blue'},
                                    {'name': 'FlashScore', 'color': 'green'},
                                    {'name': 'Both', 'color': 'yellow'},
                                    {'name': 'TennisExplorer', 'color': 'orange'},
                                ]
                            }
                        }
                    }
                )
                logger.info("✅ Added Data Source property")
                return True
            else:
                logger.info("✅ Data Source property already exists")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error adding Data Source property: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def add_odds_advantage_formula(self) -> bool:
        """
        Add instructions for creating Odds Advantage % formula property
        
        Note: Notion API doesn't support creating formula properties directly.
        This method logs instructions for manual creation.
        
        Returns:
            False (cannot be done via API)
        """
        if not self.client or not self.database_id:
            logger.error("❌ Notion client or database ID not available")
            return False
        
        try:
            database = self.client.databases.retrieve(database_id=self.database_id)
            properties = database.get('properties', {})
            
            if 'Odds Advantage %' in properties:
                logger.info("✅ Odds Advantage % formula property already exists")
                return True
            
            # Note: Formula properties cannot be created via API
            logger.warning("⚠️ Formula properties cannot be created via API")
            logger.info("📝 Please add Odds Advantage % formula manually in Notion:")
            logger.info("   1. Go to Tennis Prematch database")
            logger.info("   2. Add new property: 'Odds Advantage %' (Formula type)")
            logger.info("   3. Use this formula:")
            logger.info("")
            logger.info("   if(")
            logger.info("     prop(\"Best Odds P1\") > 0 and prop(\"Player A Odds\") > 0,")
            logger.info("     (prop(\"Best Odds P1\") / prop(\"Player A Odds\") - 1) * 100,")
            logger.info("     0")
            logger.info("   )")
            logger.info("")
            logger.info("   This calculates the percentage advantage of Best Odds vs FlashScore odds")
            
            return False  # Cannot be done via API
            
        except Exception as e:
            logger.error(f"❌ Error adding Odds Advantage % formula: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def update_all_properties(self) -> Dict[str, Any]:
        """
        Update all BetExplorer properties at once
        
        Returns:
            Dictionary with success status for each property group
        """
        logger.info("🚀 Updating all BetExplorer properties in Tennis Prematch database...")
        
        results = {
            'best_odds': self.add_best_odds_properties(),
            'data_source': self.add_data_source_property(),
            'odds_advantage': self.add_odds_advantage_formula(),
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


def main():
    """Test BetExplorer Database Updater"""
    print("📊 BETEXPLORER DATABASE UPDATER TEST")
    print("=" * 50)
    
    updater = BetExplorerDatabaseUpdater()
    
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
        if isinstance(success, dict):
            print(f"   {prop}:")
            for sub_prop, sub_success in success.items():
                status = "✅" if sub_success else "❌"
                print(f"      {status} {sub_prop}: {'Success' if sub_success else 'Failed'}")
        else:
            status = "✅" if success else "❌"
            print(f"   {status} {prop}: {'Success' if success else 'Failed'}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()

