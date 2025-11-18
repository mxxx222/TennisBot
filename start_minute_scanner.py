#!/usr/bin/env python3
"""
⚡ START MINUTE SCANNER
=====================
Launch the Telegram bot that searches for new opportunities every minute
"""

import asyncio
import sys
import os
from pathlib import Path

def main():
    """Launch the minute scanner"""
    print("⚡ TELEGRAM 5-MINUTE SCANNER LAUNCHER")
    print("=" * 50)
    print("🔄 Searches for opportunities every 5 minutes")
    print("⚡ Efficient Telegram notifications")
    print("🎰 Betfury.io betting links included")
    print("📊 Real-time odds and analysis")
    print("=" * 50)
    
    # Load secrets
    try:
        import subprocess
        result = subprocess.run(['python', 'simple_secrets.py', 'load'], 
                              capture_output=True, text=True, cwd=str(Path(__file__).parent))
        if result.returncode == 0:
            print("✅ Secrets loaded successfully")
        else:
            print("⚠️ Warning: Could not load secrets, bot will run in demo mode")
    except Exception as e:
        print(f"⚠️ Warning: Error loading secrets: {e}")
    
    # Import and start scanner
    try:
        from telegram_minute_scanner import TelegramMinuteScanner
        
        print("\n🚀 Starting Telegram 5-Minute Scanner...")
        print("📱 Check your Telegram for notifications every 5 minutes")
        print("⌨️ Press Ctrl+C to stop")
        print("\n" + "="*50)
        
        # Run the scanner
        scanner = TelegramMinuteScanner()
        asyncio.run(scanner.start_minute_scanning())
        
    except ImportError as e:
        print(f"❌ Error: Required modules not available: {e}")
        print("💡 Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
    except KeyboardInterrupt:
        print("\n🛑 Scanner stopped by user")
        print("✅ Shutdown complete")
    except Exception as e:
        print(f"❌ Scanner error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
