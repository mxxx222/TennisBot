#!/usr/bin/env python3
"""
🔍 TERMINAALI VIHJESKANNERI
===========================
Skannaa kaikki API:t ja näyttää vihjeet terminaaliin.

Features:
- ✅ Tarkistaa kaikki API-yhteydet
- 🔍 Skannaa vihjeet useista lähteistä
- 📊 Näyttää vihjeet kauniisti terminaalissa
- 💰 ROI-analyysi ja suositukset
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass
# Colorama for colored terminal output (optional)
try:
    from colorama import init, Fore, Style, Back
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    # Fallback if colorama not available
    class Fore:
        CYAN = ''
        GREEN = ''
        YELLOW = ''
        RED = ''
        MAGENTA = ''
        BOLD = ''
    class Style:
        RESET_ALL = ''
    COLORAMA_AVAILABLE = False

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class Tip:
    """Vihje dataclass"""
    match_id: str
    home_team: str
    away_team: str
    sport: str
    league: str
    market: str
    selection: str
    odds: float
    roi_percentage: float
    confidence: float
    edge: float
    recommended_stake: float
    potential_profit: float
    match_time: datetime
    source: str
    betfury_link: Optional[str] = None

class TerminalTipsScanner:
    """Terminaali vihjeskanneri"""
    
    def __init__(self):
        """Alusta skanneri"""
        self.tips: List[Tip] = []
        self.api_status: Dict[str, bool] = {}
        self.scan_count = 0
        
        # API-avaimet - ladataan ympäristömuuttujista ja secrets-tiedostosta
        self.api_keys = self._load_api_keys()
        
        # Moduulit
        self.odds_api = None
        self.scraper = None
        self.analyzer = None
        self.strategy_engine = None
        
        logger.info("🔍 Terminal Tips Scanner initialized")
    
    def _load_api_keys(self) -> Dict[str, str]:
        """Lataa API-avaimet ympäristömuuttujista ja secrets-tiedostosta"""
        api_keys = {
            'ODDS_API_KEY': os.getenv('ODDS_API_KEY', ''),
            'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN', ''),
            'TELEGRAM_CHAT_ID': os.getenv('TELEGRAM_CHAT_ID', ''),
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
            'VENICE_API_KEY': os.getenv('VENICE_API_KEY', ''),
            'WEATHER_API_KEY': os.getenv('WEATHER_API_KEY', ''),
            'NOTION_API_KEY': os.getenv('NOTION_API_KEY', ''),
        }
        
        # Yritä ladata telegram_secrets.env tiedostosta
        secrets_file = Path(__file__).parent / 'telegram_secrets.env'
        if secrets_file.exists():
            try:
                with open(secrets_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            
                            # Päivitä vain jos ei jo ympäristömuuttujasta
                            if key in api_keys and not api_keys[key]:
                                api_keys[key] = value
                            elif key not in api_keys:
                                api_keys[key] = value
                
                logger.info(f"✅ Ladataan API-avaimet tiedostosta: {secrets_file}")
            except Exception as e:
                logger.warning(f"⚠️ Virhe lukiessa secrets-tiedostoa: {e}")
        
        # Näytä mitä avaimia löytyi (piilota arvot)
        found_keys = [k for k, v in api_keys.items() if v]
        logger.info(f"🔑 Löydetty {len(found_keys)} API-avainta: {', '.join(found_keys)}")
        
        return api_keys
    
    def check_apis(self) -> Dict[str, Dict[str, Any]]:
        """Tarkista kaikki API-yhteydet"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}🔍 TARKISTETAAN API-YHTEYDET")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
        
        api_status = {}
        
        # 1. Odds API
        print(f"{Fore.YELLOW}📊 Tarkistetaan Odds API...{Style.RESET_ALL}")
        try:
            try:
                from odds_api_integration import OddsAPIIntegration
            except ImportError:
                from src.odds_api_integration import OddsAPIIntegration
            self.odds_api = OddsAPIIntegration(self.api_keys['ODDS_API_KEY'])
            api_status['odds_api'] = {
                'status': True,
                'name': 'The Odds API',
                'key_present': bool(self.api_keys['ODDS_API_KEY']),
                'message': '✅ Odds API saatavilla'
            }
            print(f"{Fore.GREEN}✅ Odds API saatavilla{Style.RESET_ALL}")
        except Exception as e:
            api_status['odds_api'] = {
                'status': False,
                'name': 'The Odds API',
                'key_present': bool(self.api_keys['ODDS_API_KEY']),
                'message': f'❌ Odds API virhe: {e}'
            }
            print(f"{Fore.RED}❌ Odds API virhe: {e}{Style.RESET_ALL}")
        
        # 2. Multi-Sport Scraper
        print(f"{Fore.YELLOW}🌐 Tarkistetaan Multi-Sport Scraper...{Style.RESET_ALL}")
        try:
            # Try different import paths
            try:
                from multi_sport_prematch_scraper import MultiSportPrematchScraper
            except ImportError:
                try:
                    from src.multi_sport_prematch_scraper import MultiSportPrematchScraper
                except ImportError:
                    from src.scrapers.multi_sport_prematch_scraper import MultiSportPrematchScraper
            self.scraper = MultiSportPrematchScraper()
            api_status['scraper'] = {
                'status': True,
                'name': 'Multi-Sport Scraper',
                'message': '✅ Scraper saatavilla'
            }
            print(f"{Fore.GREEN}✅ Scraper saatavilla{Style.RESET_ALL}")
        except Exception as e:
            api_status['scraper'] = {
                'status': False,
                'name': 'Multi-Sport Scraper',
                'message': f'❌ Scraper virhe: {e}'
            }
            print(f"{Fore.RED}❌ Scraper virhe: {e}{Style.RESET_ALL}")
        
        # 3. Prematch Analyzer
        print(f"{Fore.YELLOW}🧠 Tarkistetaan Prematch Analyzer...{Style.RESET_ALL}")
        try:
            try:
                from prematch_analyzer import PrematchAnalyzer
            except ImportError:
                from src.prematch_analyzer import PrematchAnalyzer
            self.analyzer = PrematchAnalyzer()
            api_status['analyzer'] = {
                'status': True,
                'name': 'Prematch Analyzer',
                'message': '✅ Analyzer saatavilla'
            }
            print(f"{Fore.GREEN}✅ Analyzer saatavilla{Style.RESET_ALL}")
        except Exception as e:
            api_status['analyzer'] = {
                'status': False,
                'name': 'Prematch Analyzer',
                'message': f'❌ Analyzer virhe: {e}'
            }
            print(f"{Fore.RED}❌ Analyzer virhe: {e}{Style.RESET_ALL}")
        
        # 4. Strategy Engine
        print(f"{Fore.YELLOW}🎯 Tarkistetaan Strategy Engine...{Style.RESET_ALL}")
        try:
            try:
                from betting_strategy_engine import BettingStrategyEngine
            except ImportError:
                from src.betting_strategy_engine import BettingStrategyEngine
            self.strategy_engine = BettingStrategyEngine(bankroll=10000, risk_tolerance='moderate')
            api_status['strategy'] = {
                'status': True,
                'name': 'Strategy Engine',
                'message': '✅ Strategy Engine saatavilla'
            }
            print(f"{Fore.GREEN}✅ Strategy Engine saatavilla{Style.RESET_ALL}")
        except Exception as e:
            api_status['strategy'] = {
                'status': False,
                'name': 'Strategy Engine',
                'message': f'❌ Strategy Engine virhe: {e}'
            }
            print(f"{Fore.RED}❌ Strategy Engine virhe: {e}{Style.RESET_ALL}")
        
        # 5. Telegram Bot
        print(f"{Fore.YELLOW}📱 Tarkistetaan Telegram Bot...{Style.RESET_ALL}")
        if self.api_keys['TELEGRAM_BOT_TOKEN']:
            api_status['telegram'] = {
                'status': True,
                'name': 'Telegram Bot',
                'key_present': True,
                'message': '✅ Telegram token saatavilla'
            }
            print(f"{Fore.GREEN}✅ Telegram token saatavilla{Style.RESET_ALL}")
        else:
            api_status['telegram'] = {
                'status': False,
                'name': 'Telegram Bot',
                'key_present': False,
                'message': '⚠️ Telegram token puuttuu'
            }
            print(f"{Fore.YELLOW}⚠️ Telegram token puuttuu{Style.RESET_ALL}")
        
        # 6. OpenAI
        print(f"{Fore.YELLOW}🤖 Tarkistetaan OpenAI...{Style.RESET_ALL}")
        if self.api_keys['OPENAI_API_KEY']:
            api_status['openai'] = {
                'status': True,
                'name': 'OpenAI',
                'key_present': True,
                'message': '✅ OpenAI key saatavilla'
            }
            print(f"{Fore.GREEN}✅ OpenAI key saatavilla{Style.RESET_ALL}")
        else:
            api_status['openai'] = {
                'status': False,
                'name': 'OpenAI',
                'key_present': False,
                'message': '⚠️ OpenAI key puuttuu'
            }
            print(f"{Fore.YELLOW}⚠️ OpenAI key puuttuu{Style.RESET_ALL}")
        
        # 7. Venice AI
        print(f"{Fore.YELLOW}🌊 Tarkistetaan Venice AI...{Style.RESET_ALL}")
        if self.api_keys['VENICE_API_KEY']:
            api_status['venice'] = {
                'status': True,
                'name': 'Venice AI',
                'key_present': True,
                'message': '✅ Venice AI key saatavilla'
            }
            print(f"{Fore.GREEN}✅ Venice AI key saatavilla{Style.RESET_ALL}")
        else:
            api_status['venice'] = {
                'status': False,
                'name': 'Venice AI',
                'key_present': False,
                'message': '⚠️ Venice AI key puuttuu'
            }
            print(f"{Fore.YELLOW}⚠️ Venice AI key puuttuu{Style.RESET_ALL}")
        
        self.api_status = api_status
        
        # Yhteenveto
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}📊 API-YHTEYSYHTEENVETO")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
        
        active_count = sum(1 for api in api_status.values() if api.get('status', False))
        total_count = len(api_status)
        
        for api_name, api_info in api_status.items():
            status_icon = "✅" if api_info.get('status', False) else "❌"
            status_color = Fore.GREEN if api_info.get('status', False) else Fore.RED
            print(f"{status_color}{status_icon} {api_info['name']}: {api_info['message']}{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}Yhteensä: {active_count}/{total_count} API:a aktiivisia{Style.RESET_ALL}\n")
        
        return api_status
    
    async def scan_all_matches(self) -> List[Dict[str, Any]]:
        """Hakee KAIKKI päivän ottelut ilman vetovihjeitä"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}📅 HAKETAAN KAIKKI PÄIVÄN OTTELUT...")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
        
        all_matches = []
        
        # 1. Hae kaikki ottelut Odds API:sta
        if self.odds_api:
            print(f"{Fore.YELLOW}📊 Haetaan kaikki ottelut Odds API:sta...{Style.RESET_ALL}")
            try:
                odds_matches = await self._get_all_odds_matches()
                all_matches.extend(odds_matches)
                print(f"{Fore.GREEN}✅ Löydettiin {len(odds_matches)} ottelua Odds API:sta{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Odds API virhe: {e}{Style.RESET_ALL}")
        
        # 2. Hae kaikki ottelut Scraperista
        if self.scraper:
            print(f"{Fore.YELLOW}🌐 Haetaan kaikki ottelut Scraperista...{Style.RESET_ALL}")
            try:
                scraper_matches = await self._get_all_scraper_matches()
                all_matches.extend(scraper_matches)
                print(f"{Fore.GREEN}✅ Löydettiin {len(scraper_matches)} ottelua Scraperista{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Scraper virhe: {e}{Style.RESET_ALL}")
        
        # Poista duplikaatit
        unique_matches = self._deduplicate_matches(all_matches)
        
        # Järjestä prioriteettien mukaan
        unique_matches = self._sort_by_priority(unique_matches)
        
        print(f"{Fore.GREEN}✅ Yhteensä {len(unique_matches)} uniikkia ottelua löydetty{Style.RESET_ALL}\n")
        
        return unique_matches
    
    async def scan_tips(self) -> List[Tip]:
        """Skannaa vihjeet kaikista lähteistä"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}🔍 SKANNATAAN VETOVIHJEITÄ...")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
        
        all_tips = []
        
        # 1. Odds API vihjeet
        if self.odds_api:
            print(f"{Fore.YELLOW}📊 Skannataan Odds API...{Style.RESET_ALL}")
            try:
                odds_tips = await self._scan_odds_api()
                all_tips.extend(odds_tips)
                print(f"{Fore.GREEN}✅ Löydettiin {len(odds_tips)} vihjettä Odds API:sta{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Odds API skannausvirhe: {e}{Style.RESET_ALL}")
        
        # 2. Multi-Sport Scraper vihjeet
        if self.scraper:
            print(f"{Fore.YELLOW}🌐 Skannataan Multi-Sport Scraper...{Style.RESET_ALL}")
            try:
                scraper_tips = await self._scan_multi_sport()
                all_tips.extend(scraper_tips)
                print(f"{Fore.GREEN}✅ Löydettiin {len(scraper_tips)} vihjettä Scraperista{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Scraper skannausvirhe: {e}{Style.RESET_ALL}")
        
        # 3. Analysoi ja suodata vihjeet
        if self.analyzer and self.strategy_engine:
            print(f"{Fore.YELLOW}🧠 Analysoidaan vihjeet...{Style.RESET_ALL}")
            try:
                analyzed_tips = self._analyze_tips(all_tips)
                all_tips = analyzed_tips
                print(f"{Fore.GREEN}✅ Analysoitu {len(analyzed_tips)} vihjettä{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Analyysivirhe: {e}{Style.RESET_ALL}")
        
        # Järjestä ROI:n mukaan
        all_tips.sort(key=lambda x: x.roi_percentage, reverse=True)
        
        self.tips = all_tips
        self.scan_count += 1
        
        return all_tips
    
    async def _scan_odds_api(self) -> List[Tip]:
        """Skannaa Odds API:sta - vain tämän päivän ottelut, PRIORITEETIT: 2 futisliigaa + ITF tennis"""
        tips = []
        
        try:
            # PRIORITEETIT: 2 kakkosdivisioonaa futiksessa + ITF tennis
            # Kakkosdivisioonat: Championship (Englanti), 2. Bundesliga (Saksa), Serie B (Italia)
            priority_sports = [
                'soccer_england_championship',  # Englannin Championship (kakkosdivisioona)
                'soccer_germany_bundesliga2',  # Saksan 2. Bundesliga (kakkosdivisioona)
                'soccer_italy_serie_b',        # Italian Serie B (kakkosdivisioona)
                'soccer_england_league1',      # Englannin League One (varmistus)
                'soccer_england_league2',      # Englannin League Two (varmistus)
                'tennis_atp'                   # Tennis (sisältää ITF)
            ]
            
            # Hae myös muita urheilulajeja
            other_sports = ['basketball_nba', 'icehockey_nhl']
            
            # Hae live odds - PRIORITEETIT ENSIN
            logger.info(f"🎯 Skannataan PRIORITEETIT: 2 kakkosdivisioonaa (Championship, 2. Bundesliga, Serie B) + ITF Tennis")
            odds_data = await self.odds_api.get_live_odds(
                sports=priority_sports + other_sports,
                markets=['h2h']
            )
            
            now = datetime.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            # Filtteröi vain tämän päivän ottelut
            today_matches = []
            for odds in odds_data:
                # Tarkista että ottelu on tänään
                match_time = odds.commence_time
                if isinstance(match_time, str):
                    try:
                        match_time = datetime.fromisoformat(match_time.replace('Z', '+00:00'))
                    except:
                        continue
                
                # Muunna UTC -> local time jos tarpeen
                if match_time.tzinfo is None:
                    match_time = match_time.replace(tzinfo=None)
                
                # Tarkista että ottelu on tänään (0-24h tulevaisuudessa)
                time_diff = (match_time - now).total_seconds()
                
                # Hyväksy ottelut jotka alkavat tänään tai seuraavana 24h
                if today_start <= match_time.replace(tzinfo=None) <= today_end or (0 <= time_diff <= 86400):
                    today_matches.append(odds)
            
            logger.info(f"📅 Löydettiin {len(today_matches)} tämän päivän ottelua Odds API:sta (yhteensä {len(odds_data)} ottelua)")
            
            if not today_matches:
                logger.info(f"ℹ️ Ei tämän päivän otteluita Odds API:sta. Tarkista että ottelut ovat tänään ({now.strftime('%Y-%m-%d')})")
            
            # Järjestä prioriteettien mukaan
            priority_matches = []
            other_matches = []
            
            for odds in today_matches:
                # Tarkista onko prioriteetti-liiga
                is_priority = False
                league_name = odds.sport_title
                
                # Tarkista kakkosdivisioonat futiksessa
                second_division_keywords = [
                    'Championship',      # Englannin Championship
                    '2. Bundesliga',     # Saksan 2. Bundesliga
                    'Bundesliga 2',      # Vaihtoehtoinen muoto
                    'Serie B',           # Italian Serie B
                    'League One',         # Englannin League One
                    'League Two'          # Englannin League Two
                ]
                
                for keyword in second_division_keywords:
                    if keyword in league_name:
                        is_priority = True
                        break
                
                # Tarkista ITF tennis
                if 'ITF' in league_name or 'Challenger' in league_name or 'itf' in league_name.lower():
                    is_priority = True
                
                if is_priority:
                    priority_matches.append(odds)
                else:
                    other_matches.append(odds)
            
            logger.info(f"⭐ Prioriteetti-ottelut: {len(priority_matches)} (Kakkosdivisioonat + ITF Tennis)")
            logger.info(f"📊 Muut ottelut: {len(other_matches)}")
            
            # Käsittele ensin prioriteetti-ottelut
            for odds in priority_matches + other_matches:
                # Analysoi ROI
                roi_analysis = self._quick_roi_analysis(odds)
                
                # Prioriteetti-otteluille alhaisempi ROI-kynnys
                min_roi = 5.0 if odds in priority_matches else 8.0
                
                if roi_analysis and roi_analysis['roi_percentage'] >= min_roi:
                    tip = Tip(
                        match_id=f"odds_{odds.sport_key}_{odds.home_team}_{odds.away_team}",
                        home_team=odds.home_team,
                        away_team=odds.away_team,
                        sport=self._normalize_sport(odds.sport_key),
                        league=odds.sport_title,
                        market='Match Winner',
                        selection=roi_analysis.get('best_selection', 'N/A'),
                        odds=roi_analysis.get('best_odds', 0.0),
                        roi_percentage=roi_analysis['roi_percentage'],
                        confidence=roi_analysis.get('confidence_score', 0.0),
                        edge=roi_analysis.get('edge', 0.0),
                        recommended_stake=roi_analysis.get('recommended_stake', 1.0),
                        potential_profit=roi_analysis.get('potential_profit', 0.0),
                        match_time=odds.commence_time,
                        source='Odds API'
                    )
                    tips.append(tip)
        
        except Exception as e:
            logger.error(f"Odds API skannausvirhe: {e}")
        
        return tips
    
    async def _scan_multi_sport(self) -> List[Tip]:
        """Skannaa Multi-Sport Scraperista - vain tämän päivän ottelut"""
        tips = []
        
        try:
            now = datetime.now()
            matches = self.scraper.scrape_daily_matches(
                now,
                ['football', 'tennis', 'basketball', 'ice_hockey']
            )
            
            # Filtteröi vain tämän päivän ottelut
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            today_matches = []
            for match in matches:
                match_time = match.match_time
                
                # Tarkista että ottelu on tänään
                if isinstance(match_time, str):
                    try:
                        match_time = datetime.fromisoformat(match_time.replace('Z', '+00:00'))
                    except:
                        continue
                
                # Muunna UTC -> local time jos tarpeen
                if hasattr(match_time, 'tzinfo') and match_time.tzinfo is not None:
                    match_time = match_time.replace(tzinfo=None)
                
                # Tarkista että ottelu on tänään tai seuraavana 24h
                time_diff = (match_time - now).total_seconds()
                
                if today_start <= match_time <= today_end or (0 <= time_diff <= 86400):
                    today_matches.append(match)
            
            logger.info(f"📅 Löydettiin {len(today_matches)} tämän päivän ottelua Scraperista (yhteensä {len(matches)} ottelua)")
            
            if not today_matches:
                logger.info(f"ℹ️ Ei tämän päivän otteluita Scraperista. Tarkista että ottelut ovat tänään ({now.strftime('%Y-%m-%d')})")
            
            for match in today_matches:
                # Analysoi match
                roi_analysis = self._quick_match_analysis(match)
                
                if roi_analysis and roi_analysis['roi_percentage'] >= 5.0:
                    tip = Tip(
                        match_id=match.match_id,
                        home_team=match.home_team,
                        away_team=match.away_team,
                        sport=match.sport,
                        league=match.league,
                        market=roi_analysis.get('market', 'Match Winner'),
                        selection=roi_analysis.get('selection', 'N/A'),
                        odds=roi_analysis.get('odds', 0.0),
                        roi_percentage=roi_analysis['roi_percentage'],
                        confidence=roi_analysis.get('confidence', 0.0),
                        edge=roi_analysis.get('edge', 0.0),
                        recommended_stake=roi_analysis.get('recommended_stake', 1.0),
                        potential_profit=roi_analysis.get('potential_profit', 0.0),
                        match_time=match.match_time,
                        source='Multi-Sport Scraper'
                    )
                    tips.append(tip)
        
        except Exception as e:
            logger.error(f"Scraper skannausvirhe: {e}")
        
        return tips
    
    async def _get_all_odds_matches(self) -> List[Dict[str, Any]]:
        """Hakee KAIKKI ottelut Odds API:sta ilman ROI-analyysiä"""
        matches = []
        
        try:
            # PRIORITEETIT: Kakkosdivisioonat + ITF tennis
            priority_sports = [
                'soccer_england_championship',
                'soccer_germany_bundesliga2',
                'soccer_italy_serie_b',
                'soccer_england_league1',
                'soccer_england_league2',
                'tennis_atp'
            ]
            
            other_sports = ['soccer_epl', 'soccer_spain_la_liga', 'soccer_germany_bundesliga', 
                          'soccer_italy_serie_a', 'basketball_nba', 'icehockey_nhl']
            
            odds_data = await self.odds_api.get_live_odds(
                sports=priority_sports + other_sports,
                markets=['h2h']
            )
            
            now = datetime.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            for odds in odds_data:
                match_time = odds.commence_time
                if isinstance(match_time, str):
                    try:
                        match_time = datetime.fromisoformat(match_time.replace('Z', '+00:00'))
                    except:
                        continue
                
                if match_time.tzinfo is not None:
                    match_time = match_time.replace(tzinfo=None)
                
                time_diff = (match_time - now).total_seconds()
                
                # Hyväksy tämän päivän ottelut
                if today_start <= match_time <= today_end or (0 <= time_diff <= 86400):
                    # Tarkista onko prioriteetti
                    is_priority = False
                    league_name = odds.sport_title
                    
                    second_division_keywords = ['Championship', '2. Bundesliga', 'Bundesliga 2', 
                                               'Serie B', 'League One', 'League Two']
                    for keyword in second_division_keywords:
                        if keyword in league_name:
                            is_priority = True
                            break
                    
                    if 'ITF' in league_name or 'Challenger' in league_name or 'itf' in league_name.lower():
                        is_priority = True
                    
                    match_info = {
                        'match_id': f"odds_{odds.sport_key}_{odds.home_team}_{odds.away_team}",
                        'home_team': odds.home_team,
                        'away_team': odds.away_team,
                        'sport': self._normalize_sport(odds.sport_key),
                        'league': odds.sport_title,
                        'match_time': odds.commence_time,
                        'is_priority': is_priority,
                        'source': 'Odds API',
                        'sport_key': odds.sport_key
                    }
                    
                    # Lisää kertoimet jos saatavilla
                    if odds.best_odds and 'h2h' in odds.best_odds:
                        match_info['odds'] = odds.best_odds['h2h']
                    
                    matches.append(match_info)
        
        except Exception as e:
            logger.error(f"Virhe haettaessa otteluita Odds API:sta: {e}")
        
        return matches
    
    async def _get_all_scraper_matches(self) -> List[Dict[str, Any]]:
        """Hakee KAIKKI ottelut Scraperista ilman ROI-analyysiä"""
        matches = []
        
        try:
            now = datetime.now()
            scraped_matches = self.scraper.scrape_daily_matches(
                now,
                ['football', 'tennis', 'basketball', 'ice_hockey']
            )
            
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            for match in scraped_matches:
                match_time = match.match_time
                if isinstance(match_time, str):
                    try:
                        match_time = datetime.fromisoformat(match_time.replace('Z', '+00:00'))
                    except:
                        continue
                
                if hasattr(match_time, 'tzinfo') and match_time.tzinfo is not None:
                    match_time = match_time.replace(tzinfo=None)
                
                time_diff = (match_time - now).total_seconds()
                
                if today_start <= match_time <= today_end or (0 <= time_diff <= 86400):
                    # Tarkista onko prioriteetti
                    is_priority = False
                    league_name = match.league
                    
                    second_division_keywords = ['Championship', '2. Bundesliga', 'Bundesliga 2', 
                                               'Serie B', 'League One', 'League Two']
                    for keyword in second_division_keywords:
                        if keyword in league_name:
                            is_priority = True
                            break
                    
                    if 'ITF' in league_name or 'Challenger' in league_name or 'itf' in league_name.lower():
                        is_priority = True
                    
                    match_info = {
                        'match_id': match.match_id,
                        'home_team': match.home_team,
                        'away_team': match.away_team,
                        'sport': match.sport,
                        'league': match.league,
                        'match_time': match.match_time,
                        'is_priority': is_priority,
                        'source': 'Multi-Sport Scraper',
                        'venue': getattr(match, 'venue', 'N/A')
                    }
                    
                    # Lisää kertoimet jos saatavilla
                    if match.odds:
                        match_info['odds'] = match.odds
                    
                    matches.append(match_info)
        
        except Exception as e:
            logger.error(f"Virhe haettaessa otteluita Scraperista: {e}")
        
        return matches
    
    def _deduplicate_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Poistaa duplikaatti-ottelut"""
        seen = set()
        unique = []
        
        for match in matches:
            # Luo uniikki avain
            key = f"{match['home_team']}_{match['away_team']}_{match.get('match_time', '')}"
            
            if key not in seen:
                seen.add(key)
                unique.append(match)
        
        return unique
    
    def _sort_by_priority(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Järjestää ottelut prioriteettien mukaan"""
        priority_matches = [m for m in matches if m.get('is_priority', False)]
        other_matches = [m for m in matches if not m.get('is_priority', False)]
        
        def get_sort_time(match):
            """Hae järjestysaika ottelusta"""
            match_time = match.get('match_time', datetime.now())
            if isinstance(match_time, str):
                try:
                    match_time = datetime.fromisoformat(match_time.replace('Z', '+00:00'))
                except:
                    return datetime.now()
            
            # Muunna timezone-aware -> naive jos tarpeen
            if hasattr(match_time, 'tzinfo') and match_time.tzinfo is not None:
                match_time = match_time.replace(tzinfo=None)
            
            return match_time
        
        # Järjestä prioriteetti-ottelut ensin
        priority_matches.sort(key=get_sort_time)
        other_matches.sort(key=get_sort_time)
        
        return priority_matches + other_matches
    
    def display_all_matches(self, matches: List[Dict[str, Any]]):
        """Näyttää kaikki ottelut ilman vetovihjeitä"""
        if not matches:
            print(f"\n{Fore.YELLOW}⚠️ Ei otteluita löytynyt{Style.RESET_ALL}\n")
            return
        
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}📅 KAIKKI PÄIVÄN OTTELUT ({len(matches)} kpl)")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
        
        priority_matches = [m for m in matches if m.get('is_priority', False)]
        other_matches = [m for m in matches if not m.get('is_priority', False)]
        
        if priority_matches:
            print(f"{Fore.MAGENTA}⭐ PRIORITEETTI-OTTELUT ({len(priority_matches)} kpl){Style.RESET_ALL}\n")
            for i, match in enumerate(priority_matches, 1):
                self._display_single_match(match, i, is_priority=True)
        
        if other_matches:
            print(f"\n{Fore.CYAN}📊 MUUT OTTELUT ({len(other_matches)} kpl){Style.RESET_ALL}\n")
            for i, match in enumerate(other_matches, 1):
                self._display_single_match(match, i, is_priority=False)
        
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ Yhteensä {len(matches)} ottelua ({len(priority_matches)} prioriteetti, {len(other_matches)} muuta){Style.RESET_ALL}\n")
    
    def _display_single_match(self, match: Dict[str, Any], index: int, is_priority: bool = False):
        """Näyttää yhden ottelun tiedot"""
        sport_emoji = {
            'Football': '⚽',
            'Football (Championship)': '⚽',
            'Football (2. Bundesliga)': '⚽',
            'Football (Serie B)': '⚽',
            'Tennis': '🎾',
            'Tennis (ITF)': '🎾',
            'Basketball': '🏀',
            'Ice Hockey': '🏒'
        }.get(match.get('sport', ''), '🏆')
        
        priority_icon = "⭐" if is_priority else "  "
        
        match_time = match.get('match_time', '')
        if isinstance(match_time, str):
            try:
                match_time = datetime.fromisoformat(match_time.replace('Z', '+00:00'))
            except:
                match_time_str = str(match_time)
        else:
            match_time_str = match_time.strftime('%Y-%m-%d %H:%M') if hasattr(match_time, 'strftime') else str(match_time)
        
        print(f"{priority_icon} {index}. {sport_emoji} {Fore.BOLD}{match['home_team']} vs {match['away_team']}{Style.RESET_ALL}")
        print(f"      📅 {match.get('league', 'N/A')}")
        print(f"      ⏰ {match_time_str}")
        print(f"      📡 {match.get('source', 'N/A')}")
        
        # Näytä kertoimet jos saatavilla
        if 'odds' in match and match['odds']:
            if isinstance(match['odds'], dict) and 'h2h' in match['odds']:
                h2h = match['odds']['h2h']
                if isinstance(h2h, dict) and len(h2h) > 0:
                    odds_str = ", ".join([f"{k}: {v:.2f}" for k, v in list(h2h.items())[:3]])
                    print(f"      💰 {odds_str}")
        
        print()
    
    def _quick_roi_analysis(self, odds_data) -> Optional[Dict[str, Any]]:
        """Nopea ROI-analyysi odds-datasta"""
        try:
            if not odds_data.best_odds or 'h2h' not in odds_data.best_odds:
                return None
            
            h2h_odds = odds_data.best_odds['h2h']
            if len(h2h_odds) < 2:
                return None
            
            # Etsi parhaat kertoimet
            best_selection = max(h2h_odds.items(), key=lambda x: x[1])
            selection_name = best_selection[0]
            best_odds = best_selection[1]
            
            # Laske todennäköisyys
            implied_prob = 1 / best_odds
            
            # Oletetaan että meidän malli antaa hieman paremman todennäköisyyden
            true_prob = implied_prob * 1.05  # 5% edge
            
            if true_prob > 1.0:
                true_prob = 0.95
            
            # Laske ROI
            expected_value = (true_prob * best_odds) - 1
            roi_percentage = expected_value * 100
            
            if roi_percentage < 5.0:
                return None
            
            # Laske muut arvot
            stake = 100  # $100 oletus
            potential_profit = stake * (best_odds - 1) * true_prob
            edge = (true_prob - implied_prob) * 100
            confidence = min(0.95, true_prob * 0.9)
            
            return {
                'best_selection': selection_name,
                'best_odds': best_odds,
                'roi_percentage': roi_percentage,
                'confidence_score': confidence,
                'edge': edge,
                'recommended_stake': min(5.0, max(1.0, roi_percentage / 2)),
                'potential_profit': potential_profit,
                'market': 'Match Winner'
            }
        
        except Exception as e:
            logger.error(f"ROI-analyysivirhe: {e}")
            return None
    
    def _quick_match_analysis(self, match) -> Optional[Dict[str, Any]]:
        """Nopea analyysi match-datasta"""
        try:
            if not match.odds:
                return None
            
            # Etsi parhaat kertoimet
            best_bookmaker = None
            best_odds_value = 0.0
            best_selection = None
            
            for bookmaker, odds_data in match.odds.items():
                if 'match_winner' in odds_data:
                    for selection, odds in odds_data['match_winner'].items():
                        if odds > best_odds_value:
                            best_odds_value = odds
                            best_selection = selection
                            best_bookmaker = bookmaker
            
            if not best_selection or best_odds_value == 0:
                return None
            
            # Laske ROI
            implied_prob = 1 / best_odds_value
            true_prob = implied_prob * 1.05  # 5% edge
            
            if true_prob > 1.0:
                true_prob = 0.95
            
            expected_value = (true_prob * best_odds_value) - 1
            roi_percentage = expected_value * 100
            
            if roi_percentage < 5.0:
                return None
            
            stake = 100
            potential_profit = stake * (best_odds_value - 1) * true_prob
            edge = (true_prob - implied_prob) * 100
            confidence = min(0.95, true_prob * 0.9)
            
            return {
                'selection': best_selection,
                'odds': best_odds_value,
                'bookmaker': best_bookmaker,
                'roi_percentage': roi_percentage,
                'confidence': confidence,
                'edge': edge,
                'recommended_stake': min(5.0, max(1.0, roi_percentage / 2)),
                'potential_profit': potential_profit,
                'market': 'Match Winner'
            }
        
        except Exception as e:
            logger.error(f"Match-analyysivirhe: {e}")
            return None
    
    def _analyze_tips(self, tips: List[Tip]) -> List[Tip]:
        """Analysoi vihjeet syvemmin - filtteröi pois menneet ottelut"""
        analyzed = []
        now = datetime.now()
        
        for tip in tips:
            # Tarkista että vihje on vielä validi (ei mennyt)
            match_time = tip.match_time
            if isinstance(match_time, str):
                try:
                    match_time = datetime.fromisoformat(match_time.replace('Z', '+00:00'))
                except:
                    continue
            
            # Muunna UTC -> local time jos tarpeen
            if hasattr(match_time, 'tzinfo') and match_time.tzinfo is not None:
                match_time = match_time.replace(tzinfo=None)
            
            # Hylkää menneet ottelut
            if match_time < now:
                continue
            
            # Hylkää liian kaukaiset ottelut (>48h)
            time_diff = (match_time - now).total_seconds()
            if time_diff > 172800:  # 48 tuntia
                continue
            
            # Paranna analyysiä jos mahdollista
            if self.analyzer and self.strategy_engine:
                try:
                    # Voit lisätä syvemmän analyysin tähän
                    pass
                except:
                    pass
            
            analyzed.append(tip)
        
        return analyzed
    
    def _normalize_sport(self, sport_key: str) -> str:
        """Normalisoi urheilulaji"""
        mapping = {
            # Ykkösdivisioonat
            'soccer_epl': 'Football',
            'soccer_spain_la_liga': 'Football',
            'soccer_germany_bundesliga': 'Football',
            'soccer_italy_serie_a': 'Football',
            'soccer_france_ligue_one': 'Football',
            # KAKKOSDIVISIOONAT (PRIORITEETIT)
            'soccer_england_championship': 'Football (Championship)',
            'soccer_germany_bundesliga2': 'Football (2. Bundesliga)',
            'soccer_italy_serie_b': 'Football (Serie B)',
            'soccer_england_league1': 'Football (League One)',
            'soccer_england_league2': 'Football (League Two)',
            # Tennis
            'tennis_atp': 'Tennis',
            'tennis_wta': 'Tennis',
            'tennis_itf': 'Tennis (ITF)',
            # Muut
            'basketball_nba': 'Basketball',
            'icehockey_nhl': 'Ice Hockey'
        }
        return mapping.get(sport_key, sport_key.replace('_', ' ').title())
    
    def display_tips(self, tips: List[Tip] = None):
        """Näytä vihjeet terminaalissa"""
        if tips is None:
            tips = self.tips
        
        if not tips:
            print(f"\n{Fore.YELLOW}⚠️ Ei vihjeitä löytynyt{Style.RESET_ALL}\n")
            return
        
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}💰 LÖYDETYT VIHJEET ({len(tips)} kpl)")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
        
        for i, tip in enumerate(tips, 1):
            # ROI väri
            if tip.roi_percentage >= 15:
                roi_color = Fore.GREEN
                roi_icon = "🔥"
            elif tip.roi_percentage >= 10:
                roi_color = Fore.YELLOW
                roi_icon = "⭐"
            else:
                roi_color = Fore.CYAN
                roi_icon = "💡"
            
            # Confidence väri
            if tip.confidence >= 0.7:
                conf_color = Fore.GREEN
            elif tip.confidence >= 0.5:
                conf_color = Fore.YELLOW
            else:
                conf_color = Fore.RED
            
            # Sport emoji
            sport_emoji = {
                'Football': '⚽',
                'Tennis': '🎾',
                'Basketball': '🏀',
                'Ice Hockey': '🏒'
            }.get(tip.sport, '🏆')
            
            print(f"{Fore.CYAN}{'─'*80}{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}{roi_icon} VIHJE #{i}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'─'*80}{Style.RESET_ALL}")
            print(f"{sport_emoji} {Fore.BOLD}{tip.home_team} vs {tip.away_team}{Style.RESET_ALL}")
            print(f"   📅 {tip.league}")
            print(f"   ⏰ {tip.match_time.strftime('%Y-%m-%d %H:%M')}")
            print(f"   🎯 {tip.market}: {Fore.BOLD}{tip.selection}{Style.RESET_ALL}")
            print(f"   💰 Kertoimet: {Fore.BOLD}{tip.odds:.2f}{Style.RESET_ALL}")
            print(f"   {roi_color}{roi_icon} ROI: {Fore.BOLD}{tip.roi_percentage:.1f}%{Style.RESET_ALL}")
            print(f"   {conf_color}📊 Luottamus: {Fore.BOLD}{tip.confidence:.1%}{Style.RESET_ALL}")
            print(f"   📈 Edge: {Fore.BOLD}{tip.edge:.1f}%{Style.RESET_ALL}")
            print(f"   💵 Suositus: {Fore.BOLD}{tip.recommended_stake:.1f}%{Style.RESET_ALL} panoksesta")
            print(f"   💰 Mahdollinen voitto: {Fore.BOLD}${tip.potential_profit:.0f}{Style.RESET_ALL}")
            print(f"   📡 Lähde: {tip.source}")
            if tip.betfury_link:
                print(f"   🔗 {tip.betfury_link}")
            print()
        
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ Yhteensä {len(tips)} vihjettä löydetty{Style.RESET_ALL}\n")
    
    async def run_continuous_scan(self, interval_seconds: int = 300):
        """Aja jatkuvaa skannausta"""
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}🔄 JATKUVA SKANNAUS KÄYNNISSÄ")
        print(f"{Fore.CYAN}⏰ Skannausväli: {interval_seconds // 60} minuuttia")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
        
        while True:
            try:
                # Skannaa vihjeet
                tips = await self.scan_tips()
                
                # Näytä vihjeet
                self.display_tips(tips)
                
                # Odota seuraavaan skannaukseen
                print(f"{Fore.YELLOW}⏰ Seuraava skannaus {interval_seconds // 60} minuutin kuluttua...{Style.RESET_ALL}\n")
                await asyncio.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}🛑 Skannaus pysäytetty käyttäjän toimesta{Style.RESET_ALL}\n")
                break
            except Exception as e:
                print(f"{Fore.RED}❌ Virhe skannauksessa: {e}{Style.RESET_ALL}\n")
                await asyncio.sleep(60)  # Odota 1 minuutti virheen jälkeen

async def main():
    """Pääfunktio"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}🔍 TERMINAALI VIHJESKANNERI")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
    
    scanner = TerminalTipsScanner()
    
    # Tarkista API:t
    api_status = scanner.check_apis()
    
    # VAIHE 1: Hae KAIKKI päivän ottelut ilman vetovihjeitä
    all_matches = await scanner.scan_all_matches()
    
    # Näytä kaikki ottelut
    scanner.display_all_matches(all_matches)
    
    # VAIHE 2: Kysy haluaako käyttäjä analysoida vihjeet
    print(f"{Fore.YELLOW}Haluatko analysoida vetovihjeet näistä otteluista? (y/n): {Style.RESET_ALL}", end='')
    try:
        response = input().strip().lower()
        if response == 'y':
            # Skannaa vihjeet
            tips = await scanner.scan_tips()
            
            # Näytä vihjeet
            scanner.display_tips(tips)
        else:
            print(f"{Fore.CYAN}✅ Näytetään vain ottelut ilman vetovihjeitä{Style.RESET_ALL}\n")
    except (KeyboardInterrupt, EOFError):
        print(f"\n{Fore.YELLOW}👋 Hei hei!{Style.RESET_ALL}\n")
        return
    
    # Kysy jatkuva skannaus (vain jos vihjeitä löytyi)
    if 'tips' in locals() and tips:
        print(f"{Fore.YELLOW}Haluatko ajaa jatkuvaa skannausta? (y/n): {Style.RESET_ALL}", end='')
        try:
            response = input().strip().lower()
            if response == 'y':
                await scanner.run_continuous_scan(interval_seconds=300)  # 5 minuuttia
        except (KeyboardInterrupt, EOFError):
            print(f"\n{Fore.YELLOW}👋 Hei hei!{Style.RESET_ALL}\n")
    elif 'tips' in locals() and not tips:
        print(f"{Fore.YELLOW}💡 Vinkki: Tarkista API-avaimet jos haluat löytää vihjeitä{Style.RESET_ALL}\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Hei hei!{Style.RESET_ALL}\n")

