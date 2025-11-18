#!/usr/bin/env python3
"""
📊 SMART VALUE DETECTOR - BACKTESTING SYSTEM
===========================================

Testaa Smart Value Detector -järjestelmää historiallisella datalla
ja validoi ROI-ennusteet.

Author: TennisBot Advanced Analytics
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json
import logging
from pathlib import Path

from src.smart_value_detector import (
    SmartValueDetector, MatchData, PlayerStats, ValueTrade
)

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Backtest-tulokset"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_stake: float
    total_profit: float
    total_loss: float
    net_profit: float
    roi_percentage: float
    average_edge: float
    sharpe_ratio: float
    max_drawdown: float
    profit_factor: float
    start_date: str
    end_date: str
    duration_days: int


class SVDBacktester:
    """
    Backtesting-järjestelmä Smart Value Detectorille
    """
    
    def __init__(self, initial_bankroll: float = 1000.0):
        """
        Initialize backtester
        
        Args:
            initial_bankroll: Alkupankkisaldo
        """
        self.initial_bankroll = initial_bankroll
        self.results: List[Dict] = []
        
        logger.info(f"📊 Backtester initialized with bankroll: €{initial_bankroll:,.2f}")
    
    def backtest(self, matches: List[MatchData], 
                actual_results: Dict[str, Dict],
                svd: SmartValueDetector) -> BacktestResult:
        """
        Suorita backtest
        
        Args:
            matches: Lista otteluita
            actual_results: Todelliset tulokset {match_id: {'winner': 'player1'/'player2'}}
            svd: SmartValueDetector instance
            
        Returns:
            BacktestResult
        """
        logger.info(f"🔄 Starting backtest with {len(matches)} matches")
        
        # Find value trades
        value_trades = svd.find_value_trades(matches)
        
        if not value_trades:
            logger.warning("⚠️ No value trades found")
            return self._empty_result()
        
        # Simulate trades
        bankroll = self.initial_bankroll
        trades_executed = []
        daily_profits = []
        
        for trade in value_trades:
            match_id = trade.match_id
            
            # Check if we have actual result
            if match_id not in actual_results:
                continue
            
            actual_result = actual_results[match_id]
            winner = actual_result.get('winner')
            
            # Determine if trade won
            trade_won = False
            if winner == 'player1' and trade.player_id == trade.match_id.split('_')[0]:
                trade_won = True
            elif winner == 'player2' and trade.player_id == trade.match_id.split('_')[1]:
                trade_won = True
            
            # Calculate profit/loss
            stake = trade.recommended_stake
            
            if trade_won:
                profit = stake * (trade.odds - 1)
                net_result = profit
            else:
                profit = -stake
                net_result = -stake
            
            # Update bankroll
            bankroll += net_result
            
            # Record trade
            trade_result = {
                'trade': asdict(trade),
                'actual_winner': winner,
                'trade_won': trade_won,
                'stake': stake,
                'profit': profit,
                'net_result': net_result,
                'bankroll_after': bankroll,
                'timestamp': trade.timestamp
            }
            
            trades_executed.append(trade_result)
            daily_profits.append(net_result)
        
        # Calculate metrics
        winning_trades = [t for t in trades_executed if t['trade_won']]
        losing_trades = [t for t in trades_executed if not t['trade_won']]
        
        total_stake = sum(t['stake'] for t in trades_executed)
        total_profit = sum(t['profit'] for t in winning_trades)
        total_loss = abs(sum(t['profit'] for t in losing_trades))
        net_profit = bankroll - self.initial_bankroll
        
        win_rate = len(winning_trades) / len(trades_executed) if trades_executed else 0
        roi_percentage = (net_profit / total_stake * 100) if total_stake > 0 else 0
        
        # Average edge
        avg_edge = np.mean([t['trade']['edge_percentage'] for t in trades_executed])
        
        # Sharpe ratio
        if daily_profits:
            sharpe = self._calculate_sharpe_ratio(daily_profits)
        else:
            sharpe = 0.0
        
        # Max drawdown
        max_drawdown = self._calculate_max_drawdown(trades_executed)
        
        # Profit factor
        profit_factor = total_profit / total_loss if total_loss > 0 else 0
        
        # Date range
        if trades_executed:
            start_date = min(t['timestamp'] for t in trades_executed)
            end_date = max(t['timestamp'] for t in trades_executed)
            duration = (datetime.fromisoformat(end_date) - datetime.fromisoformat(start_date)).days
        else:
            start_date = datetime.now().isoformat()
            end_date = datetime.now().isoformat()
            duration = 0
        
        result = BacktestResult(
            total_trades=len(trades_executed),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=win_rate,
            total_stake=total_stake,
            total_profit=total_profit,
            total_loss=total_loss,
            net_profit=net_profit,
            roi_percentage=roi_percentage,
            average_edge=avg_edge,
            sharpe_ratio=sharpe,
            max_drawdown=max_drawdown,
            profit_factor=profit_factor,
            start_date=start_date,
            end_date=end_date,
            duration_days=duration
        )
        
        self.results.append(asdict(result))
        
        logger.info(f"✅ Backtest completed: {len(trades_executed)} trades, ROI: {roi_percentage:.1f}%")
        
        return result
    
    def _calculate_sharpe_ratio(self, daily_returns: List[float]) -> float:
        """Calculate Sharpe ratio"""
        if not daily_returns or len(daily_returns) < 2:
            return 0.0
        
        returns = np.array(daily_returns)
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        # Annualized Sharpe (assuming daily returns)
        sharpe = (mean_return / std_return) * np.sqrt(252)
        
        return sharpe
    
    def _calculate_max_drawdown(self, trades: List[Dict]) -> float:
        """Calculate maximum drawdown"""
        if not trades:
            return 0.0
        
        bankroll_values = [t['bankroll_after'] for t in trades]
        
        peak = bankroll_values[0]
        max_dd = 0.0
        
        for value in bankroll_values:
            if value > peak:
                peak = value
            
            dd = (peak - value) / peak
            if dd > max_dd:
                max_dd = dd
        
        return max_dd * 100  # Percentage
    
    def _empty_result(self) -> BacktestResult:
        """Return empty result"""
        return BacktestResult(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            total_stake=0.0,
            total_profit=0.0,
            total_loss=0.0,
            net_profit=0.0,
            roi_percentage=0.0,
            average_edge=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            profit_factor=0.0,
            start_date=datetime.now().isoformat(),
            end_date=datetime.now().isoformat(),
            duration_days=0
        )
    
    def generate_report(self, result: BacktestResult) -> str:
        """Generate backtest report"""
        report = f"""
╔══════════════════════════════════════════════════════════╗
║  📊 SMART VALUE DETECTOR - BACKTEST RAPORTTI
╠══════════════════════════════════════════════════════════╣
║
║  📅 Aikajakso: {result.start_date[:10]} - {result.end_date[:10]}
║  ⏱️  Kesto: {result.duration_days} päivää
║
║  💰 TALOUDELLISET TULOKSET:
║  ├─ Alkupankkisaldo: €{self.initial_bankroll:,.2f}
║  ├─ Loppupankkisaldo: €{self.initial_bankroll + result.net_profit:,.2f}
║  ├─ Netto-voitto: €{result.net_profit:+,.2f}
║  ├─ ROI: {result.roi_percentage:+.1f}%
║  └─ Kokonaispanos: €{result.total_stake:,.2f}
║
║  📈 TRADE-TILASTOT:
║  ├─ Kaikki tradeja: {result.total_trades}
║  ├─ Voittavia: {result.winning_trades}
║  ├─ Häviäviä: {result.losing_trades}
║  ├─ Voittoprosentti: {result.win_rate*100:.1f}%
║  └─ Keskimääräinen edge: {result.average_edge:.1f}%
║
║  📊 RISKIMITTAUKSET:
║  ├─ Sharpe Ratio: {result.sharpe_ratio:.2f}
║  ├─ Max Drawdown: {result.max_drawdown:.1f}%
║  ├─ Profit Factor: {result.profit_factor:.2f}
║  ├─ Kokonaisvoitto: €{result.total_profit:,.2f}
║  └─ Kokonaistappio: €{result.total_loss:,.2f}
║
╚══════════════════════════════════════════════════════════╝
        """
        
        return report
    
    def project_future_performance(self, result: BacktestResult,
                                  months: int = 12) -> List[Dict]:
        """
        Ennusta tulevaa suorituskykyä backtest-tulosten perusteella
        """
        if result.total_trades == 0:
            return []
        
        # Calculate monthly metrics
        trades_per_month = result.total_trades / max(result.duration_days / 30, 1)
        monthly_roi = result.roi_percentage / max(result.duration_days / 30, 1)
        
        projections = []
        bankroll = self.initial_bankroll
        
        for month in range(1, months + 1):
            # Conservative projection (80% of backtest ROI)
            conservative_roi = monthly_roi * 0.8
            
            monthly_profit = bankroll * (conservative_roi / 100)
            bankroll_end = bankroll + monthly_profit
            
            projections.append({
                'month': month,
                'starting_balance': bankroll,
                'monthly_profit': monthly_profit,
                'ending_balance': bankroll_end,
                'cumulative_profit': bankroll_end - self.initial_bankroll,
                'roi_percentage': conservative_roi
            })
            
            bankroll = bankroll_end
        
        return projections
    
    def save_results(self, result: BacktestResult, filename: Optional[str] = None):
        """Save backtest results"""
        if filename is None:
            filename = f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data_dir = Path('data/backtests')
        data_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = data_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(asdict(result), f, indent=2, default=str)
        
        logger.info(f"💾 Saved backtest results to {filepath}")


if __name__ == "__main__":
    print("📊 SVD Backtester - Test")
    print("=" * 50)
    
    # Example usage would go here
    print("✅ Backtester ready for use")

