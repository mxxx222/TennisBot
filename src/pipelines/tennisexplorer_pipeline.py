#!/usr/bin/env python3
"""
🔄 TENNISEXPLORER PIPELINE
==========================

Main pipeline orchestrator for TennisExplorer scraper.
Coordinates scraping, data storage, and enrichment.

Data Flow:
TennisExplorer Scraper → PostgreSQL → Enrichment Pipeline → Notion API
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scrapers.tennisexplorer_scraper import TennisExplorerScraper, TennisExplorerMatch, H2HRecord, PlayerForm
from src.monitoring.tennisexplorer_monitor import TennisExplorerMonitor

# Optional: Project Status Manager
try:
    from src.notion.project_status_manager import ProjectStatusManager
    STATUS_MANAGER_AVAILABLE = True
except ImportError:
    STATUS_MANAGER_AVAILABLE = False

# Optional: Alert Manager
try:
    from src.alerts.roi_alert_manager import ROIAlertManager
    ALERT_MANAGER_AVAILABLE = True
except ImportError:
    ALERT_MANAGER_AVAILABLE = False

logger = logging.getLogger(__name__)


class TennisExplorerPipeline:
    """Pipeline to orchestrate TennisExplorer scraping and data storage"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize TennisExplorer Pipeline
        
        Args:
            config: Configuration dict with database settings, rate limits, etc.
        """
        self.config = config or {}
        
        # Initialize scraper
        scraper_config = self.config.get('scraper', {})
        self.scraper = TennisExplorerScraper(scraper_config, use_selenium=True)
        
        # Database connection (will be initialized if available)
        self.db_connection = None
        self._init_database()
        
        # Processed match IDs for duplicate detection
        self.processed_match_ids: set = set()
        
        # Metrics
        self.metrics = {
            'matches_scraped': 0,
            'matches_stored': 0,
            'h2h_scraped': 0,
            'form_scraped': 0,
            'odds_scraped': 0,
            'errors': 0,
        }
        
        # Monitor
        self.monitor = TennisExplorerMonitor()
        
        # Project Status Manager (optional)
        self.status_manager = None
        if STATUS_MANAGER_AVAILABLE:
            try:
                self.status_manager = ProjectStatusManager()
                # Try to get or create status page, but don't fail if it doesn't work
                try:
                    page_id = self.status_manager.get_or_create_status_page()
                    if page_id:
                        logger.info(f"✅ Status page ready: {page_id[:20]}...")
                except Exception as e:
                    logger.debug(f"Status page setup skipped: {e}")
            except Exception as e:
                logger.debug(f"Project Status Manager not available: {e}")
        
        # Alert Manager (optional)
        self.alert_manager = None
        if ALERT_MANAGER_AVAILABLE:
            try:
                alert_config = self.config.get('alerts', {})
                self.alert_manager = ROIAlertManager(alert_config)
            except Exception as e:
                logger.debug(f"Alert Manager not available: {e}")
        
        logger.info("🔄 TennisExplorer Pipeline initialized")
    
    def _init_database(self):
        """Initialize database connection"""
        try:
            # Try PostgreSQL first
            db_config = self.config.get('database', {})
            if db_config.get('type') == 'postgresql':
                import psycopg2
                self.db_connection = psycopg2.connect(
                    host=db_config.get('host', 'localhost'),
                    port=db_config.get('port', 5432),
                    database=db_config.get('database', 'tennisbot'),
                    user=db_config.get('user'),
                    password=db_config.get('password')
                )
                logger.info("✅ PostgreSQL connection established")
            elif db_config.get('type') == 'sqlite' or not db_config:
                # Fallback to SQLite for MVP
                import sqlite3
                db_path = db_config.get('path', 'data/tennisexplorer.db')
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
                self.db_connection = sqlite3.connect(db_path)
                logger.info(f"✅ SQLite connection established: {db_path}")
        except ImportError:
            logger.warning("⚠️ Database libraries not available, using in-memory storage")
        except Exception as e:
            logger.warning(f"⚠️ Database connection failed: {e}, using in-memory storage")
    
    def store_match(self, match: TennisExplorerMatch) -> bool:
        """
        Store match in database
        
        Args:
            match: TennisExplorerMatch object
            
        Returns:
            True if successful
        """
        if not self.db_connection:
            logger.debug("⚠️ No database connection, skipping storage")
            return False
        
        try:
            cursor = self.db_connection.cursor()
            
            # Check if match already exists
            if isinstance(self.db_connection, type(__import__('sqlite3').connect(''))):
                # SQLite
                cursor.execute("""
                    INSERT OR REPLACE INTO tennisexplorer_matches 
                    (match_id, player_a, player_b, tournament, tournament_tier, surface, 
                     current_score, match_status, match_url, scraped_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    match.match_id, match.player_a, match.player_b, match.tournament,
                    match.tournament_tier, match.surface, match.current_score,
                    'live' if match.current_score else 'scheduled', match.match_url,
                    match.scraped_at, datetime.now()
                ))
            else:
                # PostgreSQL
                cursor.execute("""
                    INSERT INTO tennisexplorer_matches 
                    (match_id, player_a, player_b, tournament, tournament_tier, surface, 
                     current_score, match_status, match_url, scraped_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (match_id) DO UPDATE SET
                        current_score = EXCLUDED.current_score,
                        match_status = EXCLUDED.match_status,
                        updated_at = EXCLUDED.updated_at
                """, (
                    match.match_id, match.player_a, match.player_b, match.tournament,
                    match.tournament_tier, match.surface, match.current_score,
                    'live' if match.current_score else 'scheduled', match.match_url,
                    match.scraped_at, datetime.now()
                ))
            
            self.db_connection.commit()
            self.metrics['matches_stored'] += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing match: {e}")
            self.metrics['errors'] += 1
            if self.db_connection:
                self.db_connection.rollback()
            return False
    
    def store_h2h(self, h2h: H2HRecord) -> bool:
        """Store H2H record in database"""
        if not self.db_connection:
            return False
        
        try:
            cursor = self.db_connection.cursor()
            
            # Store overall H2H
            if isinstance(self.db_connection, type(__import__('sqlite3').connect(''))):
                # SQLite
                cursor.execute("""
                    INSERT OR REPLACE INTO h2h_records 
                    (player_a, player_b, surface, wins_a, wins_b, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (h2h.player_a, h2h.player_b, None, h2h.overall['wins_a'], 
                      h2h.overall['wins_b'], datetime.now()))
                
                # Store surface-specific H2H
                for surface, record in h2h.by_surface.items():
                    cursor.execute("""
                        INSERT OR REPLACE INTO h2h_records 
                        (player_a, player_b, surface, wins_a, wins_b, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (h2h.player_a, h2h.player_b, surface, record['wins_a'], 
                          record['wins_b'], datetime.now()))
            else:
                # PostgreSQL
                cursor.execute("""
                    INSERT INTO h2h_records 
                    (player_a, player_b, surface, wins_a, wins_b, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (player_a, player_b, surface) DO UPDATE SET
                        wins_a = EXCLUDED.wins_a,
                        wins_b = EXCLUDED.wins_b,
                        last_updated = EXCLUDED.last_updated
                """, (h2h.player_a, h2h.player_b, None, h2h.overall['wins_a'], 
                      h2h.overall['wins_b'], datetime.now()))
                
                # Store surface-specific H2H
                for surface, record in h2h.by_surface.items():
                    cursor.execute("""
                        INSERT INTO h2h_records 
                        (player_a, player_b, surface, wins_a, wins_b, last_updated)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (player_a, player_b, surface) DO UPDATE SET
                            wins_a = EXCLUDED.wins_a,
                            wins_b = EXCLUDED.wins_b,
                            last_updated = EXCLUDED.last_updated
                    """, (h2h.player_a, h2h.player_b, surface, record['wins_a'], 
                          record['wins_b'], datetime.now()))
            
            self.db_connection.commit()
            self.metrics['h2h_scraped'] += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing H2H: {e}")
            self.metrics['errors'] += 1
            if self.db_connection:
                self.db_connection.rollback()
            return False
    
    def store_player_form(self, form: PlayerForm) -> bool:
        """Store player form in database"""
        if not self.db_connection:
            return False
        
        try:
            cursor = self.db_connection.cursor()
            
            if isinstance(self.db_connection, type(__import__('sqlite3').connect(''))):
                # SQLite
                cursor.execute("""
                    INSERT OR REPLACE INTO player_form 
                    (player_name, surface, last_5_wins, last_5_losses, 
                     last_10_wins, last_10_losses, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (form.player_name, None, form.last_5_wins, form.last_5_losses,
                      form.last_10_wins, form.last_10_losses, datetime.now()))
            else:
                # PostgreSQL
                cursor.execute("""
                    INSERT INTO player_form 
                    (player_name, surface, last_5_wins, last_5_losses, 
                     last_10_wins, last_10_losses, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (player_name, surface) DO UPDATE SET
                        last_5_wins = EXCLUDED.last_5_wins,
                        last_5_losses = EXCLUDED.last_5_losses,
                        last_10_wins = EXCLUDED.last_10_wins,
                        last_10_losses = EXCLUDED.last_10_losses,
                        updated_at = EXCLUDED.updated_at
                """, (form.player_name, None, form.last_5_wins, form.last_5_losses,
                      form.last_10_wins, form.last_10_losses, datetime.now()))
            
            self.db_connection.commit()
            self.metrics['form_scraped'] += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing player form: {e}")
            self.metrics['errors'] += 1
            if self.db_connection:
                self.db_connection.rollback()
            return False
    
    def store_odds(self, match_id: str, odds_data: Dict[str, Any]) -> bool:
        """Store odds data in database"""
        if not self.db_connection or not odds_data:
            return False
        
        try:
            cursor = self.db_connection.cursor()
            
            for bookmaker, odds in odds_data.items():
                if isinstance(self.db_connection, type(__import__('sqlite3').connect(''))):
                    # SQLite
                    cursor.execute("""
                        INSERT INTO odds_history 
                        (match_id, odds_a, odds_b, bookmaker, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    """, (match_id, odds.get('odds_a'), odds.get('odds_b'), 
                          bookmaker, datetime.now()))
                else:
                    # PostgreSQL
                    cursor.execute("""
                        INSERT INTO odds_history 
                        (match_id, odds_a, odds_b, bookmaker, timestamp)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (match_id, odds.get('odds_a'), odds.get('odds_b'), 
                          bookmaker, datetime.now()))
            
            self.db_connection.commit()
            self.metrics['odds_scraped'] += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing odds: {e}")
            self.metrics['errors'] += 1
            if self.db_connection:
                self.db_connection.rollback()
            return False
    
    async def run_scrape_cycle(self) -> Dict[str, Any]:
        """
        Run one complete scrape cycle
        
        Returns:
            Dictionary with results and metrics
        """
        logger.info("🚀 Starting TennisExplorer scrape cycle...")
        
        start_time = datetime.now()
        
        try:
            # Step 1: Scrape live matches
            logger.info("📥 Step 1: Scraping live matches...")
            matches = self.scraper.scrape_live_matches()
            self.metrics['matches_scraped'] += len(matches)
            
            logger.info(f"✅ Scraped {len(matches)} matches")
            
            # Step 2: Store matches and enrich with H2H, form, odds
            logger.info("📤 Step 2: Storing matches and enriching data...")
            
            for match in matches:
                # Store match
                self.store_match(match)
                
                # Scrape and store H2H (if not already processed)
                h2h_key = f"{match.player_a}_{match.player_b}"
                if h2h_key not in self.processed_match_ids:
                    h2h = self.scraper.scrape_h2h(match.player_a, match.player_b)
                    if h2h:
                        self.store_h2h(h2h)
                        match.h2h_overall = h2h.overall
                        match.h2h_surface = h2h.by_surface
                
                # Scrape and store player form
                form_a = self.scraper.scrape_player_form(match.player_a, match.surface)
                if form_a:
                    self.store_player_form(form_a)
                    match.recent_form_a = {
                        'last_5': f"{form_a.last_5_wins}-{form_a.last_5_losses}",
                        'last_10': f"{form_a.last_10_wins}-{form_a.last_10_losses}"
                    }
                
                form_b = self.scraper.scrape_player_form(match.player_b, match.surface)
                if form_b:
                    self.store_player_form(form_b)
                    match.recent_form_b = {
                        'last_5': f"{form_b.last_5_wins}-{form_b.last_5_losses}",
                        'last_10': f"{form_b.last_10_wins}-{form_b.last_10_losses}"
                    }
                
                # Scrape and store odds
                if match.match_url:
                    odds_data = self.scraper.scrape_odds_comparison(match.match_id, match.match_url)
                    if odds_data:
                        self.store_odds(match.match_id, odds_data)
                        # Store best odds
                        if odds_data:
                            best_odds = min(odds_data.values(), key=lambda x: x.get('odds_a', 999))
                            match.live_odds_a = best_odds.get('odds_a')
                            match.live_odds_b = best_odds.get('odds_b')
                
                self.processed_match_ids.add(match.match_id)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = {
                'success': True,
                'timestamp': end_time.isoformat(),
                'duration_seconds': duration,
                'metrics': self.metrics.copy(),
                'matches_processed': len(matches),
            }
            
            # Update monitor
            for _ in range(len(matches)):
                self.monitor.record_match_scraped()
            for _ in range(self.metrics['matches_stored']):
                self.monitor.record_match_stored()
            
            # Update last activity
            self.monitor.update_last_activity()
            
            # Check for alerts
            timeout_alert = self.monitor.check_pipeline_timeout()
            if timeout_alert.get('should_alert') and self.alert_manager:
                try:
                    await self.alert_manager.send_alert({
                        'match_id': 'system',
                        'opportunity_type': 'pipeline_timeout',
                        'strategy': 'System Alert',
                        'expected_value_pct': 0,
                        'kelly_stake_pct': 0,
                        'confidence_score': 1.0,
                        'reasoning': timeout_alert['message'],
                        'player_a': 'System',
                        'player_b': 'Monitor',
                        'tournament': 'System Health'
                    })
                except Exception as e:
                    logger.debug(f"Could not send timeout alert: {e}")
            
            # Check error rate alert
            total_requests = self.metrics['matches_scraped'] + self.metrics['h2h_scraped'] + self.metrics['form_scraped']
            if total_requests > 0:
                error_rate = (self.metrics['errors'] / total_requests) * 100
                if error_rate > 10.0 and self.alert_manager:
                    try:
                        await self.alert_manager.send_alert({
                            'match_id': 'system',
                            'opportunity_type': 'error_rate',
                            'strategy': 'System Alert',
                            'expected_value_pct': 0,
                            'kelly_stake_pct': 0,
                            'confidence_score': 1.0,
                            'reasoning': f'High error rate: {error_rate:.1f}% ({self.metrics["errors"]} errors in {total_requests} requests)',
                            'player_a': 'System',
                            'player_b': 'Monitor',
                            'tournament': 'System Health'
                        })
                    except Exception as e:
                        logger.debug(f"Could not send error rate alert: {e}")
            
            # Update Project Status page if available
            if self.status_manager:
                try:
                    metrics_summary = self.monitor.get_metrics_summary()
                    metrics_summary.update(self.metrics)
                    self.status_manager.update_metrics(metrics_summary)
                except Exception as e:
                    logger.debug(f"Could not update status page: {e}")
            
            logger.info(f"✅ Scrape cycle completed: {len(matches)} matches processed in {duration:.1f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Scrape cycle failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current pipeline metrics"""
        return self.metrics.copy()
    
    def close(self):
        """Close database connection and cleanup"""
        if self.db_connection:
            self.db_connection.close()
        if self.scraper:
            del self.scraper


async def main():
    """Test TennisExplorer Pipeline"""
    print("🔄 TENNISEXPLORER PIPELINE TEST")
    print("=" * 50)
    
    config = {
        'scraper': {
            'request_delay': 2.0,
        },
        'database': {
            'type': 'sqlite',  # Use SQLite for MVP
            'path': 'data/tennisexplorer.db'
        }
    }
    
    pipeline = TennisExplorerPipeline(config)
    
    try:
        result = await pipeline.run_scrape_cycle()
        
        if result['success']:
            print(f"\n✅ Pipeline successful!")
            print(f"   Matches scraped: {result['metrics']['matches_scraped']}")
            print(f"   Matches stored: {result['metrics']['matches_stored']}")
            print(f"   H2H scraped: {result['metrics']['h2h_scraped']}")
            print(f"   Form scraped: {result['metrics']['form_scraped']}")
            print(f"   Odds scraped: {result['metrics']['odds_scraped']}")
            print(f"   Errors: {result['metrics']['errors']}")
            print(f"   Duration: {result['duration_seconds']:.1f}s")
        else:
            print(f"\n❌ Pipeline failed: {result.get('error')}")
    
    finally:
        pipeline.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())

