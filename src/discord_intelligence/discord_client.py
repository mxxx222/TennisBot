"""
Discord Intelligence Client

Discord API wrapper for server monitoring
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.discord_config import DiscordConfig

try:
    import discord
    from discord.ext import commands
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    discord = None

logger = logging.getLogger(__name__)

class DiscordIntelligenceClient:
    """Discord client for monitoring betting servers"""
    
    def __init__(self, config: Optional[DiscordConfig] = None):
        self.config = config or DiscordConfig
        
        if not self.config.is_configured():
            logger.warning("⚠️ Discord not configured. Set DISCORD_BOT_TOKEN environment variable.")
            self.client = None
            self.is_available = False
        elif not DISCORD_AVAILABLE:
            logger.warning("⚠️ discord.py not available. Install with: pip install discord.py")
            self.client = None
            self.is_available = False
        else:
            intents = discord.Intents.default()
            intents.message_content = True
            intents.guilds = True
            
            self.client = discord.Client(intents=intents)
            self.is_available = True
            self.connected = False
            
            logger.info("✅ Discord Intelligence Client initialized")
    
    async def connect(self) -> bool:
        """Connect to Discord"""
        if not self.is_available:
            return False
        
        try:
            if not self.connected:
                await self.client.login(self.config.BOT_TOKEN)
                await self.client.connect()
                self.connected = True
                logger.info("✅ Connected to Discord")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Discord: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Discord"""
        if self.client and self.connected:
            await self.client.close()
            self.connected = False
            logger.info("✅ Disconnected from Discord")
    
    async def get_server_messages(
        self,
        server_name: str,
        channel_name: str = 'general',
        limit: int = 100,
        hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get recent messages from a Discord server channel
        
        Args:
            server_name: Name of the Discord server
            channel_name: Name of the channel
            limit: Maximum number of messages
            hours_back: How many hours back to look
        
        Returns:
            List of message dictionaries
        """
        if not self.is_available or not self.connected:
            return []
        
        try:
            # Find server
            server = None
            for guild in self.client.guilds:
                if guild.name == server_name:
                    server = guild
                    break
            
            if not server:
                logger.warning(f"Server '{server_name}' not found")
                return []
            
            # Find channel
            channel = None
            for ch in server.channels:
                if ch.name == channel_name:
                    channel = ch
                    break
            
            if not channel:
                logger.warning(f"Channel '{channel_name}' not found in {server_name}")
                return []
            
            # Get messages
            messages = []
            date_threshold = datetime.now() - timedelta(hours=hours_back)
            
            async for message in channel.history(limit=limit, after=date_threshold):
                try:
                    msg_data = {
                        'id': message.id,
                        'content': message.content,
                        'author': str(message.author),
                        'author_id': message.author.id,
                        'created_at': message.created_at.isoformat(),
                        'channel': channel_name,
                        'server': server_name,
                        'reactions': [str(r.emoji) for r in message.reactions],
                        'reaction_count': sum(r.count for r in message.reactions),
                    }
                    messages.append(msg_data)
                except Exception as e:
                    logger.debug(f"Error processing message {message.id}: {e}")
                    continue
            
            logger.info(f"✅ Retrieved {len(messages)} messages from {server_name}#{channel_name}")
            return messages
            
        except Exception as e:
            logger.error(f"❌ Error getting messages from {server_name}: {e}")
            return []
    
    async def get_user_messages(
        self,
        server_name: str,
        user_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recent messages from a specific user"""
        if not self.is_available or not self.connected:
            return []
        
        try:
            # Find server
            server = None
            for guild in self.client.guilds:
                if guild.name == server_name:
                    server = guild
                    break
            
            if not server:
                return []
            
            messages = []
            for channel in server.text_channels:
                try:
                    async for message in channel.history(limit=limit):
                        if message.author.id == user_id:
                            msg_data = {
                                'id': message.id,
                                'content': message.content,
                                'channel': channel.name,
                                'created_at': message.created_at.isoformat(),
                            }
                            messages.append(msg_data)
                except Exception:
                    continue
            
            return messages
            
        except Exception as e:
            logger.error(f"❌ Error getting user messages: {e}")
            return []
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()

