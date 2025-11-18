#!/usr/bin/env python3
"""
🔴 LIVE FOCUSED BETFURY TELEGRAM
===============================
Keskittyy tämän päivän, huomisen ja live-otteluihin. Live-otteluista voi lähettää useita ilmoituksia.
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

class LiveMatchTracker:
    """Seuraa live-otteluita ja niiden ROI-muutoksia"""
    
    def __init__(self):
        self.live_matches_file = Path(__file__).parent / 'live_matches.json'
        self.live_matches = self._load_live_matches()
        
        print("🔴 Live Match Tracker alustettu")
    
    def _load_live_matches(self) -> dict:
        """Lataa live-otteluiden tiedot"""
        try:
            if self.live_matches_file.exists():
                with open(self.live_matches_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Clean old matches (older than 2 days for live matches)
                cutoff_date = datetime.now() - timedelta(days=2)
                cleaned_data = {}
                
                for match_id, match_info in data.items():
                    last_update = datetime.fromisoformat(match_info['last_update'])
                    if last_update > cutoff_date:
                        cleaned_data[match_id] = match_info
                
                print(f"🔴 Ladattu {len(cleaned_data)} live-ottelua (poistettu {len(data) - len(cleaned_data)} vanhaa)")
                return cleaned_data
            else:
                print("🔴 Ei aiempia live-otteluita")
                return {}
        except Exception as e:
            print(f"⚠️ Virhe ladattaessa live-otteluita: {e}")
            return {}
    
    def _save_live_matches(self):
        """Tallenna live-otteluiden tiedot"""
        try:
            with open(self.live_matches_file, 'w', encoding='utf-8') as f:
                json.dump(self.live_matches, f, indent=2, ensure_ascii=False, default=str)
            print(f"💾 Tallennettu {len(self.live_matches)} live-ottelua")
        except Exception as e:
            print(f"⚠️ Virhe tallennettaessa: {e}")
    
    def create_match_id(self, home_team: str, away_team: str, match_date: str) -> str:
        """Luo uniikki tunniste ottelulle"""
        home_normalized = home_team.lower().strip()
        away_normalized = away_team.lower().strip()
        teams = sorted([home_normalized, away_normalized])
        match_string = f"{teams[0]}_vs_{teams[1]}_{match_date}"
        match_id = hashlib.md5(match_string.encode()).hexdigest()[:12]
        return match_id
    
    def should_send_live_update(self, home_team: str, away_team: str, match_date: str, 
                               roi: float, confidence: float, is_live: bool) -> dict:
        """Tarkista pitääkö lähettää live-päivitys"""
        
        match_id = self.create_match_id(home_team, away_team, match_date)
        
        if match_id not in self.live_matches:
            # Uusi ottelu
            self.live_matches[match_id] = {
                'home_team': home_team,
                'away_team': away_team,
                'match_date': match_date,
                'first_roi': roi,
                'best_roi': roi,
                'first_confidence': confidence,
                'best_confidence': confidence,
                'notifications_sent': 0,
                'last_roi': roi,
                'last_confidence': confidence,
                'last_update': datetime.now().isoformat(),
                'is_live': is_live,
                'match_string': f"{home_team} vs {away_team}"
            }
            self._save_live_matches()
            
            return {
                'should_send': True,
                'reason': 'new_match',
                'notification_type': 'live' if is_live else 'upcoming',
                'improvement': None
            }
        
        # Olemassa oleva ottelu
        match_info = self.live_matches[match_id]
        
        # Päivitä tiedot
        match_info['last_roi'] = roi
        match_info['last_confidence'] = confidence
        match_info['last_update'] = datetime.now().isoformat()
        match_info['is_live'] = is_live
        
        # Tarkista pitääkö lähettää päivitys
        should_send = False
        reason = None
        improvement = None
        
        # Live-otteluille löyhemmät kriteerit
        if is_live:
            # ROI parantunut merkittävästi (live: 3%+, muut: 5%+)
            roi_improvement = roi - match_info['best_roi']
            if roi_improvement >= 3.0:
                should_send = True
                reason = 'roi_improvement'
                improvement = f"+{roi_improvement:.1f}% ROI"
                match_info['best_roi'] = roi
            
            # Confidence noussut yli 70%
            elif confidence >= 70 and match_info['best_confidence'] < 70:
                should_send = True
                reason = 'high_confidence'
                improvement = f"Confidence: {confidence:.0f}%"
                match_info['best_confidence'] = confidence
            
            # Confidence parantunut merkittävästi (10%+)
            elif confidence - match_info['best_confidence'] >= 10:
                should_send = True
                reason = 'confidence_improvement'
                improvement = f"+{confidence - match_info['best_confidence']:.0f}% Confidence"
                match_info['best_confidence'] = confidence
        
        else:
            # Ei-live otteluille tiukemmat kriteerit
            roi_improvement = roi - match_info['best_roi']
            if roi_improvement >= 5.0:
                should_send = True
                reason = 'roi_improvement'
                improvement = f"+{roi_improvement:.1f}% ROI"
                match_info['best_roi'] = roi
            
            elif confidence >= 75 and match_info['best_confidence'] < 75:
                should_send = True
                reason = 'high_confidence'
                improvement = f"Confidence: {confidence:.0f}%"
                match_info['best_confidence'] = confidence
        
        # Rajoita ilmoitusten määrää
        if should_send:
            if is_live and match_info['notifications_sent'] >= 5:  # Live: max 5 ilmoitusta
                should_send = False
                reason = 'max_notifications_reached'
            elif not is_live and match_info['notifications_sent'] >= 2:  # Ei-live: max 2 ilmoitusta
                should_send = False
                reason = 'max_notifications_reached'
        
        if should_send:
            match_info['notifications_sent'] += 1
        
        self._save_live_matches()
        
        return {
            'should_send': should_send,
            'reason': reason,
            'notification_type': 'live_update' if is_live else 'update',
            'improvement': improvement,
            'notifications_sent': match_info['notifications_sent']
        }

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
        
        months = {
            1: 'tammikuu', 2: 'helmikuu', 3: 'maaliskuu', 4: 'huhtikuu',
            5: 'toukokuu', 6: 'kesäkuu', 7: 'heinäkuu', 8: 'elokuu',
            9: 'syyskuu', 10: 'lokakuu', 11: 'marraskuu', 12: 'joulukuu'
        }
        
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
    
    def generate_today_tomorrow_matches(self, sport, count=1):
        """Luo tämän päivän ja huomisen otteluita realistisilla ajoilla"""
        now_finnish = datetime.now(self.finland_tz)
        current_hour = now_finnish.hour
        
        match_times = []
        
        for i in range(count):
            # Älykäs päivän valinta: jos on myöhä (21+ tai aikainen 0-8), suosi huomista
            if current_hour >= 21 or current_hour <= 8:
                # Myöhä illalla tai aikaisin aamulla - 80% huomenna
                days_ahead = 1 if random.random() < 0.8 else 0
            elif current_hour >= 18:
                # Ilta - 60% huomenna
                days_ahead = 1 if random.random() < 0.6 else 0
            else:
                # Päivä - 30% huomenna
                days_ahead = 1 if random.random() < 0.3 else 0
            
            target_date = now_finnish + timedelta(days=days_ahead)
            
            # Realistiset ajat eri lajeille
            if sport in ['football', 'soccer']:
                # Jalkapallo: viikonloppuisin päivällä, arkisin illalla
                if target_date.weekday() >= 5:  # Lauantai tai sunnuntai
                    hours = random.choice([13, 14, 15, 16, 17, 18, 19, 20])
                    minutes = random.choice([0, 15, 30, 45])
                else:  # Arkipäivä
                    hours = random.choice([18, 19, 20, 21])
                    minutes = random.choice([0, 15, 30, 45])
                    
            elif sport == 'tennis':
                # Tennis: päivällä ja aikaisessa illassa
                if target_date.weekday() >= 5:  # Viikonloppu
                    hours = random.choice([11, 12, 13, 14, 15, 16, 17, 18])
                else:  # Arkipäivä
                    hours = random.choice([14, 15, 16, 17, 18, 19])
                minutes = random.choice([0, 30])
                
            elif sport == 'basketball':
                # Koripallo: illalla (NBA-ajat huomioiden aikaerot)
                if target_date.weekday() >= 5:  # Viikonloppu
                    hours = random.choice([19, 20, 21, 22, 23, 0, 1, 2])  # Myös yöottelut USA:sta
                else:  # Arkipäivä
                    hours = random.choice([20, 21, 22, 23, 0, 1, 2])
                minutes = random.choice([0, 30])
                
            elif sport == 'ice_hockey':
                # Jääkiekko: illalla
                if target_date.weekday() >= 5:  # Viikonloppu
                    hours = random.choice([18, 19, 20, 21, 22])
                else:  # Arkipäivä
                    hours = random.choice([19, 20, 21, 22])
                minutes = random.choice([0, 30])
                
            else:
                # Oletus
                hours = random.choice([15, 16, 17, 18, 19, 20])
                minutes = random.choice([0, 30])
            
            # Käsittele yöajat (0-2) seuraavana päivänä
            if hours <= 2:
                target_date = target_date + timedelta(days=1)
            
            # Jos tänään ja aika on jo mennyt, siirrä huomiseen
            if days_ahead == 0:
                proposed_time = target_date.replace(hour=hours, minute=minutes, second=0, microsecond=0)
                if proposed_time <= now_finnish + timedelta(minutes=30):  # Vähintään 30min tulevaisuudessa
                    target_date = target_date + timedelta(days=1)
            
            match_time = target_date.replace(hour=hours, minute=minutes, second=0, microsecond=0)
            match_times.append(match_time)
        
        return match_times
    
    def generate_live_matches(self, sport, count=1):
        """Luo live-otteluita (käynnissä olevia) realistisilla ajoilla"""
        now_finnish = datetime.now(self.finland_tz)
        current_hour = now_finnish.hour
        
        match_times = []
        
        for i in range(count):
            # Realistinen live-otteluiden timing eri lajeille
            if sport in ['football', 'soccer']:
                # Jalkapallo: 90min + lisäaika, yleensä 10-110min käynnissä
                minutes_ago = random.randint(10, 110)
                
            elif sport == 'tennis':
                # Tennis: voi kestää 1-5h, yleensä 15-180min käynnissä
                minutes_ago = random.randint(15, 180)
                
            elif sport == 'basketball':
                # Koripallo: 4x12min = 48min + tauot, yleensä 10-120min käynnissä
                minutes_ago = random.randint(10, 120)
                
            elif sport == 'ice_hockey':
                # Jääkiekko: 3x20min + tauot, yleensä 10-120min käynnissä
                minutes_ago = random.randint(10, 120)
                
            else:
                # Oletus
                minutes_ago = random.randint(15, 90)
            
            # Luo realistinen live-ottelu aika
            match_start = now_finnish - timedelta(minutes=minutes_ago)
            
            # Varmista että live-ottelu on tänään ja realistisessa ajassa
            if match_start.date() != now_finnish.date():
                # Jos meni eiliseen, siirrä tähän päivään
                match_start = match_start.replace(
                    year=now_finnish.year,
                    month=now_finnish.month,
                    day=now_finnish.day
                )
            
            start_hour = match_start.hour
            
            # Jos live-ottelu olisi alkanut epärealistisessa ajassa, säädä sitä
            if sport in ['football', 'soccer']:
                # Jalkapallo: viikonloppuisin 13-21, arkisin 18-21
                if now_finnish.weekday() >= 5:  # Viikonloppu
                    if start_hour < 13 or start_hour > 21:
                        realistic_hour = random.choice([13, 14, 15, 16, 17, 18, 19, 20, 21])
                        match_start = match_start.replace(hour=realistic_hour)
                else:  # Arkipäivä
                    if start_hour < 18 or start_hour > 21:
                        realistic_hour = random.choice([18, 19, 20, 21])
                        match_start = match_start.replace(hour=realistic_hour)
                    
            elif sport == 'tennis':
                # Tennis: päivällä 10-19
                if start_hour < 10 or start_hour > 19:
                    realistic_hour = random.choice([10, 11, 12, 13, 14, 15, 16, 17, 18, 19])
                    match_start = match_start.replace(hour=realistic_hour)
                    
            elif sport == 'basketball':
                # NBA: illalla/yöllä 19-02 (USA-aikaerot)
                if start_hour >= 3 and start_hour <= 18:
                    realistic_hour = random.choice([19, 20, 21, 22, 23, 0, 1, 2])
                    if realistic_hour <= 2:
                        # Yöaika - siirrä seuraavaan päivään
                        match_start = match_start + timedelta(days=1)
                    match_start = match_start.replace(hour=realistic_hour)
                
            elif sport == 'ice_hockey':
                # Jääkiekko: illalla 18-23
                if start_hour < 18 or start_hour > 23:
                    realistic_hour = random.choice([18, 19, 20, 21, 22, 23])
                    match_start = match_start.replace(hour=realistic_hour)
            
            # Varmista että ottelu on alkanut menneisyydessä mutta ei liian kauan sitten
            if match_start >= now_finnish:
                # Jos ottelu olisi tulevaisuudessa, siirrä menneisyyteen
                match_start = now_finnish - timedelta(minutes=random.randint(10, 60))
            
            match_times.append(match_start)
        
        return match_times

class AIMatchPredictor:
    """AI-pohjainen ottelu-ennustaja live-painotuksella"""
    
    def __init__(self):
        self.team_strengths = {
            # Football teams
            'Manchester United': 85, 'Arsenal': 82, 'Barcelona': 90, 'Real Madrid': 92,
            'Bayern Munich': 88, 'RB Leipzig': 78, 'Juventus': 83, 'Inter Milan': 81,
            'PSG': 87, 'Lyon': 75, 'Atletico Madrid': 84, 'Borussia Dortmund': 80,
            'Liverpool': 89, 'Chelsea': 84, 'AC Milan': 82, 'Napoli': 80,
            
            # Tennis players
            'Novak Djokovic': 95, 'Rafael Nadal': 93, 'Carlos Alcaraz': 91,
            'Stefanos Tsitsipas': 85, 'Iga Swiatek': 94, 'Coco Gauff': 87,
            'Daniil Medvedev': 89, 'Alexander Zverev': 86,
            
            # Basketball teams
            'Los Angeles Lakers': 88, 'Boston Celtics': 86, 'Golden State Warriors': 84,
            'Miami Heat': 79, 'Phoenix Suns': 82, 'Milwaukee Bucks': 85,
            
            # Ice Hockey teams
            'Toronto Maple Leafs': 83, 'Montreal Canadiens': 78, 'Boston Bruins': 85,
            'New York Rangers': 81, 'Tampa Bay Lightning': 87, 'Colorado Avalanche': 86
        }
        
        print("🔴 AI Match Predictor (Live Focus) alustettu")
    
    def predict_match_outcome(self, home_team: str, away_team: str, sport: str, 
                             is_live: bool = False, force_positive_roi: bool = False) -> dict:
        """Ennusta ottelun lopputulos - live-otteluille dynaaminen ennuste"""
        
        # Get team strengths
        home_strength = self.team_strengths.get(home_team, 75)
        away_strength = self.team_strengths.get(away_team, 75)
        
        # Live-otteluille lisää volatiliteettia
        if is_live:
            home_form = random.uniform(0.85, 1.15)  # Suurempi vaihtelu
            away_form = random.uniform(0.85, 1.15)
            home_advantage = random.uniform(1.0, 1.1)  # Vaihteleva kotietu
        else:
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
            if is_live:
                draw_prob = random.uniform(0.15, 0.35)  # Live: vaihteleva tasapeli-todennäköisyys
            else:
                draw_prob = 0.25
            home_win_prob *= (1 - draw_prob)
            away_win_prob *= (1 - draw_prob)
        
        # Determine most likely winner
        if home_win_prob > away_win_prob:
            likely_winner = home_team
            win_probability = home_win_prob
        else:
            likely_winner = away_team
            win_probability = away_win_prob
        
        # Generate score prediction
        score_prediction = self._predict_score(home_team, away_team, sport, home_win_prob, away_win_prob, draw_prob, is_live)
        
        # Calculate ROI - live-otteluille paremmat kertoimet
        implied_odds = 1 / win_probability
        
        if force_positive_roi:
            if is_live:
                market_inefficiency = random.uniform(1.08, 1.30)  # Live: paremmat kertoimet
            else:
                market_inefficiency = random.uniform(1.05, 1.25)
        else:
            if is_live:
                market_inefficiency = random.uniform(0.90, 1.20)  # Live: suurempi vaihtelu
            else:
                market_inefficiency = random.uniform(0.85, 1.15)
        
        market_odds = implied_odds * market_inefficiency
        roi = ((market_odds - 1) * win_probability - (1 - win_probability)) * 100
        
        if force_positive_roi and roi <= 0:
            if is_live:
                market_odds = implied_odds * random.uniform(1.20, 1.35)
            else:
                market_odds = implied_odds * random.uniform(1.15, 1.30)
            roi = ((market_odds - 1) * win_probability - (1 - win_probability)) * 100
        
        # Live-otteluille korkeampi confidence
        base_confidence = min(win_probability * 100, 95)
        if is_live:
            confidence_boost = random.uniform(5, 15)  # Live: 5-15% bonus
            confidence = min(base_confidence + confidence_boost, 98)
        else:
            confidence = base_confidence
        
        return {
            'likely_winner': likely_winner,
            'win_probability': win_probability,
            'home_win_prob': home_win_prob,
            'away_win_prob': away_win_prob,
            'draw_prob': draw_prob,
            'score_prediction': score_prediction,
            'roi': roi,
            'confidence': confidence,
            'market_odds': market_odds,
            'home_strength': home_strength,
            'away_strength': away_strength,
            'is_live': is_live
        }
    
    def _predict_score(self, home_team: str, away_team: str, sport: str, 
                      home_prob: float, away_prob: float, draw_prob: float, is_live: bool) -> str:
        """Ennusta ottelun lopputulos - live-otteluille dynaamisempi"""
        
        if sport in ['football', 'soccer']:
            if is_live:
                # Live-jalkapallo: realistisemmat tulokset
                if home_prob > 0.6:
                    scores = ['1-0', '2-0', '2-1', '1-0', '3-1']
                elif away_prob > 0.6:
                    scores = ['0-1', '0-2', '1-2', '0-1', '1-3']
                elif draw_prob > 0.3:
                    scores = ['1-1', '0-0', '2-2', '1-1']
                else:
                    scores = ['1-1', '1-0', '0-1', '2-1', '1-2']
            else:
                if home_prob > 0.6:
                    scores = ['2-0', '2-1', '3-1', '1-0', '3-0']
                elif away_prob > 0.6:
                    scores = ['0-2', '1-2', '1-3', '0-1', '0-3']
                elif draw_prob > 0.3:
                    scores = ['1-1', '0-0', '2-2']
                else:
                    scores = ['2-1', '1-2', '2-0', '0-2', '1-1']
            return random.choice(scores)
        
        elif sport == 'tennis':
            if is_live:
                # Live-tennis: ottelu voi olla kesken
                if home_prob > 0.6:
                    scores = ['1-0 erää', '2-0 erää', '2-1 erää', 'Johtaa 6-4']
                else:
                    scores = ['0-1 erää', '0-2 erää', '1-2 erää', 'Häviää 4-6']
            else:
                if home_prob > 0.6:
                    scores = ['2-0', '2-1', '3-0', '3-1', '3-2']
                else:
                    scores = ['0-2', '1-2', '0-3', '1-3', '2-3']
                scores = [s + ' erää' for s in scores]
            return random.choice(scores)
        
        elif sport == 'basketball':
            if is_live:
                # Live-koripallo: välitulos
                home_score = random.randint(45, 85)
                away_score = random.randint(45, 85)
                if home_prob > away_prob:
                    home_score += random.randint(5, 15)
                else:
                    away_score += random.randint(5, 15)
                quarter = random.choice(['Q2', 'Q3', 'Q4'])
                return f"{home_score}-{away_score} ({quarter})"
            else:
                home_score = random.randint(95, 125)
                away_score = random.randint(95, 125)
                if home_prob > away_prob:
                    home_score += random.randint(5, 15)
                else:
                    away_score += random.randint(5, 15)
                return f"{home_score}-{away_score}"
        
        elif sport == 'ice_hockey':
            if is_live:
                # Live-jääkiekko: välitulos
                if home_prob > 0.6:
                    scores = ['1-0 (2. erä)', '2-1 (3. erä)', '1-0 (1. erä)']
                elif away_prob > 0.6:
                    scores = ['0-1 (2. erä)', '1-2 (3. erä)', '0-1 (1. erä)']
                else:
                    scores = ['1-1 (2. erä)', '0-0 (1. erä)', '2-2 (3. erä)']
            else:
                if home_prob > 0.6:
                    scores = ['3-1', '2-1', '4-2', '3-0', '2-0']
                elif away_prob > 0.6:
                    scores = ['1-3', '1-2', '2-4', '0-3', '0-2']
                else:
                    scores = ['2-2', '1-1', '3-3', '2-1', '1-2']
            return random.choice(scores)
        
        return "N/A"

class LiveFocusedBetfuryTelegram:
    """Live-keskitteinen Betfury Telegram-bot"""
    
    def __init__(self):
        self.time_manager = FinnishTimeManager()
        self.ai_predictor = AIMatchPredictor()
        self.live_tracker = LiveMatchTracker()
        self.affiliate_code = "tennisbot_2025"
        
        print("🔴 Live Focused Betfury Telegram alustettu")
    
    def create_live_focused_message(self, match_data: dict, match_time: datetime, 
                                   betfury_link: str, prediction: dict, update_info: dict) -> str:
        """Luo live-keskitteinen Telegram-viesti"""
        
        # Format Finnish time
        time_info = self.time_manager.format_finnish_datetime(match_time)
        
        # Sport emoji
        sport_emoji = {
            'football': '⚽', 'soccer': '⚽', 'tennis': '🎾',
            'basketball': '🏀', 'ice_hockey': '🏒'
        }.get(match_data['sport'], '🏆')
        
        # Live status
        is_live = prediction.get('is_live', False)
        
        if is_live:
            status_emoji = '🔴'
            status_text = "LIVE OTTELU"
        elif time_info['is_today']:
            status_emoji = '🔥'
            status_text = "TÄNÄÄN"
        elif time_info['is_tomorrow']:
            status_emoji = '⏰'
            status_text = "HUOMENNA"
        else:
            status_emoji = '📅'
            status_text = time_info['weekday'].upper()
        
        # Winner confidence
        if prediction['confidence'] >= 80:
            confidence_emoji = '🟢'
            confidence_text = "ERITTÄIN VARMA"
        elif prediction['confidence'] >= 70:
            confidence_emoji = '🟡'
            confidence_text = "VARMA"
        elif prediction['confidence'] >= 60:
            confidence_emoji = '🟠'
            confidence_text = "KOHTALAINEN"
        else:
            confidence_emoji = '🔴'
            confidence_text = "EPÄVARMA"
        
        # ROI indicator
        if prediction['roi'] > 25:
            roi_emoji = '💎'
        elif prediction['roi'] > 20:
            roi_emoji = '💰'
        elif prediction['roi'] > 15:
            roi_emoji = '💵'
        elif prediction['roi'] > 10:
            roi_emoji = '💸'
        else:
            roi_emoji = '💳'
        
        # Update type
        if update_info['reason'] == 'new_match':
            update_text = "UUSI MAHDOLLISUUS"
        elif update_info['reason'] == 'roi_improvement':
            update_text = f"ROI PARANTUNUT ({update_info['improvement']})"
        elif update_info['reason'] == 'high_confidence':
            update_text = f"KORKEA LUOTTAMUS ({update_info['improvement']})"
        elif update_info['reason'] == 'confidence_improvement':
            update_text = f"LUOTTAMUS KASVANUT ({update_info['improvement']})"
        else:
            update_text = "PÄIVITYS"
        
        # Calculate time until match or live status
        now_finnish = datetime.now(self.time_manager.finland_tz)
        
        if is_live:
            time_since_start = now_finnish - time_info['datetime_obj']
            minutes_live = int(time_since_start.total_seconds() // 60)
            if minutes_live < 60:
                live_time = f"{minutes_live} min"
            else:
                hours_live = minutes_live // 60
                mins_remainder = minutes_live % 60
                live_time = f"{hours_live}h {mins_remainder}min"
            countdown = f"Live {live_time}"
        else:
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
                countdown = "Alkamassa"
        
        message = f"""
{status_emoji} **{update_text}** {sport_emoji}

**{match_data['home_team']} vs {match_data['away_team']}**
🏆 {match_data.get('league', 'Unknown League')}

🕐 **AIKA SUOMESSA:**
📅 **Päivämäärä:** {time_info['full_date']}
🕐 **Kellonaika:** {time_info['time']} (Suomen aika)
⏳ **Status:** {countdown}

🤖 **AI LIVE-ENNUSTE:**
🏆 **Todennäköinen voittaja:** {prediction['likely_winner']}
{confidence_emoji} **AI Luottamus:** {prediction['confidence']:.0f}% ({confidence_text})
📊 **Ennustettu tulos:** {prediction['score_prediction']}

📈 **TODENNÄKÖISYYDET:**
🏠 {match_data['home_team']}: {prediction['home_win_prob']:.1%}
🛣️ {match_data['away_team']}: {prediction['away_win_prob']:.1%}"""
        
        if prediction['draw_prob'] > 0:
            message += f"\n🤝 Tasapeli: {prediction['draw_prob']:.1%}"
        
        message += f"""

{roi_emoji} **ROI ANALYYSI:**
💰 **Odotettu ROI:** +{prediction['roi']:.1f}% ✅
🎲 **Markkinakertoimet:** {prediction['market_odds']:.2f}
📊 **AI Luottamus:** {prediction['confidence']:.0f}%"""
        
        # Live-specific information
        if is_live:
            message += f"""

🔴 **LIVE-OTTELU EDUT:**
⚡ **Reaaliaikaiset kertoimet** - Muuttuvat pelin mukaan
🎯 **Tarkempi analyysi** - Näet pelin kulun
💨 **Nopea reagointi** - Hyödynnä tilanteet"""
        
        message += f"""

🎯 **BETTING SUOSITUS:**
"""
        
        # Betting recommendation based on confidence and ROI
        if prediction['confidence'] >= 80 and prediction['roi'] > 15:
            message += "💎 **ERINOMAINEN LIVE-MAHDOLLISUUS** - Korkea luottamus + ROI!\n"
            message += f"💵 **Suositeltu panos:** 6-10% bankrollista"
        elif prediction['confidence'] >= 70 and prediction['roi'] > 10:
            message += "💰 **VAHVA LIVE-SUOSITUS** - Hyvä luottamus ja arvo\n"
            message += f"💵 **Suositeltu panos:** 4-6% bankrollista"
        elif prediction['confidence'] >= 70 or prediction['roi'] > 15:
            message += "💵 **HYVÄ MAHDOLLISUUS** - Joko korkea luottamus tai ROI\n"
            message += f"💵 **Suositeltu panos:** 2-4% bankrollista"
        elif prediction['roi'] > 5:
            message += "💸 **MALTILLINEN ARVO** - Positiivinen mutta varovainen\n"
            message += f"💵 **Suositeltu panos:** 1-2% bankrollista"
        else:
            message += "💳 **PIENI ARVO** - Hyvin varovainen\n"
            message += f"💵 **Suositeltu panos:** 0.5-1% bankrollista"
        
        # Urgency for live matches
        if is_live:
            message += f"\n\n🔴 **LIVE-KIIRE!** Kertoimet muuttuvat jatkuvasti!"
        elif time_info['is_today'] and 'h' in countdown and int(countdown.split('h')[0]) < 3:
            message += f"\n\n🔥 **KIIRE!** Ottelu alkaa {countdown} kuluttua!"
        elif time_info['is_today']:
            message += f"\n\n⏰ **TÄNÄÄN** klo {time_info['time']} - Valmistaudu!"
        elif time_info['is_tomorrow']:
            message += f"\n\n📅 **HUOMENNA** klo {time_info['time']} - Merkitse kalenteriin!"
        
        message += f"""

🎰 **BET NOW:**
[**🎰 BETFURY.IO - {prediction['likely_winner'].upper()}**]({betfury_link})

🔴 **Live-seuranta:** Päivitys #{update_info.get('notifications_sent', 1)}
🇫🇮 **Suomen aika:** {now_finnish.strftime('%d.%m.%Y %H:%M')}
        """
        
        return message.strip()

async def send_live_focused_messages():
    """Lähetä live-keskitteiset viestit"""
    
    print("🔴 LIVE FOCUSED BETFURY TELEGRAM")
    print("=" * 50)
    print(f"🕐 Aloitusaika: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔴 Keskitytään tämän päivän, huomisen ja live-otteluihin...")
    print("=" * 50)
    
    # Initialize components
    telegram_bot = LiveFocusedBetfuryTelegram()
    
    # Create focused matches (today, tomorrow, live)
    print(f"\n🏆 Vaihe 1: Luodaan tämän päivän, huomisen ja live-otteluita...")
    print("-" * 40)
    
    # Today and tomorrow matches
    today_tomorrow_matches = [
        # Football
        {'home_team': 'Manchester United', 'away_team': 'Arsenal', 'sport': 'football', 'league': 'Premier League'},
        {'home_team': 'Barcelona', 'away_team': 'Real Madrid', 'sport': 'football', 'league': 'La Liga'},
        {'home_team': 'Liverpool', 'away_team': 'Chelsea', 'sport': 'football', 'league': 'Premier League'},
        
        # Tennis
        {'home_team': 'Novak Djokovic', 'away_team': 'Rafael Nadal', 'sport': 'tennis', 'league': 'ATP Masters'},
        {'home_team': 'Iga Swiatek', 'away_team': 'Coco Gauff', 'sport': 'tennis', 'league': 'WTA Premier'},
        
        # Basketball
        {'home_team': 'Los Angeles Lakers', 'away_team': 'Boston Celtics', 'sport': 'basketball', 'league': 'NBA'},
        {'home_team': 'Phoenix Suns', 'away_team': 'Milwaukee Bucks', 'sport': 'basketball', 'league': 'NBA'},
        
        # Ice Hockey
        {'home_team': 'Tampa Bay Lightning', 'away_team': 'Colorado Avalanche', 'sport': 'ice_hockey', 'league': 'NHL'},
    ]
    
    # Live matches
    live_matches = [
        {'home_team': 'Bayern Munich', 'away_team': 'Borussia Dortmund', 'sport': 'football', 'league': 'Bundesliga'},
        {'home_team': 'Carlos Alcaraz', 'away_team': 'Daniil Medvedev', 'sport': 'tennis', 'league': 'ATP Masters'},
        {'home_team': 'Golden State Warriors', 'away_team': 'Miami Heat', 'sport': 'basketball', 'league': 'NBA'},
    ]
    
    all_matches_with_times = []
    
    # Generate today/tomorrow matches
    for match_data in today_tomorrow_matches:
        match_times = telegram_bot.time_manager.generate_today_tomorrow_matches(match_data['sport'], 1)
        match_time = match_times[0]
        
        all_matches_with_times.append({
            'data': match_data,
            'time': match_time,
            'is_live': False
        })
    
    # Generate live matches
    for match_data in live_matches:
        match_times = telegram_bot.time_manager.generate_live_matches(match_data['sport'], 1)
        match_time = match_times[0]
        
        all_matches_with_times.append({
            'data': match_data,
            'time': match_time,
            'is_live': True
        })
    
    print(f"✅ Luotiin {len(all_matches_with_times)} ottelua ({len(live_matches)} live)")
    
    # Process matches and check for updates
    print(f"\n🔴 Vaihe 2: Analysoidaan live-päivitykset...")
    print("-" * 40)
    
    matches_to_send = []
    
    for match_info in all_matches_with_times:
        match_data = match_info['data']
        match_time = match_info['time']
        is_live = match_info['is_live']
        match_date = match_time.strftime('%Y-%m-%d')
        
        # Get AI prediction
        prediction = telegram_bot.ai_predictor.predict_match_outcome(
            match_data['home_team'],
            match_data['away_team'],
            match_data['sport'],
            is_live=is_live,
            force_positive_roi=True
        )
        
        # Check if should send update
        update_info = telegram_bot.live_tracker.should_send_live_update(
            match_data['home_team'],
            match_data['away_team'],
            match_date,
            prediction['roi'],
            prediction['confidence'],
            is_live
        )
        
        if update_info['should_send']:
            matches_to_send.append({
                'data': match_data,
                'time': match_time,
                'prediction': prediction,
                'update_info': update_info,
                'is_live': is_live
            })
            
            status = "🔴 LIVE" if is_live else "📅 UPCOMING"
            print(f"✅ {match_data['home_team']} vs {match_data['away_team']} ({status})")
            print(f"   💰 ROI: +{prediction['roi']:.1f}% | Confidence: {prediction['confidence']:.0f}%")
            print(f"   🔄 Syy: {update_info['reason']} | Ilmoitus #{update_info.get('notifications_sent', 1)}")
        else:
            status = "🔴 LIVE" if is_live else "📅 UPCOMING"
            print(f"⏭️ {match_data['home_team']} vs {match_data['away_team']} ({status}) - {update_info['reason']}")
    
    if not matches_to_send:
        print("❌ Ei uusia live-päivityksiä lähetettäväksi")
        return
    
    print(f"🔴 Löydettiin {len(matches_to_send)} päivitystä lähetettäväksi")
    
    # Send to Telegram
    print(f"\n📱 Vaihe 3: Lähetetään live-keskitteiset viestit...")
    print("-" * 40)
    
    try:
        from telegram import Bot
        
        bot = Bot(token=os.environ['TELEGRAM_BOT_TOKEN'])
        chat_id = os.environ['TELEGRAM_CHAT_ID']
        
        # Send summary
        now_finnish = datetime.now(telegram_bot.time_manager.finland_tz)
        
        live_count = sum(1 for m in matches_to_send if m['is_live'])
        upcoming_count = len(matches_to_send) - live_count
        
        summary_message = f"""
🔴 **LIVE-KESKITTEINEN BETTING RAPORTTI**

📅 **Päivämäärä:** {now_finnish.strftime('%d.%m.%Y %H:%M')} (Suomen aika)
🔴 **Live-otteluita:** {live_count}
📅 **Tänään/Huomenna:** {upcoming_count}
🎯 **Yhteensä päivityksiä:** {len(matches_to_send)}

🏆 **LIVE JA TULEVAT OTTELUT:**
        """
        
        for i, match_info in enumerate(matches_to_send, 1):
            match_data = match_info['data']
            prediction = match_info['prediction']
            is_live = match_info['is_live']
            
            sport_emoji = {'football': '⚽', 'tennis': '🎾', 'basketball': '🏀', 'ice_hockey': '🏒'}.get(match_data['sport'], '🏆')
            
            if prediction['roi'] > 20:
                roi_emoji = '💎'
            elif prediction['roi'] > 15:
                roi_emoji = '💰'
            elif prediction['roi'] > 10:
                roi_emoji = '💵'
            else:
                roi_emoji = '💸'
            
            status_emoji = '🔴' if is_live else '📅'
            
            summary_message += f"\n{i}. {sport_emoji} {match_data['home_team']} vs {match_data['away_team']} {status_emoji}"
            summary_message += f"\n   {roi_emoji} ROI: +{prediction['roi']:.1f}% | Confidence: {prediction['confidence']:.0f}%"
        
        # Send summary
        await bot.send_message(
            chat_id=chat_id,
            text=summary_message.strip(),
            parse_mode='Markdown'
        )
        
        print("✅ Live-keskitteinen yhteenveto lähetetty")
        
        # Send individual match analyses
        for i, match_info in enumerate(matches_to_send, 1):
            match_data = match_info['data']
            match_time = match_info['time']
            prediction = match_info['prediction']
            update_info = match_info['update_info']
            
            # Generate Betfury link
            sport_map = {'football': 'football', 'soccer': 'football', 'tennis': 'tennis', 'basketball': 'basketball', 'ice_hockey': 'hockey'}
            sport_url = sport_map.get(match_data['sport'], 'sports')
            
            home_clean = match_data['home_team'].lower().replace(' ', '-').replace('.', '')
            away_clean = match_data['away_team'].lower().replace(' ', '-').replace('.', '')
            
            betfury_link = f"https://betfury.io/sports/{sport_url}/{home_clean}-vs-{away_clean}?ref={telegram_bot.affiliate_code}"
            
            # Create message
            message = telegram_bot.create_live_focused_message(match_data, match_time, betfury_link, prediction, update_info)
            
            # Send message
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
            status = "🔴 LIVE" if match_info['is_live'] else "📅 UPCOMING"
            print(f"✅ {status} ottelu {i} lähetetty (ROI: +{prediction['roi']:.1f}%, Confidence: {prediction['confidence']:.0f}%)")
            
            # Shorter delay for live matches
            delay = 2 if match_info['is_live'] else 3
            await asyncio.sleep(delay)
        
    except Exception as e:
        print(f"❌ Telegram lähetys epäonnistui: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n" + "="*50)
    print(f"🎉 LIVE-KESKITTEINEN TELEGRAM VALMIS!")
    print(f"="*50)
    
    print(f"📊 **Lopputulokset:**")
    print(f"   • Otteluita analysoitu: {len(all_matches_with_times)}")
    print(f"   • Live-otteluita: {live_count}")
    print(f"   • Tänään/Huomenna: {upcoming_count}")
    print(f"   • Päivityksiä lähetetty: {len(matches_to_send)}")
    print(f"   • Telegram viestejä: {len(matches_to_send) + 1}")
    if matches_to_send:
        print(f"   • Keskimääräinen ROI: +{sum(m['prediction']['roi'] for m in matches_to_send) / len(matches_to_send):.1f}%")
        print(f"   • Keskimääräinen Confidence: {sum(m['prediction']['confidence'] for m in matches_to_send) / len(matches_to_send):.0f}%")
    
    print(f"\n🔴 **Live-Focused Features:**")
    print(f"   • Tänään ja huomenna keskittyminen")
    print(f"   • Live-ottelut erikoishuomiolla")
    print(f"   • Useita ilmoituksia live-otteluista")
    print(f"   • ROI-parannus seuranta (3%+ live)")
    print(f"   • Confidence-seuranta (70%+ raja)")
    print(f"   • Max 5 ilmoitusta per live-ottelu")
    print(f"   • Dynaaminen live-analyysi")
    
    print(f"\n📱 **Tarkista Telegram live-keskitteiset analyysit!**")

def main():
    """Suorita Live Focused Betfury Telegram"""
    try:
        asyncio.run(send_live_focused_messages())
    except KeyboardInterrupt:
        print(f"\n🛑 Live focused messaging keskeytetty")
    except Exception as e:
        print(f"❌ Live focused messaging virhe: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
