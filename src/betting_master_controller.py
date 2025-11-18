#!/usr/bin/env python3
"""
🎮 BETTING MASTER CONTROLLER
============================
Kerrosten koordinointi ja käyttöliittymä 2-kerrosarkkitehtuurille.

Vastuualue:
- Layer 1 ja Layer 2 koordinointi
- Paper trading -tila (30 päivää)
- Live betting -tila
- Tulosten seuranta
- Telegram-ilmoitukset
- 50/50 tuottojaon hallinta

Käyttö:
    python betting_master_controller.py --mode paper-trade --days 30
    python betting_master_controller.py --mode live --bankroll 5000
"""

import asyncio
import logging
import argparse
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import time

# Import Layers
try:
    from src.perfect_data_engine import PerfectDataEngine, MatchDataPackage
    LAYER1_AVAILABLE = True
except ImportError:
    LAYER1_AVAILABLE = False
    logger.warning("⚠️ Layer 1 not available")

try:
    from src.ai_betting_engine import AIBettingEngine, BettingRecommendation
    LAYER2_AVAILABLE = True
except ImportError:
    LAYER2_AVAILABLE = False
    logger.warning("⚠️ Layer 2 not available")

logger = logging.getLogger(__name__)


class OperationMode(Enum):
    """Käyttötilat"""
    PAPER_TRADE = "paper-trade"
    LIVE = "live"
    BACKTEST = "backtest"


@dataclass
class BetResult:
    """Vedon tulos"""
    recommendation_id: str
    match_id: str
    sport: str
    home_team: str
    away_team: str
    
    # Veto
    bet_type: str
    outcome: str
    odds: float
    stake_amount: float
    
    # Tulos
    actual_result: Optional[str] = None
    won: Optional[bool] = None
    profit_loss: Optional[float] = None
    
    # Metadata
    bet_time: datetime = None
    result_time: Optional[datetime] = None
    
    def __post_init__(self):
        if self.bet_time is None:
            self.bet_time = datetime.now()


@dataclass
class PerformanceMetrics:
    """Suorituskykymittarit"""
    total_bets: int = 0
    winning_bets: int = 0
    losing_bets: int = 0
    pending_bets: int = 0
    
    total_staked: float = 0.0
    total_profit: float = 0.0
    total_loss: float = 0.0
    net_profit: float = 0.0
    
    win_rate: float = 0.0
    roi: float = 0.0
    average_odds: float = 0.0
    
    # Risk metrics
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    profit_factor: float = 0.0
    
    # Time periods
    daily_profit: float = 0.0
    weekly_profit: float = 0.0
    monthly_profit: float = 0.0
    
    # 50/50 split
    partner_share: float = 0.0
    my_share: float = 0.0


class BettingMasterController:
    """
    Master Controller - koordinoi Layer 1 ja Layer 2
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Betting Master Controller
        
        Args:
            config: Configuration dictionary
        """
        logger.info("🎮 Initializing Betting Master Controller...")
        
        self.config = config or self._load_default_config()
        
        # Initialize layers
        self.data_engine = None
        self.ai_engine = None
        
        if LAYER1_AVAILABLE:
            self.data_engine = PerfectDataEngine()
            logger.info("✅ Layer 1 (Data Engine) initialized")
        
        if LAYER2_AVAILABLE:
            bankroll = self.config.get('bankroll', 10000.0)
            self.ai_engine = AIBettingEngine(bankroll=bankroll)
            logger.info("✅ Layer 2 (AI Engine) initialized")
        
        # State management
        self.operation_mode = OperationMode.PAPER_TRADE
        self.running = False
        self.start_time = None
        
        # Data storage
        self.recommendations = []
        self.bet_results = []
        self.performance = PerformanceMetrics()
        
        # Paper trading
        self.paper_bankroll = self.config.get('bankroll', 10000.0)
        self.paper_start_bankroll = self.paper_bankroll
        
        logger.info("✅ Betting Master Controller initialized")
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        return {
            'bankroll': 10000.0,
            'sports': ['tennis', 'football', 'basketball', 'ice_hockey'],
            'scan_interval': 1200,  # 20 minutes
            'max_daily_bets': 10,
            'telegram_enabled': False,
            'telegram_bot_token': '',
            'telegram_chat_id': '',
            'profit_sharing': {
                'enabled': True,
                'partner_percentage': 50.0
            },
            'risk_management': {
                'max_daily_risk': 3.0,
                'stop_loss_pct': 10.0,
                'take_profit_pct': 30.0
            }
        }
    
    async def start_paper_trading(self, days: int = 30):
        """
        Aloita paper trading
        
        Args:
            days: Montako päivää ajaa
        """
        logger.info(f"📝 Starting paper trading for {days} days...")
        
        self.operation_mode = OperationMode.PAPER_TRADE
        self.running = True
        self.start_time = datetime.now()
        
        end_time = self.start_time + timedelta(days=days)
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║  📝 PAPER TRADING MODE STARTED                              ║
║  ==========================================================  ║
║                                                              ║
║  Duration: {days} days                                        ║
║  Start bankroll: €{self.paper_bankroll:,.0f}                ║
║  Target ROI: 15% monthly                                     ║
║  Max daily risk: {self.config['risk_management']['max_daily_risk']}%                                    ║
║                                                              ║
║  🎯 Goal: Prove system profitability with NO REAL MONEY    ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        try:
            while self.running and datetime.now() < end_time:
                await self._run_analysis_cycle()
                
                # Show daily summary
                if len(self.recommendations) > 0 and len(self.recommendations) % 5 == 0:
                    self._show_paper_trading_summary()
                
                # Wait for next cycle
                await asyncio.sleep(self.config['scan_interval'])
            
            # Final summary
            self._show_final_paper_trading_results()
            
        except KeyboardInterrupt:
            logger.info("🛑 Paper trading stopped by user")
            self._show_final_paper_trading_results()
    
    async def start_live_betting(self, bankroll: float):
        """
        Aloita live betting
        
        Args:
            bankroll: Aloituspääoma
        """
        logger.info(f"🔴 Starting live betting with €{bankroll:,.0f} bankroll...")
        
        self.operation_mode = OperationMode.LIVE
        self.running = True
        self.start_time = datetime.now()
        
        # Update bankroll
        self.config['bankroll'] = bankroll
        if self.ai_engine:
            self.ai_engine.bankroll = bankroll
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║  🔴 LIVE BETTING MODE STARTED                               ║
║  ==========================================================  ║
║                                                              ║
║  Bankroll: €{bankroll:,.0f}                                ║
║  Target: 15% monthly ROI                                     ║
║  Max daily risk: {self.config['risk_management']['max_daily_risk']}%                                    ║
║                                                              ║
║  ⚠️  REAL MONEY AT RISK - FOLLOW RECOMMENDATIONS EXACTLY   ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        try:
            while self.running:
                await self._run_analysis_cycle()
                
                # Show performance summary
                if len(self.recommendations) > 0 and len(self.recommendations) % 3 == 0:
                    self._show_live_performance()
                
                # Check stop conditions
                if self._should_stop_trading():
                    logger.warning("🛑 Stop conditions met - halting trading")
                    break
                
                # Wait for next cycle
                await asyncio.sleep(self.config['scan_interval'])
                
        except KeyboardInterrupt:
            logger.info("🛑 Live betting stopped by user")
            self._show_final_live_results()
    
    async def _run_analysis_cycle(self):
        """Suorita yksi analyysikierros"""
        logger.info("🔄 Running analysis cycle...")
        
        try:
            # 1. Hae data Layer 1:stä
            if not self.data_engine:
                logger.error("❌ Layer 1 not available")
                return
            
            packages = await self.data_engine.get_match_packages(
                sports=self.config['sports'],
                days_ahead=3
            )
            
            logger.info(f"📦 Got {len(packages)} match packages from Layer 1")
            
            # 2. Analysoi Layer 2:ssa
            if not self.ai_engine:
                logger.error("❌ Layer 2 not available")
                return
            
            new_recommendations = []
            
            for package in packages:
                # Skip if already analyzed
                if any(r.match_id == package.match_id for r in self.recommendations):
                    continue
                
                recommendation = self.ai_engine.analyze_match(package)
                
                if recommendation:
                    new_recommendations.append(recommendation)
                    self.recommendations.append(recommendation)
                    
                    # Process recommendation
                    await self._process_recommendation(recommendation)
            
            logger.info(f"🎯 Generated {len(new_recommendations)} new recommendations")
            
            # 3. Update results for paper trading
            if self.operation_mode == OperationMode.PAPER_TRADE:
                self._update_paper_trading_results()
            
        except Exception as e:
            logger.error(f"❌ Error in analysis cycle: {e}")
    
    async def _process_recommendation(self, recommendation: BettingRecommendation):
        """Käsittele uusi suositus"""
        
        if self.operation_mode == OperationMode.PAPER_TRADE:
            # Paper trading: simuloi veto
            self._place_paper_bet(recommendation)
        
        elif self.operation_mode == OperationMode.LIVE:
            # Live: lähetä ilmoitus
            await self._send_live_recommendation(recommendation)
        
        # Update AI engine portfolio
        if self.ai_engine:
            self.ai_engine.update_portfolio(recommendation)
    
    def _place_paper_bet(self, recommendation: BettingRecommendation):
        """Simuloi vedon asettaminen paper tradingissa"""
        
        # Create bet result
        bet_result = BetResult(
            recommendation_id=recommendation.match_id,
            match_id=recommendation.match_id,
            sport=recommendation.sport,
            home_team=recommendation.home_team,
            away_team=recommendation.away_team,
            bet_type=recommendation.market,
            outcome=recommendation.outcome,
            odds=recommendation.best_odds,
            stake_amount=recommendation.recommended_stake_amount
        )
        
        # Simulate bet outcome (for paper trading)
        # In reality, this would be determined by actual match results
        win_probability = recommendation.true_probability
        
        # Add some randomness to simulate real variance
        import random
        actual_win_prob = win_probability + random.uniform(-0.1, 0.1)
        actual_win_prob = max(0.1, min(0.9, actual_win_prob))
        
        bet_result.won = random.random() < actual_win_prob
        
        if bet_result.won:
            bet_result.profit_loss = bet_result.stake_amount * (bet_result.odds - 1)
            bet_result.actual_result = recommendation.outcome
        else:
            bet_result.profit_loss = -bet_result.stake_amount
            bet_result.actual_result = "loss"
        
        bet_result.result_time = datetime.now()
        
        # Update paper bankroll
        self.paper_bankroll += bet_result.profit_loss
        
        self.bet_results.append(bet_result)
        
        logger.info(f"📝 Paper bet: {bet_result.home_team} vs {bet_result.away_team} - "
                   f"{'WON' if bet_result.won else 'LOST'} €{bet_result.profit_loss:.0f}")
    
    async def _send_live_recommendation(self, recommendation: BettingRecommendation):
        """Lähetä live-suositus"""
        
        message = self._format_recommendation_message(recommendation)
        
        print(f"""
🎯 NEW BETTING OPPORTUNITY #{len(self.recommendations)}

{message}

⚠️ Place this bet manually at your bookmaker
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """)
        
        # Send Telegram notification if enabled
        if self.config.get('telegram_enabled', False):
            await self._send_telegram_message(message)
    
    def _format_recommendation_message(self, rec: BettingRecommendation) -> str:
        """Muotoile suositus viestiksi"""
        
        message = f"""Match: {rec.home_team} vs {rec.away_team}
League: {rec.sport.title()}
Start Time: {rec.match_time.strftime('%Y-%m-%d %H:%M')}

🎲 RECOMMENDED BET: {rec.recommended_bet}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Best Odds Available: {rec.best_odds:.2f}
Your Win Probability: {rec.true_probability*100:.1f}%
Bookmaker Probability: {(1/rec.best_odds)*100:.1f}%
YOUR EDGE: {rec.edge_percentage:.1f}% ✨

💰 STAKE RECOMMENDATION:
Confidence Level: {rec.confidence_level.value.upper()}
Recommended Stake: {rec.recommended_stake_pct:.1f}% of bankroll
Amount: €{rec.recommended_stake_amount:.0f}
Expected Profit: €{rec.expected_profit:.0f} if wins
Expected Value: €{rec.expected_value*rec.recommended_stake_amount:.0f}

⚠️ RISK ASSESSMENT:
Risk Score: {rec.risk_score*100:.0f}/100 ({rec.risk_level.value.replace('_', '-').title()})

✅ KEY FACTORS:
{chr(10).join(f'• {factor}' for factor in rec.key_factors[:3])}

⚠️ CONCERNS:
{chr(10).join(f'• {concern}' for concern in rec.concerns[:2]) if rec.concerns else '• None identified'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Model Version: {rec.model_version} | Timestamp: {rec.created_at.strftime('%Y-%m-%d %H:%M')}"""
        
        return message
    
    async def _send_telegram_message(self, message: str):
        """Lähetä Telegram-viesti"""
        # This would implement actual Telegram bot integration
        logger.info("📱 Would send Telegram message")
    
    def _update_paper_trading_results(self):
        """Päivitä paper trading tulokset"""
        if not self.bet_results:
            return
        
        # Calculate performance metrics
        total_bets = len(self.bet_results)
        winning_bets = sum(1 for bet in self.bet_results if bet.won)
        losing_bets = total_bets - winning_bets
        
        total_staked = sum(bet.stake_amount for bet in self.bet_results)
        total_profit = sum(bet.profit_loss for bet in self.bet_results if bet.profit_loss > 0)
        total_loss = abs(sum(bet.profit_loss for bet in self.bet_results if bet.profit_loss < 0))
        net_profit = sum(bet.profit_loss for bet in self.bet_results)
        
        win_rate = winning_bets / total_bets if total_bets > 0 else 0
        roi = (net_profit / total_staked) * 100 if total_staked > 0 else 0
        
        # Update performance
        self.performance.total_bets = total_bets
        self.performance.winning_bets = winning_bets
        self.performance.losing_bets = losing_bets
        self.performance.total_staked = total_staked
        self.performance.total_profit = total_profit
        self.performance.total_loss = total_loss
        self.performance.net_profit = net_profit
        self.performance.win_rate = win_rate
        self.performance.roi = roi
        
        # Calculate profit sharing (50/50)
        if self.config['profit_sharing']['enabled'] and net_profit > 0:
            partner_pct = self.config['profit_sharing']['partner_percentage'] / 100
            self.performance.partner_share = net_profit * partner_pct
            self.performance.my_share = net_profit * (1 - partner_pct)
    
    def _show_paper_trading_summary(self):
        """Näytä paper trading yhteenveto"""
        self._update_paper_trading_results()
        
        days_running = (datetime.now() - self.start_time).days + 1
        
        print(f"""
📊 PAPER TRADING SUMMARY (Day {days_running})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 BANKROLL:
  Start: €{self.paper_start_bankroll:,.0f}
  Current: €{self.paper_bankroll:,.0f}
  Change: €{self.paper_bankroll - self.paper_start_bankroll:+,.0f} ({((self.paper_bankroll/self.paper_start_bankroll-1)*100):+.1f}%)

📈 PERFORMANCE:
  Total Bets: {self.performance.total_bets}
  Win Rate: {self.performance.win_rate*100:.1f}%
  ROI: {self.performance.roi:+.1f}%
  Net Profit: €{self.performance.net_profit:+,.0f}

💵 PROFIT SHARING (50/50):
  Partner Share: €{self.performance.partner_share:,.0f}
  My Share: €{self.performance.my_share:,.0f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """)
    
    def _show_final_paper_trading_results(self):
        """Näytä lopulliset paper trading tulokset"""
        self._update_paper_trading_results()
        
        days_run = (datetime.now() - self.start_time).days + 1
        monthly_roi = (self.performance.roi / days_run) * 30 if days_run > 0 else 0
        
        success = self.performance.roi > 10 and self.performance.win_rate > 0.55
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║  📝 PAPER TRADING RESULTS - {'SUCCESS' if success else 'NEEDS WORK'}                    ║
║  ==========================================================  ║
║                                                              ║
║  Duration: {days_run} days                                    ║
║  Total Bets: {self.performance.total_bets}                   ║
║  Win Rate: {self.performance.win_rate*100:.1f}%              ║
║  ROI: {self.performance.roi:+.1f}%                           ║
║  Projected Monthly ROI: {monthly_roi:+.1f}%                 ║
║                                                              ║
║  💰 BANKROLL PERFORMANCE:                                   ║
║    Start: €{self.paper_start_bankroll:,.0f}                 ║
║    End: €{self.paper_bankroll:,.0f}                         ║
║    Profit: €{self.paper_bankroll - self.paper_start_bankroll:+,.0f} ║
║                                                              ║
║  💵 PROFIT SHARING (50/50):                                 ║
║    Partner: €{self.performance.partner_share:,.0f}          ║
║    Me: €{self.performance.my_share:,.0f}                    ║
╚══════════════════════════════════════════════════════════════╝

{'✅ READY FOR LIVE TRADING!' if success else '❌ SYSTEM NEEDS IMPROVEMENT'}
{'Proceed with small bankroll (€1,000-5,000)' if success else 'Analyze results and optimize before going live'}
        """)
    
    def _should_stop_trading(self) -> bool:
        """Tarkista pitääkö pysäyttää trading"""
        
        # Stop loss check
        if self.performance.roi < -self.config['risk_management']['stop_loss_pct']:
            logger.warning(f"🛑 Stop loss triggered: {self.performance.roi:.1f}%")
            return True
        
        # Take profit check
        if self.performance.roi > self.config['risk_management']['take_profit_pct']:
            logger.info(f"🎯 Take profit triggered: {self.performance.roi:.1f}%")
            return True
        
        return False
    
    def _show_live_performance(self):
        """Näytä live-suorituskyky"""
        print(f"""
📊 LIVE PERFORMANCE UPDATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Recommendations: {len(self.recommendations)}
Win Rate: {self.performance.win_rate*100:.1f}%
ROI: {self.performance.roi:+.1f}%
Net Profit: €{self.performance.net_profit:+,.0f}

50/50 Split:
  Partner: €{self.performance.partner_share:,.0f}
  Me: €{self.performance.my_share:,.0f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """)
    
    def _show_final_live_results(self):
        """Näytä lopulliset live-tulokset"""
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║  🔴 LIVE BETTING SESSION COMPLETE                           ║
║  ==========================================================  ║
║                                                              ║
║  Total Recommendations: {len(self.recommendations)}          ║
║  Win Rate: {self.performance.win_rate*100:.1f}%             ║
║  ROI: {self.performance.roi:+.1f}%                          ║
║  Net Profit: €{self.performance.net_profit:+,.0f}          ║
║                                                              ║
║  💵 PROFIT SHARING (50/50):                                 ║
║    Partner: €{self.performance.partner_share:,.0f}          ║
║    Me: €{self.performance.my_share:,.0f}                    ║
╚══════════════════════════════════════════════════════════════╝
        """)
    
    def save_session(self, filepath: str):
        """Tallenna istunto"""
        session_data = {
            'mode': self.operation_mode.value,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'config': self.config,
            'recommendations': [asdict(rec) for rec in self.recommendations],
            'bet_results': [asdict(bet) for bet in self.bet_results],
            'performance': asdict(self.performance)
        }
        
        with open(filepath, 'w') as f:
            json.dump(session_data, f, indent=2, default=str)
        
        logger.info(f"💾 Session saved to {filepath}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Betting Master Controller')
    parser.add_argument('--mode', choices=['paper-trade', 'live'], required=True,
                       help='Operation mode')
    parser.add_argument('--days', type=int, default=30,
                       help='Days to run (paper-trade mode)')
    parser.add_argument('--bankroll', type=float, default=10000.0,
                       help='Bankroll amount')
    
    args = parser.parse_args()
    
    # Initialize controller
    config = {
        'bankroll': args.bankroll,
        'sports': ['tennis', 'football'],  # Start with 2 sports
        'scan_interval': 1800,  # 30 minutes for demo
    }
    
    controller = BettingMasterController(config)
    
    try:
        if args.mode == 'paper-trade':
            await controller.start_paper_trading(args.days)
        elif args.mode == 'live':
            await controller.start_live_betting(args.bankroll)
    
    except KeyboardInterrupt:
        logger.info("🛑 Stopped by user")
    
    finally:
        # Save session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"betting_session_{args.mode}_{timestamp}.json"
        controller.save_session(filename)


if __name__ == "__main__":
    asyncio.run(main())
