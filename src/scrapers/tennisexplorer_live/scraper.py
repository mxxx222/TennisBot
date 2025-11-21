#!/usr/bin/env python3
"""
🎾 TENNISEXPLORER LIVE SCRAPER
==============================

Production-ready scraper for TennisExplorer live matches.
Scrapes live tennis matches and pushes to Notion Tennis Master Database.

Features:
- Selenium for dynamic content
- BeautifulSoup for parsing
- Rate limiting and anti-detection
- Multiple fallback strategies
- Notion integration
- Monitoring and logging
"""

import os
import sys
import time
import logging
import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / 'telegram_secrets.env'
if env_path.exists():
    load_dotenv(env_path)

from bs4 import BeautifulSoup

# Import local modules (handle both module and script execution)
try:
    from .parser import TennisExplorerParser
    from .models import LiveMatch
except ImportError:
    # If running as script, add current directory to path
    sys.path.insert(0, str(Path(__file__).parent))
    from parser import TennisExplorerParser
    from models import LiveMatch

logger = logging.getLogger(__name__)

# Try to import Selenium
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("⚠️ Selenium not available")

# Try to import requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("⚠️ Requests not available")

# Try to import Notion client
try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    logger.warning("⚠️ notion-client not available")


class TennisExplorerLiveScraper:
    """
    TennisExplorer Live Match Scraper
    
    Scrapes live tennis matches from TennisExplorer and writes to Notion.
    """
    
    BASE_URL = "https://www.tennisexplorer.com"
    LIVE_URL = f"{BASE_URL}/live-tennis/"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize TennisExplorer Live Scraper
        
        Args:
            config: Configuration dictionary (optional, loads from config file if not provided)
        """
        # Load config
        if config is None:
            config = self._load_config()
        self.config = config
        
        # Scraper settings
        scraper_config = self.config.get('scraper', {})
        self.request_delay = scraper_config.get('request_delay', 2.0)
        self.use_selenium = scraper_config.get('use_selenium', True) and SELENIUM_AVAILABLE
        self.max_retries = scraper_config.get('max_retries', 3)
        self.timeout = scraper_config.get('timeout', 30)
        
        # Initialize components
        self.parser = TennisExplorerParser()
        self.driver = None
        self.session = None
        self.last_request_time = 0
        
        # Notion integration
        self.notion_client = None
        self.notion_db_id = None
        self._init_notion()
        
        # Initialize browser/session
        if self.use_selenium:
            self._init_selenium()
        elif REQUESTS_AVAILABLE:
            self._init_requests()
        
        logger.info(f"🎾 TennisExplorer Live Scraper initialized (Selenium: {self.use_selenium})")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_path = project_root / 'config' / 'tennisexplorer_config.yaml'
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"⚠️ Could not load config file: {e}")
        return {}
    
    def _init_selenium(self):
        """Initialize Selenium WebDriver with anti-detection"""
        if not SELENIUM_AVAILABLE:
            logger.warning("⚠️ Selenium not available")
            return
        
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            # User agent
            user_agent = self.config.get('scraper', {}).get('user_agent')
            if not user_agent:
                user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            options.add_argument(f'user-agent={user_agent}')
            
            # Anti-detection
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("✅ Selenium WebDriver initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Selenium: {e}")
            self.driver = None
            self.use_selenium = False
    
    def _init_requests(self):
        """Initialize requests session"""
        if not REQUESTS_AVAILABLE:
            return
        
        self.session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        self.session.headers.update(headers)
        logger.info("✅ Requests session initialized")
    
    def _init_notion(self):
        """Initialize Notion client"""
        if not NOTION_AVAILABLE:
            logger.warning("⚠️ Notion client not available")
            return
        
        # Get Notion token
        notion_token = (
            os.getenv('NOTION_API_KEY') or
            os.getenv('NOTION_TOKEN') or
            self.config.get('notion', {}).get('api_key')
        )
        
        if not notion_token:
            logger.warning("⚠️ Notion token not found in environment or config")
            return
        
        try:
            self.notion_client = Client(auth=notion_token)
            
            # Get database ID
            self.notion_db_id = (
                os.getenv('NOTION_TENNISEXPLORER_DB_ID') or
                os.getenv('NOTION_TENNIS_MASTER_DB_ID') or
                self.config.get('notion', {}).get('tennisexplorer_db_id')
            )
            
            if self.notion_db_id:
                logger.info("✅ Notion client initialized")
            else:
                logger.warning("⚠️ Notion database ID not found")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Notion client: {e}")
    
    def _rate_limit(self):
        """Apply rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        self.last_request_time = time.time()
    
    def _fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch page content with rate limiting and error handling
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content as string or None
        """
        self._rate_limit()
        
        for attempt in range(self.max_retries):
            try:
                if self.use_selenium and self.driver:
                    logger.debug(f"🌐 Fetching with Selenium: {url}")
                    self.driver.get(url)
                    
                    # Wait for page to load
                    wait = WebDriverWait(self.driver, self.timeout)
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    
                    # Additional wait for dynamic content
                    time.sleep(3)
                    
                    html = self.driver.page_source
                    logger.debug(f"✅ Page loaded, HTML length: {len(html)}")
                    return html
                    
                elif self.session:
                    logger.debug(f"🌐 Fetching with requests: {url}")
                    response = self.session.get(url, timeout=self.timeout)
                    response.raise_for_status()
                    html = response.text
                    logger.debug(f"✅ Page loaded, HTML length: {len(html)}")
                    return html
                else:
                    logger.error("❌ No method available to fetch page")
                    return None
                    
            except Exception as e:
                logger.warning(f"⚠️ Attempt {attempt + 1}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"❌ Failed to fetch {url} after {self.max_retries} attempts")
                    return None
        
        return None
    
    def scrape_live_matches(self) -> List[LiveMatch]:
        """
        Scrape all live matches from TennisExplorer
        
        Returns:
            List of LiveMatch objects
        """
        logger.info("📊 Scraping live matches from TennisExplorer...")
        
        try:
            # Fetch live matches page
            html = self._fetch_page(self.LIVE_URL)
            
            if not html:
                logger.error("❌ Failed to fetch live matches page")
                return []
            
            # Parse live matches
            matches = self.parser.parse_live_matches(html)
            
            logger.info(f"✅ Found {len(matches)} live matches")
            
            # Enrich matches with additional data (optional, can be slow)
            # for match in matches:
            #     if match.match_url:
            #         self._enrich_match_data(match)
            
            return matches
            
        except Exception as e:
            logger.error(f"❌ Error scraping live matches: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return []
    
    def _enrich_match_data(self, match: LiveMatch):
        """Enrich match with detailed stats from match detail page"""
        if not match.match_url:
            return
        
        try:
            detail_html = self._fetch_page(match.match_url)
            if detail_html:
                stats = self.parser.parse_match_stats(detail_html)
                match.update_stats(stats)
                logger.debug(f"✅ Enriched match {match.match_id} with stats")
        except Exception as e:
            logger.debug(f"⚠️ Could not enrich match {match.match_id}: {e}")
    
    def write_to_notion(self, match: LiveMatch) -> bool:
        """
        Write match to Notion Tennis Master Database
        
        Args:
            match: LiveMatch object
            
        Returns:
            True if successful, False otherwise
        """
        if not self.notion_client or not self.notion_db_id:
            logger.warning("⚠️ Notion client or database ID not available")
            return False
        
        try:
            # Validate match
            validation = match.validate()
            if not validation["is_valid"]:
                logger.warning(f"⚠️ Match {match.match_id} failed validation: {validation['errors']}")
                return False
            
            # Prepare properties for Notion
            properties = {
                "Match ID": {
                    "title": [{"text": {"content": match.match_id}}]
                },
                "Player A Name": {
                    "rich_text": [{"text": {"content": match.player_a}}]
                },
                "Player B Name": {
                    "rich_text": [{"text": {"content": match.player_b}}]
                },
                "Tournament": {
                    "rich_text": [{"text": {"content": match.tournament}}]
                },
                "Surface": {
                    "select": {"name": match.surface}
                },
                "Match Status": {
                    "select": {"name": "Live"}
                },
                "Match Type": {
                    "select": {"name": "Live"}
                },
                "Live Score": {
                    "rich_text": [{"text": {"content": match.score or "N/A"}}]
                },
                "Data Source": {
                    "select": {"name": "TennisExplorer"}
                },
                "Match Date": {
                    "date": {"start": match.start_time.isoformat() if isinstance(match.start_time, datetime) else datetime.now().isoformat()}
                }
            }
            
            # Add optional fields if available
            if match.tournament_tier:
                properties["Tournament Tier"] = {
                    "select": {"name": match.tournament_tier}
                }
            
            if match.live_odds_a and match.live_odds_b:
                properties["Player A Odds"] = {"number": match.live_odds_a}
                properties["Player B Odds"] = {"number": match.live_odds_b}
            
            # Add notes with stats summary
            notes = match.stats_summary()
            if notes:
                properties["Notes"] = {
                    "rich_text": [{"text": {"content": notes}}]
                }
            
            # Create page in Notion
            self.notion_client.pages.create(
                parent={"database_id": self.notion_db_id},
                properties=properties
            )
            
            logger.debug(f"✅ Wrote match {match.match_id} to Notion")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error writing match {match.match_id} to Notion: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False
    
    def run(self):
        """
        Main execution flow
        
        Scrapes live matches and writes to Notion.
        """
        logger.info("🚀 Starting TennisExplorer Live Scraper run...")
        
        matches_found = 0
        matches_written = 0
        errors = 0
        
        try:
            # Scrape live matches
            matches = self.scrape_live_matches()
            matches_found = len(matches)
            
            logger.info(f"📊 Found {matches_found} live matches")
            
            # Write to Notion
            for match in matches:
                try:
                    if self.write_to_notion(match):
                        matches_written += 1
                    else:
                        errors += 1
                except Exception as e:
                    logger.error(f"❌ Error processing match {match.match_id}: {e}")
                    errors += 1
            
            # Summary
            logger.info(f"✅ Scraper completed: {matches_written}/{matches_found} matches written to Notion")
            if errors > 0:
                logger.warning(f"⚠️ {errors} errors encountered")
            
            return {
                "status": "success",
                "matches_found": matches_found,
                "matches_written": matches_written,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"❌ Scraper run failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "status": "failed",
                "error": str(e),
                "matches_found": matches_found,
                "matches_written": matches_written,
                "errors": errors
            }
    
    def __del__(self):
        """Cleanup resources"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass


# Main execution
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(project_root / 'logs' / 'tennisexplorer_scraper.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create logs directory if it doesn't exist
    (project_root / 'logs').mkdir(exist_ok=True)
    
    # Run scraper
    scraper = TennisExplorerLiveScraper()
    result = scraper.run()
    
    # Exit with appropriate code
    sys.exit(0 if result["status"] == "success" else 1)

