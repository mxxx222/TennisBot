"""
Intel Parser

Parse betting intelligence from Telegram messages
"""

import re
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BettingIntel:
    """Betting intelligence extracted from message"""
    intel_id: str
    channel: str
    message_id: int
    message_text: str
    intel_type: str  # 'tip', 'arbitrage', 'sharp_money', 'injury', 'lineup'
    match_info: Optional[Dict[str, str]]
    selection: Optional[str]
    odds: Optional[float]
    confidence: float
    reasoning: Optional[str]
    timestamp: str

class IntelParser:
    """Parse betting intelligence from Telegram messages"""
    
    def __init__(self):
        # Keywords for different intel types
        self.arbitrage_keywords = [
            'arbitrage', 'arb', 'sure bet', 'guaranteed profit',
            'risk free', 'free money', 'guaranteed win'
        ]
        
        self.sharp_money_keywords = [
            'sharp money', 'smart money', 'whale', 'big bet',
            'line movement', 'steam move', 'reverse line movement'
        ]
        
        self.injury_keywords = [
            'injury', 'injured', 'out', 'doubtful', 'questionable',
            'sidelined', 'medical', 'health'
        ]
        
        self.lineup_keywords = [
            'lineup', 'starting xi', 'team sheet', 'squad',
            'roster', 'confirmed team'
        ]
        
        logger.info("✅ Intel Parser initialized")
    
    def parse_message(self, message: Dict[str, Any], channel: str) -> Optional[BettingIntel]:
        """
        Parse betting intelligence from a Telegram message
        
        Args:
            message: Telegram message dictionary
            channel: Channel username
        
        Returns:
            BettingIntel object if intel found, None otherwise
        """
        text = message.get('text', '').lower()
        
        if not text or len(text) < 10:
            return None
        
        # Determine intel type
        intel_type = self._detect_intel_type(text)
        
        if not intel_type:
            return None
        
        # Extract match information
        match_info = self._extract_match_info(message.get('text', ''))
        
        # Extract selection/odds
        selection = None
        odds = None
        
        if intel_type in ['tip', 'arbitrage']:
            selection = self._extract_selection(message.get('text', ''))
            odds = self._extract_odds(message.get('text', ''))
        
        # Calculate confidence
        confidence = self._calculate_confidence(message, intel_type, channel)
        
        # Extract reasoning
        reasoning = self._extract_reasoning(message.get('text', ''))
        
        # Generate intel ID
        intel_id = f"telegram_{channel}_{message.get('id', 0)}_{intel_type}"
        
        return BettingIntel(
            intel_id=intel_id,
            channel=channel,
            message_id=message.get('id', 0),
            message_text=message.get('text', '')[:500],  # Limit length
            intel_type=intel_type,
            match_info=match_info,
            selection=selection,
            odds=odds,
            confidence=confidence,
            reasoning=reasoning,
            timestamp=datetime.now().isoformat()
        )
    
    def _detect_intel_type(self, text: str) -> Optional[str]:
        """Detect type of betting intelligence"""
        text_lower = text.lower()
        
        # Check for arbitrage
        if any(keyword in text_lower for keyword in self.arbitrage_keywords):
            return 'arbitrage'
        
        # Check for sharp money
        if any(keyword in text_lower for keyword in self.sharp_money_keywords):
            return 'sharp_money'
        
        # Check for injury
        if any(keyword in text_lower for keyword in self.injury_keywords):
            return 'injury'
        
        # Check for lineup
        if any(keyword in text_lower for keyword in self.lineup_keywords):
            return 'lineup'
        
        # Check for betting tip (odds, team names, etc.)
        if self._contains_betting_tip(text):
            return 'tip'
        
        return None
    
    def _contains_betting_tip(self, text: str) -> bool:
        """Check if text contains a betting tip"""
        betting_keywords = [
            'bet', 'pick', 'tip', 'play', 'lock', 'take',
            'odds', 'moneyline', 'over', 'under', 'spread'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in betting_keywords)
    
    def _extract_match_info(self, text: str) -> Optional[Dict[str, str]]:
        """Extract match information from text"""
        # Patterns for match descriptions
        vs_patterns = [
            r'([A-Z][a-zA-Z\s]+)\s+vs\s+([A-Z][a-zA-Z\s]+)',
            r'([A-Z][a-zA-Z\s]+)\s+@\s+([A-Z][a-zA-Z\s]+)',
            r'([A-Z][a-zA-Z\s]+)\s+v\s+([A-Z][a-zA-Z\s]+)',
        ]
        
        for pattern in vs_patterns:
            match = re.search(pattern, text)
            if match:
                home_team = match.group(1).strip()
                away_team = match.group(2).strip()
                
                if len(home_team) > 2 and len(away_team) > 2:
                    return {
                        'home_team': home_team,
                        'away_team': away_team,
                        'match_text': f"{home_team} vs {away_team}"
                    }
        
        return None
    
    def _extract_selection(self, text: str) -> Optional[str]:
        """Extract betting selection from text"""
        # Patterns for selections
        selection_patterns = [
            r'bet\s+(?:on\s+)?([A-Z][a-zA-Z\s]+)',
            r'pick\s+(?:is\s+)?([A-Z][a-zA-Z\s]+)',
            r'take\s+([A-Z][a-zA-Z\s]+)',
            r'([A-Z][a-zA-Z\s]+)\s+(?:to\s+)?win',
            r'lock[:\s]+([A-Z][a-zA-Z\s]+)',
        ]
        
        for pattern in selection_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                selection = match.group(1).strip()
                if len(selection) > 2:
                    return selection
        
        return None
    
    def _extract_odds(self, text: str) -> Optional[float]:
        """Extract odds from text"""
        # Decimal odds patterns
        odds_patterns = [
            r'(\d+\.\d+)\s*(?:odds|@|to)',
            r'odds?\s*(?:of|are|at)?\s*(\d+\.\d+)',
            r'@\s*(\d+\.\d+)',
        ]
        
        for pattern in odds_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    odds = float(match.group(1))
                    if 1.01 <= odds <= 100:  # Valid odds range
                        return odds
                except ValueError:
                    continue
        
        return None
    
    def _calculate_confidence(
        self,
        message: Dict[str, Any],
        intel_type: str,
        channel: str
    ) -> float:
        """Calculate confidence score for the intelligence"""
        confidence = 0.5  # Base confidence
        
        # Boost for premium channels
        from config.telegram_insider_config import TelegramInsiderConfig
        if channel in TelegramInsiderConfig.PREMIUM_CHANNELS:
            confidence += 0.2
        
        # Boost for message engagement
        views = message.get('views', 0)
        if views > 100:
            confidence += 0.1
        if views > 1000:
            confidence += 0.1
        
        # Boost for arbitrage (guaranteed profit)
        if intel_type == 'arbitrage':
            confidence += 0.2
        
        # Boost for sharp money intel
        if intel_type == 'sharp_money':
            confidence += 0.15
        
        return min(1.0, confidence)
    
    def _extract_reasoning(self, text: str) -> Optional[str]:
        """Extract reasoning/analysis from text"""
        # Look for reasoning patterns
        reasoning_patterns = [
            r'because\s+(.+?)(?:\.|$)',
            r'reason[:\s]+(.+?)(?:\.|$)',
            r'analysis[:\s]+(.+?)(?:\.|$)',
            r'why[:\s]+(.+?)(?:\.|$)',
        ]
        
        for pattern in reasoning_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                reasoning = match.group(1).strip()
                if len(reasoning) > 10:
                    return reasoning[:200]  # Limit length
        
        return None

