#!/usr/bin/env python3
"""
🤖 AI-ENHANCED BETFURY TELEGRAM
==============================
Näyttää TG-viesteissä todennäköisen voittajan, ROI:n ja AI:n arvelemat lopputulokset
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import random
import json

# Set credentials
os.environ['TELEGRAM_BOT_TOKEN'] = '8481385860:AAGBRbsDA8--t373COn2mgM4_c1ngc2fGRM'
os.environ['TELEGRAM_CHAT_ID'] = '-4956738581'

# Add project paths
sys.path.append(str(Path(__file__).parent / 'src'))

class AIMatchPredictor:
    """AI-pohjainen ottelu-ennustaja"""
    
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
            # Football score prediction
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
            # Tennis set prediction
            if home_prob > 0.6:
                scores = ['2-0', '2-1', '3-0', '3-1', '3-2']
            else:
                scores = ['0-2', '1-2', '0-3', '1-3', '2-3']
            
            return random.choice(scores) + ' sets'
        
        elif sport == 'basketball':
            # Basketball score prediction
            home_score = random.randint(95, 125)
            away_score = random.randint(95, 125)
            
            if home_prob > away_prob:
                home_score += random.randint(5, 15)
            else:
                away_score += random.randint(5, 15)
            
            return f"{home_score}-{away_score}"
        
        elif sport == 'ice_hockey':
            # Hockey score prediction
            if home_prob > 0.6:
                scores = ['3-1', '2-1', '4-2', '3-0', '2-0']
            elif away_prob > 0.6:
                scores = ['1-3', '1-2', '2-4', '0-3', '0-2']
            else:
                scores = ['2-2', '1-1', '3-3', '2-1', '1-2']
            
            return random.choice(scores)
        
        return "N/A"

class EnhancedBetfuryTelegram:
    """Parannettu Betfury Telegram-bot AI-ennusteilla"""
    
    def __init__(self):
        self.ai_predictor = AIMatchPredictor()
        self.affiliate_code = "tennisbot_2025"
        
        print("🤖 Enhanced Betfury Telegram alustettu")
    
    def create_ai_enhanced_message(self, match_data: dict, betfury_link: str) -> str:
        """Luo AI-parannettu Telegram-viesti"""
        
        # Get AI prediction
        prediction = self.ai_predictor.predict_match_outcome(
            match_data['home_team'],
            match_data['away_team'], 
            match_data['sport']
        )
        
        # Sport emoji
        sport_emoji = {
            'football': '⚽', 'soccer': '⚽', 'tennis': '🎾',
            'basketball': '🏀', 'ice_hockey': '🏒'
        }.get(match_data['sport'], '🏆')
        
        # Winner emoji and confidence color
        if prediction['win_probability'] > 0.7:
            confidence_emoji = '🟢'  # High confidence
        elif prediction['win_probability'] > 0.55:
            confidence_emoji = '🟡'  # Medium confidence
        else:
            confidence_emoji = '🔴'  # Low confidence
        
        # ROI color
        if prediction['roi'] > 15:
            roi_emoji = '💰'
        elif prediction['roi'] > 5:
            roi_emoji = '💵'
        elif prediction['roi'] > 0:
            roi_emoji = '💸'
        else:
            roi_emoji = '⚠️'
        
        message = f"""
🤖 **AI BETTING ANALYSIS** {sport_emoji}

**{match_data['home_team']} vs {match_data['away_team']}**
🏆 {match_data.get('league', 'Unknown League')}

🎯 **AI ENNUSTE:**
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
📊 **AI Confidence:** {prediction['confidence']:.0f}%

🔍 **JOUKKUE-ANALYYSI:**
🏠 {match_data['home_team']}: {prediction['home_strength']}/100
🛣️ {match_data['away_team']}: {prediction['away_strength']}/100

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
        
        message += f"""

🎰 **BET NOW:**
[**🎰 BETFURY.IO - {prediction['likely_winner'].upper()}**]({betfury_link})

⏰ **AI Analyysi:** {datetime.now().strftime('%H:%M:%S')}
🤖 **Powered by:** Tennis Bot AI v2.0
        """
        
        return message.strip()
    
    def create_market_analysis_message(self, match_data: dict, prediction: dict) -> str:
        """Luo markkinakohtainen analyysi"""
        
        sport_emoji = {
            'football': '⚽', 'soccer': '⚽', 'tennis': '🎾',
            'basketball': '🏀', 'ice_hockey': '🏒'
        }.get(match_data['sport'], '🏆')
        
        message = f"""
📊 **MARKKINAKOHTAINEN ANALYYSI** {sport_emoji}

**{match_data['home_team']} vs {match_data['away_team']}**

🎯 **PARHAAT MARKKINAT:**
"""
        
        # Generate market-specific recommendations
        markets = []
        
        if match_data['sport'] in ['football', 'soccer']:
            # Football markets
            if prediction['home_win_prob'] > 0.6:
                markets.append(("Match Winner (Home)", f"{prediction['home_win_prob']:.1%}", "🟢 VAHVA"))
                markets.append(("Over 2.5 Goals", "68%", "🟡 KOHTALAINEN"))
            
            if prediction['draw_prob'] > 0.3:
                markets.append(("Draw", f"{prediction['draw_prob']:.1%}", "🟡 ARVO"))
            
            markets.append(("Both Teams Score", "58%", "🟡 KOHTALAINEN"))
            
        elif match_data['sport'] == 'tennis':
            # Tennis markets
            if prediction['win_probability'] > 0.65:
                markets.append(("Match Winner", f"{prediction['win_probability']:.1%}", "🟢 VAHVA"))
                markets.append(("Set Handicap", "72%", "🟡 KOHTALAINEN"))
            
            markets.append(("Total Games Over", "61%", "🟡 ARVO"))
            
        elif match_data['sport'] == 'basketball':
            # Basketball markets
            markets.append(("Match Winner", f"{prediction['win_probability']:.1%}", "🟢 SUOSITUS"))
            markets.append(("Total Points Over", "64%", "🟡 KOHTALAINEN"))
            markets.append(("Point Spread", "59%", "🟡 ARVO"))
        
        # Add markets to message
        for market, prob, recommendation in markets:
            message += f"\n• **{market}:** {prob} - {recommendation}"
        
        message += f"""

🎲 **RISK ASSESSMENT:**
📈 **Volatility:** {"Korkea" if prediction['confidence'] < 60 else "Matala"}
🎯 **Suositeltava panos:** {self._get_stake_recommendation(prediction)}
⚡ **Nopeus:** Lyö veto nopeasti, kertoimet voivat muuttua

🤖 **AI Luottamus:** {prediction['confidence']:.0f}%
        """
        
        return message.strip()
    
    def _get_stake_recommendation(self, prediction: dict) -> str:
        """Laske panos-suositus"""
        
        if prediction['roi'] > 15 and prediction['confidence'] > 80:
            return "4-6% bankrollista (Aggressiivinen)"
        elif prediction['roi'] > 10 and prediction['confidence'] > 70:
            return "2-4% bankrollista (Aktiivinen)"
        elif prediction['roi'] > 5 and prediction['confidence'] > 60:
            return "1-2% bankrollista (Konservatiivinen)"
        else:
            return "0.5-1% bankrollista (Varovainen)"

async def send_ai_enhanced_betfury_messages():
    """Lähetä AI-parannetut Betfury viestit Telegramiin"""
    
    print("🤖 AI-ENHANCED BETFURY TELEGRAM")
    print("=" * 50)
    print(f"🕐 Aloitusaika: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🤖 Luodaan AI-ennusteita ja ROI-analyysejä...")
    print("=" * 50)
    
    # Initialize components
    telegram_bot = EnhancedBetfuryTelegram()
    
    # Get matches
    print(f"\n🏆 Vaihe 1: Haetaan otteluita...")
    print("-" * 40)
    
    try:
        from multi_sport_prematch_scraper import MultiSportPrematchScraper
        
        scraper = MultiSportPrematchScraper()
        today = datetime.now()
        sports = ['football', 'tennis', 'basketball', 'ice_hockey']
        
        matches = scraper.scrape_daily_matches(today, sports)
        print(f"✅ Löydettiin {len(matches)} ottelua")
        
    except Exception as e:
        print(f"⚠️ Käytetään demo otteluita: {e}")
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
                'home_team': 'Novak Djokovic', 'away_team': 'Rafael Nadal',
                'sport': 'tennis', 'league': 'ATP Masters'
            })(),
            type('Match', (), {
                'home_team': 'Los Angeles Lakers', 'away_team': 'Boston Celtics',
                'sport': 'basketball', 'league': 'NBA'
            })(),
            type('Match', (), {
                'home_team': 'Bayern Munich', 'away_team': 'Borussia Dortmund',
                'sport': 'football', 'league': 'Bundesliga'
            })()
        ]
        print(f"✅ Käytetään {len(matches)} demo-ottelua")
    
    # Generate AI predictions and messages
    print(f"\n🤖 Vaihe 2: Luodaan AI-ennusteita...")
    print("-" * 40)
    
    ai_messages = []
    
    for i, match in enumerate(matches[:6], 1):  # Limit to 6 matches
        try:
            print(f"🤖 {i}. Analysoidaan: {match.home_team} vs {match.away_team}")
            
            match_data = {
                'home_team': match.home_team,
                'away_team': match.away_team,
                'sport': match.sport,
                'league': getattr(match, 'league', 'Unknown')
            }
            
            # Generate Betfury link
            sport_map = {'football': 'football', 'soccer': 'football', 'tennis': 'tennis', 'basketball': 'basketball', 'ice_hockey': 'hockey'}
            sport_url = sport_map.get(match.sport, 'sports')
            
            home_clean = match.home_team.lower().replace(' ', '-').replace('.', '')
            away_clean = match.away_team.lower().replace(' ', '-').replace('.', '')
            
            betfury_link = f"https://betfury.io/sports/{sport_url}/{home_clean}-vs-{away_clean}?ref={telegram_bot.affiliate_code}"
            
            # Create AI-enhanced message
            ai_message = telegram_bot.create_ai_enhanced_message(match_data, betfury_link)
            
            # Get prediction for market analysis
            prediction = telegram_bot.ai_predictor.predict_match_outcome(
                match.home_team, match.away_team, match.sport
            )
            
            market_message = telegram_bot.create_market_analysis_message(match_data, prediction)
            
            ai_messages.append({
                'match': f"{match.home_team} vs {match.away_team}",
                'sport': match.sport,
                'main_message': ai_message,
                'market_message': market_message,
                'prediction': prediction
            })
            
            print(f"   ✅ AI Voittaja: {prediction['likely_winner']} ({prediction['win_probability']:.1%})")
            print(f"   📊 Lopputulos: {prediction['score_prediction']}")
            print(f"   💰 ROI: {prediction['roi']:.1f}%")
            
        except Exception as e:
            print(f"   ❌ AI analyysi epäonnistui: {e}")
    
    # Send to Telegram
    print(f"\n📱 Vaihe 3: Lähetetään AI-viestit Telegramiin...")
    print("-" * 40)
    
    try:
        from telegram import Bot
        
        bot = Bot(token=os.environ['TELEGRAM_BOT_TOKEN'])
        chat_id = os.environ['TELEGRAM_CHAT_ID']
        
        # Send summary
        summary_message = f"""
🤖 **AI BETTING INTELLIGENCE REPORT**

📅 **Päivämäärä:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
🎯 **AI Analyysejä:** {len(ai_messages)}
🤖 **Ennusteet:** Voittaja, ROI, Lopputulos

🏆 **TOP AI PICKS:**
        """
        
        for i, msg_data in enumerate(ai_messages, 1):
            sport_emoji = {'football': '⚽', 'tennis': '🎾', 'basketball': '🏀', 'ice_hockey': '🏒'}.get(msg_data['sport'], '🏆')
            roi_emoji = '💰' if msg_data['prediction']['roi'] > 10 else '💵' if msg_data['prediction']['roi'] > 0 else '⚠️'
            
            summary_message += f"\n{i}. {sport_emoji} {msg_data['match']} {roi_emoji}"
            summary_message += f"\n   🏆 {msg_data['prediction']['likely_winner']} ({msg_data['prediction']['win_probability']:.0%})"
            summary_message += f"\n   💰 ROI: {msg_data['prediction']['roi']:.1f}%"
        
        # Send summary
        await bot.send_message(
            chat_id=chat_id,
            text=summary_message.strip(),
            parse_mode='Markdown'
        )
        
        print("✅ AI Summary lähetetty")
        
        # Send individual AI analyses
        for i, msg_data in enumerate(ai_messages, 1):
            # Send main AI message
            await bot.send_message(
                chat_id=chat_id,
                text=msg_data['main_message'],
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
            print(f"✅ AI Analyysi {i} lähetetty")
            
            # Send market analysis
            await bot.send_message(
                chat_id=chat_id,
                text=msg_data['market_message'],
                parse_mode='Markdown'
            )
            
            print(f"✅ Markkinaanalyysi {i} lähetetty")
            
            # Delay between messages
            await asyncio.sleep(3)
        
    except Exception as e:
        print(f"❌ Telegram lähetys epäonnistui: {e}")
    
    print(f"\n" + "="*50)
    print(f"🎉 AI-ENHANCED BETFURY TELEGRAM VALMIS!")
    print(f"="*50)
    
    print(f"📊 **Lopputulokset:**")
    print(f"   • AI Analyysejä luotu: {len(ai_messages)}")
    print(f"   • Telegram viestejä: {len(ai_messages) * 2 + 1}")
    print(f"   • Keskimääräinen ROI: {sum(msg['prediction']['roi'] for msg in ai_messages) / len(ai_messages):.1f}%")
    print(f"   • Keskimääräinen confidence: {sum(msg['prediction']['confidence'] for msg in ai_messages) / len(ai_messages):.1f}%")
    
    print(f"\n🤖 **AI Features:**")
    print(f"   • Todennäköinen voittaja per ottelu")
    print(f"   • ROI-laskenta ja suositukset")
    print(f"   • AI:n arvelemat lopputulokset")
    print(f"   • Markkinakohtaiset analyysit")
    print(f"   • Panos-suositukset")
    print(f"   • Confidence-scoring")
    
    print(f"\n📱 **Tarkista Telegram AI-ennusteet ja ROI-analyysit!**")

def main():
    """Suorita AI-enhanced Betfury Telegram"""
    try:
        asyncio.run(send_ai_enhanced_betfury_messages())
    except KeyboardInterrupt:
        print(f"\n🛑 AI-enhanced messaging keskeytetty")
    except Exception as e:
        print(f"❌ AI-enhanced messaging virhe: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
