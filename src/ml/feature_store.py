#!/usr/bin/env python3
"""
Feature Store
=============

Extracts 30+ rich features per match for ML training.
Features: Rank delta, ELO, form, surface, H2H, etc.

This is Layer 2 of the Self-Learning AI Engine.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ml.data_collector import MatchResultsDB
from src.scrapers.sportbex_client import SportbexMatch

logger = logging.getLogger(__name__)


class FeatureStore:
    """Extracts and stores features for ML training"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize feature store
        
        Args:
            db_path: Path to Match Results database
        """
        self.db = MatchResultsDB(db_path)
        self.feature_version = 1
    
    def extract_features(self, match: SportbexMatch, match_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extract 30+ features from match data
        
        Args:
            match: SportbexMatch object
            match_data: Additional match data from database (optional)
            
        Returns:
            Dictionary of features
        """
        features = {}
        
        # Basic match features
        features['tournament_tier_encoded'] = self._encode_tournament_tier(match.tournament_tier)
        features['surface_encoded'] = self._encode_surface(match.surface)
        
        # Ranking features
        features['player1_ranking'] = match.player1_ranking or 500
        features['player2_ranking'] = match.player2_ranking or 500
        features['ranking_delta'] = (match.player2_ranking or 500) - (match.player1_ranking or 500)
        features['ranking_advantage'] = 1 if (match.player1_ranking or 500) < (match.player2_ranking or 500) else 0
        features['ranking_ratio'] = (match.player1_ranking or 500) / max((match.player2_ranking or 500), 1)
        
        # Odds features
        features['player1_odds'] = match.player1_odds or 2.0
        features['player2_odds'] = match.player2_odds or 2.0
        features['odds_delta'] = (match.player2_odds or 2.0) - (match.player1_odds or 2.0)
        features['implied_prob_player1'] = 1.0 / (match.player1_odds or 2.0) if match.player1_odds else 0.5
        features['implied_prob_player2'] = 1.0 / (match.player2_odds or 2.0) if match.player2_odds else 0.5
        features['odds_favorite'] = 1 if (match.player1_odds or 2.0) < (match.player2_odds or 2.0) else 0
        
        # Time features
        if match.commence_time:
            features['hour_of_day'] = match.commence_time.hour
            features['day_of_week'] = match.commence_time.weekday()
            features['is_weekend'] = 1 if match.commence_time.weekday() >= 5 else 0
        else:
            features['hour_of_day'] = 14  # Default: afternoon
            features['day_of_week'] = 2   # Default: Wednesday
            features['is_weekend'] = 0
        
        # Historical features (if available from match_data)
        if match_data:
            # These would come from additional API calls or database
            features['player1_recent_form'] = match_data.get('player1_recent_form', 0.5)
            features['player2_recent_form'] = match_data.get('player2_recent_form', 0.5)
            features['form_delta'] = features['player1_recent_form'] - features['player2_recent_form']
            
            features['player1_surface_win_pct'] = match_data.get('player1_surface_win_pct', 0.5)
            features['player2_surface_win_pct'] = match_data.get('player2_surface_win_pct', 0.5)
            features['surface_win_delta'] = features['player1_surface_win_pct'] - features['player2_surface_win_pct']
            
            features['h2h_player1_wins'] = match_data.get('h2h_player1_wins', 0)
            features['h2h_player2_wins'] = match_data.get('h2h_player2_wins', 0)
            features['h2h_total'] = features['h2h_player1_wins'] + features['h2h_player2_wins']
            features['h2h_ratio'] = (
                features['h2h_player1_wins'] / max(features['h2h_total'], 1)
                if features['h2h_total'] > 0 else 0.5
            )
            
            features['player1_elo'] = match_data.get('player1_elo', 1500)
            features['player2_elo'] = match_data.get('player2_elo', 1500)
            features['elo_delta'] = features['player1_elo'] - features['player2_elo']
            features['elo_advantage'] = 1 if features['elo_delta'] > 0 else 0
        else:
            # Default values if historical data not available
            features['player1_recent_form'] = 0.5
            features['player2_recent_form'] = 0.5
            features['form_delta'] = 0.0
            features['player1_surface_win_pct'] = 0.5
            features['player2_surface_win_pct'] = 0.5
            features['surface_win_delta'] = 0.0
            features['h2h_player1_wins'] = 0
            features['h2h_player2_wins'] = 0
            features['h2h_total'] = 0
            features['h2h_ratio'] = 0.5
            features['player1_elo'] = 1500
            features['player2_elo'] = 0
            features['elo_delta'] = 0.0
            features['elo_advantage'] = 0
        
        # Derived features
        features['ranking_vs_odds'] = features['ranking_delta'] * features['odds_delta']
        features['form_vs_odds'] = features['form_delta'] * features['odds_delta']
        features['surface_vs_odds'] = features['surface_win_delta'] * features['odds_delta']
        
        # Interaction features
        features['ranking_form_interaction'] = features['ranking_delta'] * features['form_delta']
        features['ranking_surface_interaction'] = features['ranking_delta'] * features['surface_win_delta']
        features['form_surface_interaction'] = features['form_delta'] * features['surface_win_delta']
        
        # Tournament tier interactions
        features['tier_ranking_interaction'] = features['tournament_tier_encoded'] * features['ranking_delta']
        features['tier_surface_interaction'] = features['tournament_tier_encoded'] * features['surface_encoded']
        
        # Total features: 30+
        return features
    
    def _encode_tournament_tier(self, tier: Optional[str]) -> int:
        """Encode tournament tier as integer"""
        if not tier:
            return 1
        
        tier_map = {
            'W15': 1,
            'W25': 2,
            'W35': 3,
            'W50': 4,
            'W60': 5,
            'W75': 6,
            'W80': 7,
            'W100': 8,
            'CHALLENGER': 9,
            'ATP': 10
        }
        
        tier_upper = tier.upper()
        for key, value in tier_map.items():
            if key in tier_upper:
                return value
        
        return 1  # Default: W15
    
    def _encode_surface(self, surface: Optional[str]) -> int:
        """Encode surface as integer"""
        if not surface:
            return 0  # Unknown
        
        surface_map = {
            'hard': 1,
            'clay': 2,
            'grass': 3,
            'carpet': 4
        }
        
        surface_lower = surface.lower()
        return surface_map.get(surface_lower, 0)
    
    def store_features(self, match_id: str, features: Dict[str, Any]) -> bool:
        """
        Store features in database
        
        Args:
            match_id: Match ID
            features: Feature dictionary
            
        Returns:
            True if successful
        """
        try:
            import sqlite3
            from pathlib import Path
            
            db_path = self.db.db_path
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            features_json = json.dumps(features)
            
            cursor.execute("""
                INSERT OR REPLACE INTO features (
                    match_id, features_json, feature_version, updated_at
                ) VALUES (?, ?, ?, ?)
            """, (
                match_id,
                features_json,
                self.feature_version,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"✅ Stored features for match {match_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing features for {match_id}: {e}")
            return False
    
    def get_features(self, match_id: str) -> Optional[Dict[str, Any]]:
        """
        Get features for a match
        
        Args:
            match_id: Match ID
            
        Returns:
            Feature dictionary or None
        """
        try:
            import sqlite3
            
            db_path = self.db.db_path
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            cursor.execute("SELECT features_json FROM features WHERE match_id = ?", (match_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return json.loads(row[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting features for {match_id}: {e}")
            return None
    
    def get_training_features(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get features for all matches with results (for training)
        
        Args:
            limit: Maximum number of records
            
        Returns:
            List of feature dictionaries with results
        """
        training_data = self.db.get_training_data(limit=limit)
        
        features_list = []
        for match_data in training_data:
            match_id = match_data['match_id']
            
            # Get stored features
            features = self.get_features(match_id)
            
            if not features:
                # Extract features on the fly if not stored
                # This would require reconstructing SportbexMatch object
                continue
            
            # Add target variable (result)
            features['target'] = 1 if match_data.get('player1_won') else 0
            features['match_id'] = match_id
            
            features_list.append(features)
        
        return features_list
    
    def get_feature_names(self) -> List[str]:
        """
        Get list of feature names (for model training)
        
        Returns:
            List of feature names
        """
        # Return all feature names except target and match_id
        sample_features = self.extract_features(
            SportbexMatch(
                match_id="sample",
                tournament="ITF W15",
                player1="Player A",
                player2="Player B"
            )
        )
        
        feature_names = [k for k in sample_features.keys() if k not in ['target', 'match_id']]
        return sorted(feature_names)


def main():
    """Test feature store"""
    print("\n" + "="*80)
    print("🧪 TESTING FEATURE STORE")
    print("="*80)
    
    store = FeatureStore()
    
    # Create sample match
    sample_match = SportbexMatch(
        match_id="test_1",
        tournament="ITF W15 Test",
        player1="Player A",
        player2="Player B",
        player1_ranking=200,
        player2_ranking=300,
        player1_odds=1.65,
        player2_odds=2.20,
        commence_time=datetime.now(),
        surface="Hard",
        tournament_tier="W15"
    )
    
    # Extract features
    features = store.extract_features(sample_match)
    
    print(f"\n✅ Extracted {len(features)} features:")
    for key, value in sorted(features.items()):
        print(f"   {key}: {value}")
    
    # Store features
    if store.store_features("test_1", features):
        print("\n✅ Features stored successfully")
    
    # Retrieve features
    retrieved = store.get_features("test_1")
    if retrieved:
        print(f"✅ Retrieved {len(retrieved)} features")
    
    # Get feature names
    feature_names = store.get_feature_names()
    print(f"\n📊 Feature names ({len(feature_names)}):")
    for name in feature_names:
        print(f"   - {name}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()

