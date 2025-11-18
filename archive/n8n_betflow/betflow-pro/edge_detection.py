"""
Advanced edge detection engine with multiple methods
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class EdgeDetectionEngine:
    """Advanced edge detection with multiple methods"""

    def __init__(self, historical_data: Optional[pd.DataFrame] = None):
        """
        Initialize edge detection engine
        
        Args:
            historical_data: Historical match data for ML training (optional)
        """
        self.data = historical_data if historical_data is not None else pd.DataFrame()
        self.ml_model = None
        
        if not self.data.empty:
            self.train_ml_model()
        else:
            logger.warning("No historical data provided. ML model will not be trained.")

    def calculate_base_edge(self,
                           my_probability: float,
                           market_probability: float) -> float:
        """
        Basic edge: my prob vs market prob

        Args:
            my_probability: My assessed probability (0-1)
            market_probability: Implied from odds (0-1)

        Returns:
            Edge % (-100 to 100)
        """
        if market_probability == 0:
            return 0.0
        
        edge = ((my_probability - market_probability) / market_probability) * 100
        return edge

    def detect_line_movement(self,
                            opening_odds: float,
                            current_odds: float,
                            time_hours: float) -> Dict:
        """
        Detect if line moved in our favor (opportunity)

        Returns:
            Dict with movement_direction, movement_magnitude, edge_opportunity, confidence
        """
        if opening_odds == 0:
            return {
                "movement_direction": "none",
                "movement_magnitude": 0,
                "edge_opportunity": 0,
                "confidence": 0,
                "recommendation": "HOLD"
            }
        
        movement = (current_odds - opening_odds) / opening_odds
        edge_from_movement = abs(movement) * 50  # Rough conversion

        confidence = min(10, time_hours / 6)  # More confident if more time passed

        return {
            "movement_direction": "up" if movement > 0 else "down",
            "movement_magnitude": abs(movement) * 100,
            "edge_opportunity": edge_from_movement,
            "confidence": confidence,
            "recommendation": "LAYER_BET" if movement > 0.02 else "HOLD"
        }

    def detect_smart_money(self,
                          odds_history: list,
                          volume_history: list) -> Dict:
        """
        Detect if smart money is moving (syndicates, sharp bettors)

        Smart money patterns:
        - Rapid line movement despite low volume = sharp money
        - Volume spike = public money (usually wrong)
        """
        if not odds_history or len(odds_history) < 2:
            return {"smart_money_detected": False}
        
        recent_movement = odds_history[-1] - odds_history[0]
        recent_volume = sum(volume_history[-3:]) if len(volume_history) >= 3 else sum(volume_history)

        if recent_movement > 0.05 and recent_volume < 100:
            return {
                "smart_money_detected": True,
                "direction": "against_public" if recent_movement > 0 else "with_public",
                "confidence": 8,
                "action": "FOLLOW_SMART_MONEY"
            }

        return {"smart_money_detected": False}

    def train_ml_model(self):
        """
        Train Random Forest to predict outcomes
        Uses historical data: odds, xG, form, H2H, etc.
        """
        if self.data.empty:
            logger.warning("Cannot train ML model: no data available")
            return
        
        # Check for required columns
        required_cols = ['xg_diff', 'form_diff', 'h2h_win_pct', 'home_advantage',
                        'recent_goals_diff', 'injury_count_diff', 'result']
        
        missing_cols = [col for col in required_cols if col not in self.data.columns]
        if missing_cols:
            logger.warning(f"Cannot train ML model: missing columns {missing_cols}")
            return

        try:
            # Prepare features and target
            features = self.data[[
                'xg_diff', 'form_diff', 'h2h_win_pct', 'home_advantage',
                'recent_goals_diff', 'injury_count_diff'
            ]].fillna(0)
            target = self.data['result']  # 1 = win, 0 = loss/draw

            self.ml_model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
            self.ml_model.fit(features, target)
            logger.info("ML model trained successfully")
        except Exception as e:
            logger.error(f"Error training ML model: {e}")
            self.ml_model = None

    def predict_probability_ml(self, match_features: Dict) -> float:
        """
        ML-based probability prediction

        Args:
            match_features: Dict with xg_diff, form_diff, h2h_win_pct, etc.

        Returns:
            Predicted probability (0-1)
        """
        if not self.ml_model:
            logger.warning("ML model not available. Returning default probability.")
            return 0.5

        try:
            feature_values = np.array([[
                match_features.get('xg_diff', 0),
                match_features.get('form_diff', 0),
                match_features.get('h2h_win_pct', 50) / 100,
                match_features.get('home_advantage', 0.55),
                match_features.get('recent_goals_diff', 0),
                match_features.get('injury_count_diff', 0)
            ]])

            probability = self.ml_model.predict(feature_values)[0]
            return np.clip(probability, 0.01, 0.99)
        except Exception as e:
            logger.error(f"Error predicting with ML model: {e}")
            return 0.5

    def calculate_composite_edge(self,
                                base_edge: float,
                                arb_edge: float,
                                movement_edge: float,
                                ml_probability: float,
                                market_probability: float) -> float:
        """
        Weighted composite edge from all sources

        Weights:
        - Base edge (traditional): 60%
        - Arbitrage: 20%
        - Line movement: 10%
        - ML prediction: 10%
        """
        if market_probability == 0:
            ml_edge = 0
        else:
            ml_edge = ((ml_probability - market_probability) / market_probability) * 100

        composite = (
            (base_edge * 0.60) +
            (arb_edge * 0.20) +
            (movement_edge * 0.10) +
            (ml_edge * 0.10)
        )

        return composite

    def get_confidence_score(self,
                            agreement_level: float,
                            data_points: int,
                            time_to_match: float) -> int:
        """
        1-10 confidence score

        Factors:
        - Agreement between methods (0-3 points)
        - Data points available (0-3 points)
        - Time to match (0-4 points)
        """
        confidence = 0

        # Agreement
        if agreement_level > 0.8:
            confidence += 3
        elif agreement_level > 0.6:
            confidence += 2
        elif agreement_level > 0.4:
            confidence += 1

        # Data points
        if data_points > 20:
            confidence += 3
        elif data_points > 10:
            confidence += 2
        elif data_points > 5:
            confidence += 1

        # Time (more time = more info available)
        if time_to_match > 48:
            confidence += 4
        elif time_to_match > 24:
            confidence += 3
        elif time_to_match > 6:
            confidence += 2
        elif time_to_match > 1:
            confidence += 1

        return min(10, confidence)

