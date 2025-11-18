#!/usr/bin/env python3
"""
🤖 DIRECT TELEGRAM TEST
======================
Direct test of enhanced Telegram bot with hardcoded credentials.
"""

import asyncio
import sys
from pathlib import Path

# Add project paths
current_dir = Path(__file__).parent
sys.path.append(str(current_dir / 'src'))

# Hardcode credentials for testing
TELEGRAM_BOT_TOKEN = "8481385860:AAGBRbsDA8--t373COn2mgM4_c1ngc2fGRM"
TELEGRAM_CHAT_ID = "-4956738581"

print(f"🤖 Using Bot Token: {TELEGRAM_BOT_TOKEN[:20]}...")
print(f"💬 Using Chat ID: {TELEGRAM_CHAT_ID}")

# Import Telegram
try:
    from telegram import Bot
    TELEGRAM_AVAILABLE = True
    print("✅ Telegram library available")
except ImportError:
    print("❌ Telegram library not available")
    TELEGRAM_AVAILABLE = False

async def send_enhanced_roi_message():
    """Send enhanced ROI message directly"""
    
    if not TELEGRAM_AVAILABLE:
        print("❌ Cannot send - Telegram not available")
        return
    
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    # Enhanced ROI message with AI predictions
    message = """
🤖 **ENHANCED ROI BOT - LIVE ANALYSIS**
📅 2025-11-08 10:40

💎 **INTELLIGENT MATCH ANALYSIS:**

🔥 **OPPORTUNITY #1** ⚽
**Manchester City vs Liverpool**
🏆 Premier League | 📅 2025-11-09 15:00

🤖 **AI PREDICTION:**
• Winner: Manchester City (72% confidence)
• Expected Goals: 2.8 (High-scoring match)
• AI Rating: 8.4/10 🔥

🎯 **BETTING OPPORTUNITY:**
• Market: Over/Under 2.5 - Over 2.5
• Bookmaker: Pinnacle | Odds: 1.85
• Expected ROI: 15.2%
• Edge: 8.7% | Confidence: 78%

💰 **RECOMMENDATION:**
• 🔥 MUST BET
• Stake: 4.2% ($420)
• Potential Profit: $357
• Risk: MODERATE

🔑 **KEY FACTORS:**
• 🎯 High edge (8.7%)
• 📊 High confidence (78%)
• ⚽ High-scoring match expected
• 🛡️ Low risk profile

⏰ **Expires:** 14:30

────────────────────────────────────────

⭐ **OPPORTUNITY #2** 🎾
**Novak Djokovic vs Carlos Alcaraz**
🏆 ATP Masters | 📅 2025-11-08 18:00

🤖 **AI PREDICTION:**
• Winner: Novak Djokovic (68% confidence)
• Set Prediction: 2-1 | Duration: Long
• AI Rating: 7.9/10 ⭐

🎯 **BETTING OPPORTUNITY:**
• Market: Match Winner - Djokovic
• Bookmaker: Bet365 | Odds: 2.10
• Expected ROI: 18.7%
• Edge: 6.8% | Confidence: 82%

💰 **RECOMMENDATION:**
• ⭐ STRONG BET
• Stake: 5.1% ($510)
• Potential Profit: $561
• Risk: CONSERVATIVE

🔑 **KEY FACTORS:**
• 💰 Excellent ROI (18.7%)
• 📊 High confidence (82%)
• 🛡️ Low risk profile

⏰ **Expires:** 17:30

────────────────────────────────────────

📊 **PORTFOLIO SUMMARY:**
• Total Opportunities: 8
• Average AI Rating: 7.6/10
• Total Stake: 18.5% ($1,850)
• Expected Return: 24.3%
• Risk Score: 0.42/1.0

🎯 **AI SYSTEM STATUS:**
• Prediction Accuracy: 72.5% (Last 30 days)
• ROI Performance: +18.7% (This month)
• Risk Management: ✅ Optimal

⚠️ **Remember: Bet responsibly and within your limits!**
    """
    
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message.strip(),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        print("✅ Enhanced ROI message sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

async def send_ai_prediction_showcase():
    """Send AI prediction showcase"""
    
    if not TELEGRAM_AVAILABLE:
        return
    
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    showcase_message = """
🧠 **AI PREDICTION SHOWCASE**

**🎯 MATCH WINNER PREDICTIONS:**

⚽ **FOOTBALL:**
• Man City vs Liverpool: **Man City** (72% confidence)
• Barcelona vs Real Madrid: **Barcelona** (68% confidence)
• Bayern vs Dortmund: **Bayern** (75% confidence)

🎾 **TENNIS:**
• Djokovic vs Alcaraz: **Djokovic** (68% confidence)
• Swiatek vs Gauff: **Swiatek** (71% confidence)

🏀 **BASKETBALL:**
• Lakers vs Celtics: **Lakers** (65% confidence)
• Warriors vs Heat: **Warriors** (69% confidence)

**📊 AI PERFORMANCE METRICS:**
• Overall Accuracy: 72.5%
• Football Accuracy: 74.2%
• Tennis Accuracy: 71.8%
• Basketball Accuracy: 68.5%

**💰 ROI ANALYSIS:**
• Best ROI Opportunity: 28.7%
• Average ROI: 16.3%
• Success Rate: 72.1%

**🔥 RECENT WINS:**
✅ Man United vs Arsenal: Over 2.5 (+18.5% ROI)
✅ Djokovic vs Nadal: Djokovic Win (+22.1% ROI)
✅ Lakers vs Nets: Over 215.5 (+14.7% ROI)

🎯 **The AI system analyzes 50+ factors per match including:**
• Team/player form and statistics
• Head-to-head records
• Weather and venue conditions
• Injury reports and suspensions
• Market inefficiencies and value bets

**Ready to find your next profitable bet! 🚀**
    """
    
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=showcase_message.strip(),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        print("✅ AI prediction showcase sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Error sending showcase: {e}")
        return False

async def main():
    """Main test function"""
    print("\n🧪 DIRECT TELEGRAM TEST")
    print("=" * 30)
    
    # Test 1: Send enhanced ROI analysis
    print("\n📊 Sending enhanced ROI analysis...")
    success1 = await send_enhanced_roi_message()
    
    if success1:
        # Wait a bit between messages
        await asyncio.sleep(3)
        
        # Test 2: Send AI prediction showcase
        print("\n🤖 Sending AI prediction showcase...")
        success2 = await send_ai_prediction_showcase()
        
        if success2:
            print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
            print("Check your Telegram chat for the enhanced notifications with:")
            print("• 🤖 AI winner predictions with confidence ratings")
            print("• 💰 ROI analysis and betting recommendations")
            print("• 🛡️ Risk assessment and bankroll management")
            print("• 📊 Detailed match analysis and key factors")
        else:
            print("\n❌ Second test failed")
    else:
        print("\n❌ First test failed")

if __name__ == "__main__":
    asyncio.run(main())
