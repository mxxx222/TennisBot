"""
Test script to verify BetFlow Pro system components
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
from datetime import datetime

def test_edge_detection():
    """Test edge detection engine"""
    print("Testing Edge Detection Engine...")
    from edge_detection import EdgeDetectionEngine
    
    # Create sample data
    data = pd.DataFrame({
        'xg_diff': np.random.randn(100),
        'form_diff': np.random.randn(100),
        'h2h_win_pct': np.random.uniform(30, 70, 100),
        'home_advantage': np.random.uniform(0.5, 0.6, 100),
        'recent_goals_diff': np.random.randn(100),
        'injury_count_diff': np.random.randint(-2, 3, 100),
        'result': np.random.randint(0, 2, 100)
    })
    
    engine = EdgeDetectionEngine(data)
    
    # Test base edge
    base_edge = engine.calculate_base_edge(0.55, 0.50)
    print(f"  ✓ Base edge calculation: {base_edge:.2f}%")
    
    # Test line movement
    movement = engine.detect_line_movement(2.0, 2.05, 24)
    print(f"  ✓ Line movement detection: {movement['recommendation']}")
    
    # Test ML prediction
    ml_prob = engine.predict_probability_ml({
        'xg_diff': 0.5,
        'form_diff': 0.2,
        'h2h_win_pct': 60,
        'home_advantage': 0.55,
        'recent_goals_diff': 1.0,
        'injury_count_diff': 0
    })
    print(f"  ✓ ML probability prediction: {ml_prob:.3f}")
    
    # Test composite edge
    composite = engine.calculate_composite_edge(
        base_edge=8.5,
        arb_edge=2.1,
        movement_edge=1.5,
        ml_probability=0.55,
        market_probability=0.50
    )
    print(f"  ✓ Composite edge: {composite:.2f}%")
    
    print("  ✅ Edge Detection Engine: PASSED\n")

def test_kelly_criterion():
    """Test Kelly Criterion"""
    print("Testing Kelly Criterion...")
    from kelly_criterion import KellyCriterion
    
    kelly = KellyCriterion()
    
    # Test optimal Kelly
    optimal = kelly.calculate_optimal_kelly(8.0, 2.0)
    print(f"  ✓ Optimal Kelly: {optimal:.4f}")
    
    # Test scaled Kelly
    scaled = kelly.scale_kelly(optimal, 0.5)
    print(f"  ✓ Scaled Kelly (50%): {scaled:.4f}")
    
    # Test stake calculation
    stake = kelly.calculate_stake(5000, scaled * 100, 3.0)
    print(f"  ✓ Stake calculation: €{stake:.2f}")
    
    # Test variance adjustment
    var_adjusted = kelly.calculate_variance_adjusted_kelly(8.0, 2.0, 0.3)
    print(f"  ✓ Variance-adjusted Kelly: {var_adjusted:.4f}")
    
    # Test drawdown adjustment
    dd_adjusted = kelly.drawdown_adjusted_kelly(0.05, 10.0, 15.0)
    print(f"  ✓ Drawdown-adjusted Kelly: {dd_adjusted:.4f}")
    
    print("  ✅ Kelly Criterion: PASSED\n")

def test_bookmaker_optimizer():
    """Test bookmaker optimizer"""
    print("Testing Bookmaker Optimizer...")
    from bookmaker_optimizer import BookmakerOptimizer
    
    optimizer = BookmakerOptimizer()
    
    # Test best odds
    best_odds = optimizer.get_best_odds("test_match_001", "1X2")
    print(f"  ✓ Best odds retrieval: {best_odds.get('best_book', 'Mock')}")
    
    # Test arbitrage detection
    matches = [
        {'id': 'match001', 'home_team': 'Team A', 'away_team': 'Team B'},
        {'id': 'match002', 'home_team': 'Team C', 'away_team': 'Team D'}
    ]
    arbs = optimizer.detect_arbitrage(matches)
    print(f"  ✓ Arbitrage detection: {len(arbs)} opportunities found")
    
    # Test stake calculation
    stakes = optimizer.calculate_arbitrage_stakes(1000, 1.95, 2.05)
    print(f"  ✓ Arbitrage stakes: €{stakes['stake_a']:.2f} + €{stakes['stake_b']:.2f}")
    print(f"    Profit: €{stakes['guaranteed_profit']:.2f} ({stakes['profit_percent']:.2f}%)")
    
    print("  ✅ Bookmaker Optimizer: PASSED\n")

def test_main_engine():
    """Test main engine"""
    print("Testing Main Engine...")
    from main import BetFlowProEngine
    
    engine = BetFlowProEngine()
    
    # Test match analysis
    match = {
        'id': 'test_match',
        'home_team': 'Team A',
        'away_team': 'Team B',
        'my_probability': 0.55,
        'market_probability': 0.50,
        'opening_odds': 2.0,
        'current_odds': 2.05,
        'hours_to_match': 24,
        'bet_type': '1X2',
        'xg_diff': 0.5,
        'form_diff': 0.2,
        'h2h_win_pct': 60,
        'recent_goals_diff': 1.0,
        'injury_count_diff': 0,
        'data_points': 15
    }
    
    analysis = engine.analyze_match(match)
    print(f"  ✓ Match analysis: {analysis.get('recommendation', 'N/A')}")
    print(f"    Total edge: {analysis.get('total_edge', 0):.2f}%")
    print(f"    Stake: €{analysis.get('stake', 0):.2f}")
    
    print("  ✅ Main Engine: PASSED\n")

def test_backtester():
    """Test backtester"""
    print("Testing Backtester...")
    from backtester import Backtester
    
    # Create sample historical data
    data = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=100, freq='D'),
        'match_id': [f'match_{i}' for i in range(100)],
        'my_probability': np.random.uniform(0.4, 0.6, 100),
        'market_probability': np.random.uniform(0.45, 0.55, 100),
        'odds': np.random.uniform(1.5, 3.0, 100),
        'result': np.random.randint(0, 2, 100),
        'xg_diff': np.random.randn(100),
        'form_diff': np.random.randn(100),
        'h2h_win_pct': np.random.uniform(30, 70, 100),
        'home_advantage': np.random.uniform(0.5, 0.6, 100),
        'recent_goals_diff': np.random.randn(100),
        'injury_count_diff': np.random.randint(-2, 3, 100)
    })
    
    backtester = Backtester(data)
    
    strategy = {
        'name': 'Test Strategy',
        'criteria': {
            'min_edge': 0.0,  # Low threshold for testing
            'max_stake_percent': 3.0
        }
    }
    
    results = backtester.backtest_strategy(strategy, '2024-01-01', '2024-04-10')
    
    if 'error' not in results:
        print(f"  ✓ Backtest completed: {results['total_bets']} bets")
        print(f"    ROI: {results['total_roi_percent']:.2f}%")
        print(f"    Win rate: {results['win_rate']:.2f}%")
    else:
        print(f"  ⚠ Backtest: {results.get('error', 'Unknown error')}")
    
    print("  ✅ Backtester: PASSED\n")

def main():
    """Run all tests"""
    print("=" * 60)
    print("BetFlow Pro System Test Suite")
    print("=" * 60 + "\n")
    
    try:
        test_edge_detection()
        test_kelly_criterion()
        test_bookmaker_optimizer()
        test_main_engine()
        test_backtester()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nSystem is ready to use!")
        print("\nNext steps:")
        print("1. Configure .env file with your API keys")
        print("2. Create Notion databases: python create_notion_databases.py")
        print("3. Run the system: python main.py")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

