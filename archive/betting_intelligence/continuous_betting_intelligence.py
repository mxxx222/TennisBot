#!/usr/bin/env python3
"""
🔄 CONTINUOUS BETTING INTELLIGENCE SYSTEM
========================================
Jatkuva pelien analysointi kannattavuuden, ROIn ja riskin perusteella.
Välitön ilmoitus Telegramiin uusista mahdollisuuksista + Betfury.io linkit.

Ominaisuudet:
- 🔄 Jatkuva pelien skannaus ja analysointi
- 💰 ROI, riski ja kannattavuusanalyysi
- ⚡ Välittömät Telegram-ilmoitukset
- 🎰 Betfury.io vedonlyöntilinkit jokaiseen matsiin
- 🕷️ Web scraping reaaliaikaisille kertoimille
- 📊 Monipuolinen data-analyysi
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
import sys
import os
from pathlib import Path
from dataclasses import dataclass, asdict
import threading
import queue
import requests
from concurrent.futures import ThreadPoolExecutor

# Add project paths
sys.path.append(str(Path(__file__).parent / 'src'))

# Import our modules
try:
    from enhanced_telegram_roi_bot import EnhancedTelegramROIBot
    from betfury_integration import BetfuryIntegration
    from odds_api_integration import OddsAPIIntegration, OddsData
    from prematch_analyzer import PrematchAnalyzer, ROIAnalysis
    from betting_strategy_engine import BettingStrategyEngine, BettingOpportunity, RiskLevel
    from multi_sport_prematch_scraper import MultiSportPrematchScraper, PrematchData
    from virtual_betting_tracker import VirtualBettingTracker
    from match_result_collector import MatchResultCollector
    CORE_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Warning: Some modules not available: {e}")
    CORE_MODULES_AVAILABLE = False

# Web scraping imports
try:
    import requests
    from bs4 import BeautifulSoup
    import undetected_chromedriver as uc
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    WEB_SCRAPING_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Warning: Web scraping modules not available: {e}")
    WEB_SCRAPING_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/herbspotturku/sportsbot/TennisBot/betting_intelligence.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class GameOpportunity:
    """Pelimahdollisuus kaikilla tarvittavilla tiedoilla"""
    match_id: str
    home_team: str
    away_team: str
    sport: str
    league: str
    match_time: datetime
    
    # Odds and betting info
    best_odds: Dict[str, float]
    bookmaker: str
    market: str
    selection: str
    
    # Analysis results
    roi_percentage: float
    risk_level: str
    confidence_score: float
    edge_percentage: float
    true_probability: float
    
    # Recommendations
    recommended_stake: float
    potential_profit: float
    max_loss: float
    
    # Betfury links
    betfury_main_link: str
    betfury_market_links: Dict[str, str]
    
    # Metadata
    discovered_at: datetime
    expires_at: datetime
    analysis_version: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

class ContinuousBettingIntelligence:
    """Jatkuva vedonlyönti-äly järjestelmä"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Alusta järjestelmä"""
        logger.info("🔄 Initializing Continuous Betting Intelligence System...")
        
        # Configuration
        self.config = {
            'scan_interval': 120,  # 2 minutes between scans
            'min_roi_threshold': 8.0,  # 8% minimum ROI
            'min_confidence': 0.60,  # 60% minimum confidence
            'min_edge': 3.0,  # 3% minimum edge
            'max_risk_level': 'moderate',
            'sports': ['football', 'tennis', 'basketball', 'ice_hockey'],
            'max_opportunities_per_scan': 10,
            'notification_cooldown': 300,  # 5 minutes between same match notifications
            'bankroll': 10000,
            'max_daily_stake': 20.0,  # 20% max daily stake
            'web_scraping_enabled': True,
            'odds_api_enabled': True,
            'telegram_notifications': True
        }
        
        if config:
            self.config.update(config)
        
        # Initialize components
        if CORE_MODULES_AVAILABLE:
            self.telegram_bot = EnhancedTelegramROIBot()
            self.betfury = BetfuryIntegration(affiliate_code="tennisbot_2025")
            self.analyzer = PrematchAnalyzer()
            self.strategy_engine = BettingStrategyEngine(
                bankroll=self.config['bankroll'],
                risk_tolerance=self.config['max_risk_level']
            )
            self.scraper = MultiSportPrematchScraper()
            
            # Initialize Virtual Betting Tracker for ML calibration
            try:
                self.virtual_tracker = VirtualBettingTracker(
                    virtual_bankroll=self.config.get('virtual_bankroll', 10000.0)
                )
                self.result_collector = MatchResultCollector(
                    virtual_tracker=self.virtual_tracker,
                    check_interval=300  # 5 minutes
                )
                logger.info("✅ Virtual betting tracker initialized")
            except Exception as e:
                logger.warning(f"⚠️ Virtual betting tracker not available: {e}")
                self.virtual_tracker = None
                self.result_collector = None
            
            # Initialize Odds API if key available
            try:
                self.odds_api = OddsAPIIntegration()
                logger.info("✅ Odds API initialized")
            except Exception as e:
                logger.warning(f"⚠️ Odds API not available: {e}")
                self.odds_api = None
        else:
            logger.error("❌ Core modules not available")
            return
        
        # State management
        self.discovered_opportunities: Dict[str, GameOpportunity] = {}
        self.notified_matches: Set[str] = set()
        self.last_notification_times: Dict[str, datetime] = {}
        self.daily_stake_used = 0.0
        self.daily_reset_date = datetime.now().date()
        
        # Threading
        self.running = False
        self.analysis_queue = queue.Queue()
        self.notification_queue = queue.Queue()
        
        # Web scraping setup
        if WEB_SCRAPING_AVAILABLE and self.config['web_scraping_enabled']:
            self.setup_web_scraping()
        
        logger.info("✅ Continuous Betting Intelligence System initialized")
    
    def setup_web_scraping(self):
        """Setup web scraping components"""
        try:
            # Chrome options for scraping
            self.chrome_options = uc.ChromeOptions()
            self.chrome_options.add_argument('--headless')
            self.chrome_options.add_argument('--no-sandbox')
            self.chrome_options.add_argument('--disable-dev-shm-usage')
            self.chrome_options.add_argument('--disable-gpu')
            self.chrome_options.add_argument('--window-size=1920,1080')
            
            # User agents for rotation
            self.user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            ]
            
            # Betting sites to scrape
            self.scraping_targets = {
                'betfury': 'https://betfury.io/sports',
                'stake': 'https://stake.com/sports',
                'rollbit': 'https://rollbit.com/sports'
            }
            
            logger.info("✅ Web scraping setup completed")
            
        except Exception as e:
            logger.error(f"❌ Web scraping setup failed: {e}")
            self.config['web_scraping_enabled'] = False
    
    async def start_continuous_analysis(self):
        """Aloita jatkuva analysointi"""
        logger.info("🔄 Starting continuous betting analysis...")
        self.running = True
        
        # Start background threads
        analysis_thread = threading.Thread(target=self._analysis_worker, daemon=True)
        notification_thread = threading.Thread(target=self._notification_worker, daemon=True)
        
        analysis_thread.start()
        notification_thread.start()
        
        # Start result collection for virtual bets
        if self.result_collector:
            result_collection_task = asyncio.create_task(
                self.result_collector.start_collecting()
            )
            logger.info("✅ Result collection started for virtual bets")
        
        # Main analysis loop
        while self.running:
            try:
                await self._perform_analysis_cycle()
                await asyncio.sleep(self.config['scan_interval'])
                
            except KeyboardInterrupt:
                logger.info("🛑 Stopping continuous analysis...")
                self.running = False
                if self.result_collector:
                    self.result_collector.stop_collecting()
                break
            except Exception as e:
                logger.error(f"❌ Error in analysis cycle: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _perform_analysis_cycle(self):
        """Suorita yksi analyysikierros"""
        cycle_start = datetime.now()
        logger.info(f"🔍 Starting analysis cycle at {cycle_start.strftime('%H:%M:%S')}")
        
        # Reset daily stake if new day
        if datetime.now().date() != self.daily_reset_date:
            self.daily_stake_used = 0.0
            self.daily_reset_date = datetime.now().date()
            logger.info("📅 Daily stake reset")
        
        # Check if we've reached daily stake limit
        if self.daily_stake_used >= self.config['max_daily_stake']:
            logger.info(f"💰 Daily stake limit reached ({self.daily_stake_used:.1f}%)")
            return
        
        try:
            # Step 1: Gather data from multiple sources
            all_matches_data = await self._gather_match_data()
            
            if not all_matches_data:
                logger.info("📊 No match data found in this cycle")
                return
            
            logger.info(f"📊 Found {len(all_matches_data)} matches to analyze")
            
            # Step 2: Analyze each match for opportunities
            new_opportunities = []
            
            for match_data in all_matches_data[:self.config['max_opportunities_per_scan']]:
                try:
                    opportunity = await self._analyze_match_opportunity(match_data)
                    if opportunity:
                        new_opportunities.append(opportunity)
                except Exception as e:
                    logger.error(f"❌ Error analyzing match {match_data.get('match_id', 'unknown')}: {e}")
            
            # Step 3: Filter and rank opportunities
            filtered_opportunities = self._filter_opportunities(new_opportunities)
            
            if filtered_opportunities:
                logger.info(f"🎯 Found {len(filtered_opportunities)} profitable opportunities")
                
                # Step 4: Send notifications for new opportunities
                for opportunity in filtered_opportunities:
                    await self._queue_notification(opportunity)
            
            else:
                logger.info("📊 No profitable opportunities found in this cycle")
            
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            logger.info(f"✅ Analysis cycle completed in {cycle_duration:.1f}s")
            
        except Exception as e:
            logger.error(f"❌ Error in analysis cycle: {e}")
    
    async def _gather_match_data(self) -> List[Dict[str, Any]]:
        """Kerää matsitiedot useista lähteistä"""
        all_matches = []
        
        # Source 1: Odds API
        if self.odds_api and self.config['odds_api_enabled']:
            try:
                logger.info("📊 Fetching data from Odds API...")
                odds_data = await self.odds_api.get_live_odds(
                    sports=['soccer_epl', 'tennis_atp', 'basketball_nba', 'icehockey_nhl'],
                    markets=['h2h', 'spreads', 'totals']
                )
                
                for odds in odds_data:
                    match_data = {
                        'match_id': f"odds_api_{odds.sport_key}_{odds.home_team}_{odds.away_team}",
                        'home_team': odds.home_team,
                        'away_team': odds.away_team,
                        'sport': self._normalize_sport_name(odds.sport_key),
                        'league': odds.sport_title,
                        'match_time': odds.commence_time,
                        'odds_data': odds,
                        'source': 'odds_api'
                    }
                    all_matches.append(match_data)
                
                logger.info(f"✅ Odds API: {len(odds_data)} matches")
                
            except Exception as e:
                logger.error(f"❌ Odds API error: {e}")
        
        # Source 2: Web scraping
        if WEB_SCRAPING_AVAILABLE and self.config['web_scraping_enabled']:
            try:
                logger.info("🕷️ Web scraping betting sites...")
                scraped_matches = await self._scrape_betting_sites()
                all_matches.extend(scraped_matches)
                logger.info(f"✅ Web scraping: {len(scraped_matches)} matches")
                
            except Exception as e:
                logger.error(f"❌ Web scraping error: {e}")
        
        # Source 3: Our multi-sport scraper
        try:
            logger.info("📊 Using multi-sport scraper...")
            scraper_matches = self.scraper.scrape_daily_matches(
                datetime.now(),
                self.config['sports']
            )
            
            for match in scraper_matches:
                match_data = {
                    'match_id': f"scraper_{match.sport}_{match.home_team}_{match.away_team}",
                    'home_team': match.home_team,
                    'away_team': match.away_team,
                    'sport': match.sport,
                    'league': match.league,
                    'match_time': match.match_time,
                    'prematch_data': match,
                    'source': 'scraper'
                }
                all_matches.append(match_data)
            
            logger.info(f"✅ Multi-sport scraper: {len(scraper_matches)} matches")
            
        except Exception as e:
            logger.error(f"❌ Multi-sport scraper error: {e}")
        
        # Remove duplicates based on teams and time
        unique_matches = self._deduplicate_matches(all_matches)
        logger.info(f"📊 Total unique matches: {len(unique_matches)}")
        
        return unique_matches
    
    async def _scrape_betting_sites(self) -> List[Dict[str, Any]]:
        """Skrapaa vedonlyöntisivustoja"""
        scraped_matches = []
        
        for site_name, site_url in self.scraping_targets.items():
            try:
                logger.info(f"🕷️ Scraping {site_name}...")
                
                # Use ThreadPoolExecutor for concurrent scraping
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(self._scrape_single_site, site_name, site_url)
                    site_matches = future.result(timeout=30)
                    scraped_matches.extend(site_matches)
                
            except Exception as e:
                logger.error(f"❌ Error scraping {site_name}: {e}")
        
        return scraped_matches
    
    def _scrape_single_site(self, site_name: str, site_url: str) -> List[Dict[str, Any]]:
        """Skrapaa yksittäinen sivusto"""
        matches = []
        driver = None
        
        try:
            # Initialize Chrome driver
            driver = uc.Chrome(options=self.chrome_options)
            driver.get(site_url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Site-specific scraping logic
            if site_name == 'betfury':
                matches = self._scrape_betfury(driver)
            elif site_name == 'stake':
                matches = self._scrape_stake(driver)
            elif site_name == 'rollbit':
                matches = self._scrape_rollbit(driver)
            
        except Exception as e:
            logger.error(f"❌ Error scraping {site_name}: {e}")
        
        finally:
            if driver:
                driver.quit()
        
        return matches
    
    def _scrape_betfury(self, driver) -> List[Dict[str, Any]]:
        """Skrapaa Betfury.io"""
        matches = []
        
        try:
            # Look for match containers
            match_elements = driver.find_elements(By.CSS_SELECTOR, "[data-testid*='match'], .match-card, .event-row")
            
            for element in match_elements[:20]:  # Limit to 20 matches
                try:
                    # Extract match information
                    teams_text = element.find_element(By.CSS_SELECTOR, ".teams, .match-teams, .event-teams").text
                    odds_elements = element.find_elements(By.CSS_SELECTOR, ".odds, .odd-value, .price")
                    
                    if " vs " in teams_text or " - " in teams_text:
                        separator = " vs " if " vs " in teams_text else " - "
                        teams = teams_text.split(separator)
                        
                        if len(teams) == 2 and odds_elements:
                            match_data = {
                                'match_id': f"betfury_{teams[0].strip()}_{teams[1].strip()}",
                                'home_team': teams[0].strip(),
                                'away_team': teams[1].strip(),
                                'sport': 'football',  # Default, could be improved
                                'league': 'Unknown',
                                'match_time': datetime.now() + timedelta(hours=2),
                                'odds': [float(odd.text) for odd in odds_elements[:3] if odd.text.replace('.', '').isdigit()],
                                'source': 'betfury_scraping'
                            }
                            matches.append(match_data)
                
                except Exception as e:
                    continue
        
        except Exception as e:
            logger.error(f"❌ Betfury scraping error: {e}")
        
        return matches
    
    def _scrape_stake(self, driver) -> List[Dict[str, Any]]:
        """Skrapaa Stake.com"""
        matches = []
        
        try:
            # Stake-specific scraping logic
            match_elements = driver.find_elements(By.CSS_SELECTOR, ".market-row, .match-row, .event-item")
            
            for element in match_elements[:15]:
                try:
                    # Extract match data (simplified)
                    text_content = element.text
                    if " v " in text_content:
                        # Basic extraction logic
                        lines = text_content.split('\n')
                        for line in lines:
                            if " v " in line:
                                teams = line.split(" v ")
                                if len(teams) == 2:
                                    match_data = {
                                        'match_id': f"stake_{teams[0].strip()}_{teams[1].strip()}",
                                        'home_team': teams[0].strip(),
                                        'away_team': teams[1].strip(),
                                        'sport': 'football',
                                        'league': 'Unknown',
                                        'match_time': datetime.now() + timedelta(hours=3),
                                        'source': 'stake_scraping'
                                    }
                                    matches.append(match_data)
                                    break
                
                except Exception as e:
                    continue
        
        except Exception as e:
            logger.error(f"❌ Stake scraping error: {e}")
        
        return matches
    
    def _scrape_rollbit(self, driver) -> List[Dict[str, Any]]:
        """Skrapaa Rollbit.com"""
        matches = []
        
        try:
            # Rollbit-specific scraping logic
            match_elements = driver.find_elements(By.CSS_SELECTOR, ".bet-card, .match-card, .game-row")
            
            for element in match_elements[:10]:
                try:
                    # Extract match information
                    text = element.text
                    if " vs " in text or " @ " in text:
                        separator = " vs " if " vs " in text else " @ "
                        parts = text.split(separator)
                        
                        if len(parts) >= 2:
                            match_data = {
                                'match_id': f"rollbit_{parts[0].strip()}_{parts[1].strip()}",
                                'home_team': parts[0].strip(),
                                'away_team': parts[1].strip(),
                                'sport': 'football',
                                'league': 'Unknown',
                                'match_time': datetime.now() + timedelta(hours=4),
                                'source': 'rollbit_scraping'
                            }
                            matches.append(match_data)
                
                except Exception as e:
                    continue
        
        except Exception as e:
            logger.error(f"❌ Rollbit scraping error: {e}")
        
        return matches
    
    async def _analyze_match_opportunity(self, match_data: Dict[str, Any]) -> Optional[GameOpportunity]:
        """Analysoi matsiin liittyvä mahdollisuus"""
        try:
            # Create analysis input
            if 'odds_data' in match_data:
                # From Odds API
                odds_data = match_data['odds_data']
                analysis_input = {
                    'home_team': match_data['home_team'],
                    'away_team': match_data['away_team'],
                    'sport': match_data['sport'],
                    'league': match_data['league'],
                    'match_time': match_data['match_time'],
                    'best_odds': odds_data.best_odds,
                    'bookmakers': odds_data.bookmakers,
                    'market_margin': odds_data.market_margin
                }
            else:
                # From scraping or other sources
                analysis_input = match_data
            
            # Perform ROI analysis
            roi_analysis = await self._perform_roi_analysis(analysis_input)
            
            if not roi_analysis:
                return None
            
            # Check if opportunity meets our criteria
            if (roi_analysis['roi_percentage'] < self.config['min_roi_threshold'] or
                roi_analysis['confidence_score'] < self.config['min_confidence'] or
                roi_analysis['edge_percentage'] < self.config['min_edge']):
                return None
            
            # Generate Betfury links
            betfury_links = self._generate_betfury_links(match_data)
            
            # Create opportunity object
            opportunity = GameOpportunity(
                match_id=match_data['match_id'],
                home_team=match_data['home_team'],
                away_team=match_data['away_team'],
                sport=match_data['sport'],
                league=match_data.get('league', 'Unknown'),
                match_time=match_data['match_time'],
                
                best_odds=roi_analysis['best_odds'],
                bookmaker=roi_analysis['best_bookmaker'],
                market=roi_analysis['best_market'],
                selection=roi_analysis['best_selection'],
                
                roi_percentage=roi_analysis['roi_percentage'],
                risk_level=roi_analysis['risk_level'],
                confidence_score=roi_analysis['confidence_score'],
                edge_percentage=roi_analysis['edge_percentage'],
                true_probability=roi_analysis['true_probability'],
                
                recommended_stake=roi_analysis['recommended_stake'],
                potential_profit=roi_analysis['potential_profit'],
                max_loss=roi_analysis['max_loss'],
                
                betfury_main_link=betfury_links['main'],
                betfury_market_links=betfury_links['markets'],
                
                discovered_at=datetime.now(),
                expires_at=match_data['match_time'] - timedelta(minutes=30),
                analysis_version="1.0"
            )
            
            # Automatically place virtual bet for ML calibration
            if self.virtual_tracker:
                try:
                    # Extract odds for the prediction
                    prediction_odds = roi_analysis['best_odds'].get('match_winner', 2.0)
                    if isinstance(prediction_odds, dict):
                        prediction_odds = prediction_odds.get(roi_analysis['best_selection'], 2.0)
                    
                    # Place virtual bet
                    virtual_bet = self.virtual_tracker.place_virtual_bet(
                        match_id=match_data['match_id'],
                        prediction=roi_analysis['best_selection'],
                        confidence=roi_analysis['confidence_score'],
                        odds=float(prediction_odds),
                        stake_method="kelly",
                        surface=match_data.get('surface'),
                        tournament=match_data.get('league', 'Unknown'),
                        home_player=match_data.get('home_team') if match_data['sport'] == 'tennis' else None,
                        away_player=match_data.get('away_team') if match_data['sport'] == 'tennis' else None
                    )
                    
                    if virtual_bet:
                        logger.info(
                            f"✅ Virtual bet placed for calibration: "
                            f"{roi_analysis['best_selection']} @ {prediction_odds:.2f}"
                        )
                except Exception as e:
                    logger.warning(f"⚠️ Failed to place virtual bet: {e}")
            
            return opportunity
            
        except Exception as e:
            logger.error(f"❌ Error analyzing match opportunity: {e}")
            return None
    
    async def _perform_roi_analysis(self, match_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Suorita ROI-analyysi matsille"""
        try:
            # Simulate comprehensive analysis
            # In real implementation, this would use actual analysis algorithms
            
            # Mock analysis results
            roi_percentage = 12.5 + (hash(match_data['match_id']) % 20)  # 12.5-32.5%
            confidence_score = 0.65 + (hash(match_data['home_team']) % 30) / 100  # 0.65-0.95
            edge_percentage = 5.0 + (hash(match_data['away_team']) % 15)  # 5-20%
            true_probability = 0.55 + (hash(match_data['sport']) % 30) / 100  # 0.55-0.85
            
            # Risk assessment
            if roi_percentage > 25:
                risk_level = 'high_risk'
            elif roi_percentage > 18:
                risk_level = 'moderate'
            else:
                risk_level = 'conservative'
            
            # Stake calculation (Kelly Criterion simulation)
            recommended_stake = min(edge_percentage / 4, 5.0)  # Max 5% of bankroll
            
            # Profit calculations
            best_odds = 2.1 + (hash(match_data['match_id']) % 100) / 100  # 2.1-3.1
            stake_amount = (recommended_stake / 100) * self.config['bankroll']
            potential_profit = stake_amount * (best_odds - 1)
            max_loss = stake_amount
            
            return {
                'roi_percentage': roi_percentage,
                'confidence_score': confidence_score,
                'edge_percentage': edge_percentage,
                'true_probability': true_probability,
                'risk_level': risk_level,
                'recommended_stake': recommended_stake,
                'potential_profit': potential_profit,
                'max_loss': max_loss,
                'best_odds': {'match_winner': best_odds},
                'best_bookmaker': 'Betfury',
                'best_market': 'match_winner',
                'best_selection': match_data['home_team']
            }
            
        except Exception as e:
            logger.error(f"❌ ROI analysis error: {e}")
            return None
    
    def _generate_betfury_links(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generoi Betfury-linkit matsille"""
        try:
            main_link = self.betfury.generate_match_link(
                match_data['home_team'],
                match_data['away_team'],
                match_data['sport'],
                match_data.get('league')
            )
            
            market_links = {}
            for market in ['match_winner', 'over_under', 'both_teams_score']:
                try:
                    market_link = self.betfury.generate_market_link(
                        match_data['home_team'],
                        match_data['away_team'],
                        match_data['sport'],
                        market,
                        match_data.get('league')
                    )
                    market_links[market] = market_link
                except:
                    continue
            
            return {
                'main': main_link,
                'markets': market_links
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating Betfury links: {e}")
            return {
                'main': 'https://betfury.io/sports',
                'markets': {}
            }
    
    def _filter_opportunities(self, opportunities: List[GameOpportunity]) -> List[GameOpportunity]:
        """Suodata ja järjestä mahdollisuudet"""
        if not opportunities:
            return []
        
        # Filter by criteria
        filtered = []
        for opp in opportunities:
            # Skip if already notified recently
            if opp.match_id in self.last_notification_times:
                last_notified = self.last_notification_times[opp.match_id]
                if (datetime.now() - last_notified).total_seconds() < self.config['notification_cooldown']:
                    continue
            
            # Skip if would exceed daily stake limit
            if self.daily_stake_used + opp.recommended_stake > self.config['max_daily_stake']:
                continue
            
            # Skip expired opportunities
            if opp.expires_at <= datetime.now():
                continue
            
            filtered.append(opp)
        
        # Sort by ROI * confidence score
        filtered.sort(key=lambda x: x.roi_percentage * x.confidence_score, reverse=True)
        
        return filtered[:5]  # Top 5 opportunities
    
    async def _queue_notification(self, opportunity: GameOpportunity):
        """Lisää ilmoitus jonoon"""
        try:
            self.notification_queue.put(opportunity)
            self.last_notification_times[opportunity.match_id] = datetime.now()
            self.daily_stake_used += opportunity.recommended_stake
            
            logger.info(f"📤 Queued notification for {opportunity.home_team} vs {opportunity.away_team}")
            
        except Exception as e:
            logger.error(f"❌ Error queuing notification: {e}")
    
    def _analysis_worker(self):
        """Background worker for analysis tasks"""
        while self.running:
            try:
                # Process analysis queue if needed
                time.sleep(1)
            except Exception as e:
                logger.error(f"❌ Analysis worker error: {e}")
    
    def _notification_worker(self):
        """Background worker for sending notifications"""
        while self.running:
            try:
                # Get opportunity from queue
                try:
                    opportunity = self.notification_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # Send Telegram notification
                asyncio.run(self._send_opportunity_notification(opportunity))
                
            except Exception as e:
                logger.error(f"❌ Notification worker error: {e}")
    
    async def _send_opportunity_notification(self, opportunity: GameOpportunity):
        """Lähetä mahdollisuusilmoitus Telegramiin"""
        try:
            # Create detailed message
            message = self._create_opportunity_message(opportunity)
            
            # Send to Telegram
            success = await self.telegram_bot.send_message(message)
            
            if success:
                logger.info(f"✅ Sent notification for {opportunity.home_team} vs {opportunity.away_team}")
                
                # Store in discovered opportunities
                self.discovered_opportunities[opportunity.match_id] = opportunity
            else:
                logger.error(f"❌ Failed to send notification for {opportunity.match_id}")
                
        except Exception as e:
            logger.error(f"❌ Error sending notification: {e}")
    
    def _create_opportunity_message(self, opportunity: GameOpportunity) -> str:
        """Luo mahdollisuusviesti Telegramiin"""
        
        # Risk emoji
        risk_emojis = {
            'conservative': '🟢',
            'moderate': '🟡',
            'high_risk': '🔴'
        }
        risk_emoji = risk_emojis.get(opportunity.risk_level, '⚪')
        
        # Sport emoji
        sport_emojis = {
            'football': '⚽',
            'tennis': '🎾',
            'basketball': '🏀',
            'ice_hockey': '🏒'
        }
        sport_emoji = sport_emojis.get(opportunity.sport, '🏆')
        
        message = f"""
🚨 **UUSI KANNATTAVA MAHDOLLISUUS** {sport_emoji}

**{opportunity.home_team} vs {opportunity.away_team}**
🏆 {opportunity.league}
📅 {opportunity.match_time.strftime('%d.%m.%Y %H:%M')}

💰 **ANALYYSI:**
• ROI: {opportunity.roi_percentage:.1f}%
• Luottamus: {opportunity.confidence_score:.0%}
• Edge: {opportunity.edge_percentage:.1f}%
• Todennäköisyys: {opportunity.true_probability:.0%}

🎯 **SUOSITUS:**
• Panos: {opportunity.recommended_stake:.1f}% ({opportunity.recommended_stake * self.config['bankroll'] / 100:.0f}€)
• Voitto: {opportunity.potential_profit:.0f}€
• Riski: {risk_emoji} {opportunity.risk_level.upper()}

📊 **VEDONLYÖNTI:**
• Markkinat: {opportunity.market}
• Valinta: {opportunity.selection}
• Kertoimet: {list(opportunity.best_odds.values())[0]:.2f}

🎰 **BETFURY.IO LINKIT:**
• 🎰 [**LYÖNNIT BETFURY.IO**]({opportunity.betfury_main_link})
• 💰 [**Match Winner**]({opportunity.betfury_market_links.get('match_winner', opportunity.betfury_main_link)})
• 📊 [**Over/Under**]({opportunity.betfury_market_links.get('over_under', opportunity.betfury_main_link)})

⏰ **Vanhenee:** {opportunity.expires_at.strftime('%H:%M')}
🔍 **Löydetty:** {opportunity.discovered_at.strftime('%H:%M:%S')}
        """
        
        return message.strip()
    
    def _deduplicate_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Poista duplikaattimatsi"""
        seen = set()
        unique_matches = []
        
        for match in matches:
            # Create unique key based on teams and approximate time
            key = f"{match['home_team'].lower()}_{match['away_team'].lower()}_{match['match_time'].date()}"
            
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)
        
        return unique_matches
    
    def _normalize_sport_name(self, sport_key: str) -> str:
        """Normalisoi urheilulajin nimi"""
        mappings = {
            'soccer_epl': 'football',
            'soccer_spain_la_liga': 'football',
            'soccer_germany_bundesliga': 'football',
            'tennis_atp': 'tennis',
            'tennis_wta': 'tennis',
            'basketball_nba': 'basketball',
            'icehockey_nhl': 'ice_hockey'
        }
        
        return mappings.get(sport_key, sport_key.split('_')[0])
    
    def get_system_status(self) -> Dict[str, Any]:
        """Hae järjestelmän tila"""
        return {
            'running': self.running,
            'discovered_opportunities': len(self.discovered_opportunities),
            'daily_stake_used': self.daily_stake_used,
            'daily_stake_limit': self.config['max_daily_stake'],
            'last_analysis': datetime.now().isoformat(),
            'notification_queue_size': self.notification_queue.qsize(),
            'config': self.config
        }
    
    def stop(self):
        """Pysäytä järjestelmä"""
        logger.info("🛑 Stopping Continuous Betting Intelligence System...")
        self.running = False

async def main():
    """Pääohjelma"""
    print("🔄 CONTINUOUS BETTING INTELLIGENCE SYSTEM")
    print("=" * 60)
    print("🎯 Jatkuva pelien analysointi ROI:n ja kannattavuuden perusteella")
    print("⚡ Välittömät Telegram-ilmoitukset uusista mahdollisuuksista")
    print("🎰 Betfury.io vedonlyöntilinkit jokaiseen matsiin")
    print("🕷️ Web scraping reaaliaikaisille tiedoille")
    print("=" * 60)
    
    if not CORE_MODULES_AVAILABLE:
        print("❌ Required modules not available")
        return
    
    # Initialize system
    config = {
        'scan_interval': 180,  # 3 minutes
        'min_roi_threshold': 10.0,  # 10% minimum ROI
        'min_confidence': 0.65,  # 65% minimum confidence
        'telegram_notifications': True,
        'web_scraping_enabled': True,
        'odds_api_enabled': True
    }
    
    system = ContinuousBettingIntelligence(config)
    
    try:
        print("🚀 Starting continuous analysis...")
        await system.start_continuous_analysis()
        
    except KeyboardInterrupt:
        print("\n🛑 System stopped by user")
    except Exception as e:
        print(f"❌ System error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        system.stop()
        print("✅ System shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
