#!/usr/bin/env python3
"""
🧠 INTELLIGENT BETTING STRATEGY ENGINE
=====================================
Advanced betting strategy system that analyzes prematch data and uses
statistical models to identify high-ROI betting opportunities across
multiple sports with sophisticated risk management.

Key Features:
- 📊 Multi-factor statistical analysis
- 🎯 Value betting identification
- 💰 Kelly Criterion optimization
- 🛡️ Advanced risk management
- 📈 Portfolio optimization
- 🔄 Dynamic bankroll management
- 🎲 Market inefficiency detection
"""

import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import math

# Import our modules
try:
    from prematch_analyzer import PrematchAnalyzer, ROIAnalysis, MatchInfo
    from multi_sport_prematch_scraper import MultiSportPrematchScraper, PrematchData
    MODULES_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: Prematch modules not available. Using standalone mode.")
    MODULES_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BetType(Enum):
    """Types of betting strategies"""
    VALUE_BET = "value_bet"
    ARBITRAGE = "arbitrage"
    SURE_BET = "sure_bet"
    ASIAN_HANDICAP = "asian_handicap"
    OVER_UNDER = "over_under"
    BOTH_TEAMS_SCORE = "btts"
    CORRECT_SCORE = "correct_score"
    LIVE_BET = "live_bet"

class RiskLevel(Enum):
    """Risk levels for betting strategies"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    HIGH_RISK = "high_risk"

@dataclass
class BettingOpportunity:
    """Comprehensive betting opportunity"""
    opportunity_id: str
    match_id: str
    sport: str
    league: str
    home_team: str
    away_team: str
    match_time: datetime
    
    # Betting Details
    bet_type: BetType
    market: str
    selection: str
    bookmaker: str
    odds: float
    
    # Analysis
    true_probability: float
    implied_probability: float
    edge: float  # Percentage edge
    expected_value: float
    
    # Risk Assessment
    risk_level: RiskLevel
    confidence_score: float
    volatility: float
    
    # Bankroll Management
    recommended_stake: float  # Percentage of bankroll
    kelly_fraction: float
    max_loss: float
    expected_profit: float
    
    # Supporting Data
    reasoning: str
    alternative_bets: List[Dict]
    market_analysis: Dict[str, Any]
    
    # Metadata
    created_at: datetime
    expires_at: datetime
    data_sources: List[str]

@dataclass
class BettingPortfolio:
    """Portfolio of betting opportunities"""
    portfolio_id: str
    opportunities: List[BettingOpportunity]
    total_stake: float
    expected_return: float
    risk_score: float
    diversification_score: float
    sharpe_ratio: float
    max_drawdown: float
    created_at: datetime

class BettingStrategyEngine:
    """Advanced betting strategy engine"""
    
    def __init__(self, bankroll: float = 10000, risk_tolerance: str = "moderate"):
        """Initialize the betting strategy engine"""
        logger.info("🧠 Initializing Betting Strategy Engine...")
        
        self.bankroll = bankroll
        self.risk_tolerance = risk_tolerance
        
        # Strategy parameters
        self.strategy_params = {
            'conservative': {
                'min_edge': 0.05,  # 5% minimum edge
                'max_stake': 0.02,  # 2% max stake
                'min_odds': 1.5,
                'max_odds': 3.0,
                'min_confidence': 0.8,
                'kelly_fraction': 0.25
            },
            'moderate': {
                'min_edge': 0.03,  # 3% minimum edge
                'max_stake': 0.05,  # 5% max stake
                'min_odds': 1.3,
                'max_odds': 5.0,
                'min_confidence': 0.65,
                'kelly_fraction': 0.5
            },
            'aggressive': {
                'min_edge': 0.02,  # 2% minimum edge
                'max_stake': 0.08,  # 8% max stake
                'min_odds': 1.2,
                'max_odds': 10.0,
                'min_confidence': 0.55,
                'kelly_fraction': 0.75
            },
            'high_risk': {
                'min_edge': 0.01,  # 1% minimum edge
                'max_stake': 0.15,  # 15% max stake
                'min_odds': 1.1,
                'max_odds': 50.0,
                'min_confidence': 0.45,
                'kelly_fraction': 1.0
            }
        }
        
        # Market efficiency models
        self.market_models = {
            'football': {
                'main_markets': ['1X2', 'Over/Under', 'BTTS'],
                'efficiency': 0.95,  # 95% efficient
                'best_opportunities': ['Asian Handicap', 'Correct Score'],
                'peak_inefficiency_time': 2  # Hours before match
            },
            'tennis': {
                'main_markets': ['Match Winner', 'Set Betting'],
                'efficiency': 0.92,  # 92% efficient
                'best_opportunities': ['Games Handicap', 'Total Games'],
                'peak_inefficiency_time': 1
            },
            'basketball': {
                'main_markets': ['Moneyline', 'Point Spread', 'Total Points'],
                'efficiency': 0.94,
                'best_opportunities': ['Player Props', 'Quarter Betting'],
                'peak_inefficiency_time': 3
            },
            'ice_hockey': {
                'main_markets': ['Moneyline', 'Puck Line', 'Total Goals'],
                'efficiency': 0.90,
                'best_opportunities': ['Period Betting', 'Player Props'],
                'peak_inefficiency_time': 2
            }
        }
        
        # Initialize components
        if MODULES_AVAILABLE:
            self.prematch_analyzer = PrematchAnalyzer()
            self.scraper = MultiSportPrematchScraper()
        
        # Portfolio tracking
        self.active_bets = []
        self.historical_performance = []
        
        logger.info(f"✅ Strategy Engine initialized - Bankroll: ${bankroll:,.2f}, Risk: {risk_tolerance}")
    
    def analyze_betting_opportunities(self, matches: List[PrematchData]) -> List[BettingOpportunity]:
        """Analyze matches and identify betting opportunities"""
        logger.info(f"🔍 Analyzing {len(matches)} matches for betting opportunities...")
        
        opportunities = []
        
        for match in matches:
            try:
                match_opportunities = self._analyze_single_match(match)
                opportunities.extend(match_opportunities)
            except Exception as e:
                logger.error(f"❌ Error analyzing match {match.match_id}: {e}")
        
        # Filter and rank opportunities
        filtered_opportunities = self._filter_opportunities(opportunities)
        ranked_opportunities = self._rank_opportunities(filtered_opportunities)
        
        logger.info(f"✅ Found {len(ranked_opportunities)} qualifying opportunities")
        return ranked_opportunities
    
    def _analyze_single_match(self, match: PrematchData) -> List[BettingOpportunity]:
        """Analyze a single match for betting opportunities"""
        opportunities = []
        
        # Analyze each betting market
        for bookmaker, odds_data in match.odds.items():
            for market, market_odds in odds_data.items():
                if isinstance(market_odds, dict):
                    market_opportunities = self._analyze_market(
                        match, bookmaker, market, market_odds
                    )
                    opportunities.extend(market_opportunities)
        
        return opportunities
    
    def _analyze_market(self, match: PrematchData, bookmaker: str, 
                       market: str, market_odds: Dict[str, float]) -> List[BettingOpportunity]:
        """Analyze a specific betting market"""
        opportunities = []
        
        # Calculate true probabilities based on statistical analysis
        true_probabilities = self._calculate_true_probabilities(match, market)
        
        for selection, odds in market_odds.items():
            if odds <= 0:
                continue
            
            # Get true probability for this selection
            true_prob = true_probabilities.get(selection, 0)
            if true_prob <= 0:
                continue
            
            # Calculate betting metrics
            implied_prob = 1 / odds
            edge = (true_prob * odds - 1) * 100  # Percentage edge
            
            # Check if this meets our criteria
            params = self.strategy_params[self.risk_tolerance]
            
            if (edge >= params['min_edge'] * 100 and 
                params['min_odds'] <= odds <= params['max_odds']):
                
                # Calculate optimal stake using Kelly Criterion
                kelly_fraction = self._calculate_kelly_stake(true_prob, odds)
                recommended_stake = min(
                    kelly_fraction * params['kelly_fraction'],
                    params['max_stake']
                ) * 100  # Convert to percentage
                
                # Risk assessment
                risk_level = self._assess_risk_level(match, market, odds, edge)
                confidence = self._calculate_confidence(match, market, true_prob)
                
                # Create opportunity
                opportunity = BettingOpportunity(
                    opportunity_id=f"{match.match_id}_{bookmaker}_{market}_{selection}",
                    match_id=match.match_id,
                    sport=match.sport,
                    league=match.league,
                    home_team=match.home_team,
                    away_team=match.away_team,
                    match_time=match.match_time,
                    bet_type=self._classify_bet_type(market),
                    market=market,
                    selection=selection,
                    bookmaker=bookmaker,
                    odds=odds,
                    true_probability=true_prob,
                    implied_probability=implied_prob,
                    edge=edge,
                    expected_value=edge * recommended_stake / 100,
                    risk_level=risk_level,
                    confidence_score=confidence,
                    volatility=self._calculate_volatility(match, market),
                    recommended_stake=recommended_stake,
                    kelly_fraction=kelly_fraction * 100,
                    max_loss=recommended_stake,
                    expected_profit=edge * recommended_stake / 100,
                    reasoning=self._generate_reasoning(match, market, selection, edge, true_prob),
                    alternative_bets=self._find_alternative_bets(match, market, selection),
                    market_analysis=self._analyze_market_efficiency(match.odds, market),
                    created_at=datetime.now(),
                    expires_at=match.match_time - timedelta(minutes=30),
                    data_sources=match.sources or ['scraped_data']
                )
                
                opportunities.append(opportunity)
        
        return opportunities
    
    def _calculate_true_probabilities(self, match: PrematchData, market: str) -> Dict[str, float]:
        """Calculate true probabilities for market outcomes"""
        # This is a simplified version - in production, use sophisticated models
        
        if match.sport == 'football':
            if market == '1X2':
                # Use Poisson model for football
                home_strength = match.home_team_stats.get('goals_scored', 1.5)
                away_strength = match.away_team_stats.get('goals_scored', 1.5)
                home_defense = match.home_team_stats.get('goals_conceded', 1.2)
                away_defense = match.away_team_stats.get('goals_conceded', 1.2)
                
                # Adjust for home advantage
                home_expected = home_strength * away_defense * 1.15
                away_expected = away_strength * home_defense * 0.95
                
                # Poisson probabilities (simplified)
                total_goals = home_expected + away_expected
                home_prob = home_expected / total_goals * 0.6  # Adjust for draws
                away_prob = away_expected / total_goals * 0.6
                draw_prob = 1 - home_prob - away_prob
                
                return {
                    'home': home_prob,
                    'draw': draw_prob,
                    'away': away_prob
                }
            
            elif 'over_under' in market:
                home_goals = match.home_team_stats.get('goals_scored', 1.5)
                away_goals = match.away_team_stats.get('goals_scored', 1.5)
                expected_total = (home_goals + away_goals) * 0.9  # Adjust for defense
                
                threshold = 2.5  # Assuming over/under 2.5
                over_prob = min(0.9, max(0.1, (expected_total - threshold + 1) / 2))
                
                return {
                    'over': over_prob,
                    'under': 1 - over_prob
                }
            
            elif 'both_teams_score' in market:
                home_attack = match.home_team_stats.get('goals_scored', 1.5)
                away_attack = match.away_team_stats.get('goals_scored', 1.5)
                
                # Probability both teams score
                btts_prob = min(0.85, (home_attack + away_attack) / 4)
                
                return {
                    'yes': btts_prob,
                    'no': 1 - btts_prob
                }
        
        elif match.sport == 'tennis':
            if market == 'match_winner':
                # Use ranking and form for tennis
                player1_rank = match.home_team_stats.get('ranking', 50)
                player2_rank = match.away_team_stats.get('ranking', 50)
                
                # Lower ranking number = better player
                rank_diff = player2_rank - player1_rank
                player1_prob = 0.5 + (rank_diff / 200)  # Simplified model
                player1_prob = max(0.1, min(0.9, player1_prob))
                
                return {
                    'player1': player1_prob,
                    'player2': 1 - player1_prob
                }
        
        elif match.sport in ['basketball', 'ice_hockey']:
            if market == 'moneyline':
                # Use team strength metrics
                home_strength = match.home_team_stats.get('points_per_game', 100) if match.sport == 'basketball' else match.home_team_stats.get('goals_per_game', 3)
                away_strength = match.away_team_stats.get('points_per_game', 100) if match.sport == 'basketball' else match.away_team_stats.get('goals_per_game', 3)
                
                # Home advantage
                home_strength *= 1.1
                
                total_strength = home_strength + away_strength
                home_prob = home_strength / total_strength
                
                return {
                    'home': home_prob,
                    'away': 1 - home_prob
                }
        
        # Default fallback
        return {}
    
    def _calculate_kelly_stake(self, true_prob: float, odds: float) -> float:
        """Calculate optimal stake using Kelly Criterion"""
        if odds <= 1 or true_prob <= 0:
            return 0
        
        # Kelly formula: f = (bp - q) / b
        # where b = odds - 1, p = true probability, q = 1 - p
        b = odds - 1
        p = true_prob
        q = 1 - p
        
        kelly_fraction = (b * p - q) / b
        
        # Ensure non-negative and reasonable bounds
        return max(0, min(kelly_fraction, 0.25))  # Cap at 25% for safety
    
    def _assess_risk_level(self, match: PrematchData, market: str, odds: float, edge: float) -> RiskLevel:
        """Assess risk level for a betting opportunity"""
        risk_factors = []
        
        # Odds-based risk
        if odds < 1.5:
            risk_factors.append(0.2)  # Low risk
        elif odds < 3.0:
            risk_factors.append(0.4)  # Medium risk
        elif odds < 6.0:
            risk_factors.append(0.7)  # High risk
        else:
            risk_factors.append(0.9)  # Very high risk
        
        # Market liquidity risk
        main_markets = self.market_models[match.sport]['main_markets']
        if market in main_markets:
            risk_factors.append(0.3)  # Lower risk for main markets
        else:
            risk_factors.append(0.6)  # Higher risk for exotic markets
        
        # Data quality risk
        data_quality_risk = 1 - match.data_quality
        risk_factors.append(data_quality_risk)
        
        # Time to match risk
        time_to_match = (match.match_time - datetime.now()).total_seconds() / 3600
        if time_to_match < 2:
            risk_factors.append(0.8)  # High risk close to match
        elif time_to_match < 24:
            risk_factors.append(0.4)  # Medium risk
        else:
            risk_factors.append(0.2)  # Low risk with time
        
        # Calculate overall risk
        avg_risk = np.mean(risk_factors)
        
        if avg_risk < 0.3:
            return RiskLevel.CONSERVATIVE
        elif avg_risk < 0.5:
            return RiskLevel.MODERATE
        elif avg_risk < 0.7:
            return RiskLevel.AGGRESSIVE
        else:
            return RiskLevel.HIGH_RISK
    
    def _calculate_confidence(self, match: PrematchData, market: str, true_prob: float) -> float:
        """Calculate confidence score for the prediction"""
        confidence_factors = []
        
        # Data quality
        confidence_factors.append(match.data_quality)
        
        # Sample size (H2H matches)
        h2h_count = len(match.head_to_head)
        sample_confidence = min(1.0, h2h_count / 5)  # 5 matches = full confidence
        confidence_factors.append(sample_confidence)
        
        # Market efficiency
        sport_efficiency = self.market_models[match.sport]['efficiency']
        market_confidence = 1 - sport_efficiency  # Less efficient = more confident in edge
        confidence_factors.append(market_confidence)
        
        # Probability extremes (more confident in extreme probabilities)
        prob_confidence = abs(true_prob - 0.5) * 2  # 0.5 = no confidence, 0 or 1 = full confidence
        confidence_factors.append(prob_confidence)
        
        return np.mean(confidence_factors)
    
    def _calculate_volatility(self, match: PrematchData, market: str) -> float:
        """Calculate volatility/uncertainty for the betting opportunity"""
        volatility_factors = []
        
        # Sport-specific volatility
        sport_volatilities = {
            'football': 0.3,  # Relatively low volatility
            'tennis': 0.5,    # Medium volatility
            'basketball': 0.4, # Medium-low volatility
            'ice_hockey': 0.6  # Higher volatility
        }
        volatility_factors.append(sport_volatilities.get(match.sport, 0.5))
        
        # Market-specific volatility
        if market in ['1X2', 'moneyline', 'match_winner']:
            volatility_factors.append(0.3)  # Main markets less volatile
        else:
            volatility_factors.append(0.6)  # Exotic markets more volatile
        
        # Injury/suspension impact
        total_absences = len(match.injuries.get('home_team', [])) + len(match.injuries.get('away_team', []))
        absence_volatility = min(0.8, total_absences * 0.2)
        volatility_factors.append(absence_volatility)
        
        return np.mean(volatility_factors)
    
    def _classify_bet_type(self, market: str) -> BetType:
        """Classify the type of bet based on market"""
        market_lower = market.lower()
        
        if 'asian' in market_lower or 'handicap' in market_lower:
            return BetType.ASIAN_HANDICAP
        elif 'over' in market_lower or 'under' in market_lower or 'total' in market_lower:
            return BetType.OVER_UNDER
        elif 'both' in market_lower and 'score' in market_lower:
            return BetType.BOTH_TEAMS_SCORE
        elif 'correct' in market_lower and 'score' in market_lower:
            return BetType.CORRECT_SCORE
        else:
            return BetType.VALUE_BET
    
    def _generate_reasoning(self, match: PrematchData, market: str, selection: str, 
                          edge: float, true_prob: float) -> str:
        """Generate human-readable reasoning for the bet"""
        reasoning_parts = []
        
        # Edge explanation
        reasoning_parts.append(f"🎯 {edge:.1f}% edge identified in {market} market")
        
        # Statistical basis
        if match.sport == 'football':
            home_goals = match.home_team_stats.get('goals_scored', 0)
            away_goals = match.away_team_stats.get('goals_scored', 0)
            reasoning_parts.append(f"📊 Based on team averages: {match.home_team} ({home_goals:.1f} goals/game) vs {match.away_team} ({away_goals:.1f} goals/game)")
        
        # Form analysis
        home_form = match.recent_form.get('home_team', [])
        away_form = match.recent_form.get('away_team', [])
        if home_form and away_form:
            home_form_str = ''.join(home_form[-5:])
            away_form_str = ''.join(away_form[-5:])
            reasoning_parts.append(f"📈 Recent form: {match.home_team} ({home_form_str}) vs {match.away_team} ({away_form_str})")
        
        # H2H record
        if match.head_to_head:
            recent_h2h = match.head_to_head[-3:]  # Last 3 meetings
            home_wins = sum(1 for h2h in recent_h2h if h2h['result'] == 'H')
            reasoning_parts.append(f"🔄 H2H: {match.home_team} won {home_wins}/{len(recent_h2h)} recent meetings")
        
        # Market inefficiency
        reasoning_parts.append(f"💡 Market appears to undervalue true probability ({true_prob:.1%})")
        
        return " | ".join(reasoning_parts)
    
    def _find_alternative_bets(self, match: PrematchData, market: str, selection: str) -> List[Dict]:
        """Find alternative betting opportunities in the same match"""
        alternatives = []
        
        # Look for correlated bets in other markets
        for bookmaker, odds_data in match.odds.items():
            for alt_market, alt_odds in odds_data.items():
                if alt_market != market and isinstance(alt_odds, dict):
                    for alt_selection, alt_odd in alt_odds.items():
                        if alt_odd > 0:
                            alternatives.append({
                                'market': alt_market,
                                'selection': alt_selection,
                                'odds': alt_odd,
                                'bookmaker': bookmaker
                            })
        
        # Return top 3 alternatives by odds
        alternatives.sort(key=lambda x: x['odds'], reverse=True)
        return alternatives[:3]
    
    def _analyze_market_efficiency(self, all_odds: Dict, market: str) -> Dict[str, Any]:
        """Analyze market efficiency for arbitrage opportunities"""
        analysis = {
            'bookmaker_count': len(all_odds),
            'odds_variance': 0,
            'arbitrage_opportunity': False,
            'best_odds': {},
            'market_margin': 0
        }
        
        # Find best odds for each outcome
        market_odds_by_outcome = {}
        
        for bookmaker, odds_data in all_odds.items():
            if market in odds_data and isinstance(odds_data[market], dict):
                for outcome, odds in odds_data[market].items():
                    if outcome not in market_odds_by_outcome:
                        market_odds_by_outcome[outcome] = []
                    market_odds_by_outcome[outcome].append(odds)
        
        # Calculate best odds and variance
        for outcome, odds_list in market_odds_by_outcome.items():
            if odds_list:
                best_odds = max(odds_list)
                analysis['best_odds'][outcome] = best_odds
                analysis['odds_variance'] += np.var(odds_list)
        
        # Check for arbitrage
        if analysis['best_odds']:
            total_implied_prob = sum(1/odds for odds in analysis['best_odds'].values())
            if total_implied_prob < 1.0:
                analysis['arbitrage_opportunity'] = True
                analysis['arbitrage_profit'] = (1 - total_implied_prob) * 100
        
        return analysis
    
    def _filter_opportunities(self, opportunities: List[BettingOpportunity]) -> List[BettingOpportunity]:
        """Filter opportunities based on strategy parameters"""
        params = self.strategy_params[self.risk_tolerance]
        
        filtered = []
        for opp in opportunities:
            # Check minimum edge
            if opp.edge < params['min_edge'] * 100:
                continue
            
            # Check odds range
            if not (params['min_odds'] <= opp.odds <= params['max_odds']):
                continue
            
            # Check confidence
            if opp.confidence_score < params['min_confidence']:
                continue
            
            # Check time to expiry
            time_to_expiry = (opp.expires_at - datetime.now()).total_seconds() / 3600
            if time_to_expiry < 0.5:  # Less than 30 minutes
                continue
            
            filtered.append(opp)
        
        return filtered
    
    def _rank_opportunities(self, opportunities: List[BettingOpportunity]) -> List[BettingOpportunity]:
        """Rank opportunities by attractiveness"""
        
        def calculate_score(opp: BettingOpportunity) -> float:
            # Multi-factor scoring
            edge_score = opp.edge / 10  # Edge as percentage
            confidence_score = opp.confidence_score * 5
            risk_penalty = {'conservative': 0, 'moderate': -0.5, 'aggressive': -1, 'high_risk': -2}[opp.risk_level.value]
            
            # Time bonus (more time = better)
            time_to_match = (opp.match_time - datetime.now()).total_seconds() / 3600
            time_bonus = min(2, time_to_match / 12)  # Max 2 points for 12+ hours
            
            return edge_score + confidence_score + risk_penalty + time_bonus
        
        # Sort by score descending
        opportunities.sort(key=calculate_score, reverse=True)
        return opportunities
    
    def create_betting_portfolio(self, opportunities: List[BettingOpportunity], 
                               max_positions: int = 10) -> BettingPortfolio:
        """Create an optimized betting portfolio"""
        logger.info(f"🎯 Creating betting portfolio from {len(opportunities)} opportunities...")
        
        if not opportunities:
            return BettingPortfolio(
                portfolio_id=f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                opportunities=[],
                total_stake=0,
                expected_return=0,
                risk_score=0,
                diversification_score=0,
                sharpe_ratio=0,
                max_drawdown=0,
                created_at=datetime.now()
            )
        
        # Portfolio optimization
        selected_opportunities = self._optimize_portfolio(opportunities, max_positions)
        
        # Calculate portfolio metrics
        total_stake = sum(opp.recommended_stake for opp in selected_opportunities)
        expected_return = sum(opp.expected_profit for opp in selected_opportunities)
        
        # Risk metrics
        risk_score = self._calculate_portfolio_risk(selected_opportunities)
        diversification_score = self._calculate_diversification(selected_opportunities)
        sharpe_ratio = self._calculate_sharpe_ratio(selected_opportunities)
        max_drawdown = self._calculate_max_drawdown(selected_opportunities)
        
        portfolio = BettingPortfolio(
            portfolio_id=f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            opportunities=selected_opportunities,
            total_stake=total_stake,
            expected_return=expected_return,
            risk_score=risk_score,
            diversification_score=diversification_score,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            created_at=datetime.now()
        )
        
        logger.info(f"✅ Portfolio created: {len(selected_opportunities)} bets, {total_stake:.1f}% total stake")
        return portfolio
    
    def _optimize_portfolio(self, opportunities: List[BettingOpportunity], 
                          max_positions: int) -> List[BettingOpportunity]:
        """Optimize portfolio selection using various criteria"""
        
        # Start with top opportunities
        candidates = opportunities[:max_positions * 2]  # Consider 2x positions for optimization
        
        selected = []
        remaining_bankroll = 100  # 100% of bankroll available
        
        # Diversification constraints
        sport_limits = {'football': 0.4, 'tennis': 0.3, 'basketball': 0.2, 'ice_hockey': 0.1}
        sport_allocations = {sport: 0 for sport in sport_limits}
        
        for opp in candidates:
            # Check bankroll constraint
            if opp.recommended_stake > remaining_bankroll:
                continue
            
            # Check diversification constraint
            sport_limit = sport_limits.get(opp.sport, 0.1) * 100  # Convert to percentage
            if sport_allocations[opp.sport] + opp.recommended_stake > sport_limit:
                continue
            
            # Check correlation (avoid too many bets on same match)
            same_match_count = sum(1 for sel_opp in selected if sel_opp.match_id == opp.match_id)
            if same_match_count >= 2:  # Max 2 bets per match
                continue
            
            # Add to portfolio
            selected.append(opp)
            remaining_bankroll -= opp.recommended_stake
            sport_allocations[opp.sport] += opp.recommended_stake
            
            if len(selected) >= max_positions:
                break
        
        return selected
    
    def _calculate_portfolio_risk(self, opportunities: List[BettingOpportunity]) -> float:
        """Calculate overall portfolio risk score"""
        if not opportunities:
            return 0
        
        # Weighted average risk by stake size
        total_stake = sum(opp.recommended_stake for opp in opportunities)
        if total_stake == 0:
            return 0
        
        risk_values = {'conservative': 0.2, 'moderate': 0.4, 'aggressive': 0.7, 'high_risk': 0.9}
        weighted_risk = sum(
            risk_values[opp.risk_level.value] * opp.recommended_stake 
            for opp in opportunities
        ) / total_stake
        
        return weighted_risk
    
    def _calculate_diversification(self, opportunities: List[BettingOpportunity]) -> float:
        """Calculate diversification score (higher is better)"""
        if not opportunities:
            return 0
        
        # Count unique sports, leagues, bet types
        unique_sports = len(set(opp.sport for opp in opportunities))
        unique_leagues = len(set(opp.league for opp in opportunities))
        unique_bet_types = len(set(opp.bet_type.value for opp in opportunities))
        unique_matches = len(set(opp.match_id for opp in opportunities))
        
        # Normalize by portfolio size
        portfolio_size = len(opportunities)
        diversification_score = (
            unique_sports / min(4, portfolio_size) * 0.3 +
            unique_leagues / min(6, portfolio_size) * 0.2 +
            unique_bet_types / min(5, portfolio_size) * 0.2 +
            unique_matches / portfolio_size * 0.3
        )
        
        return min(1.0, diversification_score)
    
    def _calculate_sharpe_ratio(self, opportunities: List[BettingOpportunity]) -> float:
        """Calculate Sharpe ratio for the portfolio"""
        if not opportunities:
            return 0
        
        # Expected returns and volatilities
        returns = [opp.expected_value for opp in opportunities]
        volatilities = [opp.volatility for opp in opportunities]
        
        if not returns or not volatilities:
            return 0
        
        portfolio_return = np.mean(returns)
        portfolio_volatility = np.mean(volatilities)
        
        # Risk-free rate (assume 2% annually, convert to per-bet basis)
        risk_free_rate = 0.02 / 365  # Daily risk-free rate
        
        if portfolio_volatility == 0:
            return 0
        
        sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility
        return sharpe_ratio
    
    def _calculate_max_drawdown(self, opportunities: List[BettingOpportunity]) -> float:
        """Calculate maximum potential drawdown"""
        if not opportunities:
            return 0
        
        # Worst-case scenario: all bets lose
        total_potential_loss = sum(opp.recommended_stake for opp in opportunities)
        return min(100, total_potential_loss)  # Cap at 100%
    
    def generate_betting_report(self, portfolio: BettingPortfolio) -> str:
        """Generate comprehensive betting report"""
        
        if not portfolio.opportunities:
            return "❌ No betting opportunities found matching your criteria."
        
        report_lines = []
        report_lines.append("🎯 INTELLIGENT BETTING STRATEGY REPORT")
        report_lines.append("=" * 60)
        report_lines.append(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"🏦 Bankroll: ${self.bankroll:,.2f}")
        report_lines.append(f"🎲 Risk Tolerance: {self.risk_tolerance.upper()}")
        report_lines.append("")
        
        # Portfolio Summary
        report_lines.append("📊 PORTFOLIO SUMMARY")
        report_lines.append("-" * 30)
        report_lines.append(f"💰 Total Stake: {portfolio.total_stake:.1f}% of bankroll (${portfolio.total_stake * self.bankroll / 100:,.2f})")
        report_lines.append(f"📈 Expected Return: {portfolio.expected_return:.2f}%")
        report_lines.append(f"🛡️ Risk Score: {portfolio.risk_score:.2f}/1.0")
        report_lines.append(f"🎯 Diversification: {portfolio.diversification_score:.2f}/1.0")
        report_lines.append(f"📊 Sharpe Ratio: {portfolio.sharpe_ratio:.2f}")
        report_lines.append(f"⚠️ Max Drawdown: {portfolio.max_drawdown:.1f}%")
        report_lines.append("")
        
        # Top Opportunities
        report_lines.append("🏆 TOP BETTING OPPORTUNITIES")
        report_lines.append("-" * 40)
        
        for i, opp in enumerate(portfolio.opportunities[:5], 1):
            report_lines.append(f"\n{i}. {opp.home_team} vs {opp.away_team}")
            report_lines.append(f"   🏆 {opp.league} | ⚽ {opp.sport.title()}")
            report_lines.append(f"   📅 {opp.match_time.strftime('%Y-%m-%d %H:%M')}")
            report_lines.append(f"   🎯 Bet: {opp.market} - {opp.selection}")
            report_lines.append(f"   💰 Odds: {opp.odds:.2f} @ {opp.bookmaker}")
            report_lines.append(f"   📊 Edge: {opp.edge:.1f}% | Confidence: {opp.confidence_score:.1%}")
            report_lines.append(f"   💵 Stake: {opp.recommended_stake:.1f}% (${opp.recommended_stake * self.bankroll / 100:,.2f})")
            report_lines.append(f"   🛡️ Risk: {opp.risk_level.value.upper()}")
            report_lines.append(f"   💡 {opp.reasoning}")
        
        # Risk Analysis
        report_lines.append(f"\n🛡️ RISK ANALYSIS")
        report_lines.append("-" * 20)
        
        risk_distribution = {}
        for opp in portfolio.opportunities:
            risk_level = opp.risk_level.value
            if risk_level not in risk_distribution:
                risk_distribution[risk_level] = 0
            risk_distribution[risk_level] += 1
        
        for risk_level, count in risk_distribution.items():
            percentage = count / len(portfolio.opportunities) * 100
            report_lines.append(f"   {risk_level.upper()}: {count} bets ({percentage:.1f}%)")
        
        # Sport Distribution
        report_lines.append(f"\n🏆 SPORT DISTRIBUTION")
        report_lines.append("-" * 25)
        
        sport_distribution = {}
        sport_stakes = {}
        
        for opp in portfolio.opportunities:
            sport = opp.sport
            if sport not in sport_distribution:
                sport_distribution[sport] = 0
                sport_stakes[sport] = 0
            sport_distribution[sport] += 1
            sport_stakes[sport] += opp.recommended_stake
        
        for sport, count in sport_distribution.items():
            stake_pct = sport_stakes[sport]
            report_lines.append(f"   {sport.title()}: {count} bets, {stake_pct:.1f}% stake")
        
        # Recommendations
        report_lines.append(f"\n💡 RECOMMENDATIONS")
        report_lines.append("-" * 25)
        
        if portfolio.total_stake > 20:
            report_lines.append("   ⚠️ High total stake - consider reducing position sizes")
        
        if portfolio.diversification_score < 0.5:
            report_lines.append("   📊 Low diversification - consider spreading across more sports/markets")
        
        if portfolio.risk_score > 0.7:
            report_lines.append("   🛡️ High risk portfolio - monitor closely and consider reducing stakes")
        
        if portfolio.sharpe_ratio > 1.0:
            report_lines.append("   📈 Excellent risk-adjusted returns expected")
        elif portfolio.sharpe_ratio < 0.5:
            report_lines.append("   📉 Consider focusing on higher-edge opportunities")
        
        report_lines.append(f"\n⚠️ DISCLAIMER: Betting involves risk. Never bet more than you can afford to lose.")
        report_lines.append("🎯 Always verify odds and conditions before placing bets.")
        
        return "\n".join(report_lines)

def main():
    """Main function for testing the betting strategy engine"""
    print("🧠 INTELLIGENT BETTING STRATEGY ENGINE")
    print("=" * 50)
    
    # Initialize engine
    engine = BettingStrategyEngine(bankroll=10000, risk_tolerance="moderate")
    
    # Simulate some prematch data
    sample_matches = []
    
    # Create sample football match
    football_match = PrematchData(
        match_id="football_001",
        sport="football",
        league="Premier League",
        home_team="Manchester City",
        away_team="Liverpool",
        match_time=datetime.now() + timedelta(hours=24),
        venue="Etihad Stadium",
        home_team_stats={
            'goals_scored': 2.3,
            'goals_conceded': 0.8,
            'shots_per_game': 16.2,
            'possession_avg': 65.4
        },
        away_team_stats={
            'goals_scored': 2.1,
            'goals_conceded': 1.1,
            'shots_per_game': 14.8,
            'possession_avg': 58.7
        },
        head_to_head=[
            {'date': datetime.now() - timedelta(days=120), 'result': 'H', 'home_score': 2, 'away_score': 1},
            {'date': datetime.now() - timedelta(days=240), 'result': 'A', 'home_score': 1, 'away_score': 3},
        ],
        recent_form={
            'home_team': ['W', 'W', 'D', 'W', 'W'],
            'away_team': ['W', 'L', 'W', 'W', 'D']
        },
        odds={
            'bet365': {
                '1X2': {'home': 1.85, 'draw': 3.60, 'away': 4.20},
                'over_under_2.5': {'over': 1.75, 'under': 2.05},
                'both_teams_score': {'yes': 1.65, 'no': 2.20}
            },
            'pinnacle': {
                '1X2': {'home': 1.90, 'draw': 3.50, 'away': 4.10},
                'over_under_2.5': {'over': 1.80, 'under': 2.00}
            }
        },
        market_analysis={},
        weather={'temperature': 15, 'conditions': 'clear'},
        injuries={'home_team': [], 'away_team': ['Salah']},
        suspensions={'home_team': [], 'away_team': []},
        scraped_at=datetime.now(),
        data_quality=0.85,
        sources=['flashscore', 'bet365']
    )
    
    sample_matches.append(football_match)
    
    print(f"\n🔍 Analyzing {len(sample_matches)} matches...")
    
    # Analyze opportunities
    opportunities = engine.analyze_betting_opportunities(sample_matches)
    
    print(f"✅ Found {len(opportunities)} betting opportunities")
    
    if opportunities:
        # Create portfolio
        portfolio = engine.create_betting_portfolio(opportunities, max_positions=5)
        
        # Generate report
        report = engine.generate_betting_report(portfolio)
        print(f"\n{report}")
    else:
        print("❌ No qualifying opportunities found with current parameters")

if __name__ == "__main__":
    main()
