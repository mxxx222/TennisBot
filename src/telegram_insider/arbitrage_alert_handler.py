"""
Arbitrage Alert Handler

Handle real-time arbitrage alerts from Telegram channels
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class ArbitrageAlert:
    """Arbitrage opportunity alert"""
    alert_id: str
    channel: str
    message_id: int
    match_info: Dict[str, str]
    profit_percentage: float
    bookmakers: List[str]
    odds: Dict[str, float]
    confidence: float
    timestamp: str
    message_url: str

class ArbitrageAlertHandler:
    """Handle arbitrage alerts from Telegram"""
    
    def __init__(self):
        self.alerts_sent = set()  # Track sent alerts to avoid duplicates
        self.alert_callbacks = []  # Callbacks for alert notifications
        
        logger.info("✅ Arbitrage Alert Handler initialized")
    
    def register_callback(self, callback):
        """Register callback for arbitrage alerts"""
        self.alert_callbacks.append(callback)
    
    async def process_arbitrage_intel(
        self,
        intel: Dict[str, Any],
        channel: str,
        message_id: int
    ) -> Optional[ArbitrageAlert]:
        """
        Process arbitrage intelligence and create alert if valid
        
        Args:
            intel: BettingIntel object
            channel: Channel username
            message_id: Message ID
        
        Returns:
            ArbitrageAlert if valid, None otherwise
        """
        try:
            # Extract arbitrage data
            profit_percentage = self._extract_profit_percentage(intel.get('message_text', ''))
            
            if profit_percentage < 1.5:  # Minimum 1.5% profit
                return None
            
            # Extract bookmakers and odds
            bookmakers, odds = self._extract_bookmaker_odds(intel.get('message_text', ''))
            
            if not bookmakers or len(bookmakers) < 2:
                return None
            
            # Create alert
            alert_id = f"arb_{channel}_{message_id}_{int(datetime.now().timestamp())}"
            
            if alert_id in self.alerts_sent:
                return None  # Already sent
            
            alert = ArbitrageAlert(
                alert_id=alert_id,
                channel=channel,
                message_id=message_id,
                match_info=intel.get('match_info', {}),
                profit_percentage=profit_percentage,
                bookmakers=bookmakers,
                odds=odds,
                confidence=intel.get('confidence', 0.7),
                timestamp=datetime.now().isoformat(),
                message_url=f"https://t.me/{channel.lstrip('@')}/{message_id}"
            )
            
            # Send alert via callbacks
            await self._send_alert(alert)
            
            self.alerts_sent.add(alert_id)
            
            logger.info(f"💰 Arbitrage alert created: {profit_percentage:.2f}% profit")
            
            return alert
            
        except Exception as e:
            logger.error(f"❌ Error processing arbitrage intel: {e}")
            return None
    
    def _extract_profit_percentage(self, text: str) -> float:
        """Extract profit percentage from text"""
        import re
        
        # Look for profit percentage patterns
        patterns = [
            r'(\d+\.?\d*)\s*%?\s*profit',
            r'profit[:\s]+(\d+\.?\d*)%?',
            r'margin[:\s]+(\d+\.?\d*)%?',
            r'(\d+\.?\d*)\s*%?\s*margin',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    profit = float(match.group(1))
                    if 0 < profit < 50:  # Reasonable range
                        return profit
                except ValueError:
                    continue
        
        # Default: try to calculate from odds if mentioned
        return 0.0
    
    def _extract_bookmaker_odds(self, text: str) -> tuple[List[str], Dict[str, float]]:
        """Extract bookmaker names and odds from text"""
        import re
        
        bookmakers = []
        odds = {}
        
        # Common bookmaker names
        common_bookmakers = [
            'bet365', 'pinnacle', 'betfair', 'unibet', 'bwin', 'betway',
            'draftkings', 'fanduel', 'caesars', 'betmgm', 'william hill',
            'ladbrokes', 'coral', 'betvictor', 'skybet'
        ]
        
        text_lower = text.lower()
        
        # Find bookmakers mentioned
        for bookmaker in common_bookmakers:
            if bookmaker in text_lower:
                bookmakers.append(bookmaker)
        
        # Extract odds associated with bookmakers
        odds_pattern = r'(\d+\.\d+)'
        odds_matches = re.findall(odds_pattern, text)
        
        for i, odds_value in enumerate(odds_matches[:len(bookmakers)]):
            try:
                odds_float = float(odds_value)
                if 1.01 <= odds_float <= 100:
                    if i < len(bookmakers):
                        odds[bookmakers[i]] = odds_float
            except ValueError:
                continue
        
        return bookmakers, odds
    
    async def _send_alert(self, alert: ArbitrageAlert):
        """Send arbitrage alert via registered callbacks"""
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    def convert_to_roi_format(self, alert: ArbitrageAlert) -> Dict[str, Any]:
        """Convert alert to format expected by ROI analyzer"""
        if not alert.match_info:
            return {}
        
        home_team = alert.match_info.get('home_team', '')
        away_team = alert.match_info.get('away_team', '')
        
        if not home_team or not away_team:
            return {}
        
        # Convert to odds data format
        odds_data = {}
        
        for bookmaker in alert.bookmakers:
            if bookmaker not in odds_data:
                odds_data[bookmaker] = []
            
            # Try to match odds to outcomes
            match_odds = {
                'home_team': home_team,
                'away_team': away_team,
                'home_odds': alert.odds.get(bookmaker),
                'away_odds': None,  # Would need more parsing
                'source': 'telegram',
                'telegram_alert_id': alert.alert_id,
                'profit_percentage': alert.profit_percentage
            }
            
            odds_data[bookmaker].append(match_odds)
        
        return odds_data

