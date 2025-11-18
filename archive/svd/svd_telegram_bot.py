#!/usr/bin/env python3
"""
📱 SMART VALUE DETECTOR - TELEGRAM BOT
======================================

Telegram-bot joka lähettää ilmoituksia arvovetoista ja arbitraasi-mahdollisuuksista.

Author: TennisBot Advanced Analytics
Version: 1.0.0
"""

import asyncio
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

try:
    from telegram import Bot, Update
    from telegram.ext import Application, CommandHandler, ContextTypes
except ImportError:
    print("⚠️ python-telegram-bot not installed. Install with: pip install python-telegram-bot")
    Bot = None
    Update = None
    Application = None

from src.smart_value_detector import SmartValueDetector, ValueTrade
from src.high_roi_scraper import HighROIScraper, AggregatedOdds

logger = logging.getLogger(__name__)


class SVDTelegramBot:
    """
    Telegram bot Smart Value Detectorille
    """
    
    def __init__(self, bot_token: Optional[str] = None, 
                 chat_id: Optional[str] = None,
                 svd: Optional[SmartValueDetector] = None):
        """
        Initialize Telegram bot
        
        Args:
            bot_token: Telegram bot token
            chat_id: Chat ID for notifications
            svd: SmartValueDetector instance
        """
        if Bot is None:
            raise ImportError("python-telegram-bot not installed")
        
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.bot_token:
            raise ValueError("Bot token required")
        
        self.svd = svd or SmartValueDetector()
        self.scraper = HighROIScraper()
        
        self.application = None
        self.running = False
        
        logger.info("📱 SVD Telegram Bot initialized")
    
    async def start_bot(self):
        """Start the bot"""
        if not self.application:
            self.application = Application.builder().token(self.bot_token).build()
            
            # Add command handlers
            self.application.add_handler(CommandHandler("start", self._start_command))
            self.application.add_handler(CommandHandler("help", self._help_command))
            self.application.add_handler(CommandHandler("trades", self._trades_command))
            self.application.add_handler(CommandHandler("report", self._report_command))
            self.application.add_handler(CommandHandler("status", self._status_command))
        
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        self.running = True
        logger.info("✅ Telegram bot started")
    
    async def stop_bot(self):
        """Stop the bot"""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
        
        self.running = False
        logger.info("🛑 Telegram bot stopped")
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        message = """
🎯 **Smart Value Detector Bot**

Tervetuloa! Tämä botti lähettää sinulle ilmoituksia:
• 💰 Arvovetoista (value bets)
• 🔄 Arbitraasi-mahdollisuuksista
• 📊 Päivittäisistä raporteista

**Komennot:**
/help - Näytä kaikki komennot
/trades - Näytä viimeisimmät trade-suositukset
/report - Päivittäinen raportti
/status - Botin tila

**Automaattiset ilmoitukset:**
Botti lähettää automaattisesti ilmoituksia kun löytyy:
• Edge > 5%
• Arbitraasi > 2%
• Korkea luottamus (>75%)
        """
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        message = """
📖 **Käytettävissä olevat komennot:**

/start - Aloita käyttö
/help - Näytä tämä ohje
/trades - Näytä viimeisimmät trade-suositukset
/report - Päivittäinen raportti
/status - Botin tila ja tilastot

**Miten se toimii:**
1. Bot skannaa otteluita jatkuvasti
2. Etsii arvovetoja tilastollisen analyysin avulla
3. Lähettää ilmoituksia kun löytyy hyviä mahdollisuuksia
4. Käyttää Kelly Criterion -panoksen optimointia

**Tavoite:** 15-30% kuukausi ROI konservatiivisella riskinhallinnalla
        """
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def _trades_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /trades command"""
        # Get recent trades
        recent_trades = self.svd.trades[-10:] if self.svd.trades else []
        
        if not recent_trades:
            await update.message.reply_text("❌ Ei tradeja vielä. Odota kunnes löytyy arvovetoja.")
            return
        
        message = "💰 **Viimeisimmät Trade-suositukset:**\n\n"
        
        for i, trade_data in enumerate(recent_trades[-5:], 1):
            trade = trade_data.get('trade', {})
            message += f"**{i}. {trade.get('match_name', 'Unknown')}**\n"
            message += f"Pelaaja: {trade.get('player', 'Unknown')}\n"
            message += f"Kertoimet: {trade.get('odds', 0):.2f}\n"
            message += f"Edge: {trade.get('edge_percentage', 0):.1f}%\n"
            message += f"Suosituspanos: €{trade.get('recommended_stake', 0):.2f}\n"
            message += f"Odotusarvo: €{trade.get('expected_profit', 0):.2f}\n"
            message += f"Luottamus: {trade.get('confidence_level', 'Unknown')}\n\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def _report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /report command"""
        report = self.svd.generate_daily_report()
        await update.message.reply_text(f"```{report}```", parse_mode='Markdown')
    
    async def _status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        status = f"""
📊 **Botin Tila**

✅ Tila: Aktiivinen
💰 Pankkisaldo: €{self.svd.bankroll:,.2f}
📈 Tradeja: {len(self.svd.trades)}
🔄 Seuranta: Aktiivinen

**Asetukset:**
• Min Edge: {self.svd.min_edge*100:.1f}%
• Min Luottamus: {self.svd.min_confidence*100:.0f}%
• Kelly Fraction: {self.svd.kelly_fraction*100:.0f}%
        """
        
        await update.message.reply_text(status, parse_mode='Markdown')
    
    async def send_value_trade_notification(self, trade: ValueTrade):
        """
        Lähetä ilmoitus arvovedosta
        """
        if not self.chat_id:
            logger.warning("No chat ID configured")
            return
        
        message = f"""
💰 **UUSI ARVOVETO LÖYTYI!**

🎾 **Ottelu:** {trade.match_name}
👤 **Pelaaja:** {trade.player}
📊 **Kertoimet:** {trade.odds:.2f} ({trade.bookmaker})

**Analyysi:**
• Todellinen tn: {trade.true_probability*100:.1f}%
• Markkinoiden tn: {trade.market_probability*100:.1f}%
• Edge: {trade.edge_percentage:.1f}%
• Odotusarvo: {trade.expected_value_percentage:.1f}%

**Suositus:**
• Panos: €{trade.recommended_stake:.2f}
• Odotettu voitto: €{trade.expected_profit:.2f}
• Luottamus: {trade.confidence_level}
• Riskiscore: {trade.risk_score:.2f}

{'🔄 Arbitraasi saatavilla!' if trade.arbitrage_available else ''}
        """
        
        try:
            bot = Bot(token=self.bot_token)
            await bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
            logger.info(f"✅ Sent value trade notification: {trade.match_name}")
        except Exception as e:
            logger.error(f"❌ Error sending notification: {e}")
    
    async def send_arbitrage_notification(self, aggregated_odds: AggregatedOdds):
        """
        Lähetä ilmoitus arbitraasi-mahdollisuudesta
        """
        if not self.chat_id:
            return
        
        message = f"""
🔄 **RISKITÖN ARBITRAASI LÖYTYI!**

🎾 **Ottelu:** {aggregated_odds.match_name}

**Parhaat kertoimet:**
• Pelaaja 1: {aggregated_odds.best_player1_odds:.2f} ({aggregated_odds.best_player1_bookmaker})
• Pelaaja 2: {aggregated_odds.best_player2_odds:.2f} ({aggregated_odds.best_player2_bookmaker})

**Arbitraasi:**
• Multiplier: {aggregated_odds.arbitrage_multiplier:.4f}
• Voitto: {aggregated_odds.arbitrage_profit_pct:.2f}%
• Riskitön: ✅

**Ohje:**
Panosta molempiin pelaajiin suhteessa kertoimien käänteislukuihin.
        """
        
        try:
            bot = Bot(token=self.bot_token)
            await bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
            logger.info(f"✅ Sent arbitrage notification: {aggregated_odds.match_name}")
        except Exception as e:
            logger.error(f"❌ Error sending arbitrage notification: {e}")
    
    async def send_daily_report(self):
        """Lähetä päivittäinen raportti"""
        if not self.chat_id:
            return
        
        report = self.svd.generate_daily_report()
        
        try:
            bot = Bot(token=self.bot_token)
            await bot.send_message(
                chat_id=self.chat_id,
                text=f"```{report}```",
                parse_mode='Markdown'
            )
            logger.info("✅ Sent daily report")
        except Exception as e:
            logger.error(f"❌ Error sending daily report: {e}")
    
    async def continuous_monitoring(self, matches: List, interval_seconds: int = 300):
        """
        Jatkuva seuranta ja ilmoitukset
        """
        logger.info("🔄 Starting continuous monitoring")
        
        while self.running:
            try:
                # Find value trades
                value_trades = self.svd.find_value_trades(matches)
                
                # Send notifications for high-value trades
                for trade in value_trades[:5]:  # Top 5
                    if trade.expected_value_percentage > 10:  # >10% EV
                        await self.send_value_trade_notification(trade)
                        await asyncio.sleep(1)  # Rate limiting
                
                # Check for arbitrage
                match_ids = [m.match_id for m in matches]
                all_odds = await self.scraper.scrape_all_bookmakers(match_ids)
                
                for match_id, odds_list in all_odds.items():
                    if odds_list:
                        aggregated = self.scraper.aggregate_odds(match_id, odds_list)
                        if aggregated.has_arbitrage:
                            await self.send_arbitrage_notification(aggregated)
                            await asyncio.sleep(1)
                
                # Wait before next iteration
                await asyncio.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("🛑 Stopping continuous monitoring")
                break
            except Exception as e:
                logger.error(f"❌ Error in continuous monitoring: {e}")
                await asyncio.sleep(interval_seconds)


if __name__ == "__main__":
    print("📱 SVD Telegram Bot - Test")
    print("=" * 50)
    print("✅ Bot module ready for use")
    print("\nTo start the bot:")
    print("1. Set TELEGRAM_BOT_TOKEN environment variable")
    print("2. Set TELEGRAM_CHAT_ID environment variable")
    print("3. Run: python start_svd_system.py")

