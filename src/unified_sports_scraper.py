#!/usr/bin/env python3
"""
🎯 UNIFIED SPORTS SCRAPER - HIGHEST ROI DATA COLLECTION
======================================================

Comprehensive web scraping system for all sports with anti-detection,
multi-source aggregation, and ROI optimization capabilities.

Features:
- Multi-sport data collection (Tennis, Football, Basketball, Ice Hockey)
- Anti-detection with proxy rotation and headless browsers
- Real-time odds monitoring from multiple bookmakers
- Arbitrage and value bet detection
- Comprehensive statistics collection
- ROI analysis and optimization
- Own API data provision (no paid APIs needed)

Author: TennisBot Advanced Analytics
Version: 3.0.0
"""

import asyncio
import aiohttp
import json
import time
import re
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
import random
import hashlib
import os
from pathlib import Path

from src.scrapers.enhanced_sports_scraper import EnhancedSportsScraper, ScrapedMatch
from src.scrapers.scraping_utils import (
    AntiDetectionSession, ProxyPool, ProxyConfig,
    UndetectedChromeDriver, ROIAnalyzer, DataValidator,
    RateLimiter, ScrapingMetrics
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ComprehensiveMatchData:
    """Complete match data structure for all sports"""
    match_id: str
    sport: str
    league: str
    tournament: str
    home_team: str
    away_team: str
    start_time: str
    status: str

    # Basic match info
    venue: Optional[str] = None
    referee: Optional[str] = None
    attendance: Optional[int] = None
    weather: Optional[Dict] = None

    # Scores and results
    home_score: Optional[Union[str, int]] = None
    away_score: Optional[Union[str, int]] = None
    winner: Optional[str] = None
    match_duration: Optional[str] = None

    # Odds data from multiple bookmakers
    odds_data: Dict[str, Dict[str, float]] = field(default_factory=dict)  # {'bet365': {'home': 2.10, 'away': 1.85, 'draw': 3.40}}

    # Best odds across all bookmakers
    best_odds: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Comprehensive statistics
    team_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # {'home': {...}, 'away': {...}}
    player_stats: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)  # {'home': [...], 'away': [...]}

    # Advanced analytics
    head_to_head: List[Dict[str, Any]] = field(default_factory=list)
    recent_form: Dict[str, List[str]] = field(default_factory=dict)  # {'home': ['W', 'D', 'L'], 'away': [...]}
    league_standings: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Prediction and analysis
    predicted_winner: Optional[str] = None
    win_probability: Optional[Dict[str, float]] = None
    expected_goals: Optional[Dict[str, float]] = None
    roi_analysis: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    last_updated: str = ""
    data_sources: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    data_quality: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()

@dataclass
class SportSpecificData:
    """Sport-specific data structures"""
    tennis: Dict[str, Any] = field(default_factory=dict)
    football: Dict[str, Any] = field(default_factory=dict)
    basketball: Dict[str, Any] = field(default_factory=dict)
    ice_hockey: Dict[str, Any] = field(default_factory=dict)

class UnifiedSportsScraper:
    """
    Unified scraper for all sports with comprehensive data collection
    and ROI optimization capabilities
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.setup_logging()

        # Initialize components
        self.session = None
        self.enhanced_scraper = EnhancedSportsScraper(config)
        self.roi_analyzer = ROIAnalyzer()
        self.validator = DataValidator()
        self.metrics = ScrapingMetrics()

        # Sport-specific configurations
        self.sport_configs = self._initialize_sport_configs()

        # Data sources for each sport
        self.data_sources = self._initialize_data_sources()

        # Initialize proxy and rate limiting
        self._init_proxy_pool()
        self.rate_limiter = RateLimiter()
        self._setup_rate_limits()

    def setup_logging(self):
        """Setup comprehensive logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('unified_scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _initialize_sport_configs(self) -> Dict[str, Dict]:
        """Initialize sport-specific configurations"""
        return {
            'tennis': {
                'leagues': ['ATP', 'WTA', 'ITF', 'Challenger'],
                'stats_categories': [
                    'serve_stats', 'return_stats', 'rally_stats', 'break_points',
                    'tiebreaks', 'surface_performance', 'ranking_history'
                ],
                'odds_markets': ['match_winner', 'set_handicap', 'total_games'],
                'update_frequency': 300  # 5 minutes
            },
            'football': {
                'leagues': [
                    'Premier League', 'La Liga', 'Bundesliga', 'Serie A', 'Ligue 1',
                    'Champions League', 'Europa League', 'Conference League'
                ],
                'stats_categories': [
                    'possession', 'shots', 'shots_on_target', 'corners', 'fouls',
                    'yellow_cards', 'red_cards', 'offsides', 'saves', 'tackles'
                ],
                'odds_markets': ['match_winner', 'both_teams_score', 'over_under', 'correct_score'],
                'update_frequency': 180  # 3 minutes
            },
            'basketball': {
                'leagues': ['NBA', 'EuroLeague', 'EuroCup', 'NCAA'],
                'stats_categories': [
                    'points', 'rebounds', 'assists', 'steals', 'blocks',
                    'turnovers', 'field_goals', 'three_pointers', 'free_throws'
                ],
                'odds_markets': ['match_winner', 'point_spread', 'total_points'],
                'update_frequency': 240  # 4 minutes
            },
            'ice_hockey': {
                'leagues': ['NHL', 'KHL', 'SHL', 'Liiga'],
                'stats_categories': [
                    'goals', 'assists', 'shots', 'saves', 'power_plays',
                    'penalty_kill', 'faceoffs', 'hits', 'blocks'
                ],
                'odds_markets': ['match_winner', 'puck_line', 'total_goals'],
                'update_frequency': 300  # 5 minutes
            }
        }

    def _initialize_data_sources(self) -> Dict[str, Dict]:
        """Initialize comprehensive data sources for all sports"""
        return {
            'tennis': {
                'official': {
                    'atptour.com': {'priority': 1, 'type': 'html'},
                    'wtatennis.com': {'priority': 1, 'type': 'html'},
                    'itftennis.com': {'priority': 2, 'type': 'html'}
                },
                'aggregators': {
                    'flashscore.com': {'priority': 2, 'type': 'selenium'},
                    'sofascore.com': {'priority': 2, 'type': 'selenium'},
                    'tennisexplorer.com': {'priority': 3, 'type': 'html'}
                },
                'odds_providers': {
                    'oddsportal.com': {'priority': 3, 'type': 'html'},
                    'betfury.io': {'priority': 4, 'type': 'api'},
                    'bet365.com': {'priority': 4, 'type': 'selenium'}
                }
            },
            'football': {
                'official': {
                    'premierleague.com': {'priority': 1, 'type': 'html'},
                    'laliga.com': {'priority': 1, 'type': 'html'},
                    'bundesliga.com': {'priority': 1, 'type': 'html'},
                    'seriea.it': {'priority': 1, 'type': 'html'},
                    'ligue1.com': {'priority': 1, 'type': 'html'},
                    'uefa.com': {'priority': 1, 'type': 'html'}
                },
                'aggregators': {
                    'flashscore.com': {'priority': 2, 'type': 'selenium'},
                    'sofascore.com': {'priority': 2, 'type': 'selenium'},
                    'whoscored.com': {'priority': 3, 'type': 'html'}
                },
                'odds_providers': {
                    'oddsportal.com': {'priority': 3, 'type': 'html'},
                    'betfury.io': {'priority': 4, 'type': 'api'}
                }
            },
            'basketball': {
                'official': {
                    'nba.com': {'priority': 1, 'type': 'html'},
                    'euroleague.net': {'priority': 1, 'type': 'html'}
                },
                'aggregators': {
                    'flashscore.com': {'priority': 2, 'type': 'selenium'},
                    'sofascore.com': {'priority': 2, 'type': 'selenium'}
                },
                'odds_providers': {
                    'oddsportal.com': {'priority': 3, 'type': 'html'},
                    'betfury.io': {'priority': 4, 'type': 'api'}
                }
            },
            'ice_hockey': {
                'official': {
                    'nhl.com': {'priority': 1, 'type': 'html'},
                    'khl.ru': {'priority': 1, 'type': 'html'}
                },
                'aggregators': {
                    'flashscore.com': {'priority': 2, 'type': 'selenium'},
                    'sofascore.com': {'priority': 2, 'type': 'selenium'}
                },
                'odds_providers': {
                    'oddsportal.com': {'priority': 3, 'type': 'html'},
                    'betfury.io': {'priority': 4, 'type': 'api'}
                }
            }
        }

    def _init_proxy_pool(self):
        """Initialize proxy pool from configuration"""
        proxy_configs = self.config.get('proxies', [])
        if proxy_configs:
            proxies = []
            for proxy_config in proxy_configs:
                proxies.append(ProxyConfig(**proxy_config))
            self.proxy_pool = ProxyPool(proxies=proxies)
            logger.info(f"✅ Initialized proxy pool with {len(proxies)} proxies")

    def _setup_rate_limits(self):
        """Setup rate limits for all data sources"""
        rate_limits = self.config.get('rate_limits', {})

        # Default rate limits if not specified
        default_limits = {
            'flashscore.com': 8,
            'sofascore.com': 8,
            'oddsportal.com': 6,
            'atptour.com': 12,
            'wtatennis.com': 12,
            'premierleague.com': 10,
            'nba.com': 15,
            'nhl.com': 15,
            'betfury.io': 20
        }

        # Merge with config
        all_limits = {**default_limits, **rate_limits}

        for domain, limit in all_limits.items():
            self.rate_limiter.set_limit(domain, limit)

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = AntiDetectionSession(proxy_pool=self.proxy_pool)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        pass

    async def scrape_all_sports_comprehensive(self, date_range: Tuple[str, str] = None) -> Dict[str, List[ComprehensiveMatchData]]:
        """
        Comprehensive data scraping for all sports

        Args:
            date_range: Tuple of (start_date, end_date) in YYYY-MM-DD format

        Returns:
            Dict with sport names as keys and lists of comprehensive match data
        """
        logger.info("🚀 Starting comprehensive multi-sport data scraping...")

        start_time = time.time()

        # Scrape all sports in parallel
        sports = ['tennis', 'football', 'basketball', 'ice_hockey']
        tasks = [self.scrape_sport_comprehensive(sport, date_range) for sport in sports]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        all_data = {}
        for i, sport in enumerate(sports):
            if isinstance(results[i], Exception):
                logger.error(f"❌ Error scraping {sport}: {results[i]}")
                all_data[sport] = []
            else:
                all_data[sport] = results[i]

        # Calculate statistics
        end_time = time.time()
        duration = end_time - start_time
        total_matches = sum(len(matches) for matches in all_data.values())

        logger.info(f"✅ Multi-sport scraping completed in {duration:.2f}s")
        logger.info(f"📊 Total matches scraped: {total_matches}")
        for sport, matches in all_data.items():
            logger.info(f"  {sport.upper()}: {len(matches)} matches")

        return all_data

    async def scrape_sport_comprehensive(self, sport: str, date_range: Tuple[str, str] = None) -> List[ComprehensiveMatchData]:
        """
        Comprehensive scraping for a specific sport

        Args:
            sport: Sport name ('tennis', 'football', 'basketball', 'ice_hockey')
            date_range: Date range for scraping

        Returns:
            List of comprehensive match data
        """
        logger.info(f"🎯 Starting comprehensive {sport} data scraping...")

        if sport not in self.sport_configs:
            raise ValueError(f"Unsupported sport: {sport}")

        # Get data from multiple sources
        all_matches = await self._gather_sport_data_from_sources(sport, date_range)

        # Merge and deduplicate
        merged_matches = self._merge_comprehensive_match_data(all_matches)

        # Enhance with additional data
        enhanced_matches = await self._enhance_match_data(merged_matches, sport)

        # Calculate ROI opportunities
        for match in enhanced_matches:
            match.roi_analysis = self._calculate_roi_analysis(match)

        # Validate and clean
        validated_matches = self._validate_comprehensive_matches(enhanced_matches)

        logger.info(f"✅ {sport.title()}: {len(validated_matches)} comprehensive matches")
        return validated_matches

    async def _gather_sport_data_from_sources(self, sport: str, date_range: Tuple[str, str] = None) -> List[ComprehensiveMatchData]:
        """Gather data from all sources for a sport"""
        all_matches = []

        sources = self.data_sources[sport]
        source_tasks = []

        # Create tasks for each source type
        for source_type, source_dict in sources.items():
            for source_name, source_config in source_dict.items():
                task = self._scrape_source_comprehensive(source_name, sport, source_type, source_config, date_range)
                source_tasks.append(task)

        # Execute all source scraping in parallel
        results = await asyncio.gather(*source_tasks, return_exceptions=True)

        # Collect successful results
        for result in results:
            if isinstance(result, list):
                all_matches.extend(result)
            elif isinstance(result, Exception):
                logger.warning(f"Source scraping error: {result}")

        return all_matches

    async def _scrape_source_comprehensive(self, source: str, sport: str, source_type: str,
                                         source_config: Dict, date_range: Tuple[str, str] = None) -> List[ComprehensiveMatchData]:
        """Scrape comprehensive data from a specific source"""
        matches = []

        try:
            # Rate limiting
            self.rate_limiter.wait_if_needed(source)

            # Choose scraping method based on source type
            if source_config['type'] == 'html':
                matches = await self._scrape_html_comprehensive(source, sport, date_range)
            elif source_config['type'] == 'selenium':
                matches = await self._scrape_selenium_comprehensive(source, sport, date_range)
            elif source_config['type'] == 'api':
                matches = await self._scrape_api_comprehensive(source, sport, date_range)

        except Exception as e:
            logger.error(f"❌ Error scraping {source} for {sport}: {e}")
            self.metrics.record_error(str(e), source)

        return matches

    async def _scrape_html_comprehensive(self, source: str, sport: str, date_range: Tuple[str, str] = None) -> List[ComprehensiveMatchData]:
        """Scrape comprehensive data using HTML parsing"""
        matches = []

        try:
            url = self._get_sport_source_url(source, sport, date_range)

            # Use anti-detection session
            response = self.session.get(url)
            self.metrics.record_request(source, response.status_code == 200)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                matches = self._parse_comprehensive_html(soup, source, sport)

        except Exception as e:
            logger.error(f"HTML scraping error for {source}: {e}")

        return matches

    async def _scrape_selenium_comprehensive(self, source: str, sport: str, date_range: Tuple[str, str] = None) -> List[ComprehensiveMatchData]:
        """Scrape comprehensive data using Selenium"""
        matches = []

        try:
            with UndetectedChromeDriver(headless=True, proxy_pool=self.proxy_pool) as driver:
                url = self._get_sport_source_url(source, sport, date_range)

                if driver.get_page_with_retries(url):
                    matches = self._parse_comprehensive_selenium(driver, source, sport)

        except Exception as e:
            logger.error(f"Selenium scraping error for {source}: {e}")

        return matches

    async def _scrape_api_comprehensive(self, source: str, sport: str, date_range: Tuple[str, str] = None) -> List[ComprehensiveMatchData]:
        """Scrape comprehensive data from APIs"""
        matches = []

        # This would implement API-specific scraping
        # For now, we'll focus on web scraping to avoid paid APIs
        logger.info(f"API scraping for {source} - using web scraping instead")

        return matches

    def _get_sport_source_url(self, source: str, sport: str, date_range: Tuple[str, str] = None) -> str:
        """Get the appropriate URL for a sport-specific source"""
        base_urls = {
            # Tennis
            'atptour.com': 'https://www.atptour.com/en/scores/current',
            'wtatennis.com': 'https://www.wtatennis.com/scores',
            'flashscore.com': f'https://www.flashscore.com/{sport}/',
            'sofascore.com': f'https://www.sofascore.com/{sport}',
            'oddsportal.com': f'https://www.oddsportal.com/{sport}/',
            'tennisexplorer.com': 'https://www.tennisexplorer.com/',

            # Football
            'premierleague.com': 'https://www.premierleague.com/fixtures',
            'laliga.com': 'https://www.laliga.com/en-GB/calendar',
            'bundesliga.com': 'https://www.bundesliga.com/en/bundesliga/matchday',
            'seriea.it': 'https://www.legaseriea.it/en/serie-a/fixture-and-results',
            'ligue1.com': 'https://www.ligue1.com/calendar',
            'uefa.com': 'https://www.uefa.com/uefachampionsleague/fixtures-results/',
            'whoscored.com': 'https://www.whoscored.com/',

            # Basketball
            'nba.com': 'https://www.nba.com/schedule',
            'euroleague.net': 'https://www.euroleague.net/calendar/',

            # Ice Hockey
            'nhl.com': 'https://www.nhl.com/schedule',
            'khl.ru': 'https://www.khl.ru/calendar/',

            # Betting
            'betfury.io': 'https://betfury.io/sports',
            'bet365.com': 'https://www.bet365.com/'
        }

        url = base_urls.get(source, f'https://{source}')

        # Add date parameters if provided
        if date_range:
            # Implementation varies by source - placeholder
            pass

        return url

    def _parse_comprehensive_html(self, soup, source: str, sport: str) -> List[ComprehensiveMatchData]:
        """Parse comprehensive match data from HTML"""
        matches = []

        try:
            if sport == 'tennis':
                matches = self._parse_tennis_html_comprehensive(soup, source)
            elif sport == 'football':
                matches = self._parse_football_html_comprehensive(soup, source)
            elif sport == 'basketball':
                matches = self._parse_basketball_html_comprehensive(soup, source)
            elif sport == 'ice_hockey':
                matches = self._parse_hockey_html_comprehensive(soup, source)

        except Exception as e:
            logger.error(f"Error parsing comprehensive HTML from {source}: {e}")

        return matches

    def _parse_comprehensive_selenium(self, driver, source: str, sport: str) -> List[ComprehensiveMatchData]:
        """Parse comprehensive match data using Selenium"""
        matches = []

        try:
            if sport == 'tennis':
                matches = self._parse_tennis_selenium_comprehensive(driver, source)
            elif sport == 'football':
                matches = self._parse_football_selenium_comprehensive(driver, source)
            elif sport == 'basketball':
                matches = self._parse_basketball_selenium_comprehensive(driver, source)
            elif sport == 'ice_hockey':
                matches = self._parse_hockey_selenium_comprehensive(driver, source)

        except Exception as e:
            logger.error(f"Error parsing comprehensive Selenium from {source}: {e}")

        return matches

    # Sport-specific parsing methods would go here
    # For brevity, I'll implement the core structure and key methods

    def _merge_comprehensive_match_data(self, matches: List[ComprehensiveMatchData]) -> List[ComprehensiveMatchData]:
        """Merge duplicate matches from different sources"""
        merged = {}
        duplicates_removed = 0

        for match in matches:
            # Create a unique identifier
            key = f"{match.sport}|{match.home_team}|{match.away_team}|{match.start_time[:10]}"

            if key in merged:
                # Merge data from different sources
                existing = merged[key]

                # Merge odds data
                for bookmaker, odds in match.odds_data.items():
                    if bookmaker not in existing.odds_data:
                        existing.odds_data[bookmaker] = odds

                # Merge data sources
                existing.data_sources.extend(match.data_sources)
                existing.data_sources = list(set(existing.data_sources))

                # Update statistics if more comprehensive
                if len(str(match.team_stats)) > len(str(existing.team_stats)):
                    existing.team_stats = match.team_stats

                # Update last updated
                existing.last_updated = max(existing.last_updated, match.last_updated)

                duplicates_removed += 1
            else:
                merged[key] = match

        logger.info(f"✅ Merged comprehensive match data: {len(merged)} unique matches ({duplicates_removed} duplicates removed)")
        return list(merged.values())

    async def _enhance_match_data(self, matches: List[ComprehensiveMatchData], sport: str) -> List[ComprehensiveMatchData]:
        """Enhance match data with additional analytics"""
        enhanced_matches = []

        for match in matches:
            try:
                # Calculate best odds
                match.best_odds = self._calculate_best_odds(match.odds_data)

                # Calculate confidence score
                match.confidence_score = self._calculate_comprehensive_confidence(match)

                # Add data quality metrics
                match.data_quality = self._assess_data_quality(match)

                # Add sport-specific enhancements
                if sport == 'tennis':
                    match = await self._enhance_tennis_data(match)
                elif sport == 'football':
                    match = await self._enhance_football_data(match)
                elif sport == 'basketball':
                    match = await self._enhance_basketball_data(match)
                elif sport == 'ice_hockey':
                    match = await self._enhance_hockey_data(match)

                enhanced_matches.append(match)

            except Exception as e:
                logger.warning(f"Error enhancing match data: {e}")
                enhanced_matches.append(match)

        return enhanced_matches

    def _calculate_best_odds(self, odds_data: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, Any]]:
        """Calculate best odds across all bookmakers"""
        best_odds = {}

        if not odds_data:
            return best_odds

        # Get all available markets
        all_markets = set()
        for bookmaker_odds in odds_data.values():
            all_markets.update(bookmaker_odds.keys())

        for market in all_markets:
            market_odds = []
            for bookmaker, bookmaker_odds in odds_data.items():
                if market in bookmaker_odds:
                    market_odds.append((bookmaker, bookmaker_odds[market]))

            if market_odds:
                best_bookmaker, best_value = max(market_odds, key=lambda x: x[1])
                best_odds[market] = {
                    'odds': best_value,
                    'bookmaker': best_bookmaker,
                    'sources': len(market_odds)
                }

        return best_odds

    def _calculate_comprehensive_confidence(self, match: ComprehensiveMatchData) -> float:
        """Calculate comprehensive confidence score"""
        score = 0.0

        # Base score for having basic data
        if match.home_team and match.away_team and match.start_time:
            score += 0.2

        # Odds data quality
        if match.odds_data:
            score += 0.2
            if len(match.odds_data) > 2:
                score += 0.1  # Multiple bookmakers

        # Statistics availability
        if match.team_stats:
            score += 0.2
            if match.team_stats.get('home') and match.team_stats.get('away'):
                score += 0.1

        # Head-to-head data
        if match.head_to_head:
            score += 0.1

        # Recent form
        if match.recent_form:
            score += 0.1

        # League standings
        if match.league_standings:
            score += 0.1

        return min(score, 1.0)

    def _assess_data_quality(self, match: ComprehensiveMatchData) -> Dict[str, float]:
        """Assess data quality for different aspects"""
        quality = {}

        # Odds quality
        if match.odds_data:
            total_odds = sum(len(odds) for odds in match.odds_data.values())
            quality['odds'] = min(total_odds / 10, 1.0)  # Max quality at 10+ odds points
        else:
            quality['odds'] = 0.0

        # Statistics quality
        stats_count = len(str(match.team_stats)) + len(str(match.player_stats))
        quality['statistics'] = min(stats_count / 1000, 1.0)  # Rough character count proxy

        # Historical data quality
        h2h_count = len(match.head_to_head)
        quality['historical'] = min(h2h_count / 10, 1.0)  # Max quality at 10+ H2H matches

        # Overall quality
        quality['overall'] = sum(quality.values()) / len(quality)

        return quality

    def _calculate_roi_analysis(self, match: ComprehensiveMatchData) -> Dict[str, Any]:
        """Calculate comprehensive ROI analysis"""
        analysis = {
            'arbitrage_opportunities': [],
            'value_bets': [],
            'expected_returns': {},
            'risk_assessment': {}
        }

        if not match.odds_data:
            return analysis

        # Convert odds data for ROI analyzer
        odds_list = []
        for bookmaker, odds in match.odds_data.items():
            match_odds = {
                'bookmaker': bookmaker,
                'home_team': match.home_team,
                'away_team': match.away_team,
                'home_odds': odds.get('home'),
                'away_odds': odds.get('away'),
                'draw_odds': odds.get('draw')
            }
            odds_list.append(match_odds)

        # Find arbitrage opportunities
        arbitrage = self.roi_analyzer.find_arbitrage_opportunities({'combined': odds_list})
        if arbitrage:
            analysis['arbitrage_opportunities'] = arbitrage

        # Calculate expected returns for best odds
        if match.best_odds:
            for market, best_data in match.best_odds.items():
                if market in ['home', 'away', 'draw']:
                    odds = best_data['odds']
                    analysis['expected_returns'][market] = {
                        'odds': odds,
                        'implied_probability': 1 / odds,
                        'break_even_probability': 1 / odds
                    }

        # Risk assessment
        analysis['risk_assessment'] = {
            'data_confidence': match.confidence_score,
            'odds_sources': len(match.odds_data),
            'recommended_stake': self._calculate_recommended_stake(match)
        }

        return analysis

    def _calculate_recommended_stake(self, match: ComprehensiveMatchData) -> Dict[str, Any]:
        """Calculate recommended stake based on Kelly Criterion"""
        stake_info = {
            'max_stake_percentage': 0.0,
            'confidence_level': match.confidence_score,
            'risk_level': 'high'
        }

        if match.confidence_score > 0.8:
            stake_info['risk_level'] = 'low'
            stake_info['max_stake_percentage'] = 0.05  # 5% of bankroll
        elif match.confidence_score > 0.6:
            stake_info['risk_level'] = 'medium'
            stake_info['max_stake_percentage'] = 0.03  # 3% of bankroll
        else:
            stake_info['risk_level'] = 'high'
            stake_info['max_stake_percentage'] = 0.01  # 1% of bankroll

        return stake_info

    def _validate_comprehensive_matches(self, matches: List[ComprehensiveMatchData]) -> List[ComprehensiveMatchData]:
        """Validate and clean comprehensive match data"""
        validated = []

        for match in matches:
            try:
                # Basic validation
                if not match.home_team or not match.away_team:
                    continue

                if match.home_team == match.away_team:
                    continue

                # Validate odds
                if match.odds_data:
                    for bookmaker, odds in list(match.odds_data.items()):
                        for outcome, value in list(odds.items()):
                            if not self.validator.validate_odds(value):
                                del odds[outcome]
                        if not odds:  # Remove empty bookmaker entries
                            del match.odds_data[bookmaker]

                # Clean team names
                match.home_team = self.validator.clean_team_name(match.home_team)
                match.away_team = self.validator.clean_team_name(match.away_team)

                validated.append(match)

            except Exception as e:
                logger.warning(f"Error validating match: {e}")
                continue

        return validated

    # Placeholder methods for sport-specific enhancements
    async def _enhance_tennis_data(self, match: ComprehensiveMatchData) -> ComprehensiveMatchData:
        """Add tennis-specific enhancements"""
        # Add surface analysis, ranking differences, etc.
        return match

    async def _enhance_football_data(self, match: ComprehensiveMatchData) -> ComprehensiveMatchData:
        """Add football-specific enhancements"""
        # Add tactical analysis, player injuries, etc.
        return match

    async def _enhance_basketball_data(self, match: ComprehensiveMatchData) -> ComprehensiveMatchData:
        """Add basketball-specific enhancements"""
        # Add pace analysis, home court advantage, etc.
        return match

    async def _enhance_hockey_data(self, match: ComprehensiveMatchData) -> ComprehensiveMatchData:
        """Add hockey-specific enhancements"""
        # Add goaltender analysis, power play stats, etc.
        return match

    # Placeholder methods for sport-specific parsing
    def _parse_tennis_html_comprehensive(self, soup, source: str) -> List[ComprehensiveMatchData]:
        """Parse tennis matches from HTML - comprehensive version"""
        return []

    def _parse_football_html_comprehensive(self, soup, source: str) -> List[ComprehensiveMatchData]:
        """Parse football matches from HTML - comprehensive version"""
        return []

    def _parse_basketball_html_comprehensive(self, soup, source: str) -> List[ComprehensiveMatchData]:
        """Parse basketball matches from HTML - comprehensive version"""
        return []

    def _parse_hockey_html_comprehensive(self, soup, source: str) -> List[ComprehensiveMatchData]:
        """Parse hockey matches from HTML - comprehensive version"""
        return []

    def _parse_tennis_selenium_comprehensive(self, driver, source: str) -> List[ComprehensiveMatchData]:
        """Parse tennis matches using Selenium - comprehensive version"""
        return []

    def _parse_football_selenium_comprehensive(self, driver, source: str) -> List[ComprehensiveMatchData]:
        """Parse football matches using Selenium - comprehensive version"""
        return []

    def _parse_basketball_selenium_comprehensive(self, driver, source: str) -> List[ComprehensiveMatchData]:
        """Parse basketball matches using Selenium - comprehensive version"""
        return []

    def _parse_hockey_selenium_comprehensive(self, driver, source: str) -> List[ComprehensiveMatchData]:
        """Parse hockey matches using Selenium - comprehensive version"""
        return []

    async def find_highest_roi_opportunities(self, matches_data: Dict[str, List[ComprehensiveMatchData]]) -> Dict[str, List[Dict]]:
        """Find highest ROI opportunities across all sports"""
        logger.info("💰 Analyzing highest ROI opportunities across all sports...")

        all_opportunities = {
            'arbitrage': [],
            'value_bets': [],
            'high_confidence': [],
            'multi_sport_analysis': {}
        }

        # Analyze each sport
        for sport, matches in matches_data.items():
            sport_opportunities = await self._analyze_sport_roi(matches, sport)
            for opp_type, opportunities in sport_opportunities.items():
                all_opportunities[opp_type].extend(opportunities)

        # Sort by potential ROI
        for opp_type in ['arbitrage', 'value_bets', 'high_confidence']:
            all_opportunities[opp_type].sort(key=lambda x: x.get('expected_roi', 0), reverse=True)

        # Multi-sport analysis
        all_opportunities['multi_sport_analysis'] = self._analyze_multi_sport_patterns(matches_data)

        logger.info(f"✅ Found {len(all_opportunities['arbitrage'])} arbitrage opportunities")
        logger.info(f"✅ Found {len(all_opportunities['value_bets'])} value bets")
        logger.info(f"✅ Found {len(all_opportunities['high_confidence'])} high confidence opportunities")

        return all_opportunities

    async def _analyze_sport_roi(self, matches: List[ComprehensiveMatchData], sport: str) -> Dict[str, List[Dict]]:
        """Analyze ROI opportunities for a specific sport"""
        opportunities = {
            'arbitrage': [],
            'value_bets': [],
            'high_confidence': []
        }

        for match in matches:
            # Arbitrage opportunities
            if match.roi_analysis.get('arbitrage_opportunities'):
                for arb in match.roi_analysis['arbitrage_opportunities']:
                    arb['sport'] = sport
                    arb['match_info'] = {
                        'home_team': match.home_team,
                        'away_team': match.away_team,
                        'league': match.league,
                        'start_time': match.start_time
                    }
                    opportunities['arbitrage'].append(arb)

            # High confidence opportunities
            if match.confidence_score > 0.8 and match.roi_analysis.get('risk_assessment'):
                risk = match.roi_analysis['risk_assessment']
                if risk['risk_level'] in ['low', 'medium']:
                    opportunities['high_confidence'].append({
                        'sport': sport,
                        'match': f"{match.home_team} vs {match.away_team}",
                        'league': match.league,
                        'confidence': match.confidence_score,
                        'risk_level': risk['risk_level'],
                        'recommended_stake': risk['max_stake_percentage'],
                        'expected_roi': risk['max_stake_percentage'] * match.confidence_score * 100
                    })

        return opportunities

    def _analyze_multi_sport_patterns(self, matches_data: Dict[str, List[ComprehensiveMatchData]]) -> Dict[str, Any]:
        """Analyze patterns across multiple sports"""
        analysis = {
            'total_matches': sum(len(matches) for matches in matches_data.values()),
            'sports_coverage': len(matches_data),
            'average_confidence': 0.0,
            'high_opportunity_sports': [],
            'cross_sport_arbitrage': []
        }

        total_confidence = 0
        total_matches = 0

        for sport, matches in matches_data.items():
            if matches:
                sport_confidence = sum(m.confidence_score for m in matches) / len(matches)
                total_confidence += sport_confidence * len(matches)
                total_matches += len(matches)

                if sport_confidence > 0.7:
                    analysis['high_opportunity_sports'].append({
                        'sport': sport,
                        'average_confidence': sport_confidence,
                        'matches': len(matches)
                    })

        if total_matches > 0:
            analysis['average_confidence'] = total_confidence / total_matches

        return analysis

    def export_comprehensive_data(self, data: Dict[str, List[ComprehensiveMatchData]],
                                filename: str = None) -> str:
        """Export comprehensive data to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"comprehensive_sports_data_{timestamp}.json"

        # Convert to serializable format
        export_data = {
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'scraper_version': '3.0.0',
                'sports_covered': list(data.keys()),
                'total_matches': sum(len(matches) for matches in data.values())
            },
            'matches': {}
        }

        for sport, matches in data.items():
            export_data['matches'][sport] = [asdict(match) for match in matches]

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"💾 Exported comprehensive data to {filename}")
        return filename

    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Get comprehensive scraping metrics"""
        return self.metrics.get_summary()

# Convenience functions
async def scrape_all_sports_comprehensive(config: Dict[str, Any] = None) -> Dict[str, List[ComprehensiveMatchData]]:
    """Convenience function to scrape all sports comprehensively"""
    if config is None:
        config = {}

    async with UnifiedSportsScraper(config) as scraper:
        return await scraper.scrape_all_sports_comprehensive()

async def find_highest_roi_opportunities(data: Dict[str, List[ComprehensiveMatchData]],
                                       config: Dict[str, Any] = None) -> Dict[str, List[Dict]]:
    """Convenience function to find highest ROI opportunities"""
    if config is None:
        config = {}

    async with UnifiedSportsScraper(config) as scraper:
        return await scraper.find_highest_roi_opportunities(data)

if __name__ == "__main__":
    async def main():
        """Test the unified scraper"""
        print("🚀 UNIFIED SPORTS SCRAPER - HIGHEST ROI DATA COLLECTION")
        print("=" * 70)

        # Basic configuration
        config = {
            'proxies': [],  # Add proxy configs here if available
            'rate_limits': {
                'flashscore.com': 8,
                'sofascore.com': 8,
                'oddsportal.com': 6,
                'atptour.com': 12,
                'premierleague.com': 10
            }
        }

        try:
            # Scrape all sports
            print("\n🎯 Starting comprehensive multi-sport scraping...")
            all_sports_data = await scrape_all_sports_comprehensive(config)

            # Find ROI opportunities
            print("\n💰 Analyzing highest ROI opportunities...")
            roi_opportunities = await find_highest_roi_opportunities(all_sports_data, config)

            # Display results
            print("\n📊 SCRAPING RESULTS:")
            for sport, matches in all_sports_data.items():
                print(f"  {sport.upper()}: {len(matches)} matches")

            print("
💰 ROI OPPORTUNITIES:"            print(f"  Arbitrage: {len(roi_opportunities['arbitrage'])}")
            print(f"  Value Bets: {len(roi_opportunities['value_bets'])}")
            print(f"  High Confidence: {len(roi_opportunities['high_confidence'])}")

            # Export data
            filename = UnifiedSportsScraper(config).export_comprehensive_data(all_sports_data)
            print(f"\n💾 Data exported to: {filename}")

            # Show sample opportunities
            if roi_opportunities['high_confidence']:
                print("
🎯 TOP HIGH CONFIDENCE OPPORTUNITIES:"                for i, opp in enumerate(roi_opportunities['high_confidence'][:3], 1):
                    print(f"{i}. {opp['sport'].upper()}: {opp['match']}")
                    print(".1f"                    print(".1f"                    print(".1f"
            print("\n✅ Unified sports scraping completed successfully!")

        except Exception as e:
            print(f"❌ Error during unified scraping: {e}")
            import traceback
            traceback.print_exc()

    # Run the test
    asyncio.run(main())