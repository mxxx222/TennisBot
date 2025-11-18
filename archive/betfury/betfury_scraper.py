"""
Betfury Scraper - Live Odds and Sharp Money Detection
===================================================

Specializes in:
- Live betting odds with real-time updates
- Odds movement tracking
- Sharp money detection
- Market efficiency analysis
- Value opportunity identification
"""

import asyncio
import aiohttp
import json
import time
import re
from typing import Dict, List, Optional, Any
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import hashlib

logger = logging.getLogger(__name__)

class BetfuryScraper:
    """
    Betfury scraper for live odds and market movements
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = "https://betfury.io"
        self.sports_url = f"{self.base_url}/sports"
        self.session = None
        
        # Headers for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': self.sports_url,
            'Origin': self.base_url
        }
        
        # Odds tracking
        self.odds_history = {}
        self.movement_threshold = 0.05  # 5% minimum movement
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def scrape_match(self, match_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Main method to scrape Betfury odds data for a match
        """
        match_id = match_info.get('id')
        if not match_id:
            logger.error("❌ No match ID provided for Betfury")
            return None
        
        try:
            # Try multiple approaches
            data = await self.scrape_via_selenium(match_info)
            if data:
                return data
            
            # Fallback to direct HTTP scraping
            data = await self.scrape_via_http(match_info)
            if data:
                return data
            
            logger.warning("⚠️ Betfury: All scraping methods failed")
            return None
            
        except Exception as e:
            logger.error(f"💥 Betfury scraping error: {e}")
            return None
    
    async def scrape_via_selenium(self, match_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Use Selenium to handle JavaScript-rendered odds
        """
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--enable-logging')
        
        # Enable network monitoring
        options.add_argument('--enable-logging')
        
        driver = None
        try:
            driver = webdriver.Chrome(options=options)
            
            # Go to sports page
            driver.get(self.sports_url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            await asyncio.sleep(5)  # Wait for odds to load
            
            # Navigate to live sports
            try:
                live_link = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, "Live"))
                )
                live_link.click()
                await asyncio.sleep(3)
            except:
                logger.warning("⚠️ Could not click Live link, continuing...")
            
            # Search for the match
            match_id = match_info.get('id')
            search_success = await self.search_match(driver, match_info)
            
            if not search_success:
                logger.warning("⚠️ Could not find match on Betfury")
                return None
            
            # Extract odds data
            odds_data = self.extract_odds_from_page(driver)
            
            # Monitor network requests for API calls
            network_data = self.extract_api_requests(driver)
            if network_data:
                odds_data.update(network_data)
            
            # Add movement tracking
            odds_data = self.track_odds_movement(odds_data, match_id)
            
            return odds_data
            
        except Exception as e:
            logger.error(f"❌ Betfury Selenium error: {e}")
            return None
        finally:
            if driver:
                driver.quit()
    
    async def search_match(self, driver, match_info: Dict[str, Any]) -> bool:
        """
        Search for specific match on Betfury
        """
        try:
            home_team = match_info.get('home_team', '')
            away_team = match_info.get('away_team', '')
            
            # Try to find search box
            search_selectors = [
                'input[type="search"]',
                'input[placeholder*="search"]',
                '.search-input',
                '.search-field'
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = driver.find_element(By.CSS_SELECTOR, selector)
                    if search_box:
                        break
                except:
                    continue
            
            if not search_box:
                logger.warning("⚠️ No search box found on Betfury")
                return False
            
            # Search for the match
            search_term = f"{home_team} {away_team}"
            search_box.clear()
            search_box.send_keys(search_term)
            
            await asyncio.sleep(2)
            
            # Look for match results
            result_selectors = [
                '.match-card',
                '.bet-card',
                '.event-card',
                '[data-match-id]'
            ]
            
            for selector in result_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.info(f"✅ Found {len(elements)} potential matches")
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error searching for match: {e}")
            return False
    
    def extract_odds_from_page(self, driver) -> Dict[str, Any]:
        """
        Extract odds from the current page
        """
        try:
            odds_data = {
                'odds': {},
                'odds_movement': [],
                'markets': [],
                'last_update': time.time()
            }
            
            # Look for odds in different formats
            odds_selectors = [
                '.odds-button',
                '.odd-button',
                '[data-odd]',
                '.bet-odds',
                '.market-odds'
            ]
            
            for selector in odds_selectors:
                try:
                    odds_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in odds_elements:
                        # Extract odds value
                        odds_text = element.get_attribute('data-odd') or element.text
                        if odds_text:
                            try:
                                odds_value = float(odds_text.strip())
                                
                                # Determine market type
                                market_type = self.determine_market_type(element)
                                
                                if market_type not in odds_data['odds']:
                                    odds_data['odds'][market_type] = {}
                                
                                # Determine selection
                                selection = self.determine_selection(element)
                                odds_data['odds'][market_type][selection] = odds_value
                                
                            except (ValueError, TypeError):
                                continue
                
                except Exception as e:
                    logger.debug(f"⚠️ Error extracting odds with selector {selector}: {e}")
                    continue
            
            # Extract 1X2 odds (most common)
            if '1X2' not in odds_data['odds']:
                odds_data['odds']['1X2'] = {}
                
                # Look for home/draw/away buttons
                selection_map = {
                    'home': ['home', '1', 'team1'],
                    'draw': ['draw', 'x', 'tie'],
                    'away': ['away', '2', 'team2']
                }
                
                for selection, keywords in selection_map.items():
                    value = self.find_odds_by_keywords(driver, keywords)
                    if value:
                        odds_data['odds']['1X2'][selection] = value
            
            # Calculate derived markets
            odds_data = self.calculate_derived_markets(odds_data)
            
            return odds_data
            
        except Exception as e:
            logger.error(f"❌ Error extracting odds: {e}")
            return {}
    
    def determine_market_type(self, element) -> str:
        """
        Determine betting market type from element
        """
        class_names = element.get_attribute('class', '')
        text_content = element.get_attribute('textContent', '').lower()
        
        # Common market patterns
        if any(keyword in class_names.lower() or keyword in text_content.lower() 
               for keyword in ['1x2', 'match']):
            return '1X2'
        
        elif any(keyword in class_names.lower() or keyword in text_content.lower() 
                 for keyword in ['over', 'under', 'total']):
            return 'Total Goals'
        
        elif any(keyword in class_names.lower() or keyword in text_content.lower() 
                 for keyword in ['both', 'btts', 'gg']):
            return 'Both Teams Score'
        
        elif any(keyword in class_names.lower() or keyword in text_content.lower() 
                 for keyword in ['handicap', 'spread']):
            return 'Asian Handicap'
        
        else:
            return 'Unknown'
    
    def determine_selection(self, element) -> str:
        """
        Determine selection (home/draw/away/etc.) from element
        """
        class_names = element.get_attribute('class', '').lower()
        text_content = element.get_attribute('textContent', '').lower()
        
        # Home team indicators
        if any(keyword in class_names for keyword in ['home', '1', 'team1']) or \
           any(keyword in text_content for keyword in ['home', '1']):
            return 'home'
        
        # Draw indicators
        elif any(keyword in class_names for keyword in ['draw', 'x', 'tie']) or \
             any(keyword in text_content for keyword in ['draw', 'x']):
            return 'draw'
        
        # Away team indicators
        elif any(keyword in class_names for keyword in ['away', '2', 'team2']) or \
             any(keyword in text_content for keyword in ['away', '2']):
            return 'away'
        
        # Over/Under
        elif 'over' in class_names or 'over' in text_content:
            return 'over'
        elif 'under' in class_names or 'under' in text_content:
            return 'under'
        
        # Both Teams Score
        elif any(keyword in class_names or keyword in text_content 
                 for keyword in ['yes', 'both']):
            return 'yes'
        elif any(keyword in class_names or keyword in text_content 
                 for keyword in ['no', 'btts']):
            return 'no'
        
        return 'unknown'
    
    def find_odds_by_keywords(self, driver, keywords: List[str]) -> Optional[float]:
        """
        Find odds value by searching for keywords
        """
        for keyword in keywords:
            try:
                # Search in nearby elements
                xpath = f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]"
                elements = driver.find_elements(By.XPATH, xpath)
                
                for element in elements:
                    # Look for odds value in parent or sibling
                    parent = element.find_element(By.XPATH, "./..")
                    siblings = parent.find_elements(By.XPATH, "./following-sibling::*")
                    
                    for sibling in siblings:
                        try:
                            odds_text = sibling.get_attribute('textContent') or sibling.get_attribute('data-odd')
                            if odds_text:
                                odds_value = float(odds_text.strip())
                                return odds_value
                        except (ValueError, TypeError):
                            continue
                            
            except Exception:
                continue
        
        return None
    
    def calculate_derived_markets(self, odds_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate derived betting markets from basic odds
        """
        try:
            # Calculate implied probabilities
            if '1X2' in odds_data['odds']:
                odds = odds_data['odds']['1X2']
                
                if all(market in odds for market in ['home', 'draw', 'away']):
                    # Calculate over/under 2.5 (simple approximation)
                    over_under_25 = self.calculate_over_under(odds['home'], odds['draw'], odds['away'])
                    odds_data['odds']['Total Goals'] = over_under_25
                    
                    # Calculate both teams score
                    btts_odds = self.calculate_btts(odds['home'], odds['draw'], odds['away'])
                    if btts_odds:
                        odds_data['odds']['Both Teams Score'] = btts_odds
            
            return odds_data
            
        except Exception as e:
            logger.error(f"❌ Error calculating derived markets: {e}")
            return odds_data
    
    def calculate_over_under(self, home_odds: float, draw_odds: float, away_odds: float) -> Dict[str, float]:
        """
        Calculate over/under 2.5 goals odds (simplified model)
        """
        try:
            # Simple heuristic: combine home/away odds for over 2.5
            # This is a very simplified calculation
            over_25 = (home_odds + away_odds) / 2
            under_25 = max(1.2, over_25 + 0.5)  # Simple spread
            
            return {
                'over': round(over_25, 2),
                'under': round(under_25, 2)
            }
        except Exception:
            return {'over': 2.0, 'under': 1.8}
    
    def calculate_btts(self, home_odds: float, draw_odds: float, away_odds: float) -> Optional[Dict[str, float]]:
        """
        Calculate both teams score odds
        """
        try:
            # Very simplified calculation
            # Real implementation would need historical data
            
            btts_yes = max(1.5, (home_odds + away_odds) / 3)
            btts_no = btts_yes + 0.3
            
            return {
                'yes': round(btts_yes, 2),
                'no': round(btts_no, 2)
            }
        except Exception:
            return None
    
    def extract_api_requests(self, driver) -> Dict[str, Any]:
        """
        Extract API requests to get live odds data
        """
        try:
            logs = driver.get_log('performance')
            api_data = {}
            
            for entry in logs:
                try:
                    message = json.loads(entry['message'])['message']
                    
                    if message.get('method') == 'Network.responseReceived':
                        url = message['params']['response'].get('url', '')
                        
                        # Look for Betfury API calls
                        if any(pattern in url for pattern in ['odds', 'betting', 'live', 'sports']):
                            # This would require more complex implementation
                            # to actually parse the API responses
                            pass
                            
                except Exception:
                    continue
            
            return api_data
            
        except Exception as e:
            logger.debug(f"⚠️ Error extracting API requests: {e}")
            return {}
    
    def track_odds_movement(self, odds_data: Dict[str, Any], match_id: str) -> Dict[str, Any]:
        """
        Track odds movement and detect sharp money
        """
        try:
            current_time = time.time()
            
            # Initialize match in history if not exists
            if match_id not in self.odds_history:
                self.odds_history[match_id] = {
                    'history': [],
                    'last_odds': {}
                }
            
            history = self.odds_history[match_id]
            
            # Store current odds snapshot
            current_snapshot = {
                'timestamp': current_time,
                'odds': odds_data['odds'].copy()
            }
            
            # Calculate movements
            movements = []
            last_odds = history['last_odds']
            
            for market, market_odds in odds_data['odds'].items():
                if market not in last_odds:
                    continue
                    
                for selection, current_value in market_odds.items():
                    if selection in last_odds[market]:
                        previous_value = last_odds[market][selection]
                        
                        # Calculate percentage change
                        if previous_value > 0:
                            change_pct = ((current_value - previous_value) / previous_value) * 100
                            
                            if abs(change_pct) >= self.movement_threshold * 100:
                                movement = {
                                    'market': market,
                                    'selection': selection,
                                    'previous_odds': previous_value,
                                    'current_odds': current_value,
                                    'change_pct': round(change_pct, 2),
                                    'direction': 'up' if change_pct > 0 else 'down',
                                    'timestamp': current_time
                                }
                                movements.append(movement)
            
            # Update history
            history['history'].append(current_snapshot)
            history['last_odds'] = odds_data['odds'].copy()
            
            # Keep only last 100 snapshots to save memory
            if len(history['history']) > 100:
                history['history'] = history['history'][-100:]
            
            # Add movements to odds data
            odds_data['odds_movement'] = movements
            
            # Calculate sharp money indicator
            odds_data['sharp_money_indicator'] = self.calculate_sharp_money_indicator(movements)
            
            return odds_data
            
        except Exception as e:
            logger.error(f"❌ Error tracking odds movement: {e}")
            return odds_data
    
    def calculate_sharp_money_indicator(self, movements: List[Dict[str, Any]]) -> Optional[float]:
        """
        Calculate sharp money indicator based on odds movements
        """
        if not movements:
            return None
        
        # Sharp money typically moves in the same direction across multiple selections
        direction_score = 0
        significant_moves = 0
        
        for movement in movements:
            if abs(movement['change_pct']) >= 2:  # Only significant moves
                significant_moves += 1
                
                # Weight by movement size
                direction_score += movement['change_pct'] * abs(movement['change_pct']) / 100
        
        if significant_moves >= 2:
            # Normalize to 0-1 scale
            return min(1.0, abs(direction_score) / 10)
        
        return 0.0
    
    async def scrape_via_http(self, match_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Fallback HTTP scraping method
        """
        try:
            # Try to access specific match page
            match_id = match_info.get('id')
            match_url = f"{self.base_url}/match/{match_id}"
            
            async with self.session.get(match_url, headers=self.headers, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    return self.parse_betfury_html(soup)
                else:
                    logger.warning(f"⚠️ Betfury HTTP returned status {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Betfury HTTP scraping error: {e}")
            return None
    
    def parse_betfury_html(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Parse Betfury HTML for odds data
        """
        try:
            odds_data = {
                'odds': {},
                'odds_movement': [],
                'note': 'HTTP scraping fallback'
            }
            
            # This would require detailed knowledge of Betfury's HTML structure
            # For now, return minimal data
            
            return odds_data
            
        except Exception as e:
            logger.error(f"❌ Error parsing Betfury HTML: {e}")
            return {}
    
    async def monitor_odds_live(self, match_id: str, callback: callable, interval: int = 30):
        """
        Monitor odds live for a specific match
        """
        logger.info(f"🔄 Starting live odds monitoring for match {match_id}")
        
        while True:
            try:
                match_info = {'id': match_id}
                current_data = await self.scrape_match(match_info)
                
                if current_data and callback:
                    await callback(current_data)
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"❌ Live odds monitoring error: {e}")
                await asyncio.sleep(interval * 2)  # Back off on error
    
    def get_value_opportunities(self, match_id: str, unified_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify value betting opportunities by comparing odds with xG probabilities
        """
        opportunities = []
        
        try:
            # Get current odds
            if match_id in self.odds_history:
                current_odds = self.odds_history[match_id]['last_odds']
                
                # Get xG data from unified data
                xg_data = unified_data.get('xG', {})
                if xg_data.get('home') and xg_data.get('away'):
                    
                    # Calculate xG-based win probabilities
                    home_xg = xg_data['home']
                    away_xg = xg_data['away']
                    
                    # Simple xG to probability conversion
                    home_prob = self.xg_to_probability(home_xg, away_xg)
                    draw_prob = self.calculate_draw_probability(home_xg, away_xg)
                    away_prob = 1 - home_prob - draw_prob
                    
                    # Check 1X2 market
                    if '1X2' in current_odds:
                        odds_1x2 = current_odds['1X2']
                        
                        for selection, probability in [('home', home_prob), ('draw', draw_prob), ('away', away_prob)]:
                            if selection in odds_1x2:
                                odds = odds_1x2[selection]
                                implied_prob = 1 / odds
                                
                                if probability > implied_prob + 0.05:  # 5% value threshold
                                    value = (probability * odds - 1) * 100
                                    
                                    opportunities.append({
                                        'market': '1X2',
                                        'selection': selection,
                                        'probability': round(probability * 100, 1),
                                        'implied_probability': round(implied_prob * 100, 1),
                                        'odds': odds,
                                        'value_percent': round(value, 1),
                                        'edge': round(probability - implied_prob, 3)
                                    })
            
            return opportunities
            
        except Exception as e:
            logger.error(f"❌ Error finding value opportunities: {e}")
            return []
    
    def xg_to_probability(self, team_xg: float, opponent_xg: float) -> float:
        """
        Convert xG to win probability
        """
        try:
            # Simple approximation
            total_xg = team_xg + opponent_xg
            if total_xg > 0:
                return team_xg / total_xg
            return 0.33  # Equal probability if no xG data
        except Exception:
            return 0.33
    
    def calculate_draw_probability(self, home_xg: float, away_xg: float) -> float:
        """
        Calculate draw probability based on xG difference
        """
        try:
            xg_diff = abs(home_xg - away_xg)
            
            # More balanced xG = higher draw probability
            base_draw_prob = 0.25
            balance_factor = max(0, 1 - (xg_diff / 3))  # Normalize to 0-1
            
            return base_draw_prob * balance_factor + 0.15  # Minimum 15% draw probability
            
        except Exception:
            return 0.25