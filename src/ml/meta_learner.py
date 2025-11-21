#!/usr/bin/env python3
"""
Meta-Learner
============

Combines 3 models optimally:
- GPT-4 (slow, expensive, smart) → top 20% candidates
- XGBoost (fast, accurate, systematic) → all candidates
- LightGBM (ultra-fast screener) → first filter

Weights update automatically (accuracy-based).
Agreement bonus when models agree.

This is Layer 4 of the Self-Learning AI Engine.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ml.xgboost_trainer import XGBoostTrainer
from src.ml.lightgbm_trainer import LightGBMTrainer

logger = logging.getLogger(__name__)


class MetaLearner:
    """Combines multiple models with dynamic weights"""
    
    def __init__(self, weights_path: Optional[str] = None):
        """
        Initialize meta-learner
        
        Args:
            weights_path: Path to weights JSON file
        """
        if weights_path is None:
            weights_path = Path(__file__).parent.parent.parent / 'data' / 'models' / 'meta_learner_weights.json'
        self.weights_path = Path(weights_path)
        self.weights_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize model trainers
        self.xgboost_trainer = XGBoostTrainer()
        self.lightgbm_trainer = LightGBMTrainer()
        
        # Default weights (will be updated based on accuracy)
        self.weights = {
            'gpt4': 0.4,      # High weight for smart model
            'xgboost': 0.4,   # High weight for accurate model
            'lightgbm': 0.2   # Lower weight for screener
        }
        
        # Model accuracies (for weight adjustment)
        self.accuracies = {
            'gpt4': 0.65,     # Baseline accuracy
            'xgboost': 0.70,  # Expected accuracy
            'lightgbm': 0.60  # Screener accuracy
        }
        
        # Agreement bonus multiplier
        self.agreement_bonus = 1.15  # 15% boost when all models agree
        
        # Load weights if available
        self.load_weights()
        
        logger.info("✅ Meta-Learner initialized")
    
    def load_weights(self):
        """Load weights from file"""
        if not self.weights_path.exists():
            logger.info("No weights file found - using defaults")
            return
        
        try:
            with open(self.weights_path, 'r') as f:
                data = json.load(f)
                self.weights = data.get('weights', self.weights)
                self.accuracies = data.get('accuracies', self.accuracies)
                self.agreement_bonus = data.get('agreement_bonus', self.agreement_bonus)
            
            logger.info(f"✅ Loaded weights from {self.weights_path}")
            
        except Exception as e:
            logger.warning(f"Error loading weights: {e} - using defaults")
    
    def save_weights(self):
        """Save weights to file"""
        try:
            data = {
                'weights': self.weights,
                'accuracies': self.accuracies,
                'agreement_bonus': self.agreement_bonus,
                'updated_at': datetime.now().isoformat()
            }
            
            with open(self.weights_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"✅ Saved weights to {self.weights_path}")
            
        except Exception as e:
            logger.error(f"Error saving weights: {e}")
    
    def update_weights_from_accuracy(self, model_name: str, accuracy: float, window_days: int = 30):
        """
        Update model weights based on recent accuracy
        
        Args:
            model_name: Model name ('gpt4', 'xgboost', 'lightgbm')
            accuracy: Recent accuracy (0-1)
            window_days: Time window for accuracy calculation
        """
        if model_name not in self.weights:
            logger.warning(f"Unknown model: {model_name}")
            return
        
        # Update accuracy
        self.accuracies[model_name] = accuracy
        
        # Normalize weights based on accuracies
        total_accuracy = sum(self.accuracies.values())
        if total_accuracy > 0:
            for model in self.weights.keys():
                self.weights[model] = self.accuracies[model] / total_accuracy
        
        # Normalize to sum to 1.0
        total_weight = sum(self.weights.values())
        if total_weight > 0:
            for model in self.weights.keys():
                self.weights[model] = self.weights[model] / total_weight
        
        logger.info(f"✅ Updated weights: {self.weights}")
        self.save_weights()
    
    def combine_predictions(self,
                           gpt4_pred: Optional[Dict[str, Any]],
                           xgboost_pred: Optional[Dict[str, Any]],
                           lightgbm_pred: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Combine predictions from all models
        
        Args:
            gpt4_pred: GPT-4 prediction (optional)
            xgboost_pred: XGBoost prediction (optional)
            lightgbm_pred: LightGBM prediction (optional)
            
        Returns:
            Combined prediction dictionary
        """
        predictions = []
        weights = []
        
        # Collect available predictions
        if gpt4_pred:
            prob = gpt4_pred.get('player1_win_probability', 0.5)
            predictions.append(prob)
            weights.append(self.weights['gpt4'])
        
        if xgboost_pred:
            prob = xgboost_pred.get('player1_win_probability', 0.5)
            predictions.append(prob)
            weights.append(self.weights['xgboost'])
        
        if lightgbm_pred:
            # LightGBM gives "interesting" probability, convert to win probability
            interesting_prob = lightgbm_pred.get('interesting_probability', 0.5)
            # Use as confidence indicator, not direct win probability
            # If interesting, slightly favor player1 (assuming better odds)
            prob = 0.5 + (interesting_prob - 0.5) * 0.2  # Scale to small adjustment
            predictions.append(prob)
            weights.append(self.weights['lightgbm'])
        
        if not predictions:
            logger.warning("No predictions available")
            return {
                'player1_win_probability': 0.5,
                'player2_win_probability': 0.5,
                'confidence': 0.0,
                'model': 'meta_learner',
                'error': 'No predictions available'
            }
        
        # Normalize weights
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        
        # Weighted average
        combined_prob = sum(p * w for p, w in zip(predictions, weights))
        
        # Check for agreement (all predictions agree on direction)
        if len(predictions) >= 2:
            all_above_50 = all(p > 0.5 for p in predictions)
            all_below_50 = all(p < 0.5 for p in predictions)
            
            if all_above_50 or all_below_50:
                # Models agree - apply bonus
                agreement_strength = min(abs(p - 0.5) for p in predictions)
                bonus = 1.0 + (self.agreement_bonus - 1.0) * agreement_strength
                
                if all_above_50:
                    combined_prob = min(0.95, combined_prob * bonus)
                else:
                    combined_prob = max(0.05, combined_prob / bonus)
        
        player2_prob = 1.0 - combined_prob
        confidence = abs(combined_prob - 0.5) * 2
        
        # Determine which models contributed
        contributing_models = []
        if gpt4_pred:
            contributing_models.append('gpt4')
        if xgboost_pred:
            contributing_models.append('xgboost')
        if lightgbm_pred:
            contributing_models.append('lightgbm')
        
        return {
            'player1_win_probability': combined_prob,
            'player2_win_probability': player2_prob,
            'predicted_winner': 'player1' if combined_prob > 0.5 else 'player2',
            'confidence': confidence,
            'model': 'meta_learner',
            'contributing_models': contributing_models,
            'weights_used': {
                'gpt4': self.weights['gpt4'] if gpt4_pred else 0,
                'xgboost': self.weights['xgboost'] if xgboost_pred else 0,
                'lightgbm': self.weights['lightgbm'] if lightgbm_pred else 0
            }
        }
    
    def get_recommendation(self, combined_pred: Dict[str, Any], odds: Optional[float] = None) -> str:
        """
        Get betting recommendation from combined prediction
        
        Args:
            combined_pred: Combined prediction dictionary
            odds: Betting odds (optional)
            
        Returns:
            Recommendation string
        """
        prob = combined_pred['player1_win_probability']
        confidence = combined_pred['confidence']
        
        if odds:
            implied_prob = 1.0 / odds
            edge = (prob - implied_prob) / implied_prob if prob > implied_prob else None
            
            if edge and edge >= 0.08 and confidence >= 0.6:
                return 'STRONG BET (2× stake)'
            elif edge and edge >= 0.05 and confidence >= 0.5:
                return 'BET'
            elif edge and edge >= 0.02:
                return 'WEAK BET'
            else:
                return 'NO BET'
        else:
            if confidence >= 0.7:
                return 'HIGH CONFIDENCE'
            elif confidence >= 0.5:
                return 'MEDIUM CONFIDENCE'
            else:
                return 'LOW CONFIDENCE'


def main():
    """Test meta-learner"""
    print("\n" + "="*80)
    print("🧪 TESTING META-LEARNER")
    print("="*80)
    
    meta = MetaLearner()
    
    # Sample predictions
    gpt4_pred = {
        'player1_win_probability': 0.65,
        'confidence': 0.7
    }
    
    xgboost_pred = {
        'player1_win_probability': 0.68,
        'confidence': 0.6
    }
    
    lightgbm_pred = {
        'interesting_probability': 0.75,
        'is_interesting': True
    }
    
    # Combine predictions
    combined = meta.combine_predictions(gpt4_pred, xgboost_pred, lightgbm_pred)
    
    print(f"\n✅ Combined Prediction:")
    print(f"   Player 1 Win Prob: {combined['player1_win_probability']:.3f}")
    print(f"   Confidence: {combined['confidence']:.3f}")
    print(f"   Contributing Models: {', '.join(combined['contributing_models'])}")
    
    # Get recommendation
    recommendation = meta.get_recommendation(combined, odds=1.65)
    print(f"   Recommendation: {recommendation}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()

