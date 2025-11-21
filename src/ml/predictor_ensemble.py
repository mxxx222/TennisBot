#!/usr/bin/env python3
"""
Predictor Ensemble
==================

Unified prediction interface that combines:
- GPT-4 (via AI analyzer)
- XGBoost
- LightGBM
- Meta-Learner

This is the main API for making predictions in the Self-Learning AI Engine.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ml.meta_learner import MetaLearner
from src.ml.xgboost_trainer import XGBoostTrainer
from src.ml.lightgbm_trainer import LightGBMTrainer
from src.ml.feature_store import FeatureStore
from src.scrapers.sportbex_client import SportbexMatch

logger = logging.getLogger(__name__)


class PredictorEnsemble:
    """Unified prediction interface for all models"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize predictor ensemble
        
        Args:
            db_path: Path to Match Results database
        """
        self.feature_store = FeatureStore(db_path)
        self.meta_learner = MetaLearner()
        
        # Load models
        self.xgboost_trainer = XGBoostTrainer(db_path=db_path)
        self.lightgbm_trainer = LightGBMTrainer(db_path=db_path)
        
        # Try to load trained models
        self.xgboost_loaded = self.xgboost_trainer.load_model()
        self.lightgbm_loaded = self.lightgbm_trainer.load_model()
        
        if not self.xgboost_loaded:
            logger.warning("⚠️ XGBoost model not loaded - predictions may be limited")
        if not self.lightgbm_loaded:
            logger.warning("⚠️ LightGBM model not loaded - predictions may be limited")
        
        logger.info("✅ Predictor Ensemble initialized")
    
    def predict(self,
                match: SportbexMatch,
                gpt4_pred: Optional[Dict[str, Any]] = None,
                use_lightgbm_screener: bool = True) -> Dict[str, Any]:
        """
        Make prediction for a match using ensemble
        
        Args:
            match: SportbexMatch object
            gpt4_pred: GPT-4 prediction (optional, from AI analyzer)
            use_lightgbm_screener: Whether to use LightGBM as screener first
            
        Returns:
            Combined prediction dictionary
        """
        # Step 1: LightGBM screener (fast filter)
        lightgbm_pred = None
        if use_lightgbm_screener and self.lightgbm_loaded:
            try:
                features = self.feature_store.extract_features(match)
                lightgbm_pred = self.lightgbm_trainer.predict(features)
                
                # If not interesting, return early (fast rejection)
                if lightgbm_pred and not lightgbm_pred.get('is_interesting', True):
                    logger.debug(f"Match {match.match_id} filtered by LightGBM screener")
                    return {
                        'player1_win_probability': 0.5,
                        'player2_win_probability': 0.5,
                        'confidence': 0.0,
                        'model': 'lightgbm_screener',
                        'filtered': True,
                        'reason': 'Not interesting according to LightGBM screener'
                    }
            except Exception as e:
                logger.warning(f"LightGBM prediction failed: {e}")
        
        # Step 2: Extract features
        try:
            features = self.feature_store.extract_features(match)
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return {
                'player1_win_probability': 0.5,
                'player2_win_probability': 0.5,
                'confidence': 0.0,
                'model': 'ensemble',
                'error': f'Feature extraction failed: {e}'
            }
        
        # Step 3: XGBoost prediction
        xgboost_pred = None
        if self.xgboost_loaded:
            try:
                xgboost_pred = self.xgboost_trainer.predict(features)
            except Exception as e:
                logger.warning(f"XGBoost prediction failed: {e}")
        
        # Step 4: Combine all predictions with meta-learner
        combined_pred = self.meta_learner.combine_predictions(
            gpt4_pred=gpt4_pred,
            xgboost_pred=xgboost_pred,
            lightgbm_pred=lightgbm_pred
        )
        
        # Add match information
        combined_pred['match_id'] = match.match_id
        combined_pred['player1'] = match.player1
        combined_pred['player2'] = match.player2
        combined_pred['tournament'] = match.tournament
        
        # Add recommendation if odds available
        if match.player1_odds:
            combined_pred['recommendation'] = self.meta_learner.get_recommendation(
                combined_pred, odds=match.player1_odds
            )
        elif match.player2_odds:
            # Use player2 odds as proxy
            combined_pred['recommendation'] = self.meta_learner.get_recommendation(
                combined_pred, odds=match.player2_odds
            )
        
        return combined_pred
    
    def predict_batch(self,
                      matches: List[SportbexMatch],
                      gpt4_predictions: Optional[Dict[str, Dict[str, Any]]] = None,
                      use_lightgbm_screener: bool = True) -> List[Dict[str, Any]]:
        """
        Make predictions for multiple matches
        
        Args:
            matches: List of SportbexMatch objects
            gpt4_predictions: Dictionary mapping match_id to GPT-4 prediction
            use_lightgbm_screener: Whether to use LightGBM screener
            
        Returns:
            List of prediction dictionaries
        """
        predictions = []
        
        for match in matches:
            gpt4_pred = None
            if gpt4_predictions and match.match_id in gpt4_predictions:
                gpt4_pred = gpt4_predictions[match.match_id]
            
            pred = self.predict(match, gpt4_pred=gpt4_pred, use_lightgbm_screener=use_lightgbm_screener)
            predictions.append(pred)
        
        return predictions
    
    def get_model_status(self) -> Dict[str, Any]:
        """
        Get status of all models
        
        Returns:
            Dictionary with model status
        """
        return {
            'xgboost': {
                'loaded': self.xgboost_loaded,
                'trained': self.xgboost_trainer.is_trained
            },
            'lightgbm': {
                'loaded': self.lightgbm_loaded,
                'trained': self.lightgbm_trainer.is_trained
            },
            'meta_learner': {
                'weights': self.meta_learner.weights,
                'accuracies': self.meta_learner.accuracies
            }
        }


def main():
    """Test predictor ensemble"""
    print("\n" + "="*80)
    print("🧪 TESTING PREDICTOR ENSEMBLE")
    print("="*80)
    
    ensemble = PredictorEnsemble()
    
    # Check model status
    status = ensemble.get_model_status()
    print(f"\n📊 Model Status:")
    print(f"   XGBoost: {'✅ Loaded' if status['xgboost']['loaded'] else '❌ Not loaded'}")
    print(f"   LightGBM: {'✅ Loaded' if status['lightgbm']['loaded'] else '❌ Not loaded'}")
    print(f"   Meta-Learner Weights: {status['meta_learner']['weights']}")
    
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
        surface="Hard",
        tournament_tier="W15"
    )
    
    # Make prediction
    prediction = ensemble.predict(sample_match)
    
    print(f"\n✅ Prediction:")
    print(f"   Player 1 Win Prob: {prediction['player1_win_probability']:.3f}")
    print(f"   Confidence: {prediction['confidence']:.3f}")
    print(f"   Model: {prediction['model']}")
    if 'recommendation' in prediction:
        print(f"   Recommendation: {prediction['recommendation']}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()

