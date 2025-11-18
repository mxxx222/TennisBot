#!/usr/bin/env python3
"""
📊 TENNISEXPLORER NOTION UPDATER
=================================

Updates Notion database with enriched TennisExplorer match data.
Creates/updates TennisExplorer Live Feed database with all enriched fields.
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
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


class TennisExplorerNotionUpdater:
    """Updates Notion database with TennisExplorer enriched data"""
    
    def __init__(self, database_id: Optional[str] = None):
        """
        Initialize Notion updater
        
        Args:
            database_id: TennisExplorer Live Feed database ID
        """
        if not NOTION_AVAILABLE:
            logger.warning("⚠️ notion-client not available")
            self.client = None
            return
        
        api_key = os.getenv('NOTION_API_KEY')
        if not api_key:
            logger.warning("⚠️ NOTION_API_KEY not found in environment")
            self.client = None
            return
        
        self.client = Client(auth=api_key)
        self.database_id = database_id or os.getenv('NOTION_TENNISEXPLORER_DB_ID')
        
        if not self.database_id:
            logger.warning("⚠️ TennisExplorer database ID not set")
        
        logger.info("📊 TennisExplorer Notion Updater initialized")
    
    def create_or_update_match(self, match_data: Dict[str, Any]) -> Optional[str]:
        """
        Create or update match page in Notion
        
        Args:
            match_data: Dictionary with all match and enriched data
            
        Returns:
            Notion page ID if successful, None otherwise
        """
        if not self.client or not self.database_id:
            logger.warning("⚠️ Notion client or database ID not available")
            return None
        
        try:
            # Build properties
            properties = self._build_properties(match_data)
            
            # Check if page exists (by match_id)
            existing_page = self._find_existing_page(match_data.get('match_id'))
            
            if existing_page:
                # Update existing page
                page_id = existing_page['id']
                self.client.pages.update(
                    page_id=page_id,
                    properties=properties
                )
                logger.info(f"✅ Updated match page: {match_data.get('match_id')}")
            else:
                # Create new page
                page = self.client.pages.create(
                    parent={"database_id": self.database_id},
                    properties=properties
                )
                page_id = page['id']
                logger.info(f"✅ Created match page: {match_data.get('match_id')}")
            
            return page_id
            
        except Exception as e:
            logger.error(f"❌ Error creating/updating match: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _build_properties(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build Notion properties from match data"""
        properties = {}
        
        # Basic match info
        if match_data.get('player_a'):
            properties['Pelaaja A nimi'] = {
                'rich_text': [{'text': {'content': match_data['player_a']}}]
            }
        
        if match_data.get('player_b'):
            properties['Pelaaja B nimi'] = {
                'rich_text': [{'text': {'content': match_data['player_b']}}]
            }
        
        # Match title
        title = f"{match_data.get('player_a', 'Player A')} vs {match_data.get('player_b', 'Player B')}"
        properties['Name'] = {
            'title': [{'text': {'content': title}}]
        }
        
        # Tournament
        if match_data.get('tournament'):
            properties['Turnaus'] = {
                'rich_text': [{'text': {'content': match_data['tournament']}}]
            }
        
        # Surface
        if match_data.get('surface'):
            properties['Kenttä'] = {
                'select': {'name': match_data['surface']}
            }
        
        # Tournament tier
        if match_data.get('tournament_tier'):
            properties['Tournament Tier'] = {
                'select': {'name': match_data['tournament_tier']}
            }
        
        # Date
        if match_data.get('match_date'):
            properties['Päivämäärä'] = {
                'date': {'start': match_data['match_date']}
            }
        
        # ELO ratings
        if match_data.get('elo_a'):
            properties['ELO A'] = {'number': match_data['elo_a']}
        if match_data.get('elo_b'):
            properties['ELO B'] = {'number': match_data['elo_b']}
        if match_data.get('elo_a_hard'):
            properties['ELO A Hard'] = {'number': match_data['elo_a_hard']}
        if match_data.get('elo_b_hard'):
            properties['ELO B Hard'] = {'number': match_data['elo_b_hard']}
        
        # Recent form
        if match_data.get('recent_form_a'):
            properties['Recent Form A'] = {
                'rich_text': [{'text': {'content': match_data['recent_form_a']}}]
            }
        if match_data.get('recent_form_b'):
            properties['Recent Form B'] = {
                'rich_text': [{'text': {'content': match_data['recent_form_b']}}]
            }
        
        # H2H
        if match_data.get('h2h_overall'):
            h2h = match_data['h2h_overall']
            h2h_text = f"{h2h.get('wins_a', 0)}-{h2h.get('wins_b', 0)}"
            properties['H2H Overall'] = {
                'rich_text': [{'text': {'content': h2h_text}}]
            }
        
        if match_data.get('h2h_surface'):
            h2h_surface_text = ", ".join([
                f"{surface}: {record.get('wins_a', 0)}-{record.get('wins_b', 0)}"
                for surface, record in match_data['h2h_surface'].items()
            ])
            properties['H2H Surface'] = {
                'rich_text': [{'text': {'content': h2h_surface_text}}]
            }
        
        # Service stats
        if match_data.get('service_stats_a'):
            properties['Service Stats A'] = {
                'rich_text': [{'text': {'content': match_data['service_stats_a']}}]
            }
        if match_data.get('service_stats_b'):
            properties['Service Stats B'] = {
                'rich_text': [{'text': {'content': match_data['service_stats_b']}}]
            }
        
        # Return stats
        if match_data.get('return_stats_a'):
            properties['Return Stats A'] = {
                'rich_text': [{'text': {'content': match_data['return_stats_a']}}]
            }
        if match_data.get('return_stats_b'):
            properties['Return Stats B'] = {
                'rich_text': [{'text': {'content': match_data['return_stats_b']}}]
            }
        
        # Tiebreak records
        if match_data.get('tiebreak_record_a'):
            properties['Tiebreak Record A'] = {
                'rich_text': [{'text': {'content': match_data['tiebreak_record_a']}}]
            }
        if match_data.get('tiebreak_record_b'):
            properties['Tiebreak Record B'] = {
                'rich_text': [{'text': {'content': match_data['tiebreak_record_b']}}]
            }
        
        # Deciding set records
        if match_data.get('deciding_set_record_a'):
            properties['Deciding Set Record A'] = {
                'rich_text': [{'text': {'content': match_data['deciding_set_record_a']}}]
            }
        if match_data.get('deciding_set_record_b'):
            properties['Deciding Set Record B'] = {
                'rich_text': [{'text': {'content': match_data['deciding_set_record_b']}}]
            }
        
        # Recovery data
        if match_data.get('days_since_last_match_a'):
            properties['Days Since Last Match A'] = {
                'number': match_data['days_since_last_match_a']
            }
        if match_data.get('days_since_last_match_b'):
            properties['Days Since Last Match B'] = {
                'number': match_data['days_since_last_match_b']
            }
        
        if match_data.get('travel_distance_a'):
            properties['Travel Distance A'] = {
                'number': match_data['travel_distance_a']
            }
        if match_data.get('travel_distance_b'):
            properties['Travel Distance B'] = {
                'number': match_data['travel_distance_b']
            }
        
        # Weather
        if match_data.get('weather_temp'):
            properties['Weather Temp'] = {'number': match_data['weather_temp']}
        if match_data.get('weather_wind'):
            properties['Weather Wind'] = {'number': match_data['weather_wind']}
        if match_data.get('weather_humidity'):
            properties['Weather Humidity'] = {'number': match_data['weather_humidity']}
        
        # Court speed
        if match_data.get('court_speed_index'):
            properties['Court Speed Index'] = {'number': match_data['court_speed_index']}
        
        # Tournament history
        if match_data.get('tournament_history_a'):
            properties['Tournament History A'] = {
                'rich_text': [{'text': {'content': match_data['tournament_history_a']}}]
            }
        if match_data.get('tournament_history_b'):
            properties['Tournament History B'] = {
                'rich_text': [{'text': {'content': match_data['tournament_history_b']}}]
            }
        
        # Odds
        if match_data.get('opening_odds_a'):
            properties['Opening Odds A'] = {'number': match_data['opening_odds_a']}
        if match_data.get('opening_odds_b'):
            properties['Opening Odds B'] = {'number': match_data['opening_odds_b']}
        if match_data.get('current_odds_a'):
            properties['Current Odds A'] = {'number': match_data['current_odds_a']}
        if match_data.get('current_odds_b'):
            properties['Current Odds B'] = {'number': match_data['current_odds_b']}
        
        # Odds movement
        if match_data.get('odds_movement'):
            properties['Odds Movement'] = {
                'rich_text': [{'text': {'content': match_data['odds_movement']}}]
            }
        
        # ROI opportunity
        if match_data.get('roi_opportunity'):
            properties['ROI Opportunity'] = {
                'select': {'name': match_data['roi_opportunity']}
            }
        
        # Strategy tag
        if match_data.get('strategy_tag'):
            properties['Strategy Tag'] = {
                'select': {'name': match_data['strategy_tag']}
            }
        
        # Expected value
        if match_data.get('expected_value_pct'):
            properties['Expected Value %'] = {
                'number': match_data['expected_value_pct']
            }
        
        # Kelly stake
        if match_data.get('kelly_stake_pct'):
            properties['Kelly Stake %'] = {
                'number': match_data['kelly_stake_pct']
            }
        
        # Implied probabilities
        if match_data.get('implied_probability_a'):
            properties['Implied Probability A'] = {
                'number': match_data['implied_probability_a']
            }
        if match_data.get('implied_probability_b'):
            properties['Implied Probability B'] = {
                'number': match_data['implied_probability_b']
            }
        
        # Model probabilities
        if match_data.get('model_probability_a'):
            properties['Model Probability A'] = {
                'number': match_data['model_probability_a']
            }
        if match_data.get('model_probability_b'):
            properties['Model Probability B'] = {
                'number': match_data['model_probability_b']
            }
        
        # Scraper source
        properties['Scraper Source'] = {
            'select': {'name': 'TennisExplorer'}
        }
        
        return properties
    
    def _find_existing_page(self, match_id: str) -> Optional[Dict]:
        """Find existing page by match_id"""
        if not self.client or not self.database_id:
            return None
        
        try:
            # Query database for existing page
            # Note: This assumes there's a Match ID property
            results = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    'property': 'Match ID',
                    'rich_text': {'equals': match_id}
                }
            )
            
            if results.get('results'):
                return results['results'][0]
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not find existing page: {e}")
            return None

