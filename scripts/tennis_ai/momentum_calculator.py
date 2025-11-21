#!/usr/bin/env python3
"""
🔥 MOMENTUM CALCULATOR
======================

Calculates Momentum Score, Hot Hand flags, and Rising Talent detection
by combining ELO changes, win streaks, and other metrics.

Features:
- Calculates Momentum Score (0-100 composite metric)
- Sets Hot Hand flag (Momentum > 60)
- Sets Rising Talent flag (ELO Change 30D > 50 OR 7D > 30)
- Sets Breakthrough Date (when Rising Talent first detected)
- Integrates ML model for AI Win Probability
- Calculates Market Edge % (AI vs market odds)
- Updates Player Cards DB in Notion
"""

import os
import sys
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
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

# ML Model
try:
    from src.ml.itf_match_predictor import ITFMatchPredictor
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logger.warning("⚠️ ML model not available")


class MomentumCalculator:
    """
    Calculates momentum metrics for players
    """
    
    def __init__(self, 
                 player_cards_db_id: Optional[str] = None,
                 prematch_db_id: Optional[str] = None):
        """
        Initialize calculator
        
        Args:
            player_cards_db_id: Player Cards database ID (optional, from env)
            prematch_db_id: Tennis Prematch database ID (optional, from env)
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
        self.player_cards_db_id = (
            player_cards_db_id or 
            os.getenv('NOTION_ITF_PLAYER_CARDS_DB_ID') or 
            os.getenv('PLAYER_CARDS_DB_ID')
        )
        self.prematch_db_id = (
            prematch_db_id or 
            os.getenv('NOTION_TENNIS_PREMATCH_DB_ID') or 
            os.getenv('NOTION_PREMATCH_DB_ID')
        )
        
        if not self.player_cards_db_id:
            logger.error("❌ Player Cards database ID not set")
        
        # Initialize ML model (optional)
        self.ml_predictor = None
        if ML_AVAILABLE:
            try:
                self.ml_predictor = ITFMatchPredictor()
                # Try to load trained model
                model_path = project_root / 'data' / 'models' / 'logistic_regression_model.pkl'
                if model_path.exists():
                    self.ml_predictor.load_model(str(model_path))
                    logger.info("✅ ML model loaded")
                else:
                    logger.warning("⚠️ ML model file not found, predictions disabled")
                    self.ml_predictor = None
            except Exception as e:
                logger.warning(f"⚠️ Could not load ML model: {e}")
                self.ml_predictor = None
        
        logger.info("🔥 Momentum Calculator initialized")
    
    def get_player_data(self, player_card_id: str) -> Dict[str, Any]:
        """
        Get player data from Player Card
        
        Args:
            player_card_id: Player Card page ID
            
        Returns:
            Dictionary with player data
        """
        if not self.client or not self.player_cards_db_id:
            return {}
        
        try:
            page = self.client.pages.retrieve(page_id=player_card_id)
            props = page.get('properties', {})
            
            # Extract relevant properties
            data = {
                'id': player_card_id,
                'elo': self._get_number_prop(props, 'ELO'),
                'elo_change_7d': self._get_number_prop(props, 'ELO Change 7D'),
                'elo_change_30d': self._get_number_prop(props, 'ELO Change 30D'),
                'elo_change_90d': self._get_number_prop(props, 'ELO Change 90D'),
                'win_streak': self._get_number_prop(props, 'Win Streak') or 0,
                'ranking': self._get_number_prop(props, 'Ranking') or self._get_number_prop(props, 'WTA Ranking'),
                'rising_talent': self._get_checkbox_prop(props, 'Rising Talent'),
                'breakthrough_date': self._get_date_prop(props, 'Breakthrough Date'),
                'momentum_score': self._get_number_prop(props, 'Momentum Score'),
                'hot_hand': self._get_checkbox_prop(props, 'Hot Hand'),
            }
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Error getting player data for {player_card_id}: {e}")
            return {}
    
    def calculate_momentum_score(self, player_data: Dict[str, Any]) -> float:
        """
        Calculate Momentum Score (0-100)
        
        Formula: (ELO_change_30d * 2) + (Win_streak * 10) + (Ranking_improvement * 0.5)
        
        Args:
            player_data: Player data dictionary
            
        Returns:
            Momentum Score (0-100)
        """
        # Get ELO change 30D (default to 0 if not available)
        elo_change_30d = player_data.get('elo_change_30d', 0) or 0
        
        # Get win streak (default to 0)
        win_streak = player_data.get('win_streak', 0) or 0
        
        # Get ranking improvement (for now, assume 0 - would need historical ranking data)
        ranking_improvement = 0  # TODO: Calculate ranking improvement
        
        # Calculate momentum score
        momentum = (elo_change_30d * 2) + (win_streak * 10) + (ranking_improvement * 0.5)
        
        # Cap at 0-100 range
        momentum = max(0, min(100, momentum))
        
        return round(momentum, 1)
    
    def detect_rising_talent(self, player_data: Dict[str, Any]) -> bool:
        """
        Detect if player is Rising Talent
        
        Criteria: ELO Change 30D > 50 OR ELO Change 7D > 30
        
        Args:
            player_data: Player data dictionary
            
        Returns:
            True if Rising Talent
        """
        elo_change_30d = player_data.get('elo_change_30d', 0) or 0
        elo_change_7d = player_data.get('elo_change_7d', 0) or 0
        
        return (elo_change_30d > 50) or (elo_change_7d > 30)
    
    def should_set_breakthrough_date(self, player_data: Dict[str, Any], is_rising_talent: bool) -> bool:
        """
        Determine if Breakthrough Date should be set
        
        Set when Rising Talent becomes True for the first time
        
        Args:
            player_data: Player data dictionary
            is_rising_talent: Current Rising Talent status
            
        Returns:
            True if Breakthrough Date should be set
        """
        # Only set if becoming Rising Talent for the first time
        was_rising_talent = player_data.get('rising_talent', False)
        has_breakthrough_date = player_data.get('breakthrough_date') is not None
        
        return is_rising_talent and not was_rising_talent and not has_breakthrough_date
    
    def calculate_ai_win_probability(self, player_card_id: str) -> Optional[float]:
        """
        Calculate AI Win Probability using ML model
        
        Note: This is a placeholder - would need match data for prediction
        
        Args:
            player_card_id: Player Card page ID
            
        Returns:
            AI Win Probability (0-100) or None
        """
        if not self.ml_predictor or not self.ml_predictor.is_trained:
            return None
        
        # TODO: Get upcoming matches for player and predict
        # For now, return None (would need match context)
        return None
    
    def calculate_market_edge(self, ai_probability: Optional[float], market_odds: Optional[float]) -> Optional[float]:
        """
        Calculate Market Edge % (AI probability vs market odds)
        
        Args:
            ai_probability: AI Win Probability (0-100)
            market_odds: Market odds (e.g., 1.50)
            
        Returns:
            Market Edge % or None
        """
        if ai_probability is None or market_odds is None:
            return None
        
        # Convert AI probability to decimal (0-1)
        ai_prob_decimal = ai_probability / 100.0
        
        # Calculate implied probability from odds
        implied_prob = 1.0 / market_odds
        
        # Calculate edge
        edge = (ai_prob_decimal - implied_prob) / implied_prob * 100.0
        
        return round(edge, 2)
    
    def update_player_momentum(self, player_card_id: str) -> bool:
        """
        Calculate and update momentum metrics for a player
        
        Args:
            player_card_id: Player Card page ID
            
        Returns:
            True if successful
        """
        if not self.client or not self.player_cards_db_id:
            return False
        
        try:
            # Get player data
            player_data = self.get_player_data(player_card_id)
            if not player_data:
                return False
            
            # Calculate metrics
            momentum_score = self.calculate_momentum_score(player_data)
            is_rising_talent = self.detect_rising_talent(player_data)
            is_hot_hand = momentum_score > 60
            should_set_breakthrough = self.should_set_breakthrough_date(player_data, is_rising_talent)
            
            # Build update properties
            properties = {
                'Momentum Score': {
                    'number': momentum_score
                },
                'Hot Hand': {
                    'checkbox': is_hot_hand
                },
                'Rising Talent': {
                    'checkbox': is_rising_talent
                }
            }
            
            # Set Breakthrough Date if needed
            if should_set_breakthrough:
                properties['Breakthrough Date'] = {
                    'date': {'start': datetime.now().isoformat()}
                }
            
            # TODO: Update AI Win Probability and Market Edge when match data available
            
            # Update page
            self.client.pages.update(
                page_id=player_card_id,
                properties=properties
            )
            
            logger.debug(f"✅ Updated momentum for {player_card_id[:8]}...: Score={momentum_score}, Rising={is_rising_talent}, Hot={is_hot_hand}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating momentum for {player_card_id}: {e}")
            return False
    
    def update_all_players(self, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Update momentum for all players in Player Cards DB
        
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
            
            logger.info(f"🔥 Calculating momentum for {len(players)} players...")
            
            updated_count = 0
            failed_count = 0
            
            for i, player in enumerate(players, 1):
                player_id = player.get('id')
                
                # Rate limiting (3 req/s max)
                if i % 3 == 0:
                    time.sleep(1)
                
                if self.update_player_momentum(player_id):
                    updated_count += 1
                    if i % 10 == 0:
                        logger.info(f"[{i}/{len(players)}] Processed {i} players...")
                else:
                    failed_count += 1
            
            logger.info(f"\n✅ Momentum calculation complete!")
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
    
    # Helper methods for Notion properties
    def _get_number_prop(self, props: Dict, prop_name: str) -> Optional[float]:
        """Get number property from Notion props"""
        prop = props.get(prop_name, {})
        if prop.get('number') is not None:
            return prop['number']
        return None
    
    def _get_checkbox_prop(self, props: Dict, prop_name: str) -> bool:
        """Get checkbox property from Notion props"""
        prop = props.get(prop_name, {})
        if prop.get('checkbox'):
            return prop['checkbox']
        return False
    
    def _get_date_prop(self, props: Dict, prop_name: str) -> Optional[datetime]:
        """Get date property from Notion props"""
        prop = props.get(prop_name, {})
        if prop.get('date'):
            date_str = prop['date'].get('start')
            if date_str:
                try:
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except:
                    pass
        return None


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Momentum Calculator')
    parser.add_argument('--player-id', help='Specific player card ID to update')
    parser.add_argument('--limit', type=int, help='Limit number of players')
    parser.add_argument('--all', action='store_true', help='Update all players')
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    calculator = MomentumCalculator()
    
    if not calculator.client:
        logger.error("❌ Calculator not initialized")
        return
    
    if args.player_id:
        # Update specific player
        calculator.update_player_momentum(args.player_id)
    elif args.all:
        # Update all players
        calculator.update_all_players(limit=args.limit)
    else:
        logger.info("ℹ️ Use --player-id to update specific player or --all to update all players")


if __name__ == "__main__":
    main()

