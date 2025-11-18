import logging
from typing import Optional


logger = logging.getLogger(__name__)


class BetCalculator:
    """
    Utility class for value betting calculations (Kelly, EV, ROI).
    """

    def __init__(self) -> None:
        self.logger = logger

    @staticmethod
    def calculate_kelly_stake(
        bankroll: float,
        odds: float,
        win_probability: float,
        max_stake_percent: float = 0.05,
    ) -> float:
        """
        Calculate Kelly Criterion stake size.

        Args:
            bankroll: Total available bankroll.
            odds: Decimal odds (e.g., 2.0 for evens).
            win_probability: Probability of winning (0.0 to 1.0).
            max_stake_percent: Maximum stake as percentage of bankroll.

        Returns:
            Recommended stake amount in currency units.
        """
        try:
            if win_probability <= 0 or odds <= 1.0 or bankroll <= 0:
                return 0.0

            # Kelly formula: (bp - q) / b, where b = odds - 1, p = win_probability, q = 1 - p
            b = odds - 1.0
            p = win_probability
            q = 1.0 - p

            if b <= 0:
                return 0.0

            kelly_fraction = (b * p - q) / b

            # Apply safety limits
            kelly_fraction = max(0.0, min(kelly_fraction, max_stake_percent))

            stake_amount = bankroll * kelly_fraction
            return round(stake_amount, 2)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Kelly calculation error: %s", exc)
            return 0.0

    @staticmethod
    def calculate_expected_value(
        odds: float, win_probability: float, stake: float
    ) -> float:
        """
        Calculate expected value of a bet.
        """
        try:
            if win_probability <= 0 or odds <= 1.0 or stake <= 0:
                return 0.0

            expected_return = win_probability * (odds * stake)
            expected_cost = stake
            expected_value = expected_return - expected_cost

            return round(expected_value, 2)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("EV calculation error: %s", exc)
            return 0.0

    @staticmethod
    def calculate_roi_percentage(profit: float, stake: float) -> float:
        """
        Calculate ROI as percentage.
        """
        try:
            if stake <= 0:
                return 0.0
            return round((profit / stake) * 100.0, 2)
        except Exception:  # pragma: no cover - defensive
            return 0.0
    
    @staticmethod
    def calculate_stake(odds: float, edge: float, bankroll: float) -> float:
        """
        Calculate stake based on odds, edge, and bankroll.
        
        Args:
            odds: Decimal odds (e.g., 1.65)
            edge: Edge percentage as decimal (e.g., 0.05 for 5%)
            bankroll: Total bankroll
            
        Returns:
            Recommended stake amount
        """
        try:
            if odds <= 1.0 or edge <= 0 or bankroll <= 0:
                return 0.0
            
            # Convert edge to win probability
            implied_prob = 1.0 / odds
            win_probability = implied_prob + edge
            
            # Use Kelly calculation
            return BetCalculator.calculate_kelly_stake(
                bankroll=bankroll,
                odds=odds,
                win_probability=win_probability,
                max_stake_percent=0.05
            )
        except Exception as exc:
            logger.error("Stake calculation error: %s", exc)
            return 0.0


