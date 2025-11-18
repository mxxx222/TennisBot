#!/usr/bin/env python3
"""
🎯 HIGHEST ROI SPORTS BETTING SYSTEM - COMPLETE SETUP
======================================================

The ultimate highest ROI setup for all sports using our own data sources
and advanced analytics. No paid APIs needed - everything scraped and analyzed
in-house for maximum profitability.

Features:
- Multi-sport data collection (Tennis, Football, Basketball, Ice Hockey)
- Comprehensive statistics from 100+ sources
- Advanced ROI analysis with ML models
- Kelly Criterion optimization
- Risk management and portfolio optimization
- REST API for data access
- Real-time opportunity detection
- Arbitrage and value bet identification

Author: TennisBot Advanced Analytics
Version: 3.0.0
"""

import asyncio
import json
import time
import logging
import argparse
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

# Import our complete system
from src.unified_sports_scraper import UnifiedSportsScraper, scrape_all_sports_comprehensive
from src.comprehensive_stats_collector import ComprehensiveStatsCollector, collect_all_sports_statistics
from src.sports_roi_api import create_sports_roi_api, SportsROIAPI

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('highest_roi_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HighestROISystem:
    """
    Complete highest ROI system orchestrator
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.setup_logging()

        # Initialize system components
        self.scraper = UnifiedSportsScraper(config)
        self.stats_collector = ComprehensiveStatsCollector(config)
        self.api = None

        # System state
        self.is_running = False
        self.last_analysis = None
        self.performance_stats = {
            'total_analyses': 0,
            'opportunities_found': 0,
            'successful_predictions': 0,
            'total_roi': 0.0
        }

        logger.info("🎯 Highest ROI System initialized")

    def setup_logging(self):
        """Setup comprehensive logging"""
        # Additional setup if needed
        pass

    async def start_system(self):
        """Start the complete highest ROI system"""
        logger.info("🚀 Starting Highest ROI Sports Betting System...")

        self.is_running = True

        try:
            # Initial data collection
            await self._perform_initial_data_collection()

            # Start API server if configured
            if self.config.get('start_api', True):
                await self._start_api_server()

            # Start continuous monitoring
            if self.config.get('continuous_mode', False):
                await self._start_continuous_monitoring()
            else:
                # Single analysis run
                await self._perform_analysis_cycle()

        except KeyboardInterrupt:
            logger.info("🛑 System shutdown requested")
        except Exception as e:
            logger.error(f"❌ System error: {e}")
            raise
        finally:
            self.is_running = False
            await self._shutdown_system()

    async def _perform_initial_data_collection(self):
        """Perform initial comprehensive data collection"""
        logger.info("📊 Performing initial data collection...")

        start_time = time.time()

        # Collect comprehensive data for all sports
        async with self.scraper:
            match_data = await self.scraper.scrape_all_sports_comprehensive()

        async with self.stats_collector:
            stats_data = await self.stats_collector.collect_all_sports_statistics()

        collection_time = time.time() - start_time

        # Log collection statistics
        total_matches = sum(len(matches) for matches in match_data.values())
        total_stats_points = sum(self.stats_collector._count_stats_points(stats)
                               for stats in stats_data.values() if stats)

        logger.info(f"✅ Initial data collection completed in {collection_time:.2f}s")
        logger.info(f"📊 Collected {total_matches} matches across {len(match_data)} sports")
        logger.info(f"📈 Collected {total_stats_points} statistics data points")

        # Export initial data
        self._export_system_data(match_data, stats_data, "initial_collection")

    async def _start_api_server(self):
        """Start the REST API server"""
        logger.info("🌐 Starting REST API server...")

        self.api = create_sports_roi_api(self.config)

        # Run API in background
        import threading
        api_thread = threading.Thread(
            target=self.api.run,
            kwargs={'host': self.config.get('api_host', '0.0.0.0'),
                   'port': self.config.get('api_port', 8000)},
            daemon=True
        )
        api_thread.start()

        logger.info(f"✅ API server started on port {self.config.get('api_port', 8000)}")

    async def _start_continuous_monitoring(self):
        """Start continuous monitoring and analysis"""
        logger.info("🔄 Starting continuous monitoring mode...")

        analysis_interval = self.config.get('analysis_interval_minutes', 30)
        interval_seconds = analysis_interval * 60

        logger.info(f"📊 Analysis cycle every {analysis_interval} minutes")

        while self.is_running:
            try:
                await self._perform_analysis_cycle()
                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"❌ Error in analysis cycle: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def _perform_analysis_cycle(self):
        """Perform a complete analysis cycle"""
        logger.info("🔍 Starting analysis cycle...")

        cycle_start = time.time()

        try:
            # Collect latest data
            async with self.scraper:
                match_data = await self.scraper.scrape_all_sports_comprehensive()

            async with self.stats_collector:
                stats_data = await self.stats_collector.collect_all_sports_statistics()

            # Perform ROI analysis
            from src.highest_roi_analyzer import analyze_highest_roi
            analysis_result = await analyze_highest_roi(match_data, stats_data, self.config)

            # Sync to Notion if configured
            if self.config.get('notion_sync_enabled', False):
                await self._sync_to_notion(match_data, stats_data, analysis_result)

            # Update performance stats
            self.performance_stats['total_analyses'] += 1
            self.performance_stats['opportunities_found'] += analysis_result.total_opportunities
            self.last_analysis = analysis_result

            # Log results
            cycle_time = time.time() - cycle_start
            logger.info(f"✅ Analysis cycle completed in {cycle_time:.2f}s")
            logger.info(f"🎯 Found {analysis_result.total_opportunities} ROI opportunities")
            logger.info(f"💰 Expected portfolio return: {analysis_result.expected_portfolio_return:.2f}%")

            # Export analysis results
            self._export_analysis_results(analysis_result)

            # Display top opportunities
            self._display_top_opportunities(analysis_result)

        except Exception as e:
            logger.error(f"❌ Analysis cycle failed: {e}")
            cycle_time = time.time() - cycle_start
            logger.info(f"⏱️ Cycle took {cycle_time:.2f}s despite error")

    def _export_system_data(self, match_data: Dict, stats_data: Dict, prefix: str):
        """Export system data for analysis"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # Export match data
            matches_filename = f"data/{prefix}_matches_{timestamp}.json"
            Path("data").mkdir(exist_ok=True)

            matches_export = {}
            for sport, matches in match_data.items():
                matches_export[sport] = [self._match_to_export_dict(match) for match in matches]

            with open(matches_filename, 'w', encoding='utf-8') as f:
                json.dump(matches_export, f, indent=2, ensure_ascii=False, default=str)

            # Export stats data
            stats_filename = f"data/{prefix}_stats_{timestamp}.json"
            stats_export = {}
            for sport, stats in stats_data.items():
                if stats:
                    stats_export[sport] = self._stats_to_export_dict(stats)

            with open(stats_filename, 'w', encoding='utf-8') as f:
                json.dump(stats_export, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"💾 System data exported to {matches_filename} and {stats_filename}")

        except Exception as e:
            logger.warning(f"⚠️ Failed to export system data: {e}")

    def _export_analysis_results(self, analysis_result):
        """Export analysis results"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"data/roi_analysis_{timestamp}.json"

            Path("data").mkdir(exist_ok=True)

            # Convert to exportable format
            export_data = {
                'analysis_id': analysis_result.analysis_id,
                'timestamp': analysis_result.timestamp,
                'summary': {
                    'total_opportunities': analysis_result.total_opportunities,
                    'high_confidence_opportunities': analysis_result.high_confidence_opportunities,
                    'arbitrage_opportunities': analysis_result.arbitrage_opportunities,
                    'value_bets': analysis_result.value_bets,
                    'expected_portfolio_return': analysis_result.expected_portfolio_return
                },
                'risk_assessment': analysis_result.risk_assessment,
                'performance_metrics': analysis_result.performance_metrics,
                'opportunities': [self._opportunity_to_export_dict(opp) for opp in analysis_result.opportunities]
            }

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"💾 Analysis results exported to {filename}")

        except Exception as e:
            logger.warning(f"⚠️ Failed to export analysis results: {e}")

    async def _sync_to_notion(self, match_data: Dict, stats_data: Dict, analysis_result):
        """Sync analysis results to Notion"""
        try:
            from src.notion_football_sync import NotionFootballSync
            
            notion_sync = NotionFootballSync()
            
            if not notion_sync.is_configured():
                logger.warning("⚠️ Notion not configured, skipping sync")
                return
            
            logger.info("📤 Syncing to Notion...")
            synced_count = 0
            
            # Sync football matches and analysis
            if 'football' in match_data:
                for match in match_data['football'][:10]:  # Limit to top 10
                    # Sync match
                    match_notion_data = {
                        'home_team': match.get('home_team', 'Unknown'),
                        'away_team': match.get('away_team', 'Unknown'),
                        'league': match.get('league', 'Unknown'),
                        'date_time': match.get('start_time', datetime.now().isoformat()),
                        'status': 'Scheduled',
                        'home_xg': match.get('home_xg', 0),
                        'away_xg': match.get('away_xg', 0)
                    }
                    
                    match_id = notion_sync.sync_match(match_notion_data)
                    
                    if match_id:
                        # Find corresponding analysis
                        for opp in analysis_result.opportunities:
                            if opp.sport == 'football' and opp.match_id == match.get('match_id'):
                                # Sync analysis
                                analysis_notion_data = {
                                    'match_id': match_id,
                                    'h2h_win_pct': opp.get('h2h_win_pct', 50),
                                    'form_edge_pct': opp.get('form_edge_pct', 0),
                                    'injury_impact': 0,
                                    'own_probability_pct': opp.get('probability', 50),
                                    'market_probability_pct': (1 / opp.odds) * 100 if opp.odds > 0 else 50,
                                    'best_bet_type': opp.market,
                                    'edge_pct': opp.edge_percentage
                                }
                                
                                notion_sync.sync_analysis(analysis_notion_data)
                                synced_count += 1
                                break
            
            logger.info(f"✅ Synced {synced_count} items to Notion")
            
        except Exception as e:
            logger.warning(f"⚠️ Notion sync failed: {e}")

    def _display_top_opportunities(self, analysis_result, top_n: int = 5):
        """Display top ROI opportunities"""
        if not analysis_result.opportunities:
            logger.info("📊 No opportunities found in this analysis cycle")
            return

        logger.info("🎯 TOP ROI OPPORTUNITIES:")
        logger.info("=" * 50)

        for i, opp in enumerate(analysis_result.opportunities[:top_n], 1):
            logger.info(f"{i}. {opp.sport.upper()}: {opp.match}")
            logger.info(f"   Market: {opp.market} | Selection: {opp.selection}")
            logger.info(f"   Odds: {opp.odds:.2f} | Edge: {opp.edge_percentage:.1f}%")
            logger.info(f"   Expected ROI: {opp.expected_roi:.1f}% | Confidence: {opp.confidence_score:.1f}")
            logger.info(f"   Risk Level: {opp.risk_level} | Stake: {opp.stake_percentage:.1f}%")
            logger.info("")

    def _match_to_export_dict(self, match) -> Dict:
        """Convert match to export dictionary"""
        return {
            'match_id': match.match_id,
            'sport': match.sport,
            'league': match.league,
            'home_team': match.home_team,
            'away_team': match.away_team,
            'start_time': match.start_time,
            'status': match.status,
            'confidence_score': getattr(match, 'confidence_score', 0.0),
            'data_sources': getattr(match, 'data_sources', [])
        }

    def _stats_to_export_dict(self, stats) -> Dict:
        """Convert stats to export dictionary"""
        return {
            'sport': getattr(stats, 'sport', 'unknown'),
            'last_updated': getattr(stats, 'last_updated', datetime.now().isoformat()),
            'data_points': self.stats_collector._count_stats_points(stats) if hasattr(self, 'stats_collector') else 0
        }

    def _opportunity_to_export_dict(self, opp) -> Dict:
        """Convert opportunity to export dictionary"""
        return {
            'opportunity_id': opp.opportunity_id,
            'sport': opp.sport,
            'match': opp.match,
            'market': opp.market,
            'selection': opp.selection,
            'odds': opp.odds,
            'expected_roi': opp.expected_roi,
            'confidence_score': opp.confidence_score,
            'risk_level': opp.risk_level,
            'stake_percentage': opp.stake_percentage
        }

    async def _shutdown_system(self):
        """Shutdown the system gracefully"""
        logger.info("🛑 Shutting down Highest ROI System...")

        # Save final performance stats
        self._save_performance_stats()

        logger.info("✅ System shutdown complete")

    def _save_performance_stats(self):
        """Save performance statistics"""
        try:
            stats_file = "data/system_performance.json"
            Path("data").mkdir(exist_ok=True)

            performance_data = {
                'timestamp': datetime.now().isoformat(),
                'total_runtime_hours': (datetime.now() - datetime.fromisoformat(self.performance_stats.get('start_time', datetime.now().isoformat()))).total_seconds() / 3600,
                'performance_stats': self.performance_stats
            }

            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(performance_data, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"💾 Performance stats saved to {stats_file}")

        except Exception as e:
            logger.warning(f"⚠️ Failed to save performance stats: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'is_running': self.is_running,
            'last_analysis': self.last_analysis.timestamp if self.last_analysis else None,
            'performance_stats': self.performance_stats,
            'config': {
                'continuous_mode': self.config.get('continuous_mode', False),
                'analysis_interval': self.config.get('analysis_interval_minutes', 30),
                'api_enabled': self.config.get('start_api', True)
            }
        }

def create_default_config() -> Dict[str, Any]:
    """Create default system configuration"""
    return {
        # Scraping configuration
        'rate_limits': {
            'flashscore.com': 8,
            'sofascore.com': 8,
            'oddsportal.com': 6,
            'atptour.com': 12,
            'premierleague.com': 10,
            'nba.com': 15,
            'nhl.com': 15
        },

        # Analysis configuration
        'min_edge_threshold': 0.05,  # 5% minimum edge
        'min_confidence_threshold': 0.65,  # 65% minimum confidence
        'max_risk_per_bet': 0.05,  # 5% max stake per bet
        'kelly_fraction': 0.25,  # 25% Kelly Criterion

        # System configuration
        'continuous_mode': False,
        'analysis_interval_minutes': 30,
        'start_api': True,
        'api_host': '0.0.0.0',
        'api_port': 8000,
        'cache_minutes': 15,

        # Risk management
        'max_portfolio_risk': 0.20,  # 20% max total risk
        'max_correlation': 0.7,
        'max_sport_concentration': 0.6
    }

async def main():
    """Main entry point for the Highest ROI System"""
    parser = argparse.ArgumentParser(description='Highest ROI Sports Betting System')
    parser.add_argument('--continuous', action='store_true',
                       help='Run in continuous monitoring mode')
    parser.add_argument('--no-api', action='store_true',
                       help='Disable API server')
    parser.add_argument('--interval', type=int, default=30,
                       help='Analysis interval in minutes (default: 30)')
    parser.add_argument('--config', type=str,
                       help='Path to custom configuration file')

    args = parser.parse_args()

    print("🎯 HIGHEST ROI SPORTS BETTING SYSTEM")
    print("=" * 50)
    print("🔥 Your own data provider - No paid APIs needed!")
    print("🎾 Tennis | ⚽ Football | 🏀 Basketball | 🏒 Ice Hockey")
    print("💰 Advanced ROI Analysis | 🤖 ML Models | 📊 Real-time Data")
    print()

    # Load configuration
    config = create_default_config()

    if args.config and Path(args.config).exists():
        try:
            with open(args.config, 'r') as f:
                custom_config = json.load(f)
            config.update(custom_config)
            print(f"✅ Loaded custom config from {args.config}")
        except Exception as e:
            print(f"⚠️ Failed to load config: {e}")

    # Override with command line args
    config['continuous_mode'] = args.continuous
    config['start_api'] = not args.no_api
    config['analysis_interval_minutes'] = args.interval

    # Display configuration
    print("⚙️ SYSTEM CONFIGURATION:"    print(f"  Continuous Mode: {config['continuous_mode']}")
    print(f"  API Server: {config['start_api']}")
    print(f"  Analysis Interval: {config['analysis_interval_minutes']} minutes")
    print(f"  Min Edge Threshold: {config['min_edge_threshold']:.1%}")
    print(f"  Max Risk per Bet: {config['max_risk_per_bet']:.1%}")
    print()

    # Create and start system
    system = HighestROISystem(config)

    # Record start time
    config['start_time'] = datetime.now().isoformat()

    try:
        await system.start_system()
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
    except Exception as e:
        print(f"\n❌ System error: {e}")
        raise
    finally:
        # Display final stats
        status = system.get_system_status()
        print("\n📊 FINAL SYSTEM STATISTICS:")
        print(f"  Total Analyses: {status['performance_stats']['total_analyses']}")
        print(f"  Opportunities Found: {status['performance_stats']['opportunities_found']}")
        print("✅ System shutdown complete")

if __name__ == "__main__":
    # Run the system
    asyncio.run(main())