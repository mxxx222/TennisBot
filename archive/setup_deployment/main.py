"""
Main Orchestration System for Betfury.io Educational Research
============================================================

This is the main entry point that coordinates all components of the
educational sports analytics system.

DISCLAIMER: This is for educational/research purposes only.
No actual betting or financial transactions are performed.
"""

import asyncio
import sys
import argparse
import yaml
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Import all components
from src.scraper import BetfuryScraper, MatchData
from src.ai_predictor import SportsPredictionModel, PredictionResult
from src.telegram_bot import BetfuryBot, NotificationConfig
from src.risk_manager import ResearchDataStore, EducationalRiskManager, SystemMonitor
from src.websocket_monitor import EducationalWebSocketMonitor, SportsDataAnalyzer

logger = logging.getLogger(__name__)

class BetfuryResearchSystem:
    """Main orchestration system for educational research"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize components
        self.scraper: Optional[BetfuryScraper] = None
        self.predictor: Optional[SportsPredictionModel] = None
        self.bot: Optional[BetfuryBot] = None
        self.data_store: Optional[ResearchDataStore] = None
        self.risk_manager: Optional[EducationalRiskManager] = None
        self.monitor: Optional[SystemMonitor] = None
        self.ws_monitor: Optional[EducationalWebSocketMonitor] = None
        self.ws_analyzer: Optional[SportsDataAnalyzer] = None
        
        # System state
        self.is_running = False
        self.start_time: Optional[datetime] = None
        
        # Research statistics
        self.stats = {
            'matches_analyzed': 0,
            'predictions_generated': 0,
            'high_confidence_signals': 0,
            'system_uptime': 0
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f)
            else:
                logger.warning(f"Config file {self.config_path} not found, using defaults")
                return self._default_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'debug': False,
            'research_mode': True,
            'rate_limit': {
                'min_delay_seconds': 5.0,
                'max_delay_seconds': 10.0
            },
            'scraping': {
                'timeout_seconds': 30,
                'headless_browser': True
            },
            'ml_config': {
                'min_confidence': 0.70,
                'max_odds': 3.0,
                'min_odds': 1.05
            },
            'telegram': {
                'enabled': False,
                'bot_token': '',
                'chat_id': ''
            },
            'risk_management': {
                'max_matches_per_hour': 50,
                'max_predictions_per_day': 100,
                'min_confidence_threshold': 0.70
            }
        }
    
    async def initialize(self) -> bool:
        """Initialize all system components"""
        try:
            logger.info("Initializing Betfury Educational Research System...")
            
            # Initialize data store and risk management
            self.data_store = ResearchDataStore()
            self.risk_manager = EducationalRiskManager(self.data_store)
            self.monitor = SystemMonitor(self.data_store)
            
            # Initialize scraper
            scraper_config = {
                'rate_limit': self.config['rate_limit'],
                'scraping': self.config['scraping'],
                'targets': {
                    'sports_page': 'https://betfury.io/sports',
                    'live_page': 'https://betfury.io/sports/live'
                }
            }
            self.scraper = BetfuryScraper(scraper_config)
            
            # Initialize AI predictor
            self.predictor = SportsPredictionModel(self.config['ml_config'])
            
            # Initialize Telegram bot
            telegram_config = NotificationConfig(
                enabled=self.config['telegram']['enabled'],
                bot_token=self.config['telegram']['bot_token'],
                chat_id=self.config['telegram']['chat_id']
            )
            self.bot = BetfuryBot(telegram_config)
            
            # Initialize WebSocket monitor
            self.ws_monitor = EducationalWebSocketMonitor(self.config)
            self.ws_analyzer = SportsDataAnalyzer(self.ws_monitor)
            
            # Initialize bot if enabled
            if self.config['telegram']['enabled']:
                bot_initialized = await self.bot.initialize()
                if not bot_initialized:
                    logger.warning("Telegram bot initialization failed, continuing without bot")
            
            logger.info("✅ System initialization completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            return False
    
    async def run_research_cycle(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """
        Run a complete research cycle
        
        Args:
            duration_minutes: Duration of the research cycle in minutes
            
        Returns:
            Research results summary
        """
        logger.info(f"🔬 Starting {duration_minutes}-minute research cycle")
        
        self.is_running = True
        self.start_time = datetime.now()
        
        results = {
            'start_time': self.start_time.isoformat(),
            'duration_minutes': duration_minutes,
            'matches_analyzed': 0,
            'predictions_generated': 0,
            'high_confidence_signals': 0,
            'errors': 0,
            'research_notes': []
        }
        
        try:
            async with self.scraper:
                # Main research loop
                end_time = self.start_time + timedelta(minutes=duration_minutes)
                
                while datetime.now() < end_time and self.is_running:
                    cycle_start = datetime.now()
                    
                    try:
                        # 1. Scrape live matches
                        matches = await self.scraper.get_live_matches(use_selenium=True)
                        
                        # 2. Check scraping risk
                        scraping_risk = await self.risk_manager.check_scraping_risk({
                            'url': 'https://betfury.io/sports/live',
                            'matches_count': len(matches)
                        })
                        
                        if not scraping_risk['allowed']:
                            logger.warning(f"Scraping risk check failed: {scraping_risk['reason']}")
                            await asyncio.sleep(30)
                            continue
                        
                        results['matches_analyzed'] += len(matches)
                        
                        # 3. Generate predictions for high-quality matches
                        predictions = await self._process_matches_for_predictions(matches)
                        
                        results['predictions_generated'] += len(predictions)
                        results['high_confidence_signals'] += len([p for p in predictions if p.confidence >= 0.75])
                        
                        # 4. Send notifications for high-confidence predictions
                        await self._send_prediction_notifications(predictions)
                        
                        # 5. Log research activity
                        self.data_store.log_scraping_activity(
                            'research_cycle',
                            {'matches_found': len(matches), 'predictions_generated': len(predictions)}
                        )
                        
                        # 6. Update statistics
                        self.stats['matches_analyzed'] += len(matches)
                        self.stats['predictions_generated'] += len(predictions)
                        
                        # 7. Wait for next cycle (respecting rate limits)
                        cycle_duration = (datetime.now() - cycle_start).total_seconds()
                        wait_time = max(30, 60 - cycle_duration)  # Minimum 30s between cycles
                        
                        if scraping_risk.get('suggested_delay', 0) > 0:
                            wait_time = max(wait_time, scraping_risk['suggested_delay'])
                        
                        logger.info(f"✅ Cycle complete: {len(matches)} matches, {len(predictions)} predictions")
                        logger.info(f"⏳ Waiting {wait_time:.1f} seconds for next cycle...")
                        
                        await asyncio.sleep(wait_time)
                        
                    except Exception as e:
                        logger.error(f"❌ Error in research cycle: {e}")
                        results['errors'] += 1
                        await self.risk_manager.record_error('research_cycle', str(e))
                        await asyncio.sleep(10)  # Wait before retrying
        
        except Exception as e:
            logger.error(f"❌ Research cycle failed: {e}")
            results['errors'] += 1
        
        finally:
            self.is_running = False
            results['end_time'] = datetime.now().isoformat()
            results['actual_duration_minutes'] = (datetime.now() - self.start_time).total_seconds() / 60
            results['stats'] = self.stats.copy()
            
            logger.info(f"🏁 Research cycle completed: {results}")
        
        return results
    
    async def _process_matches_for_predictions(self, matches: list[MatchData]) -> list[PredictionResult]:
        """Process matches and generate predictions"""
        predictions = []
        
        for match in matches:
            try:
                # Check prediction risk
                prediction_risk = await self.risk_manager.check_prediction_risk({
                    'match_id': match.match_id,
                    'confidence': 0.0,  # Will be calculated by model
                    'prediction': 'UNKNOWN'
                })
                
                if not prediction_risk['allowed']:
                    continue
                
                # Generate prediction
                prediction = await self.predictor.predict(match)
                
                if prediction and prediction.confidence >= self.config['ml_config']['min_confidence']:
                    predictions.append(prediction)
                    
            except Exception as e:
                logger.error(f"Error processing match {match.match_id}: {e}")
                await self.risk_manager.record_error('match_processing', str(e))
                continue
        
        return predictions
    
    async def _send_prediction_notifications(self, predictions: list[PredictionResult]):
        """Send notifications for high-confidence predictions"""
        if not self.bot or not self.bot.config.enabled:
            return
        
        high_confidence_preds = [p for p in predictions if p.confidence >= 0.75]
        
        for prediction in high_confidence_preds:
            try:
                # Format prediction data for notification
                prediction_data = {
                    'match_id': prediction.match_id,
                    'home_team': prediction.home_team,
                    'away_team': prediction.away_team,
                    'prediction': prediction.prediction,
                    'confidence': prediction.confidence,
                    'recommended_odds': prediction.recommended_odds,
                    'value_score': prediction.value_score,
                    'league': getattr(prediction, 'league', 'Unknown League'),
                    'minute': getattr(prediction, 'minute', "0'"),
                    'score': getattr(prediction, 'score', '0-0')
                }
                
                await self.bot.send_prediction_alert(prediction_data)
                
            except Exception as e:
                logger.error(f"Failed to send prediction notification: {e}")
    
    async def run_continuous_monitoring(self, max_hours: int = 24):
        """
        Run continuous monitoring system
        
        Args:
            max_hours: Maximum hours to run (safety limit)
        """
        logger.info(f"🔄 Starting continuous monitoring (max {max_hours} hours)")
        
        max_runtime = timedelta(hours=max_hours)
        start_time = datetime.now()
        
        try:
            # Create tasks for different components
            tasks = [
                asyncio.create_task(self._continuous_research_loop()),
                asyncio.create_task(self._monitor_system_health()),
                asyncio.create_task(self._periodic_summary()),
            ]
            
            # Run until max runtime or cancellation
            try:
                await asyncio.wait_for(
                    asyncio.Event().wait(),
                    timeout=max_runtime.total_seconds()
                )
            except asyncio.TimeoutError:
                logger.info("⏰ Maximum runtime reached, stopping monitoring")
            
            # Cancel all tasks
            for task in tasks:
                task.cancel()
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"❌ Continuous monitoring error: {e}")
        
        finally:
            total_runtime = datetime.now() - start_time
            logger.info(f"🏁 Continuous monitoring completed: {total_runtime}")
    
    async def _continuous_research_loop(self):
        """Continuous research loop"""
        while self.is_running:
            try:
                # Run shorter research cycles continuously
                results = await self.run_research_cycle(duration_minutes=15)
                
                # Log results
                self.data_store.log_system_event(
                    'continuous_cycle_completed',
                    results
                )
                
                # Brief pause between cycles
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                logger.info("📊 Continuous research loop cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Continuous research loop error: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_system_health(self):
        """Monitor system health and performance"""
        while self.is_running:
            try:
                # Check system status
                risk_status = await self.risk_manager.get_risk_status()
                
                if risk_status['status'] == 'critical':
                    # Send critical alert
                    if self.bot and self.bot.config.enabled:
                        await self.bot.send_status_update({
                            'system_status': 'critical',
                            'uptime': 'N/A',
                            'predictions_today': self.stats['predictions_generated'],
                            'last_update': datetime.now().strftime('%H:%M:%S'),
                            'risk_factors': risk_status.get('active_limits', [])
                        })
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except asyncio.CancelledError:
                logger.info("💊 System health monitoring cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Health monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _periodic_summary(self):
        """Send periodic summaries"""
        while self.is_running:
            try:
                # Wait for 1 hour
                await asyncio.sleep(3600)
                
                if self.bot and self.bot.config.enabled:
                    # Generate hourly summary
                    summary = {
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'total_matches': self.stats['matches_analyzed'],
                        'predictions_made': self.stats['predictions_generated'],
                        'avg_confidence': self.stats.get('avg_confidence', 0.0),
                        'system_uptime': self.stats['system_uptime']
                    }
                    
                    await self.bot.send_daily_summary(summary)
                
            except asyncio.CancelledError:
                logger.info("📋 Periodic summary cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Periodic summary error: {e}")
                await asyncio.sleep(1800)  # Retry in 30 minutes
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up system resources...")
        
        try:
            if self.bot:
                await self.bot.stop()
            
            if self.scraper:
                await self.scraper.cleanup()
            
            if self.data_store:
                await self.data_store.cleanup_old_data()
            
            logger.info("✅ Cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'system': {
                'is_running': self.is_running,
                'uptime_minutes': (datetime.now() - self.start_time).total_seconds() / 60 if self.start_time else 0,
                'config_loaded': bool(self.config)
            },
            'components': {
                'scraper': bool(self.scraper),
                'predictor': bool(self.predictor),
                'bot': bool(self.bot and self.bot.config.enabled),
                'risk_manager': bool(self.risk_manager),
                'data_store': bool(self.data_store)
            },
            'statistics': self.stats.copy(),
            'research_mode': self.config.get('research_mode', True),
            'educational_purpose': True
        }

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Betfury.io Educational Research System")
    parser.add_argument('--mode', choices=['analyze', 'research', 'continuous'], 
                       default='analyze', help='Operation mode')
    parser.add_argument('--duration', type=int, default=60, 
                       help='Duration in minutes (for analyze/research modes)')
    parser.add_argument('--config', default='config/config.yaml',
                       help='Configuration file path')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("🎯 Betfury.io Educational Research System")
    logger.info("⚠️  FOR EDUCATIONAL PURPOSES ONLY")
    
    # Initialize system
    system = BetfuryResearchSystem(args.config)
    
    try:
        # Initialize components
        if not await system.initialize():
            logger.error("❌ System initialization failed")
            return 1
        
        # Run based on mode
        if args.mode == 'analyze':
            results = await system.run_research_cycle(args.duration)
            print(f"📊 Analysis completed: {results}")
            
        elif args.mode == 'research':
            results = await system.run_research_cycle(args.duration)
            print(f"🔬 Research completed: {results}")
            
        elif args.mode == 'continuous':
            await system.run_continuous_monitoring(max_hours=args.duration // 60)
        
        # Show final status
        status = system.get_system_status()
        print(f"🏁 Final status: {status}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        return 1
        
    finally:
        await system.cleanup()

if __name__ == "__main__":
    # Run the system
    exit_code = asyncio.run(main())
    sys.exit(exit_code)