#!/usr/bin/env python3
"""
🚨 ROI ALERT MANAGER
====================

Manages alerts for high-ROI opportunities via Discord and Telegram.
"""

import os
import logging
from typing import Dict, Optional, List
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Optional: Project Status Manager
try:
    from src.notion.project_status_manager import ProjectStatusManager
    STATUS_MANAGER_AVAILABLE = True
except ImportError:
    STATUS_MANAGER_AVAILABLE = False

# Load environment variables
env_path = os.path.join(Path(__file__).parent.parent.parent, 'telegram_secrets.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

logger = logging.getLogger(__name__)

# Try to import requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Try to import Telegram
try:
    from telegram import Bot
    from telegram.constants import ParseMode
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False


class ROIAlertManager:
    """
    ROI alert manager for Discord and Telegram
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize alert manager
        
        Args:
            config: Configuration dict
        """
        self.config = config or {}
        
        # Discord webhook
        self.discord_webhook_url = os.getenv('DISCORD_WEBHOOK_URL') or self.config.get('discord_webhook_url')
        
        # Telegram
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN') or self.config.get('telegram_bot_token')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID') or self.config.get('telegram_chat_id')
        self.telegram_bot = None
        
        if TELEGRAM_AVAILABLE and self.telegram_bot_token:
            try:
                self.telegram_bot = Bot(token=self.telegram_bot_token)
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize Telegram bot: {e}")
        
        # Alert thresholds
        self.min_ev_pct = self.config.get('min_ev_pct', 15.0)
        self.min_odds_movement = self.config.get('min_odds_movement', 25.0)
        
        # Rate limiting
        self.last_alert_times: Dict[str, datetime] = {}
        self.alert_cooldown = self.config.get('alert_cooldown_seconds', 300)  # 5 minutes
        
        # Project Status Manager (optional)
        self.status_manager = None
        if STATUS_MANAGER_AVAILABLE:
            try:
                self.status_manager = ProjectStatusManager()
            except Exception as e:
                logger.debug(f"Project Status Manager not available: {e}")
        
        logger.info("🚨 ROI Alert Manager initialized")
    
    async def send_alert(self, opportunity: Dict) -> bool:
        """
        Send alert for ROI opportunity
        
        Args:
            opportunity: ROIOpportunity dictionary
            
        Returns:
            True if sent successfully
        """
        # Check if should alert
        if not self._should_alert(opportunity):
            return False
        
        # Check rate limiting
        match_id = opportunity.get('match_id')
        if match_id in self.last_alert_times:
            last_alert = self.last_alert_times[match_id]
            elapsed = (datetime.now() - last_alert).total_seconds()
            if elapsed < self.alert_cooldown:
                logger.debug(f"⏭️ Skipping alert (cooldown): {match_id}")
                return False
        
        # Send alerts
        discord_sent = False
        telegram_sent = False
        
        if self.discord_webhook_url:
            discord_sent = self._send_discord_alert(opportunity)
        
        if self.telegram_bot and self.telegram_chat_id:
            telegram_sent = await self._send_telegram_alert(opportunity)
        
        if discord_sent or telegram_sent:
            self.last_alert_times[match_id] = datetime.now()
            
            # Add to Project Status page if available
            if self.status_manager:
                try:
                    self.status_manager.add_roi_opportunity(opportunity)
                except Exception as e:
                    logger.debug(f"Could not add ROI opportunity to status page: {e}")
            
            logger.info(f"✅ Alert sent for {match_id}")
            return True
        
        return False
    
    def _should_alert(self, opportunity: Dict) -> bool:
        """Check if opportunity meets alert criteria"""
        ev_pct = opportunity.get('expected_value_pct', 0)
        
        # Check EV threshold
        if ev_pct < self.min_ev_pct:
            return False
        
        # Check opportunity type
        opp_type = opportunity.get('opportunity_type')
        if opp_type in ['momentum_shift', 'fatigue_exploit', 'h2h_imbalance']:
            return True
        
        return False
    
    def _send_discord_alert(self, opportunity: Dict) -> bool:
        """Send Discord webhook alert"""
        if not REQUESTS_AVAILABLE or not self.discord_webhook_url:
            return False
        
        try:
            # Build embed
            embed = {
                "title": "🚨 High ROI Opportunity",
                "description": f"{opportunity.get('player_a', 'Player A')} vs {opportunity.get('player_b', 'Player B')}",
                "color": 16711680,  # Red
                "fields": [
                    {"name": "Tournament", "value": opportunity.get('tournament', 'Unknown'), "inline": True},
                    {"name": "Score", "value": opportunity.get('current_score', '-'), "inline": True},
                    {"name": "Strategy", "value": opportunity.get('strategy', 'N/A'), "inline": True},
                    {"name": "Expected Value", "value": f"{opportunity.get('expected_value_pct', 0):.1f}%", "inline": True},
                    {"name": "Kelly Stake", "value": f"{opportunity.get('kelly_stake_pct', 0):.2f}%", "inline": True},
                    {"name": "Current Odds", "value": f"{opportunity.get('current_odds', 'N/A')}", "inline": True},
                    {"name": "Reasoning", "value": opportunity.get('reasoning', 'N/A'), "inline": False}
                ],
                "timestamp": datetime.now().isoformat()
            }
            
            payload = {"embeds": [embed]}
            
            response = requests.post(self.discord_webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.debug("✅ Discord alert sent")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending Discord alert: {e}")
            return False
    
    async def _send_telegram_alert(self, opportunity: Dict) -> bool:
        """Send Telegram alert"""
        if not self.telegram_bot or not self.telegram_chat_id:
            return False
        
        try:
            # Build message
            message = self._format_telegram_message(opportunity)
            
            await self.telegram_bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.debug("✅ Telegram alert sent")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending Telegram alert: {e}")
            return False
    
    def _format_telegram_message(self, opportunity: Dict) -> str:
        """Format Telegram message"""
        ev_pct = opportunity.get('expected_value_pct', 0)
        emoji = "🔥" if ev_pct > 20 else "⭐"
        
        message = f"""
{emoji} *High ROI Opportunity*

*Match:* {opportunity.get('player_a', 'Player A')} vs {opportunity.get('player_b', 'Player B')}
*Tournament:* {opportunity.get('tournament', 'Unknown')}
*Score:* {opportunity.get('current_score', '-')}

*Strategy:* {opportunity.get('strategy', 'N/A')}
*Expected Value:* {ev_pct:.1f}%
*Kelly Stake:* {opportunity.get('kelly_stake_pct', 0):.2f}%
*Current Odds:* {opportunity.get('current_odds', 'N/A')}

*Reasoning:*
{opportunity.get('reasoning', 'N/A')}
        """.strip()
        
        return message

