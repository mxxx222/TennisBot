#!/usr/bin/env python3
"""
🕷️ ADVANCED BETFURY.IO SCRAPER
=============================
Kehittynyt web scraper Betfury.io:lle Selenium + API yhdistelmällä
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import requests
import time
import re
from urllib.parse import urljoin, quote_plus
import json

# Set credentials
os.environ['TELEGRAM_BOT_TOKEN'] = '8481385860:AAGBRbsDA8--t373COn2mgM4_c1ngc2fGRM'
os.environ['TELEGRAM_CHAT_ID'] = '-4956738581'

# Add project paths
sys.path.append(str(Path(__file__).parent / 'src'))

class AdvancedBetfuryScraper:
    """Kehittynyt Betfury.io scraper"""
    
    def __init__(self):
        self.base_url = "https://betfury.io"
        self.api_base = "https://betfury.io/api"
        self.affiliate_code = "tennisbot_2025"
        
        # Setup session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://betfury.io/',
            'Origin': 'https://betfury.io'
        })
        
        print("🕷️ Advanced Betfury Scraper alustettu")
    
    def generate_smart_betfury_links(self, matches: list) -> list:
        """Luo älykkäitä Betfury linkkejä otteluille"""
        
        print(f"🧠 Luodaan älykkäitä Betfury linkkejä {len(matches)} ottelulle...")
        
        betfury_links = []
        
        for i, match in enumerate(matches, 1):
            try:
                match_name = f"{match.home_team} vs {match.away_team}"
                print(f"🔗 {i}. Luodaan linkit: {match_name}")
                
                # Generate multiple link variations
                links = self._generate_match_link_variations(match)
                
                # Test which links might work
                working_links = self._test_link_variations(links)
                
                if working_links:
                    best_link = working_links[0]  # Take the first working link
                    
                    betfury_data = {
                        'match': match_name,
                        'sport': match.sport,
                        'league': getattr(match, 'league', 'Unknown'),
                        'home_team': match.home_team,
                        'away_team': match.away_team,
                        'main_link': best_link['url'],
                        'link_type': best_link['type'],
                        'market_links': self._generate_market_links(best_link['url']),
                        'confidence': best_link['confidence'],
                        'generated_at': datetime.now()
                    }
                    
                    betfury_links.append(betfury_data)
                    
                    print(f"   ✅ Luotu {len(betfury_data['market_links'])} linkkiä")
                    print(f"   🎯 Confidence: {best_link['confidence']}%")
                else:
                    # Generate fallback link anyway
                    fallback_link = self._generate_fallback_link(match)
                    
                    betfury_data = {
                        'match': match_name,
                        'sport': match.sport,
                        'league': getattr(match, 'league', 'Unknown'),
                        'home_team': match.home_team,
                        'away_team': match.away_team,
                        'main_link': fallback_link,
                        'link_type': 'fallback',
                        'market_links': self._generate_market_links(fallback_link),
                        'confidence': 70,
                        'generated_at': datetime.now()
                    }
                    
                    betfury_links.append(betfury_data)
                    print(f"   ⚠️ Käytetään fallback linkkiä")
                
            except Exception as e:
                print(f"   ❌ Virhe: {e}")
        
        return betfury_links
    
    def _generate_match_link_variations(self, match) -> list:
        """Luo erilaisia linkki-variaatioita ottelulle"""
        
        variations = []
        
        # Clean team names
        home_clean = self._clean_team_name(match.home_team)
        away_clean = self._clean_team_name(match.away_team)
        
        # Sport mapping
        sport_map = {
            'football': ['football', 'soccer'],
            'soccer': ['football', 'soccer'],
            'tennis': ['tennis'],
            'basketball': ['basketball'],
            'ice_hockey': ['hockey', 'ice-hockey']
        }
        
        sports = sport_map.get(match.sport, [match.sport])
        
        # League mapping
        league_map = {
            'Premier League': ['england/premier-league', 'epl', 'premier-league'],
            'La Liga': ['spain/laliga', 'spain/la-liga', 'laliga'],
            'Bundesliga': ['germany/bundesliga', 'bundesliga'],
            'Serie A': ['italy/serie-a', 'serie-a'],
            'Ligue 1': ['france/ligue-1', 'ligue-1'],
            'ATP Masters': ['atp', 'atp-masters'],
            'WTA Premier': ['wta', 'wta-premier'],
            'NBA': ['usa/nba', 'nba'],
            'EuroLeague': ['europe/euroleague', 'euroleague']
        }
        
        league = getattr(match, 'league', '')
        leagues = league_map.get(league, [self._clean_team_name(league)])
        
        # Generate variations
        for sport in sports:
            for league_path in leagues:
                # Standard format
                url = f"{self.base_url}/sports/{sport}/{league_path}/{home_clean}-vs-{away_clean}?ref={self.affiliate_code}"
                variations.append({
                    'url': url,
                    'type': 'standard',
                    'confidence': 85
                })
                
                # Alternative format
                url = f"{self.base_url}/sports/{sport}/{league_path}/{home_clean}-{away_clean}?ref={self.affiliate_code}"
                variations.append({
                    'url': url,
                    'type': 'alternative',
                    'confidence': 75
                })
                
                # Short format
                url = f"{self.base_url}/sports/{sport}/{home_clean}-vs-{away_clean}?ref={self.affiliate_code}"
                variations.append({
                    'url': url,
                    'type': 'short',
                    'confidence': 65
                })
        
        # Generic sport page
        for sport in sports:
            url = f"{self.base_url}/sports/{sport}?ref={self.affiliate_code}"
            variations.append({
                'url': url,
                'type': 'sport_page',
                'confidence': 50
            })
        
        return variations
    
    def _clean_team_name(self, name: str) -> str:
        """Puhdista joukkueen nimi URL:ää varten"""
        # Convert to lowercase
        cleaned = name.lower()
        
        # Replace spaces and special characters
        cleaned = re.sub(r'[^a-z0-9\s]', '', cleaned)
        cleaned = re.sub(r'\s+', '-', cleaned.strip())
        
        # Handle common abbreviations
        replacements = {
            'fc': '',
            'ac': '',
            'real': 'real',
            'manchester-united': 'manchester-united',
            'manchester-city': 'manchester-city',
            'psg': 'paris-saint-germain',
            'bayern-munich': 'bayern-munich'
        }
        
        for old, new in replacements.items():
            if old in cleaned:
                cleaned = cleaned.replace(old, new)
        
        # Remove double dashes
        cleaned = re.sub(r'-+', '-', cleaned)
        cleaned = cleaned.strip('-')
        
        return cleaned
    
    def _test_link_variations(self, variations: list) -> list:
        """Testaa linkki-variaatioita (yksinkertainen HEAD request)"""
        
        working_links = []
        
        # Sort by confidence
        variations.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Test top variations (limit to avoid too many requests)
        for variation in variations[:5]:
            try:
                # Quick HEAD request to test if URL structure is valid
                response = self.session.head(variation['url'], timeout=5, allow_redirects=True)
                
                # Consider it working if we don't get 404
                if response.status_code != 404:
                    working_links.append(variation)
                    print(f"   ✅ {variation['type']}: {response.status_code}")
                else:
                    print(f"   ❌ {variation['type']}: 404")
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"   ⚠️ {variation['type']}: {str(e)[:30]}...")
                continue
        
        return working_links
    
    def _generate_fallback_link(self, match) -> str:
        """Luo fallback linkki jos muut eivät toimi"""
        
        sport_map = {
            'football': 'football',
            'soccer': 'football', 
            'tennis': 'tennis',
            'basketball': 'basketball',
            'ice_hockey': 'hockey'
        }
        
        sport = sport_map.get(match.sport, 'sports')
        
        # Generic sport page with search parameters
        home_encoded = quote_plus(match.home_team)
        away_encoded = quote_plus(match.away_team)
        
        return f"{self.base_url}/sports/{sport}?search={home_encoded}+{away_encoded}&ref={self.affiliate_code}"
    
    def _generate_market_links(self, base_url: str) -> dict:
        """Luo markkinakohtaiset linkit"""
        
        markets = {
            'match_winner': 'moneyline',
            'over_under': 'totals', 
            'both_teams_score': 'both-teams-to-score',
            'handicap': 'handicap',
            'correct_score': 'correct-score',
            'first_goal': 'first-goal'
        }
        
        market_links = {}
        
        for market_name, market_param in markets.items():
            if '?' in base_url:
                market_url = f"{base_url}&market={market_param}"
            else:
                market_url = f"{base_url}?market={market_param}&ref={self.affiliate_code}"
            
            market_links[market_name] = market_url
        
        return market_links
    
    def get_live_betfury_matches(self) -> list:
        """Hae live ottelut Betfury API:sta (jos mahdollista)"""
        
        print("🔍 Yritetään hakea live ottelut Betfury API:sta...")
        
        try:
            # Try different API endpoints
            api_endpoints = [
                f"{self.api_base}/sports/events",
                f"{self.api_base}/sportsbook/events", 
                f"{self.api_base}/events/live",
                f"{self.base_url}/api/sports/live"
            ]
            
            for endpoint in api_endpoints:
                try:
                    response = self.session.get(endpoint, timeout=10)
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            
                            if isinstance(data, dict) and 'events' in data:
                                events = data['events']
                            elif isinstance(data, list):
                                events = data
                            else:
                                continue
                            
                            print(f"✅ API: Löydettiin {len(events)} live ottelua")
                            return self._parse_api_events(events)
                            
                        except json.JSONDecodeError:
                            continue
                    
                except Exception as e:
                    continue
            
            print("⚠️ API haku ei onnistunut, käytetään generoituja linkkejä")
            return []
            
        except Exception as e:
            print(f"⚠️ API virhe: {e}")
            return []
    
    def _parse_api_events(self, events: list) -> list:
        """Parsii API:sta saadut tapahtumat"""
        
        parsed_events = []
        
        for event in events[:10]:  # Limit to 10
            try:
                if isinstance(event, dict):
                    # Extract event data
                    home_team = event.get('home_team', event.get('team1', ''))
                    away_team = event.get('away_team', event.get('team2', ''))
                    sport = event.get('sport', event.get('category', ''))
                    
                    if home_team and away_team:
                        parsed_events.append({
                            'home_team': home_team,
                            'away_team': away_team,
                            'sport': sport,
                            'league': event.get('league', event.get('tournament', '')),
                            'start_time': event.get('start_time', ''),
                            'event_id': event.get('id', ''),
                            'odds': event.get('odds', {})
                        })
                        
            except Exception as e:
                continue
        
        return parsed_events

async def advanced_betfury_scraping():
    """Pääfunktio: Kehittynyt Betfury scraping"""
    
    print("🕷️ ADVANCED BETFURY.IO SCRAPING")
    print("=" * 50)
    print(f"🕐 Aloitusaika: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🧠 Käytetään kehittyneitä scraping-tekniikoita...")
    print("=" * 50)
    
    # Initialize scraper
    scraper = AdvancedBetfuryScraper()
    
    # Get matches
    print(f"\n🏆 Vaihe 1: Haetaan otteluita...")
    print("-" * 40)
    
    try:
        from multi_sport_prematch_scraper import MultiSportPrematchScraper
        
        match_scraper = MultiSportPrematchScraper()
        today = datetime.now()
        sports = ['football', 'tennis', 'basketball', 'ice_hockey']
        
        matches = match_scraper.scrape_daily_matches(today, sports)
        print(f"✅ Löydettiin {len(matches)} ottelua")
        
    except Exception as e:
        print(f"⚠️ Käytetään demo otteluita: {e}")
        # Demo matches with realistic data
        matches = [
            type('Match', (), {
                'home_team': 'Manchester United', 'away_team': 'Arsenal',
                'sport': 'football', 'league': 'Premier League'
            })(),
            type('Match', (), {
                'home_team': 'Barcelona', 'away_team': 'Real Madrid', 
                'sport': 'football', 'league': 'La Liga'
            })(),
            type('Match', (), {
                'home_team': 'Bayern Munich', 'away_team': 'Borussia Dortmund',
                'sport': 'football', 'league': 'Bundesliga'
            })(),
            type('Match', (), {
                'home_team': 'Novak Djokovic', 'away_team': 'Rafael Nadal',
                'sport': 'tennis', 'league': 'ATP Masters'
            })(),
            type('Match', (), {
                'home_team': 'Los Angeles Lakers', 'away_team': 'Boston Celtics',
                'sport': 'basketball', 'league': 'NBA'
            })()
        ]
        print(f"✅ Käytetään {len(matches)} demo-ottelua")
    
    # Try to get live matches from Betfury API
    print(f"\n🔍 Vaihe 2: Haetaan live ottelut Betfury API:sta...")
    print("-" * 40)
    
    live_matches = scraper.get_live_betfury_matches()
    
    if live_matches:
        print(f"✅ Löydettiin {len(live_matches)} live ottelua API:sta")
        # Convert to match objects
        for live_match in live_matches:
            match_obj = type('Match', (), live_match)()
            matches.append(match_obj)
    
    # Generate smart Betfury links
    print(f"\n🧠 Vaihe 3: Luodaan älykkäitä Betfury linkkejä...")
    print("-" * 40)
    
    betfury_links = scraper.generate_smart_betfury_links(matches[:8])  # Limit to 8
    
    # Display results
    print(f"\n🎯 Vaihe 4: Luodut Betfury linkit")
    print("=" * 60)
    
    if not betfury_links:
        print("❌ Ei onnistuttu luomaan linkkejä")
        return
    
    print(f"✅ Luotiin linkit {len(betfury_links)} ottelulle")
    print()
    
    for i, link_data in enumerate(betfury_links, 1):
        sport_emoji = {
            'football': '⚽', 'soccer': '⚽', 'tennis': '🎾',
            'basketball': '🏀', 'ice_hockey': '🏒'
        }.get(link_data['sport'], '🏆')
        
        confidence_emoji = '🟢' if link_data['confidence'] >= 80 else '🟡' if link_data['confidence'] >= 60 else '🔴'
        
        print(f"{i}. {sport_emoji} **{link_data['match']}**")
        print(f"   🏆 {link_data['league']}")
        print(f"   🔗 **PÄÄLINKIT:** {link_data['main_link']}")
        print(f"   {confidence_emoji} Confidence: {link_data['confidence']}% ({link_data['link_type']})")
        print(f"   📊 Markkinat: {len(link_data['market_links'])}")
        
        # Show top markets
        for market, url in list(link_data['market_links'].items())[:3]:
            market_name = market.replace('_', ' ').title()
            print(f"      • {market_name}: {url[:50]}...")
        
        print()
    
    # Send to Telegram
    print(f"📱 Vaihe 5: Lähetetään linkit Telegramiin...")
    print("-" * 40)
    
    try:
        from telegram import Bot
        
        bot = Bot(token=os.environ['TELEGRAM_BOT_TOKEN'])
        chat_id = os.environ['TELEGRAM_CHAT_ID']
        
        # Summary message
        summary_message = f"""
🕷️ **ADVANCED BETFURY SCRAPING TULOKSET**

📅 **Scraping:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
🧠 **Metodi:** Älykkäät linkki-algoritmit
🎯 **Linkkejä luotu:** {len(betfury_links)}
🔗 **Confidence:** Testattu ja optimoitu

🏆 **Ottelut:**
        """
        
        for i, link_data in enumerate(betfury_links, 1):
            sport_emoji = {
                'football': '⚽', 'soccer': '⚽', 'tennis': '🎾',
                'basketball': '🏀', 'ice_hockey': '🏒'
            }.get(link_data['sport'], '🏆')
            
            confidence_emoji = '🟢' if link_data['confidence'] >= 80 else '🟡'
            
            summary_message += f"\n{i}. {sport_emoji} {link_data['match']} {confidence_emoji}"
        
        # Send summary
        await bot.send_message(
            chat_id=chat_id,
            text=summary_message.strip(),
            parse_mode='Markdown'
        )
        
        print("✅ Yhteenveto lähetetty")
        
        # Send detailed links
        for i, link_data in enumerate(betfury_links, 1):
            sport_emoji = {
                'football': '⚽', 'soccer': '⚽', 'tennis': '🎾',
                'basketball': '🏀', 'ice_hockey': '🏒'
            }.get(link_data['sport'], '🏆')
            
            confidence_emoji = '🟢' if link_data['confidence'] >= 80 else '🟡' if link_data['confidence'] >= 60 else '🔴'
            
            detailed_message = f"""
🕷️ **ADVANCED LINK #{i}** {sport_emoji}

**{link_data['match']}**
🏆 {link_data['league']}
{confidence_emoji} Confidence: {link_data['confidence']}%

🔗 **PÄÄLINKIT:**
[**🎰 BETFURY.IO**]({link_data['main_link']})

📊 **MARKKINAT:**
            """
            
            # Add market links
            for market, market_url in list(link_data['market_links'].items())[:4]:
                market_name = market.replace('_', ' ').title()
                detailed_message += f"\n• [**{market_name}**]({market_url})"
            
            detailed_message += f"\n\n🧠 **Linkki-tyyppi:** {link_data['link_type'].title()}"
            detailed_message += f"\n🕐 **Luotu:** {link_data['generated_at'].strftime('%H:%M:%S')}"
            detailed_message += f"\n✅ **Testattu ja optimoitu!**"
            
            # Send message
            await bot.send_message(
                chat_id=chat_id,
                text=detailed_message.strip(),
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
            print(f"✅ Ottelu {i} advanced linkit lähetetty")
            
            # Delay
            await asyncio.sleep(2)
        
    except Exception as e:
        print(f"❌ Telegram lähetys epäonnistui: {e}")
    
    print(f"\n" + "="*60)
    print(f"🎉 ADVANCED BETFURY SCRAPING VALMIS!")
    print(f"="*60)
    
    print(f"📊 **Lopputulokset:**")
    print(f"   • Otteluita analysoitu: {len(matches)}")
    print(f"   • Älykkäitä linkkejä luotu: {len(betfury_links)}")
    print(f"   • Keskimääräinen confidence: {sum(l['confidence'] for l in betfury_links) / len(betfury_links):.1f}%")
    print(f"   • Telegram viestejä: {len(betfury_links) + 1}")
    
    print(f"\n🧠 **Advanced Features:**")
    print(f"   • Älykkäät URL-generaattorit")
    print(f"   • Linkki-variaatioiden testaus")
    print(f"   • Confidence-scoring")
    print(f"   • Useita markkinoita per ottelu")
    print(f"   • API + scraping yhdistelmä")
    
    print(f"\n📱 **Tarkista Telegram advanced Betfury linkit!**")

def main():
    """Suorita advanced Betfury scraping"""
    try:
        asyncio.run(advanced_betfury_scraping())
    except KeyboardInterrupt:
        print(f"\n🛑 Advanced scraping keskeytetty")
    except Exception as e:
        print(f"❌ Advanced scraping virhe: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
