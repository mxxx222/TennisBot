"""
Notification utilities for Tennis ITF screening system
Handles Telegram alerts and Notion database logging
"""

import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import Dict, List, Optional
import json

from telegram import Bot
from telegram.error import TelegramError

from config.screening_config import ScreeningConfig

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Handles Telegram bot notifications"""
    
    def __init__(self):
        self.config = ScreeningConfig()
        self.bot = Bot(token=self.config.TELEGRAM_BOT_TOKEN)
        
    async def send_opportunity_alert(self, opportunity) -> bool:
        """
        Send betting opportunity alert to Telegram
        
        Args:
            opportunity: BettingOpportunity object
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Format the message
            message = self._format_opportunity_message(opportunity)
            
            # Send message
            await self.bot.send_message(
                chat_id=self.config.TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
            logger.info(f"Sent Telegram alert for {opportunity.player}")
            return True
            
        except TelegramError as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram message: {e}")
            return False
    
    def _format_opportunity_message(self, opportunity) -> str:
        """Format betting opportunity as Telegram message"""
        
        # Emoji based on confidence
        confidence_emoji = {
            'High': '🟢',
            'Medium': '🟡', 
            'Low': '🟠'
        }
        
        emoji = confidence_emoji.get(opportunity.confidence, '⚪')
        
        # Format commence time
        time_str = opportunity.commence_time.strftime('%H:%M')
        date_str = opportunity.commence_time.strftime('%d.%m')
        
        message = f"""🎾 *Tennis ITF Pick Alert*

{emoji} *{opportunity.player}* vs {opportunity.opponent}

📊 *Odds:* {opportunity.odds}
💰 *Stake:* ${opportunity.recommended_stake}
🎯 *Confidence:* {opportunity.confidence}
📈 *Edge:* +{opportunity.edge_estimate}%

⏰ *Time:* {time_str} ({date_str})
🏆 *Tournament:* {opportunity.tournament}

💡 *Auto-screened* | Odds range: 1.30-1.80 (proven edge)
📊 *ROI History:* +17.81% (98 bets)

_Place bet manually and log result in Notion_"""

        return message
    
    async def send_daily_summary(self, summary: Dict, opportunities: List) -> bool:
        """Send daily summary of opportunities"""
        try:
            message = self._format_daily_summary(summary, opportunities)
            
            await self.bot.send_message(
                chat_id=self.config.TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info("Sent daily summary to Telegram")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send daily summary: {e}")
            return False
    
    def _format_daily_summary(self, summary: Dict, opportunities: List) -> str:
        """Format daily summary message"""
        
        if summary['total_opportunities'] == 0:
            return """📊 *Daily ITF Tennis Summary*

❌ No qualified opportunities today
🎯 Looking for odds 1.30-1.80 in ITF Women's tennis

_System will check again tomorrow at 08:00 EET_"""
        
        confidence_text = ""
        for conf, count in summary['confidence_breakdown'].items():
            confidence_text += f"  • {conf}: {count}\n"
        
        message = f"""📊 *Daily ITF Tennis Summary*

✅ *Opportunities Found:* {summary['total_opportunities']}
💰 *Total Recommended Stake:* ${summary['total_stake']}
📊 *Average Odds:* {summary['avg_odds']}
📈 *Average Edge:* +{summary['avg_edge']}%

🎯 *Confidence Breakdown:*
{confidence_text}
⚖️ *Risk:* {summary['risk_percentage']}% of bankroll
💳 *Bankroll:* ${summary['bankroll']}

_All opportunities logged to Notion database_"""

        return message

class NotionLogger:
    """Handles logging to Notion database"""
    
    def __init__(self):
        self.config = ScreeningConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def log_opportunity(self, opportunity) -> bool:
        """
        Log betting opportunity to Notion database
        
        Args:
            opportunity: BettingOpportunity object
            
        Returns:
            True if logged successfully, False otherwise
        """
        if not self.config.NOTION_API_KEY or not self.config.NOTION_DATABASE_ID:
            logger.warning("Notion credentials not configured, skipping logging")
            return False
        
        try:
            # Prepare the data for Notion
            page_data = self._prepare_notion_page_data(opportunity)
            
            # Create page in Notion database
            url = "https://api.notion.com/v1/pages"
            headers = {
                "Authorization": f"Bearer {self.config.NOTION_API_KEY}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            
            async with self.session.post(url, headers=headers, json=page_data) as response:
                if response.status == 200:
                    logger.info(f"Logged opportunity to Notion: {opportunity.player}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to log to Notion: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error logging to Notion: {e}")
            return False
    
    def _prepare_notion_page_data(self, opportunity) -> Dict:
        """Prepare data structure for Notion page creation"""
        
        # Format match name
        match_name = f"{opportunity.player} vs {opportunity.opponent}"
        
        # Format date for Notion
        date_iso = opportunity.commence_time.isoformat()
        
        return {
            "parent": {"database_id": self.config.NOTION_DATABASE_ID},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": match_name}}]
                },
                "Odds": {
                    "number": opportunity.odds
                },
                "Stake": {
                    "number": opportunity.recommended_stake
                },
                "Bet Structure": {
                    "select": {"name": "SINGLE"}
                },
                "League": {
                    "rich_text": [{"text": {"content": "Tennis - ITF Women"}}]
                },
                "Team/Player": {
                    "rich_text": [{"text": {"content": opportunity.player}}]
                },
                "Date": {
                    "date": {"start": date_iso}
                },
                "Result": {
                    "select": {"name": "Pending"}
                },
                "Confidence": {
                    "select": {"name": opportunity.confidence}
                },
                "Notes": {
                    "rich_text": [{
                        "text": {
                            "content": f"Auto-screened by ITF system. "
                                     f"Edge: +{opportunity.edge_estimate}%. "
                                     f"Kelly fraction: {opportunity.kelly_fraction:.3f}. "
                                     f"Tournament: {opportunity.tournament}"
                        }
                    }]
                }
            }
        }

class NotificationManager:
    """Manages all notification channels"""
    
    def __init__(self):
        self.telegram = TelegramNotifier()
        self.notion = NotionLogger()
    
    async def send_opportunities(self, opportunities: List, summary: Dict) -> Dict[str, bool]:
        """
        Send opportunities through all notification channels
        
        Returns:
            Dictionary with success status for each channel
        """
        results = {
            'telegram_alerts': True,
            'telegram_summary': True,
            'notion_logging': True
        }
        
        # Send individual Telegram alerts
        for opportunity in opportunities:
            success = await self.telegram.send_opportunity_alert(opportunity)
            if not success:
                results['telegram_alerts'] = False
        
        # Send Telegram summary
        summary_success = await self.telegram.send_daily_summary(summary, opportunities)
        results['telegram_summary'] = summary_success
        
        # Log to Notion
        async with self.notion as notion_logger:
            for opportunity in opportunities:
                success = await notion_logger.log_opportunity(opportunity)
                if not success:
                    results['notion_logging'] = False
        
        return results
    
    def send_opportunities_sync(self, opportunities: List, summary: Dict) -> Dict[str, bool]:
        """Synchronous wrapper for send_opportunities"""
        return asyncio.run(self.send_opportunities(opportunities, summary))
