#!/usr/bin/env python3
"""
XGBoost Trainer
===============

Trains XGBoost baseline model on historical data (500+ matches).
Features: rank delta, ELO, form, surface, H2H
Target: win probability

This is part of Layer 3: Multi-Model Ensemble.
"""

import logging
import pickle
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠️ xgboost not installed. Install with: pip install xgboost")

from src.ml.feature_store import FeatureStore
from src.ml.data_collector import MatchResultsDB

logger = logging.getLogger(__name__)


class XGBoostTrainer:
    """Trains XGBoost model for tennis match prediction"""
    
    def __init__(self, db_path: Optional[str] = None, model_path: Optional[str] = None):
        """
        Initialize XGBoost trainer
        
        Args:
            db_path: Path to Match Results database
            model_path: Path to save trained model
        """
        if not XGBOOST_AVAILABLE:
            raise ImportError("xgboost not available. Install with: pip install xgboost")
        
        self.feature_store = FeatureStore(db_path)
        self.db = MatchResultsDB(db_path)
        
        if model_path is None:
            model_path = Path(__file__).parent.parent.parent / 'data' / 'models' / 'xgboost_model.pkl'
        self.model_path = Path(model_path)
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.model = None
        self.feature_names = None
        self.is_trained = False
        
        logger.info("✅ XGBoost Trainer initialized")
    
    def prepare_training_data(self, limit: Optional[int] = None) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare training data from database
        
        Args:
            limit: Maximum number of samples to use
            
        Returns:
            X (features), y (targets) as pandas DataFrame and Series
        """
        logger.info("📊 Preparing training data...")
        
        # Get training features
        training_features = self.feature_store.get_training_features(limit=limit)
        
        if not training_features:
            logger.warning("⚠️ No training data available")
            return pd.DataFrame(), pd.Series()
        
        logger.info(f"✅ Found {len(training_features)} training samples")
        
        # Convert to DataFrame
        df = pd.DataFrame(training_features)
        
        # Get feature names (exclude target and match_id)
        self.feature_names = self.feature_store.get_feature_names()
        
        # Extract features and target
        X = df[self.feature_names]
        y = df['target']
        
        # Remove any rows with NaN values
        mask = ~(X.isna().any(axis=1) | y.isna())
        X = X[mask]
        y = y[mask]
        
        logger.info(f"✅ Prepared {len(X)} samples with {len(self.feature_names)} features")
        
        return X, y
    
    def train(self, 
              n_estimators: int = 100,
              max_depth: int = 6,
              learning_rate: float = 0.1,
              min_samples_split: int = 10,
              test_size: float = 0.2,
              random_state: int = 42,
              limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Train XGBoost model
        
        Args:
            n_estimators: Number of boosting rounds
            max_depth: Maximum tree depth
            learning_rate: Learning rate
            min_samples_split: Minimum samples to split
            test_size: Test set size
            random_state: Random seed
            limit: Maximum training samples
            
        Returns:
            Training results dictionary
        """
        logger.info("🚀 Training XGBoost model...")
        
        # Prepare data
        X, y = self.prepare_training_data(limit=limit)
        
        if len(X) == 0:
            return {
                'success': False,
                'error': 'No training data available'
            }
        
        if len(X) < 50:
            logger.warning(f"⚠️ Very few training samples: {len(X)}. Need at least 50.")
            return {
                'success': False,
                'error': f'Insufficient training data: {len(X)} samples (need at least 50)'
            }
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        logger.info(f"📊 Training set: {len(X_train)} samples")
        logger.info(f"📊 Test set: {len(X_test)} samples")
        
        # Create XGBoost model
        self.model = xgb.XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            min_child_weight=min_samples_split,
            random_state=random_state,
            eval_metric='logloss',
            use_label_encoder=False
        )
        
        # Train model
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False
        )
        
        # Evaluate
        train_pred = self.model.predict(X_train)
        test_pred = self.model.predict(X_test)
        
        train_proba = self.model.predict_proba(X_train)[:, 1]
        test_proba = self.model.predict_proba(X_test)[:, 1]
        
        train_acc = accuracy_score(y_train, train_pred)
        test_acc = accuracy_score(y_test, test_pred)
        
        try:
            train_auc = roc_auc_score(y_train, train_proba)
            test_auc = roc_auc_score(y_test, test_proba)
        except Exception as e:
            logger.warning(f"Could not calculate AUC: {e}")
            train_auc = 0.0
            test_auc = 0.0
        
        # Feature importance
        feature_importance = dict(zip(
            self.feature_names,
            self.model.feature_importances_
        ))
        top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
        
        self.is_trained = True
        
        results = {
            'success': True,
            'train_accuracy': train_acc,
            'test_accuracy': test_acc,
            'train_auc': train_auc,
            'test_auc': test_auc,
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'n_features': len(self.feature_names),
            'top_features': top_features,
            'model_params': {
                'n_estimators': n_estimators,
                'max_depth': max_depth,
                'learning_rate': learning_rate
            }
        }
        
        logger.info("=" * 80)
        logger.info("✅ XGBOOST TRAINING COMPLETED")
        logger.info("=" * 80)
        logger.info(f"📊 Train Accuracy: {train_acc:.3f}")
        logger.info(f"📊 Test Accuracy: {test_acc:.3f}")
        logger.info(f"📊 Train AUC: {train_auc:.3f}")
        logger.info(f"📊 Test AUC: {test_auc:.3f}")
        logger.info(f"📈 Top 5 Features:")
        for feature, importance in top_features[:5]:
            logger.info(f"   {feature}: {importance:.4f}")
        logger.info("=" * 80)
        
        return results
    
    def predict(self, features: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Predict match outcome
        
        Args:
            features: Feature dictionary
            
        Returns:
            Prediction dictionary with probability and recommendation
        """
        if not self.is_trained or self.model is None:
            logger.warning("⚠️ Model not trained yet")
            return None
        
        try:
            # Convert features to DataFrame
            feature_df = pd.DataFrame([features])
            
            # Ensure all feature names are present
            for name in self.feature_names:
                if name not in feature_df.columns:
                    feature_df[name] = 0.0  # Default value
            
            # Select only the features used in training
            X = feature_df[self.feature_names]
            
            # Predict
            proba = self.model.predict_proba(X)[0]
            player1_win_prob = proba[1]
            player2_win_prob = proba[0]
            
            # Calculate confidence
            confidence = abs(player1_win_prob - 0.5) * 2  # 0-1 scale
            
            return {
                'player1_win_probability': player1_win_prob,
                'player2_win_probability': player2_win_prob,
                'predicted_winner': 'player1' if player1_win_prob > 0.5 else 'player2',
                'confidence': confidence,
                'model': 'xgboost'
            }
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return None
    
    def save_model(self):
        """Save trained model to file"""
        if not self.is_trained or self.model is None:
            logger.warning("⚠️ Model not trained - cannot save")
            return False
        
        try:
            model_data = {
                'model': self.model,
                'feature_names': self.feature_names,
                'is_trained': self.is_trained
            }
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"✅ Model saved to {self.model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False
    
    def load_model(self) -> bool:
        """
        Load trained model from file
        
        Returns:
            True if successful
        """
        if not self.model_path.exists():
            logger.warning(f"⚠️ Model file not found: {self.model_path}")
            return False
        
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.feature_names = model_data['feature_names']
            self.is_trained = model_data['is_trained']
            
            logger.info(f"✅ Model loaded from {self.model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False


def main():
    """Test XGBoost trainer"""
    import argparse
    
    parser = argparse.ArgumentParser(description='XGBoost Trainer')
    parser.add_argument('--train', action='store_true', help='Train model')
    parser.add_argument('--limit', type=int, help='Limit training samples')
    parser.add_argument('--n-estimators', type=int, default=100, help='Number of estimators')
    parser.add_argument('--max-depth', type=int, default=6, help='Max depth')
    parser.add_argument('--learning-rate', type=float, default=0.1, help='Learning rate')
    
    args = parser.parse_args()
    
    if not XGBOOST_AVAILABLE:
        print("❌ xgboost not available")
        print("💡 Install with: pip install xgboost")
        return
    
    trainer = XGBoostTrainer()
    
    if args.train:
        results = trainer.train(
            n_estimators=args.n_estimators,
            max_depth=args.max_depth,
            learning_rate=args.learning_rate,
            limit=args.limit
        )
        
        if results.get('success'):
            trainer.save_model()
            print("\n✅ Model trained and saved!")
        else:
            print(f"\n❌ Training failed: {results.get('error')}")
    else:
        if trainer.load_model():
            print("✅ Model loaded successfully")
        else:
            print("❌ Failed to load model. Train first with --train")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()

