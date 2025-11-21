#!/usr/bin/env python3
"""
Football OU2.5 AI Analyzer
Analyzes pre-filtered football matches for Over/Under 2.5 goals betting
Cost: ~€0.03 per match (GPT-4)

REQUIRES: OPENAI_API_KEY environment variable
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / 'telegram_secrets.env'
if env_path.exists():
    load_dotenv(env_path)

# OpenAI import
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    print("❌ ERROR: openai library not installed")
    print("   Install: pip install openai")
    exit(1)

# CONFIG
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
INPUT_FILE = project_root / 'data' / 'football_ai' / 'ai_candidates.json'
OUTPUT_FILE = project_root / 'data' / 'football_ai' / 'ai_analysis_results.json'
MODEL = 'gpt-4'  # Change to 'gpt-3.5-turbo' if you want cheaper

if not OPENAI_API_KEY:
    print("❌ ERROR: OPENAI_API_KEY not set")
    print("   Set it in telegram_secrets.env")
    print("   Get key: https://platform.openai.com/api-keys")
    exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

# AI PROMPT
ANALYSIS_PROMPT = """
You are an elite football betting analyst specializing in Over/Under 2.5 goals betting.

**Match Data:**

- Home Team: {home_team}
- Away Team: {away_team}
- League: {league}
- Home Goals Avg: {home_goals_avg}
- Away Goals Avg: {away_goals_avg}
- Home Conceded Avg: {home_conceded_avg}
- Away Conceded Avg: {away_conceded_avg}
- Home Form: {home_form}
- Away Form: {away_form}
- Pre-filter Score: {prefilter_score}/100

**Analysis Framework:**

1. **Goal-Scoring Patterns**
   - Combined average goals: {total_avg_goals}
   - Offensive strength analysis
   - Recent goal trends

2. **Defensive Weakness**
   - Combined conceded average: {total_conceded_avg}
   - Defensive vulnerabilities
   - Clean sheet probability

3. **Form Assessment**
   - Recent match results
   - Goal-scoring momentum
   - Defensive form

4. **Value Identification**
   - Expected total goals probability
   - Market inefficiencies
   - Over/Under edge calculation

5. **Risk Factors**
   - Data quality
   - Missing key players
   - Weather conditions (if available)

**Output MUST be valid JSON:**

{{
  "recommended_bet": "OVER" | "UNDER" | "Skip",
  "confidence": "High" | "Medium" | "Low",
  "win_probability": 0.00-1.00,
  "expected_value_pct": 0-100,
  "reasoning": "4-5 sentence explanation",
  "key_factors": ["Factor 1", "Factor 2", "Factor 3"],
  "suggested_stake_pct": 0-5,
  "risk_level": "Low" | "Medium" | "High",
  "skip_reasons": ["Reason"] (if Skip)
}}

**Guidelines:**

- Be ruthlessly selective (recommend <30% of matches)
- Require minimum +7% expected value
- **CRITICAL: Only recommend bets with impliedP >= 70%**
  - Validation from tennis shows 100% win rate (12/12) for 70%+ impliedP bets
  - Lower impliedP (<70%) has significantly higher failure rate
  - If win_probability < 0.70, recommend "Skip" regardless of other factors
- Focus on goal-scoring patterns and defensive weaknesses
- Consider league characteristics (some leagues are higher scoring)
- ONLY output valid JSON, no other text
"""

class FootballAIAnalyzer:
    def __init__(self, api_key, model='gpt-4'):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.analyses = []
    
    def analyze_match(self, match):
        """Analyze single match with AI"""
        
        # Calculate combined stats
        home_goals = match.get('home_goals_avg', 0) or 0
        away_goals = match.get('away_goals_avg', 0) or 0
        total_avg_goals = home_goals + away_goals
        
        home_conceded = match.get('home_conceded_avg', 0) or 0
        away_conceded = match.get('away_conceded_avg', 0) or 0
        total_conceded_avg = home_conceded + away_conceded
        
        prompt = ANALYSIS_PROMPT.format(
            home_team=match['home_team'],
            away_team=match['away_team'],
            league=match.get('league', 'Unknown'),
            home_goals_avg=home_goals if home_goals > 0 else 'N/A',
            away_goals_avg=away_goals if away_goals > 0 else 'N/A',
            home_conceded_avg=home_conceded if home_conceded > 0 else 'N/A',
            away_conceded_avg=away_conceded if away_conceded > 0 else 'N/A',
            home_form=match.get('home_form', 'N/A'),
            away_form=match.get('away_form', 'N/A'),
            prefilter_score=match['score'],
            total_avg_goals=total_avg_goals if total_avg_goals > 0 else 'N/A',
            total_conceded_avg=total_conceded_avg if total_conceded_avg > 0 else 'N/A'
        )
        
        try:
            print(f"\n🤖 Analyzing: {match['home_team']} vs {match['away_team']}...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional football betting analyst specializing in Over/Under 2.5 goals. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON
            if '```json' in content:
                json_str = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                json_str = content.split('```')[1].split('```')[0].strip()
            else:
                json_str = content.strip()
            
            result = json.loads(json_str)
            result['match_data'] = match
            result['analyzed_at'] = datetime.now().isoformat()
            
            print(f"   ✅ {result['recommended_bet']} | Confidence: {result['confidence']} | EV: +{result.get('expected_value_pct', 0)}%")
            
            return result
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return {
                'recommended_bet': 'Skip',
                'confidence': 'Low',
                'reasoning': f'Analysis failed: {str(e)}',
                'match_data': match,
                'analyzed_at': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def analyze_batch(self, matches):
        """Analyze multiple matches"""
        results = []
        
        for i, match in enumerate(matches, 1):
            print(f"\n[{i}/{len(matches)}]")
            result = self.analyze_match(match)
            results.append(result)
            self.analyses.append(result)
        
        return results
    
    def get_high_value_bets(self, min_confidence='Medium', min_ev=7):
        """Filter high-value bets"""
        confidence_rank = {'High': 3, 'Medium': 2, 'Low': 1}
        min_rank = confidence_rank[min_confidence]
        
        high_value = [
            a for a in self.analyses
            if a['recommended_bet'] != 'Skip'
            and confidence_rank.get(a['confidence'], 0) >= min_rank
            and a.get('expected_value_pct', 0) >= min_ev
        ]
        
        high_value.sort(
            key=lambda x: (
                confidence_rank.get(x['confidence'], 0),
                x.get('expected_value_pct', 0)
            ),
            reverse=True
        )
        
        return high_value

def load_candidates(filename=None):
    """Load pre-filter results"""
    if filename is None:
        filename = project_root / 'data' / 'football_ai' / 'ai_candidates.json'
    else:
        filename = Path(filename)
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        matches = data['matches']
        
        return matches
    except FileNotFoundError:
        print(f"❌ ERROR: {filename} not found")
        print("   Run prefilter_ou25_matches.py first")
        exit(1)

def save_results(analyzer, filename=None):
    """Save AI analysis results"""
    if filename is None:
        filename = project_root / 'data' / 'football_ai' / 'ai_analysis_results.json'
    else:
        filename = Path(filename)
    
    # Ensure directory exists
    filename.parent.mkdir(parents=True, exist_ok=True)
    
    high_value = analyzer.get_high_value_bets()
    
    output = {
        'generated_at': datetime.now().isoformat(),
        'model': analyzer.model,
        'total_analyzed': len(analyzer.analyses),
        'high_value_bets': len(high_value),
        'estimated_cost_eur': len(analyzer.analyses) * 0.03,
        'all_analyses': analyzer.analyses,
        'high_value_bets_detail': high_value
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Results saved to {filename}")
    return high_value

def print_summary(high_value_bets):
    """Print summary"""
    print(f"\n{'='*80}")
    print(f"🎯 AI ANALYSIS SUMMARY")
    print(f"{'='*80}\n")
    
    print(f"🏆 HIGH-VALUE BETTING OPPORTUNITIES: {len(high_value_bets)}\n")
    
    for i, bet in enumerate(high_value_bets, 1):
        match = bet['match_data']
        print(f"{i}. {match['home_team']} vs {match['away_team']}")
        print(f"   🎯 Bet: {bet['recommended_bet']} | Confidence: {bet['confidence']}")
        print(f"   💰 Stake: {bet['suggested_stake_pct']}% | EV: +{bet.get('expected_value_pct', 0)}%")
        print(f"   📊 {match['league']}")
        print(f"   💡 {bet['reasoning'][:150]}...")
        print()

if __name__ == '__main__':
    print("📥 Loading pre-filtered candidates...")
    candidates = load_candidates()
    
    print(f"✅ Loaded {len(candidates)} candidates\n")
    
    estimated_cost = len(candidates) * 0.03
    print(f"💰 Estimated API cost: €{estimated_cost:.2f}")
    
    # Check if running non-interactively
    import sys
    if sys.stdin.isatty():
        proceed = input(f"\nProceed with AI analysis of {len(candidates)} matches? (y/n): ")
        if proceed.lower() != 'y':
            print("❌ Aborted")
            exit()
    else:
        print(f"\n✅ Proceeding automatically (non-interactive mode)")
    
    print("\n🤖 Starting AI analysis...\n")
    
    analyzer = FootballAIAnalyzer(OPENAI_API_KEY, model=MODEL)
    results = analyzer.analyze_batch(candidates)
    
    high_value_bets = save_results(analyzer)
    print_summary(high_value_bets)
    
    print(f"\n✅ Analysis complete!")
    print(f"\n📋 Next: python3 scripts/football_ai/generate_bet_list.py")

