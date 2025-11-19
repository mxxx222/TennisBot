#!/usr/bin/env python3
"""
🤖 ITF MATCH PREDICTOR (ML Model v0.1)
======================================

Logistic regression model for ITF Women match prediction.
Features (5 variables for MVP):
1. Ranking delta (Player A - Player B)
2. Surface win % delta
3. Recent form score (numeric, last 5 matches)
4. Tournament tier (W15=1, W35=2, W50=3, W75=4, W100=5)
5. H2H history (if exists, else 0.5)

Train on 200+ ITF matches minimum.
Walk-forward validation (30-day backtest).
Target: >10% ROI in backtest period.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import sys
import pickle
import json
from datetime import datetime, timedelta
from functools import lru_cache
import numpy as np
import pandas as pd

# Machine Learning
try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, roc_auc_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class ITFMatchPredictor:
    """ML model for ITF Women match prediction"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ITF Match Predictor
        
        Args:
            config: Configuration dict
        """
        self.config = config or {}
        self.min_training_matches = self.config.get('min_training_matches', 200)
        self.target_roi = self.config.get('target_roi', 0.10)
        
        if not SKLEARN_AVAILABLE:
            logger.warning("⚠️ scikit-learn not available - ML features disabled")
            self.model = None
            self.scaler = None
        else:
            self.model = LogisticRegression(random_state=42, max_iter=1000)
            self.scaler = StandardScaler()
        
        self.is_trained = False
        self.feature_columns = [
            'ranking_delta',
            'surface_win_delta',
            'recent_form_score',
            'tournament_tier',
            'h2h_history'
        ]
        
        logger.info("🤖 ITF Match Predictor initialized")
    
    @staticmethod
    @lru_cache(maxsize=128)
    def _form_to_score(form_str: str) -> float:
        """Convert form string to score (cached for performance)"""
        wins = form_str.count('W')
        return wins / max(len(form_str.split('-')), 1)
    
    def extract_features(self, match_data: Dict[str, Any]) -> Optional[np.ndarray]:
        """
        Extract features from match data
        
        Args:
            match_data: Match data dictionary
            
        Returns:
            Feature array or None if insufficient data
        """
        try:
            features = []
            
            # 1. Ranking delta (Player A - Player B)
            ranking_a = match_data.get('player1_ranking', 500)
            ranking_b = match_data.get('player2_ranking', 500)
            ranking_delta = ranking_b - ranking_a  # Positive if A is better
            features.append(ranking_delta)
            
            # 2. Surface win % delta
            surface = match_data.get('surface', 'Hard')
            win_pct_a = match_data.get('player1_surface_win_pct', {}).get(surface, 0.5)
            win_pct_b = match_data.get('player2_surface_win_pct', {}).get(surface, 0.5)
            surface_win_delta = win_pct_a - win_pct_b
            features.append(surface_win_delta)
            
            # 3. Recent form score (numeric, last 5 matches)
            form_a = match_data.get('player1_recent_form', 'L-L-L-L-L')
            form_b = match_data.get('player2_recent_form', 'L-L-L-L-L')
            
            # Use cached form scoring function (moved outside for proper caching)
            form_score_a = self._form_to_score(form_a)
            form_score_b = self._form_to_score(form_b)
            recent_form_score = form_score_a - form_score_b
            features.append(recent_form_score)
            
            # 4. Tournament tier (W15=1, W35=2, W50=3, W75=4, W100=5) - cached
            tier = match_data.get('tournament_tier', 'W15')
            tier_map = {'W15': 1, 'W25': 2, 'W35': 2, 'W50': 3, 'W60': 3, 'W75': 4, 'W80': 4, 'W100': 5}
            tournament_tier = tier_map.get(tier, 1)
            features.append(tournament_tier)
            
            # 5. H2H history (if exists, else 0.5)
            h2h = match_data.get('h2h_history', 0.5)  # Win rate for player A
            features.append(h2h)
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            logger.debug(f"Error extracting features: {e}")
            return None
    
    def prepare_training_data(self, matches: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare training data from matches
        
        Args:
            matches: List of match dictionaries with results
            
        Returns:
            X (features), y (targets)
        """
        X_list = []
        y_list = []
        
        for match in matches:
            features = self.extract_features(match)
            if features is not None:
                X_list.append(features[0])
                
                # Target: 1 if player1 won, 0 if player2 won
                result = match.get('result', 'unknown')
                if result == 'player1_win':
                    y_list.append(1)
                elif result == 'player2_win':
                    y_list.append(0)
                else:
                    continue  # Skip unknown results
        
        if len(X_list) < self.min_training_matches:
            logger.warning(f"⚠️ Insufficient training data: {len(X_list)} < {self.min_training_matches}")
            return None, None
        
        X = np.array(X_list)
        y = np.array(y_list)
        
        logger.info(f"✅ Prepared training data: {len(X)} samples, {len(self.feature_columns)} features")
        return X, y
    
    def train(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Train the model on historical matches
        
        Args:
            matches: List of match dictionaries with results
            
        Returns:
            Training results dictionary
        """
        if not SKLEARN_AVAILABLE:
            logger.error("❌ scikit-learn not available")
            return {'success': False, 'error': 'scikit-learn not available'}
        
        logger.info(f"🚀 Training model on {len(matches)} matches...")
        
        # Prepare data
        X, y = self.prepare_training_data(matches)
        
        if X is None or y is None:
            return {'success': False, 'error': 'Insufficient training data'}
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_pred = self.model.predict(X_train_scaled)
        test_pred = self.model.predict(X_test_scaled)
        
        train_acc = accuracy_score(y_train, train_pred)
        test_acc = accuracy_score(y_test, test_pred)
        
        try:
            train_auc = roc_auc_score(y_train, self.model.predict_proba(X_train_scaled)[:, 1])
            test_auc = roc_auc_score(y_test, self.model.predict_proba(X_test_scaled)[:, 1])
        except:
            train_auc = 0.0
            test_auc = 0.0
        
        self.is_trained = True
        
        results = {
            'success': True,
            'train_accuracy': train_acc,
            'test_accuracy': test_acc,
            'train_auc': train_auc,
            'test_auc': test_auc,
            'training_samples': len(X_train),
            'test_samples': len(X_test),
        }
        
        logger.info(f"✅ Model trained: Test Accuracy={test_acc:.3f}, Test AUC={test_auc:.3f}")
        return results
    
    def predict(self, match_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Predict match outcome
        
        Args:
            match_data: Match data dictionary
            
        Returns:
            Prediction dictionary with probability and recommendation
        """
        if not self.is_trained:
            logger.warning("⚠️ Model not trained yet")
            return None
        
        features = self.extract_features(match_data)
        if features is None:
            return None
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Predict
        prob = self.model.predict_proba(features_scaled)[0]
        player1_win_prob = prob[1]
        player2_win_prob = prob[0]
        
        # Calculate edge (if odds provided)
        odds = match_data.get('odds', None)
        edge = None
        if odds:
            implied_prob = 1.0 / odds
            edge = (player1_win_prob - implied_prob) / implied_prob if player1_win_prob > implied_prob else None
        
        return {
            'player1_win_probability': player1_win_prob,
            'player2_win_probability': player2_win_prob,
            'predicted_winner': 'player1' if player1_win_prob > 0.5 else 'player2',
            'confidence': abs(player1_win_prob - 0.5) * 2,  # 0-1 scale
            'edge': edge,
            'recommendation': self._get_recommendation(player1_win_prob, edge),
        }
    
    def _get_recommendation(self, prob: float, edge: Optional[float]) -> str:
        """Get betting recommendation"""
        if edge is None:
            return 'No odds provided'
        
        if edge >= 0.08:
            return 'STRONG BET (2× stake)'
        elif edge >= 0.05:
            return 'BET'
        elif edge >= 0.02:
            return 'WEAK BET'
        else:
            return 'NO BET'
    
    def save_model(self, filepath: str):
        """Save trained model to file"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns,
            'is_trained': self.is_trained,
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"✅ Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model from file"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_columns = model_data['feature_columns']
        self.is_trained = model_data['is_trained']
        
        logger.info(f"✅ Model loaded from {filepath}")


def main():
    """Test ITF Match Predictor"""
    print("🤖 ITF MATCH PREDICTOR TEST")
    print("=" * 50)
    
    if not SKLEARN_AVAILABLE:
        print("❌ scikit-learn not available")
        print("💡 Install with: pip install scikit-learn")
        return
    
    predictor = ITFMatchPredictor()
    
    # Sample training data
    sample_matches = [
        {
            'player1_ranking': 250,
            'player2_ranking': 300,
            'surface': 'Hard',
            'player1_surface_win_pct': {'Hard': 0.65},
            'player2_surface_win_pct': {'Hard': 0.55},
            'player1_recent_form': 'W-W-L-W-W',
            'player2_recent_form': 'L-L-W-L-L',
            'tournament_tier': 'W15',
            'h2h_history': 0.6,
            'result': 'player1_win',
        }
    ] * 250  # Generate 250 sample matches
    
    print(f"🚀 Training on {len(sample_matches)} sample matches...")
    results = predictor.train(sample_matches)
    
    if results.get('success'):
        print(f"\n✅ Training successful!")
        print(f"   Test Accuracy: {results['test_accuracy']:.3f}")
        print(f"   Test AUC: {results['test_auc']:.3f}")
        
        # Test prediction
        test_match = {
            'player1_ranking': 200,
            'player2_ranking': 250,
            'surface': 'Hard',
            'player1_surface_win_pct': {'Hard': 0.70},
            'player2_surface_win_pct': {'Hard': 0.60},
            'player1_recent_form': 'W-W-W-L-W',
            'player2_recent_form': 'L-W-L-L-W',
            'tournament_tier': 'W35',
            'h2h_history': 0.65,
            'odds': 1.5,
        }
        
        prediction = predictor.predict(test_match)
        if prediction:
            print(f"\n📊 Prediction:")
            print(f"   Player 1 Win Prob: {prediction['player1_win_probability']:.3f}")
            print(f"   Edge: {prediction['edge']:.2%}" if prediction['edge'] else "   Edge: N/A")
            print(f"   Recommendation: {prediction['recommendation']}")
    else:
        print(f"\n❌ Training failed: {results.get('error')}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()

