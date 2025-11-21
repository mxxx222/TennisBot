#!/usr/bin/env python3
"""
W15 Tennis AI Analyzer - Enhanced with ITF Entries Intelligence
Analysoi pre-filterin läpäisseet ottelut OpenAI:llä + entries intelligence
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

# Enhanced agent import
try:
    from scripts.tennis_ai.enhanced_tennis_agent_integration import EnhancedTennisAgent
    ENHANCED_AGENT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Enhanced agent not available: {e}")
    print("   Continuing without entries intelligence enhancement")
    ENHANCED_AGENT_AVAILABLE = False

# CONFIG
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
INPUT_FILE = project_root / 'data' / 'tennis_ai' / 'ai_candidates.json'
OUTPUT_FILE = project_root / 'data' / 'tennis_ai' / 'ai_analysis_results.json'
MODEL = 'gpt-4'  # Vaihda 'gpt-3.5-turbo' jos haluat halvemman
ENABLE_INTELLIGENCE = os.getenv('ENABLE_ENTRIES_INTELLIGENCE', 'true').lower() == 'true'

if not OPENAI_API_KEY:
    print("❌ ERROR: OPENAI_API_KEY not set")
    print("   Set it in telegram_secrets.env")
    print("   Get key: https://platform.openai.com/api-keys")
    exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

# AI PROMPT (same as base analyzer)
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
- **CRITICAL: Only recommend bets with impliedP >= 70%**
  - Validation shows 100% win rate (12/12) for 70%+ impliedP bets
  - Lower impliedP (<70%) has significantly higher failure rate
  - If win_probability < 0.70, recommend "Skip" regardless of other factors
- At W15 level, upsets are common - be conservative
- ONLY output valid JSON, no other text
"""

class TennisAIAnalyzerEnhanced:
    def __init__(self, api_key, model='gpt-4', enable_intelligence=True):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.analyses = []
        self.enable_intelligence = enable_intelligence and ENHANCED_AGENT_AVAILABLE
        
        # Initialize enhanced agent if available
        if self.enable_intelligence:
            try:
                self.enhanced_agent = EnhancedTennisAgent()
                print("✅ Entries intelligence enabled")
            except Exception as e:
                print(f"⚠️  Failed to initialize enhanced agent: {e}")
                print("   Continuing without intelligence enhancement")
                self.enable_intelligence = False
        else:
            self.enhanced_agent = None
            if not ENHANCED_AGENT_AVAILABLE:
                print("⚠️  Enhanced agent not available - running in base mode")
    
    def analyze_match(self, match):
        """Analysoi yksittäinen ottelu AI:llä + entries intelligence"""
        
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
            
            base_result = json.loads(json_str)
            base_result['match_data'] = match
            base_result['analyzed_at'] = datetime.now().isoformat()
            
            # Calculate impliedP from win_probability
            win_prob = base_result.get('win_probability', 0.5)
            base_implied_p = win_prob * 100
            
            # Enhance with entries intelligence if enabled
            if self.enable_intelligence and self.enhanced_agent:
                try:
                    # Prepare base analysis for enhancement
                    base_analysis = {
                        'recommended_bet': base_result.get('recommended_bet', 'Skip'),
                        'predicted_winner': 'Home' if base_result.get('recommended_bet') == 'Player A' else 'Away' if base_result.get('recommended_bet') == 'Player B' else None,
                        'win_probability': win_prob,
                        'impliedP': base_implied_p,
                        'confidence': base_result.get('confidence', 'Low'),
                        'reasoning': base_result.get('reasoning', '')
                    }
                    
                    # Enhance with intelligence
                    enhanced_analysis = self.enhanced_agent.analyze_match_with_intelligence(
                        player1=match['player_a'],
                        player2=match['player_b'],
                        tournament=match['tournament'],
                        base_analysis=base_analysis
                    )
                    
                    # Update result with enhanced data
                    enhanced_implied_p = enhanced_analysis.get('impliedP', base_implied_p)
                    base_result['win_probability'] = enhanced_implied_p / 100
                    base_result['impliedP'] = enhanced_implied_p
                    base_result['confidence'] = enhanced_analysis.get('confidence', base_result.get('confidence'))
                    base_result['entries_intelligence'] = enhanced_analysis.get('entries_intelligence', {})
                    base_result['reasoning_enhanced'] = enhanced_analysis.get('reasoning_enhanced', base_result.get('reasoning'))
                    base_result['intelligence_enabled'] = True
                    
                    print(f"   ✅ {base_result['recommended_bet']} | Confidence: {base_result['confidence']} | ImpliedP: {enhanced_implied_p:.1f}% (Enhanced: {enhanced_analysis.get('entries_intelligence', {}).get('total_adjustment', '+0.0%')})")
                    
                except Exception as e:
                    print(f"   ⚠️  Intelligence enhancement failed: {e}")
                    print(f"   ✅ {base_result['recommended_bet']} | Confidence: {base_result['confidence']} | ImpliedP: {base_implied_p:.1f}% (Base)")
                    base_result['intelligence_enabled'] = False
                    base_result['intelligence_error'] = str(e)
            else:
                base_result['intelligence_enabled'] = False
                print(f"   ✅ {base_result['recommended_bet']} | Confidence: {base_result['confidence']} | ImpliedP: {base_implied_p:.1f}% (Base)")
            
            return base_result
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return {
                'recommended_bet': 'Skip',
                'confidence': 'Low',
                'reasoning': f'Analysis failed: {str(e)}',
                'match_data': match,
                'analyzed_at': datetime.now().isoformat(),
                'error': str(e),
                'intelligence_enabled': False
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
        confidence_rank = {'High': 3, 'Medium': 2, 'Low': 1, 'ELITE': 4}
        min_rank = confidence_rank.get(min_confidence, 2)
        
        high_value = [
            a for a in self.analyses
            if a['recommended_bet'] != 'Skip'
            and confidence_rank.get(a.get('confidence', 'Low'), 0) >= min_rank
            and a.get('expected_value_pct', 0) >= min_ev
        ]
        
        high_value.sort(
            key=lambda x: (
                confidence_rank.get(x.get('confidence', 'Low'), 0),
                x.get('impliedP', 0) if 'impliedP' in x else x.get('win_probability', 0) * 100,
                x.get('expected_value_pct', 0)
            ),
            reverse=True
        )
        
        return high_value

def load_candidates(filename=None):
    """Lataa pre-filterin tulokset"""
    # Check command line argument for filename
    import sys
    if len(sys.argv) > 1 and filename is None:
        filename = sys.argv[1]
    
    if filename is None:
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
        
        if 'original_total' in data:
            print(f"   Original: {data['original_total']} → Optimized: {len(matches)}")
            print(f"   Cost savings: €{(data['original_total'] - len(matches)) * 0.03:.2f}")
        
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
    
    filename.parent.mkdir(parents=True, exist_ok=True)
    
    high_value = analyzer.get_high_value_bets()
    
    # Count intelligence-enhanced bets
    intel_enabled_count = sum(1 for a in analyzer.analyses if a.get('intelligence_enabled', False))
    
    output = {
        'generated_at': datetime.now().isoformat(),
        'model': analyzer.model,
        'intelligence_enabled': analyzer.enable_intelligence,
        'intelligence_enhanced_count': intel_enabled_count,
        'total_analyzed': len(analyzer.analyses),
        'high_value_bets': len(high_value),
        'estimated_cost_eur': len(analyzer.analyses) * 0.03,
        'all_analyses': analyzer.analyses,
        'high_value_bets_detail': high_value
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Results saved to {filename}")
    if analyzer.enable_intelligence:
        print(f"   Intelligence enhanced: {intel_enabled_count}/{len(analyzer.analyses)} matches")
    return high_value

def print_summary(high_value_bets):
    """Tulosta yhteenveto"""
    print(f"\n{'='*80}")
    print(f"🎯 AI ANALYSIS SUMMARY (ENHANCED)")
    print(f"{'='*80}\n")
    
    print(f"🏆 HIGH-VALUE BETTING OPPORTUNITIES: {len(high_value_bets)}\n")
    
    for i, bet in enumerate(high_value_bets, 1):
        match = bet['match_data']
        intel = bet.get('entries_intelligence', {})
        implied_p = bet.get('impliedP', bet.get('win_probability', 0) * 100)
        
        print(f"{i}. {match['player_a']} vs {match['player_b']}")
        print(f"   🎯 Bet: {bet['recommended_bet']} | Confidence: {bet['confidence']}")
        print(f"   💰 Stake: {bet['suggested_stake_pct']}% | EV: +{bet.get('expected_value_pct', 0)}% | ImpliedP: {implied_p:.1f}%")
        if intel:
            print(f"   🧠 Intelligence: {intel.get('total_adjustment', 'N/A')} | Risk: {intel.get('withdrawal_risk', 'N/A')}")
        print(f"   📊 {match['tournament']} | {match['surface']}")
        print(f"   💡 {bet.get('reasoning_enhanced', bet.get('reasoning', ''))[:150]}...")
        print()

if __name__ == '__main__':
    print("📥 Loading pre-filtered candidates...")
    candidates = load_candidates()
    
    print(f"✅ Loaded {len(candidates)} candidates\n")
    
    estimated_cost = len(candidates) * 0.03
    print(f"💰 Estimated API cost: €{estimated_cost:.2f}")
    
    if ENABLE_INTELLIGENCE and ENHANCED_AGENT_AVAILABLE:
        print(f"🧠 Entries intelligence: ENABLED")
    else:
        print(f"🧠 Entries intelligence: DISABLED")
    
    import sys
    if sys.stdin.isatty():
        proceed = input(f"\nProceed with AI analysis of {len(candidates)} matches? (y/n): ")
        if proceed.lower() != 'y':
            print("❌ Aborted")
            exit()
    else:
        print(f"\n✅ Proceeding automatically (non-interactive mode)")
    
    print("\n🤖 Starting AI analysis (enhanced)...\n")
    
    analyzer = TennisAIAnalyzerEnhanced(OPENAI_API_KEY, model=MODEL, enable_intelligence=ENABLE_INTELLIGENCE)
    results = analyzer.analyze_batch(candidates)
    
    high_value_bets = save_results(analyzer)
    print_summary(high_value_bets)
    
    print(f"\n✅ Analysis complete!")
    print(f"\n📋 Next: python3 scripts/tennis_ai/generate_bet_list.py")

