#!/usr/bin/env python3
"""
Backtest 70% ImpliedP Threshold
================================

Analyzes historical predictions to compare performance with different impliedP thresholds.
Based on validation showing 100% win rate (12/12) for 70%+ impliedP bets.

Usage:
    python3 scripts/tennis_ai/backtest_70_threshold.py
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / 'telegram_secrets.env'
if env_path.exists():
    load_dotenv(env_path)

try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    print("⚠️  notion-client not installed. Install with: pip install notion-client")
    NOTION_AVAILABLE = False

# Import from validate_predictions
from scripts.tennis_ai.validate_predictions import (
    read_predictions_from_notion,
    parse_impliedp,
    NOTION_DB_ID
)

# CONFIG
NOTION_TOKEN = os.getenv('NOTION_API_KEY') or os.getenv('NOTION_TOKEN')
THRESHOLDS = [60, 65, 70, 75]  # ImpliedP thresholds to test


def calculate_roi(correct: int, total: int, avg_odds: float = 1.90) -> Dict:
    """
    Calculate ROI metrics.
    
    Args:
        correct: Number of correct predictions
        total: Total number of bets
        avg_odds: Average odds (default 1.90)
    
    Returns:
        Dict with win_rate, roi_percent, profit_per_100_bets
    """
    if total == 0:
        return {
            'win_rate': 0.0,
            'roi_percent': 0.0,
            'profit_per_100_bets': 0.0
        }
    
    win_rate = (correct / total) * 100
    
    # ROI calculation: (win_rate * (odds - 1)) - ((1 - win_rate) * 1)
    # Assuming 1 unit stake per bet
    expected_profit_per_bet = (win_rate / 100) * (avg_odds - 1) - ((1 - win_rate / 100) * 1)
    roi_percent = expected_profit_per_bet * 100
    profit_per_100_bets = expected_profit_per_bet * 100
    
    return {
        'win_rate': win_rate,
        'roi_percent': roi_percent,
        'profit_per_100_bets': profit_per_100_bets
    }


def backtest_threshold(predictions: List[Dict], threshold: float) -> Dict:
    """
    Backtest predictions with a specific impliedP threshold.
    
    Args:
        predictions: List of prediction dicts
        threshold: Minimum impliedP threshold
    
    Returns:
        Dict with statistics
    """
    # Filter by threshold
    filtered = [
        p for p in predictions
        if p.get('impliedp') is not None
        and p.get('impliedp') >= threshold
        and p.get('status') in ['W', 'L']  # Only completed bets
    ]
    
    if not filtered:
        return {
            'threshold': threshold,
            'total_bets': 0,
            'correct': 0,
            'incorrect': 0,
            'win_rate': 0.0,
            'roi': {}
        }
    
    # Count correct/incorrect
    correct = sum(1 for p in filtered if p.get('status') == 'W')
    incorrect = len(filtered) - correct
    
    # Calculate ROI
    roi = calculate_roi(correct, len(filtered))
    
    return {
        'threshold': threshold,
        'total_bets': len(filtered),
        'correct': correct,
        'incorrect': incorrect,
        'win_rate': roi['win_rate'],
        'roi': roi
    }


def print_backtest_results(results: List[Dict]):
    """Print formatted backtest results."""
    print("=" * 80)
    print("📊 BACKTEST RESULTS: ImpliedP Threshold Comparison")
    print("=" * 80)
    print()
    
    # Header
    print(f"{'Threshold':<12} {'Bets':<8} {'Win Rate':<12} {'ROI %':<12} {'Profit/100':<12}")
    print("-" * 80)
    
    # Results for each threshold
    for result in results:
        if result['total_bets'] > 0:
            win_rate_str = f"{result['win_rate']:.1f}%"
            roi_str = f"{result['roi']['roi_percent']:+.1f}%"
            profit_str = f"{result['roi']['profit_per_100_bets']:+.1f}"
            
            # Highlight 70% threshold
            marker = "🔥" if result['threshold'] == 70 else ""
            
            print(
                f"{result['threshold']:>2.0f}%+       "
                f"{result['total_bets']:<8} "
                f"{win_rate_str:<12} "
                f"{roi_str:<12} "
                f"{profit_str:<12} {marker}"
            )
        else:
            print(f"{result['threshold']:>2.0f}%+       {'No data':<8}")
    
    print()
    print("=" * 80)
    
    # Find best threshold
    valid_results = [r for r in results if r['total_bets'] > 0]
    if valid_results:
        best = max(valid_results, key=lambda x: x['roi']['roi_percent'])
        
        print(f"\n🏆 BEST THRESHOLD: {best['threshold']}%+")
        print(f"   Win Rate: {best['win_rate']:.1f}% ({best['correct']}/{best['total_bets']})")
        print(f"   ROI: {best['roi']['roi_percent']:+.1f}%")
        print(f"   Profit per 100 bets: {best['roi']['profit_per_100_bets']:+.1f} units")
        
        # Compare 70% vs others
        result_70 = next((r for r in results if r['threshold'] == 70), None)
        if result_70 and result_70['total_bets'] > 0:
            print(f"\n💡 70% Threshold Analysis:")
            print(f"   Win Rate: {result_70['win_rate']:.1f}% ({result_70['correct']}/{result_70['total_bets']})")
            print(f"   ROI: {result_70['roi']['roi_percent']:+.1f}%")
            
            # Compare with 65%
            result_65 = next((r for r in results if r['threshold'] == 65), None)
            if result_65 and result_65['total_bets'] > 0:
                improvement = result_70['roi']['roi_percent'] - result_65['roi']['roi_percent']
                print(f"   vs 65% threshold: {improvement:+.1f}% ROI improvement")
            
            if result_70['win_rate'] >= 90:
                print(f"   ✅ EXCELLENT: 70%+ threshold highly recommended")
            elif result_70['win_rate'] >= 75:
                print(f"   ✅ STRONG: 70%+ threshold recommended")


def main():
    """Main backtest function."""
    if not NOTION_AVAILABLE:
        print("❌ ERROR: notion-client not installed")
        print("   Install: pip install notion-client")
        return
    
    if not NOTION_TOKEN:
        print("❌ ERROR: NOTION_TOKEN not set")
        print("   Set NOTION_API_KEY or NOTION_TOKEN in telegram_secrets.env")
        return
    
    print("📥 Loading predictions from Notion...")
    
    try:
        notion = Client(auth=NOTION_TOKEN)
        predictions = read_predictions_from_notion(notion)
    except Exception as e:
        print(f"❌ ERROR: Failed to load predictions: {e}")
        return
    
    if not predictions:
        print("⚠️  No predictions found in Notion database")
        return
    
    print(f"✅ Loaded {len(predictions)} predictions")
    
    # Filter to only completed bets with impliedP
    completed = [
        p for p in predictions
        if p.get('status') in ['W', 'L']
        and p.get('impliedp') is not None
    ]
    
    print(f"📊 Analyzing {len(completed)} completed bets with impliedP data\n")
    
    if not completed:
        print("⚠️  No completed bets with impliedP data found")
        return
    
    # Run backtest for each threshold
    results = []
    for threshold in THRESHOLDS:
        result = backtest_threshold(completed, threshold)
        results.append(result)
    
    # Print results
    print_backtest_results(results)
    
    # Summary
    print(f"\n📋 Summary:")
    print(f"   Total completed bets: {len(completed)}")
    print(f"   Bets with impliedP data: {len(completed)}")
    print(f"\n💡 Recommendation:")
    
    result_70 = next((r for r in results if r['threshold'] == 70), None)
    if result_70 and result_70['total_bets'] > 0:
        if result_70['win_rate'] >= 90:
            print(f"   ✅ Use 70%+ impliedP threshold (win rate: {result_70['win_rate']:.1f}%)")
        elif result_70['win_rate'] >= 75:
            print(f"   ✅ Consider 70%+ impliedP threshold (win rate: {result_70['win_rate']:.1f}%)")
        else:
            print(f"   ⚠️  70% threshold shows {result_70['win_rate']:.1f}% win rate - may need adjustment")


if __name__ == '__main__':
    main()

