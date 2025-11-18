#!/usr/bin/env python3
"""
🚀 UNIFIED LIVE MONITOR - SOCCER + TENNIS HYBRID SYSTEM
======================================================

Phase 4C: Ultimate hybrid monitoring system combining:
- Enhanced soccer system (+$33,000/year potential)
- ITF tennis integration (+$4,000/year potential)
- Multi-source data enhancements (+$9,000/year boost)

Total Target: $46,000/year through unified monitoring
Sports: Soccer (7 leagues) + Tennis (ITF Women focus)

Features:
- Unified monitoring cycles for both sports
- Sport-specific AI analysis and alerts
- Combined performance tracking
- Shared infrastructure for maximum efficiency
"""

import asyncio
import aiohttp
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
import json

# Core monitoring components
from monitors.odds_tracker import OddsTracker, OddsSnapshot, OddsMovement
from monitors.value_detector import ValueDetector, ValueOpportunity
from monitors.alert_manager import AlertManager, AlertContext
from storage.odds_database import OddsDatabase

# Enhanced multi-source scrapers
from src.scrapers.betfury_scraper import BetfuryScraper
from src.scrapers.flashscore_scraper import FlashScoreScraper, FlashScoreEvent
from src.scrapers.sofascore_scraper import SofaScoreScraper, SofaScoreXG
from src.scrapers.tennis_odds_scraper import TennisOddsScraper, TennisMatch, TENNIS_SCRAPER_CONFIG
from src.betfury_integration import BetfuryIntegration

# Tennis integration
from tennis_itf_screener_enhanced import EnhancedITFScreener, ITFOpportunity

# AI Analysis
from ai_analysis.match_analyzer import AIMatchAnalyzer
from ai_analysis.hybrid_router import HybridAIRouter

# Configuration
from config.live_config import LiveMonitoringConfig

logger = logging.getLogger(__name__)

@dataclass
class SharpMoneyAlert:
    """Sharp money movement detection"""
    match_id: str
    team: str
    old_odds: float
    new_odds: float
    volume_indicator: float
    confidence: str  # LOW, MEDIUM, HIGH, CRITICAL
    timestamp: datetime
    source: str = "betfury"

@dataclass
class LiveEvent:
    """Real-time match events"""
    match_id: str
    event_type: str  # goal, card, substitution, etc.
    team: str
    player: Optional[str]
    minute: int
    timestamp: datetime
    source: str = "flashscore"

@dataclass
class xGData:
    """Expected Goals data"""
    match_id: str
    home_xg: float
    away_xg: float
    home_shots: int
    away_shots: int
    timestamp: datetime
    source: str = "sofascore"

class UnifiedLiveMonitor:
    """Unified live monitoring for soccer and tennis with multi-source data integration"""
    
    def __init__(self):
        self.config = LiveMonitoringConfig()
        
        # Core components
        self.odds_tracker = OddsTracker()
        self.value_detector = ValueDetector()
        self.alert_manager = AlertManager()
        self.database = OddsDatabase()
        
        # AI Enhancement
        self.ai_analyzer = AIMatchAnalyzer(self.database)
        self.hybrid_router = HybridAIRouter()
        
        # Enhanced scrapers (soccer)
        self.betfury_scraper = None
        self.flashscore_scraper = None
        self.sofascore_scraper = None
        self.betfury_integration = BetfuryIntegration(affiliate_code="tennisbot_2025")
        
        # Tennis components
        self.tennis_scraper = None
        self.itf_screener = None
        
        # Data storage
        self.sharp_money_alerts: List[SharpMoneyAlert] = []
        self.live_events: List[LiveEvent] = []
        self.xg_data: Dict[str, xGData] = {}
        self.tennis_opportunities: List[ITFOpportunity] = []
        
        # Performance tracking
        self.cycle_count = 0
        self.enhancement_stats = {
            'sharp_money_detected': 0,
            'live_events_captured': 0,
            'xg_analyses': 0,
            'enhanced_opportunities': 0,
            'soccer_opportunities': 0,
            'tennis_opportunities': 0,
            'unified_alerts': 0
        }
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.odds_tracker.__aenter__()
        
        # Initialize enhanced scrapers (soccer)
        scraper_config = {
            'rate_limit': 5.0,
            'timeout': 20,
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        }
        self.betfury_scraper = BetfuryScraper(scraper_config)
        
        # Initialize FlashScore scraper
        flashscore_config = {
            'rate_limit': 2.5,
            'timeout': 10,
            'max_matches': 5
        }
        self.flashscore_scraper = FlashScoreScraper(flashscore_config)
        
        # Initialize SofaScore scraper
        sofascore_config = {
            'rate_limit': 4.0,
            'timeout': 15,
            'max_matches': 3
        }
        self.sofascore_scraper = SofaScoreScraper(sofascore_config)
        
        # Initialize tennis components
        self.tennis_scraper = TennisOddsScraper(TENNIS_SCRAPER_CONFIG)
        await self.tennis_scraper.__aenter__()
        
        self.itf_screener = EnhancedITFScreener()
        await self.itf_screener.__aenter__()
        
        logger.info("🚀 Unified Live Monitor initialized - Soccer + Tennis with multi-source capabilities")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.odds_tracker.__aexit__(exc_type, exc_val, exc_tb)
        if self.betfury_scraper and hasattr(self.betfury_scraper, 'session'):
            if self.betfury_scraper.session:
                await self.betfury_scraper.session.close()
        if self.flashscore_scraper:
            await self.flashscore_scraper.__aexit__(exc_type, exc_val, exc_tb)
        if self.sofascore_scraper:
            await self.sofascore_scraper.__aexit__(exc_type, exc_val, exc_tb)
        
        # Close tennis components
        if self.tennis_scraper:
            await self.tennis_scraper.__aexit__(exc_type, exc_val, exc_tb)
        if self.itf_screener:
            await self.itf_screener.__aexit__(exc_type, exc_val, exc_tb)
    
    async def start_unified_monitoring(self):
        """Start unified live monitoring for soccer and tennis with all data sources"""
        logger.info("🚀 Starting Unified Live Monitoring System")
        logger.info("⚽ Soccer: 7 leagues with Betfury + FlashScore + SofaScore")
        logger.info("🎾 Tennis: ITF Women with scraping-powered data")
        logger.info("🎯 Target ROI: $46,000/year combined")
        
        try:
            while True:
                start_time = time.time()
                
                # Enhanced monitoring cycle
                await self._unified_monitoring_cycle()
                
                # Performance logging
                cycle_time = time.time() - start_time
                self.cycle_count += 1
                
                if self.cycle_count % 10 == 0:  # Every 10 cycles (5 minutes)
                    await self._log_enhancement_performance(cycle_time)
                
                # Wait for next cycle
                await asyncio.sleep(self.config.MONITORING_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("🛑 Enhanced monitoring stopped by user")
        except Exception as e:
            logger.error(f"💥 Enhanced monitoring error: {e}")
            raise
    
    async def _unified_monitoring_cycle(self):
        """Unified monitoring cycle for soccer and tennis with multi-source data"""
        try:
            # SOCCER MONITORING PHASE
            logger.info("⚽ Processing soccer opportunities...")
            
            # Phase 1: Standard soccer odds tracking
            soccer_snapshots = []
            for league in self.config.TARGET_LEAGUES:
                snapshots = await self.odds_tracker.fetch_league_odds(league)
                soccer_snapshots.extend(snapshots)
            
            soccer_opportunities = []
            if soccer_snapshots:
                # Detect standard movements
                movements = self.odds_tracker.detect_movements(soccer_snapshots)
                
                # ENHANCEMENT PHASE 1: Betfury Sharp Money Detection
                sharp_money_alerts = await self._detect_sharp_money(soccer_snapshots)
                
                # ENHANCEMENT PHASE 2: FlashScore Live Events
                live_events = await self._capture_live_events(soccer_snapshots)
                
                # ENHANCEMENT PHASE 3: SofaScore xG Data
                xg_enhancements = await self._gather_xg_data(soccer_snapshots)
                
                # Enhanced soccer value detection
                soccer_opportunities = await self._enhanced_value_detection(
                    soccer_snapshots, movements, sharp_money_alerts, live_events, xg_enhancements
                )
                
                # Enhanced soccer alerting
                if soccer_opportunities:
                    await self._send_enhanced_alerts(soccer_opportunities)
                
                # Send priority event alerts for significant soccer events
                await self._send_priority_event_alerts(live_events, soccer_snapshots)
                
                # Store enhanced soccer data
                await self._store_enhanced_data(soccer_snapshots, sharp_money_alerts, live_events)
                
                self.enhancement_stats['soccer_opportunities'] += len(soccer_opportunities)
                logger.info(f"⚽ Soccer: {len(soccer_opportunities)} opportunities detected")
            else:
                logger.info("ℹ️ No active soccer matches - normal during off-peak hours")
            
            # TENNIS MONITORING PHASE
            logger.info("🎾 Processing tennis opportunities...")
            
            # Run ITF tennis screening cycle
            tennis_opportunities = await self.itf_screener.run_screening_cycle()
            
            if tennis_opportunities:
                # Store tennis opportunities for unified tracking
                self.tennis_opportunities.extend(tennis_opportunities)
                self.enhancement_stats['tennis_opportunities'] += len(tennis_opportunities)
                logger.info(f"🎾 Tennis: {len(tennis_opportunities)} ITF opportunities detected")
            else:
                logger.info("ℹ️ No ITF tennis opportunities - normal during off-peak hours")
            
            # UNIFIED PERFORMANCE TRACKING
            total_opportunities = len(soccer_opportunities) + len(tennis_opportunities)
            self.enhancement_stats['enhanced_opportunities'] += total_opportunities
            self.enhancement_stats['unified_alerts'] += total_opportunities
            
            # Update unified stats
            self._update_enhancement_stats(
                sharp_money_alerts if soccer_snapshots else [],
                live_events if soccer_snapshots else [],
                xg_enhancements if soccer_snapshots else {},
                soccer_opportunities + tennis_opportunities
            )
            
            logger.info(f"✅ Unified cycle complete: {total_opportunities} total opportunities")
            logger.info(f"   ⚽ Soccer: {len(soccer_opportunities)} | 🎾 Tennis: {len(tennis_opportunities)}")
            
        except Exception as e:
            logger.error(f"💥 Unified monitoring cycle error: {e}")
    
    async def _detect_sharp_money(self, snapshots: List[OddsSnapshot]) -> List[SharpMoneyAlert]:
        """Phase 1: Detect sharp money movements via Betfury"""
        sharp_alerts = []
        
        if not self.betfury_scraper:
            return sharp_alerts
        
        try:
            # Sample a few matches for sharp money analysis (rate limiting)
            sample_matches = snapshots[:5] if len(snapshots) > 5 else snapshots
            
            for snapshot in sample_matches:
                try:
                    # Get Betfury odds data with movement tracking
                    betfury_data = await self._fetch_betfury_odds(snapshot)
                    
                    if betfury_data and 'sharp_money_indicator' in betfury_data:
                        indicator = betfury_data['sharp_money_indicator']
                        
                        if indicator and indicator > 0.6:  # Significant sharp money
                            alert = SharpMoneyAlert(
                                match_id=snapshot.match_id,
                                team=self._determine_sharp_money_team(betfury_data),
                                old_odds=snapshot.home_odds,
                                new_odds=betfury_data.get('current_home_odds', snapshot.home_odds),
                                volume_indicator=indicator,
                                confidence=self._classify_sharp_money_confidence(indicator),
                                timestamp=datetime.now(),
                                source="betfury"
                            )
                            sharp_alerts.append(alert)
                            
                except Exception as e:
                    logger.debug(f"Sharp money detection error for {snapshot.match_id}: {e}")
                    continue
            
            if sharp_alerts:
                logger.info(f"🔥 Detected {len(sharp_alerts)} sharp money movements")
            
        except Exception as e:
            logger.error(f"💥 Sharp money detection error: {e}")
        
        return sharp_alerts
    
    async def _fetch_betfury_odds(self, snapshot: OddsSnapshot) -> Optional[Dict]:
        """Fetch odds data from Betfury with movement tracking"""
        try:
            # Create match identifier for Betfury
            match_data = {
                'home_team': snapshot.home_team,
                'away_team': snapshot.away_team,
                'sport': 'soccer',  # Assuming soccer for now
                'league': snapshot.league
            }
            
            # Get odds with movement tracking
            odds_data = await self.betfury_scraper.get_live_odds(match_data)
            
            if odds_data:
                # Track movement and calculate sharp money indicator
                enhanced_data = self.betfury_scraper.track_odds_movement(odds_data, snapshot.match_id)
                return enhanced_data
            
        except Exception as e:
            logger.debug(f"Betfury odds fetch error: {e}")
        
        return None
    
    async def _capture_live_events(self, snapshots: List[OddsSnapshot]) -> List[LiveEvent]:
        """Phase 2: Capture live events from FlashScore"""
        events = []
        
        try:
            if not self.flashscore_scraper:
                return events
            
            # Get match IDs from snapshots
            match_ids = [snapshot.match_id for snapshot in snapshots]
            
            # Fetch live events from FlashScore
            flashscore_events = await self.flashscore_scraper.get_live_events(match_ids)
            
            # Convert FlashScore events to our LiveEvent format
            for fs_event in flashscore_events:
                event = LiveEvent(
                    match_id=fs_event.match_id,
                    event_type=fs_event.event_type,
                    team=fs_event.team,
                    player=fs_event.player,
                    minute=fs_event.minute,
                    timestamp=fs_event.timestamp,
                    source="flashscore"
                )
                events.append(event)
                
                # Correlate with odds movements for enhanced value detection
                movements = self.odds_tracker.detected_movements
                correlation = self.flashscore_scraper.correlate_with_odds_movement(
                    fs_event, movements
                )
                
                # Log significant correlations
                if correlation['urgency_boost']:
                    logger.info(f"🔥 Event-odds correlation detected: {fs_event.event_type} in {fs_event.match_id}")
            
            if events:
                logger.info(f"⚡ FlashScore: Captured {len(events)} live events")
                
        except Exception as e:
            logger.error(f"💥 FlashScore events capture error: {e}")
        
        return events
    
    async def _gather_xg_data(self, snapshots: List[OddsSnapshot]) -> Dict[str, xGData]:
        """Phase 3: Gather xG data from SofaScore"""
        xg_data = {}
        
        try:
            if not self.sofascore_scraper:
                return xg_data
            
            # Get match IDs from snapshots
            match_ids = [snapshot.match_id for snapshot in snapshots]
            
            # Fetch xG data from SofaScore
            sofascore_xg = await self.sofascore_scraper.get_xg_data(match_ids)
            
            # Convert SofaScore xG to our xGData format
            for match_id, ss_xg in sofascore_xg.items():
                xg = xGData(
                    match_id=match_id,
                    home_xg=ss_xg.home_xg,
                    away_xg=ss_xg.away_xg,
                    home_shots=ss_xg.home_shots,
                    away_shots=ss_xg.away_shots,
                    timestamp=ss_xg.timestamp,
                    source="sofascore"
                )
                xg_data[match_id] = xg
                
                # Get advanced insights for high-value matches
                insights = self.sofascore_scraper.get_xg_insights(match_id)
                if insights and insights['recommendations']:
                    logger.info(f"📊 xG Insight for {match_id}: {insights['recommendations'][0]}")
            
            if xg_data:
                logger.info(f"📊 SofaScore: Gathered xG data for {len(xg_data)} matches")
                
        except Exception as e:
            logger.error(f"💥 SofaScore xG data gathering error: {e}")
        
        return xg_data
    
    async def _enhanced_value_detection(self, snapshots: List[OddsSnapshot], 
                                      movements: List[OddsMovement],
                                      sharp_alerts: List[SharpMoneyAlert],
                                      events: List[LiveEvent],
                                      xg_data: Dict[str, xGData]) -> List[ValueOpportunity]:
        """Enhanced value detection with multi-source context"""
        
        # Standard value detection
        opportunities = await self.value_detector.analyze_snapshots(snapshots, movements)
        
        # Enhance opportunities with AI analysis including xG data
        if opportunities and self.ai_analyzer:
            try:
                logger.info(f"🤖 Enhancing {len(opportunities)} opportunities with AI + xG analysis...")
                enhanced_opportunities = await self.ai_analyzer.analyze_opportunities(opportunities, xg_data)
                
                # Update opportunities with AI enhancements
                for i, enhanced in enumerate(enhanced_opportunities):
                    if i < len(opportunities):
                        # Transfer AI insights to original opportunity
                        opportunities[i].ai_enhanced = True
                        opportunities[i].ai_confidence = enhanced.ai_confidence_score
                        opportunities[i].ai_reasoning = enhanced.ai_reasoning
                        opportunities[i].ai_cost = enhanced.analysis_cost
                        opportunities[i].ai_provider = 'venice'
                        opportunities[i].edge_estimate = enhanced.combined_edge
                        opportunities[i].priority_score = enhanced.priority_score
                        
            except Exception as e:
                logger.error(f"💥 AI enhancement with xG failed: {e}")
        
        
        # Enhance opportunities with multi-source data
        enhanced_opportunities = []
        
        for opp in opportunities:
            enhanced_opp = opp
            
            # Add sharp money context
            sharp_context = self._find_sharp_money_context(opp.match_id, sharp_alerts)
            if sharp_context:
                enhanced_opp.priority_score += 20  # Boost priority
                enhanced_opp.urgency_level = "HIGH"
                enhanced_opp.ai_reasoning = f"[SHARP MONEY] {enhanced_opp.ai_reasoning or ''}"
            
            # Add live event context
            event_context = self._find_event_context(opp.match_id, events)
            if event_context:
                enhanced_opp.priority_score += 15
                enhanced_opp.ai_reasoning = f"[LIVE EVENT] {enhanced_opp.ai_reasoning or ''}"
            
            # Add xG context
            xg_context = xg_data.get(opp.match_id)
            if xg_context:
                xg_edge = self._calculate_xg_edge(opp, xg_context)
                enhanced_opp.edge_percentage += xg_edge
                enhanced_opp.ai_reasoning = f"[xG ENHANCED] {enhanced_opp.ai_reasoning or ''}"
            
            enhanced_opportunities.append(enhanced_opp)
        
        # Sort by enhanced priority
        enhanced_opportunities.sort(key=lambda x: x.priority_score, reverse=True)
        
        return enhanced_opportunities
    
    async def _send_enhanced_alerts(self, opportunities: List[ValueOpportunity]):
        """Send enhanced alerts with multi-source context"""
        for opp in opportunities:
            # Create enhanced alert context
            context = AlertContext(
                opportunity=opp,
                movement_history=[],  # Would include movement data
                urgency_factors=[
                    "Sharp money detected" if "[SHARP MONEY]" in (opp.ai_reasoning or "") else None,
                    "Live event correlation" if "[LIVE EVENT]" in (opp.ai_reasoning or "") else None,
                    "xG value confirmed" if "[xG ENHANCED]" in (opp.ai_reasoning or "") else None
                ],
                betfury_links=self.betfury_integration.generate_multiple_links({
                    'home_team': opp.home_team,
                    'away_team': opp.away_team,
                    'sport': 'soccer',
                    'league': opp.league
                })
            )
            
            # Send enhanced alert
            await self.alert_manager.send_alert(context)
    
    async def _send_priority_event_alerts(self, events: List[LiveEvent], 
                                        snapshots: List[OddsSnapshot]):
        """Send instant priority alerts for significant live events"""
        try:
            for event in events:
                # Only send alerts for high-impact events
                if event.event_type in ['goal', 'red_card', 'penalty']:
                    
                    # Find corresponding odds snapshot
                    snapshot = self._find_snapshot_for_event(event, snapshots)
                    if not snapshot:
                        continue
                    
                    # Create priority event alert
                    await self._send_instant_event_alert(event, snapshot)
                    
        except Exception as e:
            logger.error(f"💥 Priority event alerts error: {e}")
    
    def _find_snapshot_for_event(self, event: LiveEvent, 
                               snapshots: List[OddsSnapshot]) -> Optional[OddsSnapshot]:
        """Find odds snapshot corresponding to an event"""
        for snapshot in snapshots:
            if snapshot.match_id == event.match_id:
                return snapshot
        return None
    
    async def _send_instant_event_alert(self, event: LiveEvent, snapshot: OddsSnapshot):
        """Send instant alert for significant live event"""
        try:
            # Create event-specific alert message
            event_emoji = {
                'goal': '⚽',
                'red_card': '🟥',
                'penalty': '🥅',
                'yellow_card': '🟨'
            }.get(event.event_type, '⚡')
            
            # Format team name
            team_display = event.team.title() if event.team in ['home', 'away'] else event.team
            if event.team == 'home':
                team_display = snapshot.home_team
            elif event.team == 'away':
                team_display = snapshot.away_team
            
            # Create instant alert message
            message = f"""🚨 **LIVE EVENT ALERT** 🚨

{event_emoji} **{event.event_type.upper().replace('_', ' ')}** - Minute {event.minute}

⚽ **{snapshot.home_team}** vs **{snapshot.away_team}**
🎯 Team: **{team_display}**
👤 Player: {event.player or 'Unknown'}

📊 Current Odds: {snapshot.home_odds:.2f} / {snapshot.away_odds:.2f}
⏰ {event.timestamp.strftime('%H:%M:%S')}

💡 *Check for immediate value opportunities!*"""
            
            # Add Betfury quick bet link
            betfury_links = self.betfury_integration.generate_multiple_links({
                'home_team': snapshot.home_team,
                'away_team': snapshot.away_team,
                'sport': 'soccer',
                'league': snapshot.league
            })
            
            if betfury_links.get('main'):
                message += f"\n\n🎰 [**QUICK BET ON BETFURY**]({betfury_links['main']})"
            
            # Send via Telegram
            await self.alert_manager.bot.send_message(
                chat_id=self.alert_manager.config.TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info(f"⚡ Sent instant event alert: {event.event_type} in {snapshot.match_id}")
            
        except Exception as e:
            logger.error(f"💥 Instant event alert error: {e}")
    
    def _find_sharp_money_context(self, match_id: str, sharp_alerts: List[SharpMoneyAlert]) -> Optional[SharpMoneyAlert]:
        """Find sharp money context for a match"""
        for alert in sharp_alerts:
            if alert.match_id == match_id:
                return alert
        return None
    
    def _find_event_context(self, match_id: str, events: List[LiveEvent]) -> Optional[LiveEvent]:
        """Find live event context for a match"""
        for event in events:
            if event.match_id == match_id:
                return event
        return None
    
    def _calculate_xg_edge(self, opp: ValueOpportunity, xg_data: xGData) -> float:
        """Calculate additional edge from xG data"""
        try:
            # Simple xG-based edge calculation
            if opp.recommended_bet == "home":
                xg_ratio = xg_data.home_xg / max(xg_data.away_xg, 0.1)
                if xg_ratio > 1.5:
                    return 0.02  # +2% edge
            elif opp.recommended_bet == "away":
                xg_ratio = xg_data.away_xg / max(xg_data.home_xg, 0.1)
                if xg_ratio > 1.5:
                    return 0.02  # +2% edge
        except:
            pass
        return 0.0
    
    def _determine_sharp_money_team(self, betfury_data: Dict) -> str:
        """Determine which team sharp money is backing"""
        # Simplified logic - would be more sophisticated in production
        home_movement = betfury_data.get('home_odds_movement', 0)
        away_movement = betfury_data.get('away_odds_movement', 0)
        
        if home_movement < away_movement:
            return betfury_data.get('home_team', 'Home')
        else:
            return betfury_data.get('away_team', 'Away')
    
    def _classify_sharp_money_confidence(self, indicator: float) -> str:
        """Classify sharp money confidence level"""
        if indicator > 0.9:
            return "CRITICAL"
        elif indicator > 0.8:
            return "HIGH"
        elif indicator > 0.7:
            return "MEDIUM"
        else:
            return "LOW"
    
    async def _store_enhanced_data(self, snapshots: List[OddsSnapshot], 
                                 sharp_alerts: List[SharpMoneyAlert],
                                 events: List[LiveEvent]):
        """Store enhanced data in database"""
        try:
            # Store standard odds data
            for snapshot in snapshots:
                await self.database.store_odds_snapshot(snapshot)
            
            # Store sharp money alerts
            for alert in sharp_alerts:
                await self.database.store_sharp_money_alert(alert)
            
            # Store live events
            for event in events:
                await self.database.store_live_event(event)
                
        except Exception as e:
            logger.error(f"💥 Enhanced data storage error: {e}")
    
    def _update_enhancement_stats(self, sharp_alerts: List[SharpMoneyAlert],
                                events: List[LiveEvent],
                                xg_data: Dict[str, xGData],
                                opportunities: List[ValueOpportunity]):
        """Update enhancement performance statistics"""
        self.enhancement_stats['sharp_money_detected'] += len(sharp_alerts)
        self.enhancement_stats['live_events_captured'] += len(events)
        self.enhancement_stats['xg_analyses'] += len(xg_data)
        
        # Count enhanced opportunities
        enhanced_count = sum(1 for opp in opportunities 
                           if any(tag in (opp.ai_reasoning or "") 
                                 for tag in ["[SHARP MONEY]", "[LIVE EVENT]", "[xG ENHANCED]"]))
        self.enhancement_stats['enhanced_opportunities'] += enhanced_count
    
    async def _log_enhancement_performance(self, cycle_time: float):
        """Log enhancement performance metrics"""
        stats = self.enhancement_stats
        
        logger.info("📊 ENHANCEMENT PERFORMANCE REPORT")
        logger.info(f"🔥 Sharp Money Alerts: {stats['sharp_money_detected']}")
        logger.info(f"⚡ Live Events Captured: {stats['live_events_captured']}")
        logger.info(f"📈 xG Analyses: {stats['xg_analyses']}")
        logger.info(f"🎯 Enhanced Opportunities: {stats['enhanced_opportunities']}")
        logger.info(f"⏱️ Avg Cycle Time: {cycle_time:.2f}s")
        logger.info(f"💰 Estimated Additional ROI: +${stats['enhanced_opportunities'] * 15:.0f}/month")

async def main():
    """Main execution function"""
    print("🚀 ENHANCED LIVE ODDS MONITOR")
    print("=" * 50)
    print("📊 Multi-Source Integration Active:")
    print("   • Phase 1: Betfury Sharp Money ($4,800/year)")
    print("   • Phase 2: FlashScore Events ($2,400/year)")
    print("   • Phase 3: SofaScore xG Data ($1,800/year)")
    print("   • Total Enhancement: +$9,000/year")
    print("=" * 50)
    
    async with EnhancedLiveMonitor() as monitor:
        await monitor.start_enhanced_monitoring()

if __name__ == "__main__":
    asyncio.run(main())
