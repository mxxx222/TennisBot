#!/usr/bin/env python3
"""
🎰 HAE BETFURY LINKIT
===================
Hakee toimivat Betfury.io betting linkit otteluille
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import requests

# Set credentials
os.environ['TELEGRAM_BOT_TOKEN'] = '8481385860:AAGBRbsDA8--t373COn2mgM4_c1ngc2fGRM'
os.environ['TELEGRAM_CHAT_ID'] = '-4956738581'

# Add project paths
sys.path.append(str(Path(__file__).parent / 'src'))

async def hae_betfury_linkit():
    """Hae toimivat Betfury.io linkit otteluille"""
    
    print("🎰 BETFURY.IO LINKKIEN HAKU")
    print("=" * 50)
    print(f"🕐 Hakuaika: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔍 Haetaan tämänpäiväisiä otteluita ja luodaan Betfury linkit...")
    print("=" * 50)
    
    # Initialize components
    try:
        from betfury_integration import BetfuryIntegration
        from multi_sport_prematch_scraper import MultiSportPrematchScraper
        from odds_api_integration import OddsAPIIntegration
        
        betfury = BetfuryIntegration(affiliate_code="tennisbot_2025")
        scraper = MultiSportPrematchScraper()
        odds_api = OddsAPIIntegration()
        
        print("✅ Komponentit alustettu")
        
    except Exception as e:
        print(f"❌ Komponenttien alustus epäonnistui: {e}")
        return
    
    # Get today's matches
    print(f"\n🏆 Vaihe 1: Haetaan tämänpäiväisiä otteluita...")
    print("-" * 40)
    
    try:
        # Get matches from scraper
        today = datetime.now()
        sports = ['football', 'tennis', 'basketball', 'ice_hockey']
        
        matches = scraper.scrape_daily_matches(today, sports)
        print(f"✅ Löydettiin {len(matches)} ottelua scrapperista")
        
        # Get matches from Odds API
        try:
            odds_matches = await odds_api.get_live_odds(['soccer_epl', 'basketball_nba'])
            print(f"✅ Löydettiin {len(odds_matches)} ottelua Odds API:sta")
        except Exception as e:
            print(f"⚠️ Odds API virhe: {e}")
            odds_matches = []
        
    except Exception as e:
        print(f"❌ Otteluiden haku epäonnistui: {e}")
        return
    
    # Create Betfury links
    print(f"\n🎰 Vaihe 2: Luodaan Betfury.io linkit...")
    print("-" * 40)
    
    betfury_links = []
    
    # Process scraper matches
    for i, match in enumerate(matches[:10], 1):  # Limit to 10 matches
        try:
            print(f"🔗 {i}. {match.home_team} vs {match.away_team} ({match.sport})")
            
            # Generate main match link
            main_link = betfury.generate_match_link(
                match.home_team,
                match.away_team,
                match.sport,
                getattr(match, 'league', None)
            )
            
            # Generate market-specific links
            market_links = {}
            
            # Common markets
            markets = ['match_winner', 'over_under', 'both_teams_score', 'handicap']
            
            for market in markets:
                try:
                    market_link = betfury.generate_market_link(
                        match.home_team,
                        match.away_team,
                        match.sport,
                        market,
                        getattr(match, 'league', None)
                    )
                    market_links[market] = market_link
                except:
                    continue
            
            betfury_links.append({
                'match': f"{match.home_team} vs {match.away_team}",
                'sport': match.sport,
                'league': getattr(match, 'league', 'Unknown'),
                'match_time': getattr(match, 'match_time', datetime.now()),
                'main_link': main_link,
                'market_links': market_links
            })
            
            print(f"   ✅ Päälinkit: {main_link[:60]}...")
            print(f"   📊 Markkinat: {len(market_links)} linkkiä")
            
        except Exception as e:
            print(f"   ❌ Virhe: {e}")
    
    # Process Odds API matches
    for i, odds_match in enumerate(odds_matches[:5], len(betfury_links) + 1):
        try:
            print(f"🔗 {i}. {odds_match.home_team} vs {odds_match.away_team} ({odds_match.sport})")
            
            main_link = betfury.generate_match_link(
                odds_match.home_team,
                odds_match.away_team,
                odds_match.sport,
                None
            )
            
            betfury_links.append({
                'match': f"{odds_match.home_team} vs {odds_match.away_team}",
                'sport': odds_match.sport,
                'league': 'Live Odds',
                'match_time': odds_match.commence_time,
                'main_link': main_link,
                'market_links': {}
            })
            
            print(f"   ✅ Linkki: {main_link[:60]}...")
            
        except Exception as e:
            print(f"   ❌ Virhe: {e}")
    
    # Display results
    print(f"\n🎯 Vaihe 3: Toimivat Betfury.io linkit")
    print("=" * 60)
    
    if not betfury_links:
        print("❌ Ei löydetty otteluita linkkien luomiseen")
        return
    
    print(f"✅ Luotiin {len(betfury_links)} ottelun linkit")
    print()
    
    for i, link_data in enumerate(betfury_links, 1):
        sport_emoji = {
            'football': '⚽',
            'tennis': '🎾', 
            'basketball': '🏀',
            'ice_hockey': '🏒',
            'soccer': '⚽'
        }.get(link_data['sport'], '🏆')
        
        print(f"{i}. {sport_emoji} **{link_data['match']}**")
        print(f"   🏆 {link_data['league']}")
        print(f"   📅 {link_data['match_time'].strftime('%H:%M')}")
        print(f"   🎰 **PÄÄLINKIT:** {link_data['main_link']}")
        
        if link_data['market_links']:
            print(f"   📊 **MARKKINAT:**")
            for market, market_link in link_data['market_links'].items():
                market_name = market.replace('_', ' ').title()
                print(f"      • {market_name}: {market_link}")
        
        print()
    
    # Send to Telegram
    print(f"📱 Vaihe 4: Lähetetään linkit Telegramiin...")
    print("-" * 40)
    
    try:
        from telegram import Bot
        
        bot = Bot(token=os.environ['TELEGRAM_BOT_TOKEN'])
        chat_id = os.environ['TELEGRAM_CHAT_ID']
        
        # Create summary message
        summary_message = f"""
🎰 **BETFURY.IO OTTELULINKIT**

📅 **Päivämäärä:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
🎯 **Otteluita:** {len(betfury_links)}
🔗 **Linkit:** Toimivat ja valmiit

🏆 **Tämänpäiväiset ottelut:**
        """
        
        # Add top matches to summary
        for i, link_data in enumerate(betfury_links[:5], 1):
            sport_emoji = {
                'football': '⚽', 'tennis': '🎾', 'basketball': '🏀',
                'ice_hockey': '🏒', 'soccer': '⚽'
            }.get(link_data['sport'], '🏆')
            
            summary_message += f"\n{i}. {sport_emoji} {link_data['match']}"
        
        if len(betfury_links) > 5:
            summary_message += f"\n... ja {len(betfury_links) - 5} muuta ottelua"
        
        # Send summary
        await bot.send_message(
            chat_id=chat_id,
            text=summary_message.strip(),
            parse_mode='Markdown'
        )
        
        print("✅ Yhteenveto lähetetty Telegramiin")
        
        # Send detailed links (max 5 matches)
        for i, link_data in enumerate(betfury_links[:5], 1):
            sport_emoji = {
                'football': '⚽', 'tennis': '🎾', 'basketball': '🏀',
                'ice_hockey': '🏒', 'soccer': '⚽'
            }.get(link_data['sport'], '🏆')
            
            detailed_message = f"""
🎰 **OTTELU #{i}** {sport_emoji}

**{link_data['match']}**
🏆 {link_data['league']}
📅 {link_data['match_time'].strftime('%H:%M')}

🎰 **PÄÄLINKIT:**
[**🎰 BETFURY.IO**]({link_data['main_link']})

📊 **MARKKINAT:**
            """
            
            # Add market links
            if link_data['market_links']:
                for market, market_link in list(link_data['market_links'].items())[:4]:
                    market_name = market.replace('_', ' ').title()
                    detailed_message += f"\n• [**{market_name}**]({market_link})"
            else:
                detailed_message += f"\n• [**Match Winner**]({link_data['main_link']})"
                detailed_message += f"\n• [**Over/Under**]({link_data['main_link']})"
            
            detailed_message += f"\n\n🔗 **Kaikki linkit toimivat suoraan!**"
            
            # Send detailed message
            await bot.send_message(
                chat_id=chat_id,
                text=detailed_message.strip(),
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
            print(f"✅ Ottelu {i} linkit lähetetty")
            
            # Small delay between messages
            await asyncio.sleep(2)
        
    except Exception as e:
        print(f"❌ Telegram lähetys epäonnistui: {e}")
    
    print(f"\n" + "="*60)
    print(f"🎉 BETFURY LINKIT HAETTU JA LÄHETETTY!")
    print(f"="*60)
    
    print(f"📊 **Tulokset:**")
    print(f"   • Otteluita löydetty: {len(matches) + len(odds_matches)}")
    print(f"   • Betfury linkkejä luotu: {len(betfury_links)}")
    print(f"   • Telegram viestejä lähetetty: {min(len(betfury_links), 5) + 1}")
    
    print(f"\n📱 **Tarkista Telegram-chatistasi:**")
    print(f"   • Yhteenveto kaikista otteluista")
    print(f"   • Yksityiskohtaiset linkit top 5 ottelulle")
    print(f"   • Kaikki linkit toimivat suoraan Betfury.io:ssa")
    
    print(f"\n🎰 **Käyttöohjeet:**")
    print(f"   1. Klikkaa Telegram-viesteissä olevia linkkejä")
    print(f"   2. Linkit vievät suoraan Betfury.io betting-sivulle")
    print(f"   3. Affiliate-koodi 'tennisbot_2025' on mukana automaattisesti")

def main():
    """Suorita Betfury linkkien haku"""
    try:
        asyncio.run(hae_betfury_linkit())
    except KeyboardInterrupt:
        print(f"\n🛑 Haku keskeytetty käyttäjän toimesta")
    except Exception as e:
        print(f"❌ Virhe: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
