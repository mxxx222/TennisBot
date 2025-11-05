#!/usr/bin/env python3
"""
BUSINESS INTELLIGENCE SYSTEM - Market Analysis Framework
========================================================

Educational implementation of market analysis and competitive intelligence
techniques using data-driven insights and pattern recognition.

⚠️  EDUCATIONAL PURPOSES ONLY - NO REAL MONEY
⚠️  This system demonstrates BI concepts, data analysis, and market
    intelligence techniques for educational purposes.

Author: Betfury.io Educational Research System
License: Educational Use Only
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime, timedelta
import logging
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class MarketPhase(Enum):
    """Educational market phases for pattern recognition"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down" 
    CONSOLIDATION = "consolidation"
    VOLATILE = "volatile"
    UNKNOWN = "unknown"


class SentimentLevel(Enum):
    """Educational sentiment classification"""
    VERY_BEARISH = "very_bearish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    BULLISH = "bullish"
    VERY_BULLISH = "very_bullish"


@dataclass
class EducationalMarketData:
    """Educational market data structure"""
    symbol: str
    timestamp: datetime
    price: float
    volume: int
    high: float
    low: float
    open: float
    close: float
    market_cap: Optional[float] = None
    sector: Optional[str] = None
    volatility: Optional[float] = None


@dataclass
class EducationalSignal:
    """Educational market signal with confidence scoring"""
    symbol: str
    signal_type: str  # buy, sell, hold, warning
    confidence: float  # 0-1 scale
    price_target: Optional[float] = None
    stop_loss: Optional[float] = None
    timeframe: str = "medium_term"
    reasoning: str = ""
    technical_score: float = 0.0
    sentiment_score: float = 0.0
    momentum_score: float = 0.0


@dataclass
class MarketIntelligenceReport:
    """Comprehensive market analysis report"""
    report_id: str
    timestamp: datetime
    market_phase: MarketPhase
    sentiment: SentimentLevel
    volatility_index: float
    signals: List[EducationalSignal]
    risk_assessment: str
    key_insights: List[str]
    educational_notes: List[str] = field(default_factory=list)


class TechnicalAnalyzer:
    """Educational technical analysis for pattern recognition"""
    
    def __init__(self, period: int = 20):
        """Initialize with educational lookback period"""
        self.period = period
    
    def calculate_sma(self, data: pd.Series, window: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return data.rolling(window=window).mean()
    
    def calculate_ema(self, data: pd.Series, window: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return data.ewm(span=window).mean()
    
    def calculate_rsi(self, data: pd.Series, window: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD indicator"""
        ema_fast = self.calculate_ema(data, fast)
        ema_slow = self.calculate_ema(data, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = self.calculate_ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def calculate_bollinger_bands(self, data: pd.Series, window: int = 20, num_std: float = 2) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = self.calculate_sma(data, window)
        std = data.rolling(window=window).std()
        
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        
        return {
            'upper': upper_band,
            'middle': sma,
            'lower': lower_band
        }
    
    def identify_patterns(self, data: pd.DataFrame) -> Dict[str, float]:
        """Identify educational technical patterns"""
        if len(data) < self.period:
            return {'pattern_strength': 0.0, 'pattern_type': 'insufficient_data'}
        
        latest = data.iloc[-1]
        previous = data.iloc[-5:-1]  # Look at 4 previous periods
        
        patterns = {}
        
        # Trend patterns
        if latest['close'] > data['close'].rolling(self.period//2).mean().iloc[-1]:
            patterns['uptrend'] = min(1.0, (latest['close'] / data['close'].rolling(self.period//2).mean().iloc[-1] - 1) * 10)
        else:
            patterns['downtrend'] = min(1.0, (1 - latest['close'] / data['close'].rolling(self.period//2).mean().iloc[-1]) * 10)
        
        # Volatility patterns
        recent_volatility = data['close'].pct_change().rolling(10).std().iloc[-1]
        historical_volatility = data['close'].pct_change().std()
        
        if recent_volatility > historical_volatility * 1.5:
            patterns['high_volatility'] = min(1.0, (recent_volatility / historical_volatility - 1))
        else:
            patterns['low_volatility'] = min(1.0, (historical_volatility / recent_volatility - 1))
        
        # Support/Resistance levels
        recent_high = data['high'].rolling(self.period//2).max().iloc[-1]
        recent_low = data['low'].rolling(self.period//2).min().iloc[-1]
        
        price_position = (latest['close'] - recent_low) / (recent_high - recent_low)
        patterns['support_resistance_level'] = price_position
        
        # Pattern strength (combination of all factors)
        pattern_strength = np.mean(list(patterns.values())) if patterns else 0.0
        
        return {
            'pattern_strength': pattern_strength,
            'pattern_details': patterns,
            'price_position': price_position,
            'trend_direction': 'up' if patterns.get('uptrend', 0) > patterns.get('downtrend', 0) else 'down'
        }


class SentimentAnalyzer:
    """Educational sentiment analysis for market mood"""
    
    def __init__(self):
        """Initialize educational sentiment analyzer"""
        self.sentiment_keywords = {
            'very_bullish': ['breakthrough', 'outperform', 'strong momentum', 'excellent', 'exceptional'],
            'bullish': ['positive', 'growth', 'improvement', 'good', 'solid'],
            'neutral': ['mixed', 'stable', 'moderate', 'balanced', 'steady'],
            'bearish': ['decline', 'weak', 'concerns', 'risk', 'pressure'],
            'very_bearish': ['crisis', 'crash', 'collapse', 'severe', 'dire']
        }
    
    def analyze_market_sentiment(self, 
                                news_sentiment: List[str],
                                social_sentiment: List[str],
                                technical_sentiment: Dict[str, float]) -> Dict[str, Any]:
        """Analyze overall market sentiment from multiple sources"""
        
        # Score sentiment from text sources
        news_score = self._score_text_sentiment(news_sentiment)
        social_score = self._score_text_sentiment(social_sentiment)
        
        # Technical sentiment (already numerical)
        tech_score = np.mean(list(technical_sentiment.values())) if technical_sentiment else 0.5
        
        # Combined sentiment score
        combined_sentiment = (news_score * 0.4 + social_score * 0.3 + tech_score * 0.3)
        
        # Determine sentiment level
        if combined_sentiment >= 0.8:
            sentiment_level = SentimentLevel.VERY_BULLISH
        elif combined_sentiment >= 0.6:
            sentiment_level = SentimentLevel.BULLISH
        elif combined_sentiment >= 0.4:
            sentiment_level = SentimentLevel.NEUTRAL
        elif combined_sentiment >= 0.2:
            sentiment_level = SentimentLevel.BEARISH
        else:
            sentiment_level = SentimentLevel.VERY_BEARISH
        
        # Calculate sentiment confidence
        sentiment_variance = np.var([news_score, social_score, tech_score])
        confidence = max(0.5, 1.0 - sentiment_variance)  # Higher confidence with less variance
        
        return {
            'sentiment_score': combined_sentiment,
            'sentiment_level': sentiment_level,
            'confidence': confidence,
            'component_scores': {
                'news_sentiment': news_score,
                'social_sentiment': social_score,
                'technical_sentiment': tech_score
            },
            'sentiment_strength': abs(combined_sentiment - 0.5) * 2  # 0-1 scale
        }
    
    def _score_text_sentiment(self, texts: List[str]) -> float:
        """Score sentiment from text using keyword matching"""
        if not texts:
            return 0.5  # Neutral if no data
        
        total_score = 0.0
        text_count = 0
        
        for text in texts:
            text_lower = text.lower()
            
            for level, keywords in self.sentiment_keywords.items():
                keyword_score = sum(1 for keyword in keywords if keyword in text_lower)
                if keyword_score > 0:
                    # Convert level to score (0-1 scale)
                    if level == 'very_bullish':
                        total_score += 1.0 * keyword_score
                    elif level == 'bullish':
                        total_score += 0.8 * keyword_score
                    elif level == 'neutral':
                        total_score += 0.5 * keyword_score
                    elif level == 'bearish':
                        total_score += 0.2 * keyword_score
                    elif level == 'very_bearish':
                        total_score += 0.0 * keyword_score
                    
                    text_count += keyword_score
        
        # Average score across all texts and keywords
        if text_count == 0:
            return 0.5
        
        return min(1.0, total_score / text_count)


class MarketPhaseDetector:
    """Educational market phase detection system"""
    
    def __init__(self):
        """Initialize educational market phase detector"""
        self.phase_indicators = {
            MarketPhase.TRENDING_UP: {
                'price_momentum': 0.7,
                'volume_trend': 0.6,
                'volatility': 0.3,
                'rsi_range': (50, 70)
            },
            MarketPhase.TRENDING_DOWN: {
                'price_momentum': -0.7,
                'volume_trend': -0.6,
                'volatility': 0.4,
                'rsi_range': (30, 50)
            },
            MarketPhase.CONSOLIDATION: {
                'price_momentum': 0.1,
                'volume_trend': 0.0,
                'volatility': 0.2,
                'rsi_range': (40, 60)
            },
            MarketPhase.VOLATILE: {
                'price_momentum': 0.0,
                'volume_trend': 0.8,
                'volatility': 0.9,
                'rsi_range': (20, 80)
            }
        }
    
    def detect_market_phase(self, 
                          market_data: List[EducationalMarketData],
                          price_momentum: float,
                          volume_trend: float,
                          current_volatility: float,
                          current_rsi: float) -> Dict[str, Any]:
        """Detect current market phase using multiple indicators"""
        
        phase_scores = {}
        
        for phase, indicators in self.phase_indicators.items():
            score = 0.0
            weight_sum = 0.0
            
            # Price momentum score
            momentum_diff = abs(price_momentum - indicators['price_momentum'])
            momentum_score = max(0, 1 - momentum_diff)
            score += momentum_score * 0.3
            weight_sum += 0.3
            
            # Volume trend score
            volume_diff = abs(volume_trend - indicators['volume_trend'])
            volume_score = max(0, 1 - volume_diff)
            score += volume_score * 0.2
            weight_sum += 0.2
            
            # Volatility score
            vol_diff = abs(current_volatility - indicators['volatility'])
            vol_score = max(0, 1 - vol_diff)
            score += vol_score * 0.2
            weight_sum += 0.2
            
            # RSI range score
            rsi_min, rsi_max = indicators['rsi_range']
            if rsi_min <= current_rsi <= rsi_max:
                rsi_score = 1.0 - abs(current_rsi - (rsi_min + rsi_max) / 2) / (rsi_max - rsi_min)
            else:
                rsi_score = 0.0
            score += rsi_score * 0.3
            weight_sum += 0.3
            
            # Normalize score
            if weight_sum > 0:
                phase_scores[phase] = score / weight_sum
            else:
                phase_scores[phase] = 0.0
        
        # Find dominant phase
        dominant_phase = max(phase_scores.items(), key=lambda x: x[1])
        
        return {
            'current_phase': dominant_phase[0],
            'phase_confidence': dominant_phase[1],
            'phase_scores': phase_scores,
            'phase_characteristics': {
                'price_momentum': price_momentum,
                'volume_trend': volume_trend,
                'volatility': current_volatility,
                'rsi': current_rsi
            }
        }


class CompetitiveAnalyzer:
    """Educational competitive analysis for market positioning"""
    
    def __init__(self):
        """Initialize competitive analyzer"""
        self.competitive_metrics = [
            'market_share', 'growth_rate', 'profit_margin', 'innovation_score',
            'customer_satisfaction', 'operational_efficiency', 'brand_strength'
        ]
    
    def analyze_competitive_landscape(self, 
                                    competitor_data: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Analyze competitive landscape using clustering and positioning"""
        
        # Prepare data for analysis
        if not competitor_data:
            return {'error': 'No competitor data provided'}
        
        companies = list(competitor_data.keys())
        metrics = list(next(iter(competitor_data.values())).keys())
        
        # Create data matrix
        data_matrix = np.array([[competitor_data[company][metric] 
                               for metric in metrics] 
                               for company in companies])
        
        # Standardize data
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(data_matrix)
        
        # K-means clustering
        n_clusters = min(3, len(companies))  # Maximum 3 clusters
        if n_clusters > 1:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(scaled_data)
            
            # PCA for 2D visualization
            pca = PCA(n_components=2)
            pca_data = pca.fit_transform(scaled_data)
        else:
            clusters = np.zeros(len(companies))
            pca_data = scaled_data
        
        # Analyze each cluster
        cluster_analysis = {}
        for cluster_id in range(n_clusters):
            cluster_companies = [companies[i] for i, c in enumerate(clusters) if c == cluster_id]
            cluster_data = data_matrix[[i for i, c in enumerate(clusters) if c == cluster_id]]
            
            cluster_analysis[f'cluster_{cluster_id}'] = {
                'companies': cluster_companies,
                'size': len(cluster_companies),
                'characteristics': {
                    metric: {
                        'mean': np.mean(cluster_data[:, idx]),
                        'std': np.std(cluster_data[:, idx])
                    }
                    for idx, metric in enumerate(metrics)
                }
            }
        
        # Identify market leaders and challengers
        market_positions = self._calculate_market_positions(data_matrix, metrics, companies)
        
        return {
            'competitive_clusters': cluster_analysis,
            'market_positions': market_positions,
            'pca_explained_variance': float(pca.explained_variance_ratio_.sum()) if 'pca' in locals() else 0.0,
            'total_companies': len(companies),
            'key_metrics': metrics
        }
    
    def _calculate_market_positions(self, 
                                  data_matrix: np.ndarray, 
                                  metrics: List[str], 
                                  companies: List[str]) -> Dict[str, Dict[str, str]]:
        """Calculate market positions for each company"""
        
        positions = {}
        
        # Normalize metrics to 0-1 scale for comparison
        normalized_data = (data_matrix - data_matrix.min(axis=0)) / (data_matrix.max(axis=0) - data_matrix.min(axis=0))
        
        for i, company in enumerate(companies):
            company_scores = normalized_data[i]
            
            # Calculate overall strength
            overall_strength = np.mean(company_scores)
            
            # Determine position
            if overall_strength >= 0.7:
                position = 'Market Leader'
            elif overall_strength >= 0.5:
                position = 'Strong Competitor'
            elif overall_strength >= 0.3:
                position = 'Moderate Player'
            else:
                position = 'Niche Player'
            
            # Find strongest and weakest areas
            strongest_metric = metrics[np.argmax(company_scores)]
            weakest_metric = metrics[np.argmin(company_scores)]
            
            positions[company] = {
                'overall_strength': overall_strength,
                'market_position': position,
                'strongest_area': strongest_metric,
                'weakest_area': weakest_metric,
                'strength_score': float(np.max(company_scores)),
                'weakness_score': float(np.min(company_scores))
            }
        
        return positions


class RiskIntelligence:
    """Educational risk intelligence system"""
    
    def __init__(self):
        """Initialize risk intelligence analyzer"""
        self.risk_factors = {
            'market_volatility': {'weight': 0.3, 'max_value': 0.5},
            'liquidity_risk': {'weight': 0.2, 'max_value': 0.8},
            'concentration_risk': {'weight': 0.2, 'max_value': 0.6},
            'operational_risk': {'weight': 0.15, 'max_value': 0.4},
            'regulatory_risk': {'weight': 0.15, 'max_value': 0.7}
        }
    
    def assess_portfolio_risk(self, 
                            portfolio_data: Dict[str, Any],
                            market_conditions: Dict[str, float]) -> Dict[str, Any]:
        """Assess educational portfolio risk using multiple factors"""
        
        risk_scores = {}
        total_risk = 0.0
        weight_sum = 0.0
        
        # Calculate individual risk scores
        for risk_factor, config in self.risk_factors.items():
            weight = config['weight']
            max_value = config['max_value']
            
            if risk_factor == 'market_volatility':
                current_vol = market_conditions.get('volatility', 0.2)
                risk_score = min(1.0, current_vol / max_value)
                
            elif risk_factor == 'liquidity_risk':
                # Lower liquidity = higher risk
                avg_volume = portfolio_data.get('average_daily_volume', 1000000)
                liquidity_score = max(0, 1 - (avg_volume / 10000000))  # Normalize around 10M
                risk_score = min(1.0, liquidity_score)
                
            elif risk_factor == 'concentration_risk':
                # Higher concentration = higher risk
                top_holdings = portfolio_data.get('top_5_holdings_pct', 50)
                concentration_score = min(1.0, top_holdings / 100)
                risk_score = concentration_score
                
            elif risk_factor == 'operational_risk':
                # Educational proxy for operational efficiency
                portfolio_data_score = portfolio_data.get('data_quality_score', 0.8)
                risk_score = max(0, 1 - portfolio_data_score)
                
            else:  # regulatory_risk
                # Educational proxy for regulatory environment
                reg_environment = market_conditions.get('regulatory_stability', 0.8)
                risk_score = max(0, 1 - reg_environment)
            
            risk_scores[risk_factor] = risk_score
            total_risk += risk_score * weight
            weight_sum += weight
        
        # Overall risk score
        overall_risk = total_risk / weight_sum if weight_sum > 0 else 0.0
        
        # Risk classification
        if overall_risk >= 0.7:
            risk_level = 'High'
        elif overall_risk >= 0.4:
            risk_level = 'Medium'
        else:
            risk_level = 'Low'
        
        # Generate educational recommendations
        recommendations = self._generate_risk_recommendations(risk_scores, overall_risk)
        
        return {
            'overall_risk_score': overall_risk,
            'risk_level': risk_level,
            'individual_risks': risk_scores,
            'risk_contributors': sorted(risk_scores.items(), key=lambda x: x[1], reverse=True),
            'recommendations': recommendations,
            'risk_trend': 'stable'  # Educational placeholder
        }
    
    def _generate_risk_recommendations(self, risk_scores: Dict[str, float], overall_risk: float) -> List[str]:
        """Generate educational risk management recommendations"""
        
        recommendations = []
        
        if risk_scores.get('market_volatility', 0) > 0.6:
            recommendations.append("Consider reducing position sizes to manage volatility exposure")
            
        if risk_scores.get('concentration_risk', 0) > 0.5:
            recommendations.append("Diversify portfolio to reduce concentration risk")
            
        if risk_scores.get('liquidity_risk', 0) > 0.4:
            recommendations.append("Focus on more liquid positions for better risk management")
            
        if overall_risk > 0.6:
            recommendations.append("Overall portfolio risk is elevated - consider defensive positioning")
            
        if len(recommendations) == 0:
            recommendations.append("Portfolio risk levels are within acceptable educational ranges")
        
        return recommendations


class BusinessIntelligenceEngine:
    """Main Business Intelligence engine for educational market analysis"""
    
    def __init__(self):
        """Initialize BI engine with all components"""
        self.technical_analyzer = TechnicalAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.phase_detector = MarketPhaseDetector()
        self.competitive_analyzer = CompetitiveAnalyzer()
        self.risk_intelligence = RiskIntelligence()
    
    def generate_intelligence_report(self, 
                                   market_data: List[EducationalMarketData],
                                   news_data: List[str],
                                   social_data: List[str],
                                   competitor_data: Dict[str, Dict[str, float]],
                                   portfolio_data: Dict[str, Any]) -> MarketIntelligenceReport:
        """Generate comprehensive educational market intelligence report"""
        
        if not market_data:
            return MarketIntelligenceReport(
                report_id=f"EDU_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(),
                market_phase=MarketPhase.UNKNOWN,
                sentiment=SentimentLevel.NEUTRAL,
                volatility_index=0.0,
                signals=[],
                risk_assessment="Insufficient data for analysis",
                key_insights=["Market data is required for comprehensive analysis"],
                educational_notes=["This is an educational framework for learning BI concepts"]
            )
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame([{
            'timestamp': data.timestamp,
            'price': data.price,
            'volume': data.volume,
            'high': data.high,
            'low': data.low,
            'open': data.open,
            'close': data.close
        } for data in market_data])
        
        df.set_index('timestamp', inplace=True)
        
        # Technical analysis
        latest_price = df['close'].iloc[-1]
        technical_patterns = self.technical_analyzer.identify_patterns(df)
        
        # Calculate technical indicators
        rsi = self.technical_analyzer.calculate_rsi(df['close']).iloc[-1]
        sma_20 = self.technical_analyzer.calculate_sma(df['close'], 20).iloc[-1]
        macd_data = self.technical_analyzer.calculate_macd(df['close'])
        macd_signal = macd_data['macd'].iloc[-1]
        
        # Price momentum and volume trend
        price_change_20d = (latest_price - df['close'].iloc[-20]) / df['close'].iloc[-20]
        volume_trend = (df['volume'].tail(10).mean() / df['volume'].iloc[-20:-10].mean() - 1)
        
        # Market phase detection
        phase_analysis = self.phase_detector.detect_market_phase(
            market_data, price_change_20d, volume_trend, 
            technical_patterns.get('pattern_strength', 0.5), rsi
        )
        
        # Sentiment analysis
        technical_sentiment = {
            'rsi_sentiment': (rsi - 50) / 50,  # Normalize to -1 to 1
            'trend_sentiment': price_change_20d * 10,  # Scale trend
            'momentum_sentiment': technical_patterns.get('pattern_strength', 0.5) - 0.5
        }
        
        sentiment_analysis = self.sentiment_analyzer.analyze_market_sentiment(
            news_data, social_data, technical_sentiment
        )
        
        # Competitive analysis
        competitive_analysis = self.competitive_analyzer.analyze_competitive_landscape(competitor_data)
        
        # Risk assessment
        market_conditions = {
            'volatility': technical_patterns.get('pattern_strength', 0.5),
            'regulatory_stability': 0.8  # Educational placeholder
        }
        
        risk_assessment = self.risk_intelligence.assess_portfolio_risk(portfolio_data, market_conditions)
        
        # Generate educational signals
        signals = self._generate_educational_signals(
            technical_patterns, sentiment_analysis, phase_analysis
        )
        
        # Compile key insights
        key_insights = [
            f"Current market phase: {phase_analysis['current_phase'].value}",
            f"Market sentiment: {sentiment_analysis['sentiment_level'].value}",
            f"Overall risk level: {risk_assessment['risk_level']}",
            f"Technical pattern strength: {technical_patterns['pattern_strength']:.2f}"
        ]
        
        if 'market_positions' in competitive_analysis:
            leaders = [k for k, v in competitive_analysis['market_positions'].items() 
                      if v['market_position'] == 'Market Leader']
            if leaders:
                key_insights.append(f"Market leaders identified: {', '.join(leaders)}")
        
        return MarketIntelligenceReport(
            report_id=f"EDU_BI_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(),
            market_phase=phase_analysis['current_phase'],
            sentiment=sentiment_analysis['sentiment_level'],
            volatility_index=technical_patterns.get('pattern_strength', 0.5),
            signals=signals,
            risk_assessment=risk_assessment['risk_level'],
            key_insights=key_insights,
            educational_notes=[
                "This is an educational BI framework for learning market analysis",
                "All analysis is based on simulated educational data",
                "This system demonstrates BI concepts and analytical techniques"
            ]
        )
    
    def _generate_educational_signals(self, 
                                    technical_patterns: Dict[str, Any],
                                    sentiment_analysis: Dict[str, Any],
                                    phase_analysis: Dict[str, Any]) -> List[EducationalSignal]:
        """Generate educational trading signals based on analysis"""
        
        signals = []
        
        # Technical signals
        if technical_patterns.get('trend_direction') == 'up' and technical_patterns.get('pattern_strength', 0) > 0.6:
            signals.append(EducationalSignal(
                symbol="EDU_ASSET",
                signal_type="buy",
                confidence=0.7,
                price_target=technical_patterns.get('pattern_strength', 0) + 0.1,
                timeframe="medium_term",
                reasoning="Strong uptrend pattern detected",
                technical_score=0.7
            ))
        
        # Sentiment signals
        sentiment_level = sentiment_analysis.get('sentiment_level')
        if sentiment_level in [SentimentLevel.BULLISH, SentimentLevel.VERY_BULLISH]:
            if sentiment_analysis.get('confidence', 0) > 0.6:
                signals.append(EducationalSignal(
                    symbol="EDU_ASSET",
                    signal_type="buy",
                    confidence=sentiment_analysis['confidence'] * 0.8,
                    reasoning="Positive market sentiment detected",
                    sentiment_score=sentiment_analysis['confidence']
                ))
        
        # Phase-based signals
        phase = phase_analysis.get('current_phase')
        if phase == MarketPhase.TRENDING_UP and phase_analysis.get('phase_confidence', 0) > 0.7:
            signals.append(EducationalSignal(
                symbol="EDU_ASSET",
                signal_type="buy",
                confidence=phase_analysis['phase_confidence'] * 0.6,
                timeframe="long_term",
                reasoning="Market in confirmed uptrend phase",
                momentum_score=0.8
            ))
        
        # Risk-based signals
        if phase_analysis.get('current_phase') == MarketPhase.VOLATILE:
            signals.append(EducationalSignal(
                symbol="EDU_ASSET",
                signal_type="hold",
                confidence=0.5,
                reasoning="High volatility detected - consider reduced exposure",
                technical_score=0.3
            ))
        
        return signals


def create_educational_market_data(symbol: str = "EDU_STOCK", days: int = 100) -> List[EducationalMarketData]:
    """Create educational market data for demonstration"""
    
    np.random.seed(42)  # For reproducible results
    data = []
    
    base_price = 100.0
    current_price = base_price
    
    for i in range(days):
        # Generate realistic price movements
        daily_return = np.random.normal(0.001, 0.02)  # Small positive drift with volatility
        current_price *= (1 + daily_return)
        
        # Generate OHLC data
        intraday_volatility = current_price * 0.01
        high = current_price + np.random.uniform(0, intraday_volatility)
        low = current_price - np.random.uniform(0, intraday_volatility)
        
        # Ensure logical relationships
        high = max(high, current_price)
        low = min(low, current_price)
        open_price = np.random.uniform(low, high)
        
        # Volume (higher on larger moves)
        volume_multiplier = abs(daily_return) * 50 + 1
        volume = int(np.random.uniform(50000, 150000) * volume_multiplier)
        
        data.append(EducationalMarketData(
            symbol=symbol,
            timestamp=datetime.now() - timedelta(days=days-i),
            price=current_price,
            volume=volume,
            high=high,
            low=low,
            open=open_price,
            close=current_price,
            sector="Educational"
        ))
    
    return data


def create_educational_competitor_data() -> Dict[str, Dict[str, float]]:
    """Create educational competitor data for analysis"""
    
    return {
        "EduCorp_A": {
            "market_share": 0.25,
            "growth_rate": 0.15,
            "profit_margin": 0.18,
            "innovation_score": 0.80,
            "customer_satisfaction": 0.85,
            "operational_efficiency": 0.75,
            "brand_strength": 0.90
        },
        "EduCorp_B": {
            "market_share": 0.20,
            "growth_rate": 0.12,
            "profit_margin": 0.15,
            "innovation_score": 0.65,
            "customer_satisfaction": 0.78,
            "operational_efficiency": 0.82,
            "brand_strength": 0.70
        },
        "EduCorp_C": {
            "market_share": 0.15,
            "growth_rate": 0.20,
            "profit_margin": 0.12,
            "innovation_score": 0.90,
            "customer_satisfaction": 0.72,
            "operational_efficiency": 0.60,
            "brand_strength": 0.65
        },
        "EduCorp_D": {
            "market_share": 0.10,
            "growth_rate": 0.08,
            "profit_margin": 0.20,
            "innovation_score": 0.55,
            "customer_satisfaction": 0.88,
            "operational_efficiency": 0.85,
            "brand_strength": 0.60
        }
    }


def demonstrate_business_intelligence():
    """Demonstrate educational BI capabilities"""
    
    print("🎓 BUSINESS INTELLIGENCE SYSTEM DEMONSTRATION")
    print("=" * 60)
    print("⚠️  EDUCATIONAL PURPOSES ONLY - NO REAL MONEY")
    print()
    
    # Initialize BI engine
    bi_engine = BusinessIntelligenceEngine()
    
    # Create educational datasets
    market_data = create_educational_market_data()
    competitor_data = create_educational_competitor_data()
    
    # Educational news and social data
    news_data = [
        "Strong quarterly results show continued growth momentum",
        "Market analysts maintain positive outlook on sector",
        "Innovation pipeline remains robust for long-term growth",
        "Customer satisfaction scores reach new highs"
    ]
    
    social_data = [
        "Great earnings call - very impressed with management",
        "Innovation continues to differentiate this company",
        "Strong brand recognition in the market",
        "Operational improvements driving efficiency gains"
    ]
    
    # Educational portfolio data
    portfolio_data = {
        'average_daily_volume': 2500000,
        'top_5_holdings_pct': 35,
        'data_quality_score': 0.85
    }
    
    # Generate comprehensive intelligence report
    report = bi_engine.generate_intelligence_report(
        market_data, news_data, social_data, competitor_data, portfolio_data
    )
    
    # Display report
    print(f"📊 MARKET INTELLIGENCE REPORT")
    print(f"Report ID: {report.report_id}")
    print(f"Timestamp: {report.timestamp}")
    print()
    
    print(f"🎯 MARKET ANALYSIS")
    print(f"Market Phase: {report.market_phase.value}")
    print(f"Market Sentiment: {report.sentiment.value}")
    print(f"Volatility Index: {report.volatility_index:.2f}")
    print(f"Risk Assessment: {report.risk_assessment}")
    print()
    
    print(f"📈 SIGNALS GENERATED ({len(report.signals)})")
    for i, signal in enumerate(report.signals, 1):
        print(f"Signal {i}: {signal.signal_type.upper()}")
        print(f"  Confidence: {signal.confidence:.1%}")
        print(f"  Reasoning: {signal.reasoning}")
        print(f"  Timeframe: {signal.timeframe}")
        print()
    
    print(f"💡 KEY INSIGHTS")
    for insight in report.key_insights:
        print(f"  • {insight}")
    print()
    
    print(f"🎓 EDUCATIONAL NOTES")
    for note in report.educational_notes:
        print(f"  • {note}")
    print()
    
    print("=" * 60)
    print("✅ BUSINESS INTELLIGENCE DEMONSTRATION COMPLETE")
    print("🔍 This framework demonstrates:")
    print("   • Technical Analysis (RSI, MACD, Bollinger Bands)")
    print("   • Sentiment Analysis (News & Social Media)")
    print("   • Market Phase Detection")
    print("   • Competitive Analysis & Clustering")
    print("   • Risk Intelligence & Assessment")
    print("   • Signal Generation & Pattern Recognition")
    print("=" * 60)


if __name__ == "__main__":
    demonstrate_business_intelligence()