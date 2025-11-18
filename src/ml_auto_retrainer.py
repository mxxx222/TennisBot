#!/usr/bin/env python3
"""
🔄 ML AUTO-RETRAINER
===================
Automatically retrains ML models using calibration data from virtual bets.
Implements incremental learning and model weight adjustment based on performance.

Author: TennisBot Auto-Retraining System
Version: 1.0.0
"""

import logging
import sqlite3
import numpy as np
import pandas as pd
import pickle
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add project paths
sys.path.append(str(Path(__file__).parent.parent))

from src.virtual_betting_tracker import VirtualBettingTracker
from src.ml_calibration_engine import CalibrationEngine
from src.ai_predictor_enhanced import EnhancedTennisPredictor

logger = logging.getLogger(__name__)

class MLAutoRetrainer:
    """Automatically retrains ML models using calibration data"""
    
    def __init__(
        self,
        predictor: EnhancedTennisPredictor,
        virtual_tracker: VirtualBettingTracker,
        calibration_engine: CalibrationEngine,
        min_samples_for_retrain: int = 100,
        retrain_interval_days: int = 7
    ):
        """
        Initialize auto-retrainer
        
        Args:
            predictor: EnhancedTennisPredictor instance
            virtual_tracker: VirtualBettingTracker instance
            calibration_engine: CalibrationEngine instance
            min_samples_for_retrain: Minimum samples needed for retraining
            retrain_interval_days: Days between automatic retraining
        """
        self.predictor = predictor
        self.tracker = virtual_tracker
        self.calibration_engine = calibration_engine
        self.min_samples_for_retrain = min_samples_for_retrain
        self.retrain_interval_days = retrain_interval_days
        self.last_retrain_date = None
        
        logger.info("✅ MLAutoRetrainer initialized")
    
    def should_retrain(self) -> bool:
        """Check if models should be retrained"""
        # Check if we have enough calibration data
        calibration_data = self.calibration_engine._get_calibration_data()
        
        if len(calibration_data) < self.min_samples_for_retrain:
            logger.info(
                f"ℹ️ Insufficient data for retraining: "
                f"{len(calibration_data)} < {self.min_samples_for_retrain}"
            )
            return False
        
        # Check if enough time has passed since last retrain
        if self.last_retrain_date:
            days_since_retrain = (datetime.now() - self.last_retrain_date).days
            if days_since_retrain < self.retrain_interval_days:
                logger.info(
                    f"ℹ️ Too soon for retraining: "
                    f"{days_since_retrain} days < {self.retrain_interval_days} days"
                )
                return False
        
        return True
    
    def retrain_models(self, force: bool = False) -> Dict[str, Any]:
        """
        Retrain ML models using calibration data
        
        Args:
            force: Force retraining even if conditions not met
            
        Returns:
            Dictionary with retraining results
        """
        if not force and not self.should_retrain():
            return {
                'status': 'skipped',
                'reason': 'Conditions not met for retraining'
            }
        
        try:
            logger.info("🔄 Starting model retraining...")
            
            # Get training data from virtual bets
            training_data = self._prepare_training_data()
            
            if len(training_data) < self.min_samples_for_retrain:
                return {
                    'status': 'insufficient_data',
                    'samples': len(training_data),
                    'required': self.min_samples_for_retrain
                }
            
            # Retrain models
            retrain_results = self._retrain_models_with_data(training_data)
            
            # Update model weights based on performance
            self._update_model_weights(retrain_results)
            
            # Save updated models
            self._save_models()
            
            # Update retrain date
            self.last_retrain_date = datetime.now()
            
            logger.info("✅ Model retraining completed")
            
            return {
                'status': 'success',
                'samples_used': len(training_data),
                'retrain_date': self.last_retrain_date.isoformat(),
                'model_performance': retrain_results
            }
            
        except Exception as e:
            logger.error(f"❌ Error retraining models: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _prepare_training_data(self) -> List[Dict[str, Any]]:
        """Prepare training data from virtual bets and calibration data"""
        training_data = []
        
        try:
            # Get calibration data (which includes outcomes)
            calibration_data = self.calibration_engine._get_calibration_data()
            
            # Get virtual bets for feature extraction
            with sqlite3.connect(self.tracker.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        vb.match_id,
                        vb.prediction,
                        vb.confidence,
                        vb.home_player,
                        vb.away_player,
                        vb.surface,
                        vb.tournament,
                        cd.actual_outcome,
                        cd.accuracy
                    FROM virtual_bets vb
                    JOIN calibration_data cd ON vb.match_id = cd.match_id
                    WHERE vb.status IN ('won', 'lost')
                    ORDER BY vb.timestamp DESC
                ''')
                
                for row in cursor.fetchall():
                    # Extract features (simplified - would need actual feature extraction)
                    training_data.append({
                        'match_id': row['match_id'],
                        'home_player': row['home_player'],
                        'away_player': row['away_player'],
                        'surface': row['surface'],
                        'tournament': row['tournament'],
                        'predicted_confidence': row['confidence'],
                        'actual_outcome': row['actual_outcome'],
                        'label': row['accuracy']  # 1 if correct, 0 if wrong
                    })
        
        except Exception as e:
            logger.error(f"❌ Error preparing training data: {e}")
        
        return training_data
    
    def _retrain_models_with_data(
        self,
        training_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Retrain models with new data"""
        results = {}
        
        try:
            # Convert to DataFrame for easier processing
            df = pd.DataFrame(training_data)
            
            # Extract features (simplified - would need proper feature engineering)
            # For now, we'll use a simplified approach
            features = []
            labels = []
            
            for _, row in df.iterrows():
                # Get player stats if available
                home_player = row.get('home_player')
                away_player = row.get('away_player')
                
                if home_player and away_player:
                    # Extract features from predictor's player stats
                    home_stats = self.predictor.player_stats.get(home_player)
                    away_stats = self.predictor.player_stats.get(away_player)
                    
                    if home_stats and away_stats:
                        # Create feature vector (simplified)
                        feature_vector = self.predictor._extract_match_features(
                            home_stats,
                            away_stats,
                            row.get('surface', 'hard')
                        )
                        features.append(feature_vector)
                        labels.append(row['label'])
            
            if len(features) < 10:
                logger.warning("⚠️ Insufficient feature data for retraining")
                return {'status': 'insufficient_features'}
            
            # Convert to numpy arrays
            X = np.array(features)
            y = np.array(labels)
            
            # Split into train/test
            from sklearn.model_selection import train_test_split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Retrain each model
            for model_name, model in self.predictor.models.items():
                try:
                    # Retrain model
                    if model_name == 'logistic_regression':
                        # Scale features for logistic regression
                        X_train_scaled = self.predictor.scalers['standard'].transform(X_train)
                        X_test_scaled = self.predictor.scalers['standard'].transform(X_test)
                        model.fit(X_train_scaled, y_train)
                        accuracy = model.score(X_test_scaled, y_test)
                    else:
                        model.fit(X_train, y_train)
                        accuracy = model.score(X_test, y_test)
                    
                    results[model_name] = {
                        'accuracy': round(accuracy, 4),
                        'samples_used': len(X_train),
                        'status': 'retrained'
                    }
                    
                    logger.info(
                        f"✅ {model_name} retrained: accuracy = {accuracy:.2%}"
                    )
                    
                except Exception as e:
                    logger.error(f"❌ Error retraining {model_name}: {e}")
                    results[model_name] = {
                        'status': 'error',
                        'error': str(e)
                    }
            
            # Mark predictor as retrained
            self.predictor.is_trained = True
            
        except Exception as e:
            logger.error(f"❌ Error in model retraining: {e}")
            results['status'] = 'error'
            results['error'] = str(e)
        
        return results
    
    def _update_model_weights(
        self,
        retrain_results: Dict[str, Any]
    ):
        """Update ensemble model weights based on retraining performance"""
        try:
            # Calculate new weights based on accuracy
            accuracies = {}
            for model_name, result in retrain_results.items():
                if isinstance(result, dict) and 'accuracy' in result:
                    accuracies[model_name] = result['accuracy']
            
            if not accuracies:
                logger.warning("⚠️ No accuracy data for weight adjustment")
                return
            
            # Normalize weights (sum to 1.0)
            total_accuracy = sum(accuracies.values())
            if total_accuracy > 0:
                new_weights = {
                    name: acc / total_accuracy
                    for name, acc in accuracies.items()
                }
                
                # Update predictor weights
                self.predictor.model_weights.update(new_weights)
                
                logger.info(f"✅ Model weights updated: {new_weights}")
            else:
                logger.warning("⚠️ Total accuracy is zero, keeping original weights")
                
        except Exception as e:
            logger.error(f"❌ Error updating model weights: {e}")
    
    def _save_models(self):
        """Save retrained models to disk"""
        try:
            models_dir = self.predictor.data_dir / 'models'
            models_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save each model
            for model_name, model in self.predictor.models.items():
                model_path = models_dir / f"{model_name}_{timestamp}.pkl"
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
            
            # Save scalers
            for scaler_name, scaler in self.predictor.scalers.items():
                scaler_path = models_dir / f"{scaler_name}_{timestamp}.pkl"
                with open(scaler_path, 'wb') as f:
                    pickle.dump(scaler, f)
            
            # Save model weights
            weights_path = models_dir / f"model_weights_{timestamp}.json"
            import json
            with open(weights_path, 'w') as f:
                json.dump(self.predictor.model_weights, f, indent=2)
            
            logger.info(f"✅ Models saved to {models_dir}")
            
        except Exception as e:
            logger.error(f"❌ Error saving models: {e}")
    
    def schedule_retraining(self):
        """Schedule automatic retraining (to be called periodically)"""
        if self.should_retrain():
            logger.info("🔄 Scheduled retraining triggered")
            return self.retrain_models()
        else:
            return {'status': 'not_scheduled'}

