#!/usr/bin/env python3
"""
🎯 ENHANCED SPORTS SCRAPER WITH ANTI-DETECTION
==============================================

Advanced web scraping system with comprehensive anti-detection measures,
proxy rotation, and ROI analysis capabilities.

Features:
- Multi-source data aggregation
- Anti-detection with proxy rotation and headless browsers
- Real-time odds monitoring
- Arbitrage and value bet detection
- Compliance and ethical scraping

Author: TennisBot Advanced Analytics
Version: 3.0.0
"""

import asyncio
import aiohttp
import json
import time
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import random
import hashlib

from scraping_utils import (
    AntiDetectionSession, ProxyPool, ProxyConfig,
    UndetectedChromeDriver, ROIAnalyzer, DataValidator,
    RateLimiter, ScrapingMetrics
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScrapedMatch:
    """Enhanced match data structure"""
    match_id: str
    sport: str
    league: str
    home_team: str
    away_team: str
    date: str
    time: str
    venue: Optional[str] = None
    status: str = "scheduled"

    # Odds data
    odds: Dict[str, Dict[str, float]] = None  # {'bookmaker': {'home': 1.85, 'away': 2.10, 'draw': 3.20}}
    best_odds: Dict[str, Dict[str, Any]] = None  # {'home': {'odds': 1.95, 'bookmaker': 'Bet365'}}

    # Statistics
    home_stats: Dict[str, Any] = None
    away_stats: Dict[str, Any] = None
    head_to_head: List[Dict] = None

    # Live data
    score: Optional[str] = None
    live_stats: Dict[str, Any] = None

    # Metadata
    last_updated: str = ""
    data_sources: List[str] = None
    confidence_score: float = 0.0

    def __post_init__(self):
        if self.odds is None:
            self.odds = {}
        if self.best_odds is None:
            self.best_odds = {}
        if self.data_sources is None:
            self.data_sources = []
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()

class EnhancedSportsScraper:
    """Enhanced sports scraper with anti-detection and ROI analysis"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = None
        self.proxy_pool = None
        self.rate_limiter = RateLimiter()
        self.metrics = ScrapingMetrics()
        self.roi_analyzer = ROIAnalyzer()
        self.validator = DataValidator()

        # Data sources configuration
        self.data_sources = {
            'tennis': {
                'atptour.com': {'type': 'html', 'priority': 1},
                'flashscore.com': {'type': 'selenium', 'priority': 2},
                'oddsportal.com': {'type': 'html', 'priority': 3},
                'betfury.io': {'type': 'api', 'priority': 4}
            },
            'football': {
                'premierleague.com': {'type': 'html', 'priority': 1},
                'flashscore.com': {'type': 'selenium', 'priority': 2},
                'oddsportal.com': {'type': 'html', 'priority': 3}
            }
        }

        # Initialize proxy pool if configured
        self._init_proxy_pool()

    def _init_proxy_pool(self):
        """Initialize proxy pool from configuration"""
        proxy_configs = self.config.get('proxies', [])
        if proxy_configs:
            proxies = []
            for proxy_config in proxy_configs:
                proxies.append(ProxyConfig(**proxy_config))
            self.proxy_pool = ProxyPool(proxies=proxies)
            logger.info(f"✅ Initialized proxy pool with {len(proxies)} proxies")

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = AntiDetectionSession(proxy_pool=self.proxy_pool)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        pass

    async def scrape_comprehensive_data(self, sport: str, date_range: Tuple[str, str] = None) -> List[ScrapedMatch]:
        """
        Comprehensive data scraping for a sport

        Args:
            sport: Sport to scrape ('tennis', 'football', etc.)
            date_range: Tuple of (start_date, end_date) in YYYY-MM-DD format

        Returns:
            List of scraped matches with full data
        """
        logger.info(f"🎯 Starting comprehensive {sport} data scraping...")

        if sport not in self.data_sources:
            raise ValueError(f"Unsupported sport: {sport}")

        start_time = time.time()

        # Scrape from all sources for this sport
        all_matches = []
        sources = self.data_sources[sport]

        # Sort sources by priority
        sorted_sources = sorted(sources.items(), key=lambda x: x[1]['priority'])

        for source_name, source_config in sorted_sources:
            try:
                logger.info(f"📊 Scraping from {source_name}...")

                if source_config['type'] == 'html':
                    matches = await self._scrape_html_source(source_name, sport, date_range)
                elif source_config['type'] == 'selenium':
                    matches = await self._scrape_selenium_source(source_name, sport, date_range)
                elif source_config['type'] == 'api':
                    matches = await self._scrape_api_source(source_name, sport, date_range)
                else:
                    continue

                if matches:
                    all_matches.extend(matches)
                    logger.info(f"✅ Got {len(matches)} matches from {source_name}")

            except Exception as e:
                logger.error(f"❌ Error scraping {source_name}: {e}")
                self.metrics.record_error(str(e), source_name)
                continue

        # Merge and deduplicate matches
        merged_matches = self._merge_match_data(all_matches)

        # Validate and clean data
        validated_matches = []
        for match in merged_matches:
            if self._validate_match_data(match):
                validated_matches.append(match)

        # Calculate best odds and ROI opportunities
        for match in validated_matches:
            match.best_odds = self._calculate_best_odds(match.odds)
            match.confidence_score = self._calculate_confidence_score(match)

        duration = time.time() - start_time
        logger.info(f"✅ Scraped {len(validated_matches)} {sport} matches in {duration:.2f}s")

        return validated_matches

    async def _scrape_html_source(self, source: str, sport: str, date_range: Tuple[str, str] = None) -> List[ScrapedMatch]:
        """Scrape data from HTML-based sources"""
        matches = []

        try:
            # Rate limiting
            domain = source.replace('www.', '')
            self.rate_limiter.wait_if_needed(domain)

            # Get URL for the source
            url = self._get_source_url(source, sport, date_range)

            # Make request with anti-detection
            response = self.session.get(url)
            self.metrics.record_request(domain, response.status_code == 200)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                matches = self._parse_html_matches(soup, source, sport)

        except Exception as e:
            logger.error(f"HTML scraping error for {source}: {e}")

        return matches

    async def _scrape_selenium_source(self, source: str, sport: str, date_range: Tuple[str, str] = None) -> List[ScrapedMatch]:
        """Scrape data using Selenium with anti-detection"""
        matches = []

        try:
            with UndetectedChromeDriver(headless=True, proxy_pool=self.proxy_pool) as driver:
                url = self._get_source_url(source, sport, date_range)

                if driver.get_page_with_retries(url):
                    # Parse page content
                    matches = self._parse_selenium_matches(driver, source, sport)

        except Exception as e:
            logger.error(f"Selenium scraping error for {source}: {e}")

        return matches

    async def _scrape_api_source(self, source: str, sport: str, date_range: Tuple[str, str] = None) -> List[ScrapedMatch]:
        """Scrape data from API endpoints"""
        matches = []

        try:
            # This would implement API-specific scraping logic
            # For now, return empty list as API scraping needs specific implementation
            pass

        except Exception as e:
            logger.error(f"API scraping error for {source}: {e}")

        return matches

    def _get_source_url(self, source: str, sport: str, date_range: Tuple[str, str] = None) -> str:
        """Get the appropriate URL for a data source"""
        base_urls = {
            'atptour.com': 'https://www.atptour.com/en/scores/current',
            'flashscore.com': f'https://www.flashscore.com/{sport}/',
            'oddsportal.com': f'https://www.oddsportal.com/{sport}/',
            'premierleague.com': 'https://www.premierleague.com/fixtures',
            'betfury.io': 'https://betfury.io/sports'
        }

        url = base_urls.get(source, f'https://{source}')

        # Add date parameters if provided
        if date_range:
            # Implementation would vary by source
            pass

        return url

    def _parse_html_matches(self, soup, source: str, sport: str) -> List[ScrapedMatch]:
        """Parse matches from HTML content"""
        matches = []

        try:
            # Generic match parsing - would need source-specific implementations
            if source == 'atptour.com' and sport == 'tennis':
                matches = self._parse_atp_matches(soup)
            elif source == 'oddsportal.com':
                matches = self._parse_oddsportal_matches(soup, sport)
            # Add more source-specific parsers

        except Exception as e:
            logger.error(f"Error parsing HTML matches from {source}: {e}")

        return matches

    def _parse_selenium_matches(self, driver, source: str, sport: str) -> List[ScrapedMatch]:
        """Parse matches using Selenium driver"""
        matches = []

        try:
            if source == 'flashscore.com':
                matches = self._parse_flashscore_selenium(driver, sport)
            # Add more selenium parsers

        except Exception as e:
            logger.error(f"Error parsing Selenium matches from {source}: {e}")

        return matches

    def _parse_atp_matches(self, soup) -> List[ScrapedMatch]:
        """Parse ATP Tour matches"""
        matches = []

        # Find match containers
        match_containers = soup.find_all('div', class_=re.compile(r'match|event'))

        for container in match_containers[:20]:  # Limit for performance
            try:
                match = self._extract_atp_match_data(container)
                if match:
                    matches.append(match)
            except Exception as e:
                logger.debug(f"Error parsing ATP match: {e}")
                continue

        return matches

    def _extract_atp_match_data(self, container) -> Optional[ScrapedMatch]:
        """Extract match data from ATP container"""
        try:
            # Extract basic info
            players = container.find_all('span', class_=re.compile(r'player|name'))
            if len(players) < 2:
                return None

            home_team = self.validator.clean_team_name(players[0].get_text(strip=True))
            away_team = self.validator.clean_team_name(players[1].get_text(strip=True))

            # Generate match ID
            match_id = hashlib.md5(f"{home_team}{away_team}{datetime.now().date()}".encode()).hexdigest()[:8]

            # Extract tournament
            tournament_elem = container.find('span', class_=re.compile(r'tournament|league'))
            league = tournament_elem.get_text(strip=True) if tournament_elem else "ATP Tour"

            # Extract date/time
            date_elem = container.find('span', class_=re.compile(r'date|time'))
            date = date_elem.get_text(strip=True) if date_elem else datetime.now().strftime('%Y-%m-%d')
            time = "TBD"  # Would need more specific parsing

            match = ScrapedMatch(
                match_id=match_id,
                sport="tennis",
                league=league,
                home_team=home_team,
                away_team=away_team,
                date=date,
                time=time,
                data_sources=["atptour.com"]
            )

            return match

        except Exception as e:
            logger.debug(f"Error extracting ATP match data: {e}")
            return None

    def _parse_oddsportal_matches(self, soup, sport: str) -> List[ScrapedMatch]:
        """Parse OddsPortal matches"""
        matches = []

        # Find odds rows
        odds_rows = soup.find_all('tr', class_=re.compile(r'odd|event'))

        for row in odds_rows[:15]:  # Limit for performance
            try:
                match = self._extract_oddsportal_match_data(row, sport)
                if match:
                    matches.append(match)
            except Exception as e:
                logger.debug(f"Error parsing OddsPortal match: {e}")
                continue

        return matches

    def _extract_oddsportal_match_data(self, row, sport: str) -> Optional[ScrapedMatch]:
        """Extract match data from OddsPortal row"""
        try:
            # Extract teams
            team_elements = row.find_all('a', class_=re.compile(r'participant|team'))
            if len(team_elements) < 2:
                return None

            home_team = self.validator.clean_team_name(team_elements[0].get_text(strip=True))
            away_team = self.validator.clean_team_name(team_elements[1].get_text(strip=True))

            # Generate match ID
            match_id = hashlib.md5(f"{home_team}{away_team}{datetime.now().date()}".encode()).hexdigest()[:8]

            # Extract odds
            odds_elements = row.find_all('span', class_=re.compile(r'odd|odds'))
            odds_data = {}

            if len(odds_elements) >= 2:
                try:
                    home_odds = float(odds_elements[0].get_text(strip=True))
                    away_odds = float(odds_elements[1].get_text(strip=True))

                    if self.validator.validate_odds(home_odds) and self.validator.validate_odds(away_odds):
                        odds_data['oddsportal.com'] = {
                            'home': home_odds,
                            'away': away_odds
                        }

                        if len(odds_elements) >= 3:
                            draw_odds = float(odds_elements[2].get_text(strip=True))
                            if self.validator.validate_odds(draw_odds):
                                odds_data['oddsportal.com']['draw'] = draw_odds

                except (ValueError, IndexError):
                    pass

            match = ScrapedMatch(
                match_id=match_id,
                sport=sport,
                league="Various",  # Would need more specific parsing
                home_team=home_team,
                away_team=away_team,
                date=datetime.now().strftime('%Y-%m-%d'),
                time="TBD",
                odds=odds_data,
                data_sources=["oddsportal.com"]
            )

            return match

        except Exception as e:
            logger.debug(f"Error extracting OddsPortal match data: {e}")
            return None

    def _parse_flashscore_selenium(self, driver, sport: str) -> List[ScrapedMatch]:
        """Parse Flashscore matches using Selenium"""
        matches = []

        try:
            # Wait for matches to load
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            WebDriverWait(driver.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "event__match"))
            )

            # Find match elements
            match_elements = driver.driver.find_elements(By.CLASS_NAME, "event__match")[:20]

            for element in match_elements:
                try:
                    match = self._extract_flashscore_match_data(element, sport)
                    if match:
                        matches.append(match)
                except Exception as e:
                    logger.debug(f"Error parsing Flashscore match: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error in Flashscore Selenium parsing: {e}")

        return matches

    def _extract_flashscore_match_data(self, element, sport: str) -> Optional[ScrapedMatch]:
        """Extract match data from Flashscore element"""
        try:
            # Extract teams
            team_elements = element.find_elements(By.CLASS_NAME, "event__participant")
            if len(team_elements) < 2:
                return None

            home_team = self.validator.clean_team_name(team_elements[0].text.strip())
            away_team = self.validator.clean_team_name(team_elements[1].text.strip())

            # Generate match ID
            match_id = hashlib.md5(f"{home_team}{away_team}{datetime.now().date()}".encode()).hexdigest()[:8]

            # Extract score if available
            score_elements = element.find_elements(By.CLASS_NAME, "event__score")
            score = score_elements[0].text.strip() if score_elements else None

            match = ScrapedMatch(
                match_id=match_id,
                sport=sport,
                league="Flashscore",
                home_team=home_team,
                away_team=away_team,
                date=datetime.now().strftime('%Y-%m-%d'),
                time="TBD",
                score=score,
                data_sources=["flashscore.com"]
            )

            return match

        except Exception as e:
            logger.debug(f"Error extracting Flashscore match data: {e}")
            return None

    def _merge_match_data(self, matches: List[ScrapedMatch]) -> List[ScrapedMatch]:
        """Merge duplicate matches from different sources"""
        merged = {}
        duplicates_removed = 0

        for match in matches:
            # Create a key for matching similar matches
            key = f"{match.sport}|{match.home_team}|{match.away_team}|{match.date}"

            if key in merged:
                # Merge data from different sources
                existing = merged[key]

                # Merge odds
                if match.odds:
                    existing.odds.update(match.odds)

                # Merge data sources
                existing.data_sources.extend(match.data_sources)
                existing.data_sources = list(set(existing.data_sources))  # Remove duplicates

                # Update last updated
                existing.last_updated = max(existing.last_updated, match.last_updated)

                duplicates_removed += 1
            else:
                merged[key] = match

        logger.info(f"✅ Merged match data: {len(merged)} unique matches ({duplicates_removed} duplicates removed)")
        return list(merged.values())

    def _validate_match_data(self, match: ScrapedMatch) -> bool:
        """Validate match data quality"""
        try:
            # Basic validation
            if not match.home_team or not match.away_team:
                return False

            if len(match.home_team) < 2 or len(match.away_team) < 2:
                return False

            # Validate odds if present
            if match.odds:
                for bookmaker, odds in match.odds.items():
                    for outcome, value in odds.items():
                        if not self.validator.validate_odds(value):
                            logger.debug(f"Invalid odds: {bookmaker} {outcome} {value}")
                            return False

            return True

        except Exception as e:
            logger.debug(f"Error validating match data: {e}")
            return False

    def _calculate_best_odds(self, odds: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, Any]]:
        """Calculate best odds across bookmakers"""
        best_odds = {}

        if not odds:
            return best_odds

        # For each market (home, away, draw)
        markets = set()
        for bookmaker_odds in odds.values():
            markets.update(bookmaker_odds.keys())

        for market in markets:
            market_odds = []
            for bookmaker, bookmaker_odds in odds.items():
                if market in bookmaker_odds:
                    market_odds.append((bookmaker, bookmaker_odds[market]))

            if market_odds:
                best_bookmaker, best_value = max(market_odds, key=lambda x: x[1])
                best_odds[market] = {
                    'odds': best_value,
                    'bookmaker': best_bookmaker
                }

        return best_odds

    def _calculate_confidence_score(self, match: ScrapedMatch) -> float:
        """Calculate confidence score for match data"""
        score = 0.0

        # Base score for having basic data
        if match.home_team and match.away_team:
            score += 0.3

        # Bonus for odds data
        if match.odds:
            score += 0.3
            # Bonus for multiple bookmakers
            if len(match.odds) > 1:
                score += 0.2

        # Bonus for statistics
        if match.home_stats or match.away_stats:
            score += 0.2

        # Bonus for head-to-head data
        if match.head_to_head:
            score += 0.1

        # Bonus for live data
        if match.score or match.live_stats:
            score += 0.1

        return min(score, 1.0)

    async def find_roi_opportunities(self, matches: List[ScrapedMatch]) -> Dict[str, List[Dict]]:
        """Find ROI opportunities in scraped data (Mojo-accelerated batch processing)"""
        logger.info("💰 Analyzing ROI opportunities...")

        # Convert matches to odds format expected by ROI analyzer
        odds_data = {}
        for match in matches:
            if match.odds:
                for bookmaker, bookmaker_odds in match.odds.items():
                    if bookmaker not in odds_data:
                        odds_data[bookmaker] = []

                    match_odds = {
                        'home_team': match.home_team,
                        'away_team': match.away_team,
                        'home_odds': bookmaker_odds.get('home'),
                        'away_odds': bookmaker_odds.get('away'),
                        'draw_odds': bookmaker_odds.get('draw')
                    }
                    odds_data[bookmaker].append(match_odds)

        # Find arbitrage opportunities - uses Mojo-accelerated calculations internally
        arbitrage_opportunities = self.roi_analyzer.find_arbitrage_opportunities(odds_data)

        # For value bets, we would need predictions - placeholder for now
        # But if we have batch ROI calculations, use them here
        value_bets = []
        
        # Try batch ROI calculation if we have predictions
        try:
            from src.mojo_bindings import batch_calculate_roi, should_use_mojo
            if should_use_mojo() and hasattr(self, 'predictions') and self.predictions:
                # Use Mojo batch ROI calculation for value bets
                # This is a placeholder - would need actual predictions
                pass
        except (ImportError, AttributeError):
            pass

        logger.info(f"✅ Found {len(arbitrage_opportunities)} arbitrage opportunities")
        logger.info(f"✅ Found {len(value_bets)} value bets")

        return {
            'arbitrage': arbitrage_opportunities,
            'value_bets': value_bets
        }

    def export_data(self, matches: List[ScrapedMatch], filename: str = None) -> str:
        """Export scraped data to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"scraped_sports_data_{timestamp}.json"

        # Convert to serializable format
        data = {
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'total_matches': len(matches),
                'scraper_version': '3.0.0',
                'sports_covered': list(set(m.sport for m in matches))
            },
            'matches': [asdict(match) for match in matches]
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"💾 Exported {len(matches)} matches to {filename}")
        return filename

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get scraping metrics summary"""
        return self.metrics.get_summary()

# Convenience functions for easy usage
async def scrape_tennis_data(config: Dict[str, Any] = None) -> List[ScrapedMatch]:
    """Convenience function to scrape tennis data"""
    if config is None:
        config = {}

    async with EnhancedSportsScraper(config) as scraper:
        return await scraper.scrape_comprehensive_data('tennis')

async def scrape_football_data(config: Dict[str, Any] = None) -> List[ScrapedMatch]:
    """Convenience function to scrape football data"""
    if config is None:
        config = {}

    async with EnhancedSportsScraper(config) as scraper:
        return await scraper.scrape_comprehensive_data('football')

if __name__ == "__main__":
    async def main():
        """Test the enhanced scraper"""
        print("🎯 ENHANCED SPORTS SCRAPER TEST")
        print("=" * 50)

        # Basic configuration
        config = {
            'proxies': [],  # Add proxy configs here if available
            'rate_limits': {
                'flashscore.com': 10,
                'oddsportal.com': 8,
                'atptour.com': 15
            }
        }

        try:
            # Test tennis scraping
            print("\n🎾 Testing tennis data scraping...")
            tennis_matches = await scrape_tennis_data(config)

            if tennis_matches:
                print(f"✅ Scraped {len(tennis_matches)} tennis matches")

                # Show sample match
                if tennis_matches:
                    match = tennis_matches[0]
                    print(f"\n📊 Sample match: {match.home_team} vs {match.away_team}")
                    print(f"🏆 League: {match.league}")
                    print(f"📈 Best odds: {match.best_odds}")
                    print(f"🎯 Confidence: {match.confidence_score:.2f}")

                # Find ROI opportunities
                async with EnhancedSportsScraper(config) as scraper:
                    roi_opportunities = await scraper.find_roi_opportunities(tennis_matches)

                    print(f"\n💰 Arbitrage opportunities: {len(roi_opportunities['arbitrage'])}")
                    print(f"💎 Value bets: {len(roi_opportunities['value_bets'])}")

                    if roi_opportunities['arbitrage']:
                        arb = roi_opportunities['arbitrage'][0]
                        print(f"🎰 Sample arbitrage: {arb['match']} - {arb['margin']}% margin")

                # Export data
                filename = EnhancedSportsScraper(config).export_data(tennis_matches)
                print(f"\n💾 Data exported to: {filename}")

            else:
                print("❌ No tennis matches scraped")

        except Exception as e:
            print(f"❌ Error during scraping: {e}")
            import traceback
            traceback.print_exc()

    # Run the test
    asyncio.run(main())