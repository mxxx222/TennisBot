"""
OpenAI Client for Premium Analysis
Used for high-stakes bet validation in hybrid AI strategy
"""

import asyncio
import logging
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import openai
from openai import OpenAI

from ai_analysis.ai_config import VeniceAIConfig
from ai_analysis.cost_tracker import VeniceAICostTracker

logger = logging.getLogger(__name__)

@dataclass
class OpenAIAnalysisResult:
    """Result from OpenAI premium analysis"""
    edge_estimate: float
    confidence_score: float
    risk_factors: List[str]
    value_assessment: str
    reasoning: str
    recommended_action: str
    tokens_used: Dict[str, int]
    cost: float
    analysis_time: float
    model_used: str

class OpenAIClient:
    """OpenAI client for premium analysis in hybrid strategy"""
    
    def __init__(self, api_key: str = None):
        self.config = VeniceAIConfig()
        
        # Initialize OpenAI client
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            # Will use OPENAI_API_KEY from environment
            self.client = OpenAI()
        
        self.cost_tracker = VeniceAICostTracker()
        
        # Premium models for high-stakes analysis
        self.premium_model = "gpt-4o"
        self.fast_model = "gpt-4o-mini"
        
        # Performance tracking
        self.total_requests = 0
        self.failed_requests = 0
        self.total_cost = 0.0
    
    async def __aenter__(self):
        """Async context manager entry"""
        try:
            # Test connection
            await self.test_connection()
            logger.info("✅ OpenAIClient initialized successfully")
            return self
        except Exception as e:
            logger.error(f"❌ OpenAIClient initialization failed: {e}")
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        try:
            # Save any final cost tracking data
            if hasattr(self.cost_tracker, 'save_costs'):
                self.cost_tracker.save_costs()
            logger.info("✅ OpenAIClient cleaned up successfully")
        except Exception as e:
            logger.error(f"⚠️ Error during OpenAIClient cleanup: {e}")
        return False
        
    async def analyze_premium_opportunity(self, match_data: Dict, 
                                        historical_context: str = "",
                                        use_fast_model: bool = False) -> Optional[OpenAIAnalysisResult]:
        """Analyze high-stakes opportunity with OpenAI premium analysis"""
        
        try:
            # Choose model based on urgency
            model = self.fast_model if use_fast_model else self.premium_model
            
            # Prepare premium analysis prompt
            prompt = self._prepare_premium_prompt(match_data, historical_context)
            
            # Make API request
            start_time = time.time()
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=model,
                messages=[
                    {"role": "system", "content": self._get_premium_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            analysis_time = time.time() - start_time
            
            # Parse response
            result = self._parse_openai_response(response, analysis_time, model)
            
            # Track costs
            self._update_cost_tracking(response.usage, model)
            
            self.total_requests += 1
            
            logger.info(f"OpenAI premium analysis completed for {match_data.get('home_team')} vs {match_data.get('away_team')} "
                       f"(Edge: {result.edge_estimate:.1f}%, Cost: ${result.cost:.4f}, Model: {model})")
            
            return result
            
        except Exception as e:
            logger.error(f"OpenAI premium analysis failed: {e}")
            self.failed_requests += 1
            return None
    
    def _prepare_premium_prompt(self, match_data: Dict, historical_context: str) -> str:
        """Prepare premium analysis prompt for OpenAI"""
        
        return f"""Analyze this high-stakes soccer betting opportunity with premium accuracy:

MATCH DETAILS:
- Home Team: {match_data.get('home_team', 'Unknown')}
- Away Team: {match_data.get('away_team', 'Unknown')}
- Current Odds: Home {match_data.get('home_odds', 0)}, Away {match_data.get('away_odds', 0)}
- League: {match_data.get('league', '').replace('soccer_', '').replace('_', ' ').title()}
- Commence Time: {match_data.get('commence_time', 'Unknown')}

CURRENT ANALYSIS:
- Preliminary Edge: {match_data.get('current_edge', 0)}%
- Stake Recommendation: ${match_data.get('stake', 0)}
- Initial Confidence: {match_data.get('confidence', 'Medium')}

HISTORICAL CONTEXT:
{historical_context or "Limited historical data available"}

PREMIUM ANALYSIS REQUIRED:
This is a high-stakes opportunity (>4% edge OR >$15 stake) requiring your most accurate assessment.

Please provide a comprehensive JSON analysis with:
{{
    "edge_estimate": float,  // Your refined edge estimate (0-15)
    "confidence_score": float,  // Confidence level (0-1)
    "risk_factors": [string],  // Key risk factors to consider
    "value_assessment": string,  // "strong_value", "moderate_value", "marginal_value", "no_value"
    "reasoning": string,  // Detailed reasoning for your assessment
    "recommended_action": string,  // "bet", "reduce_stake", "monitor", "avoid"
    "key_insights": [string],  // 2-3 most important insights
    "market_efficiency": float,  // Market efficiency score (0-1)
    "timing_sensitivity": string  // "urgent", "moderate", "flexible"
}}

Focus on:
1. Market inefficiencies in this specific league tier
2. True probability vs bookmaker odds assessment
3. Risk-adjusted return potential
4. Timing factors and market movement risks
5. Bankroll management considerations"""
    
    def _get_premium_system_prompt(self) -> str:
        """Get system prompt for premium analysis"""
        
        return """You are an elite sports betting analyst with expertise in soccer value betting and market analysis. 

Your role is to provide premium-quality analysis for high-stakes betting opportunities. You have access to advanced statistical models, market efficiency analysis, and risk assessment frameworks.

Key principles:
- Accuracy over speed - this is premium analysis
- Conservative risk assessment for large stakes
- Market efficiency awareness for different league tiers
- Comprehensive risk factor identification
- Clear, actionable recommendations

You specialize in:
- Lower-tier European soccer leagues (Championship, League 1, Serie B, etc.)
- Market inefficiency detection
- Value betting edge calculation
- Risk-adjusted return optimization
- Bankroll management for high-stakes decisions

Always provide structured JSON responses with detailed reasoning."""
    
    def _parse_openai_response(self, response, analysis_time: float, model: str) -> OpenAIAnalysisResult:
        """Parse OpenAI response into structured result"""
        
        try:
            # Extract content and usage
            content = response.choices[0].message.content
            usage = response.usage
            
            # Parse JSON response
            try:
                analysis_data = json.loads(content)
            except json.JSONDecodeError:
                # Fallback parsing if JSON fails
                analysis_data = self._extract_from_text(content)
            
            # Calculate cost (OpenAI pricing)
            input_cost = (usage.prompt_tokens / 1_000_000) * 5.00  # $5 per 1M input tokens
            output_cost = (usage.completion_tokens / 1_000_000) * 15.00  # $15 per 1M output tokens
            total_cost = input_cost + output_cost
            
            return OpenAIAnalysisResult(
                edge_estimate=float(analysis_data.get('edge_estimate', 0)),
                confidence_score=float(analysis_data.get('confidence_score', 0.5)),
                risk_factors=analysis_data.get('risk_factors', []),
                value_assessment=analysis_data.get('value_assessment', 'no_value'),
                reasoning=analysis_data.get('reasoning', 'Premium analysis completed'),
                recommended_action=analysis_data.get('recommended_action', 'monitor'),
                tokens_used={
                    'input': usage.prompt_tokens,
                    'output': usage.completion_tokens
                },
                cost=total_cost,
                analysis_time=analysis_time,
                model_used=model
            )
            
        except Exception as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            
            # Return default result
            return OpenAIAnalysisResult(
                edge_estimate=0.0,
                confidence_score=0.0,
                risk_factors=["Analysis parsing failed"],
                value_assessment="no_value",
                reasoning="Failed to parse premium analysis",
                recommended_action="avoid",
                tokens_used={'input': 0, 'output': 0},
                cost=0.0,
                analysis_time=analysis_time,
                model_used=model
            )
    
    def _extract_from_text(self, content: str) -> Dict:
        """Extract analysis data from text response (fallback)"""
        
        analysis = {
            'edge_estimate': 0.0,
            'confidence_score': 0.5,
            'risk_factors': [],
            'value_assessment': 'no_value',
            'reasoning': content[:200] + "..." if len(content) > 200 else content,
            'recommended_action': 'monitor'
        }
        
        # Simple text parsing for key metrics
        import re
        
        # Look for edge percentage
        edge_match = re.search(r'edge[:\s]*(\d+\.?\d*)%?', content.lower())
        if edge_match:
            analysis['edge_estimate'] = float(edge_match.group(1))
        
        # Look for confidence
        conf_match = re.search(r'confidence[:\s]*(\d+\.?\d*)', content.lower())
        if conf_match:
            analysis['confidence_score'] = float(conf_match.group(1))
            if analysis['confidence_score'] > 1:
                analysis['confidence_score'] /= 100
        
        # Determine value assessment
        if 'strong value' in content.lower():
            analysis['value_assessment'] = 'strong_value'
        elif 'moderate value' in content.lower():
            analysis['value_assessment'] = 'moderate_value'
        elif 'marginal value' in content.lower():
            analysis['value_assessment'] = 'marginal_value'
        
        # Determine action
        if 'bet' in content.lower() and 'avoid' not in content.lower():
            analysis['recommended_action'] = 'bet'
        elif 'reduce' in content.lower():
            analysis['recommended_action'] = 'reduce_stake'
        elif 'avoid' in content.lower():
            analysis['recommended_action'] = 'avoid'
        
        return analysis
    
    def _update_cost_tracking(self, usage, model: str):
        """Update cost tracking for OpenAI usage"""
        
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens
        
        # Calculate OpenAI cost
        input_cost = (input_tokens / 1_000_000) * 5.00
        output_cost = (output_tokens / 1_000_000) * 15.00
        total_cost = input_cost + output_cost
        
        self.total_cost += total_cost
        
        # Log to cost tracker (as OpenAI equivalent for comparison)
        self.cost_tracker.log_cost(
            feature="premium_analysis",
            model_used=f"openai_{model}",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            venice_cost=total_cost,  # This is actual OpenAI cost
            request_id=f"openai_{datetime.now().strftime('%H%M%S')}"
        )
        
        logger.info(f"OpenAI cost: ${total_cost:.4f} (Model: {model}, "
                   f"Tokens: {input_tokens + output_tokens})")
    
    async def test_connection(self) -> bool:
        """Test OpenAI API connection"""
        
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.fast_model,
                messages=[
                    {"role": "user", "content": "Test connection. Respond with 'OK' only."}
                ],
                max_tokens=5
            )
            
            if response and response.choices:
                content = response.choices[0].message.content.strip().lower()
                return 'ok' in content
            
            return False
            
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False
    
    def get_cost_summary(self) -> Dict:
        """Get OpenAI usage cost summary"""
        
        return {
            'total_requests': self.total_requests,
            'failed_requests': self.failed_requests,
            'success_rate': (self.total_requests - self.failed_requests) / max(self.total_requests, 1),
            'total_cost': round(self.total_cost, 4),
            'avg_cost_per_request': round(self.total_cost / max(self.total_requests, 1), 4),
            'premium_model': self.premium_model,
            'fast_model': self.fast_model
        }
