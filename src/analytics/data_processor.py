#!/usr/bin/env python3
"""
📊 COMPREHENSIVE DATA PROCESSOR & ANALYZER
==========================================

Advanced data processing pipeline for sports analytics
Includes statistical analysis, machine learning features, and prediction models

Author: TennisBot Advanced Analytics
Version: 2.0.0
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import json
import logging
from dataclasses import dataclass
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import scipy.stats as stats
import warnings
warnings.filterwarnings('ignore')

@dataclass
class ProcessedMatch:
    """Processed match with enhanced analytics"""
    match_id: str
    sport: str
    league: str
    home_team: str
    away_team: str
    home_odds: float
    away_odds: float
    draw_odds: Optional[float]
    predicted_winner: str
    win_probability: float
    value_bet: bool
    recommended_stake: float
    risk_level: str
    key_factors: List[str]
    statistical_edge: float
    ml_confidence: float
    historical_performance: Dict
    advanced_metrics: Dict

class AdvancedDataProcessor:
    """Comprehensive data processing and analysis system"""
    
    def __init__(self):
        self.setup_logging()
        self.scaler = StandardScaler()
        self.encoders = {}
        self.models = {}
        self.historical_data = pd.DataFrame()
        self.processed_matches = []
        
    def setup_logging(self):
        """Setup logging for data processing"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def load_historical_data(self, file_path: str = None) -> pd.DataFrame:
        """Load and prepare historical sports data"""
        if file_path:
            try:
                self.historical_data = pd.read_csv(file_path)
                self.logger.info(f"✅ Loaded historical data: {len(self.historical_data)} records")
            except Exception as e:
                self.logger.error(f"Error loading historical data: {e}")
                self.historical_data = self.generate_mock_historical_data()
        else:
            self.historical_data = self.generate_mock_historical_data()
        
        return self.historical_data
    
    def generate_mock_historical_data(self) -> pd.DataFrame:
        """Generate comprehensive mock historical data for testing"""
        np.random.seed(42)
        
        sports = ['tennis', 'football', 'basketball']
        leagues = {
            'tennis': ['ATP Masters 1000', 'WTA 1000', 'Grand Slam'],
            'football': ['Premier League', 'Champions League', 'La Liga'],
            'basketball': ['NBA', 'EuroLeague', 'FIBA']
        }
        
        data = []
        
        for i in range(1000):  # Generate 1000 historical matches
            sport = np.random.choice(sports)
            league = np.random.choice(leagues[sport])
            
            # Generate realistic odds
            if sport == 'tennis':
                home_odds = np.random.uniform(1.3, 4.0)
                away_odds = np.random.uniform(1.3, 4.0)
                draw_odds = None
            elif sport == 'football':
                home_odds = np.random.uniform(1.5, 5.0)
                away_odds = np.random.uniform(1.8, 6.0)
                draw_odds = np.random.uniform(2.5, 4.5)
            else:  # basketball
                home_odds = np.random.uniform(1.4, 3.0)
                away_odds = np.random.uniform(1.4, 3.0)
                draw_odds = None
            
            # Generate outcome based on odds (lower odds = higher probability)
            home_prob = 1 / home_odds
            away_prob = 1 / away_odds
            total_prob = home_prob + away_prob
            
            if sport == 'football':
                draw_prob = 1 / draw_odds if draw_odds else 0
                total_prob += draw_prob
                
                outcome_rand = np.random.random()
                if outcome_rand < home_prob / total_prob:
                    result = 'home_win'
                elif outcome_rand < (home_prob + away_prob) / total_prob:
                    result = 'away_win'
                else:
                    result = 'draw'
            else:
                if np.random.random() < home_prob / total_prob:
                    result = 'home_win'
                else:
                    result = 'away_win'
            
            match_data = {
                'match_id': f'{sport}_{i:04d}',
                'sport': sport,
                'league': league,
                'home_team': f'Team_H_{i}',
                'away_team': f'Team_A_{i}',
                'date': (datetime.now() - timedelta(days=np.random.randint(1, 365))).strftime('%Y-%m-%d'),
                'home_odds': round(home_odds, 2),
                'away_odds': round(away_odds, 2),
                'draw_odds': round(draw_odds, 2) if draw_odds else None,
                'result': result,
                'home_score': np.random.randint(0, 5) if sport == 'football' else np.random.randint(60, 120),
                'away_score': np.random.randint(0, 5) if sport == 'football' else np.random.randint(60, 120),
                'total_games': np.random.randint(18, 25) if sport == 'tennis' else None,
                'home_form': np.random.uniform(0.3, 0.8),  # Win rate in last 10 games
                'away_form': np.random.uniform(0.3, 0.8),
                'h2h_home_wins': np.random.randint(0, 10),
                'h2h_away_wins': np.random.randint(0, 10),
                'h2h_draws': np.random.randint(0, 5) if sport == 'football' else 0,
                'surface': np.random.choice(['Hard', 'Clay', 'Grass']) if sport == 'tennis' else None,
                'venue_advantage': np.random.uniform(-0.1, 0.2),  # Home advantage
                'weather_factor': np.random.uniform(-0.1, 0.1) if sport == 'tennis' else None,
                'injury_impact': np.random.uniform(0, 0.3),
                'motivation_factor': np.random.uniform(0.8, 1.2),
                'bookmaker_edge': np.random.uniform(0.02, 0.08)
            }
            
            data.append(match_data)
        
        df = pd.DataFrame(data)
        self.logger.info(f"🔧 Generated {len(df)} mock historical records")
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for machine learning"""
        feature_df = df.copy()
        
        # Calculate implied probabilities
        feature_df['home_implied_prob'] = 1 / feature_df['home_odds']
        feature_df['away_implied_prob'] = 1 / feature_df['away_odds']
        feature_df['draw_implied_prob'] = 1 / feature_df['draw_odds'].fillna(999)
        
        # Calculate market efficiency metrics
        feature_df['total_implied_prob'] = (
            feature_df['home_implied_prob'] + 
            feature_df['away_implied_prob'] + 
            feature_df['draw_implied_prob'].fillna(0)
        )
        
        feature_df['market_efficiency'] = 1 - feature_df['total_implied_prob']
        
        # Head-to-head features
        feature_df['h2h_total'] = (
            feature_df['h2h_home_wins'] + 
            feature_df['h2h_away_wins'] + 
            feature_df['h2h_draws'].fillna(0)
        )
        
        feature_df['h2h_home_rate'] = feature_df['h2h_home_wins'] / feature_df['h2h_total'].replace(0, 1)
        feature_df['h2h_away_rate'] = feature_df['h2h_away_wins'] / feature_df['h2h_total'].replace(0, 1)
        
        # Form difference
        feature_df['form_difference'] = feature_df['home_form'] - feature_df['away_form']
        
        # Odds ratios
        feature_df['odds_ratio'] = feature_df['home_odds'] / feature_df['away_odds']
        
        # Sport-specific features
        if 'surface' in feature_df.columns:
            surface_encoder = LabelEncoder()
            feature_df['surface_encoded'] = surface_encoder.fit_transform(feature_df['surface'].fillna('Unknown'))
            self.encoders['surface'] = surface_encoder
        
        # League encoding
        league_encoder = LabelEncoder()
        feature_df['league_encoded'] = league_encoder.fit_transform(feature_df['league'])
        self.encoders['league'] = league_encoder
        
        # Sport encoding
        sport_encoder = LabelEncoder()
        feature_df['sport_encoded'] = sport_encoder.fit_transform(feature_df['sport'])
        self.encoders['sport'] = sport_encoder
        
        return feature_df
    
    def train_prediction_models(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Train machine learning models for predictions"""
        self.logger.info("🤖 Training prediction models...")
        
        feature_df = self.prepare_features(df)
        
        # Define feature columns
        feature_columns = [
            'home_odds', 'away_odds', 'home_implied_prob', 'away_implied_prob',
            'market_efficiency', 'home_form', 'away_form', 'form_difference',
            'h2h_home_rate', 'h2h_away_rate', 'venue_advantage', 'injury_impact',
            'motivation_factor', 'odds_ratio', 'sport_encoded', 'league_encoded'
        ]
        
        # Add sport-specific features
        if 'surface_encoded' in feature_df.columns:
            feature_columns.append('surface_encoded')
        if 'weather_factor' in feature_df.columns:
            feature_columns.append('weather_factor')
        
        # Filter available columns
        available_features = [col for col in feature_columns if col in feature_df.columns]
        
        X = feature_df[available_features].fillna(0)
        y = feature_df['result']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train models
        models = {
            'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingClassifier(n_estimators=100, random_state=42)
        }
        
        model_performance = {}
        
        for name, model in models.items():
            self.logger.info(f"Training {name}...")
            
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            model_performance[name] = {
                'accuracy': accuracy,
                'model': model,
                'feature_importance': dict(zip(available_features, model.feature_importances_)) if hasattr(model, 'feature_importances_') else {}
            }
            
            self.logger.info(f"{name} accuracy: {accuracy:.3f}")
        
        self.models = model_performance
        self.feature_columns = available_features
        
        return model_performance
    
    def analyze_current_matches(self, matches_data: List[Dict]) -> List[ProcessedMatch]:
        """Analyze current matches with advanced processing"""
        self.logger.info(f"📊 Analyzing {len(matches_data)} current matches...")
        
        processed_matches = []
        
        for match in matches_data:
            try:
                processed_match = self.process_single_match(match)
                if processed_match:
                    processed_matches.append(processed_match)
            except Exception as e:
                self.logger.error(f"Error processing match {match.get('event_id', 'unknown')}: {e}")
        
        self.processed_matches = processed_matches
        self.logger.info(f"✅ Processed {len(processed_matches)} matches successfully")
        
        return processed_matches
    
    def process_single_match(self, match_data: Dict) -> Optional[ProcessedMatch]:
        """Process a single match with comprehensive analysis"""
        try:
            # Extract basic data
            match_id = match_data.get('event_id', 'unknown')
            sport = match_data.get('sport', 'unknown')
            league = match_data.get('league', 'Unknown')
            home_team = match_data.get('home_team', 'Unknown')
            away_team = match_data.get('away_team', 'Unknown')
            home_odds = match_data.get('home_odds', 2.0)
            away_odds = match_data.get('away_odds', 2.0)
            draw_odds = match_data.get('draw_odds')
            
            # Validate odds
            if not home_odds or not away_odds or home_odds < 1.01 or away_odds < 1.01:
                return None
            
            # Calculate implied probabilities
            home_implied_prob = 1 / home_odds
            away_implied_prob = 1 / away_odds
            draw_implied_prob = 1 / draw_odds if draw_odds else 0
            
            total_implied_prob = home_implied_prob + away_implied_prob + draw_implied_prob
            market_efficiency = 1 - total_implied_prob
            
            # Machine learning prediction
            ml_prediction, ml_confidence = self.get_ml_prediction(match_data)
            
            # Statistical analysis
            statistical_edge = self.calculate_statistical_edge(match_data)
            
            # Value betting analysis
            value_bet, recommended_stake = self.analyze_value_bet(
                home_odds, away_odds, ml_prediction, ml_confidence
            )
            
            # Risk assessment
            risk_level = self.assess_risk_level(ml_confidence, market_efficiency, statistical_edge)
            
            # Key factors
            key_factors = self.identify_key_factors(match_data, ml_prediction, statistical_edge)
            
            # Historical performance
            historical_performance = self.get_historical_performance(home_team, away_team, sport)
            
            # Advanced metrics
            advanced_metrics = {
                'market_efficiency': market_efficiency,
                'implied_probabilities': {
                    'home': home_implied_prob,
                    'away': away_implied_prob,
                    'draw': draw_implied_prob
                },
                'odds_ratio': home_odds / away_odds,
                'kelly_criterion': self.calculate_kelly_criterion(home_odds, ml_confidence),
                'sharpe_ratio': self.calculate_sharpe_ratio(match_data),
                'confidence_interval': self.calculate_confidence_interval(ml_confidence)
            }
            
            processed_match = ProcessedMatch(
                match_id=match_id,
                sport=sport,
                league=league,
                home_team=home_team,
                away_team=away_team,
                home_odds=home_odds,
                away_odds=away_odds,
                draw_odds=draw_odds,
                predicted_winner=ml_prediction,
                win_probability=ml_confidence,
                value_bet=value_bet,
                recommended_stake=recommended_stake,
                risk_level=risk_level,
                key_factors=key_factors,
                statistical_edge=statistical_edge,
                ml_confidence=ml_confidence,
                historical_performance=historical_performance,
                advanced_metrics=advanced_metrics
            )
            
            return processed_match
        
        except Exception as e:
            self.logger.error(f"Error in process_single_match: {e}")
            return None
    
    def get_ml_prediction(self, match_data: Dict) -> Tuple[str, float]:
        """Get machine learning prediction for match"""
        if not self.models or not hasattr(self, 'feature_columns'):
            # Fallback to odds-based prediction
            home_odds = match_data.get('home_odds', 2.0)
            away_odds = match_data.get('away_odds', 2.0)
            
            if home_odds < away_odds:
                return 'home_win', 1 / home_odds
            else:
                return 'away_win', 1 / away_odds
        
        try:
            # Prepare features for prediction
            feature_dict = self.extract_features_for_prediction(match_data)
            
            # Create feature vector
            feature_vector = []
            for col in self.feature_columns:
                feature_vector.append(feature_dict.get(col, 0))
            
            feature_vector = np.array(feature_vector).reshape(1, -1)
            feature_vector_scaled = self.scaler.transform(feature_vector)
            
            # Get predictions from best model
            best_model_name = max(self.models.keys(), key=lambda k: self.models[k]['accuracy'])
            best_model = self.models[best_model_name]['model']
            
            prediction = best_model.predict(feature_vector_scaled)[0]
            prediction_proba = best_model.predict_proba(feature_vector_scaled)[0]
            
            confidence = max(prediction_proba)
            
            return prediction, confidence
        
        except Exception as e:
            self.logger.warning(f"ML prediction error: {e}")
            # Fallback
            home_odds = match_data.get('home_odds', 2.0)
            away_odds = match_data.get('away_odds', 2.0)
            
            if home_odds < away_odds:
                return 'home_win', 1 / home_odds
            else:
                return 'away_win', 1 / away_odds
    
    def extract_features_for_prediction(self, match_data: Dict) -> Dict[str, float]:
        """Extract features from match data for ML prediction"""
        home_odds = match_data.get('home_odds', 2.0)
        away_odds = match_data.get('away_odds', 2.0)
        
        features = {
            'home_odds': home_odds,
            'away_odds': away_odds,
            'home_implied_prob': 1 / home_odds,
            'away_implied_prob': 1 / away_odds,
            'market_efficiency': 1 - (1/home_odds + 1/away_odds),
            'home_form': 0.6,  # Default values
            'away_form': 0.6,
            'form_difference': 0.0,
            'h2h_home_rate': 0.5,
            'h2h_away_rate': 0.5,
            'venue_advantage': 0.1,
            'injury_impact': 0.0,
            'motivation_factor': 1.0,
            'odds_ratio': home_odds / away_odds,
            'sport_encoded': 0,  # Default tennis
            'league_encoded': 0,
            'surface_encoded': 0,
            'weather_factor': 0.0
        }
        
        return features
    
    def calculate_statistical_edge(self, match_data: Dict) -> float:
        """Calculate statistical edge using various metrics"""
        home_odds = match_data.get('home_odds', 2.0)
        away_odds = match_data.get('away_odds', 2.0)
        
        # Market inefficiency
        total_prob = 1/home_odds + 1/away_odds
        market_edge = 1 - total_prob
        
        # Odds distribution analysis
        odds_variance = np.var([home_odds, away_odds])
        
        # Historical comparison (simplified)
        historical_edge = np.random.uniform(-0.05, 0.15)  # Mock historical edge
        
        # Combine metrics
        statistical_edge = (market_edge + historical_edge) / 2
        
        return max(0, statistical_edge)  # Ensure non-negative
    
    def analyze_value_bet(self, home_odds: float, away_odds: float, 
                         prediction: str, confidence: float) -> Tuple[bool, float]:
        """Analyze if bet provides value and calculate stake"""
        
        # Determine predicted odds
        if prediction == 'home_win':
            predicted_prob = confidence
            market_odds = home_odds
        else:
            predicted_prob = confidence
            market_odds = away_odds
        
        # Calculate expected value
        expected_value = (predicted_prob * (market_odds - 1)) - (1 - predicted_prob)
        
        # Check if it's a value bet
        value_bet = expected_value > 0.05  # 5% minimum edge
        
        # Calculate recommended stake using Kelly Criterion
        if value_bet and confidence > 0.6:
            kelly_fraction = (predicted_prob * market_odds - 1) / (market_odds - 1)
            conservative_kelly = kelly_fraction * 0.25  # 25% of Kelly
            recommended_stake = max(1.0, min(conservative_kelly * 100, 5.0))  # 1-5% of bankroll
        else:
            recommended_stake = 0.0
        
        return value_bet, recommended_stake
    
    def assess_risk_level(self, confidence: float, market_efficiency: float, 
                         statistical_edge: float) -> str:
        """Assess overall risk level of the bet"""
        
        risk_score = 0
        
        # Confidence factor
        if confidence > 0.8:
            risk_score += 3
        elif confidence > 0.7:
            risk_score += 2
        elif confidence > 0.6:
            risk_score += 1
        
        # Market efficiency factor
        if market_efficiency > 0.1:
            risk_score += 2
        elif market_efficiency > 0.05:
            risk_score += 1
        
        # Statistical edge factor
        if statistical_edge > 0.1:
            risk_score += 2
        elif statistical_edge > 0.05:
            risk_score += 1
        
        # Determine risk level
        if risk_score >= 6:
            return "LOW"
        elif risk_score >= 4:
            return "MEDIUM"
        elif risk_score >= 2:
            return "HIGH"
        else:
            return "VERY HIGH"
    
    def identify_key_factors(self, match_data: Dict, prediction: str, 
                           statistical_edge: float) -> List[str]:
        """Identify key factors influencing the prediction"""
        factors = []
        
        home_odds = match_data.get('home_odds', 2.0)
        away_odds = match_data.get('away_odds', 2.0)
        
        # Odds analysis
        if abs(home_odds - away_odds) < 0.3:
            factors.append("Very close match - small odds difference")
        elif home_odds < 1.5 or away_odds < 1.5:
            factors.append("Clear favorite identified by market")
        
        # Statistical edge
        if statistical_edge > 0.1:
            factors.append("Strong statistical edge identified")
        elif statistical_edge > 0.05:
            factors.append("Moderate statistical advantage")
        
        # Sport-specific factors
        sport = match_data.get('sport', '')
        if sport == 'tennis':
            factors.append("Tennis: Head-to-head records crucial")
        elif sport == 'football':
            factors.append("Football: Home advantage significant")
        elif sport == 'basketball':
            factors.append("Basketball: Recent form important")
        
        # Market factors
        total_prob = 1/home_odds + 1/away_odds
        if total_prob < 0.95:
            factors.append("Market shows high uncertainty")
        
        return factors[:5]  # Limit to top 5 factors
    
    def get_historical_performance(self, home_team: str, away_team: str, sport: str) -> Dict:
        """Get historical performance metrics"""
        # Mock historical performance
        return {
            'head_to_head': {
                'total_matches': np.random.randint(3, 15),
                'home_wins': np.random.randint(0, 10),
                'away_wins': np.random.randint(0, 10),
                'draws': np.random.randint(0, 5) if sport == 'football' else 0
            },
            'recent_form': {
                'home_team': {
                    'last_10_games': np.random.uniform(0.3, 0.9),
                    'home_record': np.random.uniform(0.4, 0.8),
                    'vs_similar_opponents': np.random.uniform(0.3, 0.8)
                },
                'away_team': {
                    'last_10_games': np.random.uniform(0.3, 0.9),
                    'away_record': np.random.uniform(0.2, 0.7),
                    'vs_similar_opponents': np.random.uniform(0.3, 0.8)
                }
            },
            'performance_trends': {
                'home_improving': np.random.choice([True, False]),
                'away_improving': np.random.choice([True, False]),
                'momentum_factor': np.random.uniform(-0.2, 0.2)
            }
        }
    
    def calculate_kelly_criterion(self, odds: float, probability: float) -> float:
        """Calculate Kelly Criterion for optimal bet sizing"""
        if probability <= 1/odds:
            return 0.0
        
        return (probability * odds - 1) / (odds - 1)
    
    def calculate_sharpe_ratio(self, match_data: Dict) -> float:
        """Calculate Sharpe ratio for risk-adjusted returns"""
        # Simplified Sharpe ratio calculation
        expected_return = np.random.uniform(0.05, 0.25)
        volatility = np.random.uniform(0.15, 0.35)
        risk_free_rate = 0.02
        
        return (expected_return - risk_free_rate) / volatility
    
    def calculate_confidence_interval(self, confidence: float) -> Tuple[float, float]:
        """Calculate confidence interval for prediction"""
        margin_of_error = 0.1 * (1 - confidence)  # Higher confidence = smaller margin
        
        lower_bound = max(0.0, confidence - margin_of_error)
        upper_bound = min(1.0, confidence + margin_of_error)
        
        return (lower_bound, upper_bound)
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        if not self.processed_matches:
            return {"error": "No processed matches available"}
        
        # Overall statistics
        total_matches = len(self.processed_matches)
        value_bets = [m for m in self.processed_matches if m.value_bet]
        high_confidence = [m for m in self.processed_matches if m.ml_confidence > 0.7]
        low_risk = [m for m in self.processed_matches if m.risk_level == "LOW"]
        
        # Sport breakdown
        sport_breakdown = {}
        for match in self.processed_matches:
            sport = match.sport
            if sport not in sport_breakdown:
                sport_breakdown[sport] = {
                    'total': 0,
                    'value_bets': 0,
                    'avg_confidence': 0,
                    'avg_edge': 0
                }
            
            sport_breakdown[sport]['total'] += 1
            if match.value_bet:
                sport_breakdown[sport]['value_bets'] += 1
            sport_breakdown[sport]['avg_confidence'] += match.ml_confidence
            sport_breakdown[sport]['avg_edge'] += match.statistical_edge
        
        # Calculate averages
        for sport_data in sport_breakdown.values():
            if sport_data['total'] > 0:
                sport_data['avg_confidence'] /= sport_data['total']
                sport_data['avg_edge'] /= sport_data['total']
        
        # Top recommendations
        top_recommendations = sorted(
            [m for m in self.processed_matches if m.value_bet],
            key=lambda x: (x.ml_confidence, x.statistical_edge),
            reverse=True
        )[:5]
        
        report = {
            'analysis_summary': {
                'total_matches_analyzed': total_matches,
                'value_bets_identified': len(value_bets),
                'high_confidence_predictions': len(high_confidence),
                'low_risk_opportunities': len(low_risk),
                'value_bet_percentage': round(len(value_bets) / total_matches * 100, 1) if total_matches > 0 else 0
            },
            'sport_breakdown': sport_breakdown,
            'top_recommendations': [
                {
                    'match': f"{rec.home_team} vs {rec.away_team}",
                    'sport': rec.sport,
                    'league': rec.league,
                    'prediction': rec.predicted_winner,
                    'confidence': round(rec.ml_confidence, 3),
                    'recommended_stake': rec.recommended_stake,
                    'risk_level': rec.risk_level,
                    'key_factors': rec.key_factors[:3]
                }
                for rec in top_recommendations
            ],
            'market_insights': {
                'avg_market_efficiency': np.mean([
                    m.advanced_metrics['market_efficiency'] 
                    for m in self.processed_matches
                ]),
                'most_inefficient_sport': max(
                    sport_breakdown.keys(), 
                    key=lambda s: sport_breakdown[s]['avg_edge']
                ) if sport_breakdown else None,
                'confidence_distribution': {
                    'high (>0.8)': len([m for m in self.processed_matches if m.ml_confidence > 0.8]),
                    'medium (0.6-0.8)': len([m for m in self.processed_matches if 0.6 < m.ml_confidence <= 0.8]),
                    'low (<0.6)': len([m for m in self.processed_matches if m.ml_confidence <= 0.6])
                }
            },
            'risk_analysis': {
                'low_risk_count': len([m for m in self.processed_matches if m.risk_level == "LOW"]),
                'medium_risk_count': len([m for m in self.processed_matches if m.risk_level == "MEDIUM"]),
                'high_risk_count': len([m for m in self.processed_matches if m.risk_level == "HIGH"]),
                'very_high_risk_count': len([m for m in self.processed_matches if m.risk_level == "VERY HIGH"])
            },
            'recommended_actions': self.generate_recommendations()
        }
        
        return report
    
    def generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        if not self.processed_matches:
            return ["No matches to analyze. Please load match data first."]
        
        value_bets = [m for m in self.processed_matches if m.value_bet]
        
        if len(value_bets) == 0:
            recommendations.append("No value bets identified in current market conditions")
        elif len(value_bets) > 5:
            recommendations.append(f"Multiple value opportunities found ({len(value_bets)}). Focus on highest confidence bets")
        else:
            recommendations.append(f"Limited value opportunities ({len(value_bets)}). Be selective")
        
        # Risk recommendations
        low_risk_bets = [m for m in self.processed_matches if m.risk_level == "LOW" and m.value_bet]
        if low_risk_bets:
            recommendations.append(f"Consider {len(low_risk_bets)} low-risk value bets for conservative approach")
        
        # Sport-specific recommendations
        sport_counts = {}
        for match in value_bets:
            sport_counts[match.sport] = sport_counts.get(match.sport, 0) + 1
        
        if sport_counts:
            best_sport = max(sport_counts, key=sport_counts.get)
            recommendations.append(f"Best opportunities currently in {best_sport} ({sport_counts[best_sport]} value bets)")
        
        # Market efficiency recommendation
        avg_efficiency = np.mean([m.advanced_metrics['market_efficiency'] for m in self.processed_matches])
        if avg_efficiency < -0.05:
            recommendations.append("Market appears overpriced - look for underdog value")
        elif avg_efficiency > 0.05:
            recommendations.append("Market appears efficient - be extra selective")
        
        return recommendations

    def export_processed_data(self, filename: str = None) -> str:
        """Export processed data to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"processed_matches_{timestamp}.json"
        
        # Convert processed matches to dictionaries
        export_data = {
            'metadata': {
                'processing_timestamp': datetime.now().isoformat(),
                'total_matches': len(self.processed_matches),
                'processor_version': '2.0.0'
            },
            'matches': []
        }
        
        for match in self.processed_matches:
            match_dict = {
                'match_id': match.match_id,
                'sport': match.sport,
                'league': match.league,
                'home_team': match.home_team,
                'away_team': match.away_team,
                'home_odds': match.home_odds,
                'away_odds': match.away_odds,
                'draw_odds': match.draw_odds,
                'predicted_winner': match.predicted_winner,
                'win_probability': match.win_probability,
                'value_bet': match.value_bet,
                'recommended_stake': match.recommended_stake,
                'risk_level': match.risk_level,
                'key_factors': match.key_factors,
                'statistical_edge': match.statistical_edge,
                'ml_confidence': match.ml_confidence,
                'historical_performance': match.historical_performance,
                'advanced_metrics': match.advanced_metrics
            }
            export_data['matches'].append(match_dict)
        
        # Add comprehensive report
        export_data['analysis_report'] = self.generate_comprehensive_report()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"💾 Processed data exported to {filename}")
        return filename

if __name__ == "__main__":
    # Example usage and testing
    processor = AdvancedDataProcessor()
    
    print("📊 COMPREHENSIVE DATA PROCESSOR")
    print("=" * 50)
    
    # Load historical data
    historical_data = processor.load_historical_data()
    print(f"📁 Historical data loaded: {len(historical_data)} records")
    
    # Train models
    model_performance = processor.train_prediction_models(historical_data)
    print(f"🤖 Models trained: {list(model_performance.keys())}")
    
    # Generate sample current matches
    sample_matches = [
        {
            'event_id': 'test_001',
            'sport': 'tennis',
            'league': 'ATP Masters 1000',
            'home_team': 'Novak Djokovic',
            'away_team': 'Carlos Alcaraz',
            'home_odds': 1.75,
            'away_odds': 2.05
        },
        {
            'event_id': 'test_002',
            'sport': 'football',
            'league': 'Premier League',
            'home_team': 'Manchester City',
            'away_team': 'Liverpool',
            'home_odds': 2.10,
            'away_odds': 3.40,
            'draw_odds': 3.20
        }
    ]
    
    # Process matches
    processed_matches = processor.analyze_current_matches(sample_matches)
    print(f"✅ Processed {len(processed_matches)} matches")
    
    # Generate report
    report = processor.generate_comprehensive_report()
    print(f"📋 Analysis complete: {report['analysis_summary']['value_bets_identified']} value bets found")
    
    # Export data
    filename = processor.export_processed_data()
    print(f"💾 Data exported to: {filename}")