"""
Backtest strategies on historical data
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime
import logging
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from edge_detection import EdgeDetectionEngine
from kelly_criterion import KellyCriterion

logger = logging.getLogger(__name__)


class Backtester:
    """Backtest strategies on historical data"""

    def __init__(self, historical_data: pd.DataFrame):
        """
        Initialize backtester
        
        Args:
            historical_data: DataFrame with historical match data
        """
        self.data = historical_data
        self.edge_engine = EdgeDetectionEngine(historical_data)
        self.kelly = KellyCriterion()

    def backtest_strategy(self, 
                         strategy: Dict, 
                         start_date: str, 
                         end_date: str,
                         initial_bankroll: float = 5000) -> Dict:
        """
        Backtest single strategy

        Args:
            strategy: Dict with strategy configuration:
                {
                    'name': 'Strategy Name',
                    'criteria': {
                        'min_edge': 4.0,
                        'min_confidence': 6,
                        'max_odds': 3.0
                    }
                }
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            initial_bankroll: Starting bankroll

        Returns:
            Dict with backtest results
        """
        # Filter data for period
        df = self.data.copy()
        
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        else:
            logger.warning("No 'date' column found. Using all data.")

        results = []
        bankroll = initial_bankroll
        peak_bankroll = initial_bankroll
        total_stake = 0
        total_profit = 0

        for idx, row in df.iterrows():
            # Apply strategy criteria
            if not self._matches_criteria(row, strategy.get('criteria', {})):
                continue

            # Calculate edge & Kelly
            my_prob = row.get('my_probability', row.get('true_probability', 0.5))
            market_prob = row.get('market_probability', row.get('implied_probability', 0.5))
            
            if market_prob == 0:
                continue

            edge = self.edge_engine.calculate_base_edge(my_prob, market_prob)
            
            if edge < strategy.get('criteria', {}).get('min_edge', 0):
                continue

            odds = row.get('odds', 2.0)
            kelly_base = self.kelly.calculate_optimal_kelly(edge, odds)
            kelly_scaled = self.kelly.scale_kelly(kelly_base, 0.5)  # 50% scaled Kelly
            
            stake = self.kelly.calculate_stake(
                bankroll, 
                kelly_scaled * 100, 
                strategy.get('criteria', {}).get('max_stake_percent', 3.0)
            )

            if stake <= 0:
                continue

            # Simulate outcome
            won = row.get('result', 0) == 1
            profit_loss = stake * (odds - 1) if won else -stake
            bankroll += profit_loss
            peak_bankroll = max(peak_bankroll, bankroll)
            total_stake += stake
            total_profit += profit_loss

            results.append({
                'date': row.get('date', datetime.now()),
                'match_id': row.get('match_id', idx),
                'stake': stake,
                'odds': odds,
                'edge': edge,
                'won': won,
                'profit_loss': profit_loss,
                'bankroll': bankroll,
                'roi_percent': (profit_loss / stake) * 100 if stake > 0 else 0
            })

        # Calculate statistics
        if not results:
            return {
                'strategy': strategy.get('name', 'Unknown'),
                'period': f"{start_date} to {end_date}",
                'total_bets': 0,
                'error': 'No bets matched criteria'
            }

        df_results = pd.DataFrame(results)

        total_roi = (total_profit / total_stake) * 100 if total_stake > 0 else 0

        wins = df_results['won'].sum()
        losses = len(df_results) - wins
        win_rate = (wins / len(df_results)) * 100 if len(df_results) > 0 else 0

        max_drawdown = self._calculate_max_drawdown(df_results['bankroll'].tolist())
        sharpe_ratio = self._calculate_sharpe_ratio(df_results['roi_percent'].tolist())
        
        winning_bets = df_results[df_results['profit_loss'] > 0]['profit_loss'].sum()
        losing_bets = abs(df_results[df_results['profit_loss'] < 0]['profit_loss'].sum())
        profit_factor = winning_bets / losing_bets if losing_bets > 0 else 0

        days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days
        monthly_roi = (total_roi / days * 30) if days > 0 else 0

        return {
            'strategy': strategy.get('name', 'Unknown'),
            'period': f"{start_date} to {end_date}",
            'total_bets': len(df_results),
            'wins': int(wins),
            'losses': int(losses),
            'win_rate': round(win_rate, 2),
            'total_roi_percent': round(total_roi, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'max_drawdown_percent': round(max_drawdown, 2),
            'profit_factor': round(profit_factor, 2),
            'monthly_roi_projected': round(monthly_roi, 2),
            'final_bankroll': round(bankroll, 2),
            'total_profit': round(total_profit, 2),
            'total_stake': round(total_stake, 2),
            'details': df_results.to_dict('records')
        }

    def _matches_criteria(self, row: pd.Series, criteria: Dict) -> bool:
        """Check if row matches strategy criteria"""
        for key, value in criteria.items():
            if key not in row:
                continue

            if isinstance(value, dict):
                if value.get('gt') and row[key] <= value['gt']:
                    return False
                if value.get('lt') and row[key] >= value['lt']:
                    return False
                if value.get('eq') and row[key] != value['eq']:
                    return False
            else:
                if row[key] != value:
                    return False

        return True

    def _calculate_max_drawdown(self, bankroll_history: List[float]) -> float:
        """Calculate maximum drawdown %"""
        if not bankroll_history:
            return 0.0

        peak = bankroll_history[0]
        max_dd = 0.0

        for value in bankroll_history:
            if value > peak:
                peak = value
            dd = ((peak - value) / peak) * 100
            max_dd = max(max_dd, dd)

        return max_dd

    def _calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 2.0) -> float:
        """Calculate Sharpe ratio (risk-adjusted returns)"""
        if not returns or len(returns) < 2:
            return 0.0

        mean_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return 0.0

        # Annualized Sharpe ratio
        sharpe = ((mean_return - risk_free_rate) / std_return) * np.sqrt(252)
        return sharpe

    def compare_strategies(self, 
                          strategies: List[Dict], 
                          start_date: str, 
                          end_date: str) -> pd.DataFrame:
        """
        Compare multiple strategies
        
        Args:
            strategies: List of strategy dicts
            start_date: Start date
            end_date: End date
        
        Returns:
            DataFrame with comparison results
        """
        results = []
        
        for strategy in strategies:
            result = self.backtest_strategy(strategy, start_date, end_date)
            if 'error' not in result:
                results.append({
                    'Strategy': result['strategy'],
                    'Total Bets': result['total_bets'],
                    'Win Rate %': result['win_rate'],
                    'ROI %': result['total_roi_percent'],
                    'Sharpe Ratio': result['sharpe_ratio'],
                    'Max Drawdown %': result['max_drawdown_percent'],
                    'Profit Factor': result['profit_factor'],
                    'Monthly ROI %': result['monthly_roi_projected']
                })
        
        return pd.DataFrame(results)

