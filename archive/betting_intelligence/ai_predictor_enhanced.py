#!/usr/bin/env python3
"""
🎾 ENHANCED TENNIS MATCH PREDICTOR WITH 70% ACCURACY TARGET
==========================================================

Advanced AI-powered tennis match prediction system that combines:
- Historical player performance data
- Head-to-head statistics
- Surface preferences
- Current form analysis
- Betting odds analysis
- Machine learning models

Target Accuracy: 70%+

Author: TennisBot Advanced Analytics
Version: 2.0.0
"""

import pandas as pd
import numpy as np
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import pickle
import os
from pathlib import Path

# Mojo performance layer imports
try:
    from src.mojo_bindings import (
        ensemble_aggregate,
        batch_predict,
        get_performance_stats,
        should_use_mojo
    )
    MOJO_BINDINGS_AVAILABLE = True
except ImportError:
    MOJO_BINDINGS_AVAILABLE = False
    # Logger will be initialized later, safe to ignore

# Machine Learning imports
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
    ML_AVAILABLE = True
    
    # XGBoost is optional
    try:
        import xgboost as xgb
        XGBOOST_AVAILABLE = True
    except (ImportError, Exception) as e:
        print(f"⚠️ XGBoost not available ({str(e)[:50]}...). Using other ML models.")
        XGBOOST_AVAILABLE = False
        xgb = None
        
except ImportError:
    print("⚠️ Warning: Machine learning libraries not available. Install scikit-learn.")
    ML_AVAILABLE = False
    XGBOOST_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PlayerStats:
    """Enhanced player statistics"""
    name: str
    ranking: int = 0
    points: int = 0
    
    # Surface-specific stats
    hard_court_wins: int = 0
    hard_court_losses: int = 0
    clay_court_wins: int = 0
    clay_court_losses: int = 0
    grass_court_wins: int = 0
    grass_court_losses: int = 0
    
    # Recent form (last 10 matches)
    recent_wins: int = 0
    recent_losses: int = 0
    
    # Career stats
    career_wins: int = 0
    career_losses: int = 0
    
    # Performance metrics
    ace_percentage: float = 0.0
    double_fault_percentage: float = 0.0
    first_serve_percentage: float = 0.0
    first_serve_win_percentage: float = 0.0
    break_points_saved_percentage: float = 0.0
    
    # Physical/Mental factors
    age: int = 25
    fatigue_factor: float = 0.0  # 0-1 scale
    injury_risk: float = 0.0     # 0-1 scale
    
    def get_surface_win_rate(self, surface: str) -> float:
        """Get win rate for specific surface"""
        if surface.lower() == 'hard':
            total = self.hard_court_wins + self.hard_court_losses
            return self.hard_court_wins / max(total, 1)
        elif surface.lower() == 'clay':
            total = self.clay_court_wins + self.clay_court_losses
            return self.clay_court_wins / max(total, 1)
        elif surface.lower() == 'grass':
            total = self.grass_court_wins + self.grass_court_losses
            return self.grass_court_wins / max(total, 1)
        return 0.5
    
    def get_recent_form(self) -> float:
        """Get recent form as win percentage"""
        total = self.recent_wins + self.recent_losses
        return self.recent_wins / max(total, 1)
    
    def get_career_win_rate(self) -> float:
        """Get overall career win rate"""
        total = self.career_wins + self.career_losses
        return self.career_wins / max(total, 1)

@dataclass
class MatchPrediction:
    """Match prediction with confidence metrics"""
    home_player: str
    away_player: str
    predicted_winner: str
    win_probability: float
    confidence_score: float
    
    # Detailed probabilities
    home_win_prob: float
    away_win_prob: float
    
    # Contributing factors
    ranking_advantage: float
    form_advantage: float
    surface_advantage: float
    head_to_head_advantage: float
    odds_implied_prob: float
    
    # Model predictions
    model_predictions: Dict[str, float]
    
    # Metadata
    surface: str = "hard"
    tournament: str = ""
    prediction_timestamp: str = ""
    
    def __post_init__(self):
        if not self.prediction_timestamp:
            self.prediction_timestamp = datetime.now().isoformat()

class EnhancedTennisPredictor:
    """Enhanced tennis match predictor with multiple ML models"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else Path('/Users/herbspotturku/sportsbot/TennisBot/data')
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize models
        self.models = {}
        self.scalers = {}
        self.feature_columns = []
        self.is_trained = False
        
        # Player database
        self.player_stats = {}
        self.head_to_head = {}
        
        # Model weights for ensemble
        self.model_weights = {
            'random_forest': 0.3,
            'gradient_boosting': 0.25,
            'xgboost': 0.25,
            'logistic_regression': 0.2
        }
        
        # Calibration adjustment (loaded from calibration data)
        self.calibration_adjustment = None
        self.calibration_loaded = False
        
        logger.info("🎾 Enhanced Tennis Predictor initialized")
    
    def load_player_data(self, player_data_file: str = None) -> bool:
        """Load player statistics from file or create sample data"""
        try:
            if player_data_file and os.path.exists(player_data_file):
                with open(player_data_file, 'r') as f:
                    data = json.load(f)
                    for name, stats in data.items():
                        self.player_stats[name] = PlayerStats(**stats)
                logger.info(f"✅ Loaded {len(self.player_stats)} player profiles")
                return True
            else:
                # Create sample player data for demonstration
                self._create_sample_player_data()
                logger.info("✅ Created sample player data for demonstration")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error loading player data: {e}")
            return False
    
    def _apply_calibration_adjustment(self, probability: float) -> float:
        """
        Apply calibration adjustment to probability based on calibration data
        
        Args:
            probability: Raw predicted probability
            
        Returns:
            Calibrated probability
        """
        if not self.calibration_loaded or self.calibration_adjustment is None:
            return probability
        
        # Simple linear adjustment based on calibration gap
        # In production, this would use more sophisticated calibration methods
        # like Platt scaling or isotonic regression
        try:
            # Get adjustment factor for this probability range
            adjustment = self.calibration_adjustment.get('adjustment_factor', 1.0)
            calibrated_prob = probability * adjustment
            
            # Clamp to valid range
            return max(0.0, min(1.0, calibrated_prob))
        except Exception:
            return probability
    
    def load_calibration_adjustment(self, calibration_data: Dict[str, Any]):
        """
        Load calibration adjustment from calibration analysis
        
        Args:
            calibration_data: Calibration analysis results
        """
        try:
            overall_metrics = calibration_data.get('overall_metrics', {})
            calibration_gap = overall_metrics.get('calibration_gap', 0)
            avg_confidence = overall_metrics.get('avg_confidence', 0.5)
            actual_accuracy = overall_metrics.get('overall_accuracy', 0.5)
            
            if calibration_gap > 0.01 and avg_confidence > 0:
                # Calculate adjustment factor
                adjustment_factor = actual_accuracy / avg_confidence if avg_confidence > 0 else 1.0
                
                self.calibration_adjustment = {
                    'adjustment_factor': adjustment_factor,
                    'calibration_gap': calibration_gap,
                    'last_updated': datetime.now().isoformat()
                }
                self.calibration_loaded = True
                
                logger.info(
                    f"✅ Calibration adjustment loaded: "
                    f"factor={adjustment_factor:.3f}, gap={calibration_gap:.4f}"
                )
        except Exception as e:
            logger.error(f"❌ Error loading calibration adjustment: {e}")
            self.calibration_loaded = False
    
    def _create_sample_player_data(self):
        """Create sample player data for demonstration"""
        sample_players = [
            # Top players with realistic stats
            {
                'name': 'Novak Djokovic',
                'ranking': 1, 'points': 9000,
                'hard_court_wins': 450, 'hard_court_losses': 80,
                'clay_court_wins': 200, 'clay_court_losses': 60,
                'grass_court_wins': 80, 'grass_court_losses': 20,
                'recent_wins': 8, 'recent_losses': 2,
                'career_wins': 1000, 'career_losses': 200,
                'ace_percentage': 12.5, 'first_serve_percentage': 65.0,
                'first_serve_win_percentage': 75.0, 'age': 36
            },
            {
                'name': 'Carlos Alcaraz',
                'ranking': 2, 'points': 8500,
                'hard_court_wins': 120, 'hard_court_losses': 25,
                'clay_court_wins': 80, 'clay_court_losses': 15,
                'grass_court_wins': 20, 'grass_court_losses': 8,
                'recent_wins': 9, 'recent_losses': 1,
                'career_wins': 250, 'career_losses': 60,
                'ace_percentage': 10.2, 'first_serve_percentage': 62.0,
                'first_serve_win_percentage': 72.0, 'age': 21
            },
            {
                'name': 'Daniil Medvedev',
                'ranking': 3, 'points': 7800,
                'hard_court_wins': 200, 'hard_court_losses': 40,
                'clay_court_wins': 50, 'clay_court_losses': 30,
                'grass_court_wins': 25, 'grass_court_losses': 15,
                'recent_wins': 7, 'recent_losses': 3,
                'career_wins': 350, 'career_losses': 120,
                'ace_percentage': 15.8, 'first_serve_percentage': 60.0,
                'first_serve_win_percentage': 70.0, 'age': 28
            },
            {
                'name': 'Jannik Sinner',
                'ranking': 4, 'points': 7200,
                'hard_court_wins': 100, 'hard_court_losses': 20,
                'clay_court_wins': 60, 'clay_court_losses': 18,
                'grass_court_wins': 15, 'grass_court_losses': 10,
                'recent_wins': 8, 'recent_losses': 2,
                'career_wins': 200, 'career_losses': 70,
                'ace_percentage': 11.5, 'first_serve_percentage': 63.0,
                'first_serve_win_percentage': 73.0, 'age': 23
            },
            {
                'name': 'Alexander Zverev',
                'ranking': 5, 'points': 6800,
                'hard_court_wins': 180, 'hard_court_losses': 45,
                'clay_court_wins': 90, 'clay_court_losses': 25,
                'grass_court_wins': 30, 'grass_court_losses': 20,
                'recent_wins': 6, 'recent_losses': 4,
                'career_wins': 400, 'career_losses': 150,
                'ace_percentage': 14.2, 'first_serve_percentage': 61.0,
                'first_serve_win_percentage': 68.0, 'age': 27
            }
        ]
        
        for player_data in sample_players:
            self.player_stats[player_data['name']] = PlayerStats(**player_data)
        
        # Add some lower-ranked players for variety
        for i in range(6, 51):
            name = f"Player_{i}"
            self.player_stats[name] = PlayerStats(
                name=name,
                ranking=i,
                points=max(1000, 7000 - i * 100),
                hard_court_wins=max(10, 200 - i * 3),
                hard_court_losses=max(5, 50 + i),
                clay_court_wins=max(5, 100 - i * 2),
                clay_court_losses=max(3, 30 + i),
                grass_court_wins=max(2, 50 - i),
                grass_court_losses=max(2, 20 + i // 2),
                recent_wins=np.random.randint(3, 8),
                recent_losses=np.random.randint(2, 7),
                career_wins=max(50, 500 - i * 8),
                career_losses=max(20, 100 + i * 2),
                ace_percentage=np.random.uniform(8.0, 16.0),
                first_serve_percentage=np.random.uniform(55.0, 70.0),
                first_serve_win_percentage=np.random.uniform(65.0, 78.0),
                age=np.random.randint(20, 35)
            )
    
    def create_training_data(self, num_matches: int = 1000) -> pd.DataFrame:
        """Create synthetic training data based on player stats"""
        training_data = []
        
        players = list(self.player_stats.keys())
        surfaces = ['hard', 'clay', 'grass']
        
        for _ in range(num_matches):
            # Randomly select two players
            home_player, away_player = np.random.choice(players, 2, replace=False)
            surface = np.random.choice(surfaces)
            
            # Get player stats
            home_stats = self.player_stats[home_player]
            away_stats = self.player_stats[away_player]
            
            # Create features
            features = self._extract_match_features(home_stats, away_stats, surface)
            
            # Simulate match outcome based on features
            home_win_prob = self._calculate_base_win_probability(home_stats, away_stats, surface)
            winner = 1 if np.random.random() < home_win_prob else 0
            
            # Add some noise to make it realistic
            features['outcome'] = winner
            training_data.append(features)
        
        df = pd.DataFrame(training_data)
        logger.info(f"✅ Created {len(df)} training samples")
        return df
    
    def _extract_match_features(self, home_stats: PlayerStats, away_stats: PlayerStats, surface: str) -> Dict[str, float]:
        """Extract features for machine learning model"""
        features = {
            # Ranking features
            'home_ranking': home_stats.ranking,
            'away_ranking': away_stats.ranking,
            'ranking_diff': home_stats.ranking - away_stats.ranking,
            'ranking_advantage': 1 / (1 + np.exp((home_stats.ranking - away_stats.ranking) / 10)),
            
            # Surface-specific features
            'home_surface_win_rate': home_stats.get_surface_win_rate(surface),
            'away_surface_win_rate': away_stats.get_surface_win_rate(surface),
            'surface_advantage': home_stats.get_surface_win_rate(surface) - away_stats.get_surface_win_rate(surface),
            
            # Form features
            'home_recent_form': home_stats.get_recent_form(),
            'away_recent_form': away_stats.get_recent_form(),
            'form_advantage': home_stats.get_recent_form() - away_stats.get_recent_form(),
            
            # Career features
            'home_career_win_rate': home_stats.get_career_win_rate(),
            'away_career_win_rate': away_stats.get_career_win_rate(),
            'career_advantage': home_stats.get_career_win_rate() - away_stats.get_career_win_rate(),
            
            # Performance features
            'home_ace_percentage': home_stats.ace_percentage,
            'away_ace_percentage': away_stats.ace_percentage,
            'ace_advantage': home_stats.ace_percentage - away_stats.ace_percentage,
            
            'home_first_serve_win': home_stats.first_serve_win_percentage,
            'away_first_serve_win': away_stats.first_serve_win_percentage,
            'serve_advantage': home_stats.first_serve_win_percentage - away_stats.first_serve_win_percentage,
            
            # Age and physical factors
            'home_age': home_stats.age,
            'away_age': away_stats.age,
            'age_advantage': away_stats.age - home_stats.age,  # Younger is better
            
            # Surface encoding
            'surface_hard': 1 if surface == 'hard' else 0,
            'surface_clay': 1 if surface == 'clay' else 0,
            'surface_grass': 1 if surface == 'grass' else 0,
        }
        
        return features
    
    def _calculate_base_win_probability(self, home_stats: PlayerStats, away_stats: PlayerStats, surface: str) -> float:
        """Calculate base win probability using statistical model"""
        # Ranking factor (most important)
        ranking_factor = 1 / (1 + np.exp((home_stats.ranking - away_stats.ranking) / 15))
        
        # Surface factor
        home_surface_rate = home_stats.get_surface_win_rate(surface)
        away_surface_rate = away_stats.get_surface_win_rate(surface)
        surface_factor = home_surface_rate / (home_surface_rate + away_surface_rate)
        
        # Form factor
        home_form = home_stats.get_recent_form()
        away_form = away_stats.get_recent_form()
        form_factor = home_form / (home_form + away_form + 0.01)  # Avoid division by zero
        
        # Career factor
        home_career = home_stats.get_career_win_rate()
        away_career = away_stats.get_career_win_rate()
        career_factor = home_career / (home_career + away_career + 0.01)
        
        # Combine factors with weights
        win_prob = (
            0.4 * ranking_factor +
            0.25 * surface_factor +
            0.2 * form_factor +
            0.15 * career_factor
        )
        
        # Add some randomness
        win_prob += np.random.normal(0, 0.05)
        
        return np.clip(win_prob, 0.1, 0.9)
    
    def train_models(self, training_data: pd.DataFrame = None) -> bool:
        """Train multiple ML models for ensemble prediction"""
        if not ML_AVAILABLE:
            logger.error("❌ Machine learning libraries not available")
            return False
        
        try:
            # Create training data if not provided
            if training_data is None:
                training_data = self.create_training_data(2000)
            
            # Prepare features and target
            feature_columns = [col for col in training_data.columns if col != 'outcome']
            X = training_data[feature_columns]
            y = training_data['outcome']
            
            self.feature_columns = feature_columns
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            self.scalers['standard'] = scaler
            
            # Train multiple models
            models_to_train = {
                'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
                'gradient_boosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
                'logistic_regression': LogisticRegression(random_state=42),
            }
            
            # Add XGBoost if available
            if XGBOOST_AVAILABLE:
                models_to_train['xgboost'] = xgb.XGBClassifier(n_estimators=100, random_state=42)
            else:
                logger.info("ℹ️ XGBoost not available, using scikit-learn models only")
            
            # Train and evaluate each model
            model_scores = {}
            for name, model in models_to_train.items():
                logger.info(f"🔧 Training {name}...")
                
                if name == 'logistic_regression':
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                else:
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)
                
                accuracy = accuracy_score(y_test, y_pred)
                model_scores[name] = accuracy
                self.models[name] = model
                
                logger.info(f"✅ {name} accuracy: {accuracy:.3f}")
            
            # Calculate ensemble accuracy
            ensemble_pred = self._ensemble_predict(X_test, X_test_scaled)
            ensemble_accuracy = accuracy_score(y_test, ensemble_pred)
            
            logger.info(f"🎯 Ensemble accuracy: {ensemble_accuracy:.3f}")
            
            self.is_trained = True
            
            # Save models
            self._save_models()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error training models: {e}")
            return False
    
    def _ensemble_predict(self, X, X_scaled) -> np.ndarray:
        """Make ensemble predictions using weighted voting (Mojo-accelerated)"""
        # Get predictions from each model
        predictions_list = []
        model_names = []
        
        for name, model in self.models.items():
            if name == 'logistic_regression':
                pred_proba = model.predict_proba(X_scaled)[:, 1]
            else:
                pred_proba = model.predict_proba(X)[:, 1]
            
            predictions_list.append(pred_proba)
            model_names.append(name)
        
        # Use Mojo-accelerated ensemble aggregation if available
        if MOJO_BINDINGS_AVAILABLE and should_use_mojo() and len(predictions_list) > 0:
            try:
                # Convert to numpy arrays if needed
                preds_array = [np.array(p) for p in predictions_list]
                
                # Create weights array matching model order
                weights = np.array([
                    self.model_weights.get(name, 0.25) for name in model_names
                ])
                
                # Use Mojo-accelerated ensemble aggregation
                ensemble_proba = ensemble_aggregate(preds_array, weights)
                
                # Convert to binary predictions
                return (ensemble_proba > 0.5).astype(int)
            except Exception as e:
                logger.warning(f"Mojo ensemble aggregation failed, using Python fallback: {e}")
        
        # Python fallback implementation
        predictions = []
        for name, model in self.models.items():
            if name == 'logistic_regression':
                pred_proba = model.predict_proba(X_scaled)[:, 1]
            else:
                pred_proba = model.predict_proba(X)[:, 1]
            
            predictions.append(pred_proba * self.model_weights.get(name, 0.25))
        
        ensemble_proba = np.sum(predictions, axis=0)
        return (ensemble_proba > 0.5).astype(int)
    
    def predict_match(self, home_player: str, away_player: str, surface: str = 'hard', 
                     tournament: str = "", odds: Dict[str, float] = None) -> MatchPrediction:
        """Predict match outcome with detailed analysis"""
        
        # Get player stats (create default if not found)
        home_stats = self.player_stats.get(home_player, self._create_default_player_stats(home_player))
        away_stats = self.player_stats.get(away_player, self._create_default_player_stats(away_player))
        
        # Extract features
        features = self._extract_match_features(home_stats, away_stats, surface)
        
        if self.is_trained and ML_AVAILABLE:
            # ML-based prediction
            X = pd.DataFrame([features])[self.feature_columns]
            X_scaled = self.scalers['standard'].transform(X)
            
            # Get predictions from each model
            model_predictions = {}
            for name, model in self.models.items():
                if name == 'logistic_regression':
                    prob = model.predict_proba(X_scaled)[0, 1]
                else:
                    prob = model.predict_proba(X)[0, 1]
                model_predictions[name] = prob
            
            # Ensemble prediction
            weighted_prob = sum(prob * self.model_weights.get(name, 0.25) 
                              for name, prob in model_predictions.items())
            
            home_win_prob = weighted_prob
            
        else:
            # Fallback to statistical prediction
            home_win_prob = self._calculate_base_win_probability(home_stats, away_stats, surface)
            model_predictions = {'statistical': home_win_prob}
        
        away_win_prob = 1 - home_win_prob
        
        # Determine winner and confidence
        if home_win_prob > away_win_prob:
            predicted_winner = home_player
            win_probability = home_win_prob
        else:
            predicted_winner = away_player
            win_probability = away_win_prob
        
        # Apply calibration adjustment if available
        win_probability = self._apply_calibration_adjustment(win_probability)
        
        # Calculate confidence score (higher for more decisive predictions)
        confidence_score = abs(home_win_prob - 0.5) * 2

        # Boost confidence for top players and clear advantages
        if home_stats.ranking <= 10 and away_stats.ranking <= 10:
            # Top player matchups are more predictable
            confidence_score *= 1.2
        elif abs(home_stats.ranking - away_stats.ranking) > 50:
            # Big ranking differences are very predictable
            confidence_score *= 1.3
        elif abs(home_win_prob - 0.5) > 0.3:
            # Strong predictions are more reliable
            confidence_score *= 1.1

        # Cap confidence at 1.0
        confidence_score = min(confidence_score, 1.0)
        
        # Calculate contributing factors
        ranking_advantage = features['ranking_advantage'] - 0.5
        form_advantage = features['form_advantage']
        surface_advantage = features['surface_advantage']
        head_to_head_advantage = 0.0  # Placeholder
        
        # Odds analysis
        odds_implied_prob = 0.0
        if odds and 'home' in odds and 'away' in odds:
            home_implied = 1 / odds['home']
            away_implied = 1 / odds['away']
            total_implied = home_implied + away_implied
            odds_implied_prob = home_implied / total_implied
        
        prediction = MatchPrediction(
            home_player=home_player,
            away_player=away_player,
            predicted_winner=predicted_winner,
            win_probability=win_probability,
            confidence_score=confidence_score,
            home_win_prob=home_win_prob,
            away_win_prob=away_win_prob,
            ranking_advantage=ranking_advantage,
            form_advantage=form_advantage,
            surface_advantage=surface_advantage,
            head_to_head_advantage=head_to_head_advantage,
            odds_implied_prob=odds_implied_prob,
            model_predictions=model_predictions,
            surface=surface,
            tournament=tournament
        )
        
        return prediction
    
    def _create_default_player_stats(self, player_name: str) -> PlayerStats:
        """Create default stats for unknown players"""
        return PlayerStats(
            name=player_name,
            ranking=100,  # Average ranking
            points=1000,
            hard_court_wins=50,
            hard_court_losses=50,
            clay_court_wins=25,
            clay_court_losses=25,
            grass_court_wins=10,
            grass_court_losses=10,
            recent_wins=5,
            recent_losses=5,
            career_wins=100,
            career_losses=100,
            ace_percentage=10.0,
            first_serve_percentage=60.0,
            first_serve_win_percentage=70.0,
            age=27
        )
    
    def predict_multiple_matches(self, matches: List[Dict[str, Any]]) -> List[MatchPrediction]:
        """Predict multiple matches at once"""
        predictions = []
        
        for match in matches:
            try:
                prediction = self.predict_match(
                    home_player=match.get('home_team', match.get('home_player', 'Unknown')),
                    away_player=match.get('away_team', match.get('away_player', 'Unknown')),
                    surface=match.get('surface', 'hard'),
                    tournament=match.get('league', match.get('tournament', '')),
                    odds={
                        'home': match.get('home_odds'),
                        'away': match.get('away_odds')
                    } if match.get('home_odds') and match.get('away_odds') else None
                )
                predictions.append(prediction)
                
            except Exception as e:
                logger.error(f"❌ Error predicting match {match}: {e}")
                continue
        
        return predictions
    
    def get_high_confidence_predictions(self, predictions: List[MatchPrediction], 
                                      min_confidence: float = 0.3) -> List[MatchPrediction]:
        """Filter predictions by confidence level"""
        high_confidence = [p for p in predictions if p.confidence_score >= min_confidence]
        high_confidence.sort(key=lambda x: x.confidence_score, reverse=True)
        return high_confidence
    
    def display_predictions(self, predictions: List[MatchPrediction], show_details: bool = True):
        """Display predictions in a user-friendly format"""
        print("\n" + "="*80)
        print("🎾 TENNIS MATCH PREDICTIONS WITH 70% ACCURACY TARGET")
        print("="*80)
        
        if not predictions:
            print("❌ No predictions available")
            return
        
        # Sort by confidence
        predictions.sort(key=lambda x: x.confidence_score, reverse=True)
        
        for i, pred in enumerate(predictions, 1):
            print(f"\n🏆 Match {i}: {pred.home_player} vs {pred.away_player}")
            print(f"   📊 Predicted Winner: {pred.predicted_winner}")
            print(f"   🎯 Win Probability: {pred.win_probability:.1%}")
            print(f"   ⭐ Confidence: {pred.confidence_score:.1%}")
            
            if show_details:
                print(f"   📈 Home Win: {pred.home_win_prob:.1%} | Away Win: {pred.away_win_prob:.1%}")
                print(f"   🏟️ Surface: {pred.surface.title()}")
                
                if pred.tournament:
                    print(f"   🏆 Tournament: {pred.tournament}")
                
                # Show key factors
                factors = []
                if abs(pred.ranking_advantage) > 0.1:
                    factors.append(f"Ranking {'✅' if pred.ranking_advantage > 0 else '❌'}")
                if abs(pred.form_advantage) > 0.1:
                    factors.append(f"Form {'✅' if pred.form_advantage > 0 else '❌'}")
                if abs(pred.surface_advantage) > 0.1:
                    factors.append(f"Surface {'✅' if pred.surface_advantage > 0 else '❌'}")
                
                if factors:
                    print(f"   🔍 Key Factors: {', '.join(factors)}")
                
                # Show model agreement
                if len(pred.model_predictions) > 1:
                    model_agreement = len([p for p in pred.model_predictions.values() 
                                         if (p > 0.5) == (pred.home_win_prob > 0.5)])
                    total_models = len(pred.model_predictions)
                    print(f"   🤖 Model Agreement: {model_agreement}/{total_models}")
        
        # Summary statistics
        high_conf = len([p for p in predictions if p.confidence_score >= 0.3])
        avg_confidence = np.mean([p.confidence_score for p in predictions])
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total Predictions: {len(predictions)}")
        print(f"   High Confidence (≥30%): {high_conf}")
        print(f"   Average Confidence: {avg_confidence:.1%}")
        print(f"   Target Accuracy: 70%+")
    
    def _save_models(self):
        """Save trained models to disk"""
        try:
            models_dir = self.data_dir / 'models'
            models_dir.mkdir(exist_ok=True)
            
            # Save each model
            for name, model in self.models.items():
                model_file = models_dir / f'{name}_model.pkl'
                with open(model_file, 'wb') as f:
                    pickle.dump(model, f)
            
            # Save scalers
            for name, scaler in self.scalers.items():
                scaler_file = models_dir / f'{name}_scaler.pkl'
                with open(scaler_file, 'wb') as f:
                    pickle.dump(scaler, f)
            
            # Save feature columns
            with open(models_dir / 'feature_columns.json', 'w') as f:
                json.dump(self.feature_columns, f)
            
            logger.info(f"✅ Models saved to {models_dir}")
            
        except Exception as e:
            logger.error(f"❌ Error saving models: {e}")
    
    def load_models(self) -> bool:
        """Load trained models from disk"""
        try:
            models_dir = self.data_dir / 'models'
            
            if not models_dir.exists():
                logger.warning("⚠️ No saved models found")
                return False
            
            # Load feature columns
            feature_file = models_dir / 'feature_columns.json'
            if feature_file.exists():
                with open(feature_file, 'r') as f:
                    self.feature_columns = json.load(f)
            
            # Load models
            for model_file in models_dir.glob('*_model.pkl'):
                name = model_file.stem.replace('_model', '')
                with open(model_file, 'rb') as f:
                    self.models[name] = pickle.load(f)
                logger.info(f"✅ Loaded {name} model")
            
            # Load scalers
            for scaler_file in models_dir.glob('*_scaler.pkl'):
                name = scaler_file.stem.replace('_scaler', '')
                with open(scaler_file, 'rb') as f:
                    self.scalers[name] = pickle.load(f)
            
            if self.models:
                self.is_trained = True
                logger.info(f"✅ Loaded {len(self.models)} trained models")
                return True
            else:
                logger.warning("⚠️ No models loaded")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error loading models: {e}")
            return False

def main():
    """Main function for testing the predictor"""
    print("🎾 ENHANCED TENNIS PREDICTOR TEST")
    print("=" * 50)
    
    # Initialize predictor
    predictor = EnhancedTennisPredictor()
    
    # Load player data
    predictor.load_player_data()
    
    # Try to load existing models, otherwise train new ones
    if not predictor.load_models():
        print("🔧 Training new models...")
        if predictor.train_models():
            print("✅ Models trained successfully!")
        else:
            print("❌ Model training failed, using statistical predictions")
    
    # Test predictions
    test_matches = [
        {
            'home_player': 'Novak Djokovic',
            'away_player': 'Carlos Alcaraz',
            'surface': 'hard',
            'tournament': 'ATP Masters 1000',
            'home_odds': 1.85,
            'away_odds': 1.95
        },
        {
            'home_player': 'Daniil Medvedev',
            'away_player': 'Jannik Sinner',
            'surface': 'hard',
            'tournament': 'ATP 500',
            'home_odds': 2.10,
            'away_odds': 1.75
        },
        {
            'home_player': 'Carlos Alcaraz',
            'away_player': 'Alexander Zverev',
            'surface': 'clay',
            'tournament': 'ATP Masters 1000',
            'home_odds': 1.60,
            'away_odds': 2.40
        },
        {
            'home_player': 'Player_15',
            'away_player': 'Player_25',
            'surface': 'grass',
            'tournament': 'ATP 250',
            'home_odds': 1.90,
            'away_odds': 1.90
        }
    ]
    
    # Make predictions
    predictions = predictor.predict_multiple_matches(test_matches)
    
    # Display all predictions
    predictor.display_predictions(predictions, show_details=True)
    
    # Show high confidence predictions only
    high_conf_predictions = predictor.get_high_confidence_predictions(predictions, min_confidence=0.25)
    
    if high_conf_predictions:
        print("\n" + "="*80)
        print("🎯 HIGH CONFIDENCE PREDICTIONS (≥25% confidence)")
        print("="*80)
        predictor.display_predictions(high_conf_predictions, show_details=False)
    
    print("\n🚀 Integration ready! Use this predictor with your live betting scraper.")

if __name__ == "__main__":
    main()
