#!/usr/bin/env python3
"""
Live Odds Monitoring System - Main Daemon

Professional-grade real-time monitoring for 50% equity optimization.
Tracks odds movements across multiple soccer leagues, detects value opportunities,
and sends instant alerts when odds enter the profitable 1.30-1.80 range.

Usage:
    python live_odds_monitor.py [--test] [--leagues LEAGUES] [--interval SECONDS]
    
Examples:
    python live_odds_monitor.py                           # Full monitoring
    python live_odds_monitor.py --test                    # Test mode (no alerts)
    python live_odds_monitor.py --leagues championship    # Single league
    python live_odds_monitor.py --interval 15             # 15-second updates
"""

import asyncio
import argparse
import logging
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set
import json

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config.live_config import LiveMonitoringConfig
from monitors.odds_tracker import OddsTracker, OddsSnapshot, OddsMovement
from monitors.value_detector import ValueDetector, ValueOpportunity
from monitors.alert_manager import AlertManager
from storage.odds_database import OddsDatabase
from storage.analytics import LiveAnalytics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('live_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class LiveOddsMonitor:
    """Main live odds monitoring daemon"""
    
    def __init__(self, test_mode: bool = False, target_leagues: List[str] = None, 
                 update_interval: int = None, bankroll: float = None):
        
        self.config = LiveMonitoringConfig()
        self.test_mode = test_mode
        self.target_leagues = target_leagues or self.config.TARGET_LEAGUES
        self.update_interval = update_interval or self.config.REFRESH_INTERVAL
        self.bankroll = bankroll
        
        # Initialize components
        self.odds_tracker = OddsTracker()
        self.value_detector = ValueDetector(bankroll)
        self.alert_manager = AlertManager()
        self.database = OddsDatabase()
        self.analytics = LiveAnalytics(self.database)
        
        # Control flags
        self.running = False
        self.shutdown_requested = False
        
        # Performance tracking
        self.cycle_count = 0
        self.start_time = None
        self.last_cleanup_time = datetime.now()
        self.last_summary_time = datetime.now()
        
        logger.info(f"Initialized Live Odds Monitor")
        logger.info(f"Target leagues: {len(self.target_leagues)}")
        logger.info(f"Update interval: {self.update_interval}s")
        logger.info(f"Test mode: {test_mode}")
    
    async def start_monitoring(self):
        """Start the live monitoring process"""
        
        logger.info("🚀 Starting Live Odds Monitor...")
        
        # Validate configuration
        if not self.config.validate_config():
            logger.error("❌ Configuration validation failed")
            return False
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
        self.running = True
        self.start_time = datetime.now()
        
        try:
            # Initialize odds tracker
            async with self.odds_tracker as tracker:
                
                # Send startup notification
                if not self.test_mode:
                    await self._send_startup_notification()
                
                # Main monitoring loop
                while self.running and not self.shutdown_requested:
                    cycle_start = datetime.now()
                    
                    try:
                        # Execute monitoring cycle
                        await self._execute_monitoring_cycle(tracker)
                        
                        # Periodic maintenance
                        await self._perform_maintenance()
                        
                        self.cycle_count += 1
                        
                        # Calculate sleep time to maintain interval
                        cycle_duration = (datetime.now() - cycle_start).total_seconds()
                        sleep_time = max(0, self.update_interval - cycle_duration)
                        
                        if sleep_time > 0:
                            await asyncio.sleep(sleep_time)
                        else:
                            logger.warning(f"Cycle took {cycle_duration:.1f}s (longer than {self.update_interval}s interval)")
                    
                    except Exception as e:
                        logger.error(f"Error in monitoring cycle: {e}")
                        await asyncio.sleep(self.update_interval)
                        continue
                
                # Send shutdown notification
                if not self.test_mode:
                    await self._send_shutdown_notification()
        
        except Exception as e:
            logger.error(f"Fatal error in monitoring: {e}")
            return False
        
        finally:
            self.running = False
            self.database.close()
            logger.info("🛑 Live Odds Monitor stopped")
        
        return True
    
    async def _execute_monitoring_cycle(self, tracker: OddsTracker):
        """Execute one complete monitoring cycle"""
        
        cycle_start = datetime.now()
        
        # Step 1: Fetch odds from all leagues
        logger.debug(f"Fetching odds from {len(self.target_leagues)} leagues...")
        
        all_snapshots = []
        fetch_tasks = [
            tracker.fetch_league_odds(league) 
            for league in self.target_leagues
        ]
        
        results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, list):
                all_snapshots.extend(result)
            else:
                logger.error(f"Failed to fetch {self.target_leagues[i]}: {result}")
        
        if not all_snapshots:
            logger.warning("No odds data fetched in this cycle")
            return
        
        # Step 2: Detect movements
        logger.debug(f"Analyzing {len(all_snapshots)} odds snapshots...")
        movements = tracker.detect_movements(all_snapshots)
        
        # Step 3: Detect value opportunities
        opportunities = await self.value_detector.analyze_snapshots(all_snapshots, movements)
        
        # Step 4: Store data in database
        await self._store_cycle_data(all_snapshots, movements, opportunities)
        
        # Step 5: Send alerts (if not in test mode)
        alert_results = {}
        if opportunities and not self.test_mode:
            alert_results = await self.alert_manager.process_opportunities(opportunities, movements)
        
        # Step 6: Log cycle summary
        cycle_duration = (datetime.now() - cycle_start).total_seconds()
        
        logger.info(f"Cycle {self.cycle_count}: {len(all_snapshots)} odds, "
                   f"{len(movements)} movements, {len(opportunities)} opportunities "
                   f"({cycle_duration:.1f}s)")
        
        if opportunities:
            urgent_count = sum(1 for opp in opportunities if opp.urgency_level in ['HIGH', 'CRITICAL'])
            logger.info(f"  📊 Opportunities: {urgent_count} urgent, "
                       f"avg edge: {sum(opp.edge_estimate for opp in opportunities) / len(opportunities):.1f}%")
        
        # Update tracker's last update time
        tracker.last_update_time = datetime.now()
    
    async def _store_cycle_data(self, snapshots: List[OddsSnapshot], 
                               movements: List[OddsMovement], 
                               opportunities: List[ValueOpportunity]):
        """Store cycle data in database"""
        
        try:
            # Store snapshots (sample to avoid overwhelming database)
            sample_size = min(len(snapshots), 50)  # Store max 50 snapshots per cycle
            for snapshot in snapshots[:sample_size]:
                self.database.store_odds_snapshot(snapshot)
            
            # Store all movements (they're already filtered for significance)
            for movement in movements:
                self.database.store_odds_movement(movement)
            
            # Store all opportunities
            for opportunity in opportunities:
                self.database.store_value_opportunity(opportunity)
            
        except Exception as e:
            logger.error(f"Failed to store cycle data: {e}")
    
    async def _perform_maintenance(self):
        """Perform periodic maintenance tasks"""
        
        current_time = datetime.now()
        
        # Cleanup old data (every hour)
        if (current_time - self.last_cleanup_time).total_seconds() > 3600:
            logger.info("🧹 Performing maintenance cleanup...")
            
            # Cleanup tracker data
            self.odds_tracker.cleanup_old_data()
            
            # Cleanup database
            self.database.cleanup_old_data()
            
            self.last_cleanup_time = current_time
        
        # Send periodic summary (every 6 hours)
        if (current_time - self.last_summary_time).total_seconds() > 21600:
            if not self.test_mode:
                await self._send_periodic_summary()
            
            self.last_summary_time = current_time
    
    async def _send_startup_notification(self):
        """Send notification when monitoring starts"""
        
        try:
            performance_stats = self.odds_tracker.get_performance_stats()
            await self.alert_manager.send_system_status(performance_stats)
            
            logger.info("📱 Sent startup notification")
            
        except Exception as e:
            logger.error(f"Failed to send startup notification: {e}")
    
    async def _send_shutdown_notification(self):
        """Send notification when monitoring stops"""
        
        try:
            runtime = datetime.now() - self.start_time if self.start_time else timedelta(0)
            
            message = f"""🛑 **Live Monitor Stopped**

⏱️ **Runtime**: {str(runtime).split('.')[0]}
🔄 **Cycles**: {self.cycle_count}
📊 **Performance**: {self.odds_tracker.get_performance_stats()}

_Monitor will restart automatically if configured_"""
            
            # Send via alert manager's bot
            await self.alert_manager.bot.send_message(
                chat_id=self.config.TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info("📱 Sent shutdown notification")
            
        except Exception as e:
            logger.error(f"Failed to send shutdown notification: {e}")
    
    async def _send_periodic_summary(self):
        """Send periodic performance summary"""
        
        try:
            # Get recent opportunities
            opportunities = self.database.get_recent_opportunities(6)  # Last 6 hours
            movements_count = len(self.odds_tracker.detected_movements)
            
            # Calculate average edge
            avg_edge = (sum(opp.edge_estimate for opp in opportunities) / len(opportunities)) if opportunities else 0
            
            # Get top leagues
            league_counts = {}
            for opp in opportunities:
                league_counts[opp.league] = league_counts.get(opp.league, 0) + 1
            
            top_leagues = sorted(league_counts.items(), key=lambda x: x[1], reverse=True)
            top_league_names = [league for league, count in top_leagues[:3]]
            
            await self.alert_manager.send_daily_summary(
                len(opportunities), movements_count, avg_edge, top_league_names
            )
            
            logger.info("📱 Sent periodic summary")
            
        except Exception as e:
            logger.error(f"Failed to send periodic summary: {e}")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown_requested = True
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def stop_monitoring(self):
        """Stop the monitoring process"""
        logger.info("🛑 Stop requested...")
        self.running = False
        self.shutdown_requested = True
    
    def get_status(self) -> Dict:
        """Get current monitoring status"""
        
        runtime = datetime.now() - self.start_time if self.start_time else timedelta(0)
        
        return {
            'running': self.running,
            'test_mode': self.test_mode,
            'runtime_seconds': runtime.total_seconds(),
            'cycle_count': self.cycle_count,
            'target_leagues': self.target_leagues,
            'update_interval': self.update_interval,
            'tracker_stats': self.odds_tracker.get_performance_stats(),
            'detector_stats': self.value_detector.get_performance_stats(),
            'alert_stats': self.alert_manager.get_alert_stats()
        }

def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(description='Live Odds Monitoring System')
    parser.add_argument('--test', action='store_true',
                       help='Run in test mode (no alerts sent)')
    parser.add_argument('--leagues', nargs='+',
                       help='Specific leagues to monitor (default: all)')
    parser.add_argument('--interval', type=int, default=30,
                       help='Update interval in seconds (default: 30)')
    parser.add_argument('--bankroll', type=float,
                       help='Custom bankroll amount (default: $1000)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate leagues if specified
    config = LiveMonitoringConfig()
    if args.leagues:
        invalid_leagues = [league for league in args.leagues if league not in config.TARGET_LEAGUES]
        if invalid_leagues:
            print(f"❌ Invalid leagues: {invalid_leagues}")
            print(f"Available leagues: {config.TARGET_LEAGUES}")
            sys.exit(1)
    
    # Initialize monitor
    monitor = LiveOddsMonitor(
        test_mode=args.test,
        target_leagues=args.leagues,
        update_interval=args.interval,
        bankroll=args.bankroll
    )
    
    # Start monitoring
    try:
        print(f"\n🎾 Live Odds Monitor - Professional Edition")
        print(f"{'='*50}")
        print(f"📊 Leagues: {len(monitor.target_leagues)}")
        print(f"⏱️  Interval: {args.interval}s")
        print(f"🧪 Test Mode: {args.test}")
        print(f"💰 Bankroll: ${monitor.bankroll or 1000}")
        print(f"{'='*50}")
        
        success = asyncio.run(monitor.start_monitoring())
        
        if success:
            print(f"\n✅ Monitoring completed successfully!")
            sys.exit(0)
        else:
            print(f"\n❌ Monitoring failed!")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print(f"\n⏹️ Monitoring interrupted by user")
        monitor.stop_monitoring()
        sys.exit(130)
    
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        logger.exception("Unexpected error in main")
        sys.exit(1)

if __name__ == "__main__":
    main()
