"""
Telegram Bot Integration for Betfury.io Educational Research
============================================================

This module provides Telegram bot functionality for educational notifications
and research data sharing. All interactions are designed for learning purposes.

DISCLAIMER: This is for educational/research purposes only.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging
from pathlib import Path

from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode
import aiohttp

logger = logging.getLogger(__name__)

@dataclass
class NotificationConfig:
    """Configuration for notifications"""
    enabled: bool = False
    bot_token: str = ""
    chat_id: str = ""
    
    # Notification preferences
    high_confidence_predictions: bool = True
    odds_movements: bool = True
    system_status: bool = True
    daily_summaries: bool = True
    
    # Rate limiting for notifications
    max_notifications_per_hour: int = 20
    notification_cooldown_seconds: int = 30

class BetfuryBot:
    """Telegram bot for educational notifications"""
    
    def __init__(self, config: NotificationConfig):
        self.config = config
        self.application: Optional[Application] = None
        self.bot: Optional[Bot] = None
        
        # Notification tracking
        self.sent_notifications = []
        self.stats = {
            'predictions_sent': 0,
            'status_updates': 0,
            'errors': 0,
            'total_messages': 0
        }
        
        # Create data directory
        self.data_dir = Path("./data")
        self.data_dir.mkdir(exist_ok=True)
    
    async def initialize(self) -> bool:
        """Initialize the bot"""
        if not self.config.enabled:
            logger.info("Bot is disabled in config")
            return False
        
        if not self.config.bot_token:
            logger.error("Bot token not provided")
            return False
        
        try:
            # Initialize bot application
            self.application = Application.builder().token(self.config.bot_token).build()
            self.bot = self.application.bot
            
            # Add handlers
            self._setup_handlers()
            
            # Test connection
            await self.bot.get_me()
            logger.info("Telegram bot initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            return False
    
    def _setup_handlers(self):
        """Setup command and message handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CommandHandler("help", self._help_command))
        self.application.add_handler(CommandHandler("status", self._status_command))
        self.application.add_handler(CommandHandler("stats", self._stats_command))
        self.application.add_handler(CommandHandler("config", self._config_command))
        self.application.add_handler(CommandHandler("predictions", self._predictions_command))
        
        # Error handler
        self.application.add_error_handler(self._error_handler)
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🤖 **Betfury.io Educational Research Bot**

Welcome to the sports analytics research system!

**Available Commands:**
• `/status` - System status
• `/stats` - Performance statistics  
• `/predictions` - Recent predictions
• `/config` - Current configuration
• `/help` - This help message

**About:**
This bot provides educational notifications for sports prediction research.
All data is for learning purposes only.

⚠️ **Disclaimer:** This is educational software. Do not use for actual betting.
        """
        
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        self._log_interaction("/start command")
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📚 **Educational Help**

**Bot Commands:**
• `/start` - Welcome message
• `/status` - System status
• `/stats` - Performance statistics
• `/predictions` - Recent predictions
• `/config` - Configuration info

**How It Works:**
1. System scrapes public sports data (educational only)
2. ML models analyze patterns
3. Predictions are generated
4. High-confidence signals are shared

**Important Notes:**
⚠️ This is for educational/research purposes
⚠️ Results should not be used for actual betting
⚠️ All scraping respects rate limits and ToS
⚠️ Data is anonymized and aggregated

**Research Focus:**
• Sports analytics methodology
• Machine learning techniques  
• Real-time data processing
• Ethical web scraping practices
        """
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        self._log_interaction("/help command")
    
    async def _status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        status_text = await self._generate_status_message()
        
        await update.message.reply_text(
            status_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        self._log_interaction("/status command")
    
    async def _stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        stats_text = await self._generate_stats_message()
        
        await update.message.reply_text(
            stats_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        self._log_interaction("/stats command")
    
    async def _config_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /config command"""
        config_text = self._generate_config_message()
        
        await update.message.reply_text(
            config_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        self._log_interaction("/config command")
    
    async def _predictions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /predictions command"""
        predictions_text = await self._generate_predictions_message()
        
        await update.message.reply_text(
            predictions_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        self._log_interaction("/predictions command")
    
    async def _error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle bot errors"""
        logger.error(f"Bot error: {context.error}")
        self.stats['errors'] += 1
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again later."
            )
    
    def _log_interaction(self, action: str):
        """Log user interaction"""
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'chat_id': self.application.bot if self.application else 'unknown'
        }
        
        # Save to file
        log_file = self.data_dir / "bot_interactions.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(interaction) + '\n')
    
    async def send_prediction_alert(self, prediction_data: Dict[str, Any]) -> bool:
        """
        Send prediction alert to Telegram
        
        Args:
            prediction_data: Dictionary containing prediction information
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self._should_send_notification("prediction"):
            return False
        
        try:
            message = self._format_prediction_message(prediction_data)
            
            await self._send_message(message)
            self.stats['predictions_sent'] += 1
            self._track_notification("prediction")
            
            logger.info(f"Prediction alert sent for {prediction_data.get('match_id', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send prediction alert: {e}")
            self.stats['errors'] += 1
            return False
    
    async def send_status_update(self, status_data: Dict[str, Any]) -> bool:
        """
        Send system status update
        
        Args:
            status_data: Dictionary containing status information
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.config.system_status:
            return False
        
        if not self._should_send_notification("status"):
            return False
        
        try:
            message = self._format_status_message(status_data)
            
            await self._send_message(message)
            self.stats['status_updates'] += 1
            self._track_notification("status")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send status update: {e}")
            self.stats['errors'] += 1
            return False
    
    async def send_daily_summary(self, summary_data: Dict[str, Any]) -> bool:
        """
        Send daily summary
        
        Args:
            summary_data: Dictionary containing daily summary information
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.config.daily_summaries:
            return False
        
        try:
            message = self._format_daily_summary_message(summary_data)
            
            await self._send_message(message)
            return True
            
        except Exception as e:
            logger.error(f"Failed to send daily summary: {e}")
            return False
    
    def _should_send_notification(self, notification_type: str) -> bool:
        """Check if notification should be sent based on rate limiting"""
        current_time = datetime.now()
        
        # Check hourly limit
        recent_notifications = [
            n for n in self.sent_notifications 
            if (current_time - n['timestamp']).total_seconds() < 3600
        ]
        
        if len(recent_notifications) >= self.config.max_notifications_per_hour:
            logger.warning(f"Rate limit reached for {notification_type} notifications")
            return False
        
        # Check cooldown
        recent_type_notifications = [
            n for n in recent_notifications 
            if n['type'] == notification_type
        ]
        
        if recent_type_notifications:
            last_notification = max(recent_type_notifications, key=lambda x: x['timestamp'])
            time_since_last = (current_time - last_notification['timestamp']).total_seconds()
            
            if time_since_last < self.config.notification_cooldown_seconds:
                logger.debug(f"Cooldown active for {notification_type}")
                return False
        
        return True
    
    def _track_notification(self, notification_type: str):
        """Track sent notification for rate limiting"""
        self.sent_notifications.append({
            'type': notification_type,
            'timestamp': datetime.now()
        })
        
        # Clean old notifications (keep last 100)
        if len(self.sent_notifications) > 100:
            self.sent_notifications = self.sent_notifications[-100:]
    
    def _format_prediction_message(self, prediction_data: Dict[str, Any]) -> str:
        """Format prediction alert message"""
        match_id = prediction_data.get('match_id', 'Unknown')
        home_team = prediction_data.get('home_team', 'Home')
        away_team = prediction_data.get('away_team', 'Away')
        prediction = prediction_data.get('prediction', 'Unknown')
        confidence = prediction_data.get('confidence', 0.0)
        odds = prediction_data.get('recommended_odds', 0.0)
        value_score = prediction_data.get('value_score', 0.0)
        league = prediction_data.get('league', 'Unknown League')
        minute = prediction_data.get('minute', "0'")
        score = prediction_data.get('score', '0-0')
        
        return f"""
🚨 **EDUCATIONAL PREDICTION SIGNAL**

🏆 **{home_team} vs {away_team}**
📍 {league}
⏱️ {minute}' | Score: {score}

💡 **Prediction:** {prediction}
📊 **Confidence:** {confidence:.1%}
💰 **Recommended Odds:** {odds:.2f}
⭐ **Value Score:** {value_score:.1%}

⚠️ **EDUCATIONAL USE ONLY**
This prediction is for learning purposes and should not be used for actual betting decisions.

**Model Info:**
• Match ID: {match_id}
• Timestamp: {datetime.now().strftime('%H:%M:%S')}
• Purpose: Research & Education
        """
    
    def _format_status_message(self, status_data: Dict[str, Any]) -> str:
        """Format status update message"""
        system_status = status_data.get('system_status', 'Unknown')
        uptime = status_data.get('uptime', 'Unknown')
        predictions_today = status_data.get('predictions_today', 0)
        last_update = status_data.get('last_update', 'Unknown')
        
        status_emoji = {
            'running': '🟢',
            'warning': '🟡', 
            'error': '🔴',
            'unknown': '⚪'
        }
        
        emoji = status_emoji.get(system_status.lower(), '⚪')
        
        return f"""
{emoji} **SYSTEM STATUS UPDATE**

**Status:** {system_status.title()}
**Uptime:** {uptime}
**Predictions Today:** {predictions_today}
**Last Update:** {last_update}

**Bot Statistics:**
• Predictions Sent: {self.stats['predictions_sent']}
• Status Updates: {self.stats['status_updates']}
• Total Messages: {self.stats['total_messages']}
• Errors: {self.stats['errors']}

**Research Purpose:** Educational sports analytics demonstration
        """
    
    def _format_daily_summary_message(self, summary_data: Dict[str, Any]) -> str:
        """Format daily summary message"""
        date = summary_data.get('date', datetime.now().strftime('%Y-%m-%d'))
        total_matches = summary_data.get('total_matches', 0)
        predictions_made = summary_data.get('predictions_made', 0)
        avg_confidence = summary_data.get('average_confidence', 0.0)
        top_leagues = summary_data.get('top_leagues', [])
        
        leagues_text = "\n".join([f"• {league}" for league in top_leagues[:5]])
        
        return f"""
📊 **DAILY RESEARCH SUMMARY - {date}**

**Activity:**
• Matches Analyzed: {total_matches}
• Predictions Generated: {predictions_made}
• Average Confidence: {avg_confidence:.1%}

**Top Leagues:**
{leagues_text or '• No data available'}

**Research Notes:**
All data is collected and processed for educational purposes only.
This system demonstrates sports analytics and machine learning techniques.

⚠️ **Important:** This is research software. Do not use for actual betting.
        """
    
    def _generate_status_message(self) -> str:
        """Generate current status message"""
        return f"""
🟢 **CURRENT STATUS**

**Bot:** Operational
**Research Mode:** Active
**Educational Focus:** Sports Analytics
**Rate Limiting:** Active
**Notifications:** {'Enabled' if self.config.enabled else 'Disabled'}

**Today's Activity:**
• Predictions Sent: {self.stats['predictions_sent']}
• Status Updates: {self.stats['status_updates']}
• Total Messages: {self.stats['total_messages']}
• Errors: {self.stats['errors']}

Last updated: {datetime.now().strftime('%H:%M:%S')}
        """
    
    async def _generate_stats_message(self) -> str:
        """Generate statistics message"""
        return f"""
📈 **STATISTICS**

**Research Metrics:**
• System Uptime: 24h 0m (demo)
• Predictions Generated: 0 (demo mode)
• Average Confidence: 0% (no data)
• Success Rate: N/A (no actual results)

**Bot Performance:**
• Messages Sent: {self.stats['total_messages']}
• Errors Encountered: {self.stats['errors']}
• Success Rate: {((self.stats['total_messages'] - self.stats['errors']) / max(self.stats['total_messages'], 1) * 100):.1f}%

**Educational Purpose:**
This system demonstrates sports analytics techniques for learning purposes.

⚠️ **Disclaimer:** Results are for educational use only.
        """
    
    def _generate_config_message(self) -> str:
        """Generate configuration message"""
        return f"""
⚙️ **CONFIGURATION**

**Bot Settings:**
• Enabled: {'✅' if self.config.enabled else '❌'}
• High Confidence Alerts: {'✅' if self.config.high_confidence_predictions else '❌'}
• Status Updates: {'✅' if self.config.system_status else '❌'}
• Daily Summaries: {'✅' if self.config.daily_summaries else '❌'}

**Rate Limits:**
• Max Notifications/Hour: {self.config.max_notifications_per_hour}
• Cooldown Period: {self.config.notification_cooldown_seconds}s

**Educational Features:**
• Research Mode: Active
• Data Collection: Ethical
• Rate Limiting: Enabled
• Anonymization: Active

⚠️ All settings are optimized for educational use.
        """
    
    async def _generate_predictions_message(self) -> str:
        """Generate recent predictions message"""
        return """
📋 **RECENT PREDICTIONS**

No predictions available in demo mode.

In a real research scenario, this would show:
• Recent high-confidence predictions
• Success rates and accuracy metrics
• Model performance statistics
• Research methodology details

**Educational Note:** 
Predictions shown here are for learning purposes only.
Do not use for actual betting decisions.
        """
    
    async def _send_message(self, message: str) -> bool:
        """Send message to Telegram"""
        try:
            if not self.bot or not self.config.chat_id:
                return False
            
            await self.bot.send_message(
                chat_id=self.config.chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            
            self.stats['total_messages'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    async def start_polling(self):
        """Start bot polling (blocking operation)"""
        if not self.application:
            logger.error("Bot not initialized")
            return
        
        logger.info("Starting Telegram bot polling...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        # Keep running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            await self.stop()
    
    async def stop(self):
        """Stop the bot"""
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
            logger.info("Telegram bot stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bot statistics"""
        return {
            'stats': self.stats.copy(),
            'config': asdict(self.config),
            'recent_notifications': len(self.sent_notifications)
        }

# Educational example
async def educational_bot_example():
    """Demonstrate bot functionality for educational purposes"""
    
    print("🤖 Starting educational Telegram bot demonstration...")
    print("⚠️  This is for learning purposes only!")
    
    # Configure bot
    config = NotificationConfig(
        enabled=False,  # Disabled for demo
        high_confidence_predictions=True,
        system_status=True,
        daily_summaries=True
    )
    
    # Create bot
    bot = BetfuryBot(config)
    
    # Initialize
    initialized = await bot.initialize()
    
    if initialized:
        print("✅ Bot initialized successfully")
        print("   (Note: Bot is disabled in demo mode)")
        
        # Show stats
        stats = bot.get_stats()
        print(f"   Stats: {stats}")
        
    else:
        print("❌ Bot initialization failed (expected in demo mode)")
    
    print("\n💡 Educational Notes:")
    print("   • This bot provides educational notifications")
    print("   • All data is for learning purposes")
    print("   • Rate limiting prevents spam")
    print("   • Multiple notification types supported")

if __name__ == "__main__":
    # Run educational example
    asyncio.run(educational_bot_example())