"""
Venice AI Client for Soccer Betting Analysis
90% cost savings vs OpenAI with Llama 3.3 70B model
"""

import asyncio
import aiohttp
import logging
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from ai_analysis.ai_config import VeniceAIConfig, ANALYSIS_TEMPLATES
from ai_analysis.cost_tracker import VeniceAICostTracker

logger = logging.getLogger(__name__)

@dataclass
class AIAnalysisResult:
    """Result from AI analysis"""
    edge_estimate: float
    confidence_score: float
    risk_factors: List[str]
    value_assessment: str
    reasoning: str
    recommended_action: str
    tokens_used: Dict[str, int]
    cost: float
    analysis_time: float

@dataclass
class CostTracker:
    """Track Venice AI usage costs"""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    request_count: int = 0
    daily_cost: float = 0.0
    monthly_cost: float = 0.0
    last_reset: datetime = None

class VeniceAIClient:
    """Venice AI client for soccer betting analysis"""
    
    def __init__(self):
        self.config = VeniceAIConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self.cost_tracker = VeniceAICostTracker()
        
        # Rate limiting
        self.request_times = []
        self.token_usage = []
        
        # Performance tracking
        self.total_requests = 0
        self.failed_requests = 0
        self.average_response_time = 0.0
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.REQUEST_TIMEOUT)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def analyze_match_value(self, match_data: Dict, historical_context: str = "") -> Optional[AIAnalysisResult]:
        """Analyze match for betting value using Venice AI"""
        
        try:
            # Prepare analysis prompt
            prompt = self._prepare_match_analysis_prompt(match_data, historical_context)
            
            # Make API request
            start_time = time.time()
            response = await self._make_api_request(
                messages=[
                    {"role": "system", "content": ANALYSIS_TEMPLATES['value_detection']['system_prompt']},
                    {"role": "user", "content": prompt}
                ],
                model=self.config.DEFAULT_MODEL
            )
            
            analysis_time = time.time() - start_time
            
            if not response:
                return None
            
            # Parse AI response
            result = self._parse_analysis_response(response, analysis_time)
            
            # Track costs
            self._update_cost_tracking(
                usage=response.get('usage', {}),
                feature="match_analysis",
                model_used=self.config.DEFAULT_MODEL,
                request_id=f"{match_data.get('home_team', 'unknown')}_{datetime.now().strftime('%H%M%S')}"
            )
            
            # Sport-specific logging
            sport = match_data.get('sport', 'soccer')
            if sport == 'tennis':
                logger.info(f"🎾 AI analysis completed for {match_data.get('player1')} vs {match_data.get('player2')} "
                           f"(Edge: {result.edge_estimate:.1f}%, Cost: ${result.cost:.4f})")
            else:
                logger.info(f"⚽ AI analysis completed for {match_data.get('home_team')} vs {match_data.get('away_team')} "
                           f"(Edge: {result.edge_estimate:.1f}%, Cost: ${result.cost:.4f})")
            
            return result
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            self.failed_requests += 1
            return None
    
    def _prepare_match_analysis_prompt(self, match_data: Dict, historical_context: str) -> str:
        """Prepare prompt for match analysis - Multi-sport support"""
        
        sport = match_data.get('sport', 'soccer')
        
        if sport == 'tennis':
            # Use tennis-specific template
            template = self.config.ANALYSIS_PROMPT_TEMPLATES['tennis_analysis']
            
            return template.format(
                player1=match_data.get('player1', 'Player 1'),
                player2=match_data.get('player2', 'Player 2'),
                tournament=match_data.get('tournament', 'Unknown Tournament'),
                tournament_level=match_data.get('tournament_level', 'ITF'),
                surface=match_data.get('surface', 'Hard'),
                player1_odds=match_data.get('player1_odds', 1.50),
                player2_odds=match_data.get('player2_odds', 2.50),
                player1_ranking=match_data.get('player1_ranking', 'Unknown'),
                player2_ranking=match_data.get('player2_ranking', 'Unknown'),
                head_to_head=match_data.get('head_to_head', 'No data'),
                recent_form=match_data.get('recent_form', 'No data'),
                historical_context=historical_context
            )
        
        else:
            # Use soccer-specific template (existing logic)
            template = ANALYSIS_TEMPLATES['value_detection']['user_prompt_template']
            
            # Get league tier
            league = match_data.get('league', '')
            tier = 2  # Default tier
            if 'champ' in league.lower() or 'bundesliga2' in league.lower():
                tier = 1
            elif 'league2' in league.lower() or 'ligue_two' in league.lower():
                tier = 3
        
        return template.format(
            home_team=match_data.get('home_team', 'Unknown'),
            away_team=match_data.get('away_team', 'Unknown'),
            league=league.replace('soccer_', '').replace('_', ' ').title(),
            tier=tier,
            home_odds=match_data.get('home_odds', 0),
            away_odds=match_data.get('away_odds', 0),
            market_context=historical_context or "Limited historical data available"
        )
    
    async def _make_api_request(self, messages: List[Dict], model: str = None, 
                               max_tokens: int = None) -> Optional[Dict]:
        """Make API request to Venice AI with rate limiting and retries"""
        
        # Rate limiting
        await self._enforce_rate_limits()
        
        model = model or self.config.DEFAULT_MODEL
        max_tokens = max_tokens or self.config.MAX_TOKENS
        
        headers = {
            "Authorization": f"Bearer {self.config.VENICE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": self.config.TEMPERATURE,
            "top_p": self.config.TOP_P,
            "frequency_penalty": self.config.FREQUENCY_PENALTY,
            "presence_penalty": self.config.PRESENCE_PENALTY
        }
        
        # Retry logic
        for attempt in range(self.config.MAX_RETRIES):
            try:
                async with self.session.post(
                    f"{self.config.VENICE_BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    
                    self.total_requests += 1
                    
                    if response.status == 200:
                        data = await response.json()
                        return data
                    
                    elif response.status == 429:
                        # Rate limit hit
                        wait_time = self.config.RETRY_DELAY * (2 ** attempt)
                        logger.warning(f"Rate limit hit, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    else:
                        error_text = await response.text()
                        logger.error(f"Venice AI API error {response.status}: {error_text}")
                        
                        if attempt < self.config.MAX_RETRIES - 1:
                            await asyncio.sleep(self.config.RETRY_DELAY * (attempt + 1))
                            continue
                        else:
                            return None
            
            except Exception as e:
                logger.error(f"Request attempt {attempt + 1} failed: {e}")
                if attempt < self.config.MAX_RETRIES - 1:
                    await asyncio.sleep(self.config.RETRY_DELAY * (attempt + 1))
                    continue
                else:
                    return None
        
        return None
    
    async def _enforce_rate_limits(self):
        """Enforce rate limiting"""
        
        current_time = time.time()
        
        # Clean old request times (older than 1 minute)
        self.request_times = [t for t in self.request_times if current_time - t < 60]
        
        # Check requests per minute
        if len(self.request_times) >= self.config.MAX_REQUESTS_PER_MINUTE:
            sleep_time = 60 - (current_time - self.request_times[0])
            if sleep_time > 0:
                logger.info(f"Rate limit: sleeping {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
        
        self.request_times.append(current_time)
    
    def _parse_analysis_response(self, response: Dict, analysis_time: float) -> AIAnalysisResult:
        """Parse Venice AI response into structured result"""
        
        try:
            # Extract content
            content = response['choices'][0]['message']['content']
            
            # Try to parse as JSON first
            try:
                analysis_data = json.loads(content)
            except json.JSONDecodeError:
                # Fallback: extract key information from text
                analysis_data = self._extract_from_text(content)
            
            # Extract usage and calculate cost
            usage = response.get('usage', {})
            input_tokens = usage.get('prompt_tokens', 0)
            output_tokens = usage.get('completion_tokens', 0)
            
            cost_info = self.config.calculate_cost_savings(input_tokens, output_tokens)
            
            return AIAnalysisResult(
                edge_estimate=float(analysis_data.get('edge_estimate', 0)),
                confidence_score=float(analysis_data.get('confidence_score', 0.5)),
                risk_factors=analysis_data.get('risk_factors', []),
                value_assessment=analysis_data.get('value_assessment', 'no_value'),
                reasoning=analysis_data.get('reasoning', 'Analysis completed'),
                recommended_action=analysis_data.get('recommended_action', 'monitor'),
                tokens_used={'input': input_tokens, 'output': output_tokens},
                cost=cost_info['venice_cost'],
                analysis_time=analysis_time
            )
            
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            
            # Return default result
            return AIAnalysisResult(
                edge_estimate=0.0,
                confidence_score=0.0,
                risk_factors=["Analysis parsing failed"],
                value_assessment="no_value",
                reasoning="Failed to parse AI analysis",
                recommended_action="avoid",
                tokens_used={'input': 0, 'output': 0},
                cost=0.0,
                analysis_time=analysis_time
            )
    
    def _extract_from_text(self, content: str) -> Dict:
        """Extract analysis data from text response (fallback)"""
        
        # Simple text parsing for key metrics
        analysis = {
            'edge_estimate': 0.0,
            'confidence_score': 0.5,
            'risk_factors': [],
            'value_assessment': 'no_value',
            'reasoning': content[:200] + "..." if len(content) > 200 else content,
            'recommended_action': 'monitor'
        }
        
        # Look for edge percentage
        import re
        edge_match = re.search(r'edge[:\s]*(\d+\.?\d*)%?', content.lower())
        if edge_match:
            analysis['edge_estimate'] = float(edge_match.group(1))
        
        # Look for confidence
        conf_match = re.search(r'confidence[:\s]*(\d+\.?\d*)', content.lower())
        if conf_match:
            analysis['confidence_score'] = float(conf_match.group(1))
            if analysis['confidence_score'] > 1:
                analysis['confidence_score'] /= 100  # Convert percentage to decimal
        
        # Determine value assessment
        if 'strong value' in content.lower() or 'excellent' in content.lower():
            analysis['value_assessment'] = 'strong_value'
        elif 'moderate value' in content.lower() or 'good' in content.lower():
            analysis['value_assessment'] = 'moderate_value'
        
        # Determine action
        if 'bet' in content.lower() and 'don\'t' not in content.lower():
            analysis['recommended_action'] = 'bet'
        elif 'avoid' in content.lower():
            analysis['recommended_action'] = 'avoid'
        
        return analysis
    
    def _update_cost_tracking(self, usage: Dict, feature: str = "match_analysis", 
                             model_used: str = None, request_id: str = ""):
        """Update cost tracking metrics"""
        
        input_tokens = usage.get('prompt_tokens', 0)
        output_tokens = usage.get('completion_tokens', 0)
        
        cost_info = self.config.calculate_cost_savings(input_tokens, output_tokens)
        model_used = model_used or self.config.DEFAULT_MODEL
        
        # Log to cost tracker
        savings = self.cost_tracker.log_cost(
            feature=feature,
            model_used=model_used,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            venice_cost=cost_info['venice_cost'],
            request_id=request_id
        )
        
        # Log cost savings
        if self.config.TRACK_COSTS:
            logger.info(f"Venice AI cost: ${cost_info['venice_cost']:.4f} "
                       f"(vs OpenAI: ${cost_info['openai_cost']:.4f}, "
                       f"saved: ${savings:.4f}, "
                       f"{cost_info['savings_percentage']:.1f}%)")
    
    async def analyze_pattern(self, historical_data: List[Dict]) -> Optional[Dict]:
        """Analyze historical patterns for insights"""
        
        try:
            # Prepare pattern analysis prompt
            prompt = f"""Analyze these historical betting opportunities for patterns:

Data: {json.dumps(historical_data[:10], indent=2)}  # Limit data size

Identify:
1. Most profitable league/odds combinations
2. Time-based patterns (day of week, time of day)
3. Risk indicators that predict losses
4. Optimal stake sizing patterns

Return insights as structured JSON with actionable recommendations."""

            response = await self._make_api_request(
                messages=[
                    {"role": "system", "content": ANALYSIS_TEMPLATES['pattern_analysis']['system_prompt']},
                    {"role": "user", "content": prompt}
                ],
                model=self.config.DEFAULT_MODEL
            )
            
            if response:
                content = response['choices'][0]['message']['content']
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return {"insights": content, "structured": False}
            
            return None
            
        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")
            return None
    
    def get_cost_summary(self) -> Dict:
        """Get cost tracking summary"""
        
        # Get daily summary from cost tracker
        daily_summary = self.cost_tracker.get_daily_summary()
        
        # Get ROI analysis
        roi_analysis = self.cost_tracker.get_roi_analysis()
        
        return {
            'total_requests': daily_summary.total_requests,
            'venice_cost': round(daily_summary.total_venice_cost, 4),
            'openai_equivalent_cost': round(daily_summary.total_openai_equivalent, 4),
            'total_savings': round(daily_summary.total_savings, 4),
            'savings_percentage': round(daily_summary.savings_percentage, 1),
            'avg_cost_per_request': round(daily_summary.total_venice_cost / max(daily_summary.total_requests, 1), 4),
            'success_rate': round((self.total_requests - self.failed_requests) / max(self.total_requests, 1), 3),
            'feature_breakdown': daily_summary.feature_breakdown,
            'model_breakdown': daily_summary.model_breakdown,
            'roi_analysis': roi_analysis
        }
    
    async def test_connection(self) -> bool:
        """Test Venice AI connection"""
        
        try:
            response = await self._make_api_request(
                messages=[
                    {"role": "user", "content": "Test connection. Respond with 'OK' if working."}
                ],
                model=self.config.FAST_MODEL,
                max_tokens=10
            )
            
            if response and 'choices' in response:
                content = response['choices'][0]['message']['content'].strip().lower()
                return 'ok' in content
            
            return False
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
