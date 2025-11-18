"""
Discord Intelligence Scraper

Main scraper for monitoring Discord betting servers
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import re
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.discord_config import DiscordConfig

from .discord_client import DiscordIntelligenceClient
from .sharp_bettor_tracker import SharpBettorTracker, SharpPick
from .community_intelligence import CommunityIntelligence

logger = logging.getLogger(__name__)

class DiscordIntelligenceScraper:
    """Scrape intelligence from Discord betting servers"""
    
    def __init__(self, config: Optional[DiscordConfig] = None):
        self.config = config or DiscordConfig
        self.client = DiscordIntelligenceClient(self.config)
        self.sharp_tracker = SharpBettorTracker()
        self.community_intel = CommunityIntelligence()
        self.scanned_messages = set()
        
        logger.info("🎯 Discord Intelligence Scraper initialized")
    
    async def scan_premium_servers(self) -> List[SharpPick]:
        """Scan premium Discord servers for sharp bettor picks"""
        if not self.client.is_available:
            logger.warning("⚠️ Discord client not available")
            return []
        
        logger.info("🔍 Scanning premium Discord servers...")
        
        all_picks = []
        
        async with self.client:
            for server_name in self.config.PREMIUM_SERVERS:
                try:
                    for channel_name in self.config.MONITORED_CHANNELS:
                        messages = await self.client.get_server_messages(
                            server_name=server_name,
                            channel_name=channel_name,
                            limit=self.config.MAX_MESSAGES_PER_CHANNEL,
                            hours_back=24
                        )
                        
                        for message in messages:
                            message_key = f"{server_name}_{channel_name}_{message.get('id', 0)}"
                            
                            if message_key in self.scanned_messages:
                                continue
                            
                            # Extract betting picks
                            pick = self._extract_pick(message, server_name, channel_name)
                            
                            if pick:
                                user_id = message.get('author_id', 0)
                                
                                # Register user if not exists
                                if user_id not in self.sharp_tracker.sharp_bettors:
                                    self.sharp_tracker.register_sharp_bettor(
                                        user_id=user_id,
                                        username=message.get('author', 'Unknown'),
                                        verified=False
                                    )
                                
                                # Record pick
                                self.sharp_tracker.record_pick(user_id, pick)
                                
                                # Check if from verified sharp
                                if self.sharp_tracker.is_verified_sharp(user_id):
                                    sharp_pick = SharpPick(
                                        pick_id=pick.get('pick_id', ''),
                                        user_id=user_id,
                                        username=message.get('author', ''),
                                        match_info=pick.get('match_info', {}),
                                        selection=pick.get('selection', ''),
                                        reasoning=pick.get('reasoning'),
                                        timestamp=message.get('created_at', datetime.now().isoformat()),
                                        channel=channel_name,
                                        server=server_name
                                    )
                                    all_picks.append(sharp_pick)
                            
                            # Process for community intelligence
                            match_info = self._extract_match_info(message.get('content', ''))
                            if match_info:
                                self.community_intel.process_message(message, match_info)
                            
                            self.scanned_messages.add(message_key)
                        
                        await asyncio.sleep(self.config.RATE_LIMIT_DELAY)
                    
                except Exception as e:
                    logger.error(f"❌ Error scanning {server_name}: {e}")
                    continue
        
        logger.info(f"✅ Found {len(all_picks)} sharp picks from premium servers")
        return all_picks
    
    def _extract_pick(
        self,
        message: Dict[str, Any],
        server: str,
        channel: str
    ) -> Optional[Dict[str, Any]]:
        """Extract betting pick from message"""
        content = message.get('content', '')
        
        # Check if contains betting language
        betting_keywords = ['bet', 'pick', 'lock', 'take', 'play', 'odds']
        if not any(keyword in content.lower() for keyword in betting_keywords):
            return None
        
        # Extract match info
        match_info = self._extract_match_info(content)
        if not match_info:
            return None
        
        # Extract selection
        selection = self._extract_selection(content, match_info)
        
        # Extract reasoning
        reasoning = self._extract_reasoning(content)
        
        pick_id = f"discord_{server}_{channel}_{message.get('id', 0)}"
        
        return {
            'pick_id': pick_id,
            'match_info': match_info,
            'selection': selection,
            'reasoning': reasoning,
            'channel': channel,
            'server': server
        }
    
    def _extract_match_info(self, text: str) -> Optional[Dict[str, str]]:
        """Extract match information from text"""
        vs_patterns = [
            r'([A-Z][a-zA-Z\s]+)\s+vs\s+([A-Z][a-zA-Z\s]+)',
            r'([A-Z][a-zA-Z\s]+)\s+@\s+([A-Z][a-zA-Z\s]+)',
        ]
        
        for pattern in vs_patterns:
            match = re.search(pattern, text)
            if match:
                home_team = match.group(1).strip()
                away_team = match.group(2).strip()
                
                if len(home_team) > 2 and len(away_team) > 2:
                    return {
                        'home_team': home_team,
                        'away_team': away_team
                    }
        
        return None
    
    def _extract_selection(
        self,
        text: str,
        match_info: Dict[str, str]
    ) -> Optional[str]:
        """Extract betting selection from text"""
        home_team = match_info.get('home_team', '').lower()
        away_team = match_info.get('away_team', '').lower()
        text_lower = text.lower()
        
        # Check for explicit mentions
        if home_team in text_lower:
            if any(word in text_lower for word in ['win', 'take', 'pick', 'bet']):
                return match_info['home_team']
        
        if away_team in text_lower:
            if any(word in text_lower for word in ['win', 'take', 'pick', 'bet']):
                return match_info['away_team']
        
        return None
    
    def _extract_reasoning(self, text: str) -> Optional[str]:
        """Extract reasoning from text"""
        reasoning_patterns = [
            r'because\s+(.+?)(?:\.|$)',
            r'reason[:\s]+(.+?)(?:\.|$)',
        ]
        
        for pattern in reasoning_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                reasoning = match.group(1).strip()
                if len(reasoning) > 10:
                    return reasoning[:200]
        
        return None
    
    async def cross_validate_sharp_picks(
        self,
        sharp_picks: List[SharpPick],
        our_predictions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Cross-validate sharp picks with our predictions"""
        validated = []
        
        for pick in sharp_picks:
            # Find matching prediction
            for prediction in our_predictions:
                pred_match = prediction.get('match_info', {})
                if isinstance(pred_match, dict):
                    if (pick.match_info.get('home_team', '').lower() in 
                        pred_match.get('home_team', '').lower()):
                        
                        # Check agreement
                        our_selection = prediction.get('recommended_bet', '').lower()
                        pick_selection = pick.selection.lower()
                        
                        if pick_selection in our_selection or our_selection in pick_selection:
                            # Sharp agrees - boost confidence
                            enhanced = prediction.copy()
                            from config.discord_config import DiscordConfig
                            
                            original_confidence = enhanced.get('confidence_score', 0.5)
                            enhanced['confidence_score'] = min(
                                1.0,
                                original_confidence * DiscordConfig.SHARP_AGREEMENT_BOOST
                            )
                            enhanced['sharp_validation'] = {
                                'sharp_username': pick.username,
                                'pick_id': pick.pick_id
                            }
                            
                            validated.append(enhanced)
        
        return validated

