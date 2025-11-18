"""
Hybrid AI Router for Smart Model Selection
Routes opportunities to Venice AI (90%) or OpenAI (10%) based on criteria
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import os

from ai_analysis.venice_client import VeniceAIClient, AIAnalysisResult
from ai_analysis.openai_client import OpenAIClient, OpenAIAnalysisResult
from ai_analysis.ai_config import VeniceAIConfig

logger = logging.getLogger(__name__)

@dataclass
class HybridAnalysisResult:
    """Combined result from hybrid AI analysis"""
    # Core analysis
    edge_estimate: float
    confidence_score: float
    risk_factors: List[str]
    value_assessment: str
    reasoning: str
    recommended_action: str
    
    # Hybrid metadata
    ai_provider: str  # 'venice' or 'openai'
    model_used: str
    analysis_cost: float
    cost_savings: float  # Savings vs all-OpenAI approach
    analysis_time: float
    
    # Quality indicators
    is_premium_analysis: bool
    routing_reason: str
    confidence_boost: float  # Additional confidence from premium analysis

@dataclass
class RoutingDecision:
    """Decision about which AI to use"""
    use_openai: bool
    reason: str
    priority_score: float
    triggers: List[str]

class HybridAIRouter:
    """Smart router for Venice AI + OpenAI hybrid strategy"""
    
    def __init__(self):
        self.config = VeniceAIConfig()
        
        # Initialize AI clients
        self.venice_client = VeniceAIClient()
        
        # Initialize OpenAI client if API key available
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key and openai_key != 'your_openai_api_key_here':
            self.openai_client = OpenAIClient(openai_key)
            self.openai_available = True
            logger.info("Hybrid AI router initialized: Venice AI + OpenAI")
        else:
            self.openai_client = None
            self.openai_available = False
            logger.warning("OpenAI not available, using Venice AI only")
        
        # Routing criteria
        self.high_edge_threshold = 4.0  # Use OpenAI for >4% edge
        self.high_stake_threshold = 15.0  # Use OpenAI for >$15 stake
        self.critical_time_threshold = 1.0  # Use OpenAI for <1h to match
        
        # Performance tracking
        self.venice_requests = 0
        self.openai_requests = 0
        self.total_cost_savings = 0.0
    
    async def __aenter__(self):
        """Async context manager entry"""
        try:
            # Initialize Venice AI client
            await self.venice_client.__aenter__()
            
            # Initialize OpenAI client if available
            if self.openai_client:
                await self.openai_client.__aenter__()
            
            logger.info("✅ HybridAIRouter initialized successfully")
            return self
        except Exception as e:
            logger.error(f"❌ HybridAIRouter initialization failed: {e}")
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        try:
            # Close Venice AI client
            if hasattr(self.venice_client, '__aexit__'):
                await self.venice_client.__aexit__(exc_type, exc_val, exc_tb)
            
            # Close OpenAI client if available
            if self.openai_client and hasattr(self.openai_client, '__aexit__'):
                await self.openai_client.__aexit__(exc_type, exc_val, exc_tb)
            
            logger.info("✅ HybridAIRouter cleaned up successfully")
        except Exception as e:
            logger.error(f"⚠️ Error during HybridAIRouter cleanup: {e}")
        return False
        
    async def analyze_opportunity(self, match_data: Dict, 
                                historical_context: str = "") -> Optional[HybridAnalysisResult]:
        """Analyze opportunity using hybrid AI routing"""
        
        try:
            # Make routing decision
            routing = self._make_routing_decision(match_data)
            
            if routing.use_openai and self.openai_available:
                # Use OpenAI for premium analysis
                result = await self._analyze_with_openai(match_data, historical_context, routing)
                self.openai_requests += 1
            else:
                # Use Venice AI for standard analysis
                result = await self._analyze_with_venice(match_data, historical_context, routing)
                self.venice_requests += 1
            
            if result:
                # Track cost savings
                self.total_cost_savings += result.cost_savings
                
                logger.info(f"Hybrid analysis completed: {result.ai_provider.upper()} "
                           f"(Edge: {result.edge_estimate:.1f}%, "
                           f"Cost: ${result.analysis_cost:.4f}, "
                           f"Savings: ${result.cost_savings:.4f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Hybrid analysis failed: {e}")
            return None
    
    def _make_routing_decision(self, match_data: Dict) -> RoutingDecision:
        """Decide whether to use Venice AI or OpenAI"""
        
        triggers = []
        priority_score = 0.0
        
        # Check edge threshold
        current_edge = match_data.get('current_edge', 0)
        if current_edge > self.high_edge_threshold:
            triggers.append(f"High edge: {current_edge:.1f}%")
            priority_score += 30.0
        
        # Check stake threshold
        stake = match_data.get('stake', 0)
        if stake > self.high_stake_threshold:
            triggers.append(f"High stake: ${stake:.2f}")
            priority_score += 25.0
        
        # Check time sensitivity
        commence_time = match_data.get('commence_time')
        if commence_time:
            if isinstance(commence_time, str):
                commence_time = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
            
            hours_until = (commence_time - datetime.now()).total_seconds() / 3600
            if hours_until < self.critical_time_threshold:
                triggers.append(f"Critical timing: {hours_until:.1f}h")
                priority_score += 20.0
        
        # Check confidence level
        confidence = match_data.get('confidence', 'Medium')
        if confidence in ['High', 'Critical']:
            triggers.append(f"High confidence: {confidence}")
            priority_score += 15.0
        
        # Check league tier (premium leagues get OpenAI)
        league = match_data.get('league', '').lower()
        if any(tier in league for tier in ['premier', 'bundesliga', 'serie_a', 'ligue_1']):
            triggers.append("Premium league")
            priority_score += 10.0
        
        # Decision logic
        use_openai = len(triggers) > 0 and self.openai_available
        
        if use_openai:
            reason = f"Premium analysis triggered: {', '.join(triggers)}"
        elif not self.openai_available:
            reason = "OpenAI unavailable, using Venice AI"
        else:
            reason = "Standard analysis criteria, using Venice AI"
        
        return RoutingDecision(
            use_openai=use_openai,
            reason=reason,
            priority_score=priority_score,
            triggers=triggers
        )
    
    async def _analyze_with_openai(self, match_data: Dict, historical_context: str,
                                 routing: RoutingDecision) -> Optional[HybridAnalysisResult]:
        """Analyze with OpenAI premium analysis"""
        
        try:
            # Use fast model for time-critical analysis
            use_fast = any('timing' in trigger.lower() for trigger in routing.triggers)
            
            async with self.openai_client as client:
                openai_result = await client.analyze_premium_opportunity(
                    match_data, historical_context, use_fast_model=use_fast
                )
            
            if not openai_result:
                # Fallback to Venice AI
                logger.warning("OpenAI analysis failed, falling back to Venice AI")
                return await self._analyze_with_venice(match_data, historical_context, routing)
            
            # Calculate cost savings vs all-OpenAI approach
            # (This is actual OpenAI cost, so savings = 0)
            cost_savings = 0.0
            
            # Add confidence boost for premium analysis
            confidence_boost = 0.1 if routing.priority_score > 50 else 0.05
            
            return HybridAnalysisResult(
                edge_estimate=openai_result.edge_estimate,
                confidence_score=min(openai_result.confidence_score + confidence_boost, 1.0),
                risk_factors=openai_result.risk_factors,
                value_assessment=openai_result.value_assessment,
                reasoning=f"[PREMIUM] {openai_result.reasoning}",
                recommended_action=openai_result.recommended_action,
                ai_provider="openai",
                model_used=openai_result.model_used,
                analysis_cost=openai_result.cost,
                cost_savings=cost_savings,
                analysis_time=openai_result.analysis_time,
                is_premium_analysis=True,
                routing_reason=routing.reason,
                confidence_boost=confidence_boost
            )
            
        except Exception as e:
            logger.error(f"OpenAI analysis error: {e}")
            # Fallback to Venice AI
            return await self._analyze_with_venice(match_data, historical_context, routing)
    
    async def _analyze_with_venice(self, match_data: Dict, historical_context: str,
                                 routing: RoutingDecision) -> Optional[HybridAnalysisResult]:
        """Analyze with Venice AI standard analysis"""
        
        try:
            async with self.venice_client as client:
                venice_result = await client.analyze_match_value(match_data, historical_context)
            
            if not venice_result:
                return None
            
            # Calculate cost savings vs OpenAI
            # Estimate what OpenAI would have cost
            estimated_openai_cost = venice_result.cost * 25  # Venice is ~25x cheaper
            cost_savings = estimated_openai_cost - venice_result.cost
            
            return HybridAnalysisResult(
                edge_estimate=venice_result.edge_estimate,
                confidence_score=venice_result.confidence_score,
                risk_factors=venice_result.risk_factors,
                value_assessment=venice_result.value_assessment,
                reasoning=venice_result.reasoning,
                recommended_action=venice_result.recommended_action,
                ai_provider="venice",
                model_used="llama-3.3-70b",
                analysis_cost=venice_result.cost,
                cost_savings=cost_savings,
                analysis_time=venice_result.analysis_time,
                is_premium_analysis=False,
                routing_reason=routing.reason,
                confidence_boost=0.0
            )
            
        except Exception as e:
            logger.error(f"Venice AI analysis error: {e}")
            return None
    
    async def analyze_batch(self, opportunities: List[Dict]) -> List[HybridAnalysisResult]:
        """Analyze multiple opportunities with smart batching"""
        
        if not opportunities:
            return []
        
        logger.info(f"Starting hybrid batch analysis of {len(opportunities)} opportunities...")
        
        # Separate into Venice and OpenAI batches
        venice_batch = []
        openai_batch = []
        
        for opp in opportunities:
            routing = self._make_routing_decision(opp)
            if routing.use_openai and self.openai_available:
                openai_batch.append((opp, routing))
            else:
                venice_batch.append((opp, routing))
        
        logger.info(f"Routing: {len(venice_batch)} to Venice AI, {len(openai_batch)} to OpenAI")
        
        # Process batches concurrently
        results = []
        
        # Create tasks for both batches
        tasks = []
        
        # Venice AI batch (can handle many concurrent requests)
        for opp, routing in venice_batch:
            task = self._analyze_with_venice(opp, "", routing)
            tasks.append(task)
        
        # OpenAI batch (limit concurrency to avoid rate limits)
        for opp, routing in openai_batch:
            task = self._analyze_with_openai(opp, "", routing)
            tasks.append(task)
        
        # Execute all tasks concurrently
        if tasks:
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and None results
            for result in batch_results:
                if isinstance(result, HybridAnalysisResult):
                    results.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"Batch analysis error: {result}")
        
        # Sort by edge estimate (highest first)
        results.sort(key=lambda x: x.edge_estimate, reverse=True)
        
        logger.info(f"Hybrid batch analysis completed: {len(results)} results")
        
        return results
    
    def get_routing_stats(self) -> Dict:
        """Get routing statistics"""
        
        total_requests = self.venice_requests + self.openai_requests
        
        return {
            'total_requests': total_requests,
            'venice_requests': self.venice_requests,
            'openai_requests': self.openai_requests,
            'venice_percentage': (self.venice_requests / max(total_requests, 1)) * 100,
            'openai_percentage': (self.openai_requests / max(total_requests, 1)) * 100,
            'total_cost_savings': round(self.total_cost_savings, 4),
            'avg_savings_per_request': round(self.total_cost_savings / max(total_requests, 1), 4),
            'openai_available': self.openai_available,
            'routing_criteria': {
                'high_edge_threshold': self.high_edge_threshold,
                'high_stake_threshold': self.high_stake_threshold,
                'critical_time_threshold': self.critical_time_threshold
            }
        }
    
    async def test_both_providers(self) -> Dict:
        """Test both AI providers"""
        
        results = {
            'venice_ai': False,
            'openai': False,
            'hybrid_ready': False
        }
        
        # Test Venice AI
        try:
            async with self.venice_client as client:
                venice_ok = await client.test_connection()
                results['venice_ai'] = venice_ok
        except Exception as e:
            logger.error(f"Venice AI test failed: {e}")
        
        # Test OpenAI
        if self.openai_available:
            try:
                openai_ok = await self.openai_client.test_connection()
                results['openai'] = openai_ok
            except Exception as e:
                logger.error(f"OpenAI test failed: {e}")
        
        # Hybrid ready if at least Venice works
        results['hybrid_ready'] = results['venice_ai']
        
        return results
