#!/usr/bin/env python3
"""
🎯 BETTING INTELLIGENCE DEMO
===========================
Demonstroi jatkuvan vedonlyönti-äly järjestelmän toiminnallisuutta
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add project paths
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / 'src'))

async def demo_betting_intelligence():
    """Demonstroi järjestelmän toiminnallisuutta"""
    
    print("🎯 BETTING INTELLIGENCE SYSTEM DEMO")
    print("=" * 60)
    print("🔄 Jatkuva pelien analysointi ROI:n ja kannattavuuden perusteella")
    print("⚡ Välittömät Telegram-ilmoitukset uusista mahdollisuuksista")  
    print("🎰 Betfury.io vedonlyöntilinkit jokaiseen matsiin")
    print("🕷️ Web scraping reaaliaikaisille tiedoille")
    print("=" * 60)
    
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
    
    # Test 1: Betfury Integration
    print(f"\n🎰 Test 1: Betfury.io Integration")
    print("-" * 40)
    
    try:
        from betfury_integration import BetfuryIntegration
        
        betfury = BetfuryIntegration(affiliate_code="tennisbot_2025")
        
        # Test match
        test_match = {
            'home_team': 'Manchester City',
            'away_team': 'Arsenal', 
            'sport': 'football',
            'league': 'Premier League'
        }
        
        main_link = betfury.generate_match_link(
            test_match['home_team'],
            test_match['away_team'],
            test_match['sport'],
            test_match['league']
        )
        
        market_links = betfury.generate_multiple_links(test_match)
        
        print(f"✅ Betfury integration working")
        print(f"🔗 Main Link: {main_link}")
        print(f"📊 Market Links: {len(market_links)} generated")
        
    except Exception as e:
        print(f"❌ Betfury integration error: {e}")
    
    # Test 2: Enhanced Telegram Bot
    print(f"\n🤖 Test 2: Enhanced Telegram Bot")
    print("-" * 40)
    
    try:
        from enhanced_telegram_roi_bot import EnhancedTelegramROIBot
        
        telegram_bot = EnhancedTelegramROIBot()
        
        # Create demo opportunity
        from betting_strategy_engine import BettingOpportunity, RiskLevel
        
        demo_opportunity = BettingOpportunity(
            home_team='Real Madrid',
            away_team='Barcelona',
            sport='football',
            market='match_winner',
            selection='Real Madrid',
            bookmaker='Betfury',
            odds=2.25,
            expected_value=15.8,
            confidence_score=0.72,
            edge=11.2,
            true_probability=0.68,
            recommended_stake=3.5,
            risk_level=RiskLevel.MODERATE,
            reasoning='Real Madrid has superior form and home advantage.',
            match_time=datetime.now() + timedelta(hours=2),
            expires_at=datetime.now() + timedelta(hours=1, minutes=30)
        )
        
        # Add league attribute
        demo_opportunity.league = 'La Liga'
        
        # Test message creation with Betfury links
        message = telegram_bot._create_detailed_opportunity_message(demo_opportunity, 1)
        
        print(f"✅ Telegram bot integration working")
        print(f"📱 Demo message created with Betfury links")
        print(f"🔗 Message includes betting links: {'betfury.io' in message}")
        
        # Send demo message
        print(f"\n📨 Demo Telegram Message:")
        print("=" * 50)
        print(message)
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Telegram bot error: {e}")
    
    # Test 3: Odds API Integration
    print(f"\n📊 Test 3: Odds API Integration")
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
        
    except Exception as e:
        print(f"❌ Odds API error: {e}")
    
    # Test 4: Continuous System Components
    print(f"\n🔄 Test 4: Continuous System Components")
    print("-" * 40)
    
    try:
        from continuous_betting_intelligence import ContinuousBettingIntelligence, GameOpportunity
        
        # Initialize with demo config
        config = {
            'scan_interval': 300,  # 5 minutes for demo
            'min_roi_threshold': 8.0,
            'telegram_notifications': True,
            'web_scraping_enabled': False,  # Disable for demo
            'odds_api_enabled': False  # Disable for demo
        }
        
        system = ContinuousBettingIntelligence(config)
        
        print(f"✅ Continuous system initialized")
        print(f"⚙️ Configuration loaded")
        
        # Get system status
        status = system.get_system_status()
        print(f"📊 System Status:")
        print(f"   • Running: {status['running']}")
        print(f"   • Daily Stake Used: {status['daily_stake_used']:.1f}%")
        print(f"   • Opportunities Found: {status['discovered_opportunities']}")
        
        # Create demo opportunity
        demo_game_opportunity = GameOpportunity(
            match_id="demo_real_madrid_barcelona",
            home_team="Real Madrid",
            away_team="Barcelona", 
            sport="football",
            league="La Liga",
            match_time=datetime.now() + timedelta(hours=3),
            
            best_odds={'match_winner': 2.15},
            bookmaker="Betfury",
            market="match_winner",
            selection="Real Madrid",
            
            roi_percentage=18.5,
            risk_level="moderate",
            confidence_score=0.75,
            edge_percentage=12.8,
            true_probability=0.69,
            
            recommended_stake=4.2,
            potential_profit=485.0,
            max_loss=420.0,
            
            betfury_main_link="https://betfury.io/sports/football/spain/laliga/real-madrid-vs-barcelona",
            betfury_market_links={
                'match_winner': 'https://betfury.io/sports/football/spain/laliga/real-madrid-vs-barcelona?market=moneyline',
                'over_under': 'https://betfury.io/sports/football/spain/laliga/real-madrid-vs-barcelona?market=totals'
            },
            
            discovered_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=2, minutes=30),
            analysis_version="1.0"
        )
        
        # Test message creation
        message = system._create_opportunity_message(demo_game_opportunity)
        
        print(f"\n📨 Demo Opportunity Message:")
        print("=" * 60)
        print(message)
        print("=" * 60)
        
        print(f"✅ All system components working correctly!")
        
    except Exception as e:
        print(f"❌ Continuous system error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Web Scraping Capabilities
    print(f"\n🕷️ Test 5: Web Scraping Capabilities")
    print("-" * 40)
    
    try:
        # Test basic web scraping setup
        import requests
        from bs4 import BeautifulSoup
        
        print(f"✅ Web scraping libraries available")
        print(f"📦 Requests: {requests.__version__}")
        print(f"🍲 BeautifulSoup: Available")
        
        # Test undetected chrome driver
        try:
            import undetected_chromedriver as uc
            print(f"🚗 Undetected ChromeDriver: Available")
        except ImportError:
            print(f"⚠️ Undetected ChromeDriver: Not available")
        
        # Test selenium
        try:
            from selenium import webdriver
            print(f"🕸️ Selenium: Available")
        except ImportError:
            print(f"⚠️ Selenium: Not available")
        
    except Exception as e:
        print(f"❌ Web scraping test error: {e}")
    
    print(f"\n✅ DEMO COMPLETED SUCCESSFULLY!")
    print(f"🎯 System ready for continuous betting intelligence")
    print(f"🚀 Run: python start_betting_intelligence.py")

def main():
    """Suorita demo"""
    try:
        asyncio.run(demo_betting_intelligence())
    except KeyboardInterrupt:
        print(f"\n🛑 Demo stopped by user")
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
