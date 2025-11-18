#!/usr/bin/env python3
"""
🎾 TENNIS ROI TELEGRAM BOT LAUNCHER
==================================

Launch the Telegram bot that sends notifications about the best ROI tennis matches
with high-confidence predictions and betting opportunities.

This script:
- Sets up the Telegram bot with your token
- Integrates with the tennis prediction system
- Sends automated notifications for high-ROI matches
- Provides interactive commands for users

Usage:
    python tennis_roi_telegram.py

Author: TennisBot Advanced Analytics
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project paths
sys.path.append(str(Path(__file__).parent / 'src'))

try:
    from telegram_roi_bot import TennisROIBot
    print("✅ Successfully imported Telegram ROI Bot")
except ImportError as e:
    print(f"❌ Failed to import Telegram bot: {e}")
    print("Make sure python-telegram-bot is installed: pip install python-telegram-bot")
    sys.exit(1)

def setup_bot_token():
    """Help user setup bot token"""
    print("\n🤖 TELEGRAM BOT SETUP")
    print("=" * 50)
    
    # Check if token exists
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if token:
        print(f"✅ Found bot token: {token[:10]}...")
        return token
    
    print("❌ No Telegram bot token found!")
    print("\n🔧 Setup Instructions:")
    print("1. Open Telegram and search for @BotFather")
    print("2. Send /newbot command")
    print("3. Follow instructions to create your bot")
    print("4. Copy the bot token you receive")
    print("5. Set it as environment variable:")
    print("   export TELEGRAM_BOT_TOKEN='your_token_here'")
    print("\nOr create a config file at: config/telegram_config.json")
    
    # Ask if user wants to enter token now
    response = input("\n💡 Do you have a bot token to enter now? (y/n): ").lower().strip()
    if response in ['y', 'yes']:
        token = input("🔑 Enter your bot token: ").strip()
        if token:
            os.environ['TELEGRAM_BOT_TOKEN'] = token
            print("✅ Token set for this session!")
            return token
    
    return None

async def main():
    """Main function"""
    print("🎾 TENNIS ROI TELEGRAM BOT LAUNCHER")
    print("=" * 60)
    print("This bot will send you notifications about the best tennis")
    print("betting opportunities with high ROI potential!")
    print("=" * 60)
    
    # Setup bot token
    token = setup_bot_token()
    if not token:
        print("\n❌ Cannot start without bot token. Please set up your token first.")
        return
    
    try:
        # Initialize and start the bot
        print("\n🚀 Starting Tennis ROI Bot...")
        bot = TennisROIBot(bot_token=token)
        
        print("🔧 Setting up prediction system...")
        success = await bot.start_bot()
        
        if success:
            print("✅ Bot started successfully!")
            print("\n📱 Bot Commands:")
            print("   /start - Start receiving notifications")
            print("   /roi - Get current best ROI matches")
            print("   /predictions - Get all current predictions")
            print("   /settings - View bot settings")
            print("   /help - Show help message")
            print("   /stop - Stop notifications")
            
            print("\n🎯 Bot Features:")
            print("   • Real-time tennis match analysis")
            print("   • High-confidence predictions (≥25%)")
            print("   • ROI calculations and profit estimates")
            print("   • Risk assessment and betting guidance")
            print("   • Automated notifications for best opportunities")
            
            print("\n🔄 The bot is now running and monitoring matches...")
            print("Press Ctrl+C to stop")
            
        else:
            print("❌ Failed to start bot")
            
    except KeyboardInterrupt:
        print("\n⏹️ Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

def create_systemd_service():
    """Create a systemd service file for running the bot continuously"""
    service_content = f"""[Unit]
Description=Tennis ROI Telegram Bot
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'ubuntu')}
WorkingDirectory={Path(__file__).parent}
Environment=TELEGRAM_BOT_TOKEN={os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_TOKEN_HERE')}
ExecStart={sys.executable} {Path(__file__)}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_file = Path('/tmp/tennis-roi-bot.service')
    with open(service_file, 'w') as f:
        f.write(service_content)
    
    print(f"\n📝 Systemd service file created at: {service_file}")
    print("To install as a system service:")
    print(f"   sudo cp {service_file} /etc/systemd/system/")
    print("   sudo systemctl daemon-reload")
    print("   sudo systemctl enable tennis-roi-bot")
    print("   sudo systemctl start tennis-roi-bot")

def show_usage_examples():
    """Show usage examples"""
    print("\n📚 USAGE EXAMPLES")
    print("=" * 50)
    
    print("🚀 Start the bot:")
    print("   python tennis_roi_telegram.py")
    
    print("\n🔧 Set bot token:")
    print("   export TELEGRAM_BOT_TOKEN='your_bot_token_here'")
    print("   python tennis_roi_telegram.py")
    
    print("\n📱 Telegram Commands:")
    print("   /start - Subscribe to ROI notifications")
    print("   /roi - Get current best ROI matches")
    print("   /predictions - See all current predictions")
    
    print("\n💰 Example ROI Notification:")
    print("   🏆 Djokovic vs Alcaraz")
    print("   🎯 Predicted Winner: Djokovic (65.3%)")
    print("   💰 ROI: 15.2% ($152 profit on $1000 stake)")
    print("   🛡️ Risk Level: 🟢 LOW")
    print("   💎 Recommendation: EXCELLENT BET")

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help':
            show_usage_examples()
            sys.exit(0)
        elif sys.argv[1] == '--service':
            create_systemd_service()
            sys.exit(0)
    
    # Run the bot
    asyncio.run(main())
