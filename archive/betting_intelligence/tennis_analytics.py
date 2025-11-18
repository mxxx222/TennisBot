#!/usr/bin/env python3
"""
🎾 TENNIS ANALYTICS MODULE - ITF WOMEN FOCUS
==========================================

Phase 4D: Tennis-specific analytics equivalent to soccer xG data
Provides advanced tennis metrics for enhanced value detection

Features:
- Ace percentage and service statistics
- Break point conversion rates
- Form analysis and momentum tracking
- Surface-specific performance metrics
- Head-to-head pattern analysis
- Tournament level adjustments
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json
import random

logger = logging.getLogger(__name__)

@dataclass
class TennisPlayerStats:
    """Comprehensive tennis player statistics"""
    player_name: str
    ranking: Optional[int]
    
    # Service statistics
    ace_percentage: float  # % of aces per service game
    first_serve_percentage: float  # % of first serves in
    first_serve_won: float  # % of first serve points won
    second_serve_won: float  # % of second serve points won
    service_games_won: float  # % of service games won
    
    # Return statistics  
    first_serve_return_won: float  # % of opponent first serve points won
    second_serve_return_won: float  # % of opponent second serve points won
    break_points_converted: float  # % of break points converted
    return_games_won: float  # % of return games won
    
    # Match statistics
    tiebreak_win_rate: float  # % of tiebreaks won
    deciding_set_record: float  # % of deciding sets won
    
    # Form and momentum
    recent_form: str  # "WWLWL" format (last 5 matches)
    win_streak: int  # Current win streak
    loss_streak: int  # Current loss streak
    
    # Surface-specific
    surface_record: Dict[str, float]  # Win % by surface
    
    # Tournament level
    itf_record: float  # Win % in ITF tournaments
    
    # Timestamp
    last_updated: datetime

@dataclass
class TennisMatchAnalytics:
    """Advanced tennis match analytics"""
    match_id: str
    player1: str
    player2: str
    tournament: str
    surface: str
    
    # Player statistics
    player1_stats: TennisPlayerStats
    player2_stats: TennisPlayerStats
    
    # Match-specific analytics
    service_advantage: float  # Who has service advantage (-1 to 1)
    return_advantage: float  # Who has return advantage (-1 to 1)
    surface_advantage: float  # Surface-specific advantage (-1 to 1)
    form_momentum: float  # Recent form advantage (-1 to 1)
    head_to_head_edge: float  # H2H advantage (-1 to 1)
    
    # Combined metrics (tennis equivalent of xG)
    expected_win_probability: float  # P1 win probability based on analytics
    value_score: float  # Overall value score (0-10)
    confidence_level: float  # Confidence in analytics (0-1)
    
    # Risk factors
    risk_factors: List[str]
    
    # Timestamp
    generated_at: datetime

class TennisAnalyzer:
    """Advanced tennis analytics engine"""
    
    def __init__(self):
        self.player_database = {}  # Cache for player statistics
        self.match_cache = {}  # Cache for match analytics
        
        # Analytics configuration
        self.config = {
            'ace_weight': 0.15,  # Weight for ace percentage in analysis
            'service_weight': 0.25,  # Weight for service statistics
            'return_weight': 0.20,  # Weight for return statistics
            'form_weight': 0.20,  # Weight for recent form
            'surface_weight': 0.10,  # Weight for surface advantage
            'h2h_weight': 0.10,  # Weight for head-to-head
            'min_matches_for_stats': 5,  # Minimum matches for reliable stats
            'form_lookback_days': 90,  # Days to look back for form analysis
        }
        
        # Performance tracking
        self.analyses_generated = 0
        self.cache_hits = 0
        
    async def analyze_match(self, match_data: Dict[str, Any]) -> TennisMatchAnalytics:
        """Generate comprehensive tennis match analytics"""
        
        try:
            match_id = match_data.get('match_id', 'unknown')
            
            # Check cache first
            if match_id in self.match_cache:
                self.cache_hits += 1
                return self.match_cache[match_id]
            
            # Get player statistics
            player1_stats = await self._get_player_stats(match_data.get('player1', 'Player 1'))
            player2_stats = await self._get_player_stats(match_data.get('player2', 'Player 2'))
            
            # Calculate match-specific advantages
            service_advantage = self._calculate_service_advantage(player1_stats, player2_stats)
            return_advantage = self._calculate_return_advantage(player1_stats, player2_stats)
            surface_advantage = self._calculate_surface_advantage(
                player1_stats, player2_stats, match_data.get('surface', 'Hard')
            )
            form_momentum = self._calculate_form_momentum(player1_stats, player2_stats)
            h2h_edge = self._calculate_h2h_edge(
                match_data.get('player1'), match_data.get('player2'), 
                match_data.get('head_to_head')
            )
            
            # Calculate expected win probability (tennis equivalent of xG)
            win_probability = self._calculate_win_probability(
                service_advantage, return_advantage, surface_advantage, 
                form_momentum, h2h_edge
            )
            
            # Calculate value score
            value_score = self._calculate_value_score(
                win_probability, match_data.get('player1_odds', 1.50)
            )
            
            # Assess confidence level
            confidence_level = self._assess_confidence(player1_stats, player2_stats)
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(
                player1_stats, player2_stats, match_data
            )
            
            # Create analytics object
            analytics = TennisMatchAnalytics(
                match_id=match_id,
                player1=match_data.get('player1', 'Player 1'),
                player2=match_data.get('player2', 'Player 2'),
                tournament=match_data.get('tournament', 'Unknown'),
                surface=match_data.get('surface', 'Hard'),
                player1_stats=player1_stats,
                player2_stats=player2_stats,
                service_advantage=service_advantage,
                return_advantage=return_advantage,
                surface_advantage=surface_advantage,
                form_momentum=form_momentum,
                head_to_head_edge=h2h_edge,
                expected_win_probability=win_probability,
                value_score=value_score,
                confidence_level=confidence_level,
                risk_factors=risk_factors,
                generated_at=datetime.now()
            )
            
            # Cache the result
            self.match_cache[match_id] = analytics
            self.analyses_generated += 1
            
            logger.info(f"🎾 Tennis analytics generated for {analytics.player1} vs {analytics.player2}")
            logger.info(f"   Win Probability: {win_probability:.1%} | Value Score: {value_score:.1f}/10")
            
            return analytics
            
        except Exception as e:
            logger.error(f"💥 Tennis analytics error: {e}")
            # Return basic analytics on error
            return self._create_basic_analytics(match_data)
    
    async def _get_player_stats(self, player_name: str) -> TennisPlayerStats:
        """Get comprehensive player statistics"""
        
        # Check cache first
        if player_name in self.player_database:
            return self.player_database[player_name]
        
        # In production, this would fetch from tennis databases
        # For now, generate realistic statistics
        stats = self._generate_realistic_stats(player_name)
        
        # Cache the stats
        self.player_database[player_name] = stats
        
        return stats
    
    def _generate_realistic_stats(self, player_name: str) -> TennisPlayerStats:
        """Generate realistic tennis statistics for ITF Women players"""
        
        # Generate realistic ITF Women statistics
        # Based on typical ITF tournament performance ranges
        
        stats = TennisPlayerStats(
            player_name=player_name,
            ranking=random.randint(150, 800),  # ITF ranking range
            
            # Service statistics (ITF Women typical ranges)
            ace_percentage=random.uniform(2.0, 8.0),  # 2-8% aces
            first_serve_percentage=random.uniform(55.0, 70.0),  # 55-70% first serves in
            first_serve_won=random.uniform(60.0, 75.0),  # 60-75% first serve points won
            second_serve_won=random.uniform(40.0, 55.0),  # 40-55% second serve points won
            service_games_won=random.uniform(70.0, 85.0),  # 70-85% service games won
            
            # Return statistics
            first_serve_return_won=random.uniform(25.0, 40.0),  # 25-40% return points won
            second_serve_return_won=random.uniform(45.0, 60.0),  # 45-60% return points won
            break_points_converted=random.uniform(30.0, 50.0),  # 30-50% break points converted
            return_games_won=random.uniform(15.0, 30.0),  # 15-30% return games won
            
            # Match statistics
            tiebreak_win_rate=random.uniform(40.0, 60.0),  # 40-60% tiebreaks won
            deciding_set_record=random.uniform(45.0, 55.0),  # 45-55% deciding sets won
            
            # Form and momentum
            recent_form=self._generate_recent_form(),
            win_streak=random.randint(0, 4),
            loss_streak=random.randint(0, 3),
            
            # Surface-specific records
            surface_record={
                'Hard': random.uniform(45.0, 65.0),
                'Clay': random.uniform(40.0, 70.0),
                'Grass': random.uniform(35.0, 60.0)
            },
            
            # Tournament level
            itf_record=random.uniform(50.0, 70.0),  # ITF win percentage
            
            last_updated=datetime.now()
        )
        
        return stats
    
    def _generate_recent_form(self) -> str:
        """Generate realistic recent form string"""
        results = ['W', 'L']
        form = ''.join(random.choices(results, weights=[0.55, 0.45], k=5))  # Slight win bias
        return form
    
    def _calculate_service_advantage(self, p1_stats: TennisPlayerStats, 
                                   p2_stats: TennisPlayerStats) -> float:
        """Calculate service advantage (-1 to 1, positive favors player 1)"""
        
        # Compare service statistics
        p1_service_score = (
            p1_stats.ace_percentage * 0.2 +
            p1_stats.first_serve_percentage * 0.3 +
            p1_stats.first_serve_won * 0.3 +
            p1_stats.service_games_won * 0.2
        )
        
        p2_service_score = (
            p2_stats.ace_percentage * 0.2 +
            p2_stats.first_serve_percentage * 0.3 +
            p2_stats.first_serve_won * 0.3 +
            p2_stats.service_games_won * 0.2
        )
        
        # Normalize to -1 to 1 range
        max_possible_score = 8.0 * 0.2 + 70.0 * 0.3 + 75.0 * 0.3 + 85.0 * 0.2
        min_possible_score = 2.0 * 0.2 + 55.0 * 0.3 + 60.0 * 0.3 + 70.0 * 0.2
        
        normalized_diff = (p1_service_score - p2_service_score) / (max_possible_score - min_possible_score)
        
        return max(-1.0, min(1.0, normalized_diff * 2))  # Scale and clamp
    
    def _calculate_return_advantage(self, p1_stats: TennisPlayerStats, 
                                  p2_stats: TennisPlayerStats) -> float:
        """Calculate return advantage (-1 to 1, positive favors player 1)"""
        
        # Compare return statistics
        p1_return_score = (
            p1_stats.first_serve_return_won * 0.4 +
            p1_stats.second_serve_return_won * 0.3 +
            p1_stats.break_points_converted * 0.3
        )
        
        p2_return_score = (
            p2_stats.first_serve_return_won * 0.4 +
            p2_stats.second_serve_return_won * 0.3 +
            p2_stats.break_points_converted * 0.3
        )
        
        # Normalize to -1 to 1 range
        max_possible_score = 40.0 * 0.4 + 60.0 * 0.3 + 50.0 * 0.3
        min_possible_score = 25.0 * 0.4 + 45.0 * 0.3 + 30.0 * 0.3
        
        normalized_diff = (p1_return_score - p2_return_score) / (max_possible_score - min_possible_score)
        
        return max(-1.0, min(1.0, normalized_diff * 2))  # Scale and clamp
    
    def _calculate_surface_advantage(self, p1_stats: TennisPlayerStats, 
                                   p2_stats: TennisPlayerStats, surface: str) -> float:
        """Calculate surface-specific advantage"""
        
        p1_surface_record = p1_stats.surface_record.get(surface, 50.0)
        p2_surface_record = p2_stats.surface_record.get(surface, 50.0)
        
        # Normalize difference
        diff = (p1_surface_record - p2_surface_record) / 100.0
        
        return max(-1.0, min(1.0, diff * 2))  # Scale and clamp
    
    def _calculate_form_momentum(self, p1_stats: TennisPlayerStats, 
                               p2_stats: TennisPlayerStats) -> float:
        """Calculate recent form momentum"""
        
        def form_score(form_string: str) -> float:
            """Convert form string to numerical score"""
            score = 0
            for i, result in enumerate(form_string):
                weight = 1.0 - (i * 0.15)  # Recent matches weighted more
                if result == 'W':
                    score += weight
                else:
                    score -= weight
            return score
        
        p1_form_score = form_score(p1_stats.recent_form)
        p2_form_score = form_score(p2_stats.recent_form)
        
        # Factor in win/loss streaks
        p1_streak_bonus = p1_stats.win_streak * 0.1 - p1_stats.loss_streak * 0.1
        p2_streak_bonus = p2_stats.win_streak * 0.1 - p2_stats.loss_streak * 0.1
        
        total_diff = (p1_form_score + p1_streak_bonus) - (p2_form_score + p2_streak_bonus)
        
        return max(-1.0, min(1.0, total_diff / 3.0))  # Normalize and clamp
    
    def _calculate_h2h_edge(self, player1: str, player2: str, h2h_data: Optional[str]) -> float:
        """Calculate head-to-head advantage"""
        
        if not h2h_data or h2h_data == 'No data':
            return 0.0  # No advantage if no H2H data
        
        try:
            # Parse H2H data (format: "3-1" means player1 leads 3-1)
            if '-' in h2h_data:
                p1_wins, p2_wins = map(int, h2h_data.split('-'))
                total_matches = p1_wins + p2_wins
                
                if total_matches == 0:
                    return 0.0
                
                p1_win_rate = p1_wins / total_matches
                
                # Convert to -1 to 1 scale
                return (p1_win_rate - 0.5) * 2
            
        except (ValueError, AttributeError):
            pass
        
        return 0.0  # Default to no advantage
    
    def _calculate_win_probability(self, service_adv: float, return_adv: float,
                                 surface_adv: float, form_adv: float, h2h_adv: float) -> float:
        """Calculate expected win probability (tennis equivalent of xG)"""
        
        # Weighted combination of advantages
        combined_advantage = (
            service_adv * self.config['service_weight'] +
            return_adv * self.config['return_weight'] +
            surface_adv * self.config['surface_weight'] +
            form_adv * self.config['form_weight'] +
            h2h_adv * self.config['h2h_weight']
        )
        
        # Convert to probability (sigmoid-like function)
        # Base probability is 50%, adjusted by combined advantage
        probability = 0.5 + (combined_advantage * 0.25)  # Max swing of ±25%
        
        return max(0.1, min(0.9, probability))  # Clamp to reasonable range
    
    def _calculate_value_score(self, win_probability: float, odds: float) -> float:
        """Calculate value score (0-10 scale)"""
        
        # Calculate implied probability from odds
        implied_probability = 1.0 / odds
        
        # Calculate edge
        edge = win_probability - implied_probability
        
        # Convert edge to 0-10 scale
        # Positive edge = value, negative edge = no value
        if edge <= 0:
            return 0.0
        
        # Scale: 10% edge = 10/10, 5% edge = 5/10, etc.
        value_score = min(10.0, edge * 100)
        
        return value_score
    
    def _assess_confidence(self, p1_stats: TennisPlayerStats, 
                          p2_stats: TennisPlayerStats) -> float:
        """Assess confidence in analytics (0-1 scale)"""
        
        confidence = 0.5  # Base confidence
        
        # Increase confidence if we have ranking data
        if p1_stats.ranking and p2_stats.ranking:
            confidence += 0.2
        
        # Increase confidence if players have recent form data
        if len(p1_stats.recent_form) >= 5 and len(p2_stats.recent_form) >= 5:
            confidence += 0.2
        
        # Increase confidence if stats are recent
        days_since_update = (datetime.now() - p1_stats.last_updated).days
        if days_since_update <= 7:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _identify_risk_factors(self, p1_stats: TennisPlayerStats, 
                             p2_stats: TennisPlayerStats, match_data: Dict) -> List[str]:
        """Identify potential risk factors"""
        
        risks = []
        
        # Ranking-based risks
        if p1_stats.ranking and p2_stats.ranking:
            ranking_diff = abs(p1_stats.ranking - p2_stats.ranking)
            if ranking_diff < 50:
                risks.append("Close ranking match - unpredictable")
        
        # Form-based risks
        if 'L' in p1_stats.recent_form[-2:] and 'L' in p2_stats.recent_form[-2:]:
            risks.append("Both players in poor recent form")
        
        # Surface risks
        surface = match_data.get('surface', 'Hard')
        if surface == 'Grass':
            risks.append("Grass court - higher variance")
        
        # Tournament level risks
        tournament = match_data.get('tournament', '')
        if 'W15' in tournament:
            risks.append("W15 tournament - lower prize money, motivation risk")
        
        # Odds-based risks
        odds = match_data.get('player1_odds', 1.50)
        if odds < 1.20:
            risks.append("Very low odds - limited upside")
        elif odds > 2.50:
            risks.append("High odds - underdog bet")
        
        return risks
    
    def _create_basic_analytics(self, match_data: Dict) -> TennisMatchAnalytics:
        """Create basic analytics when full analysis fails"""
        
        # Create minimal stats
        basic_stats = TennisPlayerStats(
            player_name="Unknown",
            ranking=None,
            ace_percentage=5.0,
            first_serve_percentage=60.0,
            first_serve_won=65.0,
            second_serve_won=45.0,
            service_games_won=75.0,
            first_serve_return_won=35.0,
            second_serve_return_won=50.0,
            break_points_converted=40.0,
            return_games_won=25.0,
            tiebreak_win_rate=50.0,
            deciding_set_record=50.0,
            recent_form="WWLWL",
            win_streak=0,
            loss_streak=0,
            surface_record={'Hard': 50.0, 'Clay': 50.0, 'Grass': 50.0},
            itf_record=50.0,
            last_updated=datetime.now()
        )
        
        return TennisMatchAnalytics(
            match_id=match_data.get('match_id', 'unknown'),
            player1=match_data.get('player1', 'Player 1'),
            player2=match_data.get('player2', 'Player 2'),
            tournament=match_data.get('tournament', 'Unknown'),
            surface=match_data.get('surface', 'Hard'),
            player1_stats=basic_stats,
            player2_stats=basic_stats,
            service_advantage=0.0,
            return_advantage=0.0,
            surface_advantage=0.0,
            form_momentum=0.0,
            head_to_head_edge=0.0,
            expected_win_probability=0.5,
            value_score=0.0,
            confidence_level=0.3,
            risk_factors=["Limited data available"],
            generated_at=datetime.now()
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get analyzer performance statistics"""
        
        return {
            'analyses_generated': self.analyses_generated,
            'cache_hits': self.cache_hits,
            'cache_size': len(self.match_cache),
            'player_database_size': len(self.player_database),
            'cache_hit_rate': f"{(self.cache_hits / max(self.analyses_generated, 1)) * 100:.1f}%"
        }

# Configuration for tennis analytics
TENNIS_ANALYTICS_CONFIG = {
    'update_interval': 3600,  # Update player stats every hour
    'cache_expiry': 86400,  # Cache match analytics for 24 hours
    'min_confidence_threshold': 0.6,  # Minimum confidence for reliable analytics
    'value_threshold': 3.0,  # Minimum value score to consider (out of 10)
    'max_risk_factors': 3,  # Maximum acceptable risk factors
}

if __name__ == "__main__":
    async def test_tennis_analytics():
        """Test the tennis analytics system"""
        print("🎾 Testing Tennis Analytics System...")
        
        analyzer = TennisAnalyzer()
        
        # Test match data
        test_match = {
            'match_id': 'test_itf_w15_antalya_001',
            'player1': 'Anna Konjuh',
            'player2': 'Maria Timofeeva',
            'tournament': 'ITF W15 Antalya',
            'surface': 'Hard',
            'player1_odds': 1.65,
            'player2_odds': 2.20,
            'head_to_head': '2-1'
        }
        
        # Generate analytics
        analytics = await analyzer.analyze_match(test_match)
        
        print(f"✅ Analytics generated for {analytics.player1} vs {analytics.player2}")
        print(f"📊 Expected Win Probability: {analytics.expected_win_probability:.1%}")
        print(f"🎯 Value Score: {analytics.value_score:.1f}/10")
        print(f"⭐ Confidence Level: {analytics.confidence_level:.1%}")
        print(f"⚠️ Risk Factors: {len(analytics.risk_factors)}")
        
        if analytics.risk_factors:
            for risk in analytics.risk_factors:
                print(f"   - {risk}")
        
        # Performance stats
        stats = analyzer.get_performance_stats()
        print(f"📈 Performance: {stats}")
    
    asyncio.run(test_tennis_analytics())
