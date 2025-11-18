#!/usr/bin/env python3
"""
🎰 BETFURY TELEGRAM INTEGRATION TEST
===================================
Test script to demonstrate the integration of Betfury.io betting links
with the enhanced Telegram ROI bot for all match opportunities.

This test shows how every betting opportunity now includes direct links
to Betfury.io betting pages for easy access to place bets.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add project paths
sys.path.append(str(Path(__file__).parent / 'src'))

# Import modules
try:
    from enhanced_telegram_roi_bot import EnhancedTelegramROIBot
    from betfury_integration import BetfuryIntegration
    from betting_strategy_engine import BettingOpportunity, RiskLevel
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"❌ Required modules not available: {e}")
    MODULES_AVAILABLE = False

async def test_betfury_telegram_integration():
    """Test Betfury integration with Telegram bot"""
    
    print("🎰 BETFURY TELEGRAM INTEGRATION TEST")
    print("=" * 50)
    
    if not MODULES_AVAILABLE:
        print("❌ Cannot run test - required modules not available")
        return
    
    # Initialize components
    print("🤖 Initializing Enhanced Telegram ROI Bot...")
    telegram_bot = EnhancedTelegramROIBot()
    
    print("🎰 Initializing Betfury Integration...")
    betfury = BetfuryIntegration(affiliate_code="tennisbot_2025")
    
    # Test 1: Create sample betting opportunities with Betfury links
    print(f"\n🎯 Test 1: Creating sample opportunities with Betfury links")
    
    sample_opportunities = [
        {
            'home_team': 'Manchester City',
            'away_team': 'Arsenal',
            'sport': 'football',
            'league': 'Premier League',
            'market': 'match_winner',
            'selection': 'Manchester City',
            'bookmaker': 'Betfury',
            'odds': 2.15,
            'expected_value': 18.5,
            'confidence_score': 0.78,
            'edge': 12.3,
            'true_probability': 0.65,
            'recommended_stake': 4.2,
            'risk_level': RiskLevel.MODERATE,
            'reasoning': 'Manchester City has superior form and home advantage. Arsenal missing key players.',
            'match_time': datetime.now() + timedelta(hours=2),
            'expires_at': datetime.now() + timedelta(hours=1, minutes=45)
        },
        {
            'home_team': 'Novak Djokovic',
            'away_team': 'Carlos Alcaraz',
            'sport': 'tennis',
            'league': 'ATP Masters',
            'market': 'match_winner',
            'selection': 'Novak Djokovic',
            'bookmaker': 'Betfury',
            'odds': 2.80,
            'expected_value': 22.1,
            'confidence_score': 0.72,
            'edge': 15.8,
            'true_probability': 0.58,
            'recommended_stake': 3.8,
            'risk_level': RiskLevel.MODERATE,
            'reasoning': 'Djokovic has excellent hard court record and experience advantage in big matches.',
            'match_time': datetime.now() + timedelta(hours=4),
            'expires_at': datetime.now() + timedelta(hours=3, minutes=30)
        },
        {
            'home_team': 'Los Angeles Lakers',
            'away_team': 'Boston Celtics',
            'sport': 'basketball',
            'league': 'NBA',
            'market': 'over_under',
            'selection': 'Over 225.5',
            'bookmaker': 'Betfury',
            'odds': 1.95,
            'expected_value': 14.2,
            'confidence_score': 0.69,
            'edge': 8.7,
            'true_probability': 0.62,
            'recommended_stake': 3.1,
            'risk_level': RiskLevel.CONSERVATIVE,
            'reasoning': 'Both teams average high scoring games. Fast pace expected.',
            'match_time': datetime.now() + timedelta(hours=6),
            'expires_at': datetime.now() + timedelta(hours=5, minutes=15)
        }
    ]
    
    # Convert to BettingOpportunity objects
    opportunities = []
    for opp_data in sample_opportunities:
        opportunity = BettingOpportunity(
            home_team=opp_data['home_team'],
            away_team=opp_data['away_team'],
            sport=opp_data['sport'],
            market=opp_data['market'],
            selection=opp_data['selection'],
            bookmaker=opp_data['bookmaker'],
            odds=opp_data['odds'],
            expected_value=opp_data['expected_value'],
            confidence_score=opp_data['confidence_score'],
            edge=opp_data['edge'],
            true_probability=opp_data['true_probability'],
            recommended_stake=opp_data['recommended_stake'],
            risk_level=opp_data['risk_level'],
            reasoning=opp_data['reasoning'],
            match_time=opp_data['match_time'],
            expires_at=opp_data['expires_at']
        )
        
        # Add league attribute
        opportunity.league = opp_data['league']
        opportunities.append(opportunity)
    
    print(f"✅ Created {len(opportunities)} sample opportunities")
    
    # Test 2: Generate individual Betfury links
    print(f"\n🔗 Test 2: Individual Betfury link generation")
    
    for i, opportunity in enumerate(opportunities, 1):
        print(f"\n📊 Opportunity {i}: {opportunity.home_team} vs {opportunity.away_team}")
        
        # Generate main match link
        main_link = betfury.generate_match_link(
            opportunity.home_team,
            opportunity.away_team,
            opportunity.sport,
            opportunity.league
        )
        print(f"🎰 Main Link: {main_link}")
        
        # Generate market-specific link
        market_link = betfury.generate_market_link(
            opportunity.home_team,
            opportunity.away_team,
            opportunity.sport,
            opportunity.market,
            opportunity.league
        )
        print(f"🎯 Market Link: {market_link}")
        
        # Generate multiple links
        all_links = betfury.generate_multiple_links({
            'home_team': opportunity.home_team,
            'away_team': opportunity.away_team,
            'sport': opportunity.sport,
            'league': opportunity.league
        })
        
        print(f"📋 All Links:")
        for link_type, url in all_links.items():
            print(f"   • {link_type}: {url}")
    
    # Test 3: Test Telegram message formatting with Betfury links
    print(f"\n📱 Test 3: Telegram messages with Betfury links")
    
    for i, opportunity in enumerate(opportunities, 1):
        print(f"\n" + "="*60)
        print(f"📨 TELEGRAM MESSAGE {i} - {opportunity.sport.upper()}")
        print("="*60)
        
        # Create detailed opportunity message (includes Betfury links)
        message = telegram_bot._create_detailed_opportunity_message(opportunity, i)
        print(message)
        
        # Also test the Betfury links creation separately
        print(f"\n🔗 Betfury Links Test:")
        betfury_links = telegram_bot._create_betfury_links(opportunity)
        print(betfury_links)
    
    # Test 4: Test opportunities summary with Betfury integration
    print(f"\n" + "="*60)
    print(f"📊 OPPORTUNITIES SUMMARY WITH BETFURY INTEGRATION")
    print("="*60)
    
    summary_message = telegram_bot._create_opportunities_summary(opportunities)
    print(summary_message)
    
    # Add Betfury platform info
    betfury_info = betfury.get_betfury_info()
    print(f"\n🎰 **BETTING PLATFORM INFO:**")
    print(f"• Platform: {betfury_info['platform']}")
    print(f"• Description: {betfury_info['description']}")
    print(f"• Supported Sports: {len(betfury_info['supported_sports'])}")
    print(f"• Features: {', '.join(betfury_info['features'][:3])}")
    
    # Test 5: Test sending to Telegram (demo mode)
    print(f"\n📤 Test 5: Sending to Telegram (Demo Mode)")
    
    print(f"\n🤖 Sending opportunities analysis to Telegram...")
    await telegram_bot._send_opportunities_analysis(int(telegram_bot.chat_id or "123456789"), opportunities)
    
    # Test 6: Test betting buttons for inline keyboards
    print(f"\n🔘 Test 6: Betting buttons for inline keyboards")
    
    for i, opportunity in enumerate(opportunities, 1):
        match_data = {
            'home_team': opportunity.home_team,
            'away_team': opportunity.away_team,
            'sport': opportunity.sport,
            'league': opportunity.league
        }
        
        buttons = betfury.create_betting_buttons(match_data)
        
        print(f"\n📱 Buttons for {opportunity.home_team} vs {opportunity.away_team}:")
        for button in buttons:
            print(f"   • {button['text']}: {button['url']}")
    
    # Test 7: Test Telegram message with embedded links
    print(f"\n📝 Test 7: Telegram message with embedded links")
    
    for opportunity in opportunities[:1]:  # Test with first opportunity
        match_data = {
            'home_team': opportunity.home_team,
            'away_team': opportunity.away_team,
            'sport': opportunity.sport,
            'league': opportunity.league
        }
        
        embedded_message = betfury.create_telegram_message_with_links(match_data)
        
        print(f"\n📨 Embedded Links Message:")
        print(embedded_message)
    
    print(f"\n✅ BETFURY TELEGRAM INTEGRATION TEST COMPLETED!")
    print(f"🎰 All betting opportunities now include direct Betfury.io links")
    print(f"🔗 Users can click directly from Telegram to place bets")
    print(f"📱 Multiple market options available for each match")

def main():
    """Run the test"""
    try:
        asyncio.run(test_betfury_telegram_integration())
    except KeyboardInterrupt:
        print(f"\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
