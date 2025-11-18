"""
Unified alert management system for soccer and tennis monitoring
Handles intelligent notification delivery with sport-specific formatting and urgency levels
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import json

from telegram import Bot
from telegram.error import TelegramError

from config.live_config import LiveMonitoringConfig, ALERT_TEMPLATES
from monitors.value_detector import ValueOpportunity
from monitors.odds_tracker import OddsMovement

logger = logging.getLogger(__name__)

@dataclass
class AlertContext:
    """Context information for alert delivery"""
    opportunity: ValueOpportunity
    alert_type: str  # 'VALUE_ENTRY', 'SIGNIFICANT_MOVEMENT', 'URGENT_UPDATE', 'SHARP_MONEY'
    priority: int  # 1-5 (5 = highest)
    should_send: bool = True
    reason: str = ""
    movement_history: List[OddsMovement] = None
    urgency_factors: List[str] = None
    betfury_links: Dict[str, str] = None
    sharp_money_indicator: Optional[float] = None

class AlertManager:
    """Manages intelligent alert delivery with rate limiting and prioritization"""
    
    def __init__(self):
        self.config = LiveMonitoringConfig()
        self.bot = Bot(token=self.config.TELEGRAM_BOT_TOKEN)
        
        # Alert tracking
        self.sent_alerts: Dict[str, datetime] = {}
        self.daily_alert_count = 0
        self.last_reset_date = datetime.now().date()
        
        # Rate limiting per match
        self.match_alert_counts: Dict[str, int] = {}
        self.match_last_alerts: Dict[str, datetime] = {}
        
        # Performance tracking
        self.total_alerts_sent = 0
        self.failed_alerts = 0
        
    async def process_opportunities(self, opportunities: List[ValueOpportunity],
                                 movements: List[OddsMovement]) -> Dict[str, bool]:
        """Process opportunities and send appropriate alerts"""
        
        self._reset_daily_counters_if_needed()
        
        # Create alert contexts
        alert_contexts = []
        for opportunity in opportunities:
            context = self._create_alert_context(opportunity, movements)
            if context.should_send:
                alert_contexts.append(context)
        
        # Sort by priority
        alert_contexts.sort(key=lambda x: x.priority, reverse=True)
        
        # Send alerts with rate limiting
        results = {}
        for context in alert_contexts:
            if self._should_send_alert(context):
                success = await self._send_alert(context)
                results[context.opportunity.match_id] = success
                
                if success:
                    self._update_alert_tracking(context)
            else:
                logger.debug(f"Skipped alert for {context.opportunity.match_id}: {context.reason}")
                results[context.opportunity.match_id] = False
        
        return results
    
    async def send_alert(self, context: AlertContext) -> bool:
        """Send enhanced alert with multi-source context"""
        try:
            if not self._should_send_alert(context):
                return False
            
            success = await self._send_alert(context)
            if success:
                self._update_alert_tracking(context)
            
            return success
            
        except Exception as e:
            logger.error(f"💥 Enhanced alert sending error: {e}")
            return False
    
    def _create_alert_context(self, opportunity: ValueOpportunity,
                            movements: List[OddsMovement]) -> AlertContext:
        """Create alert context with appropriate type and priority"""
        
        # Determine alert type - check for sharp money first
        if hasattr(opportunity, 'ai_reasoning') and opportunity.ai_reasoning and "[SHARP MONEY]" in opportunity.ai_reasoning:
            alert_type = 'SHARP_MONEY'
        elif opportunity.movement_direction == 'entering':
            alert_type = 'VALUE_ENTRY'
        elif opportunity.urgency_level in ['HIGH', 'CRITICAL']:
            alert_type = 'URGENT_UPDATE'
        else:
            alert_type = 'VALUE_ENTRY'
        
        # Calculate priority (1-5 scale) - boost for sharp money
        priority = self._calculate_alert_priority(opportunity)
        if alert_type == 'SHARP_MONEY':
            priority = min(5, priority + 1)  # Boost sharp money alerts
        
        # Check if we should send this alert
        should_send, reason = self._evaluate_send_decision(opportunity)
        
        # Extract sharp money indicator if available
        sharp_money_indicator = None
        if hasattr(opportunity, 'sharp_money_indicator'):
            sharp_money_indicator = opportunity.sharp_money_indicator
        
        return AlertContext(
            opportunity=opportunity,
            alert_type=alert_type,
            priority=priority,
            should_send=should_send,
            reason=reason,
            movement_history=movements,
            urgency_factors=[],
            betfury_links={},
            sharp_money_indicator=sharp_money_indicator
        )
    
    def _calculate_alert_priority(self, opportunity: ValueOpportunity) -> int:
        """Calculate alert priority (1-5, where 5 is highest)"""
        
        priority = 3  # Base priority
        
        # Urgency level adjustment
        urgency_adjustments = {
            'CRITICAL': +2,
            'HIGH': +1,
            'MEDIUM': 0,
            'LOW': -1
        }
        priority += urgency_adjustments.get(opportunity.urgency_level, 0)
        
        # Edge quality adjustment
        if opportunity.edge_estimate >= 5.0:
            priority += 1
        elif opportunity.edge_estimate >= 3.0:
            priority += 0.5
        elif opportunity.edge_estimate < 1.0:
            priority -= 1
        
        # League quality adjustment
        league_tier = self.config.get_league_tier(opportunity.league)
        if league_tier == 1:
            priority += 1
        elif league_tier == 3:
            priority -= 0.5
        
        # Movement context adjustment
        if opportunity.movement_direction == 'entering':
            priority += 1
        elif opportunity.movement_direction == 'exiting':
            priority -= 1
        
        # Time sensitivity adjustment
        if opportunity.time_sensitivity >= 0.8:
            priority += 1
        elif opportunity.time_sensitivity >= 0.6:
            priority += 0.5
        
        return max(1, min(5, int(priority)))
    
    def _evaluate_send_decision(self, opportunity: ValueOpportunity) -> tuple[bool, str]:
        """Evaluate whether to send alert for this opportunity"""
        
        # Check daily limit
        if self.daily_alert_count >= self.config.MAX_DAILY_ALERTS:
            return False, "Daily alert limit reached"
        
        # Check per-match limit
        match_count = self.match_alert_counts.get(opportunity.match_id, 0)
        if match_count >= self.config.MAX_ALERTS_PER_MATCH:
            return False, "Per-match alert limit reached"
        
        # Check cooldown period
        last_alert = self.match_last_alerts.get(opportunity.match_id)
        if last_alert:
            time_since_last = (datetime.now() - last_alert).total_seconds()
            if time_since_last < self.config.ALERT_COOLDOWN:
                return False, f"Cooldown active ({int(self.config.ALERT_COOLDOWN - time_since_last)}s remaining)"
        
        # Check minimum edge threshold for alerts
        if opportunity.edge_estimate < 1.0:
            return False, "Edge below minimum threshold"
        
        # Check time to match (don't alert for very distant matches)
        time_to_match = (opportunity.commence_time - datetime.now()).total_seconds() / 3600
        if time_to_match > 48:
            return False, "Match too far in future"
        
        return True, "Alert approved"
    
    def _should_send_alert(self, context: AlertContext) -> bool:
        """Final check before sending alert"""
        
        if not context.should_send:
            return False
        
        # Priority threshold (only send high priority alerts during high volume)
        if self.daily_alert_count > self.config.MAX_DAILY_ALERTS * 0.8:
            if context.priority < 4:
                return False
        
        return True
    
    async def _send_alert(self, context: AlertContext) -> bool:
        """Send the actual alert message"""
        
        try:
            message = self._format_alert_message(context)
            
            await self.bot.send_message(
                chat_id=self.config.TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
            self.total_alerts_sent += 1
            logger.info(f"Sent {context.alert_type} alert for {context.opportunity.team}")
            return True
            
        except TelegramError as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            self.failed_alerts += 1
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending alert: {e}")
            self.failed_alerts += 1
            return False
    
    def _format_alert_message(self, context: AlertContext) -> str:
        """Format alert message based on context - Multi-sport support"""
        
        opp = context.opportunity
        
        # Determine sport type
        sport = getattr(opp, 'sport', 'soccer')  # Default to soccer for backward compatibility
        
        # Get urgency emoji
        urgency_emoji = self.config.get_urgency_emoji(opp.urgency_level)
        
        # Format odds movement
        if opp.previous_odds:
            if opp.odds < opp.previous_odds:
                direction = "⬇️"
            else:
                direction = "⬆️"
            odds_display = f"{opp.previous_odds:.2f} → {opp.odds:.2f} {direction}"
        else:
            odds_display = f"{opp.odds:.2f}"
        
        # Format match time
        match_time = opp.commence_time.strftime('%H:%M')
        match_date = opp.commence_time.strftime('%d.%m')
        
        # Sport-specific formatting
        if sport == 'tennis':
            # Tennis-specific alert templates
            if context.alert_type == 'SHARP_MONEY':
                template = "🔥 **TENNIS SHARP MONEY** 🔥\n\n🎾 **{player1}** vs **{player2}**\n📊 Odds: {odds_display}\n💰 Stake: ${stake:.2f}\n🎯 Edge: {edge:.1%}\n⚡ Sharp Money: {sharp_indicator:.1%}\n⏰ {match_time}\n🏆 {tournament} ({surface})"
            elif context.alert_type == 'VALUE_ENTRY':
                template = "🎾 **ITF TENNIS PICK** 🎾\n\n**{player1}** vs **{player2}**\n📊 Odds: {odds_display}\n💰 Stake: ${stake:.2f}\n🎯 Edge: {edge:.1%}\n⭐ Confidence: {confidence}\n⏰ {match_time}\n🏆 {tournament} ({surface})\n\n🎾 ITF Women • Proven +17.81% ROI Edge"
            else:
                template = "🎾 **TENNIS MOVEMENT** 🎾\n\n**{player1}** vs **{player2}**\n📊 Odds: {odds_display}\n💰 Stake: ${stake:.2f}\n🎯 Edge: {edge:.1%}\n⏰ {match_time}\n🏆 {tournament}"
            
            # Format league/tournament name for tennis
            tournament_display = opp.league.replace('ITF_', 'ITF ').replace('_', ' ').title()
            surface = getattr(opp, 'surface', 'Hard')
            
        else:
            # Soccer-specific alert templates (existing logic)
            if context.alert_type == 'SHARP_MONEY':
                template = "🔥 **SHARP MONEY ALERT** 🔥\n\n⚽ **{home_team}** vs **{away_team}**\n📊 Odds: {odds_display}\n💰 Stake: ${stake:.2f}\n🎯 Edge: {edge:.1%}\n⚡ Sharp Money: {sharp_indicator:.1%}\n⏰ {match_time}\n🏆 {league}"
            elif context.alert_type == 'VALUE_ENTRY':
                template = ALERT_TEMPLATES['VALUE_ENTRY']
            else:
                template = ALERT_TEMPLATES['SIGNIFICANT_MOVEMENT']
            
            # Format league name for soccer
            league_display = opp.league.replace('soccer_', '').replace('_', ' ').title()
        
        # Format the message based on sport
        if context.alert_type == 'SHARP_MONEY':
            if sport == 'tennis':
                message = template.format(
                    player1=opp.team,
                    player2=opp.opponent,
                    odds_display=odds_display,
                    stake=opp.recommended_stake,
                    edge=opp.edge_estimate,
                    sharp_indicator=context.sharp_money_indicator or 0.0,
                    match_time=f"{match_time} ({match_date})",
                    tournament=tournament_display,
                    surface=surface
                )
            else:
                message = template.format(
                    home_team=opp.team,
                    away_team=opp.opponent,
                    odds_display=odds_display,
                    stake=opp.recommended_stake,
                    edge=opp.edge_estimate,
                    sharp_indicator=context.sharp_money_indicator or 0.0,
                    match_time=f"{match_time} ({match_date})",
                    league=league_display
                )
        else:
            if sport == 'tennis':
                message = template.format(
                    emoji=urgency_emoji,
                    player1=opp.team,
                    player2=opp.opponent,
                    old_odds=opp.previous_odds or opp.odds,
                    new_odds=opp.odds,
                    odds_display=odds_display,
                    direction=direction if opp.previous_odds else "",
                    stake=opp.recommended_stake,
                    confidence=opp.confidence,
                    edge=opp.edge_estimate,
                    match_time=f"{match_time} ({match_date})",
                    tournament=tournament_display,
                    surface=surface,
                    urgency=opp.urgency_level.title(),
                    status="QUALIFIED" if 1.30 <= opp.odds <= 1.80 else "MONITORING"  # Tennis range
                )
            else:
                message = template.format(
                    emoji=urgency_emoji,
                    home_team=opp.team,
                    away_team=opp.opponent,
                    old_odds=opp.previous_odds or opp.odds,
                    new_odds=opp.odds,
                    direction=direction if opp.previous_odds else "",
                    stake=opp.recommended_stake,
                    confidence=opp.confidence,
                    edge=opp.edge_estimate,
                    match_time=f"{match_time} ({match_date})",
                    league=league_display,
                    urgency=opp.urgency_level.title(),
                    status="QUALIFIED" if self.config.MIN_ODDS <= opp.odds <= self.config.MAX_ODDS else "MONITORING"
                )
        
        # Add hybrid AI enhancement info if available
        if getattr(opp, 'ai_enhanced', False):
            ai_confidence = getattr(opp, 'ai_confidence', 0)
            ai_reasoning = getattr(opp, 'ai_reasoning', '')
            ai_cost = getattr(opp, 'ai_cost', 0)
            ai_provider = getattr(opp, 'ai_provider', 'venice')
            is_premium = getattr(opp, 'is_premium_analysis', False)
            
            # Add AI provider and confidence indicator
            if is_premium:
                ai_emoji = '🏆'  # Premium analysis
                ai_label = f"**{ai_provider.upper()} PREMIUM**"
            elif ai_confidence > 0.7:
                ai_emoji = '🤖'  # High confidence
                ai_label = f"**{ai_provider.upper()} AI**"
            else:
                ai_emoji = '🔍'  # Standard analysis
                ai_label = f"**{ai_provider.upper()} AI**"
            
            ai_line = f"\n{ai_emoji} {ai_label} (Confidence: {ai_confidence:.1%})"
            
            # Add concise AI reasoning if available
            if ai_reasoning and len(ai_reasoning) < 80:
                # Clean up reasoning for Telegram
                clean_reasoning = ai_reasoning.replace('[PREMIUM]', '').strip()
                ai_line += f"\n💡 *{clean_reasoning[:80]}*"
            
            # Add cost info for high-value opportunities
            if opp.urgency_level in ['HIGH', 'CRITICAL'] and ai_cost > 0:
                if ai_provider == 'venice':
                    # Show savings vs OpenAI
                    openai_cost = ai_cost * 25  # Venice is ~25x cheaper
                    savings = openai_cost - ai_cost
                    ai_line += f"\n💸 Saved ${savings:.4f} vs OpenAI"
                else:
                    # Show OpenAI premium cost
                    ai_line += f"\n💰 Premium analysis: ${ai_cost:.4f}"
            
            message += ai_line
        
        # Add Betfury betting links if available
        if context.betfury_links:
            message += "\n\n🎰 **BETTING LINKS:**"
            if 'main' in context.betfury_links:
                message += f"\n💰 [**BET NOW ON BETFURY**]({context.betfury_links['main']})"
            
            # Add quick market links
            quick_markets = ['Match Winner', 'Over Under', 'Both Teams Score']
            for market in quick_markets:
                if market in context.betfury_links:
                    emoji = "⚽" if "Score" in market else "📊" if "Over" in market else "🎯"
                    message += f"\n{emoji} [{market}]({context.betfury_links[market]})"
        
        # Add urgency factors if available
        if context.urgency_factors:
            urgency_list = [factor for factor in context.urgency_factors if factor]
            if urgency_list:
                message += f"\n\n⚡ **URGENCY FACTORS:**"
                for factor in urgency_list[:3]:  # Limit to 3 factors
                    message += f"\n• {factor}"
        
        # Add priority indicator for high-priority alerts
        if context.priority >= 4:
            priority_prefix = "🚨 **PRIORITY ALERT** 🚨"
            if getattr(opp, 'ai_enhanced', False):
                ai_provider = getattr(opp, 'ai_provider', 'venice')
                is_premium = getattr(opp, 'is_premium_analysis', False)
                if is_premium:
                    priority_prefix += f" 🏆 **{ai_provider.upper()} PREMIUM**"
                else:
                    priority_prefix += f" 🤖 **{ai_provider.upper()} OPTIMIZED**"
            message = f"{priority_prefix}\n\n{message}"
        
        return message
    
    def _update_alert_tracking(self, context: AlertContext):
        """Update alert tracking after successful send"""
        
        match_id = context.opportunity.match_id
        current_time = datetime.now()
        
        # Update counters
        self.daily_alert_count += 1
        self.match_alert_counts[match_id] = self.match_alert_counts.get(match_id, 0) + 1
        self.match_last_alerts[match_id] = current_time
        self.sent_alerts[match_id] = current_time
    
    def _reset_daily_counters_if_needed(self):
        """Reset daily counters if it's a new day"""
        
        current_date = datetime.now().date()
        if current_date != self.last_reset_date:
            self.daily_alert_count = 0
            self.last_reset_date = current_date
            
            # Clean up old match tracking
            cutoff_time = datetime.now() - timedelta(days=1)
            
            old_matches = []
            for match_id, alert_time in self.match_last_alerts.items():
                if alert_time < cutoff_time:
                    old_matches.append(match_id)
            
            for match_id in old_matches:
                self.match_alert_counts.pop(match_id, None)
                self.match_last_alerts.pop(match_id, None)
                self.sent_alerts.pop(match_id, None)
            
            logger.info(f"Reset daily counters, cleaned up {len(old_matches)} old matches")
    
    async def send_daily_summary(self, opportunities_count: int, movements_count: int,
                               avg_edge: float, top_leagues: List[str]) -> bool:
        """Send daily summary of live monitoring activity"""
        
        try:
            league_breakdown = "\n".join([f"  • {league}" for league in top_leagues[:5]])
            
            avg_response_time = 15  # Placeholder - would calculate from actual data
            
            message = ALERT_TEMPLATES['DAILY_SUMMARY'].format(
                total_alerts=self.daily_alert_count,
                value_opportunities=opportunities_count,
                avg_edge=avg_edge,
                avg_response_time=avg_response_time,
                league_breakdown=league_breakdown or "  • No activity today"
            )
            
            await self.bot.send_message(
                chat_id=self.config.TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info("Sent daily summary")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send daily summary: {e}")
            return False
    
    async def send_system_status(self, performance_stats: Dict) -> bool:
        """Send system performance status"""
        
        try:
            message = f"""🔧 **Live Monitor Status**

📊 **Performance**:
  • Requests: {performance_stats.get('total_requests', 0)}
  • Error Rate: {performance_stats.get('error_rate', 0):.1%}
  • Tracked Matches: {performance_stats.get('tracked_matches', 0)}

📱 **Alerts**:
  • Sent Today: {self.daily_alert_count}
  • Success Rate: {(1 - self.failed_alerts / max(self.total_alerts_sent, 1)):.1%}
  • Failed: {self.failed_alerts}

⚡ **System**: Operational"""
            
            await self.bot.send_message(
                chat_id=self.config.TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='Markdown'
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send system status: {e}")
            return False
    
    def get_alert_stats(self) -> Dict:
        """Get alert delivery statistics"""
        
        return {
            'total_sent': self.total_alerts_sent,
            'failed_count': self.failed_alerts,
            'success_rate': (self.total_alerts_sent - self.failed_alerts) / max(self.total_alerts_sent, 1),
            'daily_count': self.daily_alert_count,
            'daily_limit': self.config.MAX_DAILY_ALERTS,
            'active_matches': len(self.match_alert_counts),
            'avg_alerts_per_match': sum(self.match_alert_counts.values()) / max(len(self.match_alert_counts), 1)
        }
