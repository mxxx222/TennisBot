"""
Telegram Insider Client

Telegram API wrapper using Telethon for channel monitoring
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.telegram_insider_config import TelegramInsiderConfig

try:
    from telethon import TelegramClient, events
    from telethon.tl.types import Channel, User
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False

logger = logging.getLogger(__name__)

class TelegramInsiderClient:
    """Telegram client for monitoring insider channels"""
    
    def __init__(self, config: Optional[TelegramInsiderConfig] = None):
        self.config = config or TelegramInsiderConfig
        
        if not self.config.is_configured():
            logger.warning("⚠️ Telegram API not configured. Set TELEGRAM_API_ID, TELEGRAM_API_HASH, and TELEGRAM_PHONE_NUMBER environment variables.")
            self.client = None
            self.is_available = False
        elif not TELETHON_AVAILABLE:
            logger.warning("⚠️ Telethon library not available. Install with: pip install telethon")
            self.client = None
            self.is_available = False
        else:
            try:
                self.client = TelegramClient(
                    self.config.SESSION_NAME,
                    int(self.config.API_ID) if self.config.API_ID else 0,
                    self.config.API_HASH
                )
                self.is_available = True
                logger.info("✅ Telegram Insider Client initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Telegram client: {e}")
                self.client = None
                self.is_available = False
        
        self.connected = False
    
    async def connect(self) -> bool:
        """Connect to Telegram"""
        if not self.is_available:
            return False
        
        try:
            if not self.connected:
                await self.client.start(phone=self.config.PHONE_NUMBER)
                self.connected = True
                logger.info("✅ Connected to Telegram")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Telegram: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Telegram"""
        if self.client and self.connected:
            await self.client.disconnect()
            self.connected = False
            logger.info("✅ Disconnected from Telegram")
    
    async def get_channel_messages(
        self,
        channel_username: str,
        limit: int = 50,
        hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get recent messages from a Telegram channel
        
        Args:
            channel_username: Channel username (with or without @)
            limit: Maximum number of messages to retrieve
            hours_back: How many hours back to look
        
        Returns:
            List of message dictionaries
        """
        if not self.is_available or not self.connected:
            return []
        
        try:
            # Remove @ if present
            channel = channel_username.lstrip('@')
            
            # Get channel entity
            entity = await self.client.get_entity(channel)
            
            # Calculate date threshold
            date_threshold = datetime.now() - timedelta(hours=hours_back)
            
            messages = []
            async for message in self.client.iter_messages(
                entity,
                limit=limit,
                offset_date=date_threshold
            ):
                try:
                    msg_data = {
                        'id': message.id,
                        'text': message.text or '',
                        'date': message.date.isoformat() if message.date else None,
                        'views': message.views or 0,
                        'forwards': message.forwards or 0,
                        'replies': message.replies.replies if hasattr(message.replies, 'replies') else 0,
                        'channel': channel,
                        'author_id': message.from_id.user_id if message.from_id else None,
                        'is_reply': message.is_reply,
                        'media': bool(message.media),
                    }
                    messages.append(msg_data)
                except Exception as e:
                    logger.debug(f"Error processing message {message.id}: {e}")
                    continue
            
            logger.info(f"✅ Retrieved {len(messages)} messages from {channel}")
            return messages
            
        except Exception as e:
            logger.error(f"❌ Error getting messages from {channel_username}: {e}")
            return []
    
    async def get_channel_info(self, channel_username: str) -> Optional[Dict[str, Any]]:
        """Get information about a channel"""
        if not self.is_available or not self.connected:
            return None
        
        try:
            channel = channel_username.lstrip('@')
            entity = await self.client.get_entity(channel)
            
            info = {
                'id': entity.id,
                'title': getattr(entity, 'title', channel),
                'username': getattr(entity, 'username', channel),
                'participants_count': getattr(entity, 'participants_count', 0),
                'is_verified': getattr(entity, 'verified', False),
                'is_scam': getattr(entity, 'scam', False),
            }
            
            return info
            
        except Exception as e:
            logger.error(f"❌ Error getting channel info for {channel_username}: {e}")
            return None
    
    async def search_channel_messages(
        self,
        channel_username: str,
        query: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search for messages in a channel"""
        if not self.is_available or not self.connected:
            return []
        
        try:
            channel = channel_username.lstrip('@')
            entity = await self.client.get_entity(channel)
            
            messages = []
            async for message in self.client.iter_messages(
                entity,
                search=query,
                limit=limit
            ):
                try:
                    msg_data = {
                        'id': message.id,
                        'text': message.text or '',
                        'date': message.date.isoformat() if message.date else None,
                        'channel': channel,
                    }
                    messages.append(msg_data)
                except Exception as e:
                    logger.debug(f"Error processing search result: {e}")
                    continue
            
            return messages
            
        except Exception as e:
            logger.error(f"❌ Error searching {channel_username}: {e}")
            return []
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()

