#!/usr/bin/env python3
"""
🔍 TEST FIXED SCANNER
====================
Test the scanner with working Telegram credentials
"""

import asyncio
import sys
import os
from pathlib import Path

# Set credentials directly (since we know they work)
os.environ['TELEGRAM_BOT_TOKEN'] = '8481385860:AAGBRbsDA8--t373COn2mgM4_c1ngc2fGRM'
os.environ['TELEGRAM_CHAT_ID'] = '-4956738581'

# Add project paths
sys.path.append(str(Path(__file__).parent / 'src'))

async def test_fixed_scanner():
    """Test the scanner with fixed Telegram"""
    
    print("🔍 TESTING FIXED SCANNER")
    print("=" * 50)
    
    print(f"✅ Using working credentials:")
    print(f"   • Bot: @pyyhkijabot")
    print(f"   • Chat: {os.environ['TELEGRAM_CHAT_ID']}")
    
    # Test scanner initialization
    print(f"\n🤖 Initializing scanner...")
    try:
        from telegram_minute_scanner import TelegramMinuteScanner
        
        scanner = TelegramMinuteScanner()
        
        # Override with working credentials
        scanner.telegram_bot.token = os.environ['TELEGRAM_BOT_TOKEN']
        scanner.telegram_bot.chat_id = os.environ['TELEGRAM_CHAT_ID']
        scanner.telegram_bot.demo_mode = False
        
        # Initialize bot properly
        from telegram import Bot
        scanner.telegram_bot.bot = Bot(scanner.telegram_bot.token)
        
        print("✅ Scanner initialized with working Telegram")
        
    except Exception as e:
        print(f"❌ Scanner initialization failed: {e}")
        return False
    
    # Test scanner message
    print(f"\n📤 Testing scanner message...")
    try:
        success = await scanner.telegram_bot.send_message("🔍 Scanner test with fixed Telegram - WORKING!")
        
        if success:
            print("✅ Scanner messaging works perfectly!")
        else:
            print("❌ Scanner messaging failed")
            return False
            
    except Exception as e:
        print(f"❌ Scanner message failed: {e}")
        return False
    
    # Test opportunity scan
    print(f"\n🎯 Testing opportunity scan...")
    try:
        opportunities = await scanner._scan_for_opportunities()
        
        print(f"✅ Scan completed - found {len(opportunities)} opportunities")
        
        if opportunities:
            # Test sending first opportunity
            filtered = scanner._filter_opportunities(opportunities)
            
            if filtered:
                print(f"📤 Sending test opportunity notification...")
                
                message = scanner._create_opportunity_message(filtered[0])
                success = await scanner.telegram_bot.send_message(message)
                
                if success:
                    print("✅ Opportunity notification sent!")
                else:
                    print("❌ Opportunity notification failed")
            else:
                print("📊 No opportunities passed filters (normal)")
        else:
            print("📊 No opportunities found (normal)")
            
    except Exception as e:
        print(f"❌ Opportunity scan failed: {e}")
        return False
    
    print(f"\n" + "="*50)
    print(f"🎉 SCANNER FULLY WORKING!")
    print(f"="*50)
    
    print(f"✅ **All systems operational:**")
    print(f"   • Telegram: ✅ CONNECTED")
    print(f"   • Scanner: ✅ INITIALIZED")
    print(f"   • Messages: ✅ SENDING")
    print(f"   • Opportunities: ✅ SCANNING")
    
    print(f"\n🚀 **Ready to run continuous scanner:**")
    print(f"   python3 start_minute_scanner.py")
    
    return True

def main():
    """Run the scanner test"""
    try:
        success = asyncio.run(test_fixed_scanner())
        
        if success:
            print(f"\n🎉 **TELEGRAM SCANNER IS FULLY OPERATIONAL!**")
            print(f"📱 Check your Telegram for test messages")
        else:
            print(f"\n❌ **Scanner test failed**")
            
    except KeyboardInterrupt:
        print(f"\n🛑 Test interrupted")
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
