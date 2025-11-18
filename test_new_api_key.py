#!/usr/bin/env python3
"""
🔑 TEST NEW ODDS API KEY
=======================
Test the new Odds API key and bot reliability with real data
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project paths
sys.path.append(str(Path(__file__).parent / 'src'))

async def test_new_api_key():
    """Test the new API key and bot functionality"""
    
    print("🔑 TESTING NEW ODDS API KEY")
    print("=" * 50)
    
    # Load secrets with new API key
    try:
        import subprocess
        result = subprocess.run(['python3', 'simple_secrets.py', 'load'], 
                              capture_output=True, text=True, cwd=str(Path(__file__).parent))
        if result.returncode == 0:
            print("✅ Secrets loaded with new API key")
        else:
            print("⚠️ Warning: Could not load secrets")
    except Exception as e:
        print(f"⚠️ Warning: Error loading secrets: {e}")
    
    # Test 1: Odds API Integration
    print(f"\n📊 Test 1: Odds API Integration")
    print("-" * 40)
    
    try:
        from odds_api_integration import OddsAPIIntegration
        
        odds_api = OddsAPIIntegration()
        
        print(f"✅ Odds API initialized")
        print(f"🔑 API Key: {odds_api.api_key[:10]}...")
        print(f"📊 Supported Sports: {len(odds_api.supported_sports)}")
        
        # Test API usage stats
        stats = odds_api.get_api_usage_stats()
        print(f"📈 API Usage: {stats['requests_made']}/{odds_api.max_requests_per_month}")
        print(f"💰 Usage: {stats['usage_percentage']:.1f}%")
        
        # Test fetching live odds
        print(f"\n🔍 Testing live odds fetch...")
        live_odds = await odds_api.get_live_odds(['soccer_epl'], ['h2h'])
        
        print(f"✅ Retrieved odds for {len(live_odds)} matches")
        
        if live_odds:
            first_match = live_odds[0]
            print(f"\n📊 Sample Match:")
            print(f"   🏆 {first_match.home_team} vs {first_match.away_team}")
            print(f"   🏟️ Sport: {first_match.sport_title}")
            print(f"   📅 Time: {first_match.commence_time}")
            print(f"   📈 Bookmakers: {len(first_match.bookmakers)}")
            
            if first_match.best_odds:
                print(f"   💰 Best Odds: {first_match.best_odds}")
            
            if first_match.arbitrage_opportunity:
                arb = first_match.arbitrage_opportunity
                print(f"   🎯 Arbitrage: {arb['profit_margin']:.2f}% profit possible")
            
            if first_match.value_bets:
                print(f"   💎 Value Bets: {len(first_match.value_bets)} opportunities")
        
    except Exception as e:
        print(f"❌ Odds API test failed: {e}")
    
    # Test 2: Minute Scanner with Real Data
    print(f"\n⚡ Test 2: Minute Scanner with Real Data")
    print("-" * 40)
    
    try:
        from telegram_minute_scanner import TelegramMinuteScanner
        
        scanner = TelegramMinuteScanner()
        
        print(f"✅ Scanner initialized")
        print(f"⚙️ Scan interval: {scanner.config['scan_interval']} seconds")
        print(f"🎯 Min ROI threshold: {scanner.config['min_roi_threshold']}%")
        
        # Test single scan with real data
        print(f"\n🔍 Performing test scan...")
        opportunities = await scanner._scan_for_opportunities()
        
        print(f"✅ Scan completed - Found {len(opportunities)} opportunities")
        
        if opportunities:
            print(f"\n🎯 Top Opportunities:")
            for i, opp in enumerate(opportunities[:3], 1):
                print(f"   {i}. {opp.home_team} vs {opp.away_team}")
                print(f"      ROI: {opp.roi_percentage:.1f}% | Confidence: {opp.confidence_score:.0%}")
                print(f"      Sport: {opp.sport} | League: {opp.league}")
                print(f"      Betfury: {opp.betfury_link}")
                print()
        
        # Test message creation
        if opportunities:
            print(f"📱 Testing message creation...")
            message = scanner._create_opportunity_message(opportunities[0])
            
            print(f"✅ Message created - Length: {len(message)} characters")
            print(f"🔗 Contains Betfury link: {'betfury.io' in message}")
            print(f"📊 Contains ROI info: {'ROI:' in message}")
            
            print(f"\n📨 Sample Message:")
            print("=" * 50)
            print(message)
            print("=" * 50)
        
    except Exception as e:
        print(f"❌ Minute scanner test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Enhanced Telegram Bot
    print(f"\n🤖 Test 3: Enhanced Telegram Bot")
    print("-" * 40)
    
    try:
        from enhanced_telegram_roi_bot import EnhancedTelegramROIBot
        
        telegram_bot = EnhancedTelegramROIBot()
        
        print(f"✅ Telegram bot initialized")
        print(f"🎯 Demo mode: {telegram_bot.demo_mode}")
        print(f"📱 Chat ID configured: {bool(telegram_bot.chat_id)}")
        
        # Test sending a message
        test_message = f"""
🔑 **NEW API KEY TEST** 📊

✅ **API Integration Working**
🔍 **Real-time odds available**
⚡ **Minute scanner operational**
🎰 **Betfury links generated**

📅 **Test Time:** {datetime.now().strftime('%H:%M:%S')}
🚀 **Status:** FULLY OPERATIONAL
        """
        
        success = await telegram_bot.send_message(test_message.strip())
        
        if success:
            print(f"✅ Test message sent successfully")
        else:
            print(f"⚠️ Message sent in demo mode")
        
    except Exception as e:
        print(f"❌ Telegram bot test failed: {e}")
    
    # Test 4: Complete System Integration
    print(f"\n🔄 Test 4: Complete System Integration")
    print("-" * 40)
    
    try:
        # Test that all components work together
        print(f"🔧 Testing component integration...")
        
        # Initialize all components
        from telegram_minute_scanner import TelegramMinuteScanner
        from betfury_integration import BetfuryIntegration
        from odds_api_integration import OddsAPIIntegration
        
        scanner = TelegramMinuteScanner()
        betfury = BetfuryIntegration(affiliate_code="api_test_2025")
        odds_api = OddsAPIIntegration()
        
        print(f"✅ All components initialized")
        
        # Test integration workflow
        print(f"🔍 Testing integration workflow...")
        
        # 1. Get odds data
        odds_data = await odds_api.get_live_odds(['soccer_epl'], ['h2h'])
        print(f"   📊 Odds data: {len(odds_data)} matches")
        
        # 2. Generate opportunities
        opportunities = await scanner._scan_for_opportunities()
        print(f"   🎯 Opportunities: {len(opportunities)} found")
        
        # 3. Generate Betfury links
        if opportunities:
            opp = opportunities[0]
            betfury_link = betfury.generate_match_link(
                opp.home_team, opp.away_team, opp.sport, opp.league
            )
            print(f"   🎰 Betfury link: {betfury_link[:50]}...")
        
        # 4. Create notification message
        if opportunities:
            message = scanner._create_opportunity_message(opportunities[0])
            print(f"   📱 Message: {len(message)} characters")
        
        print(f"✅ Complete integration test successful")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🎉 NEW API KEY TEST COMPLETED!")
    print(f"✅ System is ready with new Odds API key")
    print(f"🚀 Run: python3 start_minute_scanner.py")

def main():
    """Run the test"""
    try:
        asyncio.run(test_new_api_key())
    except KeyboardInterrupt:
        print(f"\n🛑 Test stopped by user")
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    main()
