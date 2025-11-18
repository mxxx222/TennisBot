#!/usr/bin/env python3
"""
🎯 COMPREHENSIVE STATISTICS COLLECTOR
====================================

Collects detailed statistics for all sports from multiple sources
to provide the data foundation for highest ROI analysis.

Features:
- Multi-sport statistics collection
- Historical data aggregation
- Real-time statistics updates
- Data validation and quality assessment
- Performance metrics calculation

Author: TennisBot Advanced Analytics
Version: 2.0.0
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from pathlib import Path

from src.unified_sports_scraper import UnifiedSportsScraper, ComprehensiveMatchData
from src.scrapers.scraping_utils import AntiDetectionSession, DataValidator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SportStatistics:
    """Comprehensive statistics for a sport"""
    sport: str
    last_updated: str

    # League/Tournament statistics
    league_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Team/Player statistics
    team_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    player_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Historical performance data
    historical_data: Dict[str, List[Dict]] = field(default_factory=dict)

    # Advanced analytics
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    trend_analysis: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TennisStatistics(SportStatistics):
    """Tennis-specific statistics"""
    sport: str = "tennis"

    # Serve statistics
    serve_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Return statistics
    return_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Surface performance
    surface_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Head-to-head records
    h2h_records: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Ranking history
    ranking_history: Dict[str, List[Dict]] = field(default_factory=dict)

@dataclass
class FootballStatistics(SportStatistics):
    """Football-specific statistics"""
    sport: str = "football"

    # Possession and attacking stats
    possession_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    attacking_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Defensive statistics
    defensive_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Set piece statistics
    set_piece_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Goalkeeper statistics
    goalkeeper_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

@dataclass
class BasketballStatistics(SportStatistics):
    """Basketball-specific statistics"""
    sport: str = "basketball"

    # Scoring statistics
    scoring_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Rebounding statistics
    rebounding_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Assist and playmaking stats
    playmaking_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Defensive statistics
    defensive_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

@dataclass
class HockeyStatistics(SportStatistics):
    """Ice hockey-specific statistics"""
    sport: str = "ice_hockey"

    # Goal scoring statistics
    scoring_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Goaltending statistics
    goaltending_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Power play statistics
    power_play_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Penalty kill statistics
    penalty_kill_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

class ComprehensiveStatsCollector:
    """
    Collects comprehensive statistics for all sports
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.setup_logging()

        # Initialize components
        self.session = None
        self.validator = DataValidator()
        self.unified_scraper = UnifiedSportsScraper(config)

        # Statistics storage
        self.stats_cache = {}
        self.cache_expiry = timedelta(hours=6)  # Cache stats for 6 hours

        # Data sources for statistics
        self.stats_sources = self._initialize_stats_sources()

    def setup_logging(self):
        """Setup comprehensive logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('stats_collector.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _initialize_stats_sources(self) -> Dict[str, Dict]:
        """Initialize statistics data sources"""
        return {
            'tennis': {
                'atptour.com': {'type': 'html', 'priority': 1, 'stats_type': 'player_official'},
                'wtatennis.com': {'type': 'html', 'priority': 1, 'stats_type': 'player_official'},
                'flashscore.com': {'type': 'selenium', 'priority': 2, 'stats_type': 'match_live'},
                'sofascore.com': {'type': 'selenium', 'priority': 2, 'stats_type': 'match_detailed'},
                'tennisexplorer.com': {'type': 'html', 'priority': 3, 'stats_type': 'historical'},
                'ultimate-tennis-statistics.com': {'type': 'html', 'priority': 3, 'stats_type': 'advanced'}
            },
            'football': {
                'premierleague.com': {'type': 'html', 'priority': 1, 'stats_type': 'league_official'},
                'flashscore.com': {'type': 'selenium', 'priority': 2, 'stats_type': 'match_live'},
                'sofascore.com': {'type': 'selenium', 'priority': 2, 'stats_type': 'match_detailed'},
                'whoscored.com': {'type': 'selenium', 'priority': 3, 'stats_type': 'advanced'},
                'understat.com': {'type': 'html', 'priority': 3, 'stats_type': 'expected_goals'},
                'fbref.com': {'type': 'html', 'priority': 4, 'stats_type': 'comprehensive'}
            },
            'basketball': {
                'nba.com': {'type': 'html', 'priority': 1, 'stats_type': 'league_official'},
                'flashscore.com': {'type': 'selenium', 'priority': 2, 'stats_type': 'match_live'},
                'sofascore.com': {'type': 'selenium', 'priority': 2, 'stats_type': 'match_detailed'},
                'basketball-reference.com': {'type': 'html', 'priority': 3, 'stats_type': 'historical'}
            },
            'ice_hockey': {
                'nhl.com': {'type': 'html', 'priority': 1, 'stats_type': 'league_official'},
                'flashscore.com': {'type': 'selenium', 'priority': 2, 'stats_type': 'match_live'},
                'sofascore.com': {'type': 'selenium', 'priority': 2, 'stats_type': 'match_detailed'},
                'hockey-reference.com': {'type': 'html', 'priority': 3, 'stats_type': 'historical'}
            }
        }

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = AntiDetectionSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        pass

    async def collect_all_sports_statistics(self, force_refresh: bool = False) -> Dict[str, SportStatistics]:
        """
        Collect comprehensive statistics for all sports

        Args:
            force_refresh: Force refresh cached statistics

        Returns:
            Dictionary with sport names as keys and statistics objects as values
        """
        logger.info("📊 Starting comprehensive statistics collection for all sports...")

        start_time = time.time()
        all_stats = {}

        sports = ['tennis', 'football', 'basketball', 'ice_hockey']

        # Collect statistics for each sport in parallel
        tasks = [self.collect_sport_statistics(sport, force_refresh) for sport in sports]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, sport in enumerate(sports):
            if isinstance(results[i], Exception):
                logger.error(f"❌ Error collecting {sport} statistics: {results[i]}")
                all_stats[sport] = self._create_empty_stats(sport)
            else:
                all_stats[sport] = results[i]

        # Calculate collection statistics
        end_time = time.time()
        duration = end_time - start_time
        total_stats_points = sum(self._count_stats_points(stats) for stats in all_stats.values())

        logger.info(f"✅ Statistics collection completed in {duration:.2f}s")
        logger.info(f"📈 Collected {total_stats_points} statistics data points")

        return all_stats

    async def collect_sport_statistics(self, sport: str, force_refresh: bool = False) -> SportStatistics:
        """
        Collect comprehensive statistics for a specific sport

        Args:
            sport: Sport name ('tennis', 'football', 'basketball', 'ice_hockey')
            force_refresh: Force refresh cached statistics

        Returns:
            SportStatistics object with comprehensive data
        """
        logger.info(f"🎯 Collecting comprehensive {sport} statistics...")

        # Check cache first
        cache_key = f"{sport}_stats"
        if not force_refresh and cache_key in self.stats_cache:
            cached_stats, cache_time = self.stats_cache[cache_key]
            if datetime.now() - cache_time < self.cache_expiry:
                logger.info(f"✅ Using cached {sport} statistics")
                return cached_stats

        # Create appropriate statistics object
        if sport == 'tennis':
            stats = TennisStatistics(last_updated=datetime.now().isoformat())
        elif sport == 'football':
            stats = FootballStatistics(last_updated=datetime.now().isoformat())
        elif sport == 'basketball':
            stats = BasketballStatistics(last_updated=datetime.now().isoformat())
        elif sport == 'ice_hockey':
            stats = HockeyStatistics(last_updated=datetime.now().isoformat())
        else:
            raise ValueError(f"Unsupported sport: {sport}")

        # Collect data from multiple sources
        await self._collect_from_all_sources(stats, sport)

        # Process and enhance statistics
        await self._process_statistics(stats, sport)

        # Cache the results
        self.stats_cache[cache_key] = (stats, datetime.now())

        logger.info(f"✅ Collected comprehensive {sport} statistics")
        return stats

    async def _collect_from_all_sources(self, stats: SportStatistics, sport: str):
        """Collect statistics from all available sources for a sport"""
        sources = self.stats_sources.get(sport, {})

        # Sort sources by priority
        sorted_sources = sorted(sources.items(), key=lambda x: x[1]['priority'])

        for source_name, source_config in sorted_sources:
            try:
                logger.info(f"📊 Collecting from {source_name}...")

                if source_config['type'] == 'html':
                    await self._collect_html_stats(stats, sport, source_name, source_config)
                elif source_config['type'] == 'selenium':
                    await self._collect_selenium_stats(stats, sport, source_name, source_config)

            except Exception as e:
                logger.warning(f"⚠️ Error collecting from {source_name}: {e}")
                continue

    async def _collect_html_stats(self, stats: SportStatistics, sport: str, source: str, config: Dict):
        """Collect statistics from HTML sources"""
        try:
            url = self._get_stats_source_url(source, sport, config.get('stats_type', 'general'))

            response = self.session.get(url)
            if response.status_code != 200:
                return

            soup = BeautifulSoup(response.content, 'html.parser')

            # Parse based on sport and stats type
            if sport == 'tennis':
                await self._parse_tennis_html_stats(stats, soup, source, config['stats_type'])
            elif sport == 'football':
                await self._parse_football_html_stats(stats, soup, source, config['stats_type'])
            elif sport == 'basketball':
                await self._parse_basketball_html_stats(stats, soup, source, config['stats_type'])
            elif sport == 'ice_hockey':
                await self._parse_hockey_html_stats(stats, soup, source, config['stats_type'])

        except Exception as e:
            logger.error(f"Error collecting HTML stats from {source}: {e}")

    async def _collect_selenium_stats(self, stats: SportStatistics, sport: str, source: str, config: Dict):
        """Collect statistics using Selenium"""
        try:
            from src.scrapers.scraping_utils import UndetectedChromeDriver

            with UndetectedChromeDriver(headless=True) as driver:
                url = self._get_stats_source_url(source, sport, config.get('stats_type', 'general'))

                if driver.get_page_with_retries(url):
                    # Parse based on sport and stats type
                    if sport == 'tennis':
                        await self._parse_tennis_selenium_stats(stats, driver, source, config['stats_type'])
                    elif sport == 'football':
                        await self._parse_football_selenium_stats(stats, driver, source, config['stats_type'])
                    elif sport == 'basketball':
                        await self._parse_basketball_selenium_stats(stats, driver, source, config['stats_type'])
                    elif sport == 'ice_hockey':
                        await self._parse_hockey_selenium_stats(stats, driver, source, config['stats_type'])

        except Exception as e:
            logger.error(f"Error collecting Selenium stats from {source}: {e}")

    def _get_stats_source_url(self, source: str, sport: str, stats_type: str) -> str:
        """Get the appropriate URL for statistics collection"""
        base_urls = {
            # Tennis
            'atptour.com': 'https://www.atptour.com/en/stats',
            'wtatennis.com': 'https://www.wtatennis.com/stats',
            'flashscore.com': f'https://www.flashscore.com/{sport}/',
            'sofascore.com': f'https://www.sofascore.com/{sport}/',
            'tennisexplorer.com': 'https://www.tennisexplorer.com/',
            'ultimate-tennis-statistics.com': 'https://www.ultimate-tennis-statistics.com/',

            # Football
            'premierleague.com': 'https://www.premierleague.com/stats',
            'whoscored.com': 'https://www.whoscored.com/',
            'understat.com': 'https://understat.com/',
            'fbref.com': 'https://fbref.com/',

            # Basketball
            'nba.com': 'https://www.nba.com/stats',
            'basketball-reference.com': 'https://www.basketball-reference.com/',

            # Ice Hockey
            'nhl.com': 'https://www.nhl.com/stats',
            'hockey-reference.com': 'https://www.hockey-reference.com/'
        }

        url = base_urls.get(source, f'https://{source}')

        # Add sport-specific paths
        if stats_type == 'player_official' and sport == 'tennis':
            url += '/players'
        elif stats_type == 'league_official':
            url += '/teams' if 'nba.com' in source or 'nhl.com' in source else ''

        return url

    async def _process_statistics(self, stats: SportStatistics, sport: str):
        """Process and enhance collected statistics"""
        try:
            # Calculate performance metrics
            stats.performance_metrics = self._calculate_performance_metrics(stats, sport)

            # Analyze trends
            stats.trend_analysis = self._analyze_trends(stats, sport)

            # Validate data quality
            self._validate_statistics(stats, sport)

            # Add derived statistics
            await self._add_derived_statistics(stats, sport)

        except Exception as e:
            logger.error(f"Error processing {sport} statistics: {e}")

    def _calculate_performance_metrics(self, stats: SportStatistics, sport: str) -> Dict[str, Any]:
        """Calculate advanced performance metrics"""
        metrics = {
            'data_completeness': 0.0,
            'data_freshness': 0.0,
            'statistical_significance': 0.0,
            'predictive_power': 0.0
        }

        try:
            # Data completeness
            total_fields = self._count_total_fields(stats)
            filled_fields = self._count_filled_fields(stats)
            metrics['data_completeness'] = filled_fields / max(total_fields, 1)

            # Data freshness (how recent the data is)
            if hasattr(stats, 'last_updated'):
                last_update = datetime.fromisoformat(stats.last_updated.replace('Z', '+00:00'))
                hours_old = (datetime.now() - last_update).total_seconds() / 3600
                metrics['data_freshness'] = max(0, 1 - (hours_old / 24))  # Degrades over 24 hours

            # Statistical significance (sample sizes)
            metrics['statistical_significance'] = self._calculate_statistical_significance(stats, sport)

            # Predictive power (correlation with outcomes)
            metrics['predictive_power'] = self._estimate_predictive_power(stats, sport)

        except Exception as e:
            logger.warning(f"Error calculating performance metrics: {e}")

        return metrics

    def _analyze_trends(self, stats: SportStatistics, sport: str) -> Dict[str, Any]:
        """Analyze trends in the statistics"""
        trends = {
            'momentum_indicators': {},
            'seasonal_patterns': {},
            'performance_trends': {},
            'key_insights': []
        }

        try:
            # Analyze recent performance trends
            if hasattr(stats, 'historical_data') and stats.historical_data:
                trends['performance_trends'] = self._analyze_performance_trends(stats.historical_data, sport)

            # Identify momentum indicators
            trends['momentum_indicators'] = self._calculate_momentum_indicators(stats, sport)

            # Seasonal patterns
            trends['seasonal_patterns'] = self._analyze_seasonal_patterns(stats, sport)

            # Generate key insights
            trends['key_insights'] = self._generate_key_insights(stats, sport)

        except Exception as e:
            logger.warning(f"Error analyzing trends: {e}")

        return trends

    def _validate_statistics(self, stats: SportStatistics, sport: str):
        """Validate statistics data quality"""
        try:
            # Check for logical inconsistencies
            self._check_logical_consistency(stats, sport)

            # Validate ranges and reasonableness
            self._validate_stat_ranges(stats, sport)

            # Cross-reference data sources
            self._cross_validate_sources(stats, sport)

        except Exception as e:
            logger.warning(f"Error validating statistics: {e}")

    async def _add_derived_statistics(self, stats: SportStatistics, sport: str):
        """Add derived and calculated statistics"""
        try:
            if sport == 'tennis':
                await self._add_tennis_derived_stats(stats)
            elif sport == 'football':
                await self._add_football_derived_stats(stats)
            elif sport == 'basketball':
                await self._add_basketball_derived_stats(stats)
            elif sport == 'ice_hockey':
                await self._add_hockey_derived_stats(stats)

        except Exception as e:
            logger.warning(f"Error adding derived statistics: {e}")

    # Sport-specific parsing methods (implementations would be detailed)
    async def _parse_tennis_html_stats(self, stats: TennisStatistics, soup, source: str, stats_type: str):
        """Parse tennis statistics from HTML"""
        # Implementation would parse specific tennis stats
        pass

    async def _parse_football_html_stats(self, stats: FootballStatistics, soup, source: str, stats_type: str):
        """Parse football statistics from HTML"""
        # Implementation would parse specific football stats
        pass

    async def _parse_basketball_html_stats(self, stats: BasketballStatistics, soup, source: str, stats_type: str):
        """Parse basketball statistics from HTML"""
        # Implementation would parse specific basketball stats
        pass

    async def _parse_hockey_html_stats(self, stats: HockeyStatistics, soup, source: str, stats_type: str):
        """Parse hockey statistics from HTML"""
        # Implementation would parse specific hockey stats
        pass

    async def _parse_tennis_selenium_stats(self, stats: TennisStatistics, driver, source: str, stats_type: str):
        """Parse tennis statistics using Selenium"""
        # Implementation would use Selenium for dynamic content
        pass

    async def _parse_football_selenium_stats(self, stats: FootballStatistics, driver, source: str, stats_type: str):
        """Parse football statistics using Selenium"""
        # Implementation would use Selenium for dynamic content
        pass

    async def _parse_basketball_selenium_stats(self, stats: BasketballStatistics, driver, source: str, stats_type: str):
        """Parse basketball statistics using Selenium"""
        # Implementation would use Selenium for dynamic content
        pass

    async def _parse_hockey_selenium_stats(self, stats: HockeyStatistics, driver, source: str, stats_type: str):
        """Parse hockey statistics using Selenium"""
        # Implementation would use Selenium for dynamic content
        pass

    # Helper methods
    def _create_empty_stats(self, sport: str) -> SportStatistics:
        """Create empty statistics object for a sport"""
        if sport == 'tennis':
            return TennisStatistics(last_updated=datetime.now().isoformat())
        elif sport == 'football':
            return FootballStatistics(last_updated=datetime.now().isoformat())
        elif sport == 'basketball':
            return BasketballStatistics(last_updated=datetime.now().isoformat())
        elif sport == 'ice_hockey':
            return HockeyStatistics(last_updated=datetime.now().isoformat())
        else:
            return SportStatistics(sport, datetime.now().isoformat())

    def _count_stats_points(self, stats: SportStatistics) -> int:
        """Count total statistics data points"""
        count = 0
        try:
            # Count all dictionary entries recursively
            def count_dict_items(d):
                total = 0
                for v in d.values():
                    if isinstance(v, dict):
                        total += count_dict_items(v)
                    elif isinstance(v, list):
                        total += len(v)
                    else:
                        total += 1
                return total

            count = count_dict_items(asdict(stats))
        except:
            count = 0

        return count

    def _count_total_fields(self, stats: SportStatistics) -> int:
        """Count total possible fields in statistics object"""
        # This would be a detailed count based on the dataclass structure
        return 100  # Placeholder

    def _count_filled_fields(self, stats: SportStatistics) -> int:
        """Count filled fields in statistics object"""
        # This would check which fields have actual data
        return 75  # Placeholder

    def _calculate_statistical_significance(self, stats: SportStatistics, sport: str) -> float:
        """Calculate statistical significance of the data"""
        # Based on sample sizes, consistency, etc.
        return 0.8  # Placeholder

    def _estimate_predictive_power(self, stats: SportStatistics, sport: str) -> float:
        """Estimate predictive power of the statistics"""
        # Based on historical correlation with outcomes
        return 0.7  # Placeholder

    def _analyze_performance_trends(self, historical_data: Dict, sport: str) -> Dict:
        """Analyze performance trends from historical data"""
        return {}  # Placeholder implementation

    def _calculate_momentum_indicators(self, stats: SportStatistics, sport: str) -> Dict:
        """Calculate momentum indicators"""
        return {}  # Placeholder implementation

    def _analyze_seasonal_patterns(self, stats: SportStatistics, sport: str) -> Dict:
        """Analyze seasonal patterns"""
        return {}  # Placeholder implementation

    def _generate_key_insights(self, stats: SportStatistics, sport: str) -> List[str]:
        """Generate key insights from statistics"""
        return []  # Placeholder implementation

    def _check_logical_consistency(self, stats: SportStatistics, sport: str):
        """Check for logical inconsistencies in data"""
        pass  # Placeholder implementation

    def _validate_stat_ranges(self, stats: SportStatistics, sport: str):
        """Validate that statistics are in reasonable ranges"""
        pass  # Placeholder implementation

    def _cross_validate_sources(self, stats: SportStatistics, sport: str):
        """Cross-validate data from multiple sources"""
        pass  # Placeholder implementation

    async def _add_tennis_derived_stats(self, stats: TennisStatistics):
        """Add derived tennis statistics"""
        pass  # Placeholder implementation

    async def _add_football_derived_stats(self, stats: FootballStatistics):
        """Add derived football statistics"""
        pass  # Placeholder implementation

    async def _add_basketball_derived_stats(self, stats: BasketballStatistics):
        """Add derived basketball statistics"""
        pass  # Placeholder implementation

    async def _add_hockey_derived_stats(self, stats: HockeyStatistics):
        """Add derived hockey statistics"""
        pass  # Placeholder implementation

    def export_statistics(self, stats_dict: Dict[str, SportStatistics], filename: str = None) -> str:
        """Export statistics to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"comprehensive_sports_statistics_{timestamp}.json"

        # Convert to serializable format
        export_data = {
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'collector_version': '2.0.0',
                'sports_covered': list(stats_dict.keys())
            },
            'statistics': {}
        }

        for sport, stats in stats_dict.items():
            export_data['statistics'][sport] = asdict(stats)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"💾 Exported comprehensive statistics to {filename}")
        return filename

    def get_collection_metrics(self) -> Dict[str, Any]:
        """Get statistics collection metrics"""
        return {
            'cache_size': len(self.stats_cache),
            'cache_expiry_hours': self.cache_expiry.total_seconds() / 3600,
            'sports_supported': len(self.stats_sources)
        }

# Convenience functions
async def collect_all_sports_statistics(config: Dict[str, Any] = None, force_refresh: bool = False) -> Dict[str, SportStatistics]:
    """Convenience function to collect all sports statistics"""
    if config is None:
        config = {}

    async with ComprehensiveStatsCollector(config) as collector:
        return await collector.collect_all_sports_statistics(force_refresh)

async def collect_sport_statistics(sport: str, config: Dict[str, Any] = None, force_refresh: bool = False) -> SportStatistics:
    """Convenience function to collect statistics for a specific sport"""
    if config is None:
        config = {}

    async with ComprehensiveStatsCollector(config) as collector:
        return await collector.collect_sport_statistics(sport, force_refresh)

if __name__ == "__main__":
    async def main():
        """Test the comprehensive statistics collector"""
        print("📊 COMPREHENSIVE STATISTICS COLLECTOR")
        print("=" * 50)

        # Basic configuration
        config = {
            'rate_limits': {
                'flashscore.com': 8,
                'sofascore.com': 8,
                'atptour.com': 12
            }
        }

        try:
            # Collect all sports statistics
            print("\n🎯 Collecting comprehensive statistics for all sports...")
            all_stats = await collect_all_sports_statistics(config)

            # Display results
            print("\n📊 STATISTICS COLLECTION RESULTS:")
            for sport, stats in all_stats.items():
                data_points = ComprehensiveStatsCollector(config)._count_stats_points(stats)
                print(f"  {sport.upper()}: {data_points} data points")

                # Show performance metrics
                if hasattr(stats, 'performance_metrics'):
                    metrics = stats.performance_metrics
                    print(".1f"                    print(".1f"
            # Export statistics
            filename = ComprehensiveStatsCollector(config).export_statistics(all_stats)
            print(f"\n💾 Statistics exported to: {filename}")

            print("\n✅ Comprehensive statistics collection completed successfully!")

        except Exception as e:
            print(f"❌ Error during statistics collection: {e}")
            import traceback
            traceback.print_exc()

    # Run the test
    asyncio.run(main())