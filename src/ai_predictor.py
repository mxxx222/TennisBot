"""
AI/ML Prediction Engine for Betfury.io Educational Research
===========================================================

This module provides machine learning capabilities for sports prediction
in an educational/research context. All models are designed for learning
purposes and include proper validation and ethical considerations.

DISCLAIMER: This is for educational/research purposes only.
Results should not be used for actual gambling decisions.
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging
import pickle
import json
from pathlib import Path

# Mojo performance layer imports
try:
    from src.mojo_bindings import (
        feature_transform,
        normalize_features,
        compute_statistics,
        get_performance_stats,
        should_use_mojo
    )
    MOJO_BINDINGS_AVAILABLE = True
except ImportError:
    MOJO_BINDINGS_AVAILABLE = False

from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.linear_model import LogisticRegression
import xgboost as xgb
import joblib

logger = logging.getLogger(__name__)

@dataclass
class PredictionResult:
    """Structure for prediction results"""
    match_id: str
    home_team: str
    away_team: str
    prediction: str  # HOME, DRAW, AWAY
    confidence: float
    probabilities: Dict[str, float]
    recommended_odds: float
    value_score: float
    features_used: Dict[str, float]
    timestamp: str
    model_version: str

@dataclass
class FeatureVector:
    """Feature vector for ML model"""
    current_minute: float
    home_score: int
    away_score: int
    goal_difference: int
    time_remaining: float
    home_odds: float
    draw_odds: float
    away_odds: float
    over_odds: float
    under_odds: float
    total_goals: int
    momentum_score: float
    league_strength: float
    volatility_score: float

class FeatureExtractor:
    """Extract features from match data for ML training/prediction"""
    
    def __init__(self):
        # League strength ratings (educational purposes)
        self.league_strengths = {
            'Premier League': 9.0,
            'La Liga': 9.0,
            'Bundesliga': 8.5,
            'Serie A': 8.5,
            'Ligue 1': 8.0,
            'Champions League': 10.0,
            'Europa League': 8.0,
            'Championship': 6.5,
            'Eredivisie': 6.5,
            'Liga Portugal': 6.0,
            'Unknown League': 5.0
        }
    
    def extract_features(self, match_data) -> Optional[FeatureVector]:
        """
        Extract features from match data
        
        Args:
            match_data: MatchData object from scraper
            
        Returns:
            FeatureVector object or None if extraction fails
        """
        try:
            # Parse current score
            try:
                scores = match_data.score.split('-')
                home_score = int(scores[0].strip())
                away_score = int(scores[1].strip())
            except (ValueError, IndexError):
                home_score, away_score = 0, 0
            
            # Parse current minute
            try:
                minute_str = match_data.minute.replace("'", "").replace("min", "").strip()
                current_minute = float(minute_str)
                current_minute = min(current_minute, 90.0)  # Cap at 90 minutes
            except (ValueError, AttributeError):
                current_minute = 0.0
            
            # Calculate derived features
            goal_difference = home_score - away_score
            time_remaining = 90.0 - current_minute
            total_goals = home_score + away_score
            
            # Extract odds
            odds = match_data.odds or {}
            home_odds = odds.get('home', 0.0)
            draw_odds = odds.get('draw', 0.0)
            away_odds = odds.get('away', 0.0)
            over_odds = odds.get('over_2_5', 0.0)
            under_odds = odds.get('under_2_5', 0.0)
            
            # League strength
            league_strength = self.league_strengths.get(match_data.league, 5.0)
            
            # Calculate momentum score (educational heuristic)
            momentum_score = self._calculate_momentum(
                current_minute, goal_difference, total_goals
            )
            
            # Calculate volatility score based on odds movement
            volatility_score = self._calculate_volatility(odds)
            
            return FeatureVector(
                current_minute=current_minute,
                home_score=home_score,
                away_score=away_score,
                goal_difference=goal_difference,
                time_remaining=time_remaining,
                home_odds=home_odds,
                draw_odds=draw_odds,
                away_odds=away_odds,
                over_odds=over_odds,
                under_odds=under_odds,
                total_goals=total_goals,
                momentum_score=momentum_score,
                league_strength=league_strength,
                volatility_score=volatility_score
            )
            
        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            return None
    
    def _calculate_momentum(self, minute: float, goal_diff: int, total_goals: int) -> float:
        """
        Calculate momentum score (educational heuristic)
        
        This is a simplified momentum calculation for educational purposes.
        In reality, momentum would require historical data.
        """
        # Base momentum from goal difference
        momentum = goal_diff * 2.0
        
        # Late game bonus (more important to score late)
        if minute > 70:
            momentum += abs(goal_diff) * 1.5
        elif minute > 45:
            momentum += abs(goal_diff) * 0.5
        
        # High scoring game bonus
        if total_goals > 3:
            momentum += 1.0
        
        return max(-10.0, min(10.0, momentum))  # Clamp between -10 and 10
    
    def _calculate_volatility(self, odds: Dict[str, float]) -> float:
        """Calculate volatility score from odds spread"""
        try:
            values = [v for v in odds.values() if v > 0]
            if len(values) < 2:
                return 0.0
            
            # Calculate standard deviation of odds
            return float(np.std(values))
        except Exception:
            return 0.0

class SportsPredictionModel:
    """Machine Learning model for sports outcome prediction"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self.feature_extractor = FeatureExtractor()
        self.models = {}
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.is_trained = False
        self.model_version = "1.0.0"
        
        # Model paths
        self.models_dir = Path("./models")
        self.models_dir.mkdir(exist_ok=True)
        
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'model_type': 'ensemble',
            'min_confidence': 0.70,
            'max_odds': 3.0,
            'min_odds': 1.05,
            'ensemble_models': 3,
            'random_state': 42
        }
    
    def build_models(self):
        """Build ensemble of models for prediction"""
        random_state = self.config['random_state']
        
        # Random Forest
        rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=random_state,
            class_weight='balanced'
        )
        
        # XGBoost
        xgb_model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state,
            eval_metric='logloss'
        )
        
        # Logistic Regression
        lr_model = LogisticRegression(
            random_state=random_state,
            max_iter=1000,
            class_weight='balanced'
        )
        
        # Ensemble Voting Classifier
        ensemble = VotingClassifier(
            estimators=[
                ('rf', rf_model),
                ('xgb', xgb_model),
                ('lr', lr_model)
            ],
            voting='soft'  # Use probability predictions
        )
        
        self.models = {
            'random_forest': rf_model,
            'xgboost': xgb_model,
            'logistic_regression': lr_model,
            'ensemble': ensemble
        }
        
        logger.info("ML models initialized")
    
    async def train(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Train the prediction models
        
        Args:
            training_data: DataFrame with training data
            
        Returns:
            Training results and metrics
        """
        try:
            if training_data.empty:
                raise ValueError("Training data is empty")
            
            self.build_models()
            
            # Prepare features and targets
            X = self._prepare_features(training_data)
            y = self._prepare_targets(training_data)
            
            # Encode labels
            y_encoded = self.label_encoder.fit_transform(y)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y_encoded, test_size=0.2, random_state=self.config['random_state'],
                stratify=y_encoded
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train models
            training_results = {}
            for name, model in self.models.items():
                logger.info(f"Training {name} model...")
                
                if name in ['logistic_regression']:
                    # Use scaled features for logistic regression
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                    y_proba = model.predict_proba(X_test_scaled)
                else:
                    # Tree-based models don't need scaling
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)
                    y_proba = model.predict_proba(X_test)
                
                # Calculate metrics
                accuracy = (y_pred == y_test).mean()
                auc_score = roc_auc_score(y_test, y_proba, multi_class='ovr')
                
                training_results[name] = {
                    'accuracy': accuracy,
                    'auc_score': auc_score,
                    'model': model
                }
                
                logger.info(f"{name} - Accuracy: {accuracy:.3f}, AUC: {auc_score:.3f}")
            
            # Save best model
            best_model_name = max(training_results.keys(), 
                                key=lambda x: training_results[x]['auc_score'])
            self.best_model = training_results[best_model_name]['model']
            self.best_model_name = best_model_name
            
            self.is_trained = True
            
            # Save models
            await self._save_models()
            
            return {
                'success': True,
                'best_model': best_model_name,
                'results': training_results,
                'feature_names': self._get_feature_names()
            }
            
        except Exception as e:
            logger.error(f"Training error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _prepare_features(self, data: pd.DataFrame) -> np.ndarray:
        """Prepare feature matrix"""
        # This would extract features from match data
        # For educational purposes, returning dummy features
        return np.random.rand(len(data), 13)  # 13 features as per FeatureVector
    
    def _prepare_targets(self, data: pd.DataFrame) -> List[str]:
        """Prepare target labels"""
        # This would extract outcomes from historical data
        # For educational purposes, returning dummy labels
        return np.random.choice(['HOME', 'DRAW', 'AWAY'], len(data)).tolist()
    
    def _get_feature_names(self) -> List[str]:
        """Get feature names"""
        return [
            'current_minute', 'home_score', 'away_score', 'goal_difference',
            'time_remaining', 'home_odds', 'draw_odds', 'away_odds',
            'over_odds', 'under_odds', 'total_goals', 'momentum_score',
            'league_strength', 'volatility_score'
        ]
    
    async def predict(self, match_data) -> Optional[PredictionResult]:
        """
        Make prediction for a single match
        
        Args:
            match_data: MatchData object
            
        Returns:
            PredictionResult object or None
        """
        try:
            if not self.is_trained:
                # Load trained models
                await self._load_models()
            
            # Extract features
            features = self.feature_extractor.extract_features(match_data)
            if not features:
                return None
            
            # Convert to array
            feature_array = self._features_to_array(features)
            
            # Scale if needed - use Mojo-accelerated transformation if available
            if self.best_model_name == 'logistic_regression':
                if MOJO_BINDINGS_AVAILABLE and should_use_mojo() and hasattr(self.scaler, 'mean_') and hasattr(self.scaler, 'scale_'):
                    try:
                        # Use Mojo-accelerated feature transformation
                        mean_array = np.array(self.scaler.mean_)
                        std_array = np.array(self.scaler.scale_)
                        feature_array_scaled = feature_transform(
                            feature_array.reshape(1, -1),
                            mean_array,
                            std_array
                        )
                        feature_array = feature_array_scaled
                    except Exception as e:
                        logger.debug(f"Mojo feature transform failed, using Python scaler: {e}")
                        feature_array = self.scaler.transform(feature_array.reshape(1, -1))
                else:
                    feature_array = self.scaler.transform(feature_array.reshape(1, -1))
            
            # Make prediction
            prediction_encoded = self.best_model.predict(feature_array)[0]
            probabilities = self.best_model.predict_proba(feature_array)[0]
            
            # Decode prediction
            prediction = self.label_encoder.inverse_transform([prediction_encoded])[0]
            
            # Get confidence
            confidence = float(probabilities[prediction_encoded])
            
            # Calculate recommended odds and value score
            recommended_odds = self._get_recommended_odds(match_data, prediction)
            value_score = self._calculate_value_score(confidence, recommended_odds)
            
            # Create result
            result = PredictionResult(
                match_id=match_data.match_id,
                home_team=match_data.home_team,
                away_team=match_data.away_team,
                prediction=prediction,
                confidence=confidence,
                probabilities={
                    'HOME': float(probabilities[0]),
                    'DRAW': float(probabilities[1]),
                    'AWAY': float(probabilities[2])
                },
                recommended_odds=recommended_odds,
                value_score=value_score,
                features_used=self._features_dict(features),
                timestamp=datetime.now().isoformat(),
                model_version=self.model_version
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return None
    
    def _features_to_array(self, features: FeatureVector) -> np.ndarray:
        """Convert FeatureVector to numpy array"""
        return np.array([
            features.current_minute, features.home_score, features.away_score,
            features.goal_difference, features.time_remaining, features.home_odds,
            features.draw_odds, features.away_odds, features.over_odds,
            features.under_odds, features.total_goals, features.momentum_score,
            features.league_strength, features.volatility_score
        ])
    
    def _features_dict(self, features: FeatureVector) -> Dict[str, float]:
        """Convert FeatureVector to dictionary"""
        return {
            'current_minute': features.current_minute,
            'home_score': features.home_score,
            'away_score': features.away_score,
            'goal_difference': features.goal_difference,
            'time_remaining': features.time_remaining,
            'home_odds': features.home_odds,
            'draw_odds': features.draw_odds,
            'away_odds': features.away_odds,
            'over_odds': features.over_odds,
            'under_odds': features.under_odds,
            'total_goals': features.total_goals,
            'momentum_score': features.momentum_score,
            'league_strength': features.league_strength,
            'volatility_score': features.volatility_score
        }
    
    def _get_recommended_odds(self, match_data, prediction: str) -> float:
        """Get recommended odds based on prediction"""
        odds = match_data.odds or {}
        
        if prediction == 'HOME':
            return odds.get('home', 0.0)
        elif prediction == 'AWAY':
            return odds.get('away', 0.0)
        else:  # DRAW
            return odds.get('draw', 0.0)
    
    def _calculate_value_score(self, confidence: float, odds: float) -> float:
        """Calculate value score (confidence * odds - 1)"""
        if odds <= 0:
            return 0.0
        return max(0.0, (confidence * odds) - 1.0)
    
    async def batch_predict(self, matches_data: List) -> List[PredictionResult]:
        """Make predictions for multiple matches"""
        predictions = []
        
        for match_data in matches_data:
            prediction = await self.predict(match_data)
            if prediction:
                predictions.append(prediction)
            
            # Add small delay for ethical processing
            await asyncio.sleep(0.1)
        
        return predictions
    
    async def _save_models(self):
        """Save trained models"""
        try:
            model_data = {
                'best_model': self.best_model,
                'scaler': self.scaler,
                'label_encoder': self.label_encoder,
                'best_model_name': self.best_model_name,
                'model_version': self.model_version,
                'config': self.config
            }
            
            model_path = self.models_dir / 'sports_model.pkl'
            joblib.dump(model_data, model_path)
            logger.info(f"Models saved to {model_path}")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    async def _load_models(self) -> bool:
        """Load trained models"""
        try:
            model_path = self.models_dir / 'sports_model.pkl'
            
            if not model_path.exists():
                logger.warning("No trained models found")
                return False
            
            model_data = joblib.load(model_path)
            
            self.best_model = model_data['best_model']
            self.scaler = model_data['scaler']
            self.label_encoder = model_data['label_encoder']
            self.best_model_name = model_data['best_model_name']
            self.model_version = model_data['model_version']
            self.config = model_data['config']
            
            self.is_trained = True
            logger.info(f"Models loaded from {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        if not self.is_trained:
            return {'status': 'not_trained'}
        
        return {
            'status': 'trained',
            'best_model': self.best_model_name,
            'version': self.model_version,
            'config': self.config,
            'feature_count': 14
        }

class ModelValidator:
    """Validate model performance and predictions"""
    
    def __init__(self):
        self.validation_results = []
    
    async def validate_prediction(self, prediction: PredictionResult, 
                                 actual_outcome: str) -> Dict[str, Any]:
        """
        Validate a single prediction against actual outcome
        
        Args:
            prediction: PredictionResult object
            actual_outcome: Actual outcome ('HOME', 'DRAW', 'AWAY')
            
        Returns:
            Validation metrics
        """
        is_correct = prediction.prediction == actual_outcome
        confidence_error = abs(prediction.confidence - (1.0 if is_correct else 0.0))
        
        validation = {
            'prediction_id': prediction.match_id,
            'predicted': prediction.prediction,
            'actual': actual_outcome,
            'is_correct': is_correct,
            'confidence_error': confidence_error,
            'timestamp': datetime.now().isoformat()
        }
        
        self.validation_results.append(validation)
        return validation
    
    def get_overall_metrics(self) -> Dict[str, float]:
        """Calculate overall validation metrics"""
        if not self.validation_results:
            return {}
        
        correct = sum(1 for v in self.validation_results if v['is_correct'])
        total = len(self.validation_results)
        accuracy = correct / total if total > 0 else 0.0
        
        avg_confidence_error = np.mean([v['confidence_error'] 
                                      for v in self.validation_results])
        
        return {
            'total_predictions': total,
            'correct_predictions': correct,
            'accuracy': accuracy,
            'average_confidence_error': avg_confidence_error
        }

# Educational example
async def educational_ml_example():
    """Demonstrate ML capabilities for educational purposes"""
    
    print("🤖 Starting educational ML demonstration...")
    print("⚠️  This is for learning purposes only!")
    
    # Create model
    model = SportsPredictionModel()
    
    # Generate dummy training data (in reality, you'd use real historical data)
    np.random.seed(42)
    training_data = pd.DataFrame({
        'match_id': range(1000),
        'outcome': np.random.choice(['HOME', 'DRAW', 'AWAY'], 1000)
    })
    
    # Train model
    print("📚 Training models on synthetic data...")
    results = await model.train(training_data)
    
    if results['success']:
        print(f"✅ Training successful!")
        print(f"   Best model: {results['best_model']}")
        print(f"   Features: {len(results['feature_names'])}")
        
        # Show model info
        info = model.get_model_info()
        print(f"   Model info: {info}")
        
    else:
        print(f"❌ Training failed: {results['error']}")

if __name__ == "__main__":
    # Run educational example
    asyncio.run(educational_ml_example())