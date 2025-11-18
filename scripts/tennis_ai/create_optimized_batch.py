#!/usr/bin/env python3
"""
Create optimized batch (top 20-30 matches) from pre-filter results.
This reduces costs by 70% while maintaining quality.
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# CONFIG
INPUT_FILE = project_root / 'data' / 'tennis_ai' / 'ai_candidates.json'
OUTPUT_FILE = project_root / 'data' / 'tennis_ai' / 'ai_candidates_optimized.json'
TOP_N = 25  # Number of top matches to analyze

def create_optimized_batch():
    """Create optimized batch with top N matches"""
    
    if not INPUT_FILE.exists():
        print(f"❌ ERROR: {INPUT_FILE} not found")
        print("   Run prefilter_w15_matches.py first")
        return False
    
    # Load all candidates
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    matches = data.get('matches', [])
    
    if not matches:
        print("⚠️  No matches found in candidates file")
        return False
    
    # Sort by score (already sorted, but ensure)
    matches_sorted = sorted(matches, key=lambda x: x.get('score', 0), reverse=True)
    
    # Take top N
    top_matches = matches_sorted[:TOP_N]
    
    # Create optimized data
    optimized_data = {
        'generated_at': data.get('generated_at'),
        'total_candidates': len(top_matches),
        'original_total': len(matches),
        'min_score': data.get('min_score'),
        'top_n': TOP_N,
        'matches': top_matches
    }
    
    # Save optimized batch
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(optimized_data, f, indent=2, ensure_ascii=False)
    
    # Calculate savings
    original_cost = len(matches) * 0.03
    optimized_cost = len(top_matches) * 0.03
    savings = original_cost - optimized_cost
    savings_pct = (savings / original_cost * 100) if original_cost > 0 else 0
    
    print("🎯 OPTIMIZED BATCH CREATED")
    print("=" * 70)
    print(f"📊 Statistics:")
    print(f"   Original matches: {len(matches)}")
    print(f"   Optimized batch: {len(top_matches)} (top {TOP_N})")
    reduction = len(matches) - len(top_matches)
    reduction_pct = 100 - (len(top_matches)/len(matches)*100)
    print(f"   Reduction: {reduction} matches ({reduction_pct:.1f}%)")
    print(f"\n💰 Cost Analysis:")
    print(f"   Original cost: ${original_cost:.2f}")
    print(f"   Optimized cost: ${optimized_cost:.2f}")
    print(f"   Savings: ${savings:.2f} ({savings_pct:.1f}%)")
    print(f"\n📁 Saved to: {OUTPUT_FILE}")
    print(f"\n✅ Ready for AI analysis!")
    print(f"   Run: python3 scripts/tennis_ai/ai_analyzer.py")
    print(f"   (ai_analyzer.py will automatically use optimized batch if available)")
    
    return True

if __name__ == '__main__':
    create_optimized_batch()

