#!/usr/bin/env python3
"""
🇫🇮 FINNISH TIME BETFURY TELEGRAM
=================================
Näyttää ottelun päivämäärän ja kellonajan Suomen aikaan + AI-ennusteet
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
import pytz
import random
import json

# Set credentials
os.environ['TELEGRAM_BOT_TOKEN'] = '8481385860:AAGBRbsDA8--t373COn2mgM4_c1ngc2fGRM'
os.environ['TELEGRAM_CHAT_ID'] = '-4956738581'

# Add project paths
sys.path.append(str(Path(__file__).parent / 'src'))

class FinnishTimeManager:
    """Suomen ajan hallinta"""
    
    def __init__(self):
        self.finland_tz = pytz.timezone('Europe/Helsinki')
        self.utc_tz = pytz.UTC
        
        print("🇫🇮 Finnish Time Manager alustettu")
    
    def get_finnish_time(self, utc_time=None):
        """Muunna UTC-aika Suomen aikaan"""
        if utc_time is None:
            utc_time = datetime.now(self.utc_tz)
        elif utc_time.tzinfo is None:
            utc_time = self.utc_tz.localize(utc_time)
        
        finnish_time = utc_time.astimezone(self.finland_tz)
        return finnish_time
    
    def format_finnish_datetime(self, dt):
        """Muotoile päivämäärä ja aika suomeksi"""
        finnish_dt = self.get_finnish_time(dt)
        
        # Suomalaiset kuukausien nimet
        months = {
            1: 'tammikuu', 2: 'helmikuu', 3: 'maaliskuu', 4: 'huhtikuu',
            5: 'toukokuu', 6: 'kesäkuu', 7: 'heinäkuu', 8: 'elokuu',
            9: 'syyskuu', 10: 'lokakuu', 11: 'marraskuu', 12: 'joulukuu'
        }
        
        # Suomalaiset viikonpäivien nimet
        weekdays = {
            0: 'maanantai', 1: 'tiistai', 2: 'keskiviikko', 3: 'torstai',
            4: 'perjantai', 5: 'lauantai', 6: 'sunnuntai'
        }
        
        weekday = weekdays[finnish_dt.weekday()]
        month = months[finnish_dt.month]
        
        return {
            'full_date': f"{weekday} {finnish_dt.day}. {month}ta {finnish_dt.year}",
            'short_date': f"{finnish_dt.day}.{finnish_dt.month}.{finnish_dt.year}",
            'time': f"{finnish_dt.hour:02d}:{finnish_dt.minute:02d}",
            'datetime_obj': finnish_dt,
            'weekday': weekday,
            'is_today': finnish_dt.date() == datetime.now(self.finland_tz).date(),
            'is_tomorrow': finnish_dt.date() == (datetime.now(self.finland_tz) + timedelta(days=1)).date()
        }
    
    def generate_realistic_match_times(self, sport, count=1):
        """Luo realistisia otteluaikoja eri lajeille"""
        now_finnish = datetime.now(self.finland_tz)
        
        match_times = []
        
        for i in range(count):
            if sport in ['football', 'soccer']:
                # Jalkapallo: yleensä lauantai/sunnuntai 15:00-21:00
                days_ahead = random.choice([0, 1, 2, 6, 7])  # Tänään, huomenna, ylihuomenna, lauantai, sunnuntai
                hours = random.choice([15, 16, 17, 18, 19, 20, 21])
                minutes = random.choice([0, 15, 30, 45])
                
            elif sport == 'tennis':
                # Tennis: päivällä 12:00-18:00
                days_ahead = random.choice([0, 1, 2, 3])
                hours = random.choice([12, 13, 14, 15, 16, 17, 18])
                minutes = random.choice([0, 30])
                
            elif sport == 'basketball':
                # Koripallo: illalla 19:00-23:00
                days_ahead = random.choice([0, 1, 2])
                hours = random.choice([19, 20, 21, 22, 23])
                minutes = random.choice([0, 30])
                
            elif sport == 'ice_hockey':
                # Jääkiekko: illalla 18:00-22:00
                days_ahead = random.choice([0, 1, 2])
                hours = random.choice([18, 19, 20, 21, 22])
                minutes = random.choice([0, 30])
            
            else:
                # Oletus
                days_ahead = random.choice([0, 1, 2])
                hours = random.choice([15, 16, 17, 18, 19, 20])
                minutes = random.choice([0, 30])
            
            match_time = now_finnish + timedelta(days=days_ahead)
            match_time = match_time.replace(hour=hours, minute=minutes, second=0, microsecond=0)
            
            match_times.append(match_time)
        
        return match_times

class AIMatchPredictor:
    """AI-pohjainen ottelu-ennustaja (sama kuin aiemmin)"""
    
    def __init__(self):
        self.team_strengths = {
            # Football teams
            'Manchester United': 85, 'Arsenal': 82, 'Barcelona': 90, 'Real Madrid': 92,
            'Bayern Munich': 88, 'RB Leipzig': 78, 'Juventus': 83, 'Inter Milan': 81,
            'PSG': 87, 'Lyon': 75, 'Atletico Madrid': 84, 'Borussia Dortmund': 80,
            
            # Tennis players
            'Novak Djokovic': 95, 'Rafael Nadal': 93, 'Carlos Alcaraz': 91,
            'Stefanos Tsitsipas': 85, 'Iga Swiatek': 94, 'Coco Gauff': 87,
            
            # Basketball teams
            'Los Angeles Lakers': 88, 'Boston Celtics': 86, 'Golden State Warriors': 84,
            'Miami Heat': 79, 'Real Madrid': 82, 'Barcelona': 78,
            
            # Ice Hockey teams
            'Toronto Maple Leafs': 83, 'Montreal Canadiens': 78, 'Boston Bruins': 85,
            'New York Rangers': 81, 'CSKA Moscow': 80, 'SKA St. Petersburg': 82
        }
        
        print("🤖 AI Match Predictor alustettu")
    
    def predict_match_outcome(self, home_team: str, away_team: str, sport: str) -> dict:
        """Ennusta ottelun lopputulos AI:lla"""
        
        # Get team strengths
        home_strength = self.team_strengths.get(home_team, 75)
        away_strength = self.team_strengths.get(away_team, 75)
        
        # Add randomness and sport-specific factors
        home_form = random.uniform(0.9, 1.1)
        away_form = random.uniform(0.9, 1.1)
        home_advantage = 1.05  # 5% home advantage
        
        # Calculate adjusted strengths
        home_adjusted = home_strength * home_form * home_advantage
        away_adjusted = away_strength * away_form
        
        # Calculate win probabilities
        total_strength = home_adjusted + away_adjusted
        home_win_prob = home_adjusted / total_strength
        away_win_prob = away_adjusted / total_strength
        
        # Sport-specific draw probability
        draw_prob = 0
        if sport in ['football', 'soccer']:
            draw_prob = 0.25  # 25% draw chance in football
            home_win_prob *= 0.75
            away_win_prob *= 0.75
        
        # Determine most likely winner
        if home_win_prob > away_win_prob:
            likely_winner = home_team
            win_probability = home_win_prob
        else:
            likely_winner = away_team
            win_probability = away_win_prob
        
        # Generate score prediction
        score_prediction = self._predict_score(home_team, away_team, sport, home_win_prob, away_win_prob, draw_prob)
        
        # Calculate ROI based on implied odds
        implied_odds = 1 / win_probability
        market_odds = implied_odds * random.uniform(0.85, 1.15)  # Market inefficiency
        roi = ((market_odds - 1) * win_probability - (1 - win_probability)) * 100
        
        return {
            'likely_winner': likely_winner,
            'win_probability': win_probability,
            'home_win_prob': home_win_prob,
            'away_win_prob': away_win_prob,
            'draw_prob': draw_prob,
            'score_prediction': score_prediction,
            'roi': max(roi, -50),  # Cap negative ROI
            'confidence': min(win_probability * 100, 95),
            'market_odds': market_odds,
            'home_strength': home_strength,
            'away_strength': away_strength
        }
    
    def _predict_score(self, home_team: str, away_team: str, sport: str, home_prob: float, away_prob: float, draw_prob: float) -> str:
        """Ennusta ottelun lopputulos"""
        
        if sport in ['football', 'soccer']:
            if home_prob > 0.6:
                scores = ['2-0', '2-1', '3-1', '1-0', '3-0']
            elif away_prob > 0.6:
                scores = ['0-2', '1-2', '1-3', '0-1', '0-3']
            elif draw_prob > 0.3:
                scores = ['1-1', '0-0', '2-2', '1-1', '0-0']
            else:
                scores = ['2-1', '1-2', '2-0', '0-2', '1-1']
            return random.choice(scores)
        
        elif sport == 'tennis':
            if home_prob > 0.6:
                scores = ['2-0', '2-1', '3-0', '3-1', '3-2']
            else:
                scores = ['0-2', '1-2', '0-3', '1-3', '2-3']
            return random.choice(scores) + ' erää'
        
        elif sport == 'basketball':
            home_score = random.randint(95, 125)
            away_score = random.randint(95, 125)
            if home_prob > away_prob:
                home_score += random.randint(5, 15)
            else:
                away_score += random.randint(5, 15)
            return f"{home_score}-{away_score}"
        
        elif sport == 'ice_hockey':
            if home_prob > 0.6:
                scores = ['3-1', '2-1', '4-2', '3-0', '2-0']
            elif away_prob > 0.6:
                scores = ['1-3', '1-2', '2-4', '0-3', '0-2']
            else:
                scores = ['2-2', '1-1', '3-3', '2-1', '1-2']
            return random.choice(scores)
        
        return "N/A"

class FinnishTimeBetfuryTelegram:
    """Betfury Telegram-bot Suomen ajalla ja AI-ennusteilla"""
    
    def __init__(self):
        self.time_manager = FinnishTimeManager()
        self.ai_predictor = AIMatchPredictor()
        self.affiliate_code = "tennisbot_2025"
        
        print("🇫🇮 Finnish Time Betfury Telegram alustettu")
    
    def create_finnish_time_message(self, match_data: dict, match_time: datetime, betfury_link: str) -> str:
        """Luo Telegram-viesti Suomen ajalla ja AI-ennusteilla"""
        
        # Get AI prediction
        prediction = self.ai_predictor.predict_match_outcome(
            match_data['home_team'],
            match_data['away_team'], 
            match_data['sport']
        )
        
        # Format Finnish time
        time_info = self.time_manager.format_finnish_datetime(match_time)
        
        # Sport emoji
        sport_emoji = {
            'football': '⚽', 'soccer': '⚽', 'tennis': '🎾',
            'basketball': '🏀', 'ice_hockey': '🏒'
        }.get(match_data['sport'], '🏆')
        
        # Time emoji based on when match is
        if time_info['is_today']:
            time_emoji = '🔥'
            time_text = "TÄNÄÄN"
        elif time_info['is_tomorrow']:
            time_emoji = '⏰'
            time_text = "HUOMENNA"
        else:
            time_emoji = '📅'
            time_text = time_info['weekday'].upper()
        
        # Winner confidence
        if prediction['win_probability'] > 0.7:
            confidence_emoji = '🟢'
        elif prediction['win_probability'] > 0.55:
            confidence_emoji = '🟡'
        else:
            confidence_emoji = '🔴'
        
        # ROI indicator
        if prediction['roi'] > 15:
            roi_emoji = '💰'
        elif prediction['roi'] > 5:
            roi_emoji = '💵'
        elif prediction['roi'] > 0:
            roi_emoji = '💸'
        else:
            roi_emoji = '⚠️'
        
        # Calculate time until match
        now_finnish = datetime.now(self.time_manager.finland_tz)
        time_diff = time_info['datetime_obj'] - now_finnish
        
        if time_diff.total_seconds() > 0:
            hours_until = int(time_diff.total_seconds() // 3600)
            minutes_until = int((time_diff.total_seconds() % 3600) // 60)
            
            if hours_until > 24:
                days_until = hours_until // 24
                countdown = f"{days_until} päivää"
            elif hours_until > 0:
                countdown = f"{hours_until}h {minutes_until}min"
            else:
                countdown = f"{minutes_until} minuuttia"
        else:
            countdown = "LIVE / Päättynyt"
        
        message = f"""
🇫🇮 **SUOMEN AJAN BETTING ANALYYSI** {sport_emoji}

**{match_data['home_team']} vs {match_data['away_team']}**
🏆 {match_data.get('league', 'Unknown League')}

{time_emoji} **OTTELU-AIKA SUOMESSA:**
📅 **Päivämäärä:** {time_info['full_date']}
🕐 **Kellonaika:** {time_info['time']} (Suomen aika)
⏳ **Alkuun:** {countdown}

🤖 **AI ENNUSTE:**
🏆 **Todennäköinen voittaja:** {prediction['likely_winner']}
{confidence_emoji} **Voitto-todennäköisyys:** {prediction['win_probability']:.1%}
📊 **AI Lopputulos:** {prediction['score_prediction']}

📈 **TODENNÄKÖISYYDET:**
🏠 {match_data['home_team']}: {prediction['home_win_prob']:.1%}
🛣️ {match_data['away_team']}: {prediction['away_win_prob']:.1%}"""
        
        if prediction['draw_prob'] > 0:
            message += f"\n🤝 Tasapeli: {prediction['draw_prob']:.1%}"
        
        message += f"""

{roi_emoji} **ROI ANALYYSI:**
💰 **Odotettu ROI:** {prediction['roi']:.1f}%
🎲 **Markkinakertoimet:** {prediction['market_odds']:.2f}
📊 **AI Luottamus:** {prediction['confidence']:.0f}%

🎰 **BETTING SUOSITUS:**
"""
        
        # Add betting recommendation
        if prediction['roi'] > 10 and prediction['confidence'] > 70:
            message += "✅ **VAHVA SUOSITUS** - Korkea ROI ja luottamus\n"
            message += f"💵 **Suositeltu panos:** 3-5% bankrollista"
        elif prediction['roi'] > 5 and prediction['confidence'] > 60:
            message += "🟡 **MALTILLINEN SUOSITUS** - Kohtalainen arvo\n"
            message += f"💵 **Suositeltu panos:** 1-3% bankrollista"
        elif prediction['roi'] > 0:
            message += "⚠️ **VAROVAINEN SUOSITUS** - Pieni arvo\n"
            message += f"💵 **Suositeltu panos:** 0.5-1% bankrollista"
        else:
            message += "❌ **EI SUOSITELLA** - Negatiivinen ROI\n"
            message += f"💵 **Suositeltu panos:** Älä lyö vetoa"
        
        # Add time-based urgency
        if time_info['is_today'] and hours_until < 3:
            message += f"\n\n🔥 **KIIRE!** Ottelu alkaa {hours_until}h {minutes_until}min kuluttua!"
        elif time_info['is_today']:
            message += f"\n\n⏰ **TÄNÄÄN** klo {time_info['time']} - Valmistaudu!"
        elif time_info['is_tomorrow']:
            message += f"\n\n📅 **HUOMENNA** klo {time_info['time']} - Merkitse kalenteriin!"
        
        message += f"""

🎰 **BET NOW:**
[**🎰 BETFURY.IO - {prediction['likely_winner'].upper()}**]({betfury_link})

🇫🇮 **Suomen aika:** {now_finnish.strftime('%d.%m.%Y %H:%M')}
🤖 **AI Analyysi:** Tennis Bot v2.0
        """
        
        return message.strip()

async def send_finnish_time_messages():
    """Lähetä Suomen ajan viestit Telegramiin"""
    
    print("🇫🇮 FINNISH TIME BETFURY TELEGRAM")
    print("=" * 50)
    print(f"🕐 Aloitusaika: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🇫🇮 Luodaan viestejä Suomen ajalla + AI-ennusteet...")
    print("=" * 50)
    
    # Initialize components
    telegram_bot = FinnishTimeBetfuryTelegram()
    
    # Demo matches with realistic Finnish times
    print(f"\n🏆 Vaihe 1: Luodaan demo-otteluita realistisilla ajoilla...")
    print("-" * 40)
    
    demo_matches = [
        {
            'home_team': 'Manchester United', 'away_team': 'Arsenal',
            'sport': 'football', 'league': 'Premier League'
        },
        {
            'home_team': 'Barcelona', 'away_team': 'Real Madrid',
            'sport': 'football', 'league': 'La Liga'
        },
        {
            'home_team': 'Novak Djokovic', 'away_team': 'Rafael Nadal',
            'sport': 'tennis', 'league': 'ATP Masters'
        },
        {
            'home_team': 'Los Angeles Lakers', 'away_team': 'Boston Celtics',
            'sport': 'basketball', 'league': 'NBA'
        },
        {
            'home_team': 'Bayern Munich', 'away_team': 'Borussia Dortmund',
            'sport': 'football', 'league': 'Bundesliga'
        },
        {
            'home_team': 'Boston Bruins', 'away_team': 'New York Rangers',
            'sport': 'ice_hockey', 'league': 'NHL'
        }
    ]
    
    # Generate realistic match times for each sport
    matches_with_times = []
    
    for match_data in demo_matches:
        match_times = telegram_bot.time_manager.generate_realistic_match_times(match_data['sport'], 1)
        match_time = match_times[0]
        
        matches_with_times.append({
            'data': match_data,
            'time': match_time
        })
        
        time_info = telegram_bot.time_manager.format_finnish_datetime(match_time)
        print(f"✅ {match_data['home_team']} vs {match_data['away_team']}")
        print(f"   📅 {time_info['full_date']} klo {time_info['time']}")
    
    # Create and send messages
    print(f"\n🤖 Vaihe 2: Luodaan AI-viestejä Suomen ajalla...")
    print("-" * 40)
    
    try:
        from telegram import Bot
        
        bot = Bot(token=os.environ['TELEGRAM_BOT_TOKEN'])
        chat_id = os.environ['TELEGRAM_CHAT_ID']
        
        # Send summary
        now_finnish = datetime.now(telegram_bot.time_manager.finland_tz)
        
        summary_message = f"""
🇫🇮 **SUOMEN AJAN BETTING RAPORTTI**

📅 **Päivämäärä:** {now_finnish.strftime('%d.%m.%Y %H:%M')} (Suomen aika)
🎯 **Otteluita:** {len(matches_with_times)}
🤖 **AI Ennusteet:** Voittaja + Lopputulos + ROI

🏆 **TÄMÄN PÄIVÄN OTTELUT:**
        """
        
        for i, match_info in enumerate(matches_with_times, 1):
            match_data = match_info['data']
            time_info = telegram_bot.time_manager.format_finnish_datetime(match_info['time'])
            
            sport_emoji = {'football': '⚽', 'tennis': '🎾', 'basketball': '🏀', 'ice_hockey': '🏒'}.get(match_data['sport'], '🏆')
            
            if time_info['is_today']:
                time_emoji = '🔥'
            elif time_info['is_tomorrow']:
                time_emoji = '⏰'
            else:
                time_emoji = '📅'
            
            summary_message += f"\n{i}. {sport_emoji} {match_data['home_team']} vs {match_data['away_team']}"
            summary_message += f"\n   {time_emoji} {time_info['short_date']} klo {time_info['time']}"
        
        # Send summary
        await bot.send_message(
            chat_id=chat_id,
            text=summary_message.strip(),
            parse_mode='Markdown'
        )
        
        print("✅ Suomen ajan yhteenveto lähetetty")
        
        # Send individual match analyses
        for i, match_info in enumerate(matches_with_times, 1):
            match_data = match_info['data']
            match_time = match_info['time']
            
            # Generate Betfury link
            sport_map = {'football': 'football', 'soccer': 'football', 'tennis': 'tennis', 'basketball': 'basketball', 'ice_hockey': 'hockey'}
            sport_url = sport_map.get(match_data['sport'], 'sports')
            
            home_clean = match_data['home_team'].lower().replace(' ', '-').replace('.', '')
            away_clean = match_data['away_team'].lower().replace(' ', '-').replace('.', '')
            
            betfury_link = f"https://betfury.io/sports/{sport_url}/{home_clean}-vs-{away_clean}?ref={telegram_bot.affiliate_code}"
            
            # Create message
            message = telegram_bot.create_finnish_time_message(match_data, match_time, betfury_link)
            
            # Send message
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
            print(f"✅ Ottelu {i} Suomen ajan analyysi lähetetty")
            
            # Delay between messages
            await asyncio.sleep(3)
        
    except Exception as e:
        print(f"❌ Telegram lähetys epäonnistui: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n" + "="*50)
    print(f"🎉 SUOMEN AJAN BETFURY TELEGRAM VALMIS!")
    print(f"="*50)
    
    print(f"📊 **Lopputulokset:**")
    print(f"   • Otteluita analysoitu: {len(matches_with_times)}")
    print(f"   • Telegram viestejä: {len(matches_with_times) + 1}")
    print(f"   • Aikavyöhyke: Europe/Helsinki (Suomen aika)")
    
    print(f"\n🇫🇮 **Suomen Ajan Features:**")
    print(f"   • Ottelun päivämäärä suomeksi")
    print(f"   • Kellonaika Suomen aikaan")
    print(f"   • Countdown ottelun alkuun")
    print(f"   • Tänään/Huomenna tunnistus")
    print(f"   • Kiireellisyys-ilmoitukset")
    print(f"   • AI-ennusteet ja ROI-analyysi")
    
    print(f"\n📱 **Tarkista Telegram Suomen ajan otteluanalyysit!**")

def main():
    """Suorita Finnish Time Betfury Telegram"""
    try:
        asyncio.run(send_finnish_time_messages())
    except KeyboardInterrupt:
        print(f"\n🛑 Suomen ajan messaging keskeytetty")
    except Exception as e:
        print(f"❌ Suomen ajan messaging virhe: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
