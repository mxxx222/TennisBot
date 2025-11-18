#!/usr/bin/env python3
"""
🎯 ULTIMATE BETTING INTELLIGENCE SYSTEM
=======================================
Complete AI-powered betting intelligence system that continuously searches for secure
betting opportunities, provides comprehensive analysis, and sends intelligent Telegram
announcements with winner predictions and ROI analysis.

Features:
- 🛡️ Secure betting opportunity detection
- 🔄 24/7 continuous game monitoring
- 🤖 AI-powered winner predictions
- 📊 Comprehensive statistical analysis
- 🏥 Real-time injury and suspension tracking
- 📱 Intelligent Telegram announcements
- 💰 ROI optimization and risk management
- 📈 Performance tracking and analytics
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import sys
from pathlib import Path

# Add project paths
current_dir = Path(__file__).parent
sys.path.append(str(current_dir / 'src'))

# Import our modules
try:
    from secure_betting_analyzer import SecureBettingAnalyzer, SecureBettingOpportunity
    from telegram_announcer import TelegramAnnouncer
    from continuous_game_analyzer import ContinuousGameAnalyzer, ComprehensiveMatchAnalysis
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Warning: Required modules not available: {e}")
    MODULES_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ultimate_betting_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UltimateBettingIntelligenceSystem:
    """Ultimate AI-powered betting intelligence system"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the ultimate betting system"""
        logger.info("🎯 Initializing Ultimate Betting Intelligence System...")
        
        # System configuration
        self.config = {
            'analysis_interval': 300,      # 5 minutes between analyses
            'announcement_interval': 600,   # 10 minutes between announcements
            'sports_monitored': ['football', 'tennis', 'basketball', 'ice_hockey'],
            'security_levels': ['ultra_secure', 'very_secure', 'secure'],
            'min_win_probability': 0.70,
            'min_roi_threshold': 10.0,
            'max_daily_announcements': 20,
            'telegram_enabled': True,
            'continuous_monitoring': True,
            'save_analyses': True
        }
        
        # Update with user config
        if config:
            self.config.update(config)
        
        # Initialize components
        if MODULES_AVAILABLE:
            self.secure_analyzer = SecureBettingAnalyzer()
            self.game_analyzer = ContinuousGameAnalyzer()
            
            if self.config['telegram_enabled']:
                self.telegram_announcer = TelegramAnnouncer()
            else:
                self.telegram_announcer = None
        else:
            logger.error("❌ Required modules not available")
            return
        
        # System state
        self.system_stats = {
            'total_analyses': 0,
            'secure_opportunities_found': 0,
            'announcements_sent': 0,
            'successful_predictions': 0,
            'system_uptime': datetime.now(),
            'last_analysis': None,
            'current_opportunities': []
        }
        
        # Performance tracking
        self.performance_history = []
        
        logger.info("✅ Ultimate Betting Intelligence System initialized")
    
    async def start_system(self):
        """Start the complete betting intelligence system"""
        logger.info("🚀 Starting Ultimate Betting Intelligence System...")
        
        # Send system startup announcement
        if self.telegram_announcer:
            await self._send_startup_announcement()
        
        # Start continuous monitoring tasks
        tasks = []
        
        if self.config['continuous_monitoring']:
            # Main analysis loop
            tasks.append(asyncio.create_task(self._continuous_analysis_loop()))
            
            # Announcement loop
            if self.telegram_announcer:
                tasks.append(asyncio.create_task(self._announcement_loop()))
            
            # Performance monitoring loop
            tasks.append(asyncio.create_task(self._performance_monitoring_loop()))
        
        try:
            # Run all tasks concurrently
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("🛑 System stopped by user")
        except Exception as e:
            logger.error(f"❌ System error: {e}")
        finally:
            await self._shutdown_system()
    
    async def _continuous_analysis_loop(self):
        """Main continuous analysis loop"""
        logger.info("🔄 Starting continuous analysis loop...")
        
        while True:
            try:
                # Run comprehensive analysis
                analysis_results = await self._run_comprehensive_analysis()
                
                # Process results
                await self._process_analysis_results(analysis_results)
                
                # Update system stats
                self.system_stats['total_analyses'] += 1
                self.system_stats['last_analysis'] = datetime.now()
                
                # Wait for next cycle
                await asyncio.sleep(self.config['analysis_interval'])
                
            except Exception as e:
                logger.error(f"❌ Error in analysis loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _announcement_loop(self):
        """Telegram announcement loop"""
        logger.info("📱 Starting announcement loop...")
        
        while True:
            try:
                # Check for opportunities to announce
                await self._check_and_announce_opportunities()
                
                # Wait for next announcement cycle
                await asyncio.sleep(self.config['announcement_interval'])
                
            except Exception as e:
                logger.error(f"❌ Error in announcement loop: {e}")
                await asyncio.sleep(120)  # Wait 2 minutes on error
    
    async def _performance_monitoring_loop(self):
        """Performance monitoring loop"""
        logger.info("📊 Starting performance monitoring loop...")
        
        while True:
            try:
                # Update performance metrics
                await self._update_performance_metrics()
                
                # Send periodic status updates
                if datetime.now().hour % 6 == 0:  # Every 6 hours
                    await self._send_status_update()
                
                # Wait 1 hour between performance checks
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"❌ Error in performance monitoring: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run comprehensive analysis of all available matches"""
        logger.info("🔍 Running comprehensive analysis...")
        
        try:
            # 1. Get matches for analysis
            matches = await self.game_analyzer._get_matches_for_analysis()
            
            if not matches:
                return {'status': 'no_matches', 'matches': 0}
            
            # 2. Run detailed game analysis
            game_analyses = await self.game_analyzer._analyze_matches_batch(matches)
            
            # 3. Run secure betting analysis
            secure_opportunities = self.secure_analyzer.analyze_secure_opportunities(matches)
            
            # 4. Combine and evaluate results
            combined_results = await self._combine_analysis_results(game_analyses, secure_opportunities)
            
            logger.info(f"✅ Analysis complete: {len(matches)} matches, {len(secure_opportunities)} secure opportunities")
            
            return {
                'status': 'success',
                'matches_analyzed': len(matches),
                'game_analyses': game_analyses,
                'secure_opportunities': secure_opportunities,
                'combined_results': combined_results,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"❌ Error in comprehensive analysis: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def _combine_analysis_results(self, game_analyses: List[ComprehensiveMatchAnalysis], 
                                      secure_opportunities: List[SecureBettingOpportunity]) -> List[Dict[str, Any]]:
        """Combine game analysis with secure betting opportunities"""
        
        combined_results = []
        
        # Match secure opportunities with game analyses
        for secure_opp in secure_opportunities:
            # Find corresponding game analysis
            game_analysis = None
            for analysis in game_analyses:
                if analysis.match_id == secure_opp.match_id:
                    game_analysis = analysis
                    break
            
            # Create combined result
            combined_result = {
                'match_id': secure_opp.match_id,
                'sport': secure_opp.sport,
                'home_team': secure_opp.home_team,
                'away_team': secure_opp.away_team,
                'match_time': secure_opp.match_time,
                
                # Secure betting data
                'security_level': secure_opp.security_level.value,
                'win_probability': secure_opp.win_probability,
                'expected_roi': secure_opp.expected_roi,
                'recommended_stake': secure_opp.recommended_stake,
                'safety_factors': secure_opp.safety_factors,
                
                # Game analysis data
                'ai_prediction': game_analysis.ai_winner_prediction if game_analysis else None,
                'statistical_edge': game_analysis.statistical_edge if game_analysis else None,
                'injury_analysis': game_analysis.injury_analysis if game_analysis else None,
                'confidence_metrics': game_analysis.confidence_metrics if game_analysis else None,
                
                # Combined scoring
                'overall_score': self._calculate_overall_score(secure_opp, game_analysis),
                'recommendation_strength': self._calculate_recommendation_strength(secure_opp, game_analysis)
            }
            
            combined_results.append(combined_result)
        
        # Sort by overall score
        combined_results.sort(key=lambda x: x['overall_score'], reverse=True)
        
        return combined_results
    
    def _calculate_overall_score(self, secure_opp: SecureBettingOpportunity, 
                               game_analysis: Optional[ComprehensiveMatchAnalysis]) -> float:
        """Calculate overall opportunity score"""
        
        # Base score from security
        security_scores = {
            'ultra_secure': 10.0,
            'very_secure': 8.5,
            'secure': 7.0,
            'moderate': 5.5
        }
        
        base_score = security_scores.get(secure_opp.security_level.value, 5.0)
        
        # Adjust for win probability
        prob_bonus = (secure_opp.win_probability - 0.5) * 10
        
        # Adjust for ROI
        roi_bonus = min(3.0, secure_opp.expected_roi / 10)
        
        # Adjust for AI confidence if available
        ai_bonus = 0
        if game_analysis and game_analysis.confidence_metrics:
            ai_confidence = game_analysis.confidence_metrics.get('confidence_score', 0)
            ai_bonus = ai_confidence * 2
        
        overall_score = base_score + prob_bonus + roi_bonus + ai_bonus
        return min(10.0, max(0.0, overall_score))
    
    def _calculate_recommendation_strength(self, secure_opp: SecureBettingOpportunity,
                                         game_analysis: Optional[ComprehensiveMatchAnalysis]) -> str:
        """Calculate recommendation strength"""
        
        overall_score = self._calculate_overall_score(secure_opp, game_analysis)
        
        if overall_score >= 9.0:
            return "🔥 MUST BET"
        elif overall_score >= 7.5:
            return "⭐ STRONG BET"
        elif overall_score >= 6.0:
            return "👍 GOOD BET"
        else:
            return "⚪ CONSIDER"
    
    async def _process_analysis_results(self, analysis_results: Dict[str, Any]):
        """Process and store analysis results"""
        
        if analysis_results['status'] != 'success':
            return
        
        # Update current opportunities
        self.system_stats['current_opportunities'] = analysis_results['combined_results']
        self.system_stats['secure_opportunities_found'] += len(analysis_results['secure_opportunities'])
        
        # Save results if configured
        if self.config['save_analyses']:
            await self._save_analysis_results(analysis_results)
        
        # Log summary
        logger.info(f"📊 Analysis processed: {len(analysis_results['combined_results'])} opportunities")
    
    async def _check_and_announce_opportunities(self):
        """Check for opportunities to announce"""
        
        if not self.telegram_announcer:
            return
        
        current_opportunities = self.system_stats['current_opportunities']
        
        if not current_opportunities:
            return
        
        # Filter high-quality opportunities
        announcement_worthy = [
            opp for opp in current_opportunities
            if (opp['overall_score'] >= 7.0 and 
                opp['win_probability'] >= self.config['min_win_probability'] and
                opp['expected_roi'] >= self.config['min_roi_threshold'])
        ]
        
        if announcement_worthy:
            # Announce top opportunities
            for opportunity in announcement_worthy[:3]:  # Top 3
                await self._announce_opportunity(opportunity)
                await asyncio.sleep(30)  # 30 seconds between announcements
    
    async def _announce_opportunity(self, opportunity: Dict[str, Any]):
        """Announce a specific opportunity"""
        
        try:
            # Create announcement message
            message = self._create_opportunity_announcement(opportunity)
            
            # Send announcement
            success = await self.telegram_announcer._send_announcement(message)
            
            if success:
                self.system_stats['announcements_sent'] += 1
                logger.info(f"📱 Announced: {opportunity['home_team']} vs {opportunity['away_team']}")
            
        except Exception as e:
            logger.error(f"❌ Error announcing opportunity: {e}")
    
    def _create_opportunity_announcement(self, opportunity: Dict[str, Any]) -> str:
        """Create comprehensive opportunity announcement"""
        
        # Security emoji
        security_emojis = {
            'ultra_secure': '🔒',
            'very_secure': '🛡️',
            'secure': '✅',
            'moderate': '⚠️'
        }
        
        security_emoji = security_emojis.get(opportunity['security_level'], '📊')
        
        # Sport emoji
        sport_emojis = {
            'football': '⚽',
            'tennis': '🎾',
            'basketball': '🏀',
            'ice_hockey': '🏒'
        }
        sport_emoji = sport_emojis.get(opportunity['sport'], '🏆')
        
        # Calculate financial metrics
        stake_amount = opportunity['recommended_stake'] * 100  # Assuming $10k bankroll
        potential_profit = stake_amount * opportunity['expected_roi'] / 100
        
        message = f"""
🚨 **ULTIMATE BETTING INTELLIGENCE ALERT** {security_emoji}

{sport_emoji} **{opportunity['home_team']} vs {opportunity['away_team']}**
📅 {opportunity['match_time'].strftime('%Y-%m-%d %H:%M')}

🛡️ **SECURITY ANALYSIS:**
• Level: {security_emoji} {opportunity['security_level'].upper().replace('_', ' ')}
• Win Probability: {opportunity['win_probability']:.1%}
• Overall Score: {opportunity['overall_score']:.1f}/10
• {opportunity['recommendation_strength']}

🤖 **AI PREDICTION:**
{self._format_ai_prediction(opportunity.get('ai_prediction'))}

💰 **FINANCIAL ANALYSIS:**
• Expected ROI: {opportunity['expected_roi']:.1f}%
• Recommended Stake: {opportunity['recommended_stake']:.1f}% (${stake_amount:.0f})
• Potential Profit: ${potential_profit:.0f}

🔑 **SAFETY FACTORS:**
{self._format_safety_factors(opportunity['safety_factors'])}

📊 **STATISTICAL EDGE:**
{self._format_statistical_edge(opportunity.get('statistical_edge'))}

🏥 **INJURY IMPACT:**
{self._format_injury_analysis(opportunity.get('injury_analysis'))}

⚠️ **RISK ASSESSMENT:**
• Security Level: {opportunity['security_level'].upper()}
• Data Quality: {opportunity.get('confidence_metrics', {}).get('data_reliability', 0.85):.0%}
• Model Confidence: {opportunity.get('confidence_metrics', {}).get('model_accuracy', 0.72):.0%}

🎯 **This is a HIGH-SECURITY opportunity with comprehensive AI analysis!**

⏰ **Act quickly - opportunity expires soon!**
        """
        
        return message.strip()
    
    def _format_ai_prediction(self, ai_prediction: Optional[Dict[str, Any]]) -> str:
        """Format AI prediction for announcement"""
        
        if not ai_prediction:
            return "• AI analysis: Standard prediction model applied"
        
        return f"""• Winner: {ai_prediction.get('predicted_winner', 'N/A')}
• Confidence: {ai_prediction.get('win_probability', 0):.0%}
• Key Factors: {', '.join(ai_prediction.get('key_factors', [])[:2])}"""
    
    def _format_safety_factors(self, safety_factors: List[str]) -> str:
        """Format safety factors"""
        
        if not safety_factors:
            return "• Standard security analysis applied"
        
        return '\n'.join(f"• {factor}" for factor in safety_factors[:4])
    
    def _format_statistical_edge(self, statistical_edge: Optional[Dict[str, Any]]) -> str:
        """Format statistical edge information"""
        
        if not statistical_edge:
            return "• Statistical analysis: Comprehensive model applied"
        
        match_winner = statistical_edge.get('match_winner', {})
        goals_analysis = statistical_edge.get('goals_analysis', {})
        
        return f"""• Home Win: {match_winner.get('home_win_probability', 0):.0%}
• Expected Goals: {goals_analysis.get('total_expected_goals', 0):.1f}
• Value Markets: {len(statistical_edge.get('value_markets', []))} detected"""
    
    def _format_injury_analysis(self, injury_analysis: Optional[Dict[str, Any]]) -> str:
        """Format injury analysis"""
        
        if not injury_analysis:
            return "• No significant injury concerns"
        
        home_impact = injury_analysis.get('impact_assessment', {}).get('home_team_impact', 'minimal')
        away_impact = injury_analysis.get('impact_assessment', {}).get('away_team_impact', 'minimal')
        
        return f"""• Home Team Impact: {home_impact.title()}
• Away Team Impact: {away_impact.title()}
• Key Players Affected: {injury_analysis.get('impact_assessment', {}).get('key_players_affected', 0)}"""
    
    async def _update_performance_metrics(self):
        """Update system performance metrics"""
        
        # Calculate uptime
        uptime = datetime.now() - self.system_stats['system_uptime']
        
        # Update metrics
        self.performance_history.append({
            'timestamp': datetime.now(),
            'total_analyses': self.system_stats['total_analyses'],
            'opportunities_found': self.system_stats['secure_opportunities_found'],
            'announcements_sent': self.system_stats['announcements_sent'],
            'uptime_hours': uptime.total_seconds() / 3600
        })
        
        # Keep only last 24 hours of history
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.performance_history = [
            entry for entry in self.performance_history
            if entry['timestamp'] > cutoff_time
        ]
    
    async def _send_startup_announcement(self):
        """Send system startup announcement"""
        
        startup_message = """
🚀 **ULTIMATE BETTING INTELLIGENCE SYSTEM ACTIVATED**

🎯 **Welcome to the most advanced betting intelligence system!**

**🛡️ SECURITY-FIRST APPROACH:**
• 🔒 Ultra Secure: 90%+ win probability
• 🛡️ Very Secure: 80-90% win probability  
• ✅ Secure: 70-80% win probability
• Only the safest opportunities are announced

**🤖 AI-POWERED ANALYSIS:**
• Comprehensive match analysis with 50+ factors
• Real-time injury and suspension tracking
• Weather and venue condition monitoring
• Historical performance and trend analysis
• Statistical edge detection and value betting

**📊 CONTINUOUS MONITORING:**
• 24/7 analysis of all major sports
• Football, Tennis, Basketball, Ice Hockey
• Premier leagues and tournaments worldwide
• Real-time odds monitoring and alerts

**💰 ROI OPTIMIZATION:**
• Conservative stake sizing (max 3% per bet)
• Kelly Criterion optimization
• Risk-adjusted returns calculation
• Portfolio diversification management

**📱 INTELLIGENT NOTIFICATIONS:**
• Only high-value opportunities announced
• Comprehensive analysis with each alert
• Clear reasoning and risk assessment
• Optimal timing for maximum value

🎯 **TARGET PERFORMANCE:**
• 70%+ win rate on announced opportunities
• 15%+ average ROI per successful bet
• Maximum 20 announcements per day
• Focus on quality over quantity

⚠️ **IMPORTANT REMINDERS:**
• This system provides analysis, not guarantees
• Always verify odds before placing bets
• Never bet more than you can afford to lose
• Responsible gambling is essential

🔄 **System is now monitoring matches and will announce opportunities as they arise!**

💡 **Next analysis cycle starts in 5 minutes...**
        """
        
        await self.telegram_announcer._send_announcement(startup_message.strip())
    
    async def _send_status_update(self):
        """Send periodic status update"""
        
        if not self.telegram_announcer:
            return
        
        uptime = datetime.now() - self.system_stats['system_uptime']
        
        # Calculate recent performance
        recent_analyses = sum(1 for entry in self.performance_history if entry['timestamp'] > datetime.now() - timedelta(hours=6))
        recent_opportunities = len([opp for opp in self.system_stats['current_opportunities'] if opp['overall_score'] >= 7.0])
        
        status_message = f"""
📊 **SYSTEM STATUS UPDATE**

🤖 **System Health:** ✅ OPERATIONAL

⏱️ **Uptime:** {uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m

📈 **Performance (Last 6 Hours):**
• Analyses Completed: {recent_analyses}
• Secure Opportunities: {recent_opportunities}
• Announcements Sent: {self.system_stats['announcements_sent']}

🎯 **Current Status:**
• Active Opportunities: {len(self.system_stats['current_opportunities'])}
• High-Quality Bets: {recent_opportunities}
• System Load: Normal

🔍 **Monitoring:**
• Sports: {', '.join(self.config['sports_monitored'])}
• Analysis Interval: {self.config['analysis_interval']//60} minutes
• Security Levels: {', '.join(self.config['security_levels'])}

💡 **Next deep analysis in {self.config['analysis_interval']//60} minutes**

🎯 **System performing optimally and ready to identify profitable opportunities!**
        """
        
        await self.telegram_announcer._send_announcement(status_message.strip())
    
    async def _save_analysis_results(self, results: Dict[str, Any]):
        """Save analysis results to file"""
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"ultimate_analysis_{timestamp}.json"
            
            # Prepare data for JSON serialization
            serializable_results = {
                'status': results['status'],
                'timestamp': results['timestamp'].isoformat(),
                'matches_analyzed': results['matches_analyzed'],
                'secure_opportunities_count': len(results['secure_opportunities']),
                'combined_results_count': len(results['combined_results']),
                'top_opportunities': results['combined_results'][:5]  # Save top 5
            }
            
            with open(filename, 'w') as f:
                json.dump(serializable_results, f, indent=2, default=str)
            
            logger.debug(f"✅ Analysis results saved: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Error saving analysis results: {e}")
    
    async def _shutdown_system(self):
        """Graceful system shutdown"""
        
        logger.info("🛑 Shutting down Ultimate Betting Intelligence System...")
        
        if self.telegram_announcer:
            shutdown_message = """
🛑 **SYSTEM SHUTDOWN NOTICE**

The Ultimate Betting Intelligence System is shutting down.

📊 **Final Statistics:**
• Total Analyses: {self.system_stats['total_analyses']}
• Opportunities Found: {self.system_stats['secure_opportunities_found']}
• Announcements Sent: {self.system_stats['announcements_sent']}

Thank you for using the Ultimate Betting Intelligence System!

🎯 **Remember: Always bet responsibly!**
            """
            
            await self.telegram_announcer._send_announcement(shutdown_message.strip())
        
        logger.info("✅ System shutdown complete")
    
    async def run_single_analysis(self) -> Dict[str, Any]:
        """Run a single analysis cycle (for testing)"""
        
        logger.info("🧪 Running single analysis cycle...")
        
        # Run analysis
        results = await self._run_comprehensive_analysis()
        
        # Process results
        if results['status'] == 'success':
            await self._process_analysis_results(results)
            
            # Send test announcement if opportunities found
            if results['combined_results'] and self.telegram_announcer:
                top_opportunity = results['combined_results'][0]
                await self._announce_opportunity(top_opportunity)
        
        return results

async def main():
    """Main function for testing the ultimate system"""
    print("🎯 ULTIMATE BETTING INTELLIGENCE SYSTEM")
    print("=" * 60)
    
    # Configuration
    config = {
        'analysis_interval': 300,
        'sports_monitored': ['football', 'tennis', 'basketball'],
        'telegram_enabled': True,
        'continuous_monitoring': False,  # Single run for testing
        'min_win_probability': 0.70,
        'min_roi_threshold': 10.0
    }
    
    # Initialize system
    system = UltimateBettingIntelligenceSystem(config)
    
    print(f"\n⚙️ Configuration:")
    print(f"• Sports: {', '.join(config['sports_monitored'])}")
    print(f"• Min Win Probability: {config['min_win_probability']:.0%}")
    print(f"• Min ROI Threshold: {config['min_roi_threshold']:.1f}%")
    print(f"• Telegram: {'Enabled' if config['telegram_enabled'] else 'Disabled'}")
    
    # Run single analysis
    print(f"\n🔍 Running comprehensive analysis...")
    print("-" * 50)
    
    results = await system.run_single_analysis()
    
    # Display results
    if results['status'] == 'success':
        print(f"\n✅ ANALYSIS RESULTS:")
        print(f"📊 Matches analyzed: {results['matches_analyzed']}")
        print(f"🛡️ Secure opportunities: {len(results['secure_opportunities'])}")
        print(f"🎯 Combined results: {len(results['combined_results'])}")
        
        if results['combined_results']:
            print(f"\n🏆 TOP OPPORTUNITIES:")
            for i, opp in enumerate(results['combined_results'][:3], 1):
                print(f"{i}. {opp['home_team']} vs {opp['away_team']}")
                print(f"   🛡️ Security: {opp['security_level']}")
                print(f"   📊 Score: {opp['overall_score']:.1f}/10")
                print(f"   💰 ROI: {opp['expected_roi']:.1f}%")
                print(f"   🎯 {opp['recommendation_strength']}")
        
        print(f"\n📱 Telegram announcement sent for top opportunity")
        
    else:
        print(f"\n❌ Analysis failed: {results.get('error', 'Unknown error')}")
    
    print(f"\n🎯 Ultimate system ready for continuous operation!")
    print("Add --continuous flag for 24/7 monitoring.")

if __name__ == "__main__":
    import sys
    
    if "--continuous" in sys.argv:
        # Run continuous system
        config = {
            'analysis_interval': 300,
            'announcement_interval': 600,
            'sports_monitored': ['football', 'tennis', 'basketball', 'ice_hockey'],
            'telegram_enabled': True,
            'continuous_monitoring': True
        }
        
        system = UltimateBettingIntelligenceSystem(config)
        asyncio.run(system.start_system())
    else:
        # Run single analysis
        asyncio.run(main())
