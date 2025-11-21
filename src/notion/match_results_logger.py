#!/usr/bin/env python3
"""
Match Results Notion Logger
===========================

Logs comprehensive match data to Match Results DB for ML training.
Supports all 50 properties including odds, player stats, AI predictions, and betting info.
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

logger = logging.getLogger(__name__)


class MatchResultsLogger:
    """Notion logger for Match Results DB (50 properties for ML training)"""
    
    def __init__(self, database_id: Optional[str] = None):
        """
        Initialize Match Results Notion logger
        
        Args:
            database_id: Notion Match Results database ID (optional, can be set via env)
        """
        self.client = None
        self.database_id = database_id or os.getenv('NOTION_MATCH_RESULTS_DB_ID')
        
        if NOTION_AVAILABLE:
            notion_token = os.getenv('NOTION_API_KEY') or os.getenv('NOTION_TOKEN')
            if notion_token:
                self.client = Client(auth=notion_token)
            else:
                logger.warning("⚠️ NOTION_API_KEY not set")
        
        if not self.database_id:
            logger.warning("⚠️ NOTION_MATCH_RESULTS_DB_ID not set")
        
        logger.info("📊 Match Results Logger initialized")
    
    def log_match(self, match_data: Dict[str, Any]) -> Optional[str]:
        """
        Log match to Match Results DB with all available properties
        
        Args:
            match_data: Dictionary with match data (all 50 properties supported)
            
        Returns:
            Notion page ID if successful, None otherwise
        """
        if not self.client:
            logger.warning("⚠️ Notion client not available")
            return None
        
        if not self.database_id:
            logger.warning("⚠️ NOTION_MATCH_RESULTS_DB_ID not set")
            return None
        
        try:
            # Check for duplicates
            if self._is_duplicate(match_data):
                logger.debug(f"⏭️ Skipping duplicate match: {match_data.get('match_name', 'Unknown')}")
                return None
            
            # Build properties dictionary
            properties = self._build_properties(match_data)
            
            # Create page
            page = self.client.pages.create(
                parent={'database_id': self.database_id},
                properties=properties
            )
            
            logger.info(f"✅ Logged match: {match_data.get('match_name', 'Unknown')}")
            return page['id']
        
        except Exception as e:
            logger.error(f"❌ Error logging match: {e}")
            return None
    
    def _build_properties(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build Notion properties from match data"""
        properties = {}
        
        # Basic Data
        if 'match_name' in data:
            properties['Match Name'] = {'title': [{'text': {'content': data['match_name']}}]}
        
        if 'match_id' in data:
            properties['Match ID'] = {'rich_text': [{'text': {'content': str(data['match_id'])}}]}
        
        if 'player_a' in data:
            properties['Player A'] = {'rich_text': [{'text': {'content': data['player_a']}}]}
        
        if 'player_b' in data:
            properties['Player B'] = {'rich_text': [{'text': {'content': data['player_b']}}]}
        
        if 'tournament' in data:
            properties['Tournament'] = {'rich_text': [{'text': {'content': data['tournament'][:2000]}}]}
        
        if 'tournament_tier' in data:
            properties['Tournament Tier'] = {'select': {'name': data['tournament_tier']}}
        
        if 'surface' in data:
            properties['Surface'] = {'select': {'name': data['surface']}}
        
        # Dates
        if 'match_date' in data:
            properties['Match Date'] = {'date': {'start': self._format_date(data['match_date'])}}
        
        if 'result_date' in data:
            properties['Result Date'] = {'date': {'start': self._format_date(data['result_date'])}}
        
        if 'scan_date' in data:
            properties['Scan Date'] = {'date': {'start': self._format_date(data['scan_date'])}}
        
        # Odds Data
        if 'opening_odds_a' in data:
            properties['Opening Odds A'] = {'number': data['opening_odds_a']}
        
        if 'opening_odds_b' in data:
            properties['Opening Odds B'] = {'number': data['opening_odds_b']}
        
        if 'closing_odds_a' in data:
            properties['Closing Odds A'] = {'number': data['closing_odds_a']}
        
        if 'closing_odds_b' in data:
            properties['Closing Odds B'] = {'number': data['closing_odds_b']}
        
        if 'odds_movement' in data:
            properties['Odds Movement'] = {'number': data['odds_movement']}
        
        # Player Stats
        if 'rank_a' in data:
            properties['Rank A'] = {'number': data['rank_a']}
        
        if 'rank_b' in data:
            properties['Rank B'] = {'number': data['rank_b']}
        
        if 'rank_delta' in data:
            properties['Rank Delta'] = {'number': data['rank_delta']}
        
        if 'elo_a' in data:
            properties['ELO A'] = {'number': data['elo_a']}
        
        if 'elo_b' in data:
            properties['ELO B'] = {'number': data['elo_b']}
        
        if 'elo_delta' in data:
            properties['ELO Delta'] = {'number': data['elo_delta']}
        
        if 'age_a' in data:
            properties['Age A'] = {'number': data['age_a']}
        
        if 'age_b' in data:
            properties['Age B'] = {'number': data['age_b']}
        
        if 'form_a' in data:
            properties['Form A'] = {'rich_text': [{'text': {'content': str(data['form_a'])[:2000]}}]}
        
        if 'form_b' in data:
            properties['Form B'] = {'rich_text': [{'text': {'content': str(data['form_b'])[:2000]}}]}
        
        if 'h2h_record' in data:
            properties['H2H Record'] = {'rich_text': [{'text': {'content': str(data['h2h_record'])[:2000]}}]}
        
        # AI Predictions
        if 'gpt4_prediction' in data:
            properties['GPT-4 Prediction'] = {'select': {'name': data['gpt4_prediction']}}
        
        if 'gpt4_confidence' in data:
            properties['GPT-4 Confidence'] = {'select': {'name': data['gpt4_confidence']}}
        
        if 'gpt4_score' in data:
            properties['GPT-4 Score'] = {'number': data['gpt4_score']}
        
        if 'xgboost_probability' in data:
            properties['XGBoost Probability'] = {'number': data['xgboost_probability']}
        
        if 'lightgbm_probability' in data:
            properties['LightGBM Probability'] = {'number': data['lightgbm_probability']}
        
        if 'ensemble_score' in data:
            properties['Ensemble Score'] = {'number': data['ensemble_score']}
        
        if 'ensemble_prediction' in data:
            properties['Ensemble Prediction'] = {'select': {'name': data['ensemble_prediction']}}
        
        if 'model_agreement' in data:
            properties['Model Agreement'] = {'number': data['model_agreement']}
        
        # Betting Info
        if 'bet_placed' in data:
            properties['Bet Placed'] = {'checkbox': data['bet_placed']}
        
        if 'bet_side' in data:
            properties['Bet Side'] = {'select': {'name': data['bet_side']}}
        
        if 'bet_odds' in data:
            properties['Bet Odds'] = {'number': data['bet_odds']}
        
        if 'stake_eur' in data:
            properties['Stake EUR'] = {'number': data['stake_eur']}
        
        if 'stake_pct' in data:
            properties['Stake %'] = {'number': data['stake_pct']}
        
        if 'pnl_eur' in data:
            properties['PnL EUR'] = {'number': data['pnl_eur']}
        
        if 'clv_pct' in data:
            properties['CLV %'] = {'number': data['clv_pct']}
        
        # Meta
        if 'actual_winner' in data:
            properties['Actual Winner'] = {'select': {'name': data['actual_winner']}}
        
        if 'actual_score' in data:
            properties['Actual Score'] = {'rich_text': [{'text': {'content': str(data['actual_score'])[:2000]}}]}
        
        if 'status' in data:
            properties['Status'] = {'select': {'name': data['status']}}
        else:
            properties['Status'] = {'select': {'name': 'Scanned'}}
        
        if 'data_quality' in data:
            properties['Data Quality'] = {'checkbox': data['data_quality']}
        
        if 'source' in data:
            properties['Source'] = {'rich_text': [{'text': {'content': data['source'][:2000]}}]}
        
        if 'event_id' in data:
            properties['Event ID'] = {'rich_text': [{'text': {'content': str(data['event_id'])}}]}
        
        if 'notes' in data:
            properties['Notes'] = {'rich_text': [{'text': {'content': str(data['notes'])[:2000]}}]}
        
        return properties
    
    def _format_date(self, date_value) -> str:
        """Format date for Notion"""
        if isinstance(date_value, str):
            return date_value
        elif isinstance(date_value, datetime):
            return date_value.isoformat()
        else:
            return datetime.now().isoformat()
    
    def _is_duplicate(self, match_data: Dict[str, Any]) -> bool:
        """Check if match already exists in DB"""
        if not self.client or not self.database_id:
            return False
        
        try:
            match_name = match_data.get('match_name', '')
            event_id = match_data.get('event_id', '')
            
            # Search by match name
            if match_name:
                response = self.client.databases.query(
                    database_id=self.database_id,
                    filter={
                        "property": "Match Name",
                        "title": {"equals": match_name}
                    },
                    page_size=1
                )
                if response['results']:
                    return True
            
            # Search by event ID
            if event_id:
                response = self.client.databases.query(
                    database_id=self.database_id,
                    filter={
                        "property": "Event ID",
                        "rich_text": {"equals": str(event_id)}
                    },
                    page_size=1
                )
                if response['results']:
                    return True
            
            return False
        
        except Exception as e:
            logger.debug(f"Error checking duplicate: {e}")
            return False
    
    def update_match(self, page_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update existing match with new data
        
        Args:
            page_id: Notion page ID
            updates: Dictionary with fields to update
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            properties = self._build_properties(updates)
            self.client.pages.update(
                page_id=page_id,
                properties=properties
            )
            logger.info(f"✅ Updated match: {page_id}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Error updating match: {e}")
            return False
    
    def log_matches_batch(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Log multiple matches in batch
        
        Args:
            matches: List of match data dictionaries
            
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
            page_id = self.log_match(match)
            if page_id:
                results['created'] += 1
                results['page_ids'].append(page_id)
            elif self._is_duplicate(match):
                results['duplicates'] += 1
            else:
                results['errors'] += 1
        
        logger.info(f"✅ Batch logged: {results['created']} created, {results['duplicates']} duplicates, {results['errors']} errors")
        return results

