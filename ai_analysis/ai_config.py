"""
Venice AI Configuration for Maximum ROI Optimization - Multi-Sport Support
90% cost savings vs OpenAI while maintaining analysis quality
Supports: Soccer (7 leagues) + Tennis (ITF Women focus)
"""

import os
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv('telegram_secrets.env')

class VeniceAIConfig:
    """Configuration for Venice AI integration"""
    
    # Venice AI API Configuration
    VENICE_API_KEY = os.getenv('VENICE_API_KEY', '4sN-95GvZRULODkSrIA2O-VDahLE0SjCB3h4E0Rges')
    VENICE_BASE_URL = "https://api.venice.ai/api/v1"
    
    # Model Configuration (Llama 3.3 70B for best quality)
    DEFAULT_MODEL = "llama-3.3-70b"
    FAST_MODEL = "llama-3.2-3b"  # For simple tasks
    EMBEDDING_MODEL = "text-embedding-3-small"  # For semantic search
    
    # Cost Analysis (per 1M tokens)
    VENICE_INPUT_COST = 0.15   # $0.15 per 1M input tokens
    VENICE_OUTPUT_COST = 0.60  # $0.60 per 1M output tokens
    OPENAI_INPUT_COST = 5.00   # $5.00 per 1M input tokens (GPT-4o)
    OPENAI_OUTPUT_COST = 15.00 # $15.00 per 1M output tokens (GPT-4o)
    
    # Request Configuration
    MAX_TOKENS = 4000
    TEMPERATURE = 0.1  # Low temperature for consistent analysis
    TOP_P = 0.9
    FREQUENCY_PENALTY = 0.0
    PRESENCE_PENALTY = 0.0
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE = 60
    MAX_TOKENS_PER_MINUTE = 100000
    REQUEST_TIMEOUT = 30  # seconds
    
    # Retry Configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 2.0  # seconds
    BACKOFF_MULTIPLIER = 2.0
    
    # Analysis Configuration - Multi-Sport Support
    ANALYSIS_PROMPT_TEMPLATES = {
        'soccer_analysis': """You are a professional sports betting analyst with expertise in soccer value betting.

Analyze this soccer match data and provide insights for betting decisions:

Match: {home_team} vs {away_team}
League: {league}
Odds: Home {home_odds}, Away {away_odds}
Historical Data: {historical_context}

Provide analysis in this JSON format:
{{
    "edge_estimate": float,  // Estimated edge percentage (0-10)
    "confidence_score": float,  // Confidence 0-1
    "risk_factors": [string],  // List of risk factors
    "value_assessment": string,  // "strong_value", "moderate_value", "no_value"
    "reasoning": string,  // Brief explanation
    "recommended_action": string  // "bet", "monitor", "avoid"
}}

Focus on:
- Market inefficiencies in lower-tier leagues
- Odds value vs true probability
- Historical performance patterns
- Risk-adjusted returns""",

        'tennis_analysis': """You are a professional sports betting analyst with expertise in tennis value betting, specifically ITF Women's tournaments.

Analyze this tennis match data and provide insights for betting decisions:

Match: {player1} vs {player2}
Tournament: {tournament} ({tournament_level})
Surface: {surface}
Odds: {player1} {player1_odds}, {player2} {player2_odds}
Rankings: {player1_ranking} vs {player2_ranking}
Head-to-Head: {head_to_head}
Recent Form: {recent_form}

Provide analysis in this JSON format:
{{
    "edge_estimate": float,  // Estimated edge percentage (0-15)
    "confidence_score": float,  // Confidence 0-1
    "risk_factors": [string],  // List of risk factors
    "value_assessment": string,  // "strong_value", "moderate_value", "no_value"
    "reasoning": string,  // Brief explanation with tennis-specific insights
    "recommended_action": string  // "bet", "monitor", "avoid"
}}

Focus on:
- ITF Women's tournament dynamics (proven +17.81% ROI edge)
- Odds range 1.30-1.80 (historical sweet spot)
- Ranking differentials and surface preferences
- Player form and head-to-head patterns
- Tournament level impact (W15, W25, etc.)
- Surface-specific advantages (Hard, Clay, Grass)""",

        'match_analysis': """You are a professional sports betting analyst with expertise in both soccer and tennis value betting.

Analyze this match data and provide insights for betting decisions:

Sport: {sport}
Match Details: {match_details}
Historical Data: {historical_context}

Provide analysis in this JSON format:
{{
    "edge_estimate": float,  // Estimated edge percentage (0-15)
    "confidence_score": float,  // Confidence 0-1
    "risk_factors": [string],  // List of risk factors
    "value_assessment": string,  // "strong_value", "moderate_value", "no_value"
    "reasoning": string,  // Brief explanation
    "recommended_action": string  // "bet", "monitor", "avoid"
}}

Focus on sport-specific factors and proven profitable patterns.""",

        'pattern_recognition': """Analyze these historical betting opportunities to identify patterns:

Data: {historical_opportunities}

Identify:
1. Most profitable patterns
2. Risk indicators to avoid
3. Optimal timing factors
4. League-specific insights

Return insights as structured analysis.""",

        'edge_refinement': """Refine the edge estimate for this betting opportunity:

Current Edge Estimate: {current_edge}%
Match Context: {match_context}
Historical Performance: {historical_performance}
Market Conditions: {market_conditions}

Provide refined edge estimate with reasoning."""
    }
    
    # Cost Tracking
    TRACK_COSTS = True
    COST_LOG_FILE = "venice_ai_costs.log"
    MONTHLY_BUDGET_ALERT = 50.00  # Alert if monthly costs exceed $50
    
    @classmethod
    def calculate_cost_savings(cls, input_tokens: int, output_tokens: int) -> Dict[str, float]:
        """Calculate cost savings vs OpenAI"""
        
        venice_cost = (input_tokens * cls.VENICE_INPUT_COST + 
                      output_tokens * cls.VENICE_OUTPUT_COST) / 1_000_000
        
        openai_cost = (input_tokens * cls.OPENAI_INPUT_COST + 
                      output_tokens * cls.OPENAI_OUTPUT_COST) / 1_000_000
        
        savings = openai_cost - venice_cost
        savings_percentage = (savings / openai_cost) * 100 if openai_cost > 0 else 0
        
        return {
            'venice_cost': round(venice_cost, 4),
            'openai_cost': round(openai_cost, 4),
            'savings': round(savings, 4),
            'savings_percentage': round(savings_percentage, 1)
        }
    
    @classmethod
    def get_model_for_task(cls, task_complexity: str) -> str:
        """Get appropriate model based on task complexity"""
        
        if task_complexity in ['simple', 'fast']:
            return cls.FAST_MODEL
        else:
            return cls.DEFAULT_MODEL
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate Venice AI configuration"""
        
        if not cls.VENICE_API_KEY or cls.VENICE_API_KEY == 'your_venice_api_key_here':
            print("❌ Venice AI API key not configured")
            return False
        
        if len(cls.VENICE_API_KEY) < 20:
            print("❌ Venice AI API key appears invalid")
            return False
        
        return True

# Analysis Templates for Different Use Cases
ANALYSIS_TEMPLATES = {
    'value_detection': {
        'system_prompt': """You are an expert sports betting analyst specializing in value detection in soccer markets. 
        Your goal is to identify betting opportunities with positive expected value in lower-tier leagues where market inefficiencies exist.""",
        
        'user_prompt_template': """Analyze this soccer match for betting value:

Match: {home_team} vs {away_team}
League: {league} (Tier {tier})
Current Odds: Home {home_odds}, Away {away_odds}
Market Context: {market_context}

Assess:
1. True probability vs bookmaker odds
2. Market efficiency for this league tier
3. Value betting opportunity (if any)
4. Risk factors and confidence level

Respond with structured analysis focusing on ROI potential."""
    },
    
    'risk_assessment': {
        'system_prompt': """You are a risk management specialist for sports betting. 
        Your role is to identify potential risks and provide confidence scoring for betting decisions.""",
        
        'user_prompt_template': """Evaluate the risk profile of this betting opportunity:

Opportunity: {team} @ {odds}
League: {league}
Stake: ${stake}
Estimated Edge: {edge}%

Analyze:
1. Downside risk factors
2. Probability of loss scenarios  
3. Risk-adjusted return potential
4. Confidence score (0-100)

Provide risk assessment with actionable insights."""
    },
    
    'pattern_analysis': {
        'system_prompt': """You are a pattern recognition expert for sports betting data. 
        You identify profitable patterns and trends in historical betting performance.""",
        
        'user_prompt_template': """Analyze these betting patterns for insights:

Historical Data: {historical_data}
Time Period: {time_period}
League Focus: {leagues}

Identify:
1. Most profitable patterns
2. Seasonal/temporal trends  
3. League-specific inefficiencies
4. Optimization recommendations

Provide actionable pattern insights for strategy improvement."""
    }
}

# Cost Monitoring Configuration
COST_MONITORING = {
    'daily_budget': 5.00,      # $5/day budget
    'monthly_budget': 50.00,   # $50/month budget  
    'alert_threshold': 0.80,   # Alert at 80% of budget
    'track_by_feature': True,  # Track costs by feature
    'export_monthly': True     # Export monthly cost reports
}
