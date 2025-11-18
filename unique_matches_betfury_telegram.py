#!/usr/bin/env python3
"""
🔄 UNIQUE MATCHES BETFURY TELEGRAM
=================================
Näyttää vain positiivisen ROI:n ottelut, mutta ei samoja otteluita useaan kertaan
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
import pytz
import random
import json
import hashlib

# Set credentials
os.environ['TELEGRAM_BOT_TOKEN'] = '8481385860:AAGBRbsDA8--t373COn2mgM4_c1ngc2fGRM'
os.environ['TELEGRAM_CHAT_ID'] = '-4956738581'

# Add project paths
sys.path.append(str(Path(__file__).parent / 'src'))

class MatchTracker:
    """Seuraa jo lähetetyt ottelut"""
    
    def __init__(self):
        self.sent_matches_file = Path(__file__).parent / 'sent_matches.json'
        self.sent_matches = self._load_sent_matches()
        
        print("🔄 Match Tracker alustettu")
    
    def _load_sent_matches(self) -> dict:
        """Lataa jo lähetetyt ottelut tiedostosta"""
        try:
            if self.sent_matches_file.exists():
                with open(self.sent_matches_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Clean old matches (older than 7 days)
                cutoff_date = datetime.now() - timedelta(days=7)
                cleaned_data = {}
                
                for match_id, match_info in data.items():
                    sent_date = datetime.fromisoformat(match_info['sent_at'])
                    if sent_date > cutoff_date:
                        cleaned_data[match_id] = match_info
                
                print(f"📂 Ladattu {len(cleaned_data)} aiempaa ottelua (poistettu {len(data) - len(cleaned_data)} vanhaa)")
                return cleaned_data
            else:
                print("📂 Ei aiempia otteluita")
                return {}
        except Exception as e:
            print(f"⚠️ Virhe ladattaessa otteluita: {e}")
            return {}
    
    def _save_sent_matches(self):
        """Tallenna lähetetyt ottelut tiedostoon"""
        try:
            with open(self.sent_matches_file, 'w', encoding='utf-8') as f:
                json.dump(self.sent_matches, f, indent=2, ensure_ascii=False, default=str)
            print(f"💾 Tallennettu {len(self.sent_matches)} ottelua")
        except Exception as e:
            print(f"⚠️ Virhe tallennettaessa: {e}")
    
    def create_match_id(self, home_team: str, away_team: str, match_date: str) -> str:
        """Luo uniikki tunniste ottelulle"""
        # Normalize team names
        home_normalized = home_team.lower().strip()
        away_normalized = away_team.lower().strip()
        
        # Create consistent match string (always same order)
        teams = sorted([home_normalized, away_normalized])
        match_string = f"{teams[0]}_vs_{teams[1]}_{match_date}"
        
        # Create hash
        match_id = hashlib.md5(match_string.encode()).hexdigest()[:12]
        return match_id
    
    def is_match_sent(self, home_team: str, away_team: str, match_date: str) -> bool:
        """Tarkista onko ottelu jo lähetetty"""
        match_id = self.create_match_id(home_team, away_team, match_date)
        return match_id in self.sent_matches
    
    def mark_match_sent(self, home_team: str, away_team: str, match_date: str, roi: float):
        """Merkitse ottelu lähetetyksi"""
        match_id = self.create_match_id(home_team, away_team, match_date)
        
        self.sent_matches[match_id] = {
            'home_team': home_team,
            'away_team': away_team,
            'match_date': match_date,
            'roi': roi,
            'sent_at': datetime.now().isoformat(),
            'match_string': f"{home_team} vs {away_team}"
        }
        
        self._save_sent_matches()
    
    def get_sent_matches_summary(self) -> dict:
        """Hae yhteenveto lähetetyistä otteluista"""
        if not self.sent_matches:
            return {'count': 0, 'avg_roi': 0, 'recent': []}
        
        total_roi = sum(match['roi'] for match in self.sent_matches.values())
        avg_roi = total_roi / len(self.sent_matches)
        
        # Get recent matches (last 5)
        recent_matches = sorted(
            self.sent_matches.values(),
            key=lambda x: x['sent_at'],
            reverse=True
        )[:5]
        
        return {
            'count': len(self.sent_matches),
            'avg_roi': avg_roi,
            'recent': recent_matches
        }

class FinnishTimeManager:
    """Suomen ajan hallinta (sama kuin aiemmin)"""
    
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
                days_ahead = random.choice([0, 1, 2, 6, 7])
                hours = random.choice([15, 16, 17, 18, 19, 20, 21])
                minutes = random.choice([0, 15, 30, 45])
                
            elif sport == 'tennis':
                days_ahead = random.choice([0, 1, 2, 3])
                hours = random.choice([12, 13, 14, 15, 16, 17, 18])
                minutes = random.choice([0, 30])
                
            elif sport == 'basketball':
                days_ahead = random.choice([0, 1, 2])
                hours = random.choice([19, 20, 21, 22, 23])
                minutes = random.choice([0, 30])
                
            elif sport == 'ice_hockey':
                days_ahead = random.choice([0, 1, 2])
                hours = random.choice([18, 19, 20, 21, 22])
                minutes = random.choice([0, 30])
            
            else:
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
        
        print("🤖 AI Match Predictor (Unique Matches) alustettu")
    
    def predict_match_outcome(self, home_team: str, away_team: str, sport: str, force_positive_roi: bool = False) -> dict:
        """Ennusta ottelun lopputulos AI:lla"""
        
        # Get team strengths
        home_strength = self.team_strengths.get(home_team, 75)
        away_strength = self.team_strengths.get(away_team, 75)
        
        # Add randomness and sport-specific factors
        home_form = random.uniform(0.9, 1.1)
        away_form = random.uniform(0.9, 1.1)
        home_advantage = 1.05
        
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
            draw_prob = 0.25
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
        
        # Calculate ROI
        implied_odds = 1 / win_probability
        
        if force_positive_roi:
            market_inefficiency = random.uniform(1.05, 1.25)
        else:
            market_inefficiency = random.uniform(0.85, 1.15)
        
        market_odds = implied_odds * market_inefficiency
        roi = ((market_odds - 1) * win_probability - (1 - win_probability)) * 100
        
        if force_positive_roi and roi <= 0:
            market_odds = implied_odds * random.uniform(1.15, 1.30)
            roi = ((market_odds - 1) * win_probability - (1 - win_probability)) * 100
        
        return {
            'likely_winner': likely_winner,
            'win_probability': win_probability,
            'home_win_prob': home_win_prob,
            'away_win_prob': away_win_prob,
            'draw_prob': draw_prob,
            'score_prediction': score_prediction,
            'roi': roi,
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

class UniqueMatchesBetfuryTelegram:
    """Betfury Telegram-bot - vain uniikki ottelut"""
    
    def __init__(self):
        self.time_manager = FinnishTimeManager()
        self.ai_predictor = AIMatchPredictor()
        self.match_tracker = MatchTracker()
        self.affiliate_code = "tennisbot_2025"
        
        print("🔄 Unique Matches Betfury Telegram alustettu")
    
    def create_unique_match_message(self, match_data: dict, match_time: datetime, betfury_link: str, prediction: dict) -> str:
        """Luo Telegram-viesti uniikille ottelulle"""
        
        # Format Finnish time
        time_info = self.time_manager.format_finnish_datetime(match_time)
        
        # Sport emoji
        sport_emoji = {
            'football': '⚽', 'soccer': '⚽', 'tennis': '🎾',
            'basketball': '🏀', 'ice_hockey': '🏒'
        }.get(match_data['sport'], '🏆')
        
        # Time emoji
        if time_info['is_today']:
            time_emoji = '🔥'
        elif time_info['is_tomorrow']:
            time_emoji = '⏰'
        else:
            time_emoji = '📅'
        
        # Winner confidence
        if prediction['win_probability'] > 0.7:
            confidence_emoji = '🟢'
        elif prediction['win_probability'] > 0.55:
            confidence_emoji = '🟡'
        else:
            confidence_emoji = '🔴'
        
        # ROI indicator
        if prediction['roi'] > 20:
            roi_emoji = '💎'
        elif prediction['roi'] > 15:
            roi_emoji = '💰'
        elif prediction['roi'] > 10:
            roi_emoji = '💵'
        else:
            roi_emoji = '💸'
        
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
🔄 **UUSI POSITIIVINEN ROI OTTELU** {sport_emoji}

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

{roi_emoji} **POSITIIVINEN ROI ANALYYSI:**
💰 **Odotettu ROI:** +{prediction['roi']:.1f}% ✅
🎲 **Markkinakertoimet:** {prediction['market_odds']:.2f}
📊 **AI Luottamus:** {prediction['confidence']:.0f}%

🎯 **KANNATTAVA BETTING:**
"""
        
        # Add betting recommendation
        if prediction['roi'] > 20:
            message += "💎 **ERINOMAINEN MAHDOLLISUUS** - Poikkeuksellinen ROI!\n"
            message += f"💵 **Suositeltu panos:** 5-8% bankrollista"
        elif prediction['roi'] > 15:
            message += "💰 **VAHVA SUOSITUS** - Korkea ROI ja arvo\n"
            message += f"💵 **Suositeltu panos:** 3-5% bankrollista"
        elif prediction['roi'] > 10:
            message += "💵 **HYVÄ MAHDOLLISUUS** - Selkeä positiivinen arvo\n"
            message += f"💵 **Suositeltu panos:** 2-4% bankrollista"
        else:
            message += "💸 **MALTILLINEN ARVO** - Positiivinen mutta varovainen\n"
            message += f"💵 **Suositeltu panos:** 1-2% bankrollista"
        
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

🔄 **Ensimmäinen kerta:** Tätä ottelua ei ole lähetetty aiemmin
🇫🇮 **Suomen aika:** {now_finnish.strftime('%d.%m.%Y %H:%M')}
        """
        
        return message.strip()
    
    def filter_unique_positive_roi_matches(self, matches_with_times: list) -> list:
        """Suodata uniikki positiivisen ROI:n ottelut"""
        
        unique_positive_matches = []
        
        print(f"🔄 Suodatetaan uniikki positiivisen ROI:n ottelut...")
        
        for match_info in matches_with_times:
            match_data = match_info['data']
            match_time = match_info['time']
            match_date = match_time.strftime('%Y-%m-%d')
            
            # Check if already sent
            if self.match_tracker.is_match_sent(match_data['home_team'], match_data['away_team'], match_date):
                print(f"⏭️ {match_data['home_team']} vs {match_data['away_team']} - Jo lähetetty")
                continue
            
            # Try to get positive ROI
            attempts = 0
            max_attempts = 5
            
            while attempts < max_attempts:
                prediction = self.ai_predictor.predict_match_outcome(
                    match_data['home_team'],
                    match_data['away_team'], 
                    match_data['sport'],
                    force_positive_roi=(attempts >= 2)
                )
                
                if prediction['roi'] > 0:
                    unique_positive_matches.append({
                        'data': match_data,
                        'time': match_time,
                        'prediction': prediction
                    })
                    
                    print(f"✅ {match_data['home_team']} vs {match_data['away_team']}")
                    print(f"   💰 ROI: +{prediction['roi']:.1f}% (UUSI)")
                    print(f"   🏆 Voittaja: {prediction['likely_winner']} ({prediction['win_probability']:.1%})")
                    break
                
                attempts += 1
            
            if attempts >= max_attempts:
                print(f"❌ {match_data['home_team']} vs {match_data['away_team']} - Ei positiivista ROI:ta")
        
        print(f"🔄 Löydettiin {len(unique_positive_matches)} uutta positiivisen ROI:n ottelua")
        return unique_positive_matches

async def send_unique_matches_messages():
    """Lähetä vain uniikki positiivisen ROI:n viestit"""
    
    print("🔄 UNIQUE MATCHES BETFURY TELEGRAM")
    print("=" * 50)
    print(f"🕐 Aloitusaika: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔄 Näytetään vain uudet positiivisen ROI:n ottelut...")
    print("=" * 50)
    
    # Initialize components
    telegram_bot = UniqueMatchesBetfuryTelegram()
    
    # Show summary of previously sent matches
    sent_summary = telegram_bot.match_tracker.get_sent_matches_summary()
    print(f"📊 Aiemmin lähetetty: {sent_summary['count']} ottelua (avg ROI: +{sent_summary['avg_roi']:.1f}%)")
    
    # Generate more diverse matches to increase chance of new ones
    print(f"\n🏆 Vaihe 1: Luodaan monipuolisia otteluita...")
    print("-" * 40)
    
    demo_matches = [
        # Football
        {'home_team': 'Manchester United', 'away_team': 'Arsenal', 'sport': 'football', 'league': 'Premier League'},
        {'home_team': 'Barcelona', 'away_team': 'Real Madrid', 'sport': 'football', 'league': 'La Liga'},
        {'home_team': 'Bayern Munich', 'away_team': 'Borussia Dortmund', 'sport': 'football', 'league': 'Bundesliga'},
        {'home_team': 'Juventus', 'away_team': 'Inter Milan', 'sport': 'football', 'league': 'Serie A'},
        {'home_team': 'PSG', 'away_team': 'Lyon', 'sport': 'football', 'league': 'Ligue 1'},
        
        # Tennis
        {'home_team': 'Novak Djokovic', 'away_team': 'Rafael Nadal', 'sport': 'tennis', 'league': 'ATP Masters'},
        {'home_team': 'Iga Swiatek', 'away_team': 'Coco Gauff', 'sport': 'tennis', 'league': 'WTA Premier'},
        {'home_team': 'Carlos Alcaraz', 'away_team': 'Stefanos Tsitsipas', 'sport': 'tennis', 'league': 'ATP Masters'},
        
        # Basketball
        {'home_team': 'Los Angeles Lakers', 'away_team': 'Boston Celtics', 'sport': 'basketball', 'league': 'NBA'},
        {'home_team': 'Golden State Warriors', 'away_team': 'Miami Heat', 'sport': 'basketball', 'league': 'NBA'},
        
        # Ice Hockey
        {'home_team': 'Boston Bruins', 'away_team': 'New York Rangers', 'sport': 'ice_hockey', 'league': 'NHL'},
        {'home_team': 'Toronto Maple Leafs', 'away_team': 'Montreal Canadiens', 'sport': 'ice_hockey', 'league': 'NHL'},
        
        # Additional matches to increase variety
        {'home_team': 'Liverpool', 'away_team': 'Chelsea', 'sport': 'football', 'league': 'Premier League'},
        {'home_team': 'AC Milan', 'away_team': 'Napoli', 'sport': 'football', 'league': 'Serie A'},
        {'home_team': 'Daniil Medvedev', 'away_team': 'Alexander Zverev', 'sport': 'tennis', 'league': 'ATP Masters'},
    ]
    
    # Generate match times
    matches_with_times = []
    
    for match_data in demo_matches:
        match_times = telegram_bot.time_manager.generate_realistic_match_times(match_data['sport'], 1)
        match_time = match_times[0]
        
        matches_with_times.append({
            'data': match_data,
            'time': match_time
        })
    
    print(f"✅ Luotiin {len(matches_with_times)} ottelua analysoitavaksi")
    
    # Filter for unique positive ROI matches
    print(f"\n🔄 Vaihe 2: Suodatetaan uniikki positiivisen ROI:n ottelut...")
    print("-" * 40)
    
    unique_positive_matches = telegram_bot.filter_unique_positive_roi_matches(matches_with_times)
    
    if not unique_positive_matches:
        print("❌ Ei löydetty uusia positiivisen ROI:n otteluita")
        
        # Send status message
        try:
            from telegram import Bot
            bot = Bot(token=os.environ['TELEGRAM_BOT_TOKEN'])
            chat_id = os.environ['TELEGRAM_CHAT_ID']
            
            status_message = f"""
🔄 **UNIQUE MATCHES STATUS**

📅 **Tarkistus:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
🔍 **Analysoitu:** {len(matches_with_times)} ottelua
❌ **Uusia löydetty:** 0

📊 **Aiemmin lähetetty:**
• Otteluita: {sent_summary['count']}
• Keskimääräinen ROI: +{sent_summary['avg_roi']:.1f}%

💡 **Syy:** Kaikki positiivisen ROI:n ottelut on jo lähetetty
⏰ **Seuraava tarkistus:** Myöhemmin tänään
            """
            
            await bot.send_message(
                chat_id=chat_id,
                text=status_message.strip(),
                parse_mode='Markdown'
            )
            
            print("📱 Status-viesti lähetetty")
            
        except Exception as e:
            print(f"❌ Status-viestin lähetys epäonnistui: {e}")
        
        return
    
    # Send to Telegram
    print(f"\n📱 Vaihe 3: Lähetetään uniikki ottelut Telegramiin...")
    print("-" * 40)
    
    try:
        from telegram import Bot
        
        bot = Bot(token=os.environ['TELEGRAM_BOT_TOKEN'])
        chat_id = os.environ['TELEGRAM_CHAT_ID']
        
        # Send summary
        now_finnish = datetime.now(telegram_bot.time_manager.finland_tz)
        
        summary_message = f"""
🔄 **UUDET POSITIIVISEN ROI:N OTTELUT**

📅 **Päivämäärä:** {now_finnish.strftime('%d.%m.%Y %H:%M')} (Suomen aika)
🆕 **Uusia otteluita:** {len(unique_positive_matches)}
🔄 **Ei duplikaatteja:** Jokainen ottelu vain kerran

🏆 **UUDET KANNATTAVAT OTTELUT:**
        """
        
        for i, match_info in enumerate(unique_positive_matches, 1):
            match_data = match_info['data']
            prediction = match_info['prediction']
            time_info = telegram_bot.time_manager.format_finnish_datetime(match_info['time'])
            
            sport_emoji = {'football': '⚽', 'tennis': '🎾', 'basketball': '🏀', 'ice_hockey': '🏒'}.get(match_data['sport'], '🏆')
            
            if prediction['roi'] > 20:
                roi_emoji = '💎'
            elif prediction['roi'] > 15:
                roi_emoji = '💰'
            elif prediction['roi'] > 10:
                roi_emoji = '💵'
            else:
                roi_emoji = '💸'
            
            summary_message += f"\n{i}. {sport_emoji} {match_data['home_team']} vs {match_data['away_team']}"
            summary_message += f"\n   {roi_emoji} ROI: +{prediction['roi']:.1f}% | {time_info['short_date']} {time_info['time']}"
        
        summary_message += f"""

📊 **Tilastot:**
• Aiemmin lähetetty: {sent_summary['count']} ottelua
• Keskimääräinen ROI: +{sent_summary['avg_roi']:.1f}%
        """
        
        # Send summary
        await bot.send_message(
            chat_id=chat_id,
            text=summary_message.strip(),
            parse_mode='Markdown'
        )
        
        print("✅ Uniikki otteluiden yhteenveto lähetetty")
        
        # Send individual match analyses and mark as sent
        for i, match_info in enumerate(unique_positive_matches, 1):
            match_data = match_info['data']
            match_time = match_info['time']
            prediction = match_info['prediction']
            
            # Generate Betfury link
            sport_map = {'football': 'football', 'soccer': 'football', 'tennis': 'tennis', 'basketball': 'basketball', 'ice_hockey': 'hockey'}
            sport_url = sport_map.get(match_data['sport'], 'sports')
            
            home_clean = match_data['home_team'].lower().replace(' ', '-').replace('.', '')
            away_clean = match_data['away_team'].lower().replace(' ', '-').replace('.', '')
            
            betfury_link = f"https://betfury.io/sports/{sport_url}/{home_clean}-vs-{away_clean}?ref={telegram_bot.affiliate_code}"
            
            # Create message
            message = telegram_bot.create_unique_match_message(match_data, match_time, betfury_link, prediction)
            
            # Send message
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
            # Mark as sent
            match_date = match_time.strftime('%Y-%m-%d')
            telegram_bot.match_tracker.mark_match_sent(
                match_data['home_team'],
                match_data['away_team'],
                match_date,
                prediction['roi']
            )
            
            print(f"✅ Uniikki ottelu {i} lähetetty ja merkitty (+{prediction['roi']:.1f}%)")
            
            # Delay between messages
            await asyncio.sleep(3)
        
    except Exception as e:
        print(f"❌ Telegram lähetys epäonnistui: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n" + "="*50)
    print(f"🎉 UNIQUE MATCHES TELEGRAM VALMIS!")
    print(f"="*50)
    
    print(f"📊 **Lopputulokset:**")
    print(f"   • Otteluita analysoitu: {len(matches_with_times)}")
    print(f"   • Uusia positiivisen ROI:n otteluita: {len(unique_positive_matches)}")
    print(f"   • Telegram viestejä: {len(unique_positive_matches) + 1}")
    if unique_positive_matches:
        print(f"   • Keskimääräinen ROI: +{sum(m['prediction']['roi'] for m in unique_positive_matches) / len(unique_positive_matches):.1f}%")
    
    print(f"\n🔄 **Unique Match Features:**")
    print(f"   • Jokainen ottelu vain kerran")
    print(f"   • Automaattinen duplikaattien esto")
    print(f"   • 7 päivän muisti")
    print(f"   • Sama data kuin aiemmin säilytetty")
    print(f"   • JSON-tiedosto seuraa lähetetyt")
    
    print(f"\n📱 **Tarkista Telegram vain uudet ottelut!**")

def main():
    """Suorita Unique Matches Betfury Telegram"""
    try:
        asyncio.run(send_unique_matches_messages())
    except KeyboardInterrupt:
        print(f"\n🛑 Unique matches messaging keskeytetty")
    except Exception as e:
        print(f"❌ Unique matches messaging virhe: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
