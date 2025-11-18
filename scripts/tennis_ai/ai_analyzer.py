#!/usr/bin/env python3
"""
W15 Tennis AI Analyzer
Analysoi vain pre-filterin läpäisseet ottelut OpenAI:llä
Kustannus: ~€0.03 per ottelu (GPT-4)

VAATII: OPENAI_API_KEY environment variable
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
INPUT_FILE = project_root / 'data' / 'tennis_ai' / 'ai_candidates.json'
OUTPUT_FILE = project_root / 'data' / 'tennis_ai' / 'ai_analysis_results.json'
MODEL = 'gpt-4'  # Vaihda 'gpt-3.5-turbo' jos haluat halvemman

if not OPENAI_API_KEY:
    print("❌ ERROR: OPENAI_API_KEY not set")
    print("   Set it in telegram_secrets.env")
    print("   Get key: https://platform.openai.com/api-keys")
    exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

# AI PROMPT
ANALYSIS_PROMPT = """
You are an elite tennis betting analyst specializing in ITF W15 Women's tournaments.

**Match Data:**

- Player A: {player_a} (Ranking: {ranking_a})
- Player B: {player_b} (Ranking: {ranking_b})
- Tournament: {tournament}
- Surface: {surface}
- Pre-filter Score: {prefilter_score}/100

**Analysis Framework:**

1. **Ranking Analysis**
   - Ranking gap: {ranking_gap}
   - W15 tier implications

2. **Surface Suitability**
   - {surface} court characteristics
   - Player styles and surface fit

3. **Form Assessment**
   - Recent results
   - Momentum indicators

4. **Value Identification**
   - Expected win probability
   - Market inefficiencies

5. **Risk Factors**
   - Data quality
   - Unknown variables

**Output MUST be valid JSON:**

{{
  "recommended_bet": "Player A" | "Player B" | "Skip",
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
- At W15 level, upsets are common - be conservative
- ONLY output valid JSON, no other text
"""

class TennisAIAnalyzer:
    def __init__(self, api_key, model='gpt-4'):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.analyses = []
    
    def analyze_match(self, match):
        """Analysoi yksittäinen ottelu AI:llä"""
        
        ranking_gap = None
        if match.get('ranking_a') and match.get('ranking_b'):
            ranking_gap = abs(match['ranking_a'] - match['ranking_b'])
        
        prompt = ANALYSIS_PROMPT.format(
            player_a=match['player_a'],
            player_b=match['player_b'],
            ranking_a=match.get('ranking_a', 'Unknown'),
            ranking_b=match.get('ranking_b', 'Unknown'),
            tournament=match['tournament'],
            surface=match['surface'],
            prefilter_score=match['score'],
            ranking_gap=ranking_gap or 'Unknown'
        )
        
        try:
            print(f"\n🤖 Analyzing: {match['player_a']} vs {match['player_b']}...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional tennis betting analyst. Always respond with valid JSON only."},
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
        """Analysoi useita otteluita"""
        results = []
        
        for i, match in enumerate(matches, 1):
            print(f"\n[{i}/{len(matches)}]")
            result = self.analyze_match(match)
            results.append(result)
            self.analyses.append(result)
        
        return results
    
    def get_high_value_bets(self, min_confidence='Medium', min_ev=7):
        """Suodata korkean arvon vedot"""
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
    """Lataa pre-filterin tulokset (prefers optimized batch if available)"""
    if filename is None:
        # Check for optimized batch first
        optimized_file = project_root / 'data' / 'tennis_ai' / 'ai_candidates_optimized.json'
        default_file = project_root / 'data' / 'tennis_ai' / 'ai_candidates.json'
        
        if optimized_file.exists():
            filename = optimized_file
            print("📊 Using optimized batch (top 25 matches)")
        else:
            filename = default_file
    else:
        filename = Path(filename)
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        matches = data['matches']
        
        # Show batch info if optimized
        if 'original_total' in data:
            print(f"   Original: {data['original_total']} → Optimized: {len(matches)}")
            print(f"   Cost savings: ${(data['original_total'] - len(matches)) * 0.03:.2f}")
        
        return matches
    except FileNotFoundError:
        print(f"❌ ERROR: {filename} not found")
        print("   Run prefilter_w15_matches.py first")
        exit(1)

def save_results(analyzer, filename=None):
    """Tallenna AI-analyysin tulokset"""
    if filename is None:
        filename = project_root / 'data' / 'tennis_ai' / 'ai_analysis_results.json'
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
    """Tulosta yhteenveto"""
    print(f"\n{'='*80}")
    print(f"🎯 AI ANALYSIS SUMMARY")
    print(f"{'='*80}\n")
    
    print(f"🏆 HIGH-VALUE BETTING OPPORTUNITIES: {len(high_value_bets)}\n")
    
    for i, bet in enumerate(high_value_bets, 1):
        match = bet['match_data']
        print(f"{i}. {match['player_a']} vs {match['player_b']}")
        print(f"   🎯 Bet: {bet['recommended_bet']} | Confidence: {bet['confidence']}")
        print(f"   💰 Stake: {bet['suggested_stake_pct']}% | EV: +{bet.get('expected_value_pct', 0)}%")
        print(f"   📊 {match['tournament']} | {match['surface']}")
        print(f"   💡 {bet['reasoning'][:150]}...")
        print()

if __name__ == '__main__':
    print("📥 Loading pre-filtered candidates...")
    candidates = load_candidates()
    
    print(f"✅ Loaded {len(candidates)} candidates\n")
    
    estimated_cost = len(candidates) * 0.03
    print(f"💰 Estimated API cost: €{estimated_cost:.2f}")
    proceed = input(f"\nProceed with AI analysis of {len(candidates)} matches? (y/n): ")
    
    if proceed.lower() != 'y':
        print("❌ Aborted")
        exit()
    
    print("\n🤖 Starting AI analysis...\n")
    
    analyzer = TennisAIAnalyzer(OPENAI_API_KEY, model=MODEL)
    results = analyzer.analyze_batch(candidates)
    
    high_value_bets = save_results(analyzer)
    print_summary(high_value_bets)
    
    print(f"\n✅ Analysis complete!")
    print(f"\n📋 Next: python3 scripts/tennis_ai/generate_bet_list.py")

