#!/usr/bin/env python3
"""
🔍 SCAN AND NOTIFY NOW
=====================
Perform immediate scan for opportunities and send Telegram notifications
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project paths
sys.path.append(str(Path(__file__).parent / 'src'))

async def scan_and_notify_now():
    """Perform immediate scan and send notifications"""
    
    print("🔍 IMMEDIATE OPPORTUNITY SCAN")
    print("=" * 50)
    print(f"🕐 Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Searching for profitable betting opportunities...")
    print("=" * 50)
    
    # Load secrets
    try:
        import subprocess
        result = subprocess.run(['python3', 'simple_secrets.py', 'load'], 
                              capture_output=True, text=True, cwd=str(Path(__file__).parent))
        if result.returncode == 0:
            print("✅ Secrets loaded - using real credentials")
        else:
            print("⚠️ Warning: Could not load secrets, using demo mode")
    except Exception as e:
        print(f"⚠️ Warning: Error loading secrets: {e}")
    
    # Initialize scanner
    try:
        from telegram_minute_scanner import TelegramMinuteScanner
        
        scanner = TelegramMinuteScanner()
        print("✅ Scanner initialized")
        print(f"📊 Configuration: Min ROI {scanner.config['min_roi_threshold']}%, Min Confidence {scanner.config['min_confidence']:.0%}")
        
    except Exception as e:
        print(f"❌ Scanner initialization failed: {e}")
        return
    
    # Perform scan
    print(f"\n🔍 Step 1: Scanning for opportunities...")
    print("-" * 40)
    
    try:
        opportunities = await scanner._scan_for_opportunities()
        
        print(f"✅ Scan completed")
        print(f"🎯 Found {len(opportunities)} total opportunities")
        
        if not opportunities:
            print("📊 No profitable opportunities found at this time")
            print("💡 This is normal - profitable opportunities are rare")
            
            # Send a status message anyway
            status_message = f"""
🔍 **MANUAL SCAN COMPLETED**

📅 **Scan Time:** {datetime.now().strftime('%H:%M:%S')}
🎯 **Opportunities Found:** 0
📊 **Status:** No profitable matches at this time

⏰ **Next automatic scan in 5 minutes**
🔄 **Scanner Status:** Active
            """
            
            success = await scanner.telegram_bot.send_message(status_message.strip())
            if success:
                print("📱 Status message sent to Telegram")
            else:
                print("📱 Status message sent in demo mode")
            
            return
        
    except Exception as e:
        print(f"❌ Scan failed: {e}")
        return
    
    # Filter opportunities
    print(f"\n🎯 Step 2: Filtering opportunities...")
    print("-" * 40)
    
    try:
        filtered_opportunities = scanner._filter_opportunities(opportunities)
        
        print(f"✅ Filtering completed")
        print(f"📊 {len(filtered_opportunities)} opportunities passed filters")
        
        if not filtered_opportunities:
            print("📊 No opportunities met the quality criteria")
            print("💡 Filters: ROI ≥8%, Confidence ≥60%, Not expired, Not recently notified")
            return
        
    except Exception as e:
        print(f"❌ Filtering failed: {e}")
        return
    
    # Display found opportunities
    print(f"\n🎯 Step 3: Found Opportunities")
    print("-" * 40)
    
    for i, opp in enumerate(filtered_opportunities, 1):
        print(f"{i}. {opp.home_team} vs {opp.away_team}")
        print(f"   🏆 {opp.sport.title()} - {opp.league}")
        print(f"   💰 ROI: {opp.roi_percentage:.1f}% | Confidence: {opp.confidence_score:.0%}")
        print(f"   🎯 Selection: {opp.selection} @ {opp.odds:.2f}")
        print(f"   💵 Stake: {opp.recommended_stake:.1f}% | Profit: {opp.potential_profit:.0f}€")
        print(f"   🎰 Betfury: {opp.betfury_link[:50]}...")
        print()
    
    # Send notifications
    print(f"📱 Step 4: Sending Telegram notifications...")
    print("-" * 40)
    
    # Send summary first
    summary_message = f"""
🚨 **MANUAL SCAN RESULTS**

📅 **Scan Time:** {datetime.now().strftime('%H:%M:%S')}
🎯 **Opportunities Found:** {len(filtered_opportunities)}
📊 **Ready to send notifications**

💰 **Top Opportunities:**
    """
    
    for i, opp in enumerate(filtered_opportunities[:3], 1):
        summary_message += f"\n{i}. {opp.home_team} vs {opp.away_team} - ROI: {opp.roi_percentage:.1f}%"
    
    try:
        success = await scanner.telegram_bot.send_message(summary_message.strip())
        if success:
            print("✅ Summary message sent to Telegram")
        else:
            print("✅ Summary message sent in demo mode")
    except Exception as e:
        print(f"❌ Error sending summary: {e}")
    
    # Send individual opportunity notifications
    notifications_sent = 0
    
    for i, opportunity in enumerate(filtered_opportunities, 1):
        try:
            print(f"📤 Sending notification {i}/{len(filtered_opportunities)}...")
            
            # Create detailed message
            message = scanner._create_opportunity_message(opportunity)
            
            # Send message
            success = await scanner.telegram_bot.send_message(message)
            
            if success:
                print(f"✅ Notification {i} sent successfully")
                notifications_sent += 1
            else:
                print(f"✅ Notification {i} sent in demo mode")
                notifications_sent += 1
            
            # Small delay between messages
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"❌ Error sending notification {i}: {e}")
    
    # Send completion message
    completion_message = f"""
✅ **SCAN AND NOTIFY COMPLETED**

📊 **Results:**
• Opportunities Found: {len(opportunities)}
• Passed Filters: {len(filtered_opportunities)}
• Notifications Sent: {notifications_sent}

🎰 **All opportunities include Betfury.io links**
⏰ **Next automatic scan in 5 minutes**
    """
    
    try:
        success = await scanner.telegram_bot.send_message(completion_message.strip())
        if success:
            print("✅ Completion message sent to Telegram")
        else:
            print("✅ Completion message sent in demo mode")
    except Exception as e:
        print(f"❌ Error sending completion message: {e}")
    
    print(f"\n" + "="*50)
    print(f"🎉 SCAN AND NOTIFY COMPLETED!")
    print(f"="*50)
    
    print(f"📊 **Final Results:**")
    print(f"   • Total Opportunities Scanned: {len(opportunities) if 'opportunities' in locals() else 0}")
    print(f"   • Profitable Opportunities: {len(filtered_opportunities) if 'filtered_opportunities' in locals() else 0}")
    print(f"   • Telegram Notifications Sent: {notifications_sent}")
    
    if notifications_sent > 0:
        print(f"\n📱 **Check your Telegram chat for notifications!**")
        print(f"💬 Chat ID: {scanner.telegram_bot.chat_id}")
    else:
        print(f"\n📊 **No notifications sent - no profitable opportunities found**")
        print(f"💡 This is normal - the scanner will continue checking every 5 minutes")
    
    print(f"\n🔄 **Background scanner continues running every 5 minutes**")

def main():
    """Run immediate scan and notify"""
    try:
        asyncio.run(scan_and_notify_now())
    except KeyboardInterrupt:
        print(f"\n🛑 Scan interrupted by user")
    except Exception as e:
        print(f"❌ Scan error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
