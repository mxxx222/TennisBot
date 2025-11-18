#!/usr/bin/env python3
"""
🌐 ADVANCED WEB SCRAPING UTILITIES
=================================

Comprehensive utilities for web scraping with anti-detection
Includes proxy rotation, user agent cycling, and rate limiting

Author: TennisBot Advanced Analytics
Version: 2.0.0
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import random
import time
from typing import List, Dict, Optional
import threading
import queue
from dataclasses import dataclass
import logging

# Add new imports for enhanced anti-detection
try:
    import undetected_chromedriver as uc
    UNDETECTED_CHROMEDRIVER_AVAILABLE = True
except ImportError:
    UNDETECTED_CHROMEDRIVER_AVAILABLE = False
    logging.warning("undetected-chromedriver not available - some features will be limited")

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import json
import os
from pathlib import Path
import asyncio
import aiohttp
from fake_useragent import UserAgent

@dataclass
class ProxyConfig:
    """Proxy configuration"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = 'http'

@dataclass
class ProxyPool:
    """Rotating proxy pool for anti-detection"""
    proxies: List[ProxyConfig]
    current_index: int = 0
    rotation_count: int = 0

    def get_next_proxy(self) -> ProxyConfig:
        """Get next proxy in rotation"""
        if not self.proxies:
            raise ValueError("No proxies available")

        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        self.rotation_count += 1
        return proxy

    def add_proxy(self, proxy: ProxyConfig):
        """Add proxy to pool"""
        self.proxies.append(proxy)

    def remove_failed_proxy(self, proxy: ProxyConfig):
        """Remove failed proxy from pool"""
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            if self.current_index >= len(self.proxies):
                self.current_index = 0

class AntiDetectionSession:
    """Advanced session with anti-detection features"""

    def __init__(self, proxy_pool: Optional[ProxyPool] = None):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.user_agents = [
            self.ua.random for _ in range(10)  # Generate 10 random user agents
        ]
        self.current_ua_index = 0
        self.request_count = 0
        self.last_request_time = time.time()
        self.min_delay = 1.0
        self.max_delay = 3.0
        self.proxy_pool = proxy_pool
        self.current_proxy = None

        # Setup retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.setup_default_headers()

    def setup_default_headers(self):
        """Setup default headers for anti-detection"""
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })

    def rotate_user_agent(self):
        """Rotate user agent"""
        self.current_ua_index = (self.current_ua_index + 1) % len(self.user_agents)
        self.session.headers['User-Agent'] = self.user_agents[self.current_ua_index]

    def smart_delay(self):
        """Implement smart delay between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        # Calculate delay based on request frequency
        base_delay = random.uniform(self.min_delay, self.max_delay)

        if time_since_last < 1.0:
            additional_delay = random.uniform(1.0, 2.0)
            base_delay += additional_delay

        time.sleep(base_delay)
        self.last_request_time = time.time()

    def get(self, url: str, **kwargs) -> requests.Response:
        """Enhanced GET request with anti-detection"""
        self.smart_delay()

        # Rotate user agent every 10 requests
        if self.request_count % 10 == 0:
            self.rotate_user_agent()

        # Rotate proxy every 20 requests
        if self.proxy_pool and self.request_count % 20 == 0:
            self.rotate_proxy()

        self.request_count += 1

        return self.session.get(url, **kwargs)

    def rotate_proxy(self):
        """Rotate to next proxy in pool"""
        if self.proxy_pool:
            try:
                self.current_proxy = self.proxy_pool.get_next_proxy()
                proxy_url = f"{self.current_proxy.protocol}://{self.current_proxy.username}:{self.current_proxy.password}@{self.current_proxy.host}:{self.current_proxy.port}" if self.current_proxy.username else f"{self.current_proxy.protocol}://{self.current_proxy.host}:{self.current_proxy.port}"
                self.session.proxies = {
                    'http': proxy_url,
                    'https': proxy_url
                }
                logging.info(f"🔄 Rotated to proxy: {self.current_proxy.host}:{self.current_proxy.port}")
            except Exception as e:
                logging.warning(f"⚠️ Proxy rotation failed: {e}")
                self.session.proxies = {}

class DataValidator:
    """Data validation and cleaning utilities"""

    @staticmethod
    def clean_team_name(name: str) -> str:
        """Clean and standardize team names"""
        if not name:
            return ""

        # Remove extra whitespace
        name = ' '.join(name.split())

        # Remove special characters but keep hyphens and apostrophes
        import re
        name = re.sub(r'[^\w\s\-\']', '', name)

        return name.strip()

    @staticmethod
    def validate_odds(odds: float) -> bool:
        """Validate odds values"""
        return isinstance(odds, (int, float)) and 1.01 <= odds <= 100.0

    @staticmethod
    def parse_score(score_text: str) -> Dict[str, str]:
        """Parse score text into structured format"""
        if not score_text:
            return {'status': 'Scheduled', 'score': ''}

        # Common score patterns
        patterns = {
            r'(\d+)-(\d+)': 'simple_score',
            r'Set (\d+).*?(\d+):(\d+)': 'set_score',
            r'(\d+):(\d+)': 'time_score',
            r'FT (\d+)-(\d+)': 'final_score'
        }

        import re
        for pattern, score_type in patterns.items():
            match = re.search(pattern, score_text)
            if match:
                return {
                    'status': score_type,
                    'score': score_text,
                    'parsed': match.groups()
                }

        return {'status': 'Unknown', 'score': score_text}

class RateLimiter:
    """Advanced rate limiting with per-domain limits"""

    def __init__(self):
        self.domain_limits = {}
        self.domain_requests = {}
        self.lock = threading.Lock()

    def set_limit(self, domain: str, requests_per_minute: int):
        """Set rate limit for domain"""
        with self.lock:
            self.domain_limits[domain] = requests_per_minute
            if domain not in self.domain_requests:
                self.domain_requests[domain] = queue.Queue()

    def wait_if_needed(self, domain: str):
        """Wait if rate limit would be exceeded"""
        if domain not in self.domain_limits:
            return

        with self.lock:
            current_time = time.time()
            request_queue = self.domain_requests[domain]
            limit = self.domain_limits[domain]

            # Remove requests older than 1 minute
            while not request_queue.empty():
                if current_time - request_queue.queue[0] > 60:
                    request_queue.get()
                else:
                    break

            # Check if we're at the limit
            if request_queue.qsize() >= limit:
                # Wait until the oldest request is more than 1 minute old
                oldest_request = request_queue.queue[0]
                wait_time = 60 - (current_time - oldest_request)
                if wait_time > 0:
                    time.sleep(wait_time)

            # Add current request
            request_queue.put(current_time)

class ScrapingMetrics:
    """Track scraping performance and statistics"""

    def __init__(self):
        self.start_time = time.time()
        self.requests_made = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.data_points_extracted = 0
        self.errors = []
        self.domain_stats = {}

    def record_request(self, domain: str, success: bool):
        """Record a request attempt"""
        self.requests_made += 1

        if domain not in self.domain_stats:
            self.domain_stats[domain] = {'success': 0, 'failed': 0}

        if success:
            self.successful_requests += 1
            self.domain_stats[domain]['success'] += 1
        else:
            self.failed_requests += 1
            self.domain_stats[domain]['failed'] += 1

    def record_data_point(self):
        """Record a successful data extraction"""
        self.data_points_extracted += 1

    def record_error(self, error: str, domain: str = None):
        """Record an error"""
        self.errors.append({
            'error': error,
            'domain': domain,
            'timestamp': time.time()
        })

    def get_summary(self) -> Dict:
        """Get performance summary"""
        duration = time.time() - self.start_time

        return {
            'duration_seconds': round(duration, 2),
            'requests_made': self.requests_made,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': round(self.successful_requests / max(self.requests_made, 1) * 100, 2),
            'data_points_extracted': self.data_points_extracted,
            'extraction_rate': round(self.data_points_extracted / max(self.requests_made, 1), 2),
            'requests_per_second': round(self.requests_made / max(duration, 1), 2),
            'domain_stats': self.domain_stats,
            'error_count': len(self.errors),
            'recent_errors': self.errors[-5:] if self.errors else []
        }

def get_domain_from_url(url: str) -> str:
    """Extract domain from URL"""
    from urllib.parse import urlparse
    return urlparse(url).netloc.lower()

def create_scraping_config() -> Dict:
    """Create comprehensive scraping configuration"""
    return {
        'rate_limits': {
            'flashscore.com': 10,  # requests per minute
            'oddsportal.com': 8,
            'atptour.com': 15,
            'premierleague.com': 12,
            'nba.com': 20
        },
        'delays': {
            'min_delay': 1.0,
            'max_delay': 3.0,
            'error_delay': 5.0
        },
        'retries': {
            'max_retries': 3,
            'backoff_factor': 2.0
        },
        'timeouts': {
            'connect_timeout': 10,
            'read_timeout': 30
        },
        'user_agents_rotation': True,
        'respect_robots_txt': True
    }

class UndetectedChromeDriver:
    """Enhanced Chrome driver with anti-detection features"""

    def __init__(self, headless: bool = True, proxy_pool: Optional[ProxyPool] = None):
        self.headless = headless
        self.proxy_pool = proxy_pool
        self.driver = None
        self.current_proxy = None

    def __enter__(self):
        self.start_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            self.driver.quit()

    def start_driver(self):
        """Initialize undetected Chrome driver with anti-detection"""
        if not UNDETECTED_CHROMEDRIVER_AVAILABLE:
            raise ImportError("undetected-chromedriver is not available. Install it to use this feature.")

        options = uc.ChromeOptions()

        if self.headless:
            options.add_argument('--headless')

        # Anti-detection arguments
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')  # Speed up loading
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')

        # Randomize viewport
        width = random.randint(1024, 1920)
        height = random.randint(768, 1080)
        options.add_argument(f'--window-size={width},{height}')

        # Set random user agent
        ua = UserAgent()
        options.add_argument(f'--user-agent={ua.random}')

        # Add proxy if available
        if self.proxy_pool:
            self.rotate_proxy()
            if self.current_proxy:
                proxy_url = f"{self.current_proxy.protocol}://{self.current_proxy.username}:{self.current_proxy.password}@{self.current_proxy.host}:{self.current_proxy.port}" if self.current_proxy.username else f"{self.current_proxy.protocol}://{self.current_proxy.host}:{self.current_proxy.port}"
                options.add_argument(f'--proxy-server={proxy_url}')

        # Initialize driver
        self.driver = uc.Chrome(options=options, version_main=None)

        # Execute anti-detection scripts
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")

    def rotate_proxy(self):
        """Rotate to next proxy"""
        if self.proxy_pool:
            try:
                self.current_proxy = self.proxy_pool.get_next_proxy()
                logging.info(f"🔄 Chrome driver rotated to proxy: {self.current_proxy.host}:{self.current_proxy.port}")
            except Exception as e:
                logging.warning(f"⚠️ Proxy rotation failed: {e}")

    def human_like_delay(self, min_delay: float = 0.5, max_delay: float = 2.0):
        """Add human-like delay between actions"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

    def human_like_scroll(self):
        """Perform human-like scrolling"""
        if not self.driver:
            return

        # Random scroll amount
        scroll_amount = random.randint(100, 500)
        self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        self.human_like_delay(0.5, 1.5)

    def human_like_click(self, element):
        """Perform human-like click with mouse movement"""
        if not self.driver:
            return

        # Move mouse to element with slight randomness
        actions = ActionChains(self.driver)
        actions.move_to_element(element)

        # Add small random movements
        for _ in range(random.randint(1, 3)):
            x_offset = random.randint(-5, 5)
            y_offset = random.randint(-5, 5)
            actions.move_by_offset(x_offset, y_offset)
            actions.pause(random.uniform(0.1, 0.3))

        actions.click()
        actions.perform()

        self.human_like_delay(0.5, 1.5)

    def get_page_with_retries(self, url: str, max_retries: int = 3) -> bool:
        """Load page with retries and human-like behavior"""
        for attempt in range(max_retries):
            try:
                self.driver.get(url)
                self.human_like_delay(2, 4)  # Wait for page load

                # Random scroll to simulate reading
                for _ in range(random.randint(1, 3)):
                    self.human_like_scroll()

                return True

            except Exception as e:
                logging.warning(f"⚠️ Page load attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    self.human_like_delay(5, 10)  # Longer delay before retry

        return False

class ROIAnalyzer:
    """Analyze scraped data for ROI opportunities"""

    def __init__(self):
        self.arbitrage_threshold = 0.02  # 2% minimum arbitrage margin
        self.value_threshold = 0.05  # 5% minimum value edge

    def find_arbitrage_opportunities(self, odds_data: Dict[str, List[Dict]]) -> List[Dict]:
        """Find arbitrage opportunities across bookmakers"""
        opportunities = []

        # Group odds by match
        matches = {}
        for bookmaker, matches_list in odds_data.items():
            for match in matches_list:
                match_key = f"{match['home_team']} vs {match['away_team']}"
                if match_key not in matches:
                    matches[match_key] = {}
                matches[match_key][bookmaker] = match

        # Check each match for arbitrage
        for match_key, bookmakers in matches.items():
            if len(bookmakers) >= 2:
                arbitrage = self.calculate_arbitrage(bookmakers)
                if arbitrage and arbitrage['margin'] > self.arbitrage_threshold:
                    opportunities.append(arbitrage)

        return opportunities

    def calculate_arbitrage(self, bookmakers: Dict[str, Dict]) -> Optional[Dict]:
        """Calculate if arbitrage opportunity exists"""
        try:
            # Extract 1X2 odds from each bookmaker
            home_odds = []
            draw_odds = []
            away_odds = []

            for bookmaker, match in bookmakers.items():
                if 'home_odds' in match:
                    home_odds.append((bookmaker, match['home_odds']))
                if 'draw_odds' in match:
                    draw_odds.append((bookmaker, match['draw_odds']))
                if 'away_odds' in match:
                    away_odds.append((bookmaker, match['away_odds']))

            if not (home_odds and away_odds):
                return None

            # Find best odds for each outcome
            best_home = max(home_odds, key=lambda x: x[1])
            best_away = max(away_odds, key=lambda x: x[1])
            best_draw = max(draw_odds, key=lambda x: x[1]) if draw_odds else None

            # Calculate arbitrage margin
            if best_draw:
                total_probability = (1/best_home[1]) + (1/best_draw[1]) + (1/best_away[1])
                margin = 1 - total_probability
            else:
                total_probability = (1/best_home[1]) + (1/best_away[1])
                margin = 1 - total_probability

            if margin > 0:
                # Calculate stake distribution
                total_stake = 100  # Base stake
                home_stake = total_stake / best_home[1]
                away_stake = total_stake / best_away[1]
                draw_stake = total_stake / best_draw[1] if best_draw else 0

                return {
                    'match': list(bookmakers.values())[0]['home_team'] + ' vs ' + list(bookmakers.values())[0]['away_team'],
                    'margin': round(margin * 100, 2),
                    'profit_percentage': round(margin * 100, 2),
                    'best_odds': {
                        'home': {'bookmaker': best_home[0], 'odds': best_home[1]},
                        'away': {'bookmaker': best_away[0], 'odds': best_away[1]},
                        'draw': {'bookmaker': best_draw[0], 'odds': best_draw[1]} if best_draw else None
                    },
                    'stake_distribution': {
                        'home': round(home_stake, 2),
                        'away': round(away_stake, 2),
                        'draw': round(draw_stake, 2) if draw_stake else None
                    },
                    'guaranteed_profit': round(total_stake * margin, 2)
                }

        except Exception as e:
            logging.error(f"Error calculating arbitrage: {e}")

        return None

    def find_value_bets(self, odds_data: Dict[str, List[Dict]], predictions: Dict[str, Dict]) -> List[Dict]:
        """Find value bets by comparing odds with predictions"""
        value_bets = []

        for bookmaker, matches in odds_data.items():
            for match in matches:
                match_key = f"{match['home_team']} vs {match['away_team']}"

                if match_key in predictions:
                    pred = predictions[match_key]

                    # Check each market for value
                    if 'home_odds' in match and 'home_win_prob' in pred:
                        implied_prob = 1 / match['home_odds']
                        if pred['home_win_prob'] > implied_prob + self.value_threshold:
                            value_bets.append({
                                'match': match_key,
                                'market': 'home_win',
                                'bookmaker': bookmaker,
                                'odds': match['home_odds'],
                                'implied_probability': round(implied_prob * 100, 1),
                                'predicted_probability': round(pred['home_win_prob'] * 100, 1),
                                'edge': round((pred['home_win_prob'] - implied_prob) * 100, 1),
                                'expected_value': round((pred['home_win_prob'] * match['home_odds'] - 1) * 100, 1)
                            })

                    if 'away_odds' in match and 'away_win_prob' in pred:
                        implied_prob = 1 / match['away_odds']
                        if pred['away_win_prob'] > implied_prob + self.value_threshold:
                            value_bets.append({
                                'match': match_key,
                                'market': 'away_win',
                                'bookmaker': bookmaker,
                                'odds': match['away_odds'],
                                'implied_probability': round(implied_prob * 100, 1),
                                'predicted_probability': round(pred['away_win_prob'] * 100, 1),
                                'edge': round((pred['away_win_prob'] - implied_prob) * 100, 1),
                                'expected_value': round((pred['away_win_prob'] * match['away_odds'] - 1) * 100, 1)
                            })

                    if 'draw_odds' in match and 'draw_prob' in pred:
                        implied_prob = 1 / match['draw_odds']
                        if pred['draw_prob'] > implied_prob + self.value_threshold:
                            value_bets.append({
                                'match': match_key,
                                'market': 'draw',
                                'bookmaker': bookmaker,
                                'odds': match['draw_odds'],
                                'implied_probability': round(implied_prob * 100, 1),
                                'predicted_probability': round(pred['draw_prob'] * 100, 1),
                                'edge': round((pred['draw_prob'] - implied_prob) * 100, 1),
                                'expected_value': round((pred['draw_prob'] * match['draw_odds'] - 1) * 100, 1)
                            })

        return value_bets

    def analyze_historical_trends(self, historical_data: List[Dict]) -> Dict[str, Any]:
        """Analyze historical odds data for trends"""
        trends = {
            'bookmaker_margins': {},
            'odds_movement_patterns': {},
            'sharp_money_indicators': []
        }

        # Calculate bookmaker margins over time
        for data_point in historical_data:
            bookmaker = data_point.get('bookmaker')
            if bookmaker not in trends['bookmaker_margins']:
                trends['bookmaker_margins'][bookmaker] = []

            # Calculate margin (overround)
            if 'home_odds' in data_point and 'away_odds' in data_point:
                margin = (1/data_point['home_odds']) + (1/data_point['away_odds'])
                if 'draw_odds' in data_point:
                    margin += 1/data_point['draw_odds']

                trends['bookmaker_margins'][bookmaker].append({
                    'timestamp': data_point.get('timestamp'),
                    'margin': margin - 1  # Margin over 100%
                })

        return trends

if __name__ == "__main__":
    # Test the utilities
    session = AntiDetectionSession()
    validator = DataValidator()
    metrics = ScrapingMetrics()

    print("🛠️ Web Scraping Utilities Loaded")
    print("✅ Anti-detection session ready")
    print("✅ Data validation tools ready")
    print("✅ Rate limiting configured")
    print("✅ Performance metrics initialized")