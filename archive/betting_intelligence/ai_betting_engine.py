#!/usr/bin/env python3
"""
🤖 LAYER 2: AI BETTING DECISION ENGINE
======================================
ML-pohjainen päätöksenteko joka muuttaa MatchDataPackage:n kannattaviksi vedonlyöntivinkeiksi.

Vastuualue:
- ML-ennusteet kaikille markkinoille
- Edge-tunnistus (min 5% edge)
- Kelly Criterion panoksen laskenta
- Riski-arviointi ja luottamustasot
- Portfolio-optimointi

Tuotos: BettingRecommendation toiminnallisilla ohjeilla
"""

import logging
import math
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

# Import Layer 1
try:
    from src.perfect_data_engine import MatchDataPackage, TeamStats, PlayerStats, OddsData
    LAYER1_AVAILABLE = True
except ImportError:
    LAYER1_AVAILABLE = False
    logger.warning("⚠️ Layer 1 not available - using fallback")

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Luottamustasot"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class RiskLevel(Enum):
    """Riskitasot"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class MLPrediction:
    """ML-mallin ennuste"""
    outcome: str  # 'home_win', 'away_win', 'draw'
    probability: float  # 0.0 - 1.0
    confidence: float  # 0.0 - 1.0
    model_version: str
    features_used: List[str]
    
    # Lisätiedot
    expected_score: Optional[Tuple[float, float]] = None
    alternative_outcomes: Dict[str, float] = field(default_factory=dict)


@dataclass
class EdgeAnalysis:
    """Edge-analyysi"""
    market: str
    outcome: str
    true_probability: float
    market_probability: float
    edge_percentage: float
    expected_value: float
    
    # Kelly Criterion
    kelly_fraction: float
    optimal_stake_pct: float
    
    # Riskit
    variance: float
    max_loss_probability: float


@dataclass
class BettingRecommendation:
    """
    Toiminnallinen vedonlyöntivinkki Layer 1:n datasta
    """
    # Perusinfo
    match_id: str
    sport: str
    home_team: str
    away_team: str
    match_time: datetime
    
    # Suositus
    recommended_bet: str
    market: str  # 'h2h', 'over_under', 'handicap'
    outcome: str  # 'home', 'away', 'over', 'under'
    
    # Kertoimet ja todennäköisyydet
    best_odds: float
    true_probability: float
    edge_percentage: float
    expected_value: float
    
    # Panokset
    recommended_stake_pct: float  # % of bankroll
    recommended_stake_amount: float  # Actual amount
    kelly_fraction: float
    
    # Riski ja luottamus
    confidence_level: ConfidenceLevel
    risk_level: RiskLevel
    confidence_score: float  # 0.0 - 1.0
    risk_score: float  # 0.0 - 1.0
    
    # Ennusteet
    ml_prediction: MLPrediction
    edge_analysis: EdgeAnalysis
    
    # Perustelut
    reasoning: str
    key_factors: List[str]
    concerns: List[str]
    
    # Vaihtoehdot
    alternative_bets: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    model_version: str = "v1.0"
    
    # Tuotto-odotukset
    expected_profit: float = 0.0
    max_loss: float = 0.0
    profit_probability: float = 0.0


class SportMLModel:
    """ML-malli yhdelle lajille"""
    
    def __init__(self, sport: str):
        self.sport = sport
        self.model_version = "v1.0"
        self.features = self._get_sport_features()
        
        # Simuloi koulutettu malli
        self.is_trained = True
        self.accuracy = 0.68  # 68% accuracy
        
    def _get_sport_features(self) -> List[str]:
        """Hae laji-spesifiset ominaisuudet"""
        if self.sport == 'tennis':
            return [
                'ranking_diff', 'h2h_win_rate', 'recent_form_diff',
                'surface_win_rate', 'serve_percentage_diff', 'break_points_saved_diff',
                'aces_per_match_diff', 'fatigue_factor', 'motivation_score'
            ]
        elif self.sport == 'football':
            return [
                'league_position_diff', 'goals_scored_diff', 'goals_conceded_diff',
                'home_advantage', 'recent_form_diff', 'h2h_win_rate',
                'possession_diff', 'shots_per_game_diff', 'injury_impact'
            ]
        elif self.sport == 'basketball':
            return [
                'points_per_game_diff', 'rebounds_diff', 'assists_diff',
                'field_goal_pct_diff', 'home_advantage', 'recent_form_diff',
                'pace_diff', 'defensive_rating_diff'
            ]
        elif self.sport == 'ice_hockey':
            return [
                'goals_per_game_diff', 'save_percentage_diff', 'power_play_diff',
                'penalty_kill_diff', 'home_advantage', 'recent_form_diff',
                'shots_per_game_diff', 'face_off_pct_diff'
            ]
        else:
            return ['basic_stats', 'form', 'h2h']
    
    def predict(self, package: MatchDataPackage) -> MLPrediction:
        """Tee ennuste ottelulle"""
        
        # Laske ominaisuudet
        features = self._extract_features(package)
        
        # Simuloi ML-ennuste
        # Oikeassa toteutuksessa tässä olisi koulutettu malli
        
        if package.sport == 'tennis':
            # Tennis: vain home/away win
            home_prob = self._calculate_tennis_probability(features, package)
            away_prob = 1.0 - home_prob
            
            if home_prob > away_prob:
                outcome = 'home_win'
                probability = home_prob
            else:
                outcome = 'away_win'
                probability = away_prob
                
        else:
            # Muut lajit: home/draw/away
            home_prob, draw_prob, away_prob = self._calculate_team_probabilities(features, package)
            
            probs = {'home_win': home_prob, 'draw': draw_prob, 'away_win': away_prob}
            outcome = max(probs, key=probs.get)
            probability = probs[outcome]
        
        # Laske luottamus
        confidence = self._calculate_confidence(features, package)
        
        return MLPrediction(
            outcome=outcome,
            probability=probability,
            confidence=confidence,
            model_version=self.model_version,
            features_used=list(features.keys()),
            alternative_outcomes=probs if package.sport != 'tennis' else {'home_win': home_prob, 'away_win': away_prob}
        )
    
    def _extract_features(self, package: MatchDataPackage) -> Dict[str, float]:
        """Pura ominaisuudet datasta"""
        features = {}
        
        if package.sport == 'tennis':
            # Tennis-ominaisuudet
            if package.home_player_stats and package.away_player_stats:
                home_stats = package.home_player_stats
                away_stats = package.away_player_stats
                
                # Ranking difference
                home_rank = home_stats.ranking or 50
                away_rank = away_stats.ranking or 50
                features['ranking_diff'] = (away_rank - home_rank) / 100.0
                
                # Serve percentage difference
                home_serve = home_stats.serve_percentage or 60.0
                away_serve = away_stats.serve_percentage or 60.0
                features['serve_percentage_diff'] = (home_serve - away_serve) / 100.0
                
                # Recent form
                home_form = self._calculate_form_score(home_stats.recent_form)
                away_form = self._calculate_form_score(away_stats.recent_form)
                features['recent_form_diff'] = home_form - away_form
        
        else:
            # Joukkuelaji-ominaisuudet
            if package.home_team_stats and package.away_team_stats:
                home_stats = package.home_team_stats
                away_stats = package.away_team_stats
                
                # Win percentage difference
                features['win_pct_diff'] = home_stats.win_percentage - away_stats.win_percentage
                
                # Recent form
                home_form = self._calculate_form_score(home_stats.recent_form)
                away_form = self._calculate_form_score(away_stats.recent_form)
                features['recent_form_diff'] = home_form - away_form
                
                # Home advantage
                features['home_advantage'] = 0.1  # 10% home advantage
        
        # H2H features
        if package.head_to_head:
            h2h = package.head_to_head
            if h2h.total_matches > 0:
                features['h2h_win_rate'] = h2h.team1_wins / h2h.total_matches
            else:
                features['h2h_win_rate'] = 0.5
        
        return features
    
    def _calculate_form_score(self, form: List[str]) -> float:
        """Laske muoto-pisteet"""
        if not form:
            return 0.0
        
        score = 0.0
        weight = 1.0
        
        for result in form:
            if result == 'W':
                score += weight * 1.0
            elif result == 'D':
                score += weight * 0.5
            # 'L' = 0 points
            
            weight *= 0.8  # Vanhemmat tulokset painotetaan vähemmän
        
        return score / len(form)
    
    def _calculate_tennis_probability(self, features: Dict[str, float], package: MatchDataPackage) -> float:
        """Laske tennis-todennäköisyys"""
        base_prob = 0.5
        
        # Ranking effect
        if 'ranking_diff' in features:
            base_prob += features['ranking_diff'] * 0.3
        
        # Form effect
        if 'recent_form_diff' in features:
            base_prob += features['recent_form_diff'] * 0.2
        
        # Serve advantage
        if 'serve_percentage_diff' in features:
            base_prob += features['serve_percentage_diff'] * 0.15
        
        # H2H effect
        if 'h2h_win_rate' in features:
            base_prob = base_prob * 0.7 + features['h2h_win_rate'] * 0.3
        
        # Ensure probability is between 0.1 and 0.9
        return max(0.1, min(0.9, base_prob))
    
    def _calculate_team_probabilities(self, features: Dict[str, float], package: MatchDataPackage) -> Tuple[float, float, float]:
        """Laske joukkue-todennäköisyydet (home, draw, away)"""
        
        # Base probabilities
        home_prob = 0.4
        draw_prob = 0.3
        away_prob = 0.3
        
        # Form effect
        if 'recent_form_diff' in features:
            form_diff = features['recent_form_diff']
            home_prob += form_diff * 0.2
            away_prob -= form_diff * 0.2
        
        # Home advantage
        if 'home_advantage' in features:
            home_advantage = features['home_advantage']
            home_prob += home_advantage
            away_prob -= home_advantage * 0.5
            draw_prob -= home_advantage * 0.5
        
        # Win percentage effect
        if 'win_pct_diff' in features:
            win_diff = features['win_pct_diff']
            home_prob += win_diff * 0.3
            away_prob -= win_diff * 0.3
        
        # Normalize probabilities
        total = home_prob + draw_prob + away_prob
        home_prob /= total
        draw_prob /= total
        away_prob /= total
        
        return home_prob, draw_prob, away_prob
    
    def _calculate_confidence(self, features: Dict[str, float], package: MatchDataPackage) -> float:
        """Laske luottamus ennusteeseen"""
        confidence = 0.5  # Base confidence
        
        # Data quality effect
        confidence += package.data_quality_score * 0.3
        
        # Feature completeness
        expected_features = len(self.features)
        actual_features = len(features)
        completeness = actual_features / expected_features
        confidence += completeness * 0.2
        
        # Model accuracy effect
        confidence += self.accuracy * 0.3
        
        return min(1.0, confidence)


class AIBettingEngine:
    """
    Layer 2: AI Betting Decision Engine
    
    Muuttaa Layer 1:n MatchDataPackage:n kannattaviksi vedonlyöntivinkeiksi
    käyttäen ML-malleja ja edge-analyysiä.
    """
    
    def __init__(self, bankroll: float = 10000.0, config: Dict[str, Any] = None):
        """
        Initialize AI Betting Engine
        
        Args:
            bankroll: Pankkisaldo
            config: Konfiguraatio
        """
        logger.info("🤖 Initializing AI Betting Engine (Layer 2)...")
        
        self.bankroll = bankroll
        self.config = config or self._load_default_config()
        
        # Initialize ML models for each sport
        self.ml_models = {
            'tennis': SportMLModel('tennis'),
            'football': SportMLModel('football'),
            'basketball': SportMLModel('basketball'),
            'ice_hockey': SportMLModel('ice_hockey')
        }
        
        # Portfolio tracking
        self.active_bets = []
        self.daily_risk = 0.0
        self.monthly_profit = 0.0
        
        logger.info("✅ AI Betting Engine initialized")
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        return {
            'min_edge': 5.0,  # Minimum 5% edge
            'min_confidence': 0.65,  # Minimum 65% confidence
            'kelly_fraction': 0.25,  # Conservative Kelly (25%)
            'max_stake_pct': 5.0,  # Max 5% per bet
            'max_daily_risk': 3.0,  # Max 3% daily risk
            'min_odds': 1.5,  # Minimum odds
            'max_odds': 5.0,  # Maximum odds
            'supported_markets': ['h2h', 'over_under', 'handicap']
        }
    
    def analyze_match(self, package: MatchDataPackage) -> Optional[BettingRecommendation]:
        """
        Analysoi ottelu ja luo vedonlyöntivinkki
        
        Args:
            package: MatchDataPackage Layer 1:stä
            
        Returns:
            BettingRecommendation tai None jos ei kannattavaa
        """
        logger.info(f"🤖 Analyzing match: {package.home_team} vs {package.away_team}")
        
        try:
            # 1. Tarkista että sport on tuettu
            if package.sport not in self.ml_models:
                logger.warning(f"⚠️ Sport {package.sport} not supported")
                return None
            
            # 2. Tarkista datan laatu
            if package.data_quality_score < 0.7:
                logger.warning(f"⚠️ Data quality too low: {package.data_quality_score:.2f}")
                return None
            
            # 3. Tee ML-ennuste
            ml_model = self.ml_models[package.sport]
            prediction = ml_model.predict(package)
            
            # 4. Analysoi edge kaikille markkinoille
            best_edge = None
            best_market = None
            
            for market in self.config['supported_markets']:
                if market in package.best_odds:
                    edge_analysis = self._analyze_edge(prediction, package.best_odds[market], market)
                    
                    if edge_analysis and edge_analysis.edge_percentage >= self.config['min_edge']:
                        if not best_edge or edge_analysis.edge_percentage > best_edge.edge_percentage:
                            best_edge = edge_analysis
                            best_market = market
            
            if not best_edge:
                logger.info("⚠️ No profitable edge found")
                return None
            
            # 5. Tarkista luottamus
            if prediction.confidence < self.config['min_confidence']:
                logger.info(f"⚠️ Confidence too low: {prediction.confidence:.2f}")
                return None
            
            # 6. Laske panokset
            stake_pct, stake_amount = self._calculate_optimal_stake(best_edge)
            
            # 7. Tarkista riskinhallinta
            if not self._check_risk_management(stake_pct):
                logger.info("⚠️ Risk management limits exceeded")
                return None
            
            # 8. Luo suositus
            recommendation = self._create_recommendation(
                package, prediction, best_edge, best_market, stake_pct, stake_amount
            )
            
            logger.info(f"✅ Recommendation created - Edge: {best_edge.edge_percentage:.2f}%, Stake: {stake_pct:.2f}%")
            return recommendation
            
        except Exception as e:
            logger.error(f"❌ Error analyzing match: {e}")
            return None
    
    def _analyze_edge(self, prediction: MLPrediction, market_odds: Dict[str, float], market: str) -> Optional[EdgeAnalysis]:
        """Analysoi edge tietylle markkinalle"""
        
        if market == 'h2h':
            # Match winner market
            if prediction.outcome == 'home_win' and 'home' in market_odds:
                odds = market_odds['home']
                true_prob = prediction.probability
            elif prediction.outcome == 'away_win' and 'away' in market_odds:
                odds = market_odds['away']
                true_prob = prediction.probability
            elif prediction.outcome == 'draw' and 'draw' in market_odds:
                odds = market_odds['draw']
                true_prob = prediction.probability
            else:
                return None
            
            # Calculate edge
            market_prob = 1.0 / odds
            edge_pct = ((true_prob - market_prob) / market_prob) * 100
            
            if edge_pct < self.config['min_edge']:
                return None
            
            # Expected value
            expected_value = (true_prob * (odds - 1)) - (1 - true_prob)
            
            # Kelly fraction
            kelly_fraction = (true_prob * odds - 1) / (odds - 1)
            optimal_stake_pct = kelly_fraction * self.config['kelly_fraction']
            
            return EdgeAnalysis(
                market=market,
                outcome=prediction.outcome,
                true_probability=true_prob,
                market_probability=market_prob,
                edge_percentage=edge_pct,
                expected_value=expected_value,
                kelly_fraction=kelly_fraction,
                optimal_stake_pct=optimal_stake_pct,
                variance=0.5,  # Simplified
                max_loss_probability=1 - true_prob
            )
        
        return None
    
    def _calculate_optimal_stake(self, edge_analysis: EdgeAnalysis) -> Tuple[float, float]:
        """Laske optimaalinen panos"""
        
        # Kelly Criterion with conservative fraction
        kelly_stake_pct = edge_analysis.optimal_stake_pct
        
        # Apply limits
        stake_pct = min(kelly_stake_pct, self.config['max_stake_pct'])
        stake_pct = max(stake_pct, 0.5)  # Minimum 0.5%
        
        # Calculate actual amount
        stake_amount = (stake_pct / 100) * self.bankroll
        
        return stake_pct, stake_amount
    
    def _check_risk_management(self, stake_pct: float) -> bool:
        """Tarkista riskinhallinta"""
        
        # Check daily risk limit
        new_daily_risk = self.daily_risk + stake_pct
        if new_daily_risk > self.config['max_daily_risk']:
            logger.warning(f"⚠️ Daily risk limit exceeded: {new_daily_risk:.2f}% > {self.config['max_daily_risk']}%")
            return False
        
        # Check maximum stake
        if stake_pct > self.config['max_stake_pct']:
            logger.warning(f"⚠️ Stake too high: {stake_pct:.2f}% > {self.config['max_stake_pct']}%")
            return False
        
        return True
    
    def _create_recommendation(self, package: MatchDataPackage, prediction: MLPrediction, 
                             edge_analysis: EdgeAnalysis, market: str, 
                             stake_pct: float, stake_amount: float) -> BettingRecommendation:
        """Luo BettingRecommendation"""
        
        # Determine confidence level
        confidence_level = self._get_confidence_level(prediction.confidence)
        
        # Determine risk level
        risk_level = self._get_risk_level(edge_analysis, stake_pct)
        
        # Calculate expected profit/loss
        odds = 1.0 / edge_analysis.market_probability
        expected_profit = stake_amount * (odds - 1) * edge_analysis.true_probability
        max_loss = stake_amount
        profit_probability = edge_analysis.true_probability
        
        # Generate reasoning
        reasoning = self._generate_reasoning(package, prediction, edge_analysis)
        
        # Key factors
        key_factors = self._identify_key_factors(package, prediction)
        
        # Concerns
        concerns = self._identify_concerns(package, prediction, edge_analysis)
        
        return BettingRecommendation(
            match_id=package.match_id,
            sport=package.sport,
            home_team=package.home_team,
            away_team=package.away_team,
            match_time=package.match_time,
            recommended_bet=f"{prediction.outcome.replace('_', ' ').title()}",
            market=market,
            outcome=prediction.outcome,
            best_odds=1.0 / edge_analysis.market_probability,
            true_probability=edge_analysis.true_probability,
            edge_percentage=edge_analysis.edge_percentage,
            expected_value=edge_analysis.expected_value,
            recommended_stake_pct=stake_pct,
            recommended_stake_amount=stake_amount,
            kelly_fraction=edge_analysis.kelly_fraction,
            confidence_level=confidence_level,
            risk_level=risk_level,
            confidence_score=prediction.confidence,
            risk_score=self._calculate_risk_score(edge_analysis, stake_pct),
            ml_prediction=prediction,
            edge_analysis=edge_analysis,
            reasoning=reasoning,
            key_factors=key_factors,
            concerns=concerns,
            expected_profit=expected_profit,
            max_loss=max_loss,
            profit_probability=profit_probability
        )
    
    def _get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Määritä luottamustaso"""
        if confidence >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif confidence >= 0.8:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.7:
            return ConfidenceLevel.MEDIUM
        elif confidence >= 0.6:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def _get_risk_level(self, edge_analysis: EdgeAnalysis, stake_pct: float) -> RiskLevel:
        """Määritä riskitaso"""
        risk_score = 0
        
        # Edge-based risk
        if edge_analysis.edge_percentage < 10:
            risk_score += 2
        elif edge_analysis.edge_percentage < 15:
            risk_score += 1
        
        # Stake-based risk
        if stake_pct > 4:
            risk_score += 2
        elif stake_pct > 2:
            risk_score += 1
        
        # Variance-based risk
        if edge_analysis.variance > 0.7:
            risk_score += 1
        
        if risk_score >= 4:
            return RiskLevel.VERY_HIGH
        elif risk_score >= 3:
            return RiskLevel.HIGH
        elif risk_score >= 2:
            return RiskLevel.MEDIUM
        elif risk_score >= 1:
            return RiskLevel.LOW
        else:
            return RiskLevel.VERY_LOW
    
    def _calculate_risk_score(self, edge_analysis: EdgeAnalysis, stake_pct: float) -> float:
        """Laske riskipisteet (0-1)"""
        risk_factors = []
        
        # Edge risk
        if edge_analysis.edge_percentage < 10:
            risk_factors.append(0.3)
        elif edge_analysis.edge_percentage < 15:
            risk_factors.append(0.2)
        else:
            risk_factors.append(0.1)
        
        # Stake risk
        risk_factors.append(stake_pct / self.config['max_stake_pct'] * 0.3)
        
        # Variance risk
        risk_factors.append(edge_analysis.variance * 0.2)
        
        # Max loss probability
        risk_factors.append(edge_analysis.max_loss_probability * 0.2)
        
        return min(1.0, sum(risk_factors))
    
    def _generate_reasoning(self, package: MatchDataPackage, prediction: MLPrediction, edge_analysis: EdgeAnalysis) -> str:
        """Generoi perustelut"""
        reasoning = f"ML model predicts {prediction.outcome.replace('_', ' ')} with {prediction.probability*100:.1f}% probability. "
        reasoning += f"Market implies {edge_analysis.market_probability*100:.1f}% probability, giving us {edge_analysis.edge_percentage:.1f}% edge. "
        reasoning += f"Expected value is {edge_analysis.expected_value:.3f}. "
        reasoning += f"Confidence level: {prediction.confidence*100:.1f}%."
        
        return reasoning
    
    def _identify_key_factors(self, package: MatchDataPackage, prediction: MLPrediction) -> List[str]:
        """Tunnista avaintekijät"""
        factors = []
        
        if package.sport == 'tennis':
            if package.home_player_stats and package.away_player_stats:
                home_rank = package.home_player_stats.ranking or 50
                away_rank = package.away_player_stats.ranking or 50
                
                if abs(home_rank - away_rank) > 20:
                    factors.append(f"Significant ranking difference ({home_rank} vs {away_rank})")
        
        if package.head_to_head and package.head_to_head.total_matches > 3:
            h2h = package.head_to_head
            if h2h.team1_wins / h2h.total_matches > 0.7:
                factors.append(f"Strong H2H record ({h2h.team1_wins}/{h2h.total_matches})")
        
        if prediction.confidence > 0.8:
            factors.append("High model confidence")
        
        if len(package.data_sources) >= 3:
            factors.append("Multiple data sources available")
        
        return factors
    
    def _identify_concerns(self, package: MatchDataPackage, prediction: MLPrediction, edge_analysis: EdgeAnalysis) -> List[str]:
        """Tunnista huolenaiheet"""
        concerns = []
        
        if package.data_quality_score < 0.8:
            concerns.append(f"Data quality could be better ({package.data_quality_score:.2f})")
        
        if edge_analysis.edge_percentage < 8:
            concerns.append("Relatively small edge")
        
        if prediction.confidence < 0.7:
            concerns.append("Model confidence not very high")
        
        if edge_analysis.variance > 0.6:
            concerns.append("High variance in outcome")
        
        return concerns
    
    def update_portfolio(self, recommendation: BettingRecommendation):
        """Päivitä portfolio uudella vedolla"""
        self.active_bets.append(recommendation)
        self.daily_risk += recommendation.recommended_stake_pct
        
        logger.info(f"📊 Portfolio updated - Active bets: {len(self.active_bets)}, Daily risk: {self.daily_risk:.2f}%")
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Hae portfolio-yhteenveto"""
        return {
            'active_bets': len(self.active_bets),
            'daily_risk': self.daily_risk,
            'monthly_profit': self.monthly_profit,
            'bankroll': self.bankroll,
            'risk_utilization': self.daily_risk / self.config['max_daily_risk']
        }


async def main():
    """Test AI Betting Engine"""
    print("🤖 AI BETTING ENGINE (LAYER 2) TEST")
    print("=" * 50)
    
    # Import Layer 1 for testing
    if LAYER1_AVAILABLE:
        from src.perfect_data_engine import PerfectDataEngine
        
        # Create test data
        data_engine = PerfectDataEngine()
        packages = await data_engine.get_match_packages(['tennis'], days_ahead=1)
        
        if packages:
            # Test AI engine
            ai_engine = AIBettingEngine(bankroll=10000.0)
            
            print(f"\n🤖 Testing with {len(packages)} match packages...")
            
            recommendations = []
            for package in packages:
                recommendation = ai_engine.analyze_match(package)
                if recommendation:
                    recommendations.append(recommendation)
                    ai_engine.update_portfolio(recommendation)
            
            print(f"✅ Generated {len(recommendations)} betting recommendations")
            
            if recommendations:
                rec = recommendations[0]
                print(f"\n📊 Sample recommendation:")
                print(f"  • Match: {rec.home_team} vs {rec.away_team}")
                print(f"  • Bet: {rec.recommended_bet}")
                print(f"  • Odds: {rec.best_odds:.2f}")
                print(f"  • Edge: {rec.edge_percentage:.2f}%")
                print(f"  • Stake: {rec.recommended_stake_pct:.2f}% (€{rec.recommended_stake_amount:.0f})")
                print(f"  • Confidence: {rec.confidence_level.value}")
                print(f"  • Risk: {rec.risk_level.value}")
                print(f"  • Expected profit: €{rec.expected_profit:.0f}")
            
            # Portfolio summary
            portfolio = ai_engine.get_portfolio_summary()
            print(f"\n📈 Portfolio summary:")
            for key, value in portfolio.items():
                print(f"  • {key}: {value}")
    
    else:
        print("❌ Layer 1 not available for testing")


if __name__ == "__main__":
    asyncio.run(main())
