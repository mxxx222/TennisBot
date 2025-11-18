"""
Quality Validator for High-Stakes Opportunities
Uses OpenAI premium analysis for critical betting decisions
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from ai_analysis.hybrid_router import HybridAIRouter, HybridAnalysisResult
from ai_analysis.openai_client import OpenAIClient

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result from quality validation"""
    is_validated: bool
    validation_score: float  # 0-100
    risk_assessment: str  # 'low', 'medium', 'high', 'critical'
    recommended_action: str
    stake_adjustment: float  # Multiplier for original stake
    confidence_level: str
    validation_reasoning: str
    cost: float

@dataclass
class QualityMetrics:
    """Quality metrics for validation"""
    edge_consistency: float  # How consistent is the edge estimate
    confidence_alignment: float  # How well do confidence scores align
    risk_factor_severity: float  # Severity of identified risks
    market_efficiency_score: float  # Market efficiency assessment
    timing_sensitivity: float  # How time-sensitive is this opportunity

class QualityValidator:
    """Validates high-stakes opportunities with premium analysis"""
    
    def __init__(self):
        self.hybrid_router = HybridAIRouter()
        
        # Validation thresholds
        self.high_stakes_threshold = 15.0  # $15+ stakes need validation
        self.high_edge_threshold = 4.0  # 4%+ edge needs validation
        self.critical_confidence_threshold = 0.8  # 80%+ confidence needs validation
        
        # Quality scoring weights
        self.edge_weight = 0.3
        self.confidence_weight = 0.25
        self.risk_weight = 0.25
        self.market_weight = 0.2
        
        # Performance tracking
        self.validations_performed = 0
        self.validations_passed = 0
        self.total_validation_cost = 0.0
        
    async def validate_opportunity(self, opportunity_data: Dict, 
                                 preliminary_analysis: Dict = None) -> ValidationResult:
        """Validate a high-stakes opportunity with premium analysis"""
        
        try:
            # Check if validation is needed
            if not self._needs_validation(opportunity_data, preliminary_analysis):
                return ValidationResult(
                    is_validated=False,
                    validation_score=0.0,
                    risk_assessment='low',
                    recommended_action='proceed_standard',
                    stake_adjustment=1.0,
                    confidence_level='standard',
                    validation_reasoning='No validation required for this opportunity',
                    cost=0.0
                )
            
            logger.info(f"Validating high-stakes opportunity: {opportunity_data.get('home_team')} vs {opportunity_data.get('away_team')}")
            
            # Perform hybrid analysis with premium routing
            hybrid_result = await self.hybrid_router.analyze_opportunity(
                opportunity_data, 
                self._prepare_validation_context(preliminary_analysis)
            )
            
            if not hybrid_result:
                return self._create_failed_validation()
            
            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(hybrid_result, preliminary_analysis)
            
            # Generate validation result
            validation = self._generate_validation_result(hybrid_result, quality_metrics)
            
            # Update tracking
            self.validations_performed += 1
            if validation.validation_score >= 70:
                self.validations_passed += 1
            self.total_validation_cost += validation.cost
            
            logger.info(f"Validation completed: Score {validation.validation_score:.1f}, "
                       f"Action: {validation.recommended_action}, "
                       f"Cost: ${validation.cost:.4f}")
            
            return validation
            
        except Exception as e:
            logger.error(f"Quality validation failed: {e}")
            return self._create_failed_validation()
    
    def _needs_validation(self, opportunity_data: Dict, preliminary_analysis: Dict = None) -> bool:
        """Determine if opportunity needs premium validation"""
        
        # Check stake threshold
        stake = opportunity_data.get('stake', 0)
        if stake >= self.high_stakes_threshold:
            return True
        
        # Check edge threshold
        edge = opportunity_data.get('current_edge', 0)
        if preliminary_analysis:
            edge = max(edge, preliminary_analysis.get('edge_estimate', 0))
        
        if edge >= self.high_edge_threshold:
            return True
        
        # Check confidence level
        if preliminary_analysis:
            confidence = preliminary_analysis.get('confidence_score', 0)
            if confidence >= self.critical_confidence_threshold:
                return True
        
        # Check urgency (time to match)
        commence_time = opportunity_data.get('commence_time')
        if commence_time:
            if isinstance(commence_time, str):
                commence_time = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
            
            hours_until = (commence_time - datetime.now()).total_seconds() / 3600
            if hours_until < 1.0:  # Less than 1 hour
                return True
        
        return False
    
    def _prepare_validation_context(self, preliminary_analysis: Dict = None) -> str:
        """Prepare context for validation analysis"""
        
        if not preliminary_analysis:
            return "No preliminary analysis available"
        
        context = f"""PRELIMINARY ANALYSIS CONTEXT:
- Initial Edge Estimate: {preliminary_analysis.get('edge_estimate', 0):.1f}%
- Initial Confidence: {preliminary_analysis.get('confidence_score', 0):.1%}
- Risk Factors: {', '.join(preliminary_analysis.get('risk_factors', []))}
- Value Assessment: {preliminary_analysis.get('value_assessment', 'unknown')}
- Recommended Action: {preliminary_analysis.get('recommended_action', 'unknown')}

VALIDATION REQUEST:
This is a high-stakes opportunity requiring premium validation. Please provide your most accurate assessment with particular attention to:
1. Risk factor validation and additional risk identification
2. Edge estimate refinement with confidence intervals
3. Market efficiency assessment for this specific match
4. Optimal stake sizing recommendations
5. Timing considerations and market movement risks"""
        
        return context
    
    def _calculate_quality_metrics(self, hybrid_result: HybridAnalysisResult, 
                                 preliminary_analysis: Dict = None) -> QualityMetrics:
        """Calculate quality metrics for validation scoring"""
        
        # Edge consistency (how consistent is the edge estimate)
        edge_consistency = 1.0
        if preliminary_analysis:
            prelim_edge = preliminary_analysis.get('edge_estimate', 0)
            if prelim_edge > 0:
                edge_diff = abs(hybrid_result.edge_estimate - prelim_edge)
                edge_consistency = max(0, 1 - (edge_diff / max(prelim_edge, hybrid_result.edge_estimate)))
        
        # Confidence alignment
        confidence_alignment = hybrid_result.confidence_score
        
        # Risk factor severity (more risk factors = lower score)
        risk_count = len(hybrid_result.risk_factors)
        risk_factor_severity = max(0, 1 - (risk_count * 0.1))
        
        # Market efficiency (based on value assessment)
        market_efficiency_map = {
            'strong_value': 0.9,
            'moderate_value': 0.7,
            'marginal_value': 0.5,
            'no_value': 0.2
        }
        market_efficiency_score = market_efficiency_map.get(hybrid_result.value_assessment, 0.5)
        
        # Timing sensitivity (premium analysis gets bonus)
        timing_sensitivity = 0.8 if hybrid_result.is_premium_analysis else 0.6
        
        return QualityMetrics(
            edge_consistency=edge_consistency,
            confidence_alignment=confidence_alignment,
            risk_factor_severity=risk_factor_severity,
            market_efficiency_score=market_efficiency_score,
            timing_sensitivity=timing_sensitivity
        )
    
    def _generate_validation_result(self, hybrid_result: HybridAnalysisResult,
                                  quality_metrics: QualityMetrics) -> ValidationResult:
        """Generate final validation result"""
        
        # Calculate overall validation score (0-100)
        validation_score = (
            quality_metrics.edge_consistency * self.edge_weight +
            quality_metrics.confidence_alignment * self.confidence_weight +
            quality_metrics.risk_factor_severity * self.risk_weight +
            quality_metrics.market_efficiency_score * self.market_weight
        ) * 100
        
        # Determine risk assessment
        if validation_score >= 85:
            risk_assessment = 'low'
        elif validation_score >= 70:
            risk_assessment = 'medium'
        elif validation_score >= 50:
            risk_assessment = 'high'
        else:
            risk_assessment = 'critical'
        
        # Determine recommended action
        if validation_score >= 80 and hybrid_result.recommended_action == 'bet':
            recommended_action = 'proceed_full'
            stake_adjustment = 1.0
        elif validation_score >= 70 and hybrid_result.recommended_action in ['bet', 'monitor']:
            recommended_action = 'proceed_reduced'
            stake_adjustment = 0.75
        elif validation_score >= 50:
            recommended_action = 'proceed_minimal'
            stake_adjustment = 0.5
        else:
            recommended_action = 'avoid'
            stake_adjustment = 0.0
        
        # Adjust for premium analysis
        if hybrid_result.is_premium_analysis:
            validation_score += 5  # Bonus for premium analysis
            if stake_adjustment > 0:
                stake_adjustment = min(1.0, stake_adjustment + 0.1)
        
        # Determine confidence level
        if validation_score >= 85:
            confidence_level = 'very_high'
        elif validation_score >= 70:
            confidence_level = 'high'
        elif validation_score >= 50:
            confidence_level = 'medium'
        else:
            confidence_level = 'low'
        
        # Create validation reasoning
        validation_reasoning = self._create_validation_reasoning(
            hybrid_result, quality_metrics, validation_score, risk_assessment
        )
        
        return ValidationResult(
            is_validated=True,
            validation_score=min(100, validation_score),
            risk_assessment=risk_assessment,
            recommended_action=recommended_action,
            stake_adjustment=stake_adjustment,
            confidence_level=confidence_level,
            validation_reasoning=validation_reasoning,
            cost=hybrid_result.analysis_cost
        )
    
    def _create_validation_reasoning(self, hybrid_result: HybridAnalysisResult,
                                   quality_metrics: QualityMetrics,
                                   validation_score: float,
                                   risk_assessment: str) -> str:
        """Create detailed validation reasoning"""
        
        reasoning_parts = []
        
        # AI provider and model
        ai_info = f"{hybrid_result.ai_provider.upper()} ({hybrid_result.model_used})"
        if hybrid_result.is_premium_analysis:
            ai_info += " - PREMIUM ANALYSIS"
        reasoning_parts.append(f"Analysis by: {ai_info}")
        
        # Edge assessment
        reasoning_parts.append(f"Edge estimate: {hybrid_result.edge_estimate:.1f}% (Confidence: {hybrid_result.confidence_score:.1%})")
        
        # Quality metrics
        reasoning_parts.append(f"Quality score: {validation_score:.1f}/100")
        reasoning_parts.append(f"Risk assessment: {risk_assessment.upper()}")
        
        # Key factors
        if hybrid_result.risk_factors:
            reasoning_parts.append(f"Risk factors: {', '.join(hybrid_result.risk_factors[:3])}")
        
        # Value assessment
        reasoning_parts.append(f"Value assessment: {hybrid_result.value_assessment.replace('_', ' ').title()}")
        
        # Cost efficiency
        if hybrid_result.cost_savings > 0:
            reasoning_parts.append(f"Cost savings: ${hybrid_result.cost_savings:.4f} vs all-OpenAI")
        
        # Routing reason
        reasoning_parts.append(f"Routing: {hybrid_result.routing_reason}")
        
        return " | ".join(reasoning_parts)
    
    def _create_failed_validation(self) -> ValidationResult:
        """Create result for failed validation"""
        
        return ValidationResult(
            is_validated=False,
            validation_score=0.0,
            risk_assessment='critical',
            recommended_action='avoid',
            stake_adjustment=0.0,
            confidence_level='none',
            validation_reasoning='Validation failed due to technical error',
            cost=0.0
        )
    
    async def validate_batch(self, opportunities: List[Dict]) -> List[Tuple[Dict, ValidationResult]]:
        """Validate multiple opportunities in batch"""
        
        if not opportunities:
            return []
        
        logger.info(f"Starting batch validation of {len(opportunities)} opportunities...")
        
        # Filter opportunities that need validation
        validation_candidates = []
        for opp in opportunities:
            if self._needs_validation(opp):
                validation_candidates.append(opp)
        
        logger.info(f"Validation required for {len(validation_candidates)} out of {len(opportunities)} opportunities")
        
        # Validate candidates concurrently
        validation_tasks = []
        for opp in validation_candidates:
            task = self.validate_opportunity(opp)
            validation_tasks.append((opp, task))
        
        # Execute validations
        results = []
        for opp, task in validation_tasks:
            try:
                validation_result = await task
                results.append((opp, validation_result))
            except Exception as e:
                logger.error(f"Batch validation error for {opp.get('home_team', 'unknown')}: {e}")
                results.append((opp, self._create_failed_validation()))
        
        # Add non-validated opportunities with default result
        for opp in opportunities:
            if not any(opp is candidate for candidate in validation_candidates):
                default_validation = ValidationResult(
                    is_validated=False,
                    validation_score=60.0,  # Default score for standard opportunities
                    risk_assessment='medium',
                    recommended_action='proceed_standard',
                    stake_adjustment=1.0,
                    confidence_level='standard',
                    validation_reasoning='Standard opportunity, no validation required',
                    cost=0.0
                )
                results.append((opp, default_validation))
        
        logger.info(f"Batch validation completed: {len(results)} results")
        
        return results
    
    def get_validation_stats(self) -> Dict:
        """Get validation performance statistics"""
        
        success_rate = self.validations_passed / max(self.validations_performed, 1)
        avg_cost = self.total_validation_cost / max(self.validations_performed, 1)
        
        return {
            'validations_performed': self.validations_performed,
            'validations_passed': self.validations_passed,
            'success_rate': round(success_rate, 3),
            'total_cost': round(self.total_validation_cost, 4),
            'avg_cost_per_validation': round(avg_cost, 4),
            'thresholds': {
                'high_stakes': self.high_stakes_threshold,
                'high_edge': self.high_edge_threshold,
                'critical_confidence': self.critical_confidence_threshold
            },
            'hybrid_router_stats': self.hybrid_router.get_routing_stats()
        }
