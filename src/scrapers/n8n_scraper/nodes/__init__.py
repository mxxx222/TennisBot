# N8N-Style Web Scraper Nodes
# Modular nodes for data collection from various sources

from .base_node import BaseNode, SourceNode, DataNode, NodeExecutionResult
from .web_scraper_node import WebScraperNode
from .telegram_scraper_node import TelegramScraperNode
from .discord_scraper_node import DiscordScraperNode
from .data_filter_node import DataFilterNode
from .data_transformer_node import DataTransformerNode
from .database_storage_node import DatabaseStorageNode

__all__ = [
    'BaseNode', 'SourceNode', 'DataNode', 'NodeExecutionResult',
    'WebScraperNode', 'TelegramScraperNode', 'DiscordScraperNode',
    'DataFilterNode', 'DataTransformerNode', 'DatabaseStorageNode'
]