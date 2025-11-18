#!/usr/bin/env python3
"""
🔧 DIRECT TELEGRAM FIX
=====================
Fix Telegram bot with direct credentials
"""

import asyncio
import sys
import os
from pathlib import Path

# Set credentials directly
os.environ['TELEGRAM_BOT_TOKEN'] = '8481385860:AAGBRbsDA8--t373COn2mgM4_c1ngc2fGRM'
os.environ['TELEGRAM_CHAT_ID'] = '-4956738581'

# Add project paths
sys.path.append(str(Path(__file__).parent / 'src'))

async def fix_telegram_direct():
    """Fix Telegram with direct credentials"""
    
    print("🔧 DIRECT TELEGRAM FIX")
    print("=" * 50)
    
    token = os.environ['TELEGRAM_BOT_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    
    print(f"✅ Using direct credentials:")
    print(f"   • Bot Token: {token[:10]}...")
    print(f"   • Chat ID: {chat_id}")
    
    # Test Telegram library
    print(f"\n📚 Testing Telegram library...")
    try:
        from telegram import Bot
        print("✅ python-telegram-bot imported successfully")
        
    except ImportError as e:
        print(f"❌ Failed to import: {e}")
        return False
    
    # Initialize bot
    print(f"\n🤖 Initializing bot...")
    try:
        bot = Bot(token=token)
        print("✅ Bot initialized")
        
    except Exception as e:
        print(f"❌ Bot initialization failed: {e}")
        return False
    
    # Test connection
    print(f"\n🔗 Testing connection...")
    try:
        bot_info = await bot.get_me()
        print(f"✅ Bot connected:")
        print(f"   • Name: {bot_info.first_name}")
        print(f"   • Username: @{bot_info.username}")
        print(f"   • ID: {bot_info.id}")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    # Send test message
    print(f"\n📤 Sending test message...")
    try:
        test_message = f"""
🔧 **TELEGRAM FIX SUCCESS!**

✅ **Status:** WORKING PERFECTLY
🤖 **Bot:** @{bot_info.username}
📅 **Fixed:** {asyncio.get_event_loop().time()}

🎉 **Ready for betting notifications!**
        """
        
        await bot.send_message(
            chat_id=chat_id,
            text=test_message.strip(),
            parse_mode='Markdown'
        )
        
        print("✅ Test message sent!")
        print(f"📱 Check Telegram chat: {chat_id}")
        
    except Exception as e:
        print(f"❌ Message failed: {e}")
        return False
    
    # Test opportunity message
    print(f"\n🎯 Testing opportunity message...")
    try:
        opportunity_message = f"""
🚨 **5-MIN SCANNER ALERT** ⚽

**Real Madrid vs Barcelona**
🏆 La Liga

💰 **ANALYSIS:**
• ROI: 18.5%
• Confidence: 75%
• Risk: 🟡 MODERATE

🎯 **BETTING INFO:**
• Selection: Real Madrid
• Odds: 2.25
• Stake: 4.0%
• Profit: 450€

🎰 **BET NOW:**
[**🎰 BETFURY.IO**](https://betfury.io/sports/football/spain/laliga/real-madrid-vs-barcelona?ref=tennisbot_2025)

⏰ **Expires:** 14:30
🔍 **Test:** TELEGRAM FIX
        """
        
        await bot.send_message(
            chat_id=chat_id,
            text=opportunity_message.strip(),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        
        print("✅ Opportunity message sent!")
        
    except Exception as e:
        print(f"❌ Opportunity message failed: {e}")
        return False
    
    print(f"\n" + "="*50)
    print(f"🎉 TELEGRAM COMPLETELY FIXED!")
    print(f"="*50)
    
    print(f"✅ **All systems working:**")
    print(f"   • Credentials: ✅ SET")
    print(f"   • Library: ✅ IMPORTED")
    print(f"   • Bot: ✅ CONNECTED")
    print(f"   • Messages: ✅ SENDING")
    print(f"   • Opportunities: ✅ FORMATTED")
    
    print(f"\n📱 **Check your Telegram for 2 test messages!**")
    print(f"🤖 Bot: @{bot_info.username}")
    print(f"💬 Chat: {chat_id}")
    
    return True

async def test_scanner_with_fix():
    """Test the scanner with fixed credentials"""
    
    print(f"\n🔍 TESTING SCANNER WITH FIX...")
    print("-" * 40)
    
    try:
        from telegram_minute_scanner import TelegramMinuteScanner
        
        # Create scanner
        scanner = TelegramMinuteScanner()
        
        # Override credentials
        scanner.telegram_bot.token = os.environ['TELEGRAM_BOT_TOKEN']
        scanner.telegram_bot.chat_id = os.environ['TELEGRAM_CHAT_ID']
        scanner.telegram_bot.demo_mode = False
        scanner.telegram_bot.bot = Bot(scanner.telegram_bot.token)
        
        print("✅ Scanner initialized with fixed credentials")
        
        # Test scanner message
        success = await scanner.telegram_bot.send_message("🔍 Scanner test - credentials fixed!")
        
        if success:
            print("✅ Scanner messaging works!")
        else:
            print("❌ Scanner messaging failed")
            
    except Exception as e:
        print(f"❌ Scanner test failed: {e}")

def main():
    """Run the direct fix"""
    try:
        print("🚀 STARTING DIRECT TELEGRAM FIX...")
        
        success = asyncio.run(fix_telegram_direct())
        
        if success:
            print(f"\n🎉 **TELEGRAM IS FIXED AND WORKING!**")
            
            # Test scanner
            asyncio.run(test_scanner_with_fix())
            
            print(f"\n🚀 **READY TO USE:**")
            print(f"   • python3 start_minute_scanner.py")
            print(f"   • python3 scan_and_notify_now.py")
            
        else:
            print(f"\n❌ **Fix failed - check errors above**")
            
    except KeyboardInterrupt:
        print(f"\n🛑 Fix interrupted")
    except Exception as e:
        print(f"❌ Fix error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
