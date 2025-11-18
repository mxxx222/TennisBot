"""
Value detection system for live odds monitoring
Identifies when odds enter/exit profitable ranges and calculates urgency levels
Enhanced with Venice AI for 90% cost savings vs OpenAI
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math

from config.live_config import LiveMonitoringConfig
from monitors.odds_tracker import OddsSnapshot, OddsMovement
from utils.bet_calculator import BetCalculator

logger = logging.getLogger(__name__)

# AI Enhancement imports
try:
    from ai_analysis.match_analyzer import AIMatchAnalyzer, EnhancedOpportunity
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    logger.warning("AI analysis not available - running in basic mode")

@dataclass
class ValueOpportunity:
    """Represents a detected value betting opportunity"""
    match_id: str
    team: str
    opponent: str
    odds: float
    previous_odds: Optional[float]
    league: str
    commence_time: datetime
    detected_time: datetime
    
    # Value metrics
    recommended_stake: float
    confidence: str
    edge_estimate: float
    kelly_fraction: float
    
    # Urgency and priority
    urgency_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    priority_score: float
    time_sensitivity: float  # How quickly this opportunity might disappear
    
    # Movement context
    movement_direction: str  # 'entering', 'stable', 'exiting'
    odds_velocity: float  # Rate of odds change
    
    # AI Enhancement fields (optional)
    ai_enhanced: bool = False
    ai_reasoning: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_cost: Optional[float] = None
    
    def __post_init__(self):
        if isinstance(self.commence_time, str):
            self.commence_time = datetime.fromisoformat(self.commence_time.replace('Z', '+00:00'))
        if isinstance(self.detected_time, str):
            self.detected_time = datetime.fromisoformat(self.detected_time.replace('Z', '+00:00'))

class ValueDetector:
    """Detects and analyzes value betting opportunities in real-time"""
    
    def __init__(self, bankroll: float = None):
        self.config = LiveMonitoringConfig()
        self.bet_calculator = BetCalculator(bankroll)
        
        # AI Enhancement
        if AI_AVAILABLE:
            self.ai_analyzer = AIMatchAnalyzer()
            logger.info("AI-enhanced value detection initialized (Venice AI)")
        else:
            self.ai_analyzer = None
            logger.info("Basic value detection initialized (no AI)")
        
        # Tracking for opportunity analysis
        self.active_opportunities: Dict[str, ValueOpportunity] = {}
        self.opportunity_history: List[ValueOpportunity] = []
        
        # Performance tracking
        self.detection_count = 0
        self.false_positive_count = 0
        self.ai_enhancement_count = 0
        
    async def analyze_snapshots(self, snapshots: List[OddsSnapshot], 
                               movements: List[OddsMovement]) -> List[ValueOpportunity]:
        """Analyze odds snapshots and movements to detect value opportunities"""
        
        opportunities = []
        current_time = datetime.now()
        
        for snapshot in snapshots:
            # Check home team opportunity
            home_opportunity = self._evaluate_opportunity(
                snapshot, 'home', snapshot.home_odds, movements, current_time
            )
            if home_opportunity:
                opportunities.append(home_opportunity)
            
            # Check away team opportunity  
            away_opportunity = self._evaluate_opportunity(
                snapshot, 'away', snapshot.away_odds, movements, current_time
            )
            if away_opportunity:
                opportunities.append(away_opportunity)
        
        # Update active opportunities tracking
        self._update_active_opportunities(opportunities)
        
        # AI Enhancement: Analyze with Venice AI if available
        if self.ai_analyzer and opportunities:
            try:
                logger.info(f"Enhancing {len(opportunities)} opportunities with Venice AI...")
                enhanced_opportunities = await self.ai_analyzer.analyze_opportunities(opportunities)
                
                if enhanced_opportunities:
                    # Convert enhanced opportunities back to ValueOpportunity format
                    ai_enhanced = []
                    for enhanced in enhanced_opportunities:
                        # Find original opportunity to preserve data
                        original = next((opp for opp in opportunities if opp.match_id == enhanced.match_id), None)
                        if original:
                            # Update original with AI insights
                            original.ai_enhanced = True
                            original.ai_reasoning = enhanced.ai_reasoning
                            original.ai_confidence = enhanced.ai_confidence_score
                            original.ai_cost = enhanced.analysis_cost
                            
                            # Update edge and confidence with AI insights
                            original.edge_estimate = enhanced.combined_edge
                            original.confidence = self._confidence_from_score(enhanced.final_confidence)
                            original.urgency_level = self._urgency_from_priority(enhanced.priority_score)
                            original.priority_score = enhanced.priority_score
                            
                            # Recalculate stake with new edge
                            original.recommended_stake = self.bet_calculator.calculate_stake(original.odds, enhanced.combined_edge)[0]
                            
                            ai_enhanced.append(original)
                    
                    self.ai_enhancement_count += len(ai_enhanced)
                    logger.info(f"AI enhancement completed: {len(ai_enhanced)} opportunities analyzed")
                    return sorted(ai_enhanced, key=lambda x: x.priority_score, reverse=True)
            
            except Exception as e:
                logger.error(f"AI enhancement failed: {e}")
                # Continue with original opportunities
        
        return opportunities
    
    def _evaluate_opportunity(self, snapshot: OddsSnapshot, side: str, odds: float,
                            movements: List[OddsMovement], current_time: datetime) -> Optional[ValueOpportunity]:
        """Evaluate if a specific odds represents a value opportunity"""
        
        # Check if odds are in profitable range
        if not (self.config.MIN_ODDS <= odds <= self.config.MAX_ODDS):
            return None
        
        # Calculate bet sizing and edge
        stake, confidence, edge = self.bet_calculator.calculate_stake(odds)
        if stake <= 0:
            return None
        
        # Get team names
        if side == 'home':
            team = snapshot.home_team
            opponent = snapshot.away_team
        else:
            team = snapshot.away_team
            opponent = snapshot.home_team
        
        # Find relevant movement for this team
        relevant_movement = self._find_relevant_movement(
            snapshot.match_id, team, movements
        )
        
        # Calculate Kelly fraction
        true_prob = self.bet_calculator.estimate_true_probability(odds)
        kelly_fraction = self.bet_calculator.calculate_kelly_fraction(odds, true_prob)
        
        # Determine urgency and priority
        urgency_level = self._calculate_urgency(
            odds, edge, snapshot.league, snapshot.commence_time, relevant_movement
        )
        
        priority_score = self._calculate_priority_score(
            odds, edge, snapshot.league, urgency_level, relevant_movement
        )
        
        # Calculate time sensitivity
        time_sensitivity = self._calculate_time_sensitivity(
            snapshot.commence_time, relevant_movement, snapshot.league
        )
        
        # Determine movement context
        movement_direction, odds_velocity = self._analyze_movement_context(relevant_movement)
        
        # Get previous odds if available
        previous_odds = relevant_movement.old_odds if relevant_movement else None
        
        opportunity = ValueOpportunity(
            match_id=f"{snapshot.match_id}_{side}",
            team=team,
            opponent=opponent,
            odds=odds,
            previous_odds=previous_odds,
            league=snapshot.league,
            commence_time=snapshot.commence_time,
            detected_time=current_time,
            recommended_stake=stake,
            confidence=confidence,
            edge_estimate=edge,
            kelly_fraction=kelly_fraction,
            urgency_level=urgency_level,
            priority_score=priority_score,
            time_sensitivity=time_sensitivity,
            movement_direction=movement_direction,
            odds_velocity=odds_velocity
        )
        
        self.detection_count += 1
        return opportunity
    
    def _find_relevant_movement(self, match_id: str, team: str, 
                              movements: List[OddsMovement]) -> Optional[OddsMovement]:
        """Find the most relevant odds movement for this opportunity"""
        
        for movement in movements:
            if movement.match_id == match_id and movement.team == team:
                return movement
        
        return None
    
    def _calculate_urgency(self, odds: float, edge: float, league: str,
                          commence_time: datetime, movement: Optional[OddsMovement]) -> str:
        """Calculate urgency level based on multiple factors"""
        
        urgency_score = 0
        
        # Base urgency from edge
        if edge >= 5.0:
            urgency_score += 3
        elif edge >= 3.0:
            urgency_score += 2
        elif edge >= 1.5:
            urgency_score += 1
        
        # League quality factor
        league_tier = self.config.get_league_tier(league)
        if league_tier == 1:
            urgency_score += 2
        elif league_tier == 2:
            urgency_score += 1
        
        # Movement significance
        if movement:
            if movement.significance == 'CRITICAL':
                urgency_score += 3
            elif movement.significance == 'HIGH':
                urgency_score += 2
            elif movement.significance == 'MEDIUM':
                urgency_score += 1
        
        # Time to match factor
        time_to_match = (commence_time - datetime.now()).total_seconds() / 3600
        if time_to_match < 2:  # Less than 2 hours
            urgency_score += 2
        elif time_to_match < 6:  # Less than 6 hours
            urgency_score += 1
        
        # Odds position in range (closer to boundaries = more urgent)
        range_position = self._calculate_range_position(odds)
        if range_position > 0.8:  # Near boundaries
            urgency_score += 1
        
        # Convert score to urgency level
        if urgency_score >= 7:
            return 'CRITICAL'
        elif urgency_score >= 5:
            return 'HIGH'
        elif urgency_score >= 3:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _calculate_priority_score(self, odds: float, edge: float, league: str,
                                urgency: str, movement: Optional[OddsMovement]) -> float:
        """Calculate numerical priority score for ranking opportunities"""
        
        score = 0.0
        
        # Edge contribution (0-50 points)
        score += min(edge * 10, 50)
        
        # League quality (0-20 points)
        league_tier = self.config.get_league_tier(league)
        if league_tier == 1:
            score += 20
        elif league_tier == 2:
            score += 15
        else:
            score += 10
        
        # Urgency multiplier (1.0-2.0x)
        urgency_multipliers = {
            'CRITICAL': 2.0,
            'HIGH': 1.7,
            'MEDIUM': 1.4,
            'LOW': 1.0
        }
        score *= urgency_multipliers.get(urgency, 1.0)
        
        # Movement bonus (0-15 points)
        if movement:
            if movement.movement_type == 'odds_moved_into_profitable_range':
                score += 15
            elif movement.significance in ['HIGH', 'CRITICAL']:
                score += 10
            elif movement.significance == 'MEDIUM':
                score += 5
        
        # Odds quality bonus (prefer middle of range)
        range_center = (self.config.MIN_ODDS + self.config.MAX_ODDS) / 2
        distance_from_center = abs(odds - range_center)
        max_distance = (self.config.MAX_ODDS - self.config.MIN_ODDS) / 2
        center_score = (1 - distance_from_center / max_distance) * 10
        score += center_score
        
        return round(score, 2)
    
    def _calculate_time_sensitivity(self, commence_time: datetime,
                                  movement: Optional[OddsMovement], league: str) -> float:
        """Calculate how time-sensitive this opportunity is (0-1 scale)"""
        
        sensitivity = 0.5  # Base sensitivity
        
        # Time to match factor
        time_to_match = (commence_time - datetime.now()).total_seconds() / 3600
        if time_to_match < 1:
            sensitivity += 0.4
        elif time_to_match < 3:
            sensitivity += 0.3
        elif time_to_match < 6:
            sensitivity += 0.2
        elif time_to_match < 12:
            sensitivity += 0.1
        
        # Movement velocity factor
        if movement and abs(movement.change) >= self.config.SIGNIFICANT_CHANGE:
            sensitivity += 0.2
        
        # League factor (higher tier = more efficient = faster corrections)
        league_tier = self.config.get_league_tier(league)
        if league_tier == 1:
            sensitivity += 0.2
        elif league_tier == 2:
            sensitivity += 0.1
        
        return min(sensitivity, 1.0)
    
    def _analyze_movement_context(self, movement: Optional[OddsMovement]) -> Tuple[str, float]:
        """Analyze the movement context and velocity"""
        
        if not movement:
            return 'stable', 0.0
        
        # Determine direction
        if movement.movement_type == 'odds_moved_into_profitable_range':
            direction = 'entering'
        elif movement.movement_type == 'odds_moved_out_of_range':
            direction = 'exiting'
        else:
            direction = 'stable'
        
        # Calculate velocity (change per minute)
        # This is simplified - in a real system you'd track time between updates
        velocity = abs(movement.change) * 2  # Assume 30-second updates
        
        return direction, velocity
    
    def _calculate_range_position(self, odds: float) -> float:
        """Calculate position within profitable range (0-1 scale)"""
        
        range_size = self.config.MAX_ODDS - self.config.MIN_ODDS
        position_in_range = (odds - self.config.MIN_ODDS) / range_size
        
        # Distance from center (0 = center, 1 = boundary)
        center_position = 0.5
        distance_from_center = abs(position_in_range - center_position) * 2
        
        return distance_from_center
    
    def _update_active_opportunities(self, new_opportunities: List[ValueOpportunity]):
        """Update tracking of active opportunities"""
        
        # Add new opportunities
        for opp in new_opportunities:
            self.active_opportunities[opp.match_id] = opp
        
        # Remove expired opportunities
        current_time = datetime.now()
        expired_keys = []
        
        for match_id, opp in self.active_opportunities.items():
            # Remove if match has started or opportunity is old
            if (opp.commence_time < current_time or 
                (current_time - opp.detected_time).total_seconds() > 3600):
                expired_keys.append(match_id)
                self.opportunity_history.append(opp)
        
        for key in expired_keys:
            del self.active_opportunities[key]
        
        # Limit history size
        if len(self.opportunity_history) > 1000:
            self.opportunity_history = self.opportunity_history[-500:]
    
    def get_top_opportunities(self, limit: int = 5) -> List[ValueOpportunity]:
        """Get top opportunities ranked by priority score"""
        
        opportunities = list(self.active_opportunities.values())
        opportunities.sort(key=lambda x: x.priority_score, reverse=True)
        
        return opportunities[:limit]
    
    def get_urgent_opportunities(self) -> List[ValueOpportunity]:
        """Get opportunities marked as HIGH or CRITICAL urgency"""
        
        urgent = []
        for opp in self.active_opportunities.values():
            if opp.urgency_level in ['HIGH', 'CRITICAL']:
                urgent.append(opp)
        
        # Sort by urgency and priority
        urgent.sort(key=lambda x: (
            {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}[x.urgency_level],
            x.priority_score
        ), reverse=True)
        
        return urgent
    
    def get_performance_stats(self) -> Dict:
        """Get value detection performance statistics"""
        
        return {
            'total_detections': self.detection_count,
            'active_opportunities': len(self.active_opportunities),
            'historical_opportunities': len(self.opportunity_history),
            'false_positive_rate': self.false_positive_count / max(self.detection_count, 1),
            'avg_priority_score': sum(opp.priority_score for opp in self.active_opportunities.values()) / max(len(self.active_opportunities), 1),
            'urgency_breakdown': self._get_urgency_breakdown()
        }
    
    def _get_urgency_breakdown(self) -> Dict[str, int]:
        """Get breakdown of opportunities by urgency level"""
        
        breakdown = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        
        for opp in self.active_opportunities.values():
            breakdown[opp.urgency_level] += 1
        
        return breakdown
    
    def _confidence_from_score(self, score: float) -> str:
        """Convert AI confidence score to confidence string"""
        if score >= 0.8:
            return 'High'
        elif score >= 0.6:
            return 'Medium'
        else:
            return 'Low'
    
    def _urgency_from_priority(self, priority_score: float) -> str:
        """Convert AI priority score to urgency level"""
        if priority_score >= 80:
            return 'CRITICAL'
        elif priority_score >= 60:
            return 'HIGH'
        elif priority_score >= 40:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def get_ai_enhancement_stats(self) -> Dict:
        """Get AI enhancement statistics"""
        
        if not self.ai_analyzer:
            return {'ai_available': False}
        
        total_opportunities = len(self.opportunity_history) + len(self.active_opportunities)
        ai_enhanced_count = 0
        total_ai_cost = 0.0
        
        for opp in self.opportunity_history + list(self.active_opportunities.values()):
            if getattr(opp, 'ai_enhanced', False):
                ai_enhanced_count += 1
                if getattr(opp, 'ai_cost', 0):
                    total_ai_cost += opp.ai_cost
        
        # Get AI analyzer stats if available
        ai_stats = {}
        if hasattr(self.ai_analyzer, 'get_analysis_stats'):
            try:
                ai_stats = self.ai_analyzer.get_analysis_stats()
            except:
                pass
        
        return {
            'ai_available': True,
            'total_enhancements': self.ai_enhancement_count,
            'enhancement_rate': ai_enhanced_count / max(total_opportunities, 1),
            'total_ai_cost': total_ai_cost,
            'estimated_openai_cost': total_ai_cost * 25,  # Venice is ~25x cheaper
            'cost_savings': total_ai_cost * 24,  # Savings vs OpenAI
            'analyzer_stats': ai_stats
        }
