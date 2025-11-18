"""
Advanced Kelly Criterion with variance management
"""
import numpy as np
import logging

logger = logging.getLogger(__name__)


class KellyCriterion:
    """Advanced Kelly Criterion with variance management"""

    @staticmethod
    def calculate_optimal_kelly(edge_percent: float,
                               odds: float) -> float:
        """
        Traditional Kelly Criterion

        Formula: f* = (bp - q) / b
        where: b = odds - 1, p = win probability, q = 1 - p

        Or simplified: f* = (edge * (odds - 1)) / (odds - 1)
        """
        if odds <= 1:
            return 0.0
        
        edge_decimal = edge_percent / 100
        kelly = (edge_decimal * (odds - 1)) / (odds - 1)
        return max(0, kelly)

    @staticmethod
    def scale_kelly(kelly_percent: float,
                   scale_factor: float = 0.5) -> float:
        """
        Scaled Kelly for safety

        Common factors:
        - 1.0 = Full Kelly (aggressive)
        - 0.5 = Half Kelly (balanced) ← RECOMMENDED
        - 0.25 = Quarter Kelly (conservative)
        - 0.1 = Tenth Kelly (ultra-safe)
        """
        return kelly_percent * scale_factor

    @staticmethod
    def calculate_stake(bankroll: float,
                       kelly_percent: float,
                       max_percent_per_bet: float = 3.0) -> float:
        """
        Calculate actual stake in currency

        Args:
            bankroll: Total bankroll (€)
            kelly_percent: Kelly % (from calculate_optimal_kelly)
            max_percent_per_bet: Max % of bankroll per bet (risk limit)

        Returns:
            Stake in €
        """
        kelly_stake = (kelly_percent / 100) * bankroll
        max_stake = (max_percent_per_bet / 100) * bankroll

        # Use the LOWER of Kelly or max limit
        stake = min(kelly_stake, max_stake)

        return stake

    @staticmethod
    def calculate_variance_adjusted_kelly(edge_percent: float,
                                         odds: float,
                                         variance: float) -> float:
        """
        Adjust Kelly based on variance of outcomes

        High variance = lower Kelly (less confident)
        Low variance = higher Kelly (more confident)

        Args:
            variance: Historical variance of returns (0-1)
                      0.1 = low variance (steady)
                      0.5 = medium variance
                      0.9 = high variance (risky)
        """
        kelly_base = KellyCriterion.calculate_optimal_kelly(edge_percent, odds)

        # Variance adjustment (inverse relationship)
        variance_factor = 1 - (variance * 0.5)

        adjusted_kelly = kelly_base * variance_factor
        return max(0, adjusted_kelly)

    @staticmethod
    def drawdown_adjusted_kelly(kelly_percent: float,
                               current_drawdown_percent: float,
                               max_drawdown_tolerance: float = 15.0) -> float:
        """
        Reduce Kelly if drawdown is high

        Args:
            kelly_percent: Base Kelly %
            current_drawdown_percent: Current drawdown from peak (%)
            max_drawdown_tolerance: When to trigger (%)

        Returns:
            Adjusted Kelly % (lower if in drawdown)
        """
        if current_drawdown_percent > max_drawdown_tolerance * 0.75:
            # Serious drawdown - cut Kelly by 50%
            return kelly_percent * 0.5
        elif current_drawdown_percent > max_drawdown_tolerance * 0.5:
            # Moderate drawdown - cut Kelly by 25%
            return kelly_percent * 0.75
        else:
            return kelly_percent

    @staticmethod
    def betting_sequence_kelly(edge_percent: float,
                              odds: float,
                              past_results: list,
                              win_streak_length: int) -> float:
        """
        Adjust Kelly based on recent results (hot hand / cold hand)

        Args:
            past_results: [1, 1, 0, 1, 1, 1, 0, 0, 1] (1=win, 0=loss)
            win_streak_length: Current consecutive wins

        Returns:
            Adjusted Kelly (higher after wins, lower after losses)
        """
        kelly_base = KellyCriterion.calculate_optimal_kelly(edge_percent, odds)

        # Streak momentum
        if win_streak_length >= 3:
            # Winning streak - increase Kelly by 10% per win (up to +30%)
            streak_bonus = min(0.30, win_streak_length * 0.10)
            return kelly_base * (1 + streak_bonus)

        elif win_streak_length < -2:
            # Losing streak - reduce Kelly by 15% per loss
            streak_penalty = abs(win_streak_length) * 0.15
            return kelly_base * (1 - streak_penalty)

        else:
            return kelly_base

