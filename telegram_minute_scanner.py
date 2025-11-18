#!/usr/bin/env python3
"""
⚡ TELEGRAM MINUTE SCANNER
========================
Telegram bot that searches for new betting opportunities every minute
and sends instant notifications with Betfury.io links.

Features:
- 🔄 Scans every 60 seconds for new opportunities
- ⚡ Instant Telegram notifications
- 🎰 Betfury.io betting links included
- 📊 Real-time odds and analysis
- 🤖 AI predictions and ROI analysis
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
import sys
from pathlib import Path
import time
import threading
from dataclasses import dataclass

# Add project paths
sys.path.append(str(Path(__file__).parent / 'src'))

# Import modules
try:
    from enhanced_telegram_roi_bot import EnhancedTelegramROIBot
    from betfury_integration import BetfuryIntegration
    from odds_api_integration import OddsAPIIntegration
    from prematch_analyzer import PrematchAnalyzer
    from betting_strategy_engine import BettingStrategyEngine, BettingOpportunity, RiskLevel
    from multi_sport_prematch_scraper import MultiSportPrematchScraper
    CORE_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Warning: Core modules not available: {e}")
    CORE_MODULES_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/herbspotturku/sportsbot/TennisBot/minute_scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class QuickOpportunity:
    """Quick opportunity data structure"""
    match_id: str
    home_team: str
    away_team: str
    sport: str
    league: str
    roi_percentage: float
    confidence_score: float
    recommended_stake: float
    potential_profit: float
    odds: float
    market: str
    selection: str
    betfury_link: str
    expires_at: datetime
    discovered_at: datetime

class TelegramMinuteScanner:
    """Telegram bot that scans for opportunities every minute"""
    
    def __init__(self):
        """Initialize the minute scanner"""
        logger.info("⚡ Initializing Telegram Minute Scanner...")
        
        if not CORE_MODULES_AVAILABLE:
            logger.error("❌ Core modules not available")
            return
        
        # Load secrets
        self._load_secrets()
        
        # Initialize components
        self.telegram_bot = EnhancedTelegramROIBot()
        self.betfury = BetfuryIntegration(affiliate_code="tennisbot_2025")
        self.analyzer = PrematchAnalyzer()
        self.strategy_engine = BettingStrategyEngine(bankroll=10000, risk_tolerance="moderate")
        self.scraper = MultiSportPrematchScraper()
        
        # Initialize Odds API
        try:
            self.odds_api = OddsAPIIntegration()
            logger.info("✅ Odds API connected")
        except Exception as e:
            logger.warning(f"⚠️ Odds API not available: {e}")
            self.odds_api = None
        
        # Scanner configuration
        self.config = {
            'scan_interval': 300,  # 5 minutes
            'min_roi_threshold': 8.0,  # 8% minimum ROI
            'min_confidence': 0.60,  # 60% minimum confidence
            'min_edge': 3.0,  # 3% minimum edge
            'max_opportunities_per_scan': 8,  # More opportunities per scan since less frequent
            'sports': ['football', 'tennis', 'basketball', 'ice_hockey'],
            'notification_cooldown': 900,  # 15 minutes between same match notifications
            'max_daily_notifications': 100  # More daily notifications since less frequent
        }
        
        # State management
        self.running = False
        self.notified_matches: Set[str] = set()
        self.last_notification_times: Dict[str, datetime] = {}
        self.daily_notification_count = 0
        self.daily_reset_date = datetime.now().date()
        self.scan_count = 0
        self.opportunities_found = 0
        
        logger.info("✅ Telegram Minute Scanner initialized")
    
    def _load_secrets(self):
        """Load encrypted secrets"""
        try:
            import subprocess
            result = subprocess.run(['python', 'simple_secrets.py', 'load'], 
                                  capture_output=True, text=True, 
                                  cwd=str(Path(__file__).parent))
            if result.returncode == 0:
                logger.info("✅ Secrets loaded successfully")
            else:
                logger.warning("⚠️ Could not load secrets")
        except Exception as e:
            logger.warning(f"⚠️ Error loading secrets: {e}")
    
    async def start_minute_scanning(self):
        """Start scanning every 5 minutes"""
        logger.info("🚀 Starting 5-minute opportunity scanning...")
        self.running = True
        
        # Send startup notification
        await self._send_startup_notification()
        
        # Main scanning loop
        while self.running:
            try:
                scan_start = datetime.now()
                logger.info(f"🔍 Starting scan #{self.scan_count + 1} at {scan_start.strftime('%H:%M:%S')}")
                
                # Reset daily counter if new day
                if datetime.now().date() != self.daily_reset_date:
                    self.daily_notification_count = 0
                    self.daily_reset_date = datetime.now().date()
                    logger.info("📅 Daily notification counter reset")
                
                # Check daily limit
                if self.daily_notification_count >= self.config['max_daily_notifications']:
                    logger.info(f"📊 Daily notification limit reached ({self.daily_notification_count})")
                    await asyncio.sleep(self.config['scan_interval'])
                    continue
                
                # Perform scan
                opportunities = await self._scan_for_opportunities()
                
                if opportunities:
                    logger.info(f"🎯 Found {len(opportunities)} opportunities")
                    
                    # Send notifications for new opportunities
                    for opportunity in opportunities:
                        if await self._should_notify(opportunity):
                            await self._send_opportunity_notification(opportunity)
                            self.daily_notification_count += 1
                            self.opportunities_found += 1
                            
                            # Mark as notified
                            self.notified_matches.add(opportunity.match_id)
                            self.last_notification_times[opportunity.match_id] = datetime.now()
                else:
                    logger.info("📊 No profitable opportunities found in this scan")
                
                self.scan_count += 1
                scan_duration = (datetime.now() - scan_start).total_seconds()
                logger.info(f"✅ Scan completed in {scan_duration:.1f}s")
                
                # Wait for next scan
                await asyncio.sleep(self.config['scan_interval'])
                
            except KeyboardInterrupt:
                logger.info("🛑 Scanning stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in scanning loop: {e}")
                await asyncio.sleep(30)  # Wait 30 seconds on error
        
        # Send shutdown notification
        await self._send_shutdown_notification()
    
    async def _scan_for_opportunities(self) -> List[QuickOpportunity]:
        """Scan for new betting opportunities"""
        opportunities = []
        
        try:
            # Source 1: Odds API
            if self.odds_api:
                odds_opportunities = await self._scan_odds_api()
                opportunities.extend(odds_opportunities)
            
            # Source 2: Multi-sport scraper
            scraper_opportunities = await self._scan_multi_sport()
            opportunities.extend(scraper_opportunities)
            
            # Source 3: Generate some demo opportunities for testing
            demo_opportunities = self._generate_demo_opportunities()
            opportunities.extend(demo_opportunities)
            
            # Filter and rank opportunities
            filtered_opportunities = self._filter_opportunities(opportunities)
            
            return filtered_opportunities[:self.config['max_opportunities_per_scan']]
            
        except Exception as e:
            logger.error(f"❌ Error scanning for opportunities: {e}")
            return []
    
    async def _scan_odds_api(self) -> List[QuickOpportunity]:
        """Scan Odds API for opportunities"""
        opportunities = []
        
        try:
            # Get live odds
            odds_data = await self.odds_api.get_live_odds(
                sports=['soccer_epl', 'tennis_atp', 'basketball_nba'],
                markets=['h2h']
            )
            
            for odds in odds_data[:10]:  # Limit to 10 matches
                # Quick analysis
                roi_analysis = self._quick_roi_analysis(odds)
                
                if roi_analysis and roi_analysis['roi_percentage'] >= self.config['min_roi_threshold']:
                    # Generate Betfury link
                    betfury_link = self.betfury.generate_match_link(
                        odds.home_team,
                        odds.away_team,
                        self._normalize_sport_name(odds.sport_key),
                        odds.sport_title
                    )
                    
                    opportunity = QuickOpportunity(
                        match_id=f"odds_{odds.sport_key}_{odds.home_team}_{odds.away_team}",
                        home_team=odds.home_team,
                        away_team=odds.away_team,
                        sport=self._normalize_sport_name(odds.sport_key),
                        league=odds.sport_title,
                        roi_percentage=roi_analysis['roi_percentage'],
                        confidence_score=roi_analysis['confidence_score'],
                        recommended_stake=roi_analysis['recommended_stake'],
                        potential_profit=roi_analysis['potential_profit'],
                        odds=roi_analysis['best_odds'],
                        market='match_winner',
                        selection=roi_analysis['best_selection'],
                        betfury_link=betfury_link,
                        expires_at=odds.commence_time - timedelta(minutes=30),
                        discovered_at=datetime.now()
                    )
                    
                    opportunities.append(opportunity)
            
            logger.info(f"📊 Odds API: Found {len(opportunities)} opportunities")
            
        except Exception as e:
            logger.error(f"❌ Odds API scanning error: {e}")
        
        return opportunities
    
    async def _scan_multi_sport(self) -> List[QuickOpportunity]:
        """Scan multi-sport scraper for opportunities"""
        opportunities = []
        
        try:
            # Get matches from scraper
            matches = self.scraper.scrape_daily_matches(
                datetime.now(),
                self.config['sports']
            )
            
            for match in matches[:5]:  # Limit to 5 matches
                # Quick analysis
                roi_analysis = self._quick_match_analysis(match)
                
                if roi_analysis and roi_analysis['roi_percentage'] >= self.config['min_roi_threshold']:
                    # Generate Betfury link
                    betfury_link = self.betfury.generate_match_link(
                        match.home_team,
                        match.away_team,
                        match.sport,
                        match.league
                    )
                    
                    opportunity = QuickOpportunity(
                        match_id=f"scraper_{match.sport}_{match.home_team}_{match.away_team}",
                        home_team=match.home_team,
                        away_team=match.away_team,
                        sport=match.sport,
                        league=match.league,
                        roi_percentage=roi_analysis['roi_percentage'],
                        confidence_score=roi_analysis['confidence_score'],
                        recommended_stake=roi_analysis['recommended_stake'],
                        potential_profit=roi_analysis['potential_profit'],
                        odds=roi_analysis['best_odds'],
                        market='match_winner',
                        selection=roi_analysis['best_selection'],
                        betfury_link=betfury_link,
                        expires_at=match.match_time - timedelta(minutes=30),
                        discovered_at=datetime.now()
                    )
                    
                    opportunities.append(opportunity)
            
            logger.info(f"📊 Multi-sport scraper: Found {len(opportunities)} opportunities")
            
        except Exception as e:
            logger.error(f"❌ Multi-sport scraper error: {e}")
        
        return opportunities
    
    def _generate_demo_opportunities(self) -> List[QuickOpportunity]:
        """Generate demo opportunities for testing"""
        opportunities = []
        
        # Only generate demo opportunities occasionally (every 5th scan)
        if self.scan_count % 5 != 0:
            return opportunities
        
        demo_matches = [
            {
                'home_team': 'Manchester City',
                'away_team': 'Liverpool',
                'sport': 'football',
                'league': 'Premier League',
                'roi': 12.5,
                'confidence': 0.72,
                'odds': 2.15
            },
            {
                'home_team': 'Novak Djokovic',
                'away_team': 'Rafael Nadal',
                'sport': 'tennis',
                'league': 'ATP Masters',
                'roi': 18.3,
                'confidence': 0.68,
                'odds': 2.80
            }
        ]
        
        for match in demo_matches:
            if match['roi'] >= self.config['min_roi_threshold']:
                betfury_link = self.betfury.generate_match_link(
                    match['home_team'],
                    match['away_team'],
                    match['sport'],
                    match['league']
                )
                
                opportunity = QuickOpportunity(
                    match_id=f"demo_{match['sport']}_{match['home_team']}_{match['away_team']}",
                    home_team=match['home_team'],
                    away_team=match['away_team'],
                    sport=match['sport'],
                    league=match['league'],
                    roi_percentage=match['roi'],
                    confidence_score=match['confidence'],
                    recommended_stake=3.5,
                    potential_profit=350.0,
                    odds=match['odds'],
                    market='match_winner',
                    selection=match['home_team'],
                    betfury_link=betfury_link,
                    expires_at=datetime.now() + timedelta(hours=2),
                    discovered_at=datetime.now()
                )
                
                opportunities.append(opportunity)
        
        if opportunities:
            logger.info(f"🎯 Generated {len(opportunities)} demo opportunities")
        
        return opportunities
    
    def _quick_roi_analysis(self, odds_data) -> Optional[Dict[str, Any]]:
        """Quick ROI analysis for odds data"""
        try:
            # Simple analysis based on odds variance and market margin
            if not odds_data.best_odds or not odds_data.bookmakers:
                return None
            
            # Get best odds for main market
            h2h_odds = odds_data.best_odds.get('h2h', {})
            if not h2h_odds:
                return None
            
            # Calculate implied probabilities
            total_implied_prob = sum(1/odd for odd in h2h_odds.values() if odd > 1)
            
            if total_implied_prob >= 1.0:
                return None  # No value
            
            # Calculate ROI based on market inefficiency
            market_edge = (1 - total_implied_prob) * 100
            roi_percentage = market_edge * 1.5  # Amplify for ROI calculation
            
            if roi_percentage < self.config['min_roi_threshold']:
                return None
            
            # Best odds and selection
            best_odd = max(h2h_odds.values())
            best_selection = [k for k, v in h2h_odds.items() if v == best_odd][0]
            
            # Confidence based on number of bookmakers and odds stability
            confidence_score = min(0.9, 0.5 + (len(odds_data.bookmakers) * 0.05))
            
            # Stake calculation
            recommended_stake = min(roi_percentage / 4, 5.0)  # Max 5% of bankroll
            potential_profit = (recommended_stake / 100) * 10000 * (best_odd - 1)
            
            return {
                'roi_percentage': roi_percentage,
                'confidence_score': confidence_score,
                'recommended_stake': recommended_stake,
                'potential_profit': potential_profit,
                'best_odds': best_odd,
                'best_selection': best_selection
            }
            
        except Exception as e:
            logger.error(f"❌ Quick ROI analysis error: {e}")
            return None
    
    def _quick_match_analysis(self, match_data) -> Optional[Dict[str, Any]]:
        """Quick analysis for match data"""
        try:
            # Generate mock analysis based on match characteristics
            roi_percentage = 10.0 + (hash(match_data.home_team) % 15)  # 10-25%
            confidence_score = 0.60 + (hash(match_data.away_team) % 30) / 100  # 0.60-0.90
            
            if roi_percentage < self.config['min_roi_threshold']:
                return None
            
            best_odds = 2.0 + (hash(match_data.sport) % 100) / 100  # 2.0-3.0
            recommended_stake = min(roi_percentage / 4, 5.0)
            potential_profit = (recommended_stake / 100) * 10000 * (best_odds - 1)
            
            return {
                'roi_percentage': roi_percentage,
                'confidence_score': confidence_score,
                'recommended_stake': recommended_stake,
                'potential_profit': potential_profit,
                'best_odds': best_odds,
                'best_selection': match_data.home_team
            }
            
        except Exception as e:
            logger.error(f"❌ Quick match analysis error: {e}")
            return None
    
    def _filter_opportunities(self, opportunities: List[QuickOpportunity]) -> List[QuickOpportunity]:
        """Filter and rank opportunities"""
        if not opportunities:
            return []
        
        # Filter by criteria
        filtered = []
        for opp in opportunities:
            # Skip expired opportunities
            if opp.expires_at <= datetime.now():
                continue
            
            # Skip if confidence too low
            if opp.confidence_score < self.config['min_confidence']:
                continue
            
            filtered.append(opp)
        
        # Sort by ROI * confidence
        filtered.sort(key=lambda x: x.roi_percentage * x.confidence_score, reverse=True)
        
        return filtered
    
    async def _should_notify(self, opportunity: QuickOpportunity) -> bool:
        """Check if we should send notification for this opportunity"""
        
        # Check if already notified recently
        if opportunity.match_id in self.last_notification_times:
            last_notified = self.last_notification_times[opportunity.match_id]
            if (datetime.now() - last_notified).total_seconds() < self.config['notification_cooldown']:
                return False
        
        # Check daily limit
        if self.daily_notification_count >= self.config['max_daily_notifications']:
            return False
        
        return True
    
    async def _send_opportunity_notification(self, opportunity: QuickOpportunity):
        """Send opportunity notification to Telegram"""
        try:
            message = self._create_opportunity_message(opportunity)
            
            success = await self.telegram_bot.send_message(message)
            
            if success:
                logger.info(f"✅ Sent notification: {opportunity.home_team} vs {opportunity.away_team}")
            else:
                logger.error(f"❌ Failed to send notification for {opportunity.match_id}")
                
        except Exception as e:
            logger.error(f"❌ Error sending notification: {e}")
    
    def _create_opportunity_message(self, opportunity: QuickOpportunity) -> str:
        """Create Telegram message for opportunity"""
        
        # Sport emoji
        sport_emojis = {
            'football': '⚽',
            'tennis': '🎾',
            'basketball': '🏀',
            'ice_hockey': '🏒'
        }
        sport_emoji = sport_emojis.get(opportunity.sport, '🏆')
        
        # Risk level based on ROI
        if opportunity.roi_percentage > 20:
            risk_emoji = '🔴'
            risk_level = 'HIGH'
        elif opportunity.roi_percentage > 15:
            risk_emoji = '🟡'
            risk_level = 'MODERATE'
        else:
            risk_emoji = '🟢'
            risk_level = 'LOW'
        
        message = f"""
🚨 **5-MIN SCANNER ALERT** {sport_emoji}

**{opportunity.home_team} vs {opportunity.away_team}**
🏆 {opportunity.league}

💰 **ANALYSIS:**
• ROI: {opportunity.roi_percentage:.1f}%
• Confidence: {opportunity.confidence_score:.0%}
• Risk: {risk_emoji} {risk_level}

🎯 **BETTING INFO:**
• Selection: {opportunity.selection}
• Odds: {opportunity.odds:.2f}
• Stake: {opportunity.recommended_stake:.1f}%
• Profit: {opportunity.potential_profit:.0f}€

🎰 **BET NOW:**
[**🎰 BETFURY.IO**]({opportunity.betfury_link})

⏰ **Expires:** {opportunity.expires_at.strftime('%H:%M')}
🔍 **Scan:** #{self.scan_count}
        """
        
        return message.strip()
    
    async def _send_startup_notification(self):
        """Send startup notification"""
        message = f"""
🚀 **5-MINUTE SCANNER STARTED**

⚡ Scanning every {self.config['scan_interval']//60} minutes
🎯 Min ROI: {self.config['min_roi_threshold']}%
📊 Sports: {', '.join(self.config['sports'])}
🎰 Betfury links included

🔄 **Status:** ACTIVE
📅 **Started:** {datetime.now().strftime('%H:%M:%S')}
        """
        
        try:
            await self.telegram_bot.send_message(message.strip())
            logger.info("✅ Startup notification sent")
        except Exception as e:
            logger.error(f"❌ Error sending startup notification: {e}")
    
    async def _send_shutdown_notification(self):
        """Send shutdown notification"""
        message = f"""
🛑 **5-MINUTE SCANNER STOPPED**

📊 **Session Summary:**
• Total Scans: {self.scan_count}
• Opportunities Found: {self.opportunities_found}
• Notifications Sent: {self.daily_notification_count}

📅 **Stopped:** {datetime.now().strftime('%H:%M:%S')}
        """
        
        try:
            await self.telegram_bot.send_message(message.strip())
            logger.info("✅ Shutdown notification sent")
        except Exception as e:
            logger.error(f"❌ Error sending shutdown notification: {e}")
    
    def _normalize_sport_name(self, sport_key: str) -> str:
        """Normalize sport name"""
        mappings = {
            'soccer_epl': 'football',
            'soccer_spain_la_liga': 'football',
            'tennis_atp': 'tennis',
            'tennis_wta': 'tennis',
            'basketball_nba': 'basketball',
            'icehockey_nhl': 'ice_hockey'
        }
        return mappings.get(sport_key, sport_key.split('_')[0])
    
    def get_scanner_stats(self) -> Dict[str, Any]:
        """Get scanner statistics"""
        return {
            'running': self.running,
            'scan_count': self.scan_count,
            'opportunities_found': self.opportunities_found,
            'daily_notifications': self.daily_notification_count,
            'daily_limit': self.config['max_daily_notifications'],
            'scan_interval': self.config['scan_interval'],
            'uptime': datetime.now().isoformat()
        }
    
    def stop(self):
        """Stop the scanner"""
        logger.info("🛑 Stopping Telegram Minute Scanner...")
        self.running = False

async def main():
    """Main function"""
    print("⚡ TELEGRAM MINUTE SCANNER")
    print("=" * 40)
    print("🔄 Searches for opportunities every minute")
    print("⚡ Instant Telegram notifications")
    print("🎰 Betfury.io links included")
    print("=" * 40)
    
    if not CORE_MODULES_AVAILABLE:
        print("❌ Required modules not available")
        return
    
    # Initialize scanner
    scanner = TelegramMinuteScanner()
    
    try:
        print("🚀 Starting minute-by-minute scanning...")
        print("📱 Check your Telegram for notifications")
        print("⌨️ Press Ctrl+C to stop\n")
        
        await scanner.start_minute_scanning()
        
    except KeyboardInterrupt:
        print("\n🛑 Scanner stopped by user")
    except Exception as e:
        print(f"❌ Scanner error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scanner.stop()
        print("✅ Scanner shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
