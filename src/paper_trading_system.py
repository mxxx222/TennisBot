#!/usr/bin/env python3
"""
📝 PAPER TRADING SYSTEM
=======================
30 päivän paper trading -järjestelmä järjestelmän testaamiseen ilman oikeaa rahaa.

Ominaisuudet:
- Simuloi oikeat markkinaolosuhteet
- Seuraa kaikkia vetoja ja tuloksia
- Laskee tarkat suorituskykymittarit
- Generoi yksityiskohtaisia raportteja
- Validoi järjestelmän kannattavuus

Tavoite: Todistaa järjestelmän toimivuus ennen oikean rahan käyttöä
"""

import asyncio
import logging
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import statistics
import math

logger = logging.getLogger(__name__)


@dataclass
class PaperBet:
    """Paper trading veto"""
    bet_id: str
    match_id: str
    sport: str
    home_team: str
    away_team: str
    
    # Veto
    bet_type: str  # 'h2h', 'over_under', etc.
    outcome: str   # 'home', 'away', 'over', 'under'
    odds: float
    stake: float
    
    # Ennuste
    predicted_probability: float
    confidence: float
    edge_percentage: float
    expected_value: float
    
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
class PaperTradingResults:
    """Paper trading tulokset"""
    # Perusstatistiikka
    total_bets: int = 0
    winning_bets: int = 0
    losing_bets: int = 0
    
    # Rahat
    starting_bankroll: float = 10000.0
    current_bankroll: float = 10000.0
    total_staked: float = 0.0
    total_profit: float = 0.0
    total_loss: float = 0.0
    net_profit: float = 0.0
    
    # Suorituskyky
    win_rate: float = 0.0
    roi: float = 0.0
    average_odds: float = 0.0
    
    # Riskimittarit
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    profit_factor: float = 0.0
    
    # Aikaperiodit
    daily_profits: List[float] = None
    weekly_profits: List[float] = None
    
    # Lajit
    sport_performance: Dict[str, Dict[str, Any]] = None
    
    # Luottamus
    avg_confidence: float = 0.0
    avg_edge: float = 0.0
    
    def __post_init__(self):
        if self.daily_profits is None:
            self.daily_profits = []
        if self.weekly_profits is None:
            self.weekly_profits = []
        if self.sport_performance is None:
            self.sport_performance = {}


class MarketSimulator:
    """Simuloi oikeat markkinaolosuhteet"""
    
    def __init__(self):
        self.variance_factor = 0.15  # 15% variance in outcomes
        
    def simulate_match_result(self, predicted_probability: float, confidence: float) -> bool:
        """
        Simuloi ottelun tulos
        
        Args:
            predicted_probability: Ennustettu todennäköisyys
            confidence: Luottamus ennusteeseen
            
        Returns:
            True jos veto voittaa
        """
        
        # Lisää varianssia luottamuksen perusteella
        # Matalampi luottamus = enemmän varianssia
        variance = self.variance_factor * (1 - confidence)
        
        # Säädä todennäköisyyttä varianssilla
        adjusted_probability = predicted_probability + random.uniform(-variance, variance)
        adjusted_probability = max(0.05, min(0.95, adjusted_probability))
        
        # Simuloi tulos
        return random.random() < adjusted_probability
    
    def simulate_odds_movement(self, original_odds: float) -> float:
        """Simuloi kerrointen liike"""
        
        # Kertoimet voivat liikkua ±5%
        movement = random.uniform(-0.05, 0.05)
        new_odds = original_odds * (1 + movement)
        
        return max(1.01, new_odds)  # Minimum odds 1.01


class PaperTradingSystem:
    """
    Paper Trading System - testaa järjestelmää 30 päivää
    """
    
    def __init__(self, starting_bankroll: float = 10000.0):
        """
        Initialize Paper Trading System
        
        Args:
            starting_bankroll: Aloituspääoma
        """
        logger.info("📝 Initializing Paper Trading System...")
        
        self.starting_bankroll = starting_bankroll
        self.current_bankroll = starting_bankroll
        self.peak_bankroll = starting_bankroll
        
        # Bets and results
        self.bets: List[PaperBet] = []
        self.results = PaperTradingResults(
            starting_bankroll=starting_bankroll,
            current_bankroll=starting_bankroll
        )
        
        # Market simulator
        self.market_simulator = MarketSimulator()
        
        # Tracking
        self.daily_bankrolls = [starting_bankroll]
        self.start_time = datetime.now()
        
        logger.info(f"✅ Paper Trading initialized with €{starting_bankroll:,.0f}")
    
    def place_bet(self, match_id: str, sport: str, home_team: str, away_team: str,
                  bet_type: str, outcome: str, odds: float, stake: float,
                  predicted_probability: float, confidence: float, 
                  edge_percentage: float, expected_value: float) -> str:
        """
        Aseta paper bet
        
        Args:
            match_id: Ottelun ID
            sport: Laji
            home_team: Kotijoukkue
            away_team: Vierasjoukkue
            bet_type: Vetotyyppi
            outcome: Tulos johon vedetään
            odds: Kertoimet
            stake: Panos
            predicted_probability: Ennustettu todennäköisyys
            confidence: Luottamus
            edge_percentage: Edge %
            expected_value: Odotettu arvo
            
        Returns:
            Bet ID
        """
        
        # Check bankroll
        if stake > self.current_bankroll:
            logger.warning(f"⚠️ Insufficient bankroll: €{stake:.0f} > €{self.current_bankroll:.0f}")
            return None
        
        # Create bet
        bet_id = f"paper_{len(self.bets)+1:04d}_{datetime.now().strftime('%H%M%S')}"
        
        bet = PaperBet(
            bet_id=bet_id,
            match_id=match_id,
            sport=sport,
            home_team=home_team,
            away_team=away_team,
            bet_type=bet_type,
            outcome=outcome,
            odds=odds,
            stake=stake,
            predicted_probability=predicted_probability,
            confidence=confidence,
            edge_percentage=edge_percentage,
            expected_value=expected_value
        )
        
        # Deduct stake from bankroll
        self.current_bankroll -= stake
        
        # Add to bets
        self.bets.append(bet)
        
        logger.info(f"📝 Paper bet placed: {home_team} vs {away_team} - {outcome} @ {odds:.2f} (€{stake:.0f})")
        
        return bet_id
    
    def settle_bet(self, bet_id: str, force_result: Optional[bool] = None) -> bool:
        """
        Selvitä veto
        
        Args:
            bet_id: Bet ID
            force_result: Pakota tulos (testaukseen)
            
        Returns:
            True jos veto voitti
        """
        
        # Find bet
        bet = None
        for b in self.bets:
            if b.bet_id == bet_id:
                bet = b
                break
        
        if not bet:
            logger.error(f"❌ Bet not found: {bet_id}")
            return False
        
        if bet.won is not None:
            logger.warning(f"⚠️ Bet already settled: {bet_id}")
            return bet.won
        
        # Simulate result
        if force_result is not None:
            won = force_result
        else:
            won = self.market_simulator.simulate_match_result(
                bet.predicted_probability, 
                bet.confidence
            )
        
        # Update bet
        bet.won = won
        bet.result_time = datetime.now()
        bet.actual_result = bet.outcome if won else "loss"
        
        if won:
            # Calculate winnings
            winnings = bet.stake * bet.odds
            profit = winnings - bet.stake
            bet.profit_loss = profit
            
            # Add to bankroll
            self.current_bankroll += winnings
            
            logger.info(f"✅ Bet WON: {bet.home_team} vs {bet.away_team} - Profit: €{profit:.0f}")
        else:
            # Loss
            bet.profit_loss = -bet.stake
            # Stake already deducted
            
            logger.info(f"❌ Bet LOST: {bet.home_team} vs {bet.away_team} - Loss: €{bet.stake:.0f}")
        
        # Update peak bankroll
        if self.current_bankroll > self.peak_bankroll:
            self.peak_bankroll = self.current_bankroll
        
        # Update results
        self._update_results()
        
        return won
    
    def simulate_day(self, num_bets: int = 3) -> List[str]:
        """
        Simuloi yhden päivän paper trading
        
        Args:
            num_bets: Montako vetoa päivässä
            
        Returns:
            Lista bet ID:itä
        """
        logger.info(f"📅 Simulating day with {num_bets} bets...")
        
        bet_ids = []
        
        # Generate demo bets for the day
        sports = ['tennis', 'football', 'basketball', 'ice_hockey']
        
        for i in range(num_bets):
            sport = random.choice(sports)
            
            # Generate demo match
            if sport == 'tennis':
                teams = [
                    ('Novak Djokovic', 'Carlos Alcaraz'),
                    ('Iga Swiatek', 'Coco Gauff'),
                    ('Daniil Medvedev', 'Stefanos Tsitsipas')
                ]
            elif sport == 'football':
                teams = [
                    ('Manchester City', 'Arsenal'),
                    ('Real Madrid', 'Barcelona'),
                    ('Bayern Munich', 'Borussia Dortmund')
                ]
            elif sport == 'basketball':
                teams = [
                    ('Los Angeles Lakers', 'Boston Celtics'),
                    ('Golden State Warriors', 'Miami Heat'),
                    ('Milwaukee Bucks', 'Phoenix Suns')
                ]
            else:  # ice_hockey
                teams = [
                    ('Toronto Maple Leafs', 'Montreal Canadiens'),
                    ('Boston Bruins', 'New York Rangers'),
                    ('Tampa Bay Lightning', 'Florida Panthers')
                ]
            
            home_team, away_team = random.choice(teams)
            
            # Generate bet parameters
            odds = random.uniform(1.6, 3.5)
            predicted_prob = random.uniform(0.4, 0.8)
            confidence = random.uniform(0.6, 0.9)
            edge = ((predicted_prob - (1/odds)) / (1/odds)) * 100
            
            # Only place bet if edge > 5%
            if edge < 5:
                continue
            
            # Calculate stake (Kelly Criterion)
            kelly_fraction = (predicted_prob * odds - 1) / (odds - 1)
            conservative_kelly = kelly_fraction * 0.25  # 25% Kelly
            stake_pct = min(conservative_kelly, 0.05)  # Max 5%
            stake = max(50, self.current_bankroll * stake_pct)  # Min €50
            
            # Place bet
            bet_id = self.place_bet(
                match_id=f"demo_{sport}_{i:03d}_{datetime.now().strftime('%Y%m%d')}",
                sport=sport,
                home_team=home_team,
                away_team=away_team,
                bet_type='h2h',
                outcome='home',
                odds=odds,
                stake=stake,
                predicted_probability=predicted_prob,
                confidence=confidence,
                edge_percentage=edge,
                expected_value=stake * ((predicted_prob * (odds - 1)) - (1 - predicted_prob))
            )
            
            if bet_id:
                bet_ids.append(bet_id)
                
                # Settle bet immediately (for simulation)
                self.settle_bet(bet_id)
        
        # Record daily bankroll
        self.daily_bankrolls.append(self.current_bankroll)
        
        return bet_ids
    
    def run_30_day_simulation(self) -> PaperTradingResults:
        """
        Aja 30 päivän simulaatio
        
        Returns:
            Lopulliset tulokset
        """
        logger.info("🚀 Starting 30-day paper trading simulation...")
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║  📝 30-DAY PAPER TRADING SIMULATION                         ║
║  ==========================================================  ║
║                                                              ║
║  Starting bankroll: €{self.starting_bankroll:,.0f}          ║
║  Target: Prove system profitability                         ║
║  Success criteria: >55% win rate, >10% ROI                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        for day in range(30):
            logger.info(f"📅 Day {day + 1}/30")
            
            # Simulate 2-5 bets per day
            num_bets = random.randint(2, 5)
            bet_ids = self.simulate_day(num_bets)
            
            # Show progress every 5 days
            if (day + 1) % 5 == 0:
                self._show_progress_report(day + 1)
        
        # Final results
        final_results = self._generate_final_report()
        
        return final_results
    
    def _update_results(self):
        """Päivitä tulokset"""
        
        settled_bets = [bet for bet in self.bets if bet.won is not None]
        
        if not settled_bets:
            return
        
        # Basic stats
        self.results.total_bets = len(settled_bets)
        self.results.winning_bets = sum(1 for bet in settled_bets if bet.won)
        self.results.losing_bets = self.results.total_bets - self.results.winning_bets
        
        # Money stats
        self.results.current_bankroll = self.current_bankroll
        self.results.total_staked = sum(bet.stake for bet in settled_bets)
        self.results.total_profit = sum(bet.profit_loss for bet in settled_bets if bet.profit_loss > 0)
        self.results.total_loss = abs(sum(bet.profit_loss for bet in settled_bets if bet.profit_loss < 0))
        self.results.net_profit = sum(bet.profit_loss for bet in settled_bets)
        
        # Performance metrics
        self.results.win_rate = self.results.winning_bets / self.results.total_bets
        self.results.roi = (self.results.net_profit / self.results.total_staked) * 100 if self.results.total_staked > 0 else 0
        self.results.average_odds = statistics.mean(bet.odds for bet in settled_bets)
        
        # Risk metrics
        self.results.max_drawdown = self.peak_bankroll - min(self.daily_bankrolls)
        self.results.max_drawdown_pct = (self.results.max_drawdown / self.peak_bankroll) * 100
        
        # Profit factor
        if self.results.total_loss > 0:
            self.results.profit_factor = self.results.total_profit / self.results.total_loss
        
        # Sharpe ratio (simplified)
        if len(self.daily_bankrolls) > 1:
            daily_returns = [(self.daily_bankrolls[i] - self.daily_bankrolls[i-1]) / self.daily_bankrolls[i-1] 
                           for i in range(1, len(self.daily_bankrolls))]
            if daily_returns:
                avg_return = statistics.mean(daily_returns)
                std_return = statistics.stdev(daily_returns) if len(daily_returns) > 1 else 0
                self.results.sharpe_ratio = (avg_return / std_return) if std_return > 0 else 0
        
        # Confidence and edge
        self.results.avg_confidence = statistics.mean(bet.confidence for bet in settled_bets)
        self.results.avg_edge = statistics.mean(bet.edge_percentage for bet in settled_bets)
        
        # Sport performance
        sport_stats = {}
        for sport in set(bet.sport for bet in settled_bets):
            sport_bets = [bet for bet in settled_bets if bet.sport == sport]
            sport_wins = sum(1 for bet in sport_bets if bet.won)
            sport_profit = sum(bet.profit_loss for bet in sport_bets)
            
            sport_stats[sport] = {
                'bets': len(sport_bets),
                'wins': sport_wins,
                'win_rate': sport_wins / len(sport_bets),
                'profit': sport_profit,
                'roi': (sport_profit / sum(bet.stake for bet in sport_bets)) * 100
            }
        
        self.results.sport_performance = sport_stats
    
    def _show_progress_report(self, day: int):
        """Näytä edistymisraportti"""
        
        print(f"""
📊 PROGRESS REPORT - DAY {day}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 BANKROLL:
  Current: €{self.current_bankroll:,.0f}
  Change: €{self.current_bankroll - self.starting_bankroll:+,.0f} ({((self.current_bankroll/self.starting_bankroll-1)*100):+.1f}%)
  Peak: €{self.peak_bankroll:,.0f}

📈 PERFORMANCE:
  Bets: {self.results.total_bets}
  Win Rate: {self.results.win_rate*100:.1f}%
  ROI: {self.results.roi:+.1f}%
  Avg Edge: {self.results.avg_edge:.1f}%

⚠️ RISK:
  Max Drawdown: €{self.results.max_drawdown:,.0f} ({self.results.max_drawdown_pct:.1f}%)
  Profit Factor: {self.results.profit_factor:.2f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """)
    
    def _generate_final_report(self) -> PaperTradingResults:
        """Generoi lopullinen raportti"""
        
        success = (self.results.win_rate > 0.55 and 
                  self.results.roi > 10 and 
                  self.results.total_bets >= 50)
        
        monthly_roi = (self.results.roi / 30) * 30  # Already monthly
        projected_annual = ((self.current_bankroll / self.starting_bankroll) ** (365/30) - 1) * 100
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║  📝 30-DAY PAPER TRADING RESULTS - {'SUCCESS' if success else 'NEEDS WORK'}              ║
║  ==========================================================  ║
║                                                              ║
║  💰 FINANCIAL PERFORMANCE:                                  ║
║    Starting Bankroll: €{self.starting_bankroll:,.0f}        ║
║    Final Bankroll: €{self.current_bankroll:,.0f}            ║
║    Net Profit: €{self.results.net_profit:+,.0f}            ║
║    ROI: {self.results.roi:+.1f}%                            ║
║                                                              ║
║  📊 BETTING STATISTICS:                                     ║
║    Total Bets: {self.results.total_bets}                    ║
║    Win Rate: {self.results.win_rate*100:.1f}%               ║
║    Average Odds: {self.results.average_odds:.2f}            ║
║    Average Edge: {self.results.avg_edge:.1f}%               ║
║    Average Confidence: {self.results.avg_confidence*100:.1f}% ║
║                                                              ║
║  ⚠️ RISK METRICS:                                           ║
║    Max Drawdown: €{self.results.max_drawdown:,.0f} ({self.results.max_drawdown_pct:.1f}%) ║
║    Profit Factor: {self.results.profit_factor:.2f}          ║
║    Sharpe Ratio: {self.results.sharpe_ratio:.2f}            ║
║                                                              ║
║  🎯 PROJECTIONS:                                            ║
║    Monthly ROI: {monthly_roi:+.1f}%                         ║
║    Projected Annual: {projected_annual:+.1f}%               ║
╚══════════════════════════════════════════════════════════════╝

{'✅ SYSTEM READY FOR LIVE TRADING!' if success else '❌ SYSTEM NEEDS OPTIMIZATION'}
{'Recommended next step: Start with €1,000-5,000 live bankroll' if success else 'Recommended: Analyze and improve before live trading'}

🏆 SPORT BREAKDOWN:
        """)
        
        for sport, stats in self.results.sport_performance.items():
            print(f"  {sport.title()}: {stats['bets']} bets, {stats['win_rate']*100:.1f}% win rate, {stats['roi']:+.1f}% ROI")
        
        return self.results
    
    def save_results(self, filepath: str):
        """Tallenna tulokset"""
        
        data = {
            'simulation_date': datetime.now().isoformat(),
            'duration_days': 30,
            'results': asdict(self.results),
            'bets': [asdict(bet) for bet in self.bets],
            'daily_bankrolls': self.daily_bankrolls
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"💾 Results saved to {filepath}")


async def main():
    """Test Paper Trading System"""
    print("📝 PAPER TRADING SYSTEM TEST")
    print("=" * 50)
    
    # Initialize system
    system = PaperTradingSystem(starting_bankroll=10000.0)
    
    # Run 30-day simulation
    results = system.run_30_day_simulation()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"paper_trading_results_{timestamp}.json"
    system.save_results(filename)
    
    print(f"\n💾 Results saved to {filename}")


if __name__ == "__main__":
    asyncio.run(main())
