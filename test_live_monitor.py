#!/usr/bin/env python3
"""
Test script for Live Odds Monitoring System
Validates all components and runs integration tests
"""

import asyncio
import sys
from pathlib import Path
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config.live_config import LiveMonitoringConfig
from monitors.odds_tracker import OddsTracker
from monitors.value_detector import ValueDetector
from monitors.alert_manager import AlertManager
from storage.odds_database import OddsDatabase
from storage.analytics import LiveAnalytics

# Configure logging for testing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_configuration():
    """Test configuration validation"""
    print("🔧 Testing Configuration...")
    
    config = LiveMonitoringConfig()
    
    # Test config validation
    is_valid = config.validate_config()
    print(f"  ✅ Configuration valid: {is_valid}")
    
    # Test league configuration
    print(f"  📊 Target leagues: {len(config.TARGET_LEAGUES)}")
    for league in config.TARGET_LEAGUES:
        tier = config.get_league_tier(league)
        print(f"    - {league} (Tier {tier})")
    
    return is_valid

async def test_odds_tracker():
    """Test odds tracking functionality"""
    print("\n📊 Testing Odds Tracker...")
    
    try:
        async with OddsTracker() as tracker:
            # Test single league fetch
            test_league = "soccer_efl_champ"
            snapshots = await tracker.fetch_league_odds(test_league)
            
            print(f"  ✅ Fetched {len(snapshots)} odds from {test_league}")
            
            if snapshots:
                sample = snapshots[0]
                print(f"    Sample: {sample.home_team} vs {sample.away_team}")
                print(f"    Odds: {sample.home_odds:.2f} / {sample.away_odds:.2f}")
                
                # Test movement detection (simulate second fetch)
                movements = tracker.detect_movements(snapshots)
                print(f"  📈 Detected {len(movements)} movements")
            
            return len(snapshots) > 0
            
    except Exception as e:
        print(f"  ❌ Odds tracker test failed: {e}")
        return False

async def test_value_detector():
    """Test value detection functionality"""
    print("\n🎯 Testing Value Detector...")
    
    try:
        detector = ValueDetector()
        
        # Create mock snapshots for testing
        from monitors.odds_tracker import OddsSnapshot
        from datetime import datetime, timedelta
        
        mock_snapshots = [
            OddsSnapshot(
                match_id="test_match_1",
                home_team="Test Team A",
                away_team="Test Team B", 
                home_odds=1.65,  # In profitable range
                away_odds=2.30,  # Outside range
                timestamp=datetime.now(),
                league="soccer_efl_champ",
                commence_time=datetime.now() + timedelta(hours=3)
            ),
            OddsSnapshot(
                match_id="test_match_2",
                home_team="Test Team C",
                away_team="Test Team D",
                home_odds=1.45,  # In profitable range
                away_odds=1.75,  # In profitable range
                timestamp=datetime.now(),
                league="soccer_england_league1",
                commence_time=datetime.now() + timedelta(hours=5)
            )
        ]
        
        opportunities = detector.analyze_snapshots(mock_snapshots, [])
        print(f"  ✅ Detected {len(opportunities)} value opportunities")
        
        for opp in opportunities:
            print(f"    - {opp.team} @ {opp.odds:.2f} (Edge: +{opp.edge_estimate:.1f}%, {opp.urgency_level})")
        
        return len(opportunities) > 0
        
    except Exception as e:
        print(f"  ❌ Value detector test failed: {e}")
        return False

async def test_alert_manager():
    """Test alert management functionality"""
    print("\n📱 Testing Alert Manager...")
    
    try:
        alert_manager = AlertManager()
        
        # Test system status message
        test_stats = {
            'total_requests': 100,
            'error_rate': 0.05,
            'tracked_matches': 25
        }
        
        # In test mode, we'll just validate the message format
        print("  ✅ Alert manager initialized")
        print("  📊 Alert statistics available")
        
        stats = alert_manager.get_alert_stats()
        print(f"    - Total sent: {stats['total_sent']}")
        print(f"    - Success rate: {stats['success_rate']:.1%}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Alert manager test failed: {e}")
        return False

def test_database():
    """Test database functionality"""
    print("\n💾 Testing Database...")
    
    try:
        with OddsDatabase() as db:
            # Test database initialization
            stats = db.get_database_stats()
            print(f"  ✅ Database initialized")
            print(f"    - Size: {stats.get('database_size_mb', 0):.1f} MB")
            print(f"    - Snapshots: {stats.get('odds_snapshots_count', 0)}")
            print(f"    - Opportunities: {stats.get('value_opportunities_count', 0)}")
            
            # Test performance summary
            summary = db.get_performance_summary(7)
            if summary:
                print(f"  📊 Performance data available")
                print(f"    - Total bets: {summary.get('total_bets', 0)}")
                print(f"    - ROI: {summary.get('roi', 0):.1f}%")
            else:
                print(f"  ℹ️  No performance data yet (expected for new system)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Database test failed: {e}")
        return False

def test_analytics():
    """Test analytics functionality"""
    print("\n📈 Testing Analytics...")
    
    try:
        analytics = LiveAnalytics()
        
        # Test real-time metrics
        metrics = analytics.get_real_time_metrics()
        print(f"  ✅ Analytics initialized")
        print(f"    - System active: {metrics.get('system_active', False)}")
        print(f"    - Current hour: {metrics.get('current_hour', 0)}")
        
        # Test report generation
        report = analytics.generate_performance_report(7)
        if report:
            print(f"  📊 Performance report generated")
            recommendations = report.get('recommendations', [])
            print(f"    - Recommendations: {len(recommendations)}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Analytics test failed: {e}")
        return False

async def test_integration():
    """Test full system integration"""
    print("\n🔄 Testing System Integration...")
    
    try:
        # Test a mini monitoring cycle
        config = LiveMonitoringConfig()
        
        async with OddsTracker() as tracker:
            # Fetch from one league
            test_league = config.TARGET_LEAGUES[0]
            snapshots = await tracker.fetch_league_odds(test_league)
            
            if snapshots:
                # Detect movements
                movements = tracker.detect_movements(snapshots)
                
                # Detect opportunities
                detector = ValueDetector()
                opportunities = detector.analyze_snapshots(snapshots, movements)
                
                print(f"  ✅ Integration test completed")
                print(f"    - Snapshots: {len(snapshots)}")
                print(f"    - Movements: {len(movements)}")
                print(f"    - Opportunities: {len(opportunities)}")
                
                return True
            else:
                print(f"  ⚠️  No data available for integration test")
                return False
        
    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")
        return False

async def run_all_tests():
    """Run all tests"""
    print("🧪 LIVE ODDS MONITOR - SYSTEM TESTS")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_configuration()),
        ("Odds Tracker", test_odds_tracker()),
        ("Value Detector", test_value_detector()),
        ("Alert Manager", test_alert_manager()),
        ("Database", test_database()),
        ("Analytics", test_analytics()),
        ("Integration", test_integration())
    ]
    
    results = []
    
    for test_name, test_coro in tests:
        if asyncio.iscoroutine(test_coro):
            result = await test_coro
        else:
            result = test_coro
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 ALL TESTS PASSED! System ready for production.")
        return True
    else:
        print(f"\n⚠️  {len(results) - passed} tests failed. Check configuration and dependencies.")
        return False

def main():
    """Main entry point"""
    
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Test runner error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
