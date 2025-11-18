#!/usr/bin/env python3
"""
🔬 QUICK BOT RELIABILITY TEST
============================
Fast and comprehensive test to evaluate bot reliability
"""

import asyncio
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project paths
sys.path.append(str(Path(__file__).parent / 'src'))

async def quick_reliability_test():
    """Quick comprehensive reliability test"""
    
    print("🔬 QUICK BOT RELIABILITY TEST")
    print("=" * 50)
    
    test_results = []
    start_time = time.time()
    
    # Load secrets
    try:
        import subprocess
        result = subprocess.run(['python3', 'simple_secrets.py', 'load'], 
                              capture_output=True, text=True, cwd=str(Path(__file__).parent))
        if result.returncode == 0:
            print("✅ Secrets loaded successfully")
            test_results.append(("Secret Loading", True, "Loaded successfully"))
        else:
            print("⚠️ Warning: Could not load secrets")
            test_results.append(("Secret Loading", False, "Could not load secrets"))
    except Exception as e:
        print(f"❌ Error loading secrets: {e}")
        test_results.append(("Secret Loading", False, str(e)))
    
    # Test 1: Component Initialization
    print(f"\n🔧 Test 1: Component Initialization")
    print("-" * 40)
    
    components = []
    
    try:
        from telegram_minute_scanner import TelegramMinuteScanner
        scanner = TelegramMinuteScanner()
        components.append(("Minute Scanner", True, "Initialized successfully"))
        print("   ✅ Minute Scanner: PASS")
    except Exception as e:
        components.append(("Minute Scanner", False, str(e)))
        print(f"   ❌ Minute Scanner: FAIL - {e}")
    
    try:
        from enhanced_telegram_roi_bot import EnhancedTelegramROIBot
        telegram_bot = EnhancedTelegramROIBot()
        components.append(("Telegram Bot", True, f"Demo mode: {telegram_bot.demo_mode}"))
        print(f"   ✅ Telegram Bot: PASS (Demo: {telegram_bot.demo_mode})")
    except Exception as e:
        components.append(("Telegram Bot", False, str(e)))
        print(f"   ❌ Telegram Bot: FAIL - {e}")
    
    try:
        from betfury_integration import BetfuryIntegration
        betfury = BetfuryIntegration(affiliate_code="reliability_test")
        components.append(("Betfury Integration", True, "Initialized successfully"))
        print("   ✅ Betfury Integration: PASS")
    except Exception as e:
        components.append(("Betfury Integration", False, str(e)))
        print(f"   ❌ Betfury Integration: FAIL - {e}")
    
    try:
        from odds_api_integration import OddsAPIIntegration
        odds_api = OddsAPIIntegration()
        stats = odds_api.get_api_usage_stats()
        components.append(("Odds API", True, f"Usage: {stats['usage_percentage']:.1f}%"))
        print(f"   ✅ Odds API: PASS (Usage: {stats['usage_percentage']:.1f}%)")
    except Exception as e:
        components.append(("Odds API", False, str(e)))
        print(f"   ❌ Odds API: FAIL - {e}")
    
    test_results.extend(components)
    
    # Test 2: Data Processing
    print(f"\n📊 Test 2: Data Processing")
    print("-" * 40)
    
    try:
        # Test opportunity creation
        from telegram_minute_scanner import QuickOpportunity
        
        test_opportunity = QuickOpportunity(
            match_id="reliability_test",
            home_team="Test Team A",
            away_team="Test Team B",
            sport="football",
            league="Test League",
            roi_percentage=15.8,
            confidence_score=0.72,
            recommended_stake=3.5,
            potential_profit=420.0,
            odds=2.25,
            market="match_winner",
            selection="Test Team A",
            betfury_link="https://betfury.io/test",
            expires_at=datetime.now() + timedelta(hours=2),
            discovered_at=datetime.now()
        )
        
        print("   ✅ Opportunity Creation: PASS")
        test_results.append(("Opportunity Creation", True, "Created successfully"))
        
        # Test message creation
        if 'scanner' in locals():
            message = scanner._create_opportunity_message(test_opportunity)
            message_valid = len(message) > 100 and 'ROI:' in message and 'BETFURY.IO' in message
            
            if message_valid:
                print(f"   ✅ Message Creation: PASS (Length: {len(message)})")
                test_results.append(("Message Creation", True, f"Length: {len(message)}"))
            else:
                print(f"   ❌ Message Creation: FAIL (Invalid message)")
                test_results.append(("Message Creation", False, "Invalid message"))
        
    except Exception as e:
        print(f"   ❌ Data Processing: FAIL - {e}")
        test_results.append(("Data Processing", False, str(e)))
    
    # Test 3: Betfury Link Generation
    print(f"\n🎰 Test 3: Betfury Link Generation")
    print("-" * 40)
    
    try:
        if 'betfury' in locals():
            test_matches = [
                ("Real Madrid", "Barcelona", "football", "La Liga"),
                ("Novak Djokovic", "Rafael Nadal", "tennis", "ATP Masters")
            ]
            
            link_tests = []
            for home, away, sport, league in test_matches:
                try:
                    link = betfury.generate_match_link(home, away, sport, league)
                    valid = link and 'betfury.io' in link and 'reliability_test' in link
                    
                    if valid:
                        print(f"   ✅ {home} vs {away}: PASS")
                        link_tests.append(True)
                    else:
                        print(f"   ❌ {home} vs {away}: FAIL (Invalid link)")
                        link_tests.append(False)
                        
                except Exception as e:
                    print(f"   ❌ {home} vs {away}: FAIL - {e}")
                    link_tests.append(False)
            
            success_rate = sum(link_tests) / len(link_tests) if link_tests else 0
            test_results.append(("Betfury Links", success_rate >= 0.8, f"Success rate: {success_rate:.1%}"))
            
    except Exception as e:
        print(f"   ❌ Betfury Link Generation: FAIL - {e}")
        test_results.append(("Betfury Links", False, str(e)))
    
    # Test 4: Performance Test
    print(f"\n⚡ Test 4: Performance Test")
    print("-" * 40)
    
    try:
        if 'scanner' in locals():
            # Test scanning performance
            scan_times = []
            for i in range(5):
                scan_start = time.time()
                opportunities = await scanner._scan_for_opportunities()
                scan_time = time.time() - scan_start
                scan_times.append(scan_time)
            
            avg_scan_time = sum(scan_times) / len(scan_times)
            performance_good = avg_scan_time < 10.0  # 10 seconds max
            
            if performance_good:
                print(f"   ✅ Scan Performance: PASS (Avg: {avg_scan_time:.2f}s)")
                test_results.append(("Scan Performance", True, f"Avg: {avg_scan_time:.2f}s"))
            else:
                print(f"   ⚠️ Scan Performance: SLOW (Avg: {avg_scan_time:.2f}s)")
                test_results.append(("Scan Performance", False, f"Too slow: {avg_scan_time:.2f}s"))
                
    except Exception as e:
        print(f"   ❌ Performance Test: FAIL - {e}")
        test_results.append(("Performance Test", False, str(e)))
    
    # Test 5: API Integration
    print(f"\n📡 Test 5: API Integration")
    print("-" * 40)
    
    try:
        if 'odds_api' in locals():
            # Test API call
            api_start = time.time()
            live_odds = await odds_api.get_live_odds(['soccer_epl'], ['h2h'])
            api_time = time.time() - api_start
            
            api_working = api_time < 30.0  # 30 seconds max
            
            if api_working:
                print(f"   ✅ API Integration: PASS ({len(live_odds)} matches, {api_time:.2f}s)")
                test_results.append(("API Integration", True, f"{len(live_odds)} matches in {api_time:.2f}s"))
            else:
                print(f"   ⚠️ API Integration: SLOW ({api_time:.2f}s)")
                test_results.append(("API Integration", False, f"Too slow: {api_time:.2f}s"))
                
    except Exception as e:
        print(f"   ❌ API Integration: FAIL - {e}")
        test_results.append(("API Integration", False, str(e)))
    
    # Test 6: Error Handling
    print(f"\n🛡️ Test 6: Error Handling")
    print("-" * 40)
    
    error_handling_tests = []
    
    # Test invalid opportunity data
    try:
        if 'scanner' in locals():
            # Test with invalid data
            invalid_opportunities = []
            filtered = scanner._filter_opportunities(invalid_opportunities)
            
            print("   ✅ Empty Data Handling: PASS")
            error_handling_tests.append(True)
    except Exception as e:
        print(f"   ❌ Empty Data Handling: FAIL - {e}")
        error_handling_tests.append(False)
    
    # Test invalid Betfury data
    try:
        if 'betfury' in locals():
            # Test with extreme values
            link = betfury.generate_match_link("", "", "unknown", "")
            print("   ✅ Invalid Betfury Data: PASS")
            error_handling_tests.append(True)
    except Exception as e:
        print(f"   ❌ Invalid Betfury Data: FAIL - {e}")
        error_handling_tests.append(False)
    
    error_success_rate = sum(error_handling_tests) / len(error_handling_tests) if error_handling_tests else 0
    test_results.append(("Error Handling", error_success_rate >= 0.5, f"Success rate: {error_success_rate:.1%}"))
    
    # Calculate overall results
    total_time = time.time() - start_time
    total_tests = len(test_results)
    passed_tests = sum(1 for _, success, _ in test_results if success)
    success_rate = passed_tests / total_tests if total_tests > 0 else 0
    
    # Display Results
    print(f"\n" + "="*50)
    print(f"🔬 RELIABILITY TEST RESULTS")
    print(f"="*50)
    
    print(f"📊 **OVERALL RESULTS:**")
    print(f"   • Total Tests: {total_tests}")
    print(f"   • Passed: {passed_tests} ✅")
    print(f"   • Failed: {total_tests - passed_tests} ❌")
    print(f"   • Success Rate: {success_rate:.1%}")
    print(f"   • Test Duration: {total_time:.1f} seconds")
    
    # Reliability Assessment
    if success_rate >= 0.90:
        reliability_status = "🟢 EXCELLENT"
        verdict = "BOT IS HIGHLY RELIABLE"
    elif success_rate >= 0.80:
        reliability_status = "🟡 GOOD"
        verdict = "BOT IS RELIABLE"
    elif success_rate >= 0.70:
        reliability_status = "🟠 FAIR"
        verdict = "BOT NEEDS MINOR IMPROVEMENTS"
    else:
        reliability_status = "🔴 POOR"
        verdict = "BOT NEEDS SIGNIFICANT IMPROVEMENTS"
    
    print(f"   • Reliability: {reliability_status}")
    
    print(f"\n📋 **DETAILED RESULTS:**")
    for test_name, success, details in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   • {test_name}: {status} - {details}")
    
    print(f"\n🎯 **VERDICT: {verdict}** ")
    
    if success_rate >= 0.80:
        print(f"✅ The bot is ready for production use!")
        print(f"🚀 Run: python3 start_minute_scanner.py")
    else:
        print(f"⚠️ The bot needs improvements before production use.")
        print(f"🔧 Review failed tests and fix issues.")
    
    print(f"\n" + "="*50)
    
    return success_rate

def main():
    """Run the quick reliability test"""
    try:
        success_rate = asyncio.run(quick_reliability_test())
        
        # Exit code based on success rate
        if success_rate >= 0.80:
            exit(0)  # Success
        else:
            exit(1)  # Needs improvement
            
    except KeyboardInterrupt:
        print(f"\n🛑 Test interrupted by user")
        exit(2)
    except Exception as e:
        print(f"❌ Test error: {e}")
        exit(3)

if __name__ == "__main__":
    main()
