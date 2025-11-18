#!/usr/bin/env python3
"""
📊 NOTION DATA MANAGER
======================
Laajennettu Notion-integraatio pelien hakemiseen ja tallentamiseen.

Features:
- 🔄 Pelien hakeminen Notion-tietokannasta
- 💾 Pelien tallentaminen Notion-tietokantaan
- 🔄 Automaattinen synkronointi
- 📊 ROI-analyysien tallennus
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml

try:
    from src.notion_mcp_integration import NotionMCPIntegration
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    NotionMCPIntegration = None

logger = logging.getLogger(__name__)


class NotionDataManager:
    """
    Notion Data Manager - pelien hakeminen ja tallentaminen
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize Notion Data Manager
        
        Args:
            config_path: Path to configuration file
        """
        logger.info("📊 Initializing Notion Data Manager...")
        
        # Load configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "unified_data_config.yaml"
        
        self.config = self._load_config(config_path)
        
        # Initialize Notion integration
        self.notion_integration = None
        self.database_ids = {}
        
        self._initialize_notion()
        
        logger.info("✅ Notion Data Manager initialized")
    
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Replace environment variables
            if 'api_keys' in config:
                for key, value in config['api_keys'].items():
                    if isinstance(value, str) and value.startswith('${'):
                        env_var = value[2:-1]
                        config['api_keys'][key] = os.getenv(env_var, '')
            
            return config
        except Exception as e:
            logger.error(f"❌ Error loading config: {e}")
            return {}
    
    def _initialize_notion(self):
        """Initialize Notion integration"""
        if not NOTION_AVAILABLE:
            logger.warning("⚠️ Notion integration not available")
            return
        
        try:
            notion_token = self.config.get('api_keys', {}).get('notion_token')
            if not notion_token:
                logger.warning("⚠️ Notion token not found in config")
                return
            
            self.notion_integration = NotionMCPIntegration(notion_token=notion_token)
            self.notion_integration.initialize_notion_client(notion_token)
            
            # Load database IDs from config
            self.database_ids = self.config.get('notion_databases', {})
            
            logger.info("✅ Notion integration initialized")
            
        except Exception as e:
            logger.error(f"❌ Error initializing Notion: {e}")
    
    def fetch_matches_from_notion(self, sport: str, date_from: datetime = None, date_to: datetime = None) -> List[Dict[str, Any]]:
        """
        Hae pelit Notion-tietokannasta
        
        Args:
            sport: Laji (tennis, football, basketball, ice_hockey)
            date_from: Alkupäivämäärä
            date_to: Loppupäivämäärä
            
        Returns:
            Lista otteludata-diktejä
        """
        if not self.notion_integration or not self.notion_integration.notion_client:
            logger.warning("⚠️ Notion client not initialized")
            return []
        
        database_id = self.database_ids.get(sport)
        if not database_id:
            logger.warning(f"⚠️ Database ID not found for {sport}")
            return []
        
        try:
            logger.info(f"🔍 Fetching {sport} matches from Notion...")
            
            # Build query
            query = {
                "database_id": database_id,
                "filter": {}
            }
            
            # Add date filter if provided
            if date_from or date_to:
                date_filter = {}
                if date_from:
                    date_filter["on_or_after"] = date_from.isoformat()
                if date_to:
                    date_filter["on_or_before"] = date_to.isoformat()
                
                query["filter"] = {
                    "property": "Date",
                    "date": date_filter
                }
            
            # Query Notion database
            response = self.notion_integration.notion_client.databases.query(**query)
            
            matches = []
            for page in response.get('results', []):
                match_data = self._parse_notion_page(page, sport)
                if match_data:
                    matches.append(match_data)
            
            logger.info(f"✅ Fetched {len(matches)} matches from Notion")
            return matches
            
        except Exception as e:
            logger.error(f"❌ Error fetching matches from Notion: {e}")
            return []
    
    def _parse_notion_page(self, page: Dict, sport: str) -> Optional[Dict[str, Any]]:
        """Parse Notion page to match data"""
        try:
            properties = page.get('properties', {})
            
            # Extract match data based on sport
            if sport == 'tennis':
                match_data = {
                    'match_id': page.get('id', ''),
                    'player_1': self._get_property_value(properties.get('Player 1', {})),
                    'player_2': self._get_property_value(properties.get('Player 2', {})),
                    'tournament': self._get_property_value(properties.get('Tournament', {})),
                    'surface': self._get_property_value(properties.get('Surface', {})),
                    'date': self._get_property_value(properties.get('Date', {})),
                    'status': self._get_property_value(properties.get('Status', {})),
                    'odds_player_1': self._get_property_value(properties.get('Odds Player 1', {})),
                    'odds_player_2': self._get_property_value(properties.get('Odds Player 2', {})),
                    'roi': self._get_property_value(properties.get('ROI', {})),
                    'edge': self._get_property_value(properties.get('Edge', {})),
                    'confidence': self._get_property_value(properties.get('Confidence', {}))
                }
            else:
                match_data = {
                    'match_id': page.get('id', ''),
                    'home_team': self._get_property_value(properties.get('Home Team', {})),
                    'away_team': self._get_property_value(properties.get('Away Team', {})),
                    'league': self._get_property_value(properties.get('League', {})),
                    'date': self._get_property_value(properties.get('Date', {})),
                    'status': self._get_property_value(properties.get('Status', {})),
                    'odds_home': self._get_property_value(properties.get('Odds Home', {})),
                    'odds_away': self._get_property_value(properties.get('Odds Away', {})),
                    'roi': self._get_property_value(properties.get('ROI', {})),
                    'edge': self._get_property_value(properties.get('Edge', {})),
                    'confidence': self._get_property_value(properties.get('Confidence', {}))
                }
            
            match_data['sport'] = sport
            return match_data
            
        except Exception as e:
            logger.error(f"❌ Error parsing Notion page: {e}")
            return None
    
    def _get_property_value(self, property_data: Dict) -> Any:
        """Extract value from Notion property"""
        if not property_data:
            return None
        
        prop_type = property_data.get('type')
        
        if prop_type == 'title':
            title_array = property_data.get('title', [])
            return title_array[0].get('plain_text', '') if title_array else ''
        elif prop_type == 'rich_text':
            rich_text_array = property_data.get('rich_text', [])
            return rich_text_array[0].get('plain_text', '') if rich_text_array else ''
        elif prop_type == 'number':
            return property_data.get('number')
        elif prop_type == 'date':
            date_obj = property_data.get('date')
            return date_obj.get('start') if date_obj else None
        elif prop_type == 'select':
            select_obj = property_data.get('select')
            return select_obj.get('name') if select_obj else None
        
        return None
    
    def store_match_to_notion(self, match_data: Dict[str, Any], sport: str) -> bool:
        """
        Tallenna ottelu Notion-tietokantaan
        
        Args:
            match_data: Otteludata-dikti
            sport: Laji
            
        Returns:
            True jos onnistui
        """
        if not self.notion_integration or not self.notion_integration.notion_client:
            logger.warning("⚠️ Notion client not initialized")
            return False
        
        database_id = self.database_ids.get(sport)
        if not database_id:
            logger.warning(f"⚠️ Database ID not found for {sport}")
            return False
        
        try:
            logger.info(f"💾 Storing {sport} match to Notion...")
            
            # Convert match data to Notion properties
            properties = self._convert_match_to_notion_properties(match_data, sport)
            
            # Create page in database
            self.notion_integration.notion_client.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )
            
            logger.info(f"✅ Stored match to Notion")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing match to Notion: {e}")
            return False
    
    def _convert_match_to_notion_properties(self, match_data: Dict, sport: str) -> Dict:
        """Convert match data to Notion properties format"""
        properties = {}
        
        if sport == 'tennis':
            properties = {
                "Match": {
                    "title": [{"text": {"content": f"{match_data.get('player_1', '')} vs {match_data.get('player_2', '')}"}}]
                },
                "Player 1": {"rich_text": [{"text": {"content": str(match_data.get('player_1', ''))}}]},
                "Player 2": {"rich_text": [{"text": {"content": str(match_data.get('player_2', ''))}}]},
                "Tournament": {"select": {"name": str(match_data.get('tournament', ''))}},
                "Surface": {"select": {"name": str(match_data.get('surface', ''))}},
                "Date": {"date": {"start": match_data.get('match_time', datetime.now()).isoformat()}},
                "Status": {"select": {"name": str(match_data.get('status', 'Scheduled'))}},
                "Odds Player 1": {"number": match_data.get('odds', {}).get('player_1')},
                "Odds Player 2": {"number": match_data.get('odds', {}).get('player_2')},
                "ROI": {"number": match_data.get('roi', 0)},
                "Edge": {"number": match_data.get('edge', 0)},
                "Expected Value": {"number": match_data.get('expected_value', 0)},
                "Confidence": {"select": {"name": self._get_confidence_level(match_data.get('confidence', 0))}}
            }
        else:
            properties = {
                "Match": {
                    "title": [{"text": {"content": f"{match_data.get('home_team', '')} vs {match_data.get('away_team', '')}"}}]
                },
                "Home Team": {"rich_text": [{"text": {"content": str(match_data.get('home_team', ''))}}]},
                "Away Team": {"rich_text": [{"text": {"content": str(match_data.get('away_team', ''))}}]},
                "League": {"select": {"name": str(match_data.get('league', ''))}},
                "Date": {"date": {"start": match_data.get('match_time', datetime.now()).isoformat()}},
                "Status": {"select": {"name": str(match_data.get('status', 'Scheduled'))}},
                "Odds Home": {"number": match_data.get('odds', {}).get('home')},
                "Odds Away": {"number": match_data.get('odds', {}).get('away')},
                "ROI": {"number": match_data.get('roi', 0)},
                "Edge": {"number": match_data.get('edge', 0)},
                "Expected Value": {"number": match_data.get('expected_value', 0)},
                "Confidence": {"select": {"name": self._get_confidence_level(match_data.get('confidence', 0))}}
            }
        
        return properties
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Convert confidence score to confidence level"""
        if confidence >= 0.75:
            return "High"
        elif confidence >= 0.65:
            return "Medium"
        else:
            return "Low"
    
    def store_roi_analysis(self, roi_data: Dict[str, Any]) -> bool:
        """
        Tallenna ROI-analyysi Notioniin
        
        Args:
            roi_data: ROI-analyysidata
            
        Returns:
            True jos onnistui
        """
        if not self.notion_integration:
            return False
        
        return self.notion_integration.sync_roi_analysis(roi_data)
    
    def sync_matches(self, matches: List[Dict[str, Any]], sport: str) -> int:
        """
        Synkronoi useita otteluita Notioniin
        
        Args:
            matches: Lista otteludata-diktejä
            sport: Laji
            
        Returns:
            Onnistuneiden synkronointien määrä
        """
        success_count = 0
        
        for match_data in matches:
            if self.store_match_to_notion(match_data, sport):
                success_count += 1
        
        logger.info(f"✅ Synced {success_count}/{len(matches)} matches to Notion")
        return success_count

