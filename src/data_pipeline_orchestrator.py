#!/usr/bin/env python3
"""
🔄 DATA PIPELINE ORCHESTRATOR
==============================
Automaattinen datan hakeminen, prosessointi ja synkronointi.

Features:
- 🔄 Automaattinen datan hakeminen useista lähteistä
- 📊 Tilastojen keräys
- 💰 ROI-analyysi
- 💾 Notion-synkronointi
- 📱 Telegram-ilmoitukset
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml

# Import components
try:
    from src.unified_data_fetcher import UnifiedDataFetcher, UnifiedMatchData
    UNIFIED_FETCHER_AVAILABLE = True
except ImportError:
    UNIFIED_FETCHER_AVAILABLE = False
    UnifiedDataFetcher = None
    # Create a simple dataclass if not available
    from dataclasses import dataclass
    from typing import Optional
    from datetime import datetime
    
    @dataclass
    class UnifiedMatchData:
        match_id: str
        sport: str
        league: str
        home_team: str
        away_team: str
        match_time: datetime
        venue: Optional[str] = None
        odds_data: Optional[Dict[str, Any]] = None
        team_stats: Optional[Dict[str, Any]] = None
        player_stats: Optional[Dict[str, Any]] = None
        historical_data: Optional[Dict[str, Any]] = None
        external_factors: Optional[Dict[str, Any]] = None
        sources: List[str] = None
        data_quality: float = 0.0
        fetched_at: Optional[datetime] = None

try:
    from src.notion_data_manager import NotionDataManager
    NOTION_MANAGER_AVAILABLE = True
except ImportError:
    NOTION_MANAGER_AVAILABLE = False
    NotionDataManager = None

try:
    from src.highest_roi_analyzer import HighestROIAnalyzer, ROIAnalysis
    ROI_ANALYZER_AVAILABLE = True
except ImportError:
    ROI_ANALYZER_AVAILABLE = False
    HighestROIAnalyzer = None

try:
    from src.multi_sport_stats_collector import MultiSportStatsCollector
    STATS_COLLECTOR_AVAILABLE = True
except ImportError:
    STATS_COLLECTOR_AVAILABLE = False
    MultiSportStatsCollector = None

logger = logging.getLogger(__name__)


class DataPipelineOrchestrator:
    """
    Automaattinen datan hakeminen ja prosessointi
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize Data Pipeline Orchestrator
        
        Args:
            config_path: Path to configuration file
        """
        logger.info("🔄 Initializing Data Pipeline Orchestrator...")
        
        # Load configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "unified_data_config.yaml"
        
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.data_fetcher = None
        self.notion_manager = None
        self.roi_analyzer = None
        self.stats_collector = None
        
        self._initialize_components()
        
        # Pipeline state
        self.running = False
        self.last_fetch_time = None
        self.last_analysis_time = None
        self.last_sync_time = None
        
        # Statistics
        self.stats = {
            'matches_fetched': 0,
            'matches_analyzed': 0,
            'roi_opportunities_found': 0,
            'matches_synced': 0,
            'errors': 0
        }
        
        logger.info("✅ Data Pipeline Orchestrator initialized")
    
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"❌ Error loading config: {e}")
            return {}
    
    def _initialize_components(self):
        """Initialize all pipeline components"""
        
        # Unified Data Fetcher
        if UNIFIED_FETCHER_AVAILABLE:
            try:
                self.data_fetcher = UnifiedDataFetcher()
                logger.info("✅ Unified Data Fetcher initialized")
            except Exception as e:
                logger.warning(f"⚠️ Unified Data Fetcher initialization failed: {e}")
        
        # Notion Data Manager
        if NOTION_MANAGER_AVAILABLE:
            try:
                self.notion_manager = NotionDataManager()
                logger.info("✅ Notion Data Manager initialized")
            except Exception as e:
                logger.warning(f"⚠️ Notion Data Manager initialization failed: {e}")
        
        # Highest ROI Analyzer
        if ROI_ANALYZER_AVAILABLE:
            try:
                bankroll = self.config.get('roi_analysis', {}).get('bankroll', {}).get('initial', 10000.0)
                self.roi_analyzer = HighestROIAnalyzer(bankroll=bankroll)
                logger.info("✅ Highest ROI Analyzer initialized")
            except Exception as e:
                logger.warning(f"⚠️ Highest ROI Analyzer initialization failed: {e}")
        
        # Multi-Sport Statistics Collector
        if STATS_COLLECTOR_AVAILABLE:
            try:
                self.stats_collector = MultiSportStatsCollector()
                logger.info("✅ Multi-Sport Statistics Collector initialized")
            except Exception as e:
                logger.warning(f"⚠️ Multi-Sport Statistics Collector initialization failed: {e}")
    
    async def start(self):
        """Käynnistä automaattinen prosessointi"""
        logger.info("🚀 Starting Data Pipeline Orchestrator...")
        
        self.running = True
        
        # Get pipeline configuration
        pipeline_config = self.config.get('pipeline', {})
        fetch_interval = pipeline_config.get('fetch_interval', 300)  # 5 minutes
        analysis_interval = pipeline_config.get('analysis_interval', 600)  # 10 minutes
        sync_interval = pipeline_config.get('sync_interval', 900)  # 15 minutes
        
        # Start main loop
        while self.running:
            try:
                current_time = datetime.now()
                
                # Fetch data
                if (not self.last_fetch_time or 
                    (current_time - self.last_fetch_time).total_seconds() >= fetch_interval):
                    await self._fetch_data()
                    self.last_fetch_time = current_time
                
                # Analyze matches
                if (not self.last_analysis_time or 
                    (current_time - self.last_analysis_time).total_seconds() >= analysis_interval):
                    await self._analyze_matches()
                    self.last_analysis_time = current_time
                
                # Sync to Notion
                if (not self.last_sync_time or 
                    (current_time - self.last_sync_time).total_seconds() >= sync_interval):
                    await self._sync_to_notion()
                    self.last_sync_time = current_time
                
                # Wait before next iteration
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"❌ Error in pipeline loop: {e}")
                self.stats['errors'] += 1
                await asyncio.sleep(60)
    
    async def stop(self):
        """Pysäytä automaattinen prosessointi"""
        logger.info("🛑 Stopping Data Pipeline Orchestrator...")
        self.running = False
    
    async def _fetch_data(self):
        """Hae data useista lähteistä"""
        logger.info("🔍 Fetching data from all sources...")
        
        if not self.data_fetcher:
            logger.warning("⚠️ Data fetcher not available")
            return []
        
        try:
            # Get enabled sports
            sports = [sport for sport, config in self.config.get('sports', {}).items() 
                     if config.get('enabled', False)]
            
            # Fetch matches
            matches = await self.data_fetcher.fetch_all_matches(sports)
            
            self.stats['matches_fetched'] += len(matches)
            logger.info(f"✅ Fetched {len(matches)} matches")
            
            return matches
            
        except Exception as e:
            logger.error(f"❌ Error fetching data: {e}")
            self.stats['errors'] += 1
            return []
    
    async def _analyze_matches(self):
        """Analysoi ottelut ja laske ROI"""
        logger.info("💰 Analyzing matches for ROI opportunities...")
        
        if not self.roi_analyzer or not self.data_fetcher:
            logger.warning("⚠️ ROI analyzer or data fetcher not available")
            return []
        
        try:
            # Fetch matches if not already fetched
            matches = await self._fetch_data()
            
            roi_opportunities = []
            
            for match in matches:
                try:
                    # Enhance match with statistics
                    if self.stats_collector:
                        match = await self._enhance_match_with_stats(match)
                    
                    # Analyze match
                    roi_analysis = self.roi_analyzer.analyze_match(match)
                    
                    if roi_analysis:
                        roi_opportunities.append({
                            'match': match,
                            'roi_analysis': roi_analysis
                        })
                        
                        self.stats['roi_opportunities_found'] += 1
                        
                        # Send Telegram notification if enabled
                        await self._send_telegram_notification(match, roi_analysis)
                
                except Exception as e:
                    logger.error(f"❌ Error analyzing match {match.match_id}: {e}")
                    continue
            
            self.stats['matches_analyzed'] += len(matches)
            logger.info(f"✅ Analyzed {len(matches)} matches, found {len(roi_opportunities)} ROI opportunities")
            
            return roi_opportunities
            
        except Exception as e:
            logger.error(f"❌ Error analyzing matches: {e}")
            self.stats['errors'] += 1
            return []
    
    async def _enhance_match_with_stats(self, match: UnifiedMatchData) -> UnifiedMatchData:
        """Lisää tilastot otteluun"""
        if not self.stats_collector:
            return match
        
        try:
            # Collect team/player statistics
            if match.sport == 'tennis':
                # Collect player stats
                player1_stats = self.stats_collector.collect_stats(match.sport, match.home_team)
                player2_stats = self.stats_collector.collect_stats(match.sport, match.away_team)
                
                if player1_stats:
                    match.player_stats = {
                        match.home_team: player1_stats,
                        match.away_team: player2_stats
                    }
            else:
                # Collect team stats
                home_stats = self.stats_collector.collect_stats(match.sport, match.home_team, match.league)
                away_stats = self.stats_collector.collect_stats(match.sport, match.away_team, match.league)
                
                if home_stats and away_stats:
                    match.team_stats = {
                        match.home_team: home_stats,
                        match.away_team: away_stats
                    }
            
            # Collect H2H
            h2h = self.stats_collector.collect_head_to_head(match.sport, match.home_team, match.away_team, match.league)
            if h2h:
                if not match.historical_data:
                    match.historical_data = {}
                match.historical_data['head_to_head'] = h2h
            
        except Exception as e:
            logger.warning(f"⚠️ Error enhancing match with stats: {e}")
        
        return match
    
    async def _sync_to_notion(self):
        """Synkronoi data Notioniin"""
        logger.info("💾 Syncing data to Notion...")
        
        if not self.notion_manager:
            logger.warning("⚠️ Notion manager not available")
            return
        
        try:
            # Get analyzed matches
            roi_opportunities = await self._analyze_matches()
            
            synced_count = 0
            
            for opportunity in roi_opportunities:
                match = opportunity['match']
                roi_analysis = opportunity['roi_analysis']
                
                # Convert to match data format
                match_data = {
                    'match_id': match.match_id,
                    'sport': match.sport,
                    'home_team': match.home_team,
                    'away_team': match.away_team,
                    'league': match.league,
                    'match_time': match.match_time,
                    'odds': self._extract_odds_from_match(match),
                    'roi': roi_analysis.expected_roi,
                    'edge': roi_analysis.edge_percentage,
                    'expected_value': roi_analysis.expected_value,
                    'confidence': roi_analysis.confidence_level,
                    'status': 'Scheduled'
                }
                
                # Store to Notion
                if self.notion_manager.store_match_to_notion(match_data, match.sport):
                    synced_count += 1
            
            self.stats['matches_synced'] += synced_count
            logger.info(f"✅ Synced {synced_count} matches to Notion")
            
        except Exception as e:
            logger.error(f"❌ Error syncing to Notion: {e}")
            self.stats['errors'] += 1
    
    def _extract_odds_from_match(self, match: UnifiedMatchData) -> Dict[str, float]:
        """Extract odds from match data"""
        odds = {}
        
        if match.odds_data and match.odds_data.get('best_odds'):
            best_odds = match.odds_data['best_odds']
            h2h_odds = best_odds.get('h2h', {})
            
            if match.sport == 'tennis':
                odds['player_1'] = h2h_odds.get(match.home_team)
                odds['player_2'] = h2h_odds.get(match.away_team)
            else:
                odds['home'] = h2h_odds.get(match.home_team)
                odds['away'] = h2h_odds.get(match.away_team)
        
        return odds
    
    async def _send_telegram_notification(self, match: UnifiedMatchData, roi_analysis: ROIAnalysis):
        """Lähetä Telegram-ilmoitus"""
        pipeline_config = self.config.get('pipeline', {})
        
        if not pipeline_config.get('enable_telegram_notifications', False):
            return
        
        # This would send Telegram notification
        # Implementation depends on Telegram bot setup
        logger.info(f"📱 Would send Telegram notification for ROI opportunity: {roi_analysis.expected_roi:.2f}%")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Hae pipeline-tilastot"""
        return {
            **self.stats,
            'last_fetch_time': self.last_fetch_time.isoformat() if self.last_fetch_time else None,
            'last_analysis_time': self.last_analysis_time.isoformat() if self.last_analysis_time else None,
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'running': self.running
        }


async def main():
    """Test Data Pipeline Orchestrator"""
    print("🔄 DATA PIPELINE ORCHESTRATOR TEST")
    print("=" * 50)
    
    orchestrator = DataPipelineOrchestrator()
    
    print("✅ Orchestrator initialized")
    print("\n📊 Statistics:")
    stats = orchestrator.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n🚀 Starting pipeline (will run for 30 seconds)...")
    
    # Run for 30 seconds as test
    try:
        await asyncio.wait_for(orchestrator.start(), timeout=30.0)
    except asyncio.TimeoutError:
        await orchestrator.stop()
        print("\n✅ Pipeline test completed")
    
    print("\n📊 Final Statistics:")
    final_stats = orchestrator.get_statistics()
    for key, value in final_stats.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())

