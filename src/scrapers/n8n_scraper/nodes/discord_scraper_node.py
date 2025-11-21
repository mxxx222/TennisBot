#!/usr/bin/env python3
"""
Discord Scraper Node for N8N-Style Scraper

Scrapes text content from Discord servers and channels.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import hashlib
import os

from .base_node import SourceNode, NodeExecutionResult

# Optional discord.py support
try:
    import discord
    from discord.ext import commands
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    discord = None

logger = logging.getLogger(__name__)


class DiscordScraperNode(SourceNode):
    """
    Node for scraping text content from Discord servers and channels.

    Supports:
    - Multiple servers and channels
    - Message filtering by time and content
    - Rate limiting and error handling
    - Message metadata extraction
    """

    def __init__(self, node_id: str, config: Dict[str, Any]):
        super().__init__(node_id, config)

        # Discord configuration
        self.servers = config.get('servers', [])
        self.channels = config.get('channels', [])
        self.bot_token = config.get('token') or os.getenv('DISCORD_BOT_TOKEN')

        # Scraping parameters
        self.max_messages = config.get('max_messages', 100)
        self.hours_back = config.get('hours_back', 24)
        self.min_content_length = config.get('min_content_length', 10)

        # Content filtering
        self.keywords = config.get('keywords', [])
        self.exclude_keywords = config.get('exclude_keywords', [])

        # Client state
        self.client = None
        self.is_available = False
        self.connected = False

        # Validate configuration
        if not self.servers and not self.channels:
            raise ValueError("No Discord servers or channels provided")

        if not self.bot_token:
            logger.warning("Discord bot token not configured")
            self.is_available = False
        elif not DISCORD_AVAILABLE:
            logger.warning("discord.py not available. Install with: pip install discord.py")
            self.is_available = False
        else:
            self.is_available = True

    @property
    def inputs(self) -> List[str]:
        return ['trigger', 'optional_servers', 'optional_channels']

    @property
    def outputs(self) -> List[str]:
        return ['data', 'metadata']

    async def execute(self, input_data: Dict[str, Any]) -> NodeExecutionResult:
        """Execute Discord scraping"""
        if not self.is_available:
            return NodeExecutionResult(
                success=False,
                error="Discord client not available - check bot token and dependencies",
                node_id=self.node_id
            )

        try:
            # Get servers and channels to scrape
            servers_to_scrape, channels_to_scrape = self._get_targets_to_scrape(input_data)

            if not servers_to_scrape and not channels_to_scrape:
                return NodeExecutionResult(
                    success=False,
                    error="No servers or channels to scrape",
                    node_id=self.node_id
                )

            # Initialize and connect client
            await self._init_client()
            await self._connect_client()

            scraped_messages = []
            metadata = {
                'total_servers': len(servers_to_scrape),
                'total_channels': len(channels_to_scrape),
                'successful_servers': 0,
                'successful_channels': 0,
                'failed_targets': 0,
                'total_messages': 0,
                'filtered_messages': 0,
                'servers_scraped': [],
                'channels_scraped': [],
                'time_range': f"{self.hours_back} hours back"
            }

            # Scrape servers
            for server_name in servers_to_scrape:
                try:
                    server_messages, server_metadata = await self._scrape_server(server_name)
                    if server_messages:
                        scraped_messages.extend(server_messages)
                        metadata['successful_servers'] += 1
                        metadata['total_messages'] += len(server_messages)
                        metadata['servers_scraped'].append(server_name)

                        logger.info(f"✅ Scraped {len(server_messages)} messages from server {server_name}")
                    else:
                        metadata['failed_targets'] += 1

                except Exception as e:
                    logger.error(f"Failed to scrape server {server_name}: {e}")
                    metadata['failed_targets'] += 1
                    continue

            # Scrape specific channels
            for channel_target in channels_to_scrape:
                try:
                    if isinstance(channel_target, dict):
                        server_name = channel_target.get('server')
                        channel_name = channel_target.get('channel')
                    else:
                        # Assume format "server#channel"
                        parts = channel_target.split('#', 1)
                        server_name = parts[0] if len(parts) > 1 else None
                        channel_name = parts[1] if len(parts) > 1 else channel_target

                    if not server_name or not channel_name:
                        continue

                    messages = await self._scrape_channel(server_name, channel_name)
                    if messages:
                        scraped_messages.extend(messages)
                        metadata['successful_channels'] += 1
                        metadata['total_messages'] += len(messages)
                        metadata['channels_scraped'].append(f"{server_name}#{channel_name}")

                        logger.info(f"✅ Scraped {len(messages)} messages from {server_name}#{channel_name}")
                    else:
                        metadata['failed_targets'] += 1

                except Exception as e:
                    logger.error(f"Failed to scrape channel {channel_target}: {e}")
                    metadata['failed_targets'] += 1
                    continue

            # Filter messages if keywords specified
            if self.keywords or self.exclude_keywords:
                filtered_messages = self._filter_messages(scraped_messages)
                metadata['filtered_messages'] = len(scraped_messages) - len(filtered_messages)
                scraped_messages = filtered_messages

            # Clean up
            await self._disconnect_client()

            return NodeExecutionResult(
                success=True,
                data={
                    'messages': scraped_messages,
                    'servers_scraped': metadata['servers_scraped'],
                    'channels_scraped': metadata['channels_scraped'],
                    'message_count': len(scraped_messages)
                },
                metadata=metadata,
                node_id=self.node_id
            )

        except Exception as e:
            logger.error(f"Discord scraping failed: {e}")
            await self._cleanup()
            return NodeExecutionResult(
                success=False,
                error=str(e),
                node_id=self.node_id
            )

    def _get_targets_to_scrape(self, input_data: Dict[str, Any]) -> tuple:
        """Get servers and channels to scrape from config and inputs"""
        servers = list(self.servers)
        channels = list(self.channels)

        # Add from inputs
        if 'optional_servers' in input_data:
            additional_servers = input_data['optional_servers']
            if isinstance(additional_servers, list):
                servers.extend(additional_servers)
            elif isinstance(additional_servers, str):
                servers.append(additional_servers)

        if 'optional_channels' in input_data:
            additional_channels = input_data['optional_channels']
            if isinstance(additional_channels, list):
                channels.extend(additional_channels)
            elif isinstance(additional_channels, str):
                channels.append(additional_channels)

        # Remove duplicates
        servers = list(set(servers))
        channels = list(set(channels))

        return servers, channels

    async def _init_client(self) -> None:
        """Initialize Discord client"""
        if not DISCORD_AVAILABLE:
            raise RuntimeError("discord.py library not available")

        try:
            intents = discord.Intents.default()
            intents.message_content = True
            intents.guilds = True

            self.client = discord.Client(intents=intents)
            logger.debug("Discord client initialized")

        except Exception as e:
            raise RuntimeError(f"Failed to initialize Discord client: {e}")

    async def _connect_client(self) -> None:
        """Connect to Discord"""
        if not self.client:
            raise RuntimeError("Client not initialized")

        try:
            await self.client.login(self.bot_token)
            await self.client.connect()
            self.connected = True
            logger.debug("Connected to Discord")

        except Exception as e:
            raise RuntimeError(f"Failed to connect to Discord: {e}")

    async def _disconnect_client(self) -> None:
        """Disconnect from Discord"""
        if self.client and self.connected:
            await self.client.close()
            self.connected = False
            logger.debug("Disconnected from Discord")

    async def _scrape_server(self, server_name: str) -> tuple:
        """Scrape all configured channels in a server"""
        if not self.client or not self.connected:
            return [], {}

        try:
            # Find server
            server = None
            for guild in self.client.guilds:
                if guild.name == server_name:
                    server = guild
                    break

            if not server:
                logger.warning(f"Server '{server_name}' not found")
                return [], {}

            # Scrape all text channels
            all_messages = []
            date_threshold = datetime.now() - timedelta(hours=self.hours_back)

            for channel in server.text_channels:
                try:
                    messages = []
                    async for message in channel.history(limit=self.max_messages, after=date_threshold):
                        try:
                            # Skip empty messages
                            if not message.content or len(message.content.strip()) < self.min_content_length:
                                continue

                            message_data = {
                                'id': self._generate_message_id(server_name, channel.name, message.id),
                                'discord_id': message.id,
                                'server': server_name,
                                'channel': channel.name,
                                'content': message.content.strip(),
                                'timestamp': message.created_at.isoformat(),
                                'author': str(message.author),
                                'author_id': message.author.id,
                                'reactions': [str(r.emoji) for r in message.reactions],
                                'reaction_count': sum(r.count for r in message.reactions),
                                'has_attachments': bool(message.attachments),
                                'has_embeds': bool(message.embeds),
                                'metadata': {
                                    'content_length': len(message.content),
                                    'mention_count': len(message.mentions),
                                    'channel_mention_count': len(message.channel_mentions),
                                    'role_mention_count': len(message.role_mentions)
                                }
                            }
                            messages.append(message_data)

                        except Exception as e:
                            logger.debug(f"Error processing message {message.id}: {e}")
                            continue

                    all_messages.extend(messages)
                    logger.debug(f"Scraped {len(messages)} messages from {server_name}#{channel.name}")

                except Exception as e:
                    logger.warning(f"Failed to scrape channel {channel.name} in {server_name}: {e}")
                    continue

            return all_messages, {'server': server_name, 'channels_scraped': len(server.text_channels)}

        except Exception as e:
            logger.error(f"Error scraping server {server_name}: {e}")
            return [], {}

    async def _scrape_channel(self, server_name: str, channel_name: str) -> List[Dict[str, Any]]:
        """Scrape messages from a specific channel"""
        if not self.client or not self.connected:
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
                if hasattr(ch, 'name') and ch.name == channel_name:
                    channel = ch
                    break

            if not channel:
                logger.warning(f"Channel '{channel_name}' not found in {server_name}")
                return []

            # Get messages
            messages = []
            date_threshold = datetime.now() - timedelta(hours=self.hours_back)

            async for message in channel.history(limit=self.max_messages, after=date_threshold):
                try:
                    # Skip empty messages
                    if not message.content or len(message.content.strip()) < self.min_content_length:
                        continue

                    message_data = {
                        'id': self._generate_message_id(server_name, channel_name, message.id),
                        'discord_id': message.id,
                        'server': server_name,
                        'channel': channel_name,
                        'content': message.content.strip(),
                        'timestamp': message.created_at.isoformat(),
                        'author': str(message.author),
                        'author_id': message.author.id,
                        'reactions': [str(r.emoji) for r in message.reactions],
                        'reaction_count': sum(r.count for r in message.reactions),
                        'has_attachments': bool(message.attachments),
                        'has_embeds': bool(message.embeds),
                        'metadata': {
                            'content_length': len(message.content),
                            'mention_count': len(message.mentions),
                            'channel_mention_count': len(message.channel_mentions),
                            'role_mention_count': len(message.role_mentions)
                        }
                    }
                    messages.append(message_data)

                except Exception as e:
                    logger.debug(f"Error processing message {message.id}: {e}")
                    continue

            return messages

        except Exception as e:
            logger.error(f"Error scraping channel {server_name}#{channel_name}: {e}")
            return []

    def _filter_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter messages based on keywords"""
        if not self.keywords and not self.exclude_keywords:
            return messages

        filtered = []

        for message in messages:
            content = message.get('content', '').lower()

            # Check exclude keywords first
            if self.exclude_keywords:
                excluded = any(keyword.lower() in content for keyword in self.exclude_keywords)
                if excluded:
                    continue

            # Check include keywords
            if self.keywords:
                included = any(keyword.lower() in content for keyword in self.keywords)
                if not included:
                    continue

            filtered.append(message)

        return filtered

    def _generate_message_id(self, server: str, channel: str, message_id: int) -> str:
        """Generate unique ID for message"""
        content_hash = hashlib.md5(f"{server}_{channel}_{message_id}".encode()).hexdigest()[:8]
        return f"discord_{content_hash}"

    async def _cleanup(self) -> None:
        """Clean up resources"""
        await self._disconnect_client()
        self.client = None