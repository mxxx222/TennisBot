"""
AI-Powered Match Analysis Module
Uses Venice AI for advanced pattern recognition and value detection
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json

from ai_analysis.venice_client import VeniceAIClient, AIAnalysisResult
from ai_analysis.ai_config import VeniceAIConfig

logger = logging.getLogger(__name__)

@dataclass
class EnhancedOpportunity:
    """Betting opportunity enhanced with AI analysis - Multi-sport support"""
    # Original opportunity data
    match_id: str
    sport: str  # soccer, tennis
    team: str  # or player name for tennis
    opponent: str
    odds: float
    league: str  # or tournament for tennis
    commence_time: datetime
    
    # AI-enhanced data
    ai_edge_estimate: float
    ai_confidence_score: float
    ai_risk_factors: List[str]
    ai_value_assessment: str
    ai_reasoning: str
    ai_recommended_action: str
    
    # Combined scoring
    combined_edge: float
    final_confidence: float
    priority_score: float
    
    # Cost tracking
    analysis_cost: float
    cost_savings_vs_openai: float
    
    # Sport-specific fields
    surface: Optional[str] = None  # Tennis surface (Hard, Clay, Grass)
    tournament_level: Optional[str] = None  # ITF W15, ITF W25, etc.
    player_ranking: Optional[int] = None  # Tennis player ranking
    head_to_head: Optional[str] = None  # Tennis H2H record

class AIMatchAnalyzer:
    """AI-powered match analysis using Venice AI"""
    
    def __init__(self, database = None):
        self.config = VeniceAIConfig()
        self.database = database
        self.ai_client = VeniceAIClient()
        
        # Analysis cache to avoid duplicate API calls
        self.analysis_cache: Dict[str, AIAnalysisResult] = {}
        self.cache_expiry = 3600  # 1 hour cache
        
        # Performance tracking
        self.total_analyses = 0
        self.cache_hits = 0
        self.ai_enhanced_opportunities = 0
        
    async def analyze_opportunities(self, opportunities: List, xg_data: Dict = None) -> List[EnhancedOpportunity]:
        """Analyze opportunities with AI enhancement including xG data"""
        
        if not opportunities:
            return []
        
        logger.info(f"Starting AI analysis of {len(opportunities)} opportunities...")
        
        enhanced_opportunities = []
        
        async with self.ai_client as client:
            # Test connection first
            if not await client.test_connection():
                logger.error("Venice AI connection failed, falling back to basic analysis")
                return self._fallback_analysis(opportunities)
            
            # Analyze each opportunity with xG data
            for opportunity in opportunities:
                try:
                    enhanced = await self._analyze_single_opportunity(client, opportunity, xg_data)
                    if enhanced:
                        enhanced_opportunities.append(enhanced)
                        self.ai_enhanced_opportunities += 1
                
                except Exception as e:
                    logger.error(f"Failed to analyze {opportunity.team}: {e}")
                    # Add fallback analysis
                    fallback = self._create_fallback_opportunity(opportunity)
                    enhanced_opportunities.append(fallback)
        
        # Sort by combined priority score
        enhanced_opportunities.sort(key=lambda x: x.priority_score, reverse=True)
        
        logger.info(f"AI analysis completed: {len(enhanced_opportunities)} enhanced opportunities")
        
        return enhanced_opportunities
    
    async def _analyze_single_opportunity(self, client: VeniceAIClient, 
                                        opportunity, xg_data: Dict = None) -> Optional[EnhancedOpportunity]:
        """Analyze a single opportunity with AI"""
        
        # Create cache key
        cache_key = f"{opportunity.match_id}_{opportunity.odds:.2f}"
        
        # Check cache first
        if cache_key in self.analysis_cache:
            cached_time = getattr(self.analysis_cache[cache_key], 'timestamp', datetime.now())
            if (datetime.now() - cached_time).total_seconds() < self.cache_expiry:
                ai_result = self.analysis_cache[cache_key]
                self.cache_hits += 1
                logger.debug(f"Using cached analysis for {opportunity.team}")
            else:
                # Cache expired, remove entry
                del self.analysis_cache[cache_key]
                ai_result = None
        else:
            ai_result = None
        
        # Get AI analysis if not cached
        if not ai_result:
            # Prepare match data for AI with xG enhancement
            match_data = self._prepare_match_data(opportunity, xg_data)
            
            # Get historical context
            historical_context = await self._get_historical_context(opportunity)
            
            # Get AI analysis
            ai_result = await client.analyze_match_value(match_data, historical_context)
            
            if ai_result:
                # Cache the result
                ai_result.timestamp = datetime.now()
                self.analysis_cache[cache_key] = ai_result
                self.total_analyses += 1
            else:
                logger.warning(f"AI analysis failed for {opportunity.team}")
                return self._create_fallback_opportunity(opportunity)
        
        # Combine AI analysis with existing data
        enhanced = self._combine_analysis(opportunity, ai_result)
        
        return enhanced
    
    def _prepare_match_data(self, opportunity, xg_data: Dict = None) -> Dict:
        """Prepare match data for AI analysis - Multi-sport support with xG enhancement"""
        
        # Determine sport type
        sport = getattr(opportunity, 'sport', 'soccer')  # Default to soccer for backward compatibility
        
        if sport == 'tennis':
            # Tennis-specific data preparation
            match_data = {
                'match_id': opportunity.match_id,
                'sport': 'tennis',
                'player1': opportunity.team,
                'player2': opportunity.opponent,
                'player1_odds': opportunity.odds,
                'player2_odds': getattr(opportunity, 'opponent_odds', 2.0),
                'tournament': opportunity.league,
                'tournament_level': getattr(opportunity, 'tournament_level', 'ITF'),
                'surface': getattr(opportunity, 'surface', 'Hard'),
                'commence_time': opportunity.commence_time.isoformat(),
                'current_edge': getattr(opportunity, 'edge_estimate', 0),
                'confidence': getattr(opportunity, 'confidence', 'Medium'),
                'stake': getattr(opportunity, 'recommended_stake', 0),
                'player1_ranking': getattr(opportunity, 'player_ranking', None),
                'player2_ranking': getattr(opportunity, 'opponent_ranking', None),
                'head_to_head': getattr(opportunity, 'head_to_head', None),
                'recent_form': getattr(opportunity, 'recent_form', None)
            }
            
            # Tennis-specific analysis context
            match_data.update({
                'is_itf_women': 'ITF' in match_data['tournament_level'],
                'odds_in_profitable_range': 1.30 <= opportunity.odds <= 1.80,
                'ranking_differential': (match_data['player2_ranking'] or 500) - (match_data['player1_ranking'] or 500),
                'surface_advantage': self._assess_surface_advantage(match_data['surface'], match_data['player1']),
                'has_tennis_data': True
            })
            
        else:
            # Soccer-specific data preparation (existing logic)
            match_data = {
                'match_id': opportunity.match_id,
                'sport': 'soccer',
                'home_team': opportunity.team,
                'away_team': opportunity.opponent,
                'home_odds': opportunity.odds,
                'away_odds': getattr(opportunity, 'opponent_odds', 2.0),
                'league': opportunity.league,
                'commence_time': opportunity.commence_time.isoformat(),
                'current_edge': getattr(opportunity, 'edge_estimate', 0),
                'confidence': getattr(opportunity, 'confidence', 'Medium'),
                'stake': getattr(opportunity, 'recommended_stake', 0)
            }
            
            # Add xG data if available (soccer only)
            if xg_data and opportunity.match_id in xg_data:
                xg = xg_data[opportunity.match_id]
                match_data.update({
                    'xg_data': {
                        'home_xg': xg.home_xg,
                        'away_xg': xg.away_xg,
                        'home_shots': xg.home_shots,
                        'away_shots': xg.away_shots,
                        'xg_difference': xg.home_xg - xg.away_xg,
                        'total_xg': xg.home_xg + xg.away_xg,
                        'xg_dominance': 'home' if xg.home_xg > xg.away_xg else 'away',
                        'shot_efficiency': {
                            'home': xg.home_xg / max(xg.home_shots, 1),
                            'away': xg.away_xg / max(xg.away_shots, 1)
                        }
                    },
                    'has_xg_data': True
                })
                
                logger.debug(f"Enhanced {opportunity.match_id} with xG data: {xg.home_xg:.1f} - {xg.away_xg:.1f}")
            else:
                match_data['has_xg_data'] = False
        
        return match_data
    
    def _assess_surface_advantage(self, surface: str, player: str) -> str:
        """Assess surface advantage for tennis player (simplified)"""
        # This is a simplified assessment - in production would use player stats
        surface_preferences = {
            'Clay': 'baseline_specialist',
            'Grass': 'serve_and_volley',
            'Hard': 'all_court_player'
        }
        
        return surface_preferences.get(surface, 'neutral')
    
    async def _get_historical_context(self, opportunity) -> str:
        """Get historical context for the match/teams"""
        
        try:
            # Get recent opportunities for similar matches (if database available)
            if self.database:
                recent_opportunities = self.database.get_recent_opportunities(hours=168)  # 1 week
            else:
                recent_opportunities = []
            
            # Filter for same league
            league_opportunities = [
                opp for opp in recent_opportunities 
                if opp.league == opportunity.league
            ]
            
            # Filter for similar odds range
            odds_min, odds_max = opportunity.odds * 0.9, opportunity.odds * 1.1
            similar_odds = [
                opp for opp in league_opportunities
                if odds_min <= opp.odds <= odds_max
            ]
            
            if similar_odds:
                avg_edge = sum(opp.edge_estimate for opp in similar_odds) / len(similar_odds)
                success_rate = len([opp for opp in similar_odds if opp.urgency_level in ['HIGH', 'CRITICAL']]) / len(similar_odds)
                
                context = f"""Historical context for {opportunity.league}:
- Similar odds range: {len(similar_odds)} recent opportunities
- Average edge: {avg_edge:.1f}%
- Success rate: {success_rate:.1%}
- League tier: {self._get_league_tier(opportunity.league)}
- Recent volume: {len(league_opportunities)} opportunities in past week"""
                
                return context
            else:
                return f"Limited historical data for {opportunity.league} at {opportunity.odds:.2f} odds"
        
        except Exception as e:
            logger.error(f"Failed to get historical context: {e}")
            return "Historical context unavailable"
    
    def _get_league_tier(self, league: str) -> int:
        """Get league tier for context"""
        
        if 'champ' in league.lower() or 'bundesliga2' in league.lower():
            return 1
        elif 'league1' in league.lower() or 'serie_b' in league.lower() or 'segunda' in league.lower():
            return 2
        else:
            return 3
    
    def _combine_analysis(self, opportunity, ai_result: AIAnalysisResult) -> EnhancedOpportunity:
        """Combine original analysis with AI insights"""
        
        # Get original edge estimate
        original_edge = getattr(opportunity, 'edge_estimate', 0)
        original_confidence = self._confidence_to_score(getattr(opportunity, 'confidence', 'Medium'))
        
        # Combine edge estimates (weighted average)
        ai_weight = min(ai_result.confidence_score, 0.8)  # Cap AI weight at 80%
        original_weight = 1 - ai_weight
        
        combined_edge = (original_edge * original_weight + ai_result.edge_estimate * ai_weight)
        
        # Combine confidence scores
        final_confidence = (original_confidence * 0.4 + ai_result.confidence_score * 0.6)
        
        # Calculate priority score
        priority_score = self._calculate_priority_score(
            combined_edge, final_confidence, ai_result, opportunity
        )
        
        return EnhancedOpportunity(
            match_id=opportunity.match_id,
            team=opportunity.team,
            opponent=opportunity.opponent,
            odds=opportunity.odds,
            league=opportunity.league,
            commence_time=opportunity.commence_time,
            ai_edge_estimate=ai_result.edge_estimate,
            ai_confidence_score=ai_result.confidence_score,
            ai_risk_factors=ai_result.risk_factors,
            ai_value_assessment=ai_result.value_assessment,
            ai_reasoning=ai_result.reasoning,
            ai_recommended_action=ai_result.recommended_action,
            combined_edge=combined_edge,
            final_confidence=final_confidence,
            priority_score=priority_score,
            analysis_cost=ai_result.cost,
            cost_savings_vs_openai=self._calculate_openai_savings(ai_result)
        )
    
    def _confidence_to_score(self, confidence: str) -> float:
        """Convert confidence string to numeric score"""
        
        confidence_map = {
            'Low': 0.3,
            'Medium': 0.6,
            'High': 0.8,
            'Critical': 0.9
        }
        
        return confidence_map.get(confidence, 0.5)
    
    def _calculate_priority_score(self, combined_edge: float, final_confidence: float,
                                ai_result: AIAnalysisResult, opportunity) -> float:
        """Calculate final priority score"""
        
        score = 0.0
        
        # Edge contribution (0-50 points)
        score += min(combined_edge * 10, 50)
        
        # Confidence contribution (0-30 points)
        score += final_confidence * 30
        
        # AI assessment bonus (0-20 points)
        assessment_bonus = {
            'strong_value': 20,
            'moderate_value': 10,
            'no_value': 0
        }
        score += assessment_bonus.get(ai_result.value_assessment, 0)
        
        # League tier bonus (0-15 points)
        tier = self._get_league_tier(opportunity.league)
        tier_bonus = {1: 15, 2: 10, 3: 5}
        score += tier_bonus.get(tier, 0)
        
        # Risk penalty (0 to -20 points)
        risk_penalty = min(len(ai_result.risk_factors) * 5, 20)
        score -= risk_penalty
        
        # Time sensitivity bonus (0-10 points)
        time_to_match = (opportunity.commence_time - datetime.now()).total_seconds() / 3600
        if time_to_match < 2:
            score += 10
        elif time_to_match < 6:
            score += 5
        
        return max(0, score)
    
    def _calculate_openai_savings(self, ai_result: AIAnalysisResult) -> float:
        """Calculate savings vs OpenAI for this analysis"""
        
        tokens = ai_result.tokens_used
        cost_info = self.config.calculate_cost_savings(
            tokens.get('input', 0),
            tokens.get('output', 0)
        )
        
        return cost_info['savings']
    
    def _fallback_analysis(self, opportunities: List) -> List[EnhancedOpportunity]:
        """Fallback analysis when AI is unavailable"""
        
        logger.warning("Using fallback analysis (AI unavailable)")
        
        fallback_opportunities = []
        for opportunity in opportunities:
            fallback = self._create_fallback_opportunity(opportunity)
            fallback_opportunities.append(fallback)
        
        return fallback_opportunities
    
    def _create_fallback_opportunity(self, opportunity) -> EnhancedOpportunity:
        """Create enhanced opportunity without AI analysis"""
        
        # Use original edge estimate
        original_edge = getattr(opportunity, 'edge_estimate', 0)
        original_confidence = self._confidence_to_score(getattr(opportunity, 'confidence', 'Medium'))
        
        # Simple priority calculation
        priority_score = original_edge * 10 + original_confidence * 20
        
        return EnhancedOpportunity(
            match_id=opportunity.match_id,
            team=opportunity.team,
            opponent=opportunity.opponent,
            odds=opportunity.odds,
            league=opportunity.league,
            commence_time=opportunity.commence_time,
            ai_edge_estimate=0.0,
            ai_confidence_score=0.0,
            ai_risk_factors=["AI analysis unavailable"],
            ai_value_assessment="fallback",
            ai_reasoning="Fallback analysis used",
            ai_recommended_action="monitor",
            combined_edge=original_edge,
            final_confidence=original_confidence,
            priority_score=priority_score,
            analysis_cost=0.0,
            cost_savings_vs_openai=0.0
        )
    
    async def analyze_historical_patterns(self) -> Optional[Dict]:
        """Analyze historical patterns for system optimization"""
        
        try:
            # Get recent opportunities (if database available)
            if self.database:
                opportunities = self.database.get_recent_opportunities(hours=168 * 4)  # 4 weeks
            else:
                opportunities = []
            
            if len(opportunities) < 10:
                logger.warning("Insufficient data for pattern analysis")
                return None
            
            # Prepare data for AI analysis
            historical_data = []
            for opp in opportunities[-20:]:  # Last 20 opportunities
                historical_data.append({
                    'league': opp.league,
                    'odds': opp.odds,
                    'edge_estimate': opp.edge_estimate,
                    'urgency_level': opp.urgency_level,
                    'detected_time': opp.detected_time.isoformat(),
                    'commence_time': opp.commence_time.isoformat()
                })
            
            async with self.ai_client as client:
                pattern_insights = await client.analyze_pattern(historical_data)
                
                if pattern_insights:
                    logger.info("Historical pattern analysis completed")
                    return pattern_insights
                else:
                    logger.warning("Pattern analysis failed")
                    return None
        
        except Exception as e:
            logger.error(f"Historical pattern analysis failed: {e}")
            return None
    
    def get_analysis_stats(self) -> Dict:
        """Get analysis performance statistics"""
        
        cost_summary = {}
        if hasattr(self.ai_client, 'get_cost_summary'):
            try:
                cost_summary = self.ai_client.get_cost_summary()
            except:
                pass
        
        return {
            'total_analyses': self.total_analyses,
            'cache_hits': self.cache_hits,
            'cache_hit_rate': self.cache_hits / max(self.total_analyses, 1),
            'ai_enhanced_opportunities': self.ai_enhanced_opportunities,
            'cached_analyses': len(self.analysis_cache),
            'cost_summary': cost_summary
        }
    
    def clear_cache(self):
        """Clear analysis cache"""
        self.analysis_cache.clear()
        logger.info("Analysis cache cleared")
