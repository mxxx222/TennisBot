#!/usr/bin/env python3
"""
📢 TELEGRAM ANNOUNCER
====================
Advanced Telegram announcement system for secure betting opportunities
with real-time notifications and comprehensive match analysis.

Features:
- 📢 Automated announcements for secure bets
- 🛡️ Security-focused notifications
- 🤖 AI-powered match analysis alerts
- 📊 Real-time odds monitoring
- 🎯 Personalized betting recommendations
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json

# Telegram imports
try:
    from telegram import Bot
    from telegram.constants import ParseMode
    TELEGRAM_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: python-telegram-bot not available")
    TELEGRAM_AVAILABLE = False
    Bot = None

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramAnnouncer:
    """Advanced Telegram announcer for betting opportunities"""
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
        """Initialize Telegram announcer"""
        logger.info("📢 Initializing Telegram Announcer...")
        
        # Get credentials
        self.bot_token = bot_token or "8481385860:AAGBRbsDA8--t373COn2mgM4_c1ngc2fGRM"
        self.chat_id = chat_id or "-4956738581"
        
        # Initialize bot
        if TELEGRAM_AVAILABLE and self.bot_token and self.chat_id:
            self.bot = Bot(token=self.bot_token)
            self.demo_mode = False
        else:
            self.bot = None
            self.demo_mode = True
            logger.warning("⚠️ Running in demo mode")
        
        # Announcement settings
        self.settings = {
            'min_security_level': 'secure',
            'min_win_probability': 0.70,
            'max_announcements_per_hour': 5,
            'announcement_cooldown': 300,  # 5 minutes between similar announcements
            'include_analysis': True,
            'include_statistics': True,
            'include_recommendations': True
        }
        
        # Tracking
        self.last_announcements = {}
        self.announcement_count = 0
        self.last_reset_time = datetime.now()
        
        logger.info("✅ Telegram Announcer initialized")
    
    async def announce_secure_opportunity(self, opportunity: Any) -> bool:
        """Announce a secure betting opportunity"""
        
        try:
            # Check if we should announce this opportunity
            if not self._should_announce(opportunity):
                return False
            
            # Create announcement message
            message = self._create_secure_opportunity_message(opportunity)
            
            # Send announcement
            success = await self._send_announcement(message)
            
            if success:
                self._track_announcement(opportunity)
                logger.info(f"✅ Announced opportunity: {opportunity.home_team} vs {opportunity.away_team}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error announcing opportunity: {e}")
            return False
    
    async def announce_daily_summary(self, opportunities: List[Any], analysis_summary: Dict[str, Any]) -> bool:
        """Announce daily summary of opportunities"""
        
        try:
            message = self._create_daily_summary_message(opportunities, analysis_summary)
            success = await self._send_announcement(message)
            
            if success:
                logger.info("✅ Sent daily summary announcement")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error sending daily summary: {e}")
            return False
    
    async def announce_live_alert(self, match_data: Dict[str, Any], alert_type: str) -> bool:
        """Announce live match alerts"""
        
        try:
            message = self._create_live_alert_message(match_data, alert_type)
            success = await self._send_announcement(message)
            
            if success:
                logger.info(f"✅ Sent live alert: {alert_type}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error sending live alert: {e}")
            return False
    
    async def announce_system_status(self, status_data: Dict[str, Any]) -> bool:
        """Announce system status updates"""
        
        try:
            message = self._create_system_status_message(status_data)
            success = await self._send_announcement(message)
            
            if success:
                logger.info("✅ Sent system status announcement")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error sending system status: {e}")
            return False
    
    def _should_announce(self, opportunity: Any) -> bool:
        """Check if opportunity should be announced"""
        
        # Check rate limiting
        if self._is_rate_limited():
            return False
        
        # Check security level
        security_levels = ['ultra_secure', 'very_secure', 'secure', 'moderate']
        min_level_index = security_levels.index(self.settings['min_security_level'])
        opp_level_index = security_levels.index(opportunity.security_level.value)
        
        if opp_level_index > min_level_index:
            return False
        
        # Check win probability
        if opportunity.win_probability < self.settings['min_win_probability']:
            return False
        
        # Check cooldown for similar opportunities
        cooldown_key = f"{opportunity.sport}_{opportunity.market}"
        if cooldown_key in self.last_announcements:
            time_since_last = (datetime.now() - self.last_announcements[cooldown_key]).total_seconds()
            if time_since_last < self.settings['announcement_cooldown']:
                return False
        
        return True
    
    def _is_rate_limited(self) -> bool:
        """Check if rate limited"""
        
        # Reset counter if new hour
        if (datetime.now() - self.last_reset_time).total_seconds() > 3600:
            self.announcement_count = 0
            self.last_reset_time = datetime.now()
        
        return self.announcement_count >= self.settings['max_announcements_per_hour']
    
    def _create_secure_opportunity_message(self, opportunity: Any) -> str:
        """Create secure opportunity announcement message"""
        
        # Security emoji mapping
        security_emojis = {
            'ultra_secure': '🔒',
            'very_secure': '🛡️',
            'secure': '✅',
            'moderate': '⚠️'
        }
        
        security_emoji = security_emojis.get(opportunity.security_level.value, '📊')
        
        # Sport emoji
        sport_emojis = {
            'football': '⚽',
            'tennis': '🎾',
            'basketball': '🏀',
            'ice_hockey': '🏒'
        }
        sport_emoji = sport_emojis.get(opportunity.sport, '🏆')
        
        # Calculate potential profit
        stake_amount = opportunity.recommended_stake * 100  # Assuming $10k bankroll
        potential_profit = stake_amount * (opportunity.odds - 1) * opportunity.win_probability
        
        message = f"""
🚨 **SECURE BETTING ALERT** {security_emoji}

{sport_emoji} **{opportunity.home_team} vs {opportunity.away_team}**
📅 {opportunity.match_time.strftime('%Y-%m-%d %H:%M')}

🛡️ **SECURITY ANALYSIS:**
• Security Level: {security_emoji} {opportunity.security_level.value.upper().replace('_', ' ')}
• Win Probability: {opportunity.win_probability:.1%}
• Risk Score: {opportunity.risk_score:.3f} (Lower is better)
• Confidence: {opportunity.confidence_score:.1%}

🎯 **BETTING OPPORTUNITY:**
• Market: {opportunity.market}
• Selection: {opportunity.selection}
• Bookmaker: {opportunity.bookmaker}
• Odds: {opportunity.odds:.2f}

💰 **FINANCIAL ANALYSIS:**
• Expected ROI: {opportunity.expected_roi:.1f}%
• Recommended Stake: {opportunity.recommended_stake:.1f}% (${stake_amount:.0f})
• Potential Profit: ${potential_profit:.0f}
• Max Loss: ${stake_amount:.0f}

🔑 **KEY SAFETY FACTORS:**
{self._format_safety_factors(opportunity.safety_factors)}

🛡️ **RISK MITIGATION:**
{self._format_risk_mitigation(opportunity.risk_mitigation)}

📊 **KEY STATISTICS:**
{self._format_key_statistics(opportunity.key_statistics)}

⏰ **EXPIRES:** {opportunity.expires_at.strftime('%H:%M')} (Act quickly!)

🎯 **This is a HIGH-SECURITY opportunity with {opportunity.win_probability:.0%} win probability!**
        """
        
        return message.strip()
    
    def _create_daily_summary_message(self, opportunities: List[Any], analysis_summary: Dict[str, Any]) -> str:
        """Create daily summary announcement"""
        
        if not opportunities:
            return """
📊 **DAILY ANALYSIS SUMMARY**
📅 {datetime.now().strftime('%Y-%m-%d')}

❌ **No secure opportunities found today**

The AI system analyzed all available matches but found no opportunities meeting our strict security criteria:
• Minimum 70% win probability
• Maximum 30% risk score
• Strong supporting factors

🔍 **System Status:**
• Matches analyzed: {analysis_summary.get('matches_analyzed', 0)}
• Security checks passed: 0
• Next analysis: In 2 hours

💡 **Tip:** Secure opportunities are rare but highly profitable when found!
            """
        
        # Group by security level
        by_security = {}
        for opp in opportunities:
            level = opp.security_level.value
            if level not in by_security:
                by_security[level] = []
            by_security[level].append(opp)
        
        # Calculate metrics
        total_stake = sum(opp.recommended_stake for opp in opportunities)
        avg_win_prob = sum(opp.win_probability for opp in opportunities) / len(opportunities)
        avg_roi = sum(opp.expected_roi for opp in opportunities) / len(opportunities)
        
        message = f"""
📊 **DAILY SECURE BETTING SUMMARY**
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}

🛡️ **SECURITY OVERVIEW:**
• Total Secure Opportunities: {len(opportunities)}
• Average Win Probability: {avg_win_prob:.1%}
• Average ROI: {avg_roi:.1f}%
• Total Recommended Stake: {total_stake:.1f}%

🔒 **BY SECURITY LEVEL:**
{self._format_security_distribution(by_security)}

🏆 **TOP 3 OPPORTUNITIES:**
{self._format_top_opportunities(opportunities[:3])}

📈 **ANALYSIS SUMMARY:**
• Matches Analyzed: {analysis_summary.get('matches_analyzed', 0)}
• Security Checks: {analysis_summary.get('security_checks', 0)}
• Success Rate: {analysis_summary.get('success_rate', 0):.1f}%

🎯 **RECOMMENDATION:**
Focus on the highest security level opportunities for maximum safety and consistent profits.

⚠️ **Remember:** Even secure bets carry risk. Never bet more than you can afford to lose!
        """
        
        return message.strip()
    
    def _create_live_alert_message(self, match_data: Dict[str, Any], alert_type: str) -> str:
        """Create live match alert message"""
        
        alert_messages = {
            'odds_movement': f"""
🚨 **LIVE ODDS ALERT**

⚽ **{match_data['home_team']} vs {match_data['away_team']}**

📊 **Significant odds movement detected:**
• Market: {match_data.get('market', 'Match Winner')}
• Previous Odds: {match_data.get('previous_odds', 0):.2f}
• Current Odds: {match_data.get('current_odds', 0):.2f}
• Change: {match_data.get('odds_change', 0):+.2f}

🎯 **Potential opportunity if odds continue moving in our favor!**
            """,
            
            'injury_news': f"""
🏥 **INJURY NEWS ALERT**

⚽ **{match_data['home_team']} vs {match_data['away_team']}**

🚨 **Late injury news:**
• Player: {match_data.get('injured_player', 'Key Player')}
• Team: {match_data.get('affected_team', 'Home')}
• Impact: {match_data.get('impact_level', 'High')}

📊 **This may affect our betting analysis. Reviewing opportunities...**
            """,
            
            'weather_change': f"""
🌧️ **WEATHER ALERT**

⚽ **{match_data['home_team']} vs {match_data['away_team']}**

🌤️ **Weather conditions changed:**
• Previous: {match_data.get('previous_weather', 'Clear')}
• Current: {match_data.get('current_weather', 'Rain')}
• Impact on play: {match_data.get('weather_impact', 'Moderate')}

🎯 **Adjusting over/under analysis accordingly...**
            """
        }
        
        return alert_messages.get(alert_type, "🚨 **LIVE ALERT** - Check latest match information").strip()
    
    def _create_system_status_message(self, status_data: Dict[str, Any]) -> str:
        """Create system status message"""
        
        status_emoji = "✅" if status_data.get('status') == 'healthy' else "⚠️"
        
        message = f"""
🤖 **SYSTEM STATUS UPDATE** {status_emoji}

📊 **Current Status:** {status_data.get('status', 'Unknown').upper()}

🔍 **Analysis Engine:**
• Matches Processed: {status_data.get('matches_processed', 0)}
• Opportunities Found: {status_data.get('opportunities_found', 0)}
• Success Rate: {status_data.get('success_rate', 0):.1f}%

🛡️ **Security Analyzer:**
• Security Checks: {status_data.get('security_checks', 0)}
• Ultra Secure Found: {status_data.get('ultra_secure_count', 0)}
• Average Win Probability: {status_data.get('avg_win_prob', 0):.1%}

📱 **Notification System:**
• Announcements Sent: {status_data.get('announcements_sent', 0)}
• Response Rate: {status_data.get('response_rate', 0):.1f}%

🎯 **Performance (Last 24h):**
• Total ROI: {status_data.get('total_roi', 0):.1f}%
• Winning Bets: {status_data.get('winning_bets', 0)}
• Accuracy: {status_data.get('accuracy', 0):.1f}%

💡 **Next scheduled analysis:** {status_data.get('next_analysis', 'In 2 hours')}
        """
        
        return message.strip()
    
    def _format_safety_factors(self, factors: List[str]) -> str:
        """Format safety factors list"""
        if not factors:
            return "• Standard security analysis applied"
        
        return '\n'.join(f"• {factor}" for factor in factors[:5])
    
    def _format_risk_mitigation(self, mitigation: List[str]) -> str:
        """Format risk mitigation strategies"""
        if not mitigation:
            return "• Conservative stake sizing recommended"
        
        return '\n'.join(f"• {strategy}" for strategy in mitigation[:3])
    
    def _format_key_statistics(self, statistics: Dict[str, Any]) -> str:
        """Format key statistics"""
        if not statistics:
            return "• Comprehensive analysis completed"
        
        lines = []
        for key, value in list(statistics.items())[:4]:
            if isinstance(value, float):
                lines.append(f"• {key.replace('_', ' ').title()}: {value:.2f}")
            else:
                lines.append(f"• {key.replace('_', ' ').title()}: {value}")
        
        return '\n'.join(lines)
    
    def _format_security_distribution(self, by_security: Dict[str, List]) -> str:
        """Format security level distribution"""
        lines = []
        
        security_emojis = {
            'ultra_secure': '🔒',
            'very_secure': '🛡️',
            'secure': '✅',
            'moderate': '⚠️'
        }
        
        for level, opportunities in by_security.items():
            emoji = security_emojis.get(level, '📊')
            count = len(opportunities)
            lines.append(f"• {emoji} {level.replace('_', ' ').title()}: {count}")
        
        return '\n'.join(lines) if lines else "• No opportunities by security level"
    
    def _format_top_opportunities(self, opportunities: List[Any]) -> str:
        """Format top opportunities summary"""
        if not opportunities:
            return "• No top opportunities available"
        
        lines = []
        for i, opp in enumerate(opportunities, 1):
            lines.append(
                f"{i}. {opp.home_team} vs {opp.away_team} "
                f"({opp.win_probability:.0%} win, {opp.expected_roi:.1f}% ROI)"
            )
        
        return '\n'.join(lines)
    
    async def _send_announcement(self, message: str) -> bool:
        """Send announcement message"""
        
        if self.demo_mode or not self.bot:
            print("📢 TELEGRAM ANNOUNCEMENT (Demo Mode):")
            print("=" * 60)
            print(message)
            print("=" * 60)
            return True
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            return True
        except Exception as e:
            logger.error(f"❌ Error sending announcement: {e}")
            return False
    
    def _track_announcement(self, opportunity: Any):
        """Track announcement for rate limiting"""
        
        self.announcement_count += 1
        cooldown_key = f"{opportunity.sport}_{opportunity.market}"
        self.last_announcements[cooldown_key] = datetime.now()
    
    async def send_welcome_announcement(self) -> bool:
        """Send welcome announcement when system starts"""
        
        welcome_message = """
🤖 **SECURE BETTING SYSTEM ACTIVATED**

🛡️ **Welcome to the Advanced Betting Intelligence System!**

**🎯 What I Do:**
• 🔍 Continuously analyze matches across all major sports
• 🛡️ Identify ultra-secure betting opportunities (70%+ win rate)
• 📊 Provide comprehensive risk analysis and statistics
• 💰 Calculate optimal stake sizes and ROI projections
• 🚨 Send real-time alerts for high-value opportunities

**🔒 Security Levels:**
• 🔒 Ultra Secure: 90%+ win probability
• 🛡️ Very Secure: 80-90% win probability
• ✅ Secure: 70-80% win probability

**📊 Analysis Includes:**
• Team form and statistics
• Head-to-head records
• Injury reports and suspensions
• Weather and venue conditions
• Market inefficiencies and value bets

**⚠️ Important:**
• Only secure opportunities meeting strict criteria are announced
• Conservative stake sizing (max 2-3% per bet)
• Comprehensive risk management included
• Always bet responsibly!

🎯 **System is now monitoring matches and will announce opportunities as they arise!**

📈 **Target: 70%+ win rate with consistent profits**
        """
        
        return await self._send_announcement(welcome_message.strip())
    
    async def send_test_announcement(self) -> bool:
        """Send test announcement"""
        
        test_message = """
🧪 **SYSTEM TEST - SECURE BETTING ANALYZER**

✅ **All systems operational:**
• 🔍 Match analysis engine: Active
• 🛡️ Security analyzer: Active  
• 📊 Risk calculator: Active
• 🤖 AI predictor: Active
• 📱 Telegram announcer: Active

🎯 **Ready to find secure betting opportunities!**

The system will now continuously monitor matches and announce only the most secure opportunities with:
• 70%+ win probability
• Comprehensive safety analysis
• Conservative risk management
• Detailed statistics and reasoning

💡 **Next analysis cycle starts in 5 minutes...**
        """
        
        return await self._send_announcement(test_message.strip())

async def main():
    """Test the Telegram announcer"""
    print("📢 TELEGRAM ANNOUNCER TEST")
    print("=" * 40)
    
    # Initialize announcer
    announcer = TelegramAnnouncer()
    
    # Send welcome announcement
    print("\n📱 Sending welcome announcement...")
    await announcer.send_welcome_announcement()
    
    # Wait a bit
    await asyncio.sleep(2)
    
    # Send test announcement
    print("\n🧪 Sending test announcement...")
    await announcer.send_test_announcement()
    
    print("\n✅ Announcer test completed!")

if __name__ == "__main__":
    asyncio.run(main())
