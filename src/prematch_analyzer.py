#!/usr/bin/env python3
"""
🎯 PREMATCH ANALYZER - Advanced Sports Betting Intelligence
===========================================================
Comprehensive prematch analysis system that gathers detailed information
and uses advanced knowledge to identify the best betting opportunities
with high ROI potential across multiple sports.

Features:
- Multi-sport prematch data collection
- Advanced statistical analysis
- ROI calculation and optimization
- Betting strategy recommendations
- Risk assessment and bankroll management
"""

import logging
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TeamStats:
    """Team/Player statistics for analysis"""
    name: str
    recent_form: List[str]  # W/L/D for last 5-10 games
    home_record: Tuple[int, int, int]  # W-D-L at home
    away_record: Tuple[int, int, int]  # W-D-L away
    goals_scored_avg: float
    goals_conceded_avg: float
    possession_avg: float
    shots_per_game: float
    shots_on_target_pct: float
    pass_accuracy: float
    injury_list: List[str]
    suspension_list: List[str]
    market_value: float
    recent_transfers: List[Dict]
    head_to_head_record: Dict[str, int]

@dataclass
class MatchInfo:
    """Comprehensive match information"""
    match_id: str
    sport: str
    league: str
    home_team: str
    away_team: str
    match_time: datetime
    venue: str
    weather: Optional[Dict] = None
    referee: Optional[str] = None
    tv_coverage: bool = False
    importance: str = "regular"  # regular, cup, playoff, final
    
@dataclass
class BettingOdds:
    """Betting odds and market information"""
    bookmaker: str
    match_winner_home: float
    match_winner_draw: float
    match_winner_away: float
    over_under_2_5: Dict[str, float]
    both_teams_score: Dict[str, float]
    asian_handicap: Dict[str, float]
    total_goals: Dict[str, float]
    first_goal_scorer: Dict[str, float]
    correct_score: Dict[str, float]
    margin: float  # Bookmaker margin
    
@dataclass
class ROIAnalysis:
    """ROI analysis results"""
    match_id: str
    recommended_bet: str
    stake_percentage: float  # % of bankroll
    expected_roi: float
    confidence_level: float
    risk_rating: str  # LOW, MEDIUM, HIGH, VERY_HIGH
    value_rating: float  # 1-10 scale
    reasoning: str
    alternative_bets: List[Dict]

class PrematchAnalyzer:
    """Advanced prematch analysis system"""
    
    def __init__(self):
        """Initialize the prematch analyzer"""
        logger.info("🎯 Initializing Prematch Analyzer...")
        
        # Sports configuration
        self.supported_sports = {
            'football': {
                'leagues': ['Premier League', 'La Liga', 'Bundesliga', 'Serie A', 'Ligue 1', 'Champions League'],
                'key_stats': ['goals', 'possession', 'shots', 'corners', 'cards'],
                'betting_markets': ['1X2', 'Over/Under', 'BTTS', 'Asian Handicap', 'Correct Score']
            },
            'tennis': {
                'tournaments': ['ATP Masters', 'WTA Premier', 'Grand Slams'],
                'key_stats': ['serve_pct', 'break_points', 'aces', 'unforced_errors'],
                'betting_markets': ['Match Winner', 'Set Betting', 'Games Handicap', 'Total Games']
            },
            'basketball': {
                'leagues': ['NBA', 'EuroLeague', 'NCAA'],
                'key_stats': ['points', 'rebounds', 'assists', 'field_goal_pct'],
                'betting_markets': ['Moneyline', 'Point Spread', 'Total Points', 'Player Props']
            },
            'ice_hockey': {
                'leagues': ['NHL', 'KHL', 'SHL'],
                'key_stats': ['goals', 'shots', 'saves', 'power_play_pct'],
                'betting_markets': ['Moneyline', 'Puck Line', 'Total Goals', 'Period Betting']
            }
        }
        
        # ROI calculation parameters
        self.roi_params = {
            'min_confidence': 0.6,  # 60% minimum confidence
            'max_stake_pct': 0.05,  # Max 5% of bankroll per bet
            'min_roi_threshold': 0.15,  # 15% minimum expected ROI
            'kelly_fraction': 0.25,  # Conservative Kelly Criterion
            'risk_tolerance': 'medium'
        }
        
        # Data sources
        self.data_sources = {
            'odds': ['bet365', 'pinnacle', 'betfair', 'unibet'],
            'stats': ['flashscore', 'sofascore', 'transfermarkt', 'whoscored'],
            'weather': ['openweathermap'],
            'news': ['espn', 'bbc_sport', 'sky_sports']
        }
        
        logger.info("✅ Prematch Analyzer initialized")
    
    def analyze_match(self, match_info: MatchInfo) -> ROIAnalysis:
        """Comprehensive match analysis for ROI optimization"""
        logger.info(f"🔍 Analyzing match: {match_info.home_team} vs {match_info.away_team}")
        
        try:
            # 1. Gather comprehensive data
            team_stats = self._gather_team_statistics(match_info)
            odds_data = self._gather_betting_odds(match_info)
            external_factors = self._analyze_external_factors(match_info)
            
            # 2. Statistical analysis
            statistical_edge = self._calculate_statistical_edge(team_stats, match_info)
            
            # 3. Value betting identification
            value_bets = self._identify_value_bets(odds_data, statistical_edge)
            
            # 4. ROI calculation
            roi_analysis = self._calculate_roi(value_bets, match_info, statistical_edge)
            
            # 5. Risk assessment
            risk_assessment = self._assess_risk(match_info, team_stats, external_factors)
            
            # 6. Generate recommendations
            recommendations = self._generate_recommendations(
                roi_analysis, risk_assessment, statistical_edge
            )
            
            logger.info(f"✅ Analysis complete for {match_info.match_id}")
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Error analyzing match {match_info.match_id}: {e}")
            return self._create_no_bet_recommendation(match_info.match_id, str(e))
    
    def _gather_team_statistics(self, match_info: MatchInfo) -> Dict[str, TeamStats]:
        """Gather comprehensive team statistics"""
        logger.info("📊 Gathering team statistics...")
        
        # Simulate comprehensive team data gathering
        # In production, this would connect to real APIs
        
        home_stats = TeamStats(
            name=match_info.home_team,
            recent_form=['W', 'W', 'D', 'W', 'L'],
            home_record=(8, 2, 2),  # 8W-2D-2L at home
            away_record=(5, 3, 4),  # 5W-3D-4L away
            goals_scored_avg=2.1,
            goals_conceded_avg=1.2,
            possession_avg=58.5,
            shots_per_game=14.2,
            shots_on_target_pct=42.3,
            pass_accuracy=85.7,
            injury_list=['Player A (knee)', 'Player B (hamstring)'],
            suspension_list=[],
            market_value=450.5,  # Million euros
            recent_transfers=[],
            head_to_head_record={'wins': 3, 'draws': 1, 'losses': 1}
        )
        
        away_stats = TeamStats(
            name=match_info.away_team,
            recent_form=['L', 'W', 'W', 'D', 'W'],
            home_record=(6, 4, 2),
            away_record=(4, 2, 6),  # Poor away form
            goals_scored_avg=1.8,
            goals_conceded_avg=1.5,
            possession_avg=52.1,
            shots_per_game=12.8,
            shots_on_target_pct=38.9,
            pass_accuracy=82.3,
            injury_list=['Player C (ankle)'],
            suspension_list=['Player D (red card)'],
            market_value=320.2,
            recent_transfers=[{'player': 'Star Player', 'type': 'out', 'impact': 'high'}],
            head_to_head_record={'wins': 1, 'draws': 1, 'losses': 3}
        )
        
        return {'home': home_stats, 'away': away_stats}
    
    def _gather_betting_odds(self, match_info: MatchInfo) -> Dict[str, BettingOdds]:
        """Gather betting odds from multiple bookmakers"""
        logger.info("💰 Gathering betting odds...")
        
        # Simulate odds gathering from multiple bookmakers
        odds_data = {}
        
        for bookmaker in self.data_sources['odds']:
            odds_data[bookmaker] = BettingOdds(
                bookmaker=bookmaker,
                match_winner_home=1.85 + np.random.uniform(-0.1, 0.1),
                match_winner_draw=3.40 + np.random.uniform(-0.2, 0.2),
                match_winner_away=4.20 + np.random.uniform(-0.3, 0.3),
                over_under_2_5={'over': 1.90, 'under': 1.90},
                both_teams_score={'yes': 1.75, 'no': 2.05},
                asian_handicap={'-0.5': 1.95, '+0.5': 1.85},
                total_goals={'over_1.5': 1.25, 'under_1.5': 3.75},
                first_goal_scorer={'home_player': 4.5, 'away_player': 6.0},
                correct_score={'1-0': 8.5, '2-1': 9.0, '0-0': 11.0},
                margin=0.05  # 5% bookmaker margin
            )
        
        return odds_data
    
    def _analyze_external_factors(self, match_info: MatchInfo) -> Dict[str, Any]:
        """Analyze external factors affecting the match"""
        logger.info("🌤️ Analyzing external factors...")
        
        external_factors = {
            'weather': {
                'temperature': 18,  # Celsius
                'humidity': 65,     # %
                'wind_speed': 12,   # km/h
                'precipitation': 0, # mm
                'conditions': 'clear'
            },
            'venue_factors': {
                'pitch_condition': 'good',
                'capacity': 75000,
                'expected_attendance': 68000,
                'home_advantage': 0.15  # 15% boost for home team
            },
            'referee_factors': {
                'name': match_info.referee,
                'cards_per_game': 4.2,
                'penalty_frequency': 0.3,
                'home_bias': 0.02  # Slight home bias
            },
            'media_pressure': {
                'tv_audience': 2.5e6 if match_info.tv_coverage else 0,
                'importance_multiplier': 1.5 if match_info.importance != 'regular' else 1.0
            }
        }
        
        return external_factors
    
    def _calculate_statistical_edge(self, team_stats: Dict[str, TeamStats], match_info: MatchInfo) -> Dict[str, float]:
        """Calculate statistical edge for different betting markets"""
        logger.info("📈 Calculating statistical edge...")
        
        home_stats = team_stats['home']
        away_stats = team_stats['away']
        
        # Goal expectancy model (Poisson-based)
        home_attack = home_stats.goals_scored_avg
        home_defense = home_stats.goals_conceded_avg
        away_attack = away_stats.goals_scored_avg
        away_defense = away_stats.goals_conceded_avg
        
        # Adjust for home advantage
        home_advantage = 0.15
        home_expected_goals = home_attack * away_defense * (1 + home_advantage)
        away_expected_goals = away_attack * home_defense * (1 - home_advantage * 0.5)
        
        # Form analysis
        home_form_score = self._calculate_form_score(home_stats.recent_form)
        away_form_score = self._calculate_form_score(away_stats.recent_form)
        
        # Head-to-head factor
        h2h_factor = (home_stats.head_to_head_record['wins'] - 
                     away_stats.head_to_head_record['wins']) * 0.1
        
        statistical_edge = {
            'home_win_probability': self._calculate_win_probability(
                home_expected_goals, away_expected_goals, home_form_score, h2h_factor
            ),
            'draw_probability': self._calculate_draw_probability(
                home_expected_goals, away_expected_goals
            ),
            'away_win_probability': self._calculate_win_probability(
                away_expected_goals, home_expected_goals, away_form_score, -h2h_factor
            ),
            'over_2_5_probability': self._calculate_over_under_probability(
                home_expected_goals + away_expected_goals, 2.5
            ),
            'btts_probability': self._calculate_btts_probability(
                home_expected_goals, away_expected_goals
            ),
            'expected_total_goals': home_expected_goals + away_expected_goals,
            'confidence_score': self._calculate_confidence_score(team_stats)
        }
        
        return statistical_edge
    
    def _calculate_form_score(self, recent_form: List[str]) -> float:
        """Calculate form score from recent results"""
        form_values = {'W': 3, 'D': 1, 'L': 0}
        total_points = sum(form_values.get(result, 0) for result in recent_form)
        max_points = len(recent_form) * 3
        return total_points / max_points if max_points > 0 else 0.5
    
    def _calculate_win_probability(self, team_goals: float, opponent_goals: float, 
                                 form_score: float, h2h_factor: float) -> float:
        """Calculate win probability using Poisson distribution"""
        # Simplified Poisson-based calculation
        base_prob = team_goals / (team_goals + opponent_goals + 1)  # +1 for draw
        
        # Adjust for form and head-to-head
        adjusted_prob = base_prob * (0.7 + 0.3 * form_score) * (1 + h2h_factor)
        
        return max(0.05, min(0.90, adjusted_prob))  # Clamp between 5% and 90%
    
    def _calculate_draw_probability(self, home_goals: float, away_goals: float) -> float:
        """Calculate draw probability"""
        goal_diff = abs(home_goals - away_goals)
        base_draw_prob = 0.25  # Base 25% draw probability
        
        # Higher draw probability when teams are evenly matched
        if goal_diff < 0.3:
            return min(0.35, base_draw_prob + 0.1)
        else:
            return max(0.15, base_draw_prob - goal_diff * 0.1)
    
    def _calculate_over_under_probability(self, expected_goals: float, threshold: float) -> float:
        """Calculate over/under probability using Poisson distribution"""
        # Simplified calculation - in production use proper Poisson
        if expected_goals > threshold:
            return 0.55 + (expected_goals - threshold) * 0.1
        else:
            return 0.45 - (threshold - expected_goals) * 0.1
    
    def _calculate_btts_probability(self, home_goals: float, away_goals: float) -> float:
        """Calculate both teams to score probability"""
        # Teams with higher goal averages more likely to both score
        combined_attack = (home_goals + away_goals) / 2
        
        if combined_attack > 1.5:
            return min(0.75, 0.4 + combined_attack * 0.15)
        else:
            return max(0.25, combined_attack * 0.2)
    
    def _calculate_confidence_score(self, team_stats: Dict[str, TeamStats]) -> float:
        """Calculate overall confidence in predictions"""
        factors = []
        
        # Sample size (more games = higher confidence)
        home_games = sum(team_stats['home'].home_record)
        away_games = sum(team_stats['away'].away_record)
        sample_factor = min(1.0, (home_games + away_games) / 20)
        factors.append(sample_factor)
        
        # Form consistency
        home_form_consistency = self._calculate_form_consistency(team_stats['home'].recent_form)
        away_form_consistency = self._calculate_form_consistency(team_stats['away'].recent_form)
        consistency_factor = (home_form_consistency + away_form_consistency) / 2
        factors.append(consistency_factor)
        
        # Injury/suspension impact
        home_absences = len(team_stats['home'].injury_list) + len(team_stats['home'].suspension_list)
        away_absences = len(team_stats['away'].injury_list) + len(team_stats['away'].suspension_list)
        absence_factor = max(0.3, 1.0 - (home_absences + away_absences) * 0.1)
        factors.append(absence_factor)
        
        return np.mean(factors)
    
    def _calculate_form_consistency(self, recent_form: List[str]) -> float:
        """Calculate how consistent recent form is"""
        if len(recent_form) < 3:
            return 0.5
        
        # Count streaks and patterns
        streaks = 0
        current_streak = 1
        
        for i in range(1, len(recent_form)):
            if recent_form[i] == recent_form[i-1]:
                current_streak += 1
            else:
                if current_streak >= 2:
                    streaks += 1
                current_streak = 1
        
        if current_streak >= 2:
            streaks += 1
        
        return min(1.0, streaks / (len(recent_form) - 1))
    
    def _identify_value_bets(self, odds_data: Dict[str, BettingOdds], 
                           statistical_edge: Dict[str, float]) -> List[Dict]:
        """Identify value betting opportunities"""
        logger.info("💎 Identifying value bets...")
        
        value_bets = []
        
        for bookmaker, odds in odds_data.items():
            # Check 1X2 market
            markets = [
                ('home_win', odds.match_winner_home, statistical_edge['home_win_probability']),
                ('draw', odds.match_winner_draw, statistical_edge['draw_probability']),
                ('away_win', odds.match_winner_away, statistical_edge['away_win_probability']),
                ('over_2.5', odds.over_under_2_5.get('over', 0), statistical_edge['over_2_5_probability']),
                ('under_2.5', odds.over_under_2_5.get('under', 0), 1 - statistical_edge['over_2_5_probability']),
                ('btts_yes', odds.both_teams_score.get('yes', 0), statistical_edge['btts_probability']),
                ('btts_no', odds.both_teams_score.get('no', 0), 1 - statistical_edge['btts_probability'])
            ]
            
            for market_name, odds_value, true_probability in markets:
                if odds_value > 0:
                    implied_probability = 1 / odds_value
                    value = (true_probability * odds_value) - 1
                    
                    if value > 0.05:  # 5% minimum value
                        value_bets.append({
                            'bookmaker': bookmaker,
                            'market': market_name,
                            'odds': odds_value,
                            'true_probability': true_probability,
                            'implied_probability': implied_probability,
                            'value': value,
                            'confidence': statistical_edge['confidence_score']
                        })
        
        # Sort by value descending
        value_bets.sort(key=lambda x: x['value'], reverse=True)
        return value_bets
    
    def _calculate_roi(self, value_bets: List[Dict], match_info: MatchInfo, 
                      statistical_edge: Dict[str, float]) -> List[Dict]:
        """Calculate ROI for each value bet"""
        logger.info("📊 Calculating ROI...")
        
        roi_calculations = []
        
        for bet in value_bets[:5]:  # Top 5 value bets
            # Kelly Criterion for optimal stake
            kelly_fraction = (bet['true_probability'] * bet['odds'] - 1) / (bet['odds'] - 1)
            
            # Conservative Kelly (use fraction of Kelly)
            optimal_stake = kelly_fraction * self.roi_params['kelly_fraction']
            optimal_stake = max(0.01, min(optimal_stake, self.roi_params['max_stake_pct']))
            
            # Expected ROI calculation
            expected_roi = (bet['true_probability'] * (bet['odds'] - 1) - 
                          (1 - bet['true_probability'])) * optimal_stake
            
            # Risk assessment
            risk_factors = self._assess_bet_risk(bet, match_info, statistical_edge)
            
            roi_calculations.append({
                'market': bet['market'],
                'bookmaker': bet['bookmaker'],
                'odds': bet['odds'],
                'optimal_stake_pct': optimal_stake * 100,
                'expected_roi': expected_roi * 100,
                'value': bet['value'] * 100,
                'confidence': bet['confidence'] * 100,
                'risk_score': risk_factors['overall_risk'],
                'risk_factors': risk_factors
            })
        
        return roi_calculations
    
    def _assess_bet_risk(self, bet: Dict, match_info: MatchInfo, 
                        statistical_edge: Dict[str, float]) -> Dict[str, Any]:
        """Assess risk factors for a specific bet"""
        risk_factors = {
            'market_liquidity': 0.8 if bet['market'] in ['home_win', 'away_win', 'draw'] else 0.6,
            'odds_movement': np.random.uniform(0.7, 0.9),  # Simulated odds stability
            'injury_impact': 0.9 if len([]) == 0 else 0.7,  # Based on key injuries
            'weather_impact': 0.95,  # Minimal weather impact for indoor sports
            'referee_impact': 0.85,  # Some referee bias possible
            'motivation_factor': 1.0 if match_info.importance == 'regular' else 0.8
        }
        
        # Calculate overall risk
        risk_weights = {
            'market_liquidity': 0.2,
            'odds_movement': 0.25,
            'injury_impact': 0.2,
            'weather_impact': 0.1,
            'referee_impact': 0.15,
            'motivation_factor': 0.1
        }
        
        overall_risk = sum(factor * risk_weights[name] 
                          for name, factor in risk_factors.items())
        
        risk_factors['overall_risk'] = overall_risk
        risk_factors['risk_level'] = self._categorize_risk(overall_risk)
        
        return risk_factors
    
    def _categorize_risk(self, risk_score: float) -> str:
        """Categorize risk level"""
        if risk_score >= 0.85:
            return "LOW"
        elif risk_score >= 0.70:
            return "MEDIUM"
        elif risk_score >= 0.55:
            return "HIGH"
        else:
            return "VERY_HIGH"
    
    def _assess_risk(self, match_info: MatchInfo, team_stats: Dict[str, TeamStats], 
                    external_factors: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive risk assessment"""
        return {
            'overall_risk': 0.75,
            'factors': external_factors,
            'recommendation': 'MEDIUM_RISK'
        }
    
    def _generate_recommendations(self, roi_analysis: List[Dict], 
                                risk_assessment: Dict[str, Any], 
                                statistical_edge: Dict[str, float]) -> ROIAnalysis:
        """Generate final betting recommendations"""
        
        if not roi_analysis:
            return self._create_no_bet_recommendation("no_match_id", "No profitable opportunities found")
        
        best_bet = roi_analysis[0]
        
        # Generate reasoning
        reasoning = f"""
        🎯 ANALYSIS SUMMARY:
        • Statistical Edge: {statistical_edge['confidence_score']:.1%} confidence
        • Best Value: {best_bet['value']:.1f}% on {best_bet['market']}
        • Expected ROI: {best_bet['expected_roi']:.1f}%
        • Risk Level: {best_bet['risk_score']:.1%} ({best_bet['risk_factors']['risk_level']})
        
        🧠 KEY FACTORS:
        • Market inefficiency detected in {best_bet['market']} market
        • {best_bet['bookmaker']} offering {best_bet['odds']:.2f} odds
        • True probability estimated at {best_bet['confidence']:.1f}%
        • Optimal stake: {best_bet['optimal_stake_pct']:.1f}% of bankroll
        """
        
        return ROIAnalysis(
            match_id="analysis_001",
            recommended_bet=f"{best_bet['market']} @ {best_bet['odds']:.2f}",
            stake_percentage=best_bet['optimal_stake_pct'],
            expected_roi=best_bet['expected_roi'],
            confidence_level=best_bet['confidence'],
            risk_rating=best_bet['risk_factors']['risk_level'],
            value_rating=min(10, best_bet['value'] / 10),
            reasoning=reasoning.strip(),
            alternative_bets=[
                {
                    'market': bet['market'],
                    'odds': bet['odds'],
                    'roi': bet['expected_roi'],
                    'stake_pct': bet['optimal_stake_pct']
                }
                for bet in roi_analysis[1:4]  # Top 3 alternatives
            ]
        )
    
    def _create_no_bet_recommendation(self, match_id: str, reason: str) -> ROIAnalysis:
        """Create a no-bet recommendation"""
        return ROIAnalysis(
            match_id=match_id,
            recommended_bet="NO BET",
            stake_percentage=0.0,
            expected_roi=0.0,
            confidence_level=0.0,
            risk_rating="NO_RISK",
            value_rating=0.0,
            reasoning=f"❌ No betting opportunity: {reason}",
            alternative_bets=[]
        )
    
    def analyze_multiple_matches(self, matches: List[MatchInfo]) -> List[ROIAnalysis]:
        """Analyze multiple matches and rank by ROI potential"""
        logger.info(f"🎯 Analyzing {len(matches)} matches for ROI opportunities...")
        
        analyses = []
        for match in matches:
            try:
                analysis = self.analyze_match(match)
                if analysis.expected_roi > self.roi_params['min_roi_threshold'] * 100:
                    analyses.append(analysis)
            except Exception as e:
                logger.error(f"❌ Error analyzing {match.match_id}: {e}")
        
        # Sort by expected ROI descending
        analyses.sort(key=lambda x: x.expected_roi, reverse=True)
        
        logger.info(f"✅ Found {len(analyses)} profitable opportunities")
        return analyses
    
    def get_daily_recommendations(self, date: datetime = None) -> Dict[str, Any]:
        """Get daily betting recommendations across all sports"""
        if date is None:
            date = datetime.now()
        
        logger.info(f"📅 Getting recommendations for {date.strftime('%Y-%m-%d')}")
        
        # Simulate getting matches for the day
        sample_matches = self._get_sample_matches(date)
        
        # Analyze all matches
        analyses = self.analyze_multiple_matches(sample_matches)
        
        # Categorize by sport and quality
        recommendations = {
            'date': date.strftime('%Y-%m-%d'),
            'total_matches_analyzed': len(sample_matches),
            'profitable_opportunities': len(analyses),
            'top_recommendations': analyses[:5],
            'by_sport': self._categorize_by_sport(analyses),
            'risk_distribution': self._analyze_risk_distribution(analyses),
            'bankroll_allocation': self._calculate_bankroll_allocation(analyses),
            'summary': self._generate_daily_summary(analyses)
        }
        
        return recommendations
    
    def _get_sample_matches(self, date: datetime) -> List[MatchInfo]:
        """Generate sample matches for demonstration"""
        matches = []
        
        # Sample football matches
        football_matches = [
            ("Manchester City", "Liverpool", "Premier League"),
            ("Barcelona", "Real Madrid", "La Liga"),
            ("Bayern Munich", "Borussia Dortmund", "Bundesliga"),
            ("Juventus", "AC Milan", "Serie A"),
            ("PSG", "Marseille", "Ligue 1")
        ]
        
        for i, (home, away, league) in enumerate(football_matches):
            matches.append(MatchInfo(
                match_id=f"football_{i+1}",
                sport="football",
                league=league,
                home_team=home,
                away_team=away,
                match_time=date + timedelta(hours=15 + i),
                venue=f"{home} Stadium",
                tv_coverage=True,
                importance="regular"
            ))
        
        # Sample tennis matches
        tennis_matches = [
            ("Novak Djokovic", "Carlos Alcaraz", "ATP Masters"),
            ("Iga Swiatek", "Aryna Sabalenka", "WTA Premier"),
            ("Stefanos Tsitsipas", "Alexander Zverev", "ATP Masters")
        ]
        
        for i, (player1, player2, tournament) in enumerate(tennis_matches):
            matches.append(MatchInfo(
                match_id=f"tennis_{i+1}",
                sport="tennis",
                league=tournament,
                home_team=player1,
                away_team=player2,
                match_time=date + timedelta(hours=12 + i * 2),
                venue="Center Court",
                tv_coverage=True,
                importance="regular"
            ))
        
        return matches
    
    def _categorize_by_sport(self, analyses: List[ROIAnalysis]) -> Dict[str, List[ROIAnalysis]]:
        """Categorize recommendations by sport"""
        by_sport = {}
        
        for analysis in analyses:
            # Extract sport from match_id (simplified)
            sport = analysis.match_id.split('_')[0] if '_' in analysis.match_id else 'unknown'
            
            if sport not in by_sport:
                by_sport[sport] = []
            
            by_sport[sport].append(analysis)
        
        return by_sport
    
    def _analyze_risk_distribution(self, analyses: List[ROIAnalysis]) -> Dict[str, int]:
        """Analyze risk distribution of recommendations"""
        risk_counts = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'VERY_HIGH': 0}
        
        for analysis in analyses:
            risk_counts[analysis.risk_rating] += 1
        
        return risk_counts
    
    def _calculate_bankroll_allocation(self, analyses: List[ROIAnalysis]) -> Dict[str, float]:
        """Calculate optimal bankroll allocation"""
        total_allocation = sum(analysis.stake_percentage for analysis in analyses)
        
        return {
            'total_recommended_allocation': min(total_allocation, 20.0),  # Max 20% of bankroll
            'number_of_bets': len(analyses),
            'average_stake': total_allocation / len(analyses) if analyses else 0,
            'max_single_stake': max((analysis.stake_percentage for analysis in analyses), default=0),
            'diversification_score': len(set(analysis.risk_rating for analysis in analyses))
        }
    
    def _generate_daily_summary(self, analyses: List[ROIAnalysis]) -> str:
        """Generate daily summary"""
        if not analyses:
            return "❌ No profitable betting opportunities found today."
        
        avg_roi = np.mean([analysis.expected_roi for analysis in analyses])
        best_roi = max(analysis.expected_roi for analysis in analyses)
        
        return f"""
        📊 DAILY BETTING SUMMARY:
        • {len(analyses)} profitable opportunities identified
        • Average expected ROI: {avg_roi:.1f}%
        • Best opportunity ROI: {best_roi:.1f}%
        • Risk distribution: Balanced across multiple levels
        • Recommended total allocation: {min(sum(a.stake_percentage for a in analyses), 20.0):.1f}%
        
        🎯 Focus on top 3 recommendations for optimal risk-reward balance.
        """

def main():
    """Main function for testing the prematch analyzer"""
    print("🎯 PREMATCH ANALYZER - SPORTS BETTING INTELLIGENCE")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = PrematchAnalyzer()
    
    # Get daily recommendations
    recommendations = analyzer.get_daily_recommendations()
    
    print(f"\n📅 DAILY RECOMMENDATIONS - {recommendations['date']}")
    print("=" * 60)
    print(f"📊 Matches analyzed: {recommendations['total_matches_analyzed']}")
    print(f"💰 Profitable opportunities: {recommendations['profitable_opportunities']}")
    
    if recommendations['top_recommendations']:
        print(f"\n🏆 TOP RECOMMENDATIONS:")
        print("-" * 40)
        
        for i, rec in enumerate(recommendations['top_recommendations'], 1):
            print(f"\n{i}. {rec.recommended_bet}")
            print(f"   💰 Expected ROI: {rec.expected_roi:.1f}%")
            print(f"   🎯 Confidence: {rec.confidence_level:.1f}%")
            print(f"   💵 Stake: {rec.stake_percentage:.1f}% of bankroll")
            print(f"   🛡️ Risk: {rec.risk_rating}")
            print(f"   ⭐ Value Rating: {rec.value_rating:.1f}/10")
    
    print(f"\n📈 BANKROLL ALLOCATION:")
    print("-" * 30)
    allocation = recommendations['bankroll_allocation']
    print(f"Total allocation: {allocation['total_recommended_allocation']:.1f}%")
    print(f"Number of bets: {allocation['number_of_bets']}")
    print(f"Average stake: {allocation['average_stake']:.1f}%")
    
    print(f"\n🎲 RISK DISTRIBUTION:")
    print("-" * 25)
    for risk_level, count in recommendations['risk_distribution'].items():
        print(f"{risk_level}: {count} bets")
    
    print(f"\n{recommendations['summary']}")

if __name__ == "__main__":
    main()
