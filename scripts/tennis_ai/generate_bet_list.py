#!/usr/bin/env python3
"""
Generate Human-Readable Bet List
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

def load_results(filename=None):
    if filename is None:
        filename = project_root / 'data' / 'tennis_ai' / 'ai_analysis_results.json'
    else:
        filename = Path(filename)
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ ERROR: {filename} not found")
        print("   Run ai_analyzer.py first")
        exit(1)

def generate_bet_list(data):
    bets = data['high_value_bets_detail']
    
    output = []
    output.append("🎾 TENNIS AI - BET LIST")
    output.append("="*80)
    output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    output.append(f"Total high-value bets: {len(bets)}")
    output.append(f"Model: {data['model']}")
    output.append(f"API Cost: €{data['estimated_cost_eur']:.2f}")
    output.append("")
    output.append("="*80)
    output.append("")
    
    for i, bet in enumerate(bets, 1):
        match = bet['match_data']
        
        output.append(f"BET #{i}")
        output.append("-" * 80)
        output.append(f"Match:      {match['player_a']} vs {match['player_b']}")
        output.append(f"Tournament: {match['tournament']}")
        output.append(f"Surface:    {match['surface']}")
        output.append(f"Rankings:   {match.get('ranking_a', '?')} vs {match.get('ranking_b', '?')}")
        output.append("")
        output.append(f"✅ RECOMMENDATION: {bet['recommended_bet']}")
        output.append(f"📊 Confidence:     {bet['confidence']}")
        output.append(f"💰 Stake:          {bet['suggested_stake_pct']}% of bankroll")
        output.append(f"📈 Expected Value: +{bet.get('expected_value_pct', 0)}%")
        output.append(f"⚠️  Risk Level:     {bet['risk_level']}")
        output.append("")
        output.append("💡 REASONING:")
        output.append(f"   {bet['reasoning']}")
        output.append("")
        output.append("🎯 KEY FACTORS:")
        for factor in bet.get('key_factors', []):
            output.append(f"   • {factor}")
        output.append("")
        if match.get('page_url'):
            output.append(f"🔗 Notion: {match['page_url']}")
        output.append("")
        output.append("="*80)
        output.append("")
    
    # Summary
    output.append("\n📊 QUICK SUMMARY")
    output.append("="*80)
    output.append(f"{'#':<4} {'Match':<40} {'Bet':<15} {'Conf':<8} {'Stake':<6} {'EV':<6}")
    output.append("-"*80)
    
    for i, bet in enumerate(bets, 1):
        match = bet['match_data']
        match_str = f"{match['player_a'][:18]} vs {match['player_b'][:18]}"
        output.append(
            f"{i:<4} {match_str:<40} {bet['recommended_bet']:<15} "
            f"{bet['confidence']:<8} {bet['suggested_stake_pct']}%    +{bet.get('expected_value_pct', 0)}%"
        )
    
    output.append("="*80)
    
    return "\n".join(output)

if __name__ == '__main__':
    print("📥 Loading AI analysis results...")
    data = load_results()
    
    print("📝 Generating bet list...")
    bet_list = generate_bet_list(data)
    
    output_file = project_root / 'data' / 'tennis_ai' / 'bet_list.txt'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(bet_list)
    
    print(bet_list)
    print(f"\n✅ Saved to {output_file}")

