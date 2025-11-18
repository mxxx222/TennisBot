#!/usr/bin/env python3
"""
🚀 SMART VALUE DETECTOR - KÄYNNISTYS
===================================

Käynnistää Smart Value Detector -järjestelmän täydessä toiminnassa:
- Arvovetojen tunnistus
- Arbitraasi-seuranta
- Telegram-ilmoitukset
- Jatkuva seuranta

Author: TennisBot Advanced Analytics
Version: 1.0.0
"""

import asyncio
import os
import sys
import yaml
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.smart_value_detector import SmartValueDetector, MatchData, PlayerStats
from src.high_roi_scraper import HighROIScraper
from src.svd_telegram_bot import SVDTelegramBot

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/svd_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class SVDSystem:
    """
    Smart Value Detector -järjestelmän pääorkestraattori
    """
    
    def __init__(self, config_path: str = "config/svd_config.yaml"):
        """Initialize system"""
        self.config = self._load_config(config_path)
        svd_config = self.config.get('smart_value_detector', {})
        
        # Initialize components
        self.svd = SmartValueDetector(
            bankroll=svd_config.get('bankroll', {}).get('initial', 1000.0),
            config=svd_config
        )
        
        self.scraper = HighROIScraper(config=svd_config.get('scraping', {}))
        
        # Telegram bot (optional)
        self.telegram_bot = None
        if svd_config.get('telegram', {}).get('enabled', False):
            try:
                self.telegram_bot = SVDTelegramBot(svd=self.svd)
            except Exception as e:
                logger.warning(f"⚠️ Telegram bot not available: {e}")
        
        self.running = False
        
        logger.info("🎯 Smart Value Detector System initialized")
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration"""
        config_file = Path(config_path)
        
        if not config_file.exists():
            logger.warning(f"⚠️ Config file not found: {config_path}, using defaults")
            return {}
        
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    async def start(self):
        """Start the system"""
        logger.info("🚀 Starting Smart Value Detector System...")
        
        self.running = True
        
        # Start Telegram bot if enabled
        if self.telegram_bot:
            await self.telegram_bot.start_bot()
            logger.info("✅ Telegram bot started")
        
        # Main loop
        try:
            while self.running:
                await self._run_analysis_cycle()
                
                # Wait before next cycle
                interval = self.config.get('smart_value_detector', {}).get(
                    'market_analysis', {}
                ).get('odds_update_interval', 300)
                
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down...")
        finally:
            await self._shutdown()
    
    async def _run_analysis_cycle(self):
        """Run one analysis cycle"""
        logger.info("🔄 Running analysis cycle...")
        
        try:
            # 1. Get matches (from scraping or API)
            matches = await self._get_matches()
            
            if not matches:
                logger.warning("⚠️ No matches found")
                return
            
            logger.info(f"📊 Analyzing {len(matches)} matches")
            
            # 2. Scrape odds
            match_ids = [m.match_id for m in matches]
            all_odds = await self.scraper.scrape_all_bookmakers(match_ids)
            
            # 3. Update match data with odds
            for match in matches:
                if match.match_id in all_odds:
                    odds_list = all_odds[match.match_id]
                    if odds_list:
                        # Use best odds
                        best_player1 = max(odds_list, key=lambda x: x.player1_odds)
                        best_player2 = max(odds_list, key=lambda x: x.player2_odds)
                        
                        match.market_odds = {
                            'player1': best_player1.player1_odds,
                            'player2': best_player2.player2_odds,
                            'bookmaker': best_player1.bookmaker,
                            'sources': {
                                odds.bookmaker: {
                                    'player1': odds.player1_odds,
                                    'player2': odds.player2_odds
                                }
                                for odds in odds_list
                            }
                        }
            
            # 4. Find value trades
            value_trades = self.svd.find_value_trades(matches)
            
            logger.info(f"💰 Found {len(value_trades)} value trades")
            
            # 5. Send notifications
            if self.telegram_bot and value_trades:
                for trade in value_trades[:5]:  # Top 5
                    await self.telegram_bot.send_value_trade_notification(trade)
                    await asyncio.sleep(1)  # Rate limiting
            
            # 6. Check arbitrage
            aggregated_odds_list = []
            for match_id, odds_list in all_odds.items():
                if odds_list:
                    aggregated = self.scraper.aggregate_odds(match_id, odds_list)
                    aggregated_odds_list.append(aggregated)
            
            arbitrage_opps = self.scraper.find_arbitrage_opportunities(aggregated_odds_list)
            
            if arbitrage_opps and self.telegram_bot:
                for arb in arbitrage_opps[:3]:  # Top 3
                    await self.telegram_bot.send_arbitrage_notification(arb)
                    await asyncio.sleep(1)
            
            # 7. Save results
            if value_trades:
                self.svd.save_trades()
            
            logger.info("✅ Analysis cycle completed")
            
        except Exception as e:
            logger.error(f"❌ Error in analysis cycle: {e}", exc_info=True)
    
    async def _get_matches(self) -> list:
        """
        Hae ottelut käyttäen olemassa olevia data-lähteitä
        """
        try:
            from src.svd_data_integration import SVDDataIntegration
            
            integration = SVDDataIntegration()
            matches = await integration.get_tennis_matches()
            
            logger.info(f"📊 Retrieved {len(matches)} matches from data sources")
            
            return matches
            
        except Exception as e:
            logger.error(f"❌ Error getting matches: {e}")
            return []
    
    async def _shutdown(self):
        """Shutdown system"""
        logger.info("🛑 Shutting down system...")
        
        if self.telegram_bot:
            await self.telegram_bot.stop_bot()
        
        self.running = False
        
        logger.info("✅ System shut down")


def main():
    """Main function"""
    print("""
╔════════════════════════════════════════════════╗
║  🎯 SMART VALUE DETECTOR SYSTEM
║  ============================================
║
║  Laillinen rahanteko-kone
║  Tavoite: 15-30% kuukausi ROI
║
╚════════════════════════════════════════════════╝
    """)
    
    # Check environment
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("⚠️ Warning: TELEGRAM_BOT_TOKEN not set")
        print("   Telegram notifications will be disabled")
    
    # Create and start system
    system = SVDSystem()
    
    try:
        asyncio.run(system.start())
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")


if __name__ == "__main__":
    main()

