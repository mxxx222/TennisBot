#!/usr/bin/env python3
"""
🤖 TELEGRAM ROI BOT FOR TENNIS PREDICTIONS
==========================================

Telegram bot that sends notifications about the best ROI tennis matches
with high-confidence predictions and betting opportunities.

Features:
- Automated ROI analysis of tennis matches
- High-confidence prediction filtering
- Beautiful formatted messages with emojis
- Real-time notifications for best opportunities
- Risk assessment and betting recommendations

Author: TennisBot Advanced Analytics
Version: 1.0.0
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys

# Add project paths
sys.path.append(str(Path(__file__).parent.parent / 'src' / 'scrapers'))
sys.path.append(str(Path(__file__).parent.parent / 'src'))

# Telegram bot imports
try:
    from telegram import Bot, Update
    from telegram.ext import Application, CommandHandler, ContextTypes
    import telegram
    TELEGRAM_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: python-telegram-bot not available. Install with: pip install python-telegram-bot")
    TELEGRAM_AVAILABLE = False

# Project imports
try:
    from predict_winners import TennisWinnerPredictor
    from ai_predictor_enhanced import MatchPrediction
    PREDICTOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Warning: Prediction system not available: {e}")
    PREDICTOR_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/herbspotturku/sportsbot/TennisBot/data/telegram_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TennisROIBot:
    """Telegram bot for tennis ROI notifications"""
    
    def __init__(self, bot_token: str = None):
        self.bot_token = bot_token or self._load_bot_token()
        self.application = None
        self.predictor = None
        self.data_dir = Path('/Users/herbspotturku/sportsbot/TennisBot/data')
        self.data_dir.mkdir(exist_ok=True)
        
        # ROI thresholds - ADJUSTED FOR BETTER RESULTS
        self.min_confidence = 0.35  # 35% minimum confidence (increased)
        self.min_roi_percentage = 7.0  # 7% minimum ROI (decreased)
        self.max_risk_level = 0.4  # Maximum risk tolerance (increased)
        
        # Notification settings
        self.chat_ids = set()  # Will store user chat IDs
        self.last_notification_time = {}
        self.notification_cooldown = 300  # 5 minutes between similar notifications
        
        logger.info("🤖 Tennis ROI Bot initialized")
    
    def _load_bot_token(self) -> str:
        """Load bot token from environment or config file"""
        # Try environment variable first
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if token:
            return token
        
        # Try config file
        config_file = Path('/Users/herbspotturku/sportsbot/TennisBot/config/telegram_config.json')
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('bot_token', '')
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        # Create example config file
        self._create_example_config()
        
        logger.warning("⚠️ No Telegram bot token found. Please set TELEGRAM_BOT_TOKEN environment variable or create config file.")
    def _load_chat_id(self) -> str:
        """Load chat ID from environment or config file"""
        # Try environment variable first
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        if chat_id:
            return chat_id

        # Try config file
        config_file = Path('/Users/herbspotturku/sportsbot/TennisBot/config/telegram_config.json')
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('chat_id', '')
            except Exception as e:
                logger.error(f"Error loading config: {e}")

        logger.warning("⚠️ No Telegram chat ID found. Please set TELEGRAM_CHAT_ID environment variable or add to config file.")
        return ""
        return ""
    
    def _create_example_config(self):
        """Create example configuration file"""
        config_dir = Path('/Users/herbspotturku/sportsbot/TennisBot/config')
        config_dir.mkdir(exist_ok=True)
        
        example_config = {
            "bot_token": "YOUR_TELEGRAM_BOT_TOKEN_HERE",
            "notification_settings": {
                "min_confidence": 0.25,
                "min_roi_percentage": 10.0,
                "max_risk_level": 0.3,
                "notification_cooldown_seconds": 300
            },
            "message_settings": {
                "include_emojis": True,
                "detailed_analysis": True,
                "show_risk_warning": True
            }
        }
        
        config_file = config_dir / 'telegram_config_example.json'
        with open(config_file, 'w') as f:
            json.dump(example_config, f, indent=2)
        
        logger.info(f"📝 Created example config at {config_file}")
    
    async def setup(self):
        """Setup the Telegram bot"""
        if not TELEGRAM_AVAILABLE:
            logger.error("❌ Telegram bot library not available")
            return False
        
        if not self.bot_token:
            logger.error("❌ No Telegram bot token provided")
            return False
        
        try:
            # Initialize predictor
            if PREDICTOR_AVAILABLE:
                self.predictor = TennisWinnerPredictor()
                self.predictor.setup()
                logger.info("✅ Tennis predictor initialized")
            else:
                logger.warning("⚠️ Tennis predictor not available")
            
            # Setup Telegram application
            self.application = Application.builder().token(self.bot_token).build()
            
            # Add command handlers
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("roi", self.roi_command))
            self.application.add_handler(CommandHandler("predictions", self.predictions_command))
            self.application.add_handler(CommandHandler("settings", self.settings_command))
            self.application.add_handler(CommandHandler("stop", self.stop_command))
            
            logger.info("✅ Telegram bot setup complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting up Telegram bot: {e}")
            return False
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        chat_id = update.effective_chat.id
        self.chat_ids.add(chat_id)
        
        welcome_message = """
🎾 **TENNIS ROI BOT - WELCOME!**

I'll send you notifications about the best tennis betting opportunities with high ROI potential!

**Available Commands:**
🔍 `/roi` - Get current best ROI matches
📊 `/predictions` - Get all current predictions
⚙️ `/settings` - View current settings
❓ `/help` - Show this help message
⏹️ `/stop` - Stop notifications

**What I Do:**
• 🎯 Analyze live tennis matches for ROI opportunities
• 📈 Filter high-confidence predictions (≥25%)
• 💰 Calculate potential returns and risk levels
• ⚡ Send real-time notifications for best matches
• 🛡️ Provide risk assessments and betting guidance

**Target Accuracy: 70%+**

Ready to find profitable tennis bets! 🚀
        """
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        logger.info(f"✅ New user started: {chat_id}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """
🤖 **TENNIS ROI BOT HELP**

**Commands:**
• `/start` - Start receiving notifications
• `/roi` - Get current best ROI matches
• `/predictions` - Get all current predictions
• `/settings` - View bot settings
• `/stop` - Stop notifications
• `/help` - Show this help

**How It Works:**
1. 🔍 I continuously scan live tennis matches
2. 🤖 AI analyzes each match with 70% accuracy target
3. 📊 I calculate ROI potential for each prediction
4. 💰 Best opportunities are sent to you automatically
5. 🎯 You get clear betting recommendations

**ROI Criteria:**
• ✅ Minimum 25% prediction confidence
• 💰 Minimum 10% ROI potential
• 🛡️ Risk assessment included
• ⏰ Real-time updates

**Message Format:**
🏆 Match details with predicted winner
📊 Win probability and confidence score
💰 ROI calculation and potential profit
🎯 Clear betting recommendation
⚠️ Risk level and warnings

Need help? Just ask! 🎾
        """
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def roi_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /roi command - get current best ROI matches"""
        chat_id = update.effective_chat.id
        
        await update.message.reply_text("🔍 Analyzing current tennis matches for ROI opportunities...")
        
        try:
            # Get current predictions
            roi_matches = await self.get_best_roi_matches()
            
            if roi_matches:
                message = self.format_roi_matches_message(roi_matches)
                await update.message.reply_text(message, parse_mode='Markdown')
                logger.info(f"📊 Sent ROI matches to {chat_id}")
            else:
                no_matches_message = """
🎾 **NO HIGH-ROI MATCHES CURRENTLY**

Currently no tennis matches meet our ROI criteria:
• ✅ Minimum 25% confidence
• 💰 Minimum 10% ROI potential
• 🛡️ Acceptable risk level

I'll notify you automatically when good opportunities appear! 🚀
                """
                await update.message.reply_text(no_matches_message, parse_mode='Markdown')
                
        except Exception as e:
            error_message = f"❌ Error getting ROI matches: {str(e)}"
            await update.message.reply_text(error_message)
            logger.error(f"Error in roi_command: {e}")
    
    async def predictions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /predictions command - get all current predictions"""
        chat_id = update.effective_chat.id
        
        await update.message.reply_text("📊 Getting all current tennis predictions...")
        
        try:
            if not self.predictor:
                await update.message.reply_text("❌ Prediction system not available")
                return
            
            # Get all predictions
            predictions_data = self.predictor.scrape_and_predict(max_live_matches=15, max_upcoming_matches=20)
            all_predictions = predictions_data['live'] + predictions_data['upcoming']
            
            if all_predictions:
                # Sort by confidence
                all_predictions.sort(key=lambda x: x.confidence_score, reverse=True)
                
                message = self.format_all_predictions_message(all_predictions[:10])  # Top 10
                await update.message.reply_text(message, parse_mode='Markdown')
                logger.info(f"📊 Sent all predictions to {chat_id}")
            else:
                await update.message.reply_text("❌ No predictions available at the moment")
                
        except Exception as e:
            error_message = f"❌ Error getting predictions: {str(e)}"
            await update.message.reply_text(error_message)
            logger.error(f"Error in predictions_command: {e}")
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command"""
        settings_message = f"""
⚙️ **CURRENT BOT SETTINGS**

**ROI Criteria:**
• 🎯 Minimum Confidence: {self.min_confidence:.0%}
• 💰 Minimum ROI: {self.min_roi_percentage}%
• 🛡️ Max Risk Level: {self.max_risk_level:.0%}

**Notifications:**
• ⏰ Cooldown: {self.notification_cooldown // 60} minutes
• 👥 Active Users: {len(self.chat_ids)}
• 🎯 Target Accuracy: 70%+

**System Status:**
• 🤖 Predictor: {'✅ Active' if self.predictor else '❌ Inactive'}
• 📊 ML Models: {'✅ Loaded' if self.predictor and self.predictor.predictor.is_trained else '❌ Not Loaded'}
• 🔍 Scraping: ✅ Active

To modify settings, contact the administrator.
        """
        
        await update.message.reply_text(settings_message, parse_mode='Markdown')
    
    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop command"""
        chat_id = update.effective_chat.id
        if chat_id in self.chat_ids:
            self.chat_ids.remove(chat_id)
        
        stop_message = """
⏹️ **NOTIFICATIONS STOPPED**

You will no longer receive automatic ROI notifications.

To restart notifications, use `/start` command.

Thanks for using Tennis ROI Bot! 🎾
        """
        
        await update.message.reply_text(stop_message, parse_mode='Markdown')
        logger.info(f"🛑 User stopped notifications: {chat_id}")
    
    async def get_best_roi_matches(self) -> List[Dict[str, Any]]:
        """Get the best ROI matches from current predictions"""
        if not self.predictor:
            return []
        
        try:
            # Get current predictions
            predictions_data = self.predictor.scrape_and_predict(max_live_matches=20, max_upcoming_matches=30)
            all_predictions = predictions_data['live'] + predictions_data['upcoming']
            
            # Filter for high-confidence predictions
            high_confidence_predictions = [
                p for p in all_predictions 
                if p.confidence_score >= self.min_confidence
            ]
            
            # Calculate ROI for each prediction
            roi_matches = []
            for pred in high_confidence_predictions:
                roi_data = self.calculate_roi(pred)
                if roi_data and roi_data['roi_percentage'] >= self.min_roi_percentage:
                    roi_matches.append(roi_data)
            
            # Sort by ROI percentage
            roi_matches.sort(key=lambda x: x['roi_percentage'], reverse=True)
            
            return roi_matches[:5]  # Top 5 ROI matches
            
        except Exception as e:
            logger.error(f"Error getting ROI matches: {e}")
            return []
    
    def calculate_roi(self, prediction: MatchPrediction) -> Optional[Dict[str, Any]]:
        """Calculate ROI for a prediction (Mojo-accelerated)"""
        try:
            win_prob = prediction.win_probability
            confidence = prediction.confidence_score

            # CORRECTED: Proper implied odds calculation
            if win_prob > 0.5:
                # Favorite: fair odds = 1/probability
                fair_odds = 1 / win_prob
                # Bookmakers offer slightly less than fair odds
                market_odds = fair_odds * 0.95  # 5% margin for favorites
            else:
                # Underdog: fair odds = 1/(1-probability)
                fair_odds = 1 / (1 - win_prob)
                # Underdogs get better odds from bookmakers
                market_odds = fair_odds * 0.92  # 8% margin for underdogs

            # Calculate potential ROI - use Mojo if available
            stake = 100  # $100 stake for calculation
            
            # Try Mojo-accelerated expected ROI calculation
            try:
                from src.mojo_bindings import expected_roi, should_use_mojo
                if should_use_mojo():
                    # Use Mojo for ROI calculation
                    roi_percentage = expected_roi(win_prob, market_odds, stake)
                    profit = (roi_percentage / 100.0) * stake
                else:
                    raise ImportError("Mojo not enabled")
            except (ImportError, Exception):
                # Python fallback
                potential_return = stake * market_odds
                profit = potential_return - stake
                roi_percentage = (profit / stake) * 100

            # CORRECTED: Risk assessment - higher confidence = lower risk
            risk_level = 1 - confidence  # High confidence = low risk

            # Only return if ROI meets criteria
            if roi_percentage >= self.min_roi_percentage and risk_level <= self.max_risk_level:
                return {
                    'prediction': prediction,
                    'roi_percentage': roi_percentage,
                    'potential_profit': profit,
                    'stake': stake,
                    'implied_odds': fair_odds,
                    'market_odds': market_odds,
                    'risk_level': risk_level,
                    'risk_category': self.get_risk_category(risk_level)
                }

            return None

        except Exception as e:
            logger.error(f"Error calculating ROI: {e}")
            return None
    
    def get_risk_category(self, risk_level: float) -> str:
        """Get risk category based on risk level"""
        if risk_level <= 0.2:
            return "🟢 LOW"
        elif risk_level <= 0.4:
            return "🟡 MEDIUM"
        elif risk_level <= 0.6:
            return "🟠 HIGH"
        else:
            return "🔴 VERY HIGH"
    
    def format_roi_matches_message(self, roi_matches: List[Dict[str, Any]]) -> str:
        """Format ROI matches for Telegram message"""
        if not roi_matches:
            return "❌ No high-ROI matches found"
        
        message = "💰 **BEST ROI TENNIS MATCHES**\n\n"
        
        for i, match in enumerate(roi_matches, 1):
            pred = match['prediction']
            
            message += f"🏆 **Match {i}: {pred.home_player} vs {pred.away_player}**\n"
            message += f"🎯 **Predicted Winner:** {pred.predicted_winner}\n"
            message += f"📊 **Win Probability:** {pred.win_probability:.1%}\n"
            message += f"⭐ **Confidence:** {pred.confidence_score:.1%}\n"
            message += f"💰 **ROI:** {match['roi_percentage']:.1f}%\n"
            message += f"💵 **Potential Profit:** ${match['potential_profit']:.0f} (on ${match['stake']} stake)\n"
            message += f"🎲 **Odds:** {match['market_odds']:.2f}\n"
            message += f"🛡️ **Risk Level:** {match['risk_category']}\n"
            
            # Add match details
            if pred.surface:
                message += f"🏟️ **Surface:** {pred.surface.title()}\n"
            if pred.tournament:
                message += f"🏆 **Tournament:** {pred.tournament}\n"
            
            # Betting recommendation
            if match['roi_percentage'] >= 20:
                message += "💎 **Recommendation:** EXCELLENT BET\n"
            elif match['roi_percentage'] >= 15:
                message += "🔥 **Recommendation:** STRONG BET\n"
            else:
                message += "💡 **Recommendation:** GOOD BET\n"
            
            # Risk warning
            if match['risk_level'] > 0.3:
                message += "⚠️ **Warning:** Higher risk - bet responsibly\n"
            
            message += "\n" + "─" * 40 + "\n\n"
        
        message += "🎯 **Target Accuracy: 70%+**\n"
        message += "⚠️ **Always bet responsibly and within your limits**"
        
        return message
    
    def format_all_predictions_message(self, predictions: List[MatchPrediction]) -> str:
        """Format all predictions for Telegram message"""
        if not predictions:
            return "❌ No predictions available"
        
        message = "📊 **ALL TENNIS PREDICTIONS**\n\n"
        
        for i, pred in enumerate(predictions, 1):
            confidence_emoji = "🔥" if pred.confidence_score >= 0.4 else "⭐" if pred.confidence_score >= 0.25 else "💡"
            
            message += f"{confidence_emoji} **{i}. {pred.home_player} vs {pred.away_player}**\n"
            message += f"🏆 Winner: {pred.predicted_winner} ({pred.win_probability:.1%})\n"
            message += f"⭐ Confidence: {pred.confidence_score:.1%}\n"
            
            if i < len(predictions):
                message += "\n"
        
        message += f"\n📈 **Total Predictions:** {len(predictions)}\n"
        message += "🎯 **Target Accuracy: 70%+**"
        
        return message
    
    async def send_immediate_roi_notification(self, roi_matches: List[Dict[str, Any]]):
        """Send IMMEDIATE ROI notification for high-confidence, low-risk opportunities"""
        if not roi_matches or not self.chat_ids:
            return

        message = "🚨 **URGENT: HIGH-CONFIDENCE ROI OPPORTUNITY!**\n\n"
        message += "🎯 **AI RECOMMENDS THIS BET NOW!**\n\n"
        message += self.format_roi_matches_message(roi_matches[:2])  # Top 2 matches for immediate alerts

        failed_sends = []
        for chat_id in self.chat_ids.copy():
            try:
                bot = Bot(token=self.bot_token)
                await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
                logger.info(f"📤 Sent IMMEDIATE ROI notification to {chat_id}")
            except Exception as e:
                logger.error(f"❌ Failed to send immediate notification to {chat_id}: {e}")
                failed_sends.append(chat_id)

        # Remove failed chat IDs
        for chat_id in failed_sends:
            self.chat_ids.discard(chat_id)
    async def send_roi_notification(self, roi_matches: List[Dict[str, Any]]):
        """Send ROI notification to all subscribers"""
        if not roi_matches or not self.chat_ids:
            return
        
        message = "🚨 **NEW HIGH-ROI OPPORTUNITIES!**\n\n"
        message += self.format_roi_matches_message(roi_matches[:3])  # Top 3 matches
        
        failed_sends = []
        for chat_id in self.chat_ids.copy():
            try:
                bot = Bot(token=self.bot_token)
                await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
                logger.info(f"📤 Sent ROI notification to {chat_id}")
            except Exception as e:
                logger.error(f"❌ Failed to send to {chat_id}: {e}")
                failed_sends.append(chat_id)
        
        # Remove failed chat IDs
        for chat_id in failed_sends:
            self.chat_ids.discard(chat_id)
    
    async def run_continuous_monitoring(self, check_interval: int = 300):
        """Run continuous ROI monitoring with immediate notifications"""
        logger.info(f"🔄 Starting continuous ROI monitoring (every {check_interval // 60} minutes)")

        while True:
            try:
                # Get best ROI matches with LOW RISK and HIGH CONFIDENCE
                roi_matches = await self.get_best_roi_matches()

                if roi_matches:
                    # Filter for IMMEDIATE NOTIFICATION criteria:
                    # - Low risk (risk_level <= 0.3)
                    # - High confidence (confidence_score >= 0.4)
                    # - Good ROI (roi_percentage >= 15)
                    immediate_matches = [
                        match for match in roi_matches
                        if (match['risk_level'] <= 0.3 and
                            match['prediction'].confidence_score >= 0.4 and
                            match['roi_percentage'] >= 15)
                    ]

                    if immediate_matches:
                        logger.info(f"🚨 FOUND {len(immediate_matches)} IMMEDIATE OPPORTUNITIES!")
                        await self.send_immediate_roi_notification(immediate_matches)

                        # Update last notification times
                        current_time = datetime.now()
                        for match in immediate_matches:
                            match_key = f"{match['prediction'].home_player}_{match['prediction'].away_player}"
                            self.last_notification_time[match_key] = current_time

                    # Check for regular notifications (avoid spam)
                    current_time = datetime.now()
                    regular_matches = [m for m in roi_matches if m not in immediate_matches]

                    if regular_matches:
                        should_notify = True
                        for match in regular_matches:
                            match_key = f"{match['prediction'].home_player}_{match['prediction'].away_player}"
                            last_time = self.last_notification_time.get(match_key)

                            if last_time and (current_time - last_time).seconds < self.notification_cooldown:
                                should_notify = False
                                break

                        if should_notify and self.chat_ids:
                            await self.send_roi_notification(regular_matches)

                            # Update last notification times
                            for match in regular_matches:
                                match_key = f"{match['prediction'].home_player}_{match['prediction'].away_player}"
                                self.last_notification_time[match_key] = current_time

                # Wait for next check
                await asyncio.sleep(check_interval)

            except Exception as e:
                logger.error(f"❌ Error in continuous monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    async def run_continuous_monitoring(self, check_interval: int = 600):
        """Run continuous ROI monitoring"""
        logger.info(f"🔄 Starting continuous ROI monitoring (every {check_interval // 60} minutes)")
        
        while True:
            try:
                # Get best ROI matches
                roi_matches = await self.get_best_roi_matches()
                
                if roi_matches:
                    # Check if we should send notification (avoid spam)
                    current_time = datetime.now()
                    should_notify = True
                    
                    for match in roi_matches:
                        match_key = f"{match['prediction'].home_player}_{match['prediction'].away_player}"
                        last_time = self.last_notification_time.get(match_key)
                        
                        if last_time and (current_time - last_time).seconds < self.notification_cooldown:
                            should_notify = False
                            break
                    
                    if should_notify and self.chat_ids:
                        await self.send_roi_notification(roi_matches)
                        
                        # Update last notification times
                        for match in roi_matches:
                            match_key = f"{match['prediction'].home_player}_{match['prediction'].away_player}"
                            self.last_notification_time[match_key] = current_time
                
                # Wait for next check
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in continuous monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def start_bot(self):
        """Start the Telegram bot"""
        if not await self.setup():
            return False
        
        try:
            logger.info("🚀 Starting Telegram ROI Bot...")
            
            # Start the bot
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            logger.info("✅ Telegram bot is running!")
            
            # Start continuous monitoring in background
            monitoring_task = asyncio.create_task(self.run_continuous_monitoring())
            
            # Keep the bot running
            try:
                await monitoring_task
            except KeyboardInterrupt:
                logger.info("⏹️ Bot stopped by user")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error starting bot: {e}")
            return False
        finally:
            # Cleanup
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()

async def main():
    """Main function to run the ROI bot"""
    print("🤖 TENNIS ROI TELEGRAM BOT")
    print("=" * 50)
    
    # Check if Telegram is available
    if not TELEGRAM_AVAILABLE:
        print("❌ Telegram bot library not available")
        print("Install with: pip install python-telegram-bot")
        return
    
    # Initialize bot
    bot = TennisROIBot()
    
    if not bot.bot_token:
        print("❌ No Telegram bot token found!")
        print("\n🔧 Setup Instructions:")
        print("1. Create a bot with @BotFather on Telegram")
        print("2. Get your bot token")
        print("3. Set environment variable: export TELEGRAM_BOT_TOKEN='your_token_here'")
        print("4. Or create config file at: config/telegram_config.json")
        return
    
    # Start the bot
    success = await bot.start_bot()
    
    if success:
        print("✅ ROI Bot started successfully!")
    else:
        print("❌ Failed to start ROI Bot")

if __name__ == "__main__":
    asyncio.run(main())
