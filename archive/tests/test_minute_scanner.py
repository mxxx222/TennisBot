#!/usr/bin/env python3
"""
⚡ TEST MINUTE SCANNER
====================
Test the Telegram minute scanner functionality
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project paths
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / 'src'))

async def test_minute_scanner():
    """Test the minute scanner"""
    
    print("⚡ TELEGRAM MINUTE SCANNER TEST")
    print("=" * 50)
    
    # Load secrets
    try:
        import subprocess
        result = subprocess.run(['python', 'simple_secrets.py', 'load'], 
                              capture_output=True, text=True, cwd=str(Path(__file__).parent))
        if result.returncode == 0:
            print("✅ Secrets loaded successfully")
        else:
            print("⚠️ Warning: Could not load secrets, using demo mode")
    except Exception as e:
        print(f"⚠️ Warning: Error loading secrets: {e}")
    
    # Test scanner initialization
    try:
        from telegram_minute_scanner import TelegramMinuteScanner, QuickOpportunity
        
        scanner = TelegramMinuteScanner()
        
        print("✅ Scanner initialized successfully")
        print(f"⚙️ Configuration:")
        print(f"   • Scan Interval: {scanner.config['scan_interval']} seconds")
        print(f"   • Min ROI: {scanner.config['min_roi_threshold']}%")
        print(f"   • Min Confidence: {scanner.config['min_confidence']:.0%}")
        print(f"   • Max Daily Notifications: {scanner.config['max_daily_notifications']}")
        
        # Test opportunity creation
        print(f"\n🎯 Testing opportunity creation...")
        
        demo_opportunity = QuickOpportunity(
            match_id="test_real_madrid_barcelona",
            home_team="Real Madrid",
            away_team="Barcelona",
            sport="football",
            league="La Liga",
            roi_percentage=15.8,
            confidence_score=0.72,
            recommended_stake=3.5,
            potential_profit=420.0,
            odds=2.25,
            market="match_winner",
            selection="Real Madrid",
            betfury_link="https://betfury.io/sports/football/spain/laliga/real-madrid-vs-barcelona?ref=tennisbot_2025",
            expires_at=datetime.now() + timedelta(hours=2),
            discovered_at=datetime.now()
        )
        
        # Test message creation
        message = scanner._create_opportunity_message(demo_opportunity)
        
        print("✅ Opportunity message created")
        print(f"\n📨 Sample Telegram Message:")
        print("=" * 60)
        print(message)
        print("=" * 60)
        
        # Test scanner stats
        stats = scanner.get_scanner_stats()
        print(f"\n📊 Scanner Statistics:")
        print(f"   • Running: {stats['running']}")
        print(f"   • Scan Count: {stats['scan_count']}")
        print(f"   • Opportunities Found: {stats['opportunities_found']}")
        print(f"   • Daily Notifications: {stats['daily_notifications']}")
        print(f"   • Scan Interval: {stats['scan_interval']} seconds")
        
        # Test demo opportunity generation
        print(f"\n🎲 Testing demo opportunity generation...")
        demo_opportunities = scanner._generate_demo_opportunities()
        
        if demo_opportunities:
            print(f"✅ Generated {len(demo_opportunities)} demo opportunities")
            for i, opp in enumerate(demo_opportunities, 1):
                print(f"   {i}. {opp.home_team} vs {opp.away_team} - ROI: {opp.roi_percentage:.1f}%")
        else:
            print("📊 No demo opportunities generated (normal for most scans)")
        
        # Test filtering
        print(f"\n🔍 Testing opportunity filtering...")
        
        test_opportunities = [
            QuickOpportunity(
                match_id="test1",
                home_team="Team A",
                away_team="Team B", 
                sport="football",
                league="Test League",
                roi_percentage=12.5,  # Above threshold
                confidence_score=0.75,  # Above threshold
                recommended_stake=3.0,
                potential_profit=300.0,
                odds=2.1,
                market="match_winner",
                selection="Team A",
                betfury_link="https://betfury.io/test1",
                expires_at=datetime.now() + timedelta(hours=1),
                discovered_at=datetime.now()
            ),
            QuickOpportunity(
                match_id="test2",
                home_team="Team C",
                away_team="Team D",
                sport="tennis", 
                league="Test Tournament",
                roi_percentage=5.0,  # Below threshold
                confidence_score=0.80,
                recommended_stake=2.0,
                potential_profit=200.0,
                odds=1.9,
                market="match_winner",
                selection="Team C",
                betfury_link="https://betfury.io/test2",
                expires_at=datetime.now() + timedelta(hours=1),
                discovered_at=datetime.now()
            )
        ]
        
        filtered = scanner._filter_opportunities(test_opportunities)
        print(f"✅ Filtered {len(test_opportunities)} opportunities to {len(filtered)}")
        
        for opp in filtered:
            print(f"   • {opp.home_team} vs {opp.away_team} - ROI: {opp.roi_percentage:.1f}%")
        
        # Test single scan simulation
        print(f"\n🔄 Simulating single scan...")
        
        # Temporarily set scan count to trigger demo opportunities
        scanner.scan_count = 5
        opportunities = await scanner._scan_for_opportunities()
        
        if opportunities:
            print(f"✅ Scan found {len(opportunities)} opportunities")
            
            for i, opp in enumerate(opportunities, 1):
                print(f"   {i}. {opp.home_team} vs {opp.away_team}")
                print(f"      ROI: {opp.roi_percentage:.1f}% | Confidence: {opp.confidence_score:.0%}")
                print(f"      Betfury: {opp.betfury_link}")
        else:
            print("📊 No opportunities found in simulation")
        
        print(f"\n✅ MINUTE SCANNER TEST COMPLETED!")
        print(f"🚀 Ready to run: python telegram_minute_scanner.py")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run the test"""
    try:
        asyncio.run(test_minute_scanner())
    except KeyboardInterrupt:
        print(f"\n🛑 Test stopped by user")
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    main()
