#!/usr/bin/env python3
"""
Telegram Scraper Node for N8N-Style Scraper

Scrapes text content from Telegram channels and groups.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import hashlib
import os

from .base_node import SourceNode, NodeExecutionResult

# Optional Telethon support
try:
    from telethon import TelegramClient
    from telethon.tl.types import Channel, User
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    TelegramClient = None

logger = logging.getLogger(__name__)


class TelegramScraperNode(SourceNode):
    """
    Node for scraping text content from Telegram channels and groups.

    Supports:
    - Multiple channels/groups
    - Message filtering by time and content
    - Rate limiting and error handling
    - Message metadata extraction
    """

    def __init__(self, node_id: str, config: Dict[str, Any]):
        super().__init__(node_id, config)

        # Telegram configuration
        self.channels = config.get('channels', [])
        self.api_id = config.get('api_id') or os.getenv('TELEGRAM_API_ID')
        self.api_hash = config.get('api_hash') or os.getenv('TELEGRAM_API_HASH')
        self.phone_number = config.get('phone_number') or os.getenv('TELEGRAM_PHONE_NUMBER')
        self.session_name = config.get('session_name', 'n8n_telegram_scraper')

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
        if not self.channels:
            raise ValueError("No Telegram channels provided")

        if not all([self.api_id, self.api_hash, self.phone_number]):
            logger.warning("Telegram API credentials not fully configured")
            self.is_available = False
        elif not TELETHON_AVAILABLE:
            logger.warning("Telethon library not available. Install with: pip install telethon")
            self.is_available = False
        else:
            self.is_available = True

    @property
    def inputs(self) -> List[str]:
        return ['trigger', 'optional_channels']

    @property
    def outputs(self) -> List[str]:
        return ['data', 'metadata']

    async def execute(self, input_data: Dict[str, Any]) -> NodeExecutionResult:
        """Execute Telegram scraping"""
        if not self.is_available:
            return NodeExecutionResult(
                success=False,
                error="Telegram client not available - check configuration and dependencies",
                node_id=self.node_id
            )

        try:
            # Get channels to scrape
            channels_to_scrape = self._get_channels_to_scrape(input_data)

            if not channels_to_scrape:
                return NodeExecutionResult(
                    success=False,
                    error="No channels to scrape",
                    node_id=self.node_id
                )

            # Initialize and connect client
            await self._init_client()
            await self._connect_client()

            scraped_messages = []
            metadata = {
                'total_channels': len(channels_to_scrape),
                'successful_channels': 0,
                'failed_channels': 0,
                'total_messages': 0,
                'filtered_messages': 0,
                'channels_scraped': [],
                'time_range': f"{self.hours_back} hours back"
            }

            # Scrape each channel
            for channel in channels_to_scrape:
                try:
                    messages = await self._scrape_channel(channel)
                    if messages:
                        scraped_messages.extend(messages)
                        metadata['successful_channels'] += 1
                        metadata['total_messages'] += len(messages)
                        metadata['channels_scraped'].append(channel)

                        logger.info(f"✅ Scraped {len(messages)} messages from {channel}")
                    else:
                        metadata['failed_channels'] += 1
                        logger.warning(f"⚠️ No messages scraped from {channel}")

                except Exception as e:
                    logger.error(f"Failed to scrape {channel}: {e}")
                    metadata['failed_channels'] += 1
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
                    'channels_scraped': metadata['channels_scraped'],
                    'message_count': len(scraped_messages)
                },
                metadata=metadata,
                node_id=self.node_id
            )

        except Exception as e:
            logger.error(f"Telegram scraping failed: {e}")
            await self._cleanup()
            return NodeExecutionResult(
                success=False,
                error=str(e),
                node_id=self.node_id
            )

    def _get_channels_to_scrape(self, input_data: Dict[str, Any]) -> List[str]:
        """Get channels to scrape from config and inputs"""
        channels = list(self.channels)  # Copy config channels

        # Add channels from input if provided
        if 'optional_channels' in input_data:
            additional_channels = input_data['optional_channels']
            if isinstance(additional_channels, list):
                channels.extend(additional_channels)
            elif isinstance(additional_channels, str):
                channels.append(additional_channels)

        # Remove duplicates while preserving order
        seen = set()
        unique_channels = []
        for channel in channels:
            # Normalize channel names (remove @ if present)
            normalized = channel.lstrip('@')
            if normalized not in seen:
                seen.add(normalized)
                unique_channels.append(normalized)

        return unique_channels

    async def _init_client(self) -> None:
        """Initialize Telegram client"""
        if not TELETHON_AVAILABLE:
            raise RuntimeError("Telethon library not available")

        try:
            self.client = TelegramClient(
                self.session_name,
                int(self.api_id),
                self.api_hash
            )
            logger.debug("Telegram client initialized")

        except Exception as e:
            raise RuntimeError(f"Failed to initialize Telegram client: {e}")

    async def _connect_client(self) -> None:
        """Connect to Telegram"""
        if not self.client:
            raise RuntimeError("Client not initialized")

        try:
            await self.client.start(phone=self.phone_number)
            self.connected = True
            logger.debug("Connected to Telegram")

        except Exception as e:
            raise RuntimeError(f"Failed to connect to Telegram: {e}")

    async def _disconnect_client(self) -> None:
        """Disconnect from Telegram"""
        if self.client and self.connected:
            await self.client.disconnect()
            self.connected = False
            logger.debug("Disconnected from Telegram")

    async def _scrape_channel(self, channel_username: str) -> List[Dict[str, Any]]:
        """Scrape messages from a single channel"""
        if not self.client or not self.connected:
            return []

        try:
            # Get channel entity
            entity = await self.client.get_entity(channel_username)

            # Calculate date threshold
            date_threshold = datetime.now() - timedelta(hours=self.hours_back)

            messages = []
            async for message in self.client.iter_messages(
                entity,
                limit=self.max_messages,
                offset_date=date_threshold
            ):
                try:
                    # Skip empty messages
                    if not message.text or len(message.text.strip()) < self.min_content_length:
                        continue

                    # Extract message data
                    message_data = {
                        'id': self._generate_message_id(channel_username, message.id),
                        'telegram_id': message.id,
                        'channel': channel_username,
                        'content': message.text.strip(),
                        'timestamp': message.date.isoformat() if message.date else datetime.now().isoformat(),
                        'author_id': message.from_id.user_id if message.from_id else None,
                        'views': message.views or 0,
                        'forwards': message.forwards or 0,
                        'replies': message.replies.replies if hasattr(message.replies, 'replies') and message.replies else 0,
                        'is_reply': message.is_reply,
                        'has_media': bool(message.media),
                        'metadata': {
                            'content_length': len(message.text),
                            'has_links': bool(message.entities) if message.entities else False,
                            'message_type': 'text'
                        }
                    }

                    messages.append(message_data)

                except Exception as e:
                    logger.debug(f"Error processing message {message.id}: {e}")
                    continue

            return messages

        except Exception as e:
            logger.error(f"Error scraping channel {channel_username}: {e}")
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

    def _generate_message_id(self, channel: str, message_id: int) -> str:
        """Generate unique ID for message"""
        content_hash = hashlib.md5(f"{channel}_{message_id}".encode()).hexdigest()[:8]
        return f"telegram_{content_hash}"

    async def _cleanup(self) -> None:
        """Clean up resources"""
        await self._disconnect_client()
        self.client = None