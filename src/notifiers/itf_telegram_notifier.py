#!/usr/bin/env python3
"""
📱 ITF TELEGRAM NOTIFIER
========================

Sends Telegram alerts for ITF betting opportunities:
- Model edge >5% (value bet detected)
- Model edge >8% (2× stake recommendation)
- Live momentum shifts
- Set 1 deficit recovery opportunities
"""

import logging
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from dotenv import load_dotenv
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables
env_path = os.path.join(Path(__file__).parent.parent.parent, 'telegram_secrets.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

# Telegram
try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    try:
        import telegram
        TELEGRAM_AVAILABLE = True
    except ImportError:
        TELEGRAM_AVAILABLE = False

logger = logging.getLogger(__name__)


class ITFTelegramNotifier:
    """Telegram notifier for ITF betting alerts"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ITF Telegram Notifier
        
        Args:
            config: Configuration dict
        """
        self.config = config or {}
        self.enabled = self.config.get('telegram_enabled', True)
        self.min_edge = self.config.get('min_edge_for_alert', 0.05)
        
        # Get Telegram credentials
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN') or self.config.get('bot_token')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID') or self.config.get('chat_id')
        
        if not TELEGRAM_AVAILABLE:
            logger.warning("⚠️ python-telegram-bot not available")
            self.bot = None
        elif not self.bot_token or not self.chat_id:
            logger.warning("⚠️ Telegram credentials not configured")
            self.bot = None
        else:
            try:
                self.bot = Bot(token=self.bot_token)
                logger.info("✅ ITF Telegram Notifier initialized")
            except Exception as e:
                logger.error(f"❌ Error initializing Telegram bot: {e}")
                self.bot = None
    
    async def send_alert(self, message: str, parse_mode: str = "Markdown") -> bool:
        """
        Send alert message to Telegram
        
        Args:
            message: Message text
            parse_mode: Parse mode (Markdown or HTML)
            
        Returns:
            True if successful
        """
        if not self.enabled or not self.bot or not self.chat_id:
            return False
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            logger.info("✅ Telegram alert sent")
            return True
            
        except TelegramError as e:
            logger.error(f"❌ Telegram error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error sending Telegram alert: {e}")
            return False
    
    async def send_value_bet_alert(self, match_data: Dict[str, Any], edge: float, odds: float) -> bool:
        """
        Send value bet alert (edge >5%)
        
        Args:
            match_data: Match data dictionary
            edge: Calculated edge percentage
            odds: Betting odds
            
        Returns:
            True if successful
        """
        if edge < self.min_edge:
            return False
        
        player1 = match_data.get('player1', 'Player 1')
        player2 = match_data.get('player2', 'Player 2')
        tournament = match_data.get('tournament', 'ITF Tournament')
        
        message = f"🎾 *Value Bet Detected*\n\n"
        message += f"*Match:* {player1} vs {player2}\n"
        message += f"*Tournament:* {tournament}\n"
        message += f"*Odds:* {odds:.2f}\n"
        message += f"*Edge:* {edge:.2%}\n"
        
        if edge >= 0.08:
            message += f"*Recommendation:* STRONG BET (2× stake)\n"
        else:
            message += f"*Recommendation:* BET\n"
        
        return await self.send_alert(message)
    
    async def send_momentum_alert(self, alert_data: Dict[str, Any]) -> bool:
        """
        Send live momentum shift alert
        
        Args:
            alert_data: Alert data dictionary
            
        Returns:
            True if successful
        """
        player1 = alert_data.get('player1', 'Player 1')
        player2 = alert_data.get('player2', 'Player 2')
        set1_score = alert_data.get('set1_score', 'N/A')
        comeback_pct = alert_data.get('comeback_percent', 0.0)
        
        message = f"⚡ *Live Momentum Alert*\n\n"
        message += f"*Match:* {player1} vs {player2}\n"
        message += f"*Set 1 Score:* {set1_score}\n"
        message += f"*Historical Comeback %:* {comeback_pct:.1%}\n"
        message += f"*Pattern:* Set 1 Deficit Recovery Opportunity"
        
        return await self.send_alert(message)
    
    async def send_steam_move_alert(self, match_data: Dict[str, Any], move_pct: float) -> bool:
        """
        Send steam move alert (odds moved >15% <2h before match)
        
        Args:
            match_data: Match data dictionary
            move_pct: Odds movement percentage
            
        Returns:
            True if successful
        """
        player1 = match_data.get('player1', 'Player 1')
        player2 = match_data.get('player2', 'Player 2')
        
        message = f"📈 *Steam Move Alert*\n\n"
        message += f"*Match:* {player1} vs {player2}\n"
        message += f"*Odds Move:* {move_pct:.2f}%\n"
        message += f"*Time:* <2 hours before match\n"
        message += f"*Action:* Monitor closely"
        
        return await self.send_alert(message)


async def main():
    """Test ITF Telegram Notifier"""
    print("📱 ITF TELEGRAM NOTIFIER TEST")
    print("=" * 50)
    
    config = {
        'telegram_enabled': True,
        'min_edge_for_alert': 0.05,
    }
    
    notifier = ITFTelegramNotifier(config)
    
    if not notifier.bot:
        print("❌ Telegram bot not configured")
        print("\n💡 Setup:")
        print("1. Create Telegram bot: @BotFather")
        print("2. Get bot token")
        print("3. Add to telegram_secrets.env: TELEGRAM_BOT_TOKEN=your_token")
        print("4. Get chat ID: @userinfobot")
        print("5. Add to telegram_secrets.env: TELEGRAM_CHAT_ID=your_chat_id")
        return
    
    # Test value bet alert
    match_data = {
        'player1': 'Maria Garcia',
        'player2': 'Anna Smith',
        'tournament': 'ITF W15 Antalya',
    }
    
    print("\n🧪 Testing value bet alert...")
    success = await notifier.send_value_bet_alert(match_data, 0.06, 1.75)
    print(f"   Result: {'✅ Sent' if success else '❌ Failed'}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    import asyncio
    asyncio.run(main())

