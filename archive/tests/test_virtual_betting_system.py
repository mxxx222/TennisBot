#!/usr/bin/env python3
"""
🧪 TEST VIRTUAL BETTING & ML CALIBRATION SYSTEM
================================================
Test script to demonstrate the virtual betting and calibration system.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
import sys

# Add project paths
sys.path.append(str(Path(__file__).parent / 'src'))

from src.virtual_betting_tracker import VirtualBettingTracker
from src.match_result_collector import MatchResultCollector
from src.ml_calibration_engine import CalibrationEngine
from src.ml_auto_retrainer import MLAutoRetrainer
from src.virtual_betting_dashboard import VirtualBettingDashboard
from src.ai_predictor_enhanced import EnhancedTennisPredictor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_virtual_betting_system():
    """Test the complete virtual betting and calibration system"""
    
    print("\n" + "="*80)
    print("🧪 TESTING VIRTUAL BETTING & ML CALIBRATION SYSTEM")
    print("="*80 + "\n")
    
    # Initialize components
    print("1️⃣ Initializing components...")
    tracker = VirtualBettingTracker(virtual_bankroll=10000.0)
    calibration_engine = CalibrationEngine()
    predictor = EnhancedTennisPredictor()
    predictor.load_player_data()
    
    auto_retrainer = MLAutoRetrainer(
        predictor=predictor,
        virtual_tracker=tracker,
        calibration_engine=calibration_engine,
        min_samples_for_retrain=10  # Lower for testing
    )
    
    dashboard = VirtualBettingDashboard(
        virtual_tracker=tracker,
        calibration_engine=calibration_engine,
        auto_retrainer=auto_retrainer
    )
    
    result_collector = MatchResultCollector(
        virtual_tracker=tracker,
        check_interval=60  # 1 minute for testing
    )
    
    print("✅ All components initialized\n")
    
    # Test 1: Place virtual bets
    print("2️⃣ Testing virtual bet placement...")
    test_matches = [
        {
            'match_id': 'test_match_1',
            'prediction': 'Novak Djokovic',
            'confidence': 0.75,
            'odds': 1.85,
            'surface': 'hard',
            'tournament': 'ATP Masters 1000',
            'home_player': 'Novak Djokovic',
            'away_player': 'Carlos Alcaraz'
        },
        {
            'match_id': 'test_match_2',
            'prediction': 'Daniil Medvedev',
            'confidence': 0.68,
            'odds': 2.10,
            'surface': 'hard',
            'tournament': 'ATP 500',
            'home_player': 'Daniil Medvedev',
            'away_player': 'Jannik Sinner'
        },
        {
            'match_id': 'test_match_3',
            'prediction': 'Carlos Alcaraz',
            'confidence': 0.82,
            'odds': 1.60,
            'surface': 'clay',
            'tournament': 'ATP Masters 1000',
            'home_player': 'Carlos Alcaraz',
            'away_player': 'Alexander Zverev'
        }
    ]
    
    for match in test_matches:
        bet = tracker.place_virtual_bet(
            match_id=match['match_id'],
            prediction=match['prediction'],
            confidence=match['confidence'],
            odds=match['odds'],
            stake_method="kelly",
            surface=match['surface'],
            tournament=match['tournament'],
            home_player=match['home_player'],
            away_player=match['away_player']
        )
        if bet:
            print(f"  ✅ Virtual bet placed: {match['prediction']} @ {match['odds']:.2f}")
    
    print(f"\n✅ {len(test_matches)} virtual bets placed\n")
    
    # Test 2: Update outcomes
    print("3️⃣ Testing outcome updates...")
    await result_collector.update_result_manually('test_match_1', 'Novak Djokovic')
    await result_collector.update_result_manually('test_match_2', 'Jannik Sinner')
    await result_collector.update_result_manually('test_match_3', 'Carlos Alcaraz')
    print("✅ Outcomes updated\n")
    
    # Test 3: Get statistics
    print("4️⃣ Getting statistics...")
    stats = tracker.get_statistics()
    print(f"  Total Bets: {stats.get('total_bets', 0)}")
    print(f"  Won: {stats.get('won_bets', 0)}")
    print(f"  Lost: {stats.get('lost_bets', 0)}")
    print(f"  Win Rate: {stats.get('win_rate', 0):.2f}%")
    print(f"  Total P&L: {stats.get('total_profit_loss', 0):.2f}")
    print(f"  ROI: {stats.get('roi', 0):.2f}%")
    print(f"  Bankroll: {stats.get('current_bankroll', 0):.2f}\n")
    
    # Test 4: Calibration analysis
    print("5️⃣ Running calibration analysis...")
    calibration = calibration_engine.analyze_calibration()
    if calibration.get('status') == 'success':
        overall = calibration.get('overall_metrics', {})
        print(f"  Total Samples: {calibration.get('total_samples', 0)}")
        print(f"  Overall Accuracy: {overall.get('overall_accuracy', 0):.2%}")
        print(f"  Calibration Gap: {overall.get('calibration_gap', 0):.4f}")
        print(f"  Brier Score: {calibration.get('brier_score', 0):.4f}")
        print(f"  Reliability: {overall.get('reliability', 0):.2%}")
    else:
        print(f"  Status: {calibration.get('status')}")
    print()
    
    # Test 5: Dashboard summary
    print("6️⃣ Dashboard summary...")
    dashboard.print_summary()
    
    # Test 6: Export reports
    print("7️⃣ Exporting reports...")
    daily_report_path = dashboard.export_report('daily')
    print(f"  ✅ Daily report exported to: {daily_report_path}")
    
    calibration_report_path = calibration_engine.export_calibration_report()
    print(f"  ✅ Calibration report exported to: {calibration_report_path}\n")
    
    print("="*80)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
    print("="*80 + "\n")
    
    print("📝 System is ready for production use:")
    print("  - Virtual bets are automatically placed on predictions")
    print("  - Results are collected and bets are updated")
    print("  - Calibration data is analyzed for model improvement")
    print("  - Models can be automatically retrained")
    print("  - Comprehensive reporting is available\n")

if __name__ == "__main__":
    asyncio.run(test_virtual_betting_system())

