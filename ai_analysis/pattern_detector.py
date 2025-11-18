"""
AI-Powered Pattern Detection for Historical Analysis
Uses Venice AI to identify profitable patterns and optimize strategy
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import statistics

from ai_analysis.venice_client import VeniceAIClient

logger = logging.getLogger(__name__)

@dataclass
class PatternInsight:
    """Insight from pattern analysis"""
    pattern_type: str
    description: str
    profitability_score: float
    confidence: float
    sample_size: int
    recommendation: str
    supporting_data: Dict

@dataclass
class OptimizationRecommendation:
    """Optimization recommendation from AI analysis"""
    category: str  # 'league', 'timing', 'odds_range', 'stake_sizing'
    current_performance: float
    recommended_change: str
    expected_improvement: float
    implementation_priority: str  # 'high', 'medium', 'low'
    reasoning: str

class AIPatternDetector:
    """AI-powered pattern detection and optimization"""
    
    def __init__(self, database = None):
        self.database = database
        self.ai_client = VeniceAIClient()
        
        # Pattern cache
        self.pattern_cache: Dict[str, List[PatternInsight]] = {}
        self.cache_expiry = 86400  # 24 hours
        
        # Analysis tracking
        self.total_pattern_analyses = 0
        self.optimization_recommendations = []
        
    async def detect_profitable_patterns(self, days: int = 30) -> List[PatternInsight]:
        """Detect profitable patterns in historical data"""
        
        cache_key = f"patterns_{days}d"
        
        # Check cache
        if cache_key in self.pattern_cache:
            cached_time = getattr(self.pattern_cache[cache_key], 'timestamp', datetime.now())
            if (datetime.now() - cached_time).total_seconds() < self.cache_expiry:
                logger.info("Using cached pattern analysis")
                return self.pattern_cache[cache_key]
        
        logger.info(f"Analyzing patterns from last {days} days...")
        
        try:
            # Get historical data (if database available)
            if self.database:
                opportunities = self.database.get_recent_opportunities(days * 24)
                performance_summary = self.database.get_performance_summary(days)
            else:
                opportunities = []
                performance_summary = {}
            
            if len(opportunities) < 20:
                logger.warning("Insufficient data for pattern analysis")
                return []
            
            # Analyze different pattern types
            patterns = []
            
            async with self.ai_client as client:
                # League patterns
                league_patterns = await self._analyze_league_patterns(client, opportunities)
                patterns.extend(league_patterns)
                
                # Timing patterns
                timing_patterns = await self._analyze_timing_patterns(client, opportunities)
                patterns.extend(timing_patterns)
                
                # Odds range patterns
                odds_patterns = await self._analyze_odds_patterns(client, opportunities)
                patterns.extend(odds_patterns)
                
                # Movement patterns
                movement_patterns = await self._analyze_movement_patterns(client, opportunities)
                patterns.extend(movement_patterns)
            
            # Cache results
            for pattern in patterns:
                pattern.timestamp = datetime.now()
            self.pattern_cache[cache_key] = patterns
            
            self.total_pattern_analyses += 1
            logger.info(f"Pattern analysis completed: {len(patterns)} patterns identified")
            
            return patterns
            
        except Exception as e:
            logger.error(f"Pattern detection failed: {e}")
            return []
    
    async def _analyze_league_patterns(self, client: VeniceAIClient, 
                                     opportunities: List) -> List[PatternInsight]:
        """Analyze patterns by league"""
        
        try:
            # Group by league
            league_data = {}
            for opp in opportunities:
                league = opp.league
                if league not in league_data:
                    league_data[league] = []
                league_data[league].append({
                    'odds': opp.odds,
                    'edge_estimate': opp.edge_estimate,
                    'urgency_level': opp.urgency_level,
                    'detected_time': opp.detected_time.isoformat()
                })
            
            # Prepare AI prompt
            prompt = f"""Analyze league-specific patterns in soccer betting data:

League Performance Data:
{json.dumps({k: v[:5] for k, v in league_data.items()}, indent=2)}

For each league, identify:
1. Average profitability patterns
2. Optimal odds ranges
3. Best timing windows
4. Risk factors specific to that league

Return analysis as JSON array of patterns with:
- pattern_type: "league_specific"
- league: league name
- profitability_score: 0-100
- confidence: 0-1
- key_insights: [list of insights]
- recommendations: specific actions"""

            response = await client._make_api_request([
                {"role": "system", "content": "You are a sports betting pattern analyst specializing in league-specific inefficiencies."},
                {"role": "user", "content": prompt}
            ])
            
            if response:
                content = response['choices'][0]['message']['content']
                try:
                    patterns_data = json.loads(content)
                    return self._parse_league_patterns(patterns_data, league_data)
                except json.JSONDecodeError:
                    return self._extract_league_patterns_from_text(content, league_data)
            
            return []
            
        except Exception as e:
            logger.error(f"League pattern analysis failed: {e}")
            return []
    
    async def _analyze_timing_patterns(self, client: VeniceAIClient,
                                     opportunities: List) -> List[PatternInsight]:
        """Analyze timing-based patterns"""
        
        try:
            # Group by time factors
            hourly_data = {}
            daily_data = {}
            
            for opp in opportunities:
                hour = opp.detected_time.hour
                day = opp.detected_time.strftime('%A')
                
                if hour not in hourly_data:
                    hourly_data[hour] = []
                if day not in daily_data:
                    daily_data[day] = []
                
                opp_data = {
                    'edge_estimate': opp.edge_estimate,
                    'urgency_level': opp.urgency_level,
                    'odds': opp.odds
                }
                
                hourly_data[hour].append(opp_data)
                daily_data[day].append(opp_data)
            
            # Calculate timing statistics
            timing_stats = {
                'hourly_performance': {},
                'daily_performance': {}
            }
            
            for hour, opps in hourly_data.items():
                if len(opps) >= 3:  # Minimum sample size
                    avg_edge = statistics.mean([o['edge_estimate'] for o in opps])
                    timing_stats['hourly_performance'][hour] = {
                        'avg_edge': avg_edge,
                        'count': len(opps),
                        'high_urgency_pct': len([o for o in opps if o['urgency_level'] in ['HIGH', 'CRITICAL']]) / len(opps)
                    }
            
            for day, opps in daily_data.items():
                if len(opps) >= 3:
                    avg_edge = statistics.mean([o['edge_estimate'] for o in opps])
                    timing_stats['daily_performance'][day] = {
                        'avg_edge': avg_edge,
                        'count': len(opps),
                        'high_urgency_pct': len([o for o in opps if o['urgency_level'] in ['HIGH', 'CRITICAL']]) / len(opps)
                    }
            
            # AI analysis of timing patterns
            prompt = f"""Analyze timing patterns in betting opportunities:

Timing Performance Data:
{json.dumps(timing_stats, indent=2)}

Identify:
1. Most profitable hours of day
2. Best days of week for opportunities
3. Seasonal or temporal trends
4. Optimal monitoring schedules

Return insights about when to focus monitoring efforts for maximum ROI."""

            response = await client._make_api_request([
                {"role": "system", "content": "You are a temporal pattern analyst for sports betting optimization."},
                {"role": "user", "content": prompt}
            ])
            
            if response:
                content = response['choices'][0]['message']['content']
                return self._parse_timing_patterns(content, timing_stats)
            
            return []
            
        except Exception as e:
            logger.error(f"Timing pattern analysis failed: {e}")
            return []
    
    async def _analyze_odds_patterns(self, client: VeniceAIClient,
                                   opportunities: List) -> List[PatternInsight]:
        """Analyze odds range patterns"""
        
        try:
            # Group by odds ranges
            odds_ranges = {
                '1.30-1.40': [],
                '1.41-1.50': [],
                '1.51-1.60': [],
                '1.61-1.70': [],
                '1.71-1.80': []
            }
            
            for opp in opportunities:
                odds = opp.odds
                if 1.30 <= odds <= 1.40:
                    odds_ranges['1.30-1.40'].append(opp)
                elif 1.41 <= odds <= 1.50:
                    odds_ranges['1.41-1.50'].append(opp)
                elif 1.51 <= odds <= 1.60:
                    odds_ranges['1.51-1.60'].append(opp)
                elif 1.61 <= odds <= 1.70:
                    odds_ranges['1.61-1.70'].append(opp)
                elif 1.71 <= odds <= 1.80:
                    odds_ranges['1.71-1.80'].append(opp)
            
            # Calculate performance by odds range
            range_performance = {}
            for range_name, opps in odds_ranges.items():
                if len(opps) >= 5:  # Minimum sample size
                    avg_edge = statistics.mean([o.edge_estimate for o in opps])
                    high_confidence_pct = len([o for o in opps if o.urgency_level in ['HIGH', 'CRITICAL']]) / len(opps)
                    
                    range_performance[range_name] = {
                        'avg_edge': avg_edge,
                        'count': len(opps),
                        'high_confidence_pct': high_confidence_pct,
                        'avg_odds': statistics.mean([o.odds for o in opps])
                    }
            
            # AI analysis
            prompt = f"""Analyze odds range performance patterns:

Odds Range Performance:
{json.dumps(range_performance, indent=2)}

Determine:
1. Most profitable odds ranges
2. Sweet spots for maximum edge
3. Risk-adjusted returns by range
4. Optimal filtering thresholds

Provide recommendations for odds range optimization."""

            response = await client._make_api_request([
                {"role": "system", "content": "You are an odds analysis specialist for value betting optimization."},
                {"role": "user", "content": prompt}
            ])
            
            if response:
                content = response['choices'][0]['message']['content']
                return self._parse_odds_patterns(content, range_performance)
            
            return []
            
        except Exception as e:
            logger.error(f"Odds pattern analysis failed: {e}")
            return []
    
    async def _analyze_movement_patterns(self, client: VeniceAIClient,
                                       opportunities: List) -> List[PatternInsight]:
        """Analyze odds movement patterns"""
        
        try:
            # Analyze movement directions
            movement_data = {
                'entering': [],
                'stable': [],
                'exiting': []
            }
            
            for opp in opportunities:
                movement = getattr(opp, 'movement_direction', 'stable')
                if movement in movement_data:
                    movement_data[movement].append({
                        'edge_estimate': opp.edge_estimate,
                        'urgency_level': opp.urgency_level,
                        'odds': opp.odds,
                        'league': opp.league
                    })
            
            # Calculate movement statistics
            movement_stats = {}
            for movement_type, opps in movement_data.items():
                if len(opps) >= 3:
                    avg_edge = statistics.mean([o['edge_estimate'] for o in opps])
                    movement_stats[movement_type] = {
                        'avg_edge': avg_edge,
                        'count': len(opps),
                        'high_urgency_pct': len([o for o in opps if o['urgency_level'] in ['HIGH', 'CRITICAL']]) / len(opps)
                    }
            
            # AI analysis
            prompt = f"""Analyze odds movement patterns for betting optimization:

Movement Pattern Data:
{json.dumps(movement_stats, indent=2)}

Analyze:
1. Most profitable movement types
2. Timing of entries vs movements
3. Risk factors by movement pattern
4. Optimal response strategies

Provide actionable insights for movement-based betting decisions."""

            response = await client._make_api_request([
                {"role": "system", "content": "You are an odds movement specialist for sports betting."},
                {"role": "user", "content": prompt}
            ])
            
            if response:
                content = response['choices'][0]['message']['content']
                return self._parse_movement_patterns(content, movement_stats)
            
            return []
            
        except Exception as e:
            logger.error(f"Movement pattern analysis failed: {e}")
            return []
    
    def _parse_league_patterns(self, patterns_data: List[Dict], 
                             league_data: Dict) -> List[PatternInsight]:
        """Parse league patterns from AI response"""
        
        insights = []
        
        try:
            for pattern in patterns_data:
                if isinstance(pattern, dict):
                    league = pattern.get('league', 'Unknown')
                    sample_size = len(league_data.get(league, []))
                    
                    insight = PatternInsight(
                        pattern_type="league_specific",
                        description=f"League performance pattern for {league}",
                        profitability_score=float(pattern.get('profitability_score', 0)),
                        confidence=float(pattern.get('confidence', 0.5)),
                        sample_size=sample_size,
                        recommendation=pattern.get('recommendations', 'Monitor performance'),
                        supporting_data={'league': league, 'insights': pattern.get('key_insights', [])}
                    )
                    insights.append(insight)
        
        except Exception as e:
            logger.error(f"Failed to parse league patterns: {e}")
        
        return insights
    
    def _parse_timing_patterns(self, content: str, timing_stats: Dict) -> List[PatternInsight]:
        """Parse timing patterns from AI response"""
        
        insights = []
        
        # Extract key insights from text
        if 'hour' in content.lower():
            insight = PatternInsight(
                pattern_type="timing_hourly",
                description="Hourly performance patterns identified",
                profitability_score=75.0,  # Default score
                confidence=0.7,
                sample_size=len(timing_stats.get('hourly_performance', {})),
                recommendation=content[:200] + "..." if len(content) > 200 else content,
                supporting_data=timing_stats
            )
            insights.append(insight)
        
        if 'day' in content.lower():
            insight = PatternInsight(
                pattern_type="timing_daily",
                description="Daily performance patterns identified",
                profitability_score=70.0,
                confidence=0.6,
                sample_size=len(timing_stats.get('daily_performance', {})),
                recommendation=content[:200] + "..." if len(content) > 200 else content,
                supporting_data=timing_stats
            )
            insights.append(insight)
        
        return insights
    
    def _parse_odds_patterns(self, content: str, range_performance: Dict) -> List[PatternInsight]:
        """Parse odds patterns from AI response"""
        
        insights = []
        
        # Find best performing range
        best_range = None
        best_score = 0
        
        for range_name, data in range_performance.items():
            score = data['avg_edge'] * data['high_confidence_pct']
            if score > best_score:
                best_score = score
                best_range = range_name
        
        if best_range:
            insight = PatternInsight(
                pattern_type="odds_range_optimal",
                description=f"Optimal odds range identified: {best_range}",
                profitability_score=best_score * 100,
                confidence=0.8,
                sample_size=range_performance[best_range]['count'],
                recommendation=f"Focus on {best_range} odds range for maximum edge",
                supporting_data={'best_range': best_range, 'performance': range_performance}
            )
            insights.append(insight)
        
        return insights
    
    def _parse_movement_patterns(self, content: str, movement_stats: Dict) -> List[PatternInsight]:
        """Parse movement patterns from AI response"""
        
        insights = []
        
        # Find best movement type
        best_movement = None
        best_score = 0
        
        for movement_type, data in movement_stats.items():
            score = data['avg_edge'] * data['high_urgency_pct']
            if score > best_score:
                best_score = score
                best_movement = movement_type
        
        if best_movement:
            insight = PatternInsight(
                pattern_type="movement_optimal",
                description=f"Optimal movement pattern: {best_movement}",
                profitability_score=best_score * 100,
                confidence=0.7,
                sample_size=movement_stats[best_movement]['count'],
                recommendation=f"Prioritize {best_movement} movement opportunities",
                supporting_data={'best_movement': best_movement, 'stats': movement_stats}
            )
            insights.append(insight)
        
        return insights
    
    def _extract_league_patterns_from_text(self, content: str, 
                                         league_data: Dict) -> List[PatternInsight]:
        """Extract patterns from text when JSON parsing fails"""
        
        insights = []
        
        # Simple text-based extraction
        for league in league_data.keys():
            if league.lower() in content.lower():
                insight = PatternInsight(
                    pattern_type="league_mention",
                    description=f"Pattern mentioned for {league}",
                    profitability_score=50.0,  # Default
                    confidence=0.5,
                    sample_size=len(league_data[league]),
                    recommendation=f"Review {league} performance",
                    supporting_data={'league': league, 'content_snippet': content[:100]}
                )
                insights.append(insight)
        
        return insights
    
    async def generate_optimization_recommendations(self, 
                                                 patterns: List[PatternInsight]) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on patterns"""
        
        recommendations = []
        
        try:
            # Analyze patterns for optimization opportunities
            for pattern in patterns:
                if pattern.profitability_score > 70 and pattern.confidence > 0.6:
                    
                    if pattern.pattern_type == "league_specific":
                        rec = OptimizationRecommendation(
                            category="league",
                            current_performance=pattern.profitability_score,
                            recommended_change=f"Increase focus on {pattern.supporting_data.get('league', 'this league')}",
                            expected_improvement=10.0,
                            implementation_priority="high",
                            reasoning=pattern.recommendation
                        )
                        recommendations.append(rec)
                    
                    elif pattern.pattern_type == "odds_range_optimal":
                        best_range = pattern.supporting_data.get('best_range', '')
                        rec = OptimizationRecommendation(
                            category="odds_range",
                            current_performance=pattern.profitability_score,
                            recommended_change=f"Narrow focus to {best_range} odds range",
                            expected_improvement=15.0,
                            implementation_priority="high",
                            reasoning=f"This range shows {pattern.profitability_score:.1f}% profitability score"
                        )
                        recommendations.append(rec)
                    
                    elif pattern.pattern_type in ["timing_hourly", "timing_daily"]:
                        rec = OptimizationRecommendation(
                            category="timing",
                            current_performance=pattern.profitability_score,
                            recommended_change="Optimize monitoring schedule based on timing patterns",
                            expected_improvement=8.0,
                            implementation_priority="medium",
                            reasoning=pattern.recommendation
                        )
                        recommendations.append(rec)
            
            self.optimization_recommendations = recommendations
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate optimization recommendations: {e}")
            return []
    
    def get_pattern_summary(self) -> Dict:
        """Get summary of pattern analysis"""
        
        return {
            'total_pattern_analyses': self.total_pattern_analyses,
            'cached_patterns': len(self.pattern_cache),
            'optimization_recommendations': len(self.optimization_recommendations),
            'last_analysis': datetime.now().isoformat()
        }
