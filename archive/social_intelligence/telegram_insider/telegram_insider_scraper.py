"""
Telegram Insider Scraper

Main scraper for monitoring Telegram insider channels
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.telegram_insider_config import TelegramInsiderConfig

from .telegram_client import TelegramInsiderClient
from .intel_parser import IntelParser, BettingIntel
from .arbitrage_alert_handler import ArbitrageAlertHandler, ArbitrageAlert

logger = logging.getLogger(__name__)

class TelegramInsiderScraper:
    """Scrape betting intelligence from Telegram insider channels"""
    
    def __init__(self, config: Optional[TelegramInsiderConfig] = None):
        self.config = config or TelegramInsiderConfig
        self.client = TelegramInsiderClient(self.config)
        self.parser = IntelParser()
        self.alert_handler = ArbitrageAlertHandler()
        self.scanned_messages = set()  # Track scanned messages
        self.intel_found = []
        
        logger.info("🎯 Telegram Insider Scraper initialized")
    
    async def scan_premium_channels(self) -> List[BettingIntel]:
        """Scan premium tipster channels for intelligence"""
        if not self.client.is_available:
            logger.warning("⚠️ Telegram client not available")
            return []
        
        logger.info("🔍 Scanning premium Telegram channels...")
        
        all_intel = []
        
        async with self.client:
            for channel in self.config.PREMIUM_CHANNELS:
                try:
                    logger.info(f"📊 Scanning {channel}...")
                    
                    messages = await self.client.get_channel_messages(
                        channel_username=channel,
                        limit=self.config.MAX_MESSAGES_PER_CHANNEL,
                        hours_back=24
                    )
                    
                    for message in messages:
                        message_key = f"{channel}_{message.get('id', 0)}"
                        
                        if message_key in self.scanned_messages:
                            continue
                        
                        # Parse intelligence from message
                        intel = self.parser.parse_message(message, channel)
                        
                        if intel:
                            all_intel.append(intel)
                            self.scanned_messages.add(message_key)
                            
                            # Handle arbitrage alerts immediately
                            if intel.intel_type == 'arbitrage':
                                await self.alert_handler.process_arbitrage_intel(
                                    intel.__dict__,
                                    channel,
                                    message.get('id', 0)
                                )
                    
                    # Rate limiting
                    await asyncio.sleep(self.config.RATE_LIMIT_DELAY)
                    
                except Exception as e:
                    logger.error(f"❌ Error scanning {channel}: {e}")
                    continue
        
        logger.info(f"✅ Found {len(all_intel)} intelligence items from premium channels")
        self.intel_found.extend(all_intel)
        
        return all_intel
    
    async def scan_free_channels(self) -> List[BettingIntel]:
        """Scan free channels for opportunities"""
        if not self.client.is_available:
            return []
        
        logger.info("🔍 Scanning free Telegram channels...")
        
        all_intel = []
        
        async with self.client:
            for channel in self.config.FREE_CHANNELS:
                try:
                    messages = await self.client.get_channel_messages(
                        channel_username=channel,
                        limit=30,  # Fewer messages for free channels
                        hours_back=12
                    )
                    
                    for message in messages:
                        message_key = f"{channel}_{message.get('id', 0)}"
                        
                        if message_key in self.scanned_messages:
                            continue
                        
                        intel = self.parser.parse_message(message, channel)
                        
                        if intel and intel.confidence >= 0.6:  # Higher threshold for free
                            all_intel.append(intel)
                            self.scanned_messages.add(message_key)
                    
                    await asyncio.sleep(self.config.RATE_LIMIT_DELAY * 2)  # Slower for free
                    
                except Exception as e:
                    logger.error(f"❌ Error scanning {channel}: {e}")
                    continue
        
        logger.info(f"✅ Found {len(all_intel)} intelligence items from free channels")
        self.intel_found.extend(all_intel)
        
        return all_intel
    
    async def cross_validate_with_predictions(
        self,
        intel: BettingIntel,
        our_predictions: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Cross-validate Telegram intel with our AI predictions
        
        Args:
            intel: BettingIntel from Telegram
            our_predictions: List of our AI predictions
        
        Returns:
            Enhanced prediction if validation passes, None otherwise
        """
        if not intel.match_info:
            return None
        
        # Find matching prediction
        home_team = intel.match_info.get('home_team', '').lower()
        away_team = intel.match_info.get('away_team', '').lower()
        
        for prediction in our_predictions:
            pred_match = prediction.get('match_info', {})
            if isinstance(pred_match, dict):
                pred_home = pred_match.get('home_team', '').lower()
                pred_away = pred_match.get('away_team', '').lower()
                
                if (home_team in pred_home or pred_home in home_team) and \
                   (away_team in pred_away or pred_away in away_team):
                    
                    # Check agreement
                    agreement = self._calculate_agreement(intel, prediction)
                    
                    if agreement > 0.75:  # 75% agreement threshold
                        # Boost confidence
                        enhanced = prediction.copy()
                        original_confidence = enhanced.get('confidence_score', 0.5)
                        enhanced['confidence_score'] = min(
                            1.0,
                            original_confidence * self.config.CONFIDENCE_BOOST_MULTIPLIER
                        )
                        enhanced['telegram_validation'] = {
                            'channel': intel.channel,
                            'agreement': agreement,
                            'intel_type': intel.intel_type
                        }
                        
                        return enhanced
        
        return None
    
    def _calculate_agreement(
        self,
        intel: BettingIntel,
        prediction: Dict[str, Any]
    ) -> float:
        """Calculate agreement score between intel and prediction"""
        if not intel.selection:
            return 0.0
        
        our_selection = prediction.get('recommended_bet', '').lower()
        intel_selection = intel.selection.lower()
        
        # Direct match
        if intel_selection in our_selection or our_selection in intel_selection:
            return 1.0
        
        # Partial match
        intel_words = set(intel_selection.split())
        our_words = set(our_selection.split())
        
        if intel_words.intersection(our_words):
            return 0.5
        
        return 0.0
    
    def get_intel_summary(self) -> Dict[str, Any]:
        """Get summary of intelligence found"""
        if not self.intel_found:
            return {
                'total_intel': 0,
                'by_type': {},
                'premium_count': 0,
                'free_count': 0
            }
        
        by_type = {}
        premium_count = 0
        free_count = 0
        
        for intel in self.intel_found:
            intel_type = intel.intel_type
            by_type[intel_type] = by_type.get(intel_type, 0) + 1
            
            if intel.channel in self.config.PREMIUM_CHANNELS:
                premium_count += 1
            else:
                free_count += 1
        
        return {
            'total_intel': len(self.intel_found),
            'by_type': by_type,
            'premium_count': premium_count,
            'free_count': free_count,
            'channels_scanned': len(self.config.PREMIUM_CHANNELS) + len(self.config.FREE_CHANNELS)
        }

