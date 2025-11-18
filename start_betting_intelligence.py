#!/usr/bin/env python3
"""
🚀 BETTING INTELLIGENCE LAUNCHER
===============================
Käynnistä jatkuva vedonlyönti-äly järjestelmä

Käyttö:
python start_betting_intelligence.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project paths
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / 'src'))

def load_secrets():
    """Lataa salaiset tiedot"""
    try:
        import subprocess
        result = subprocess.run(['python', 'simple_secrets.py', 'load'], 
                              capture_output=True, text=True, cwd=str(Path(__file__).parent))
        if result.returncode == 0:
            print("✅ Secrets loaded successfully")
        else:
            print("⚠️ Warning: Could not load secrets")
    except Exception as e:
        print(f"⚠️ Warning: Error loading secrets: {e}")

async def main():
    """Pääohjelma"""
    print("🚀 BETTING INTELLIGENCE SYSTEM LAUNCHER")
    print("=" * 50)
    
    # Load secrets first
    load_secrets()
    
    # Import and start the system
    try:
        from continuous_betting_intelligence import ContinuousBettingIntelligence
        
        # Configuration
        config = {
            'scan_interval': 120,  # 2 minutes between scans
            'min_roi_threshold': 8.0,  # 8% minimum ROI
            'min_confidence': 0.60,  # 60% minimum confidence
            'min_edge': 3.0,  # 3% minimum edge
            'max_daily_stake': 20.0,  # 20% max daily stake
            'telegram_notifications': True,
            'web_scraping_enabled': True,
            'odds_api_enabled': True,
            'sports': ['football', 'tennis', 'basketball', 'ice_hockey']
        }
        
        print("🔧 Configuration:")
        print(f"• Scan Interval: {config['scan_interval']} seconds")
        print(f"• Min ROI: {config['min_roi_threshold']}%")
        print(f"• Min Confidence: {config['min_confidence']:.0%}")
        print(f"• Max Daily Stake: {config['max_daily_stake']}%")
        print(f"• Sports: {', '.join(config['sports'])}")
        
        # Initialize and start system
        system = ContinuousBettingIntelligence(config)
        
        print("\n🚀 Starting Continuous Betting Intelligence...")
        print("🔄 System will continuously analyze games for profitable opportunities")
        print("⚡ Instant Telegram notifications for new opportunities")
        print("🎰 Betfury.io betting links included with every match")
        print("🕷️ Web scraping for real-time odds data")
        print("\n⌨️ Press Ctrl+C to stop\n")
        
        await system.start_continuous_analysis()
        
    except ImportError as e:
        print(f"❌ Error: Required modules not available: {e}")
        print("💡 Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ System error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 System stopped by user")
        print("✅ Shutdown complete")
    except Exception as e:
        print(f"❌ Launcher error: {e}")
