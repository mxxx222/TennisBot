"""
Find best odds across multiple bookmakers and detect arbitrage
"""
import logging
from typing import Dict, List, Optional
from bookmakers.pinnacle_api import PinnacleAPI
from bookmakers.bet365_api import Bet365API
from bookmakers.mock_odds import MockOddsGenerator

logger = logging.getLogger(__name__)


class BookmakerOptimizer:
    """Find best odds across multiple bookmakers"""

    def __init__(self):
        self.bookmakers = {
            "Pinnacle": PinnacleAPI(),
            "Bet365": Bet365API(),
        }
        self.mock_generator = MockOddsGenerator()

    def get_best_odds(self, match_id: str, bet_type: str) -> Dict:
        """
        Compare odds across all bookmakers
        Return best odds + bookmaker name

        Args:
            match_id: Match identifier
            bet_type: Type of bet (1X2, OU2.5, BTTS, etc.)

        Returns:
            Dict with best_book, best_odds, all_odds, odds_difference_percent
        """
        odds_by_book = {}

        for book_name, api_client in self.bookmakers.items():
            try:
                odds = api_client.get_odds(match_id, bet_type)
                if odds:
                    odds_by_book[book_name] = odds
            except Exception as e:
                logger.error(f"Error fetching from {book_name}: {e}")
                continue

        if not odds_by_book:
            logger.warning(f"No odds available for match {match_id}")
            return {
                "best_book": None,
                "best_odds": None,
                "all_odds": {},
                "odds_difference_percent": 0
            }

        # Find best odds based on bet type
        if bet_type == "1X2":
            best_home = self._find_best_odds(odds_by_book, "home_odds")
            best_draw = self._find_best_odds(odds_by_book, "draw_odds")
            best_away = self._find_best_odds(odds_by_book, "away_odds")

            return {
                "best_book": best_home["book"],
                "best_odds": {
                    "home": best_home["odds"],
                    "draw": best_draw["odds"],
                    "away": best_away["odds"]
                },
                "all_odds": odds_by_book,
                "odds_difference_percent": self.calculate_odds_diff(odds_by_book, bet_type)
            }
        else:
            # For other bet types, find best single odds
            best = self._find_best_single_odds(odds_by_book, bet_type)
            return {
                "best_book": best["book"],
                "best_odds": best["odds"],
                "all_odds": odds_by_book,
                "odds_difference_percent": self.calculate_odds_diff(odds_by_book, bet_type)
            }

    def _find_best_odds(self, odds_by_book: Dict, odds_key: str) -> Dict:
        """Find best odds for a specific key (home_odds, away_odds, etc.)"""
        best_value = 0
        best_book = None

        for book_name, odds_data in odds_by_book.items():
            if odds_key in odds_data:
                if odds_data[odds_key] > best_value:
                    best_value = odds_data[odds_key]
                    best_book = book_name

        return {"book": best_book, "odds": best_value}

    def _find_best_single_odds(self, odds_by_book: Dict, bet_type: str) -> Dict:
        """Find best single odds value"""
        best_value = 0
        best_book = None

        for book_name, odds_data in odds_by_book.items():
            # Try common odds keys
            for key in ["odds", "over_odds", "under_odds", "yes_odds", "no_odds"]:
                if key in odds_data and odds_data[key] > best_value:
                    best_value = odds_data[key]
                    best_book = book_name

        return {"book": best_book, "odds": best_value}

    def calculate_odds_diff(self, odds_dict: Dict, bet_type: str) -> float:
        """Calculate max odds difference in %"""
        if not odds_dict or len(odds_dict) < 2:
            return 0.0

        if bet_type == "1X2":
            # Calculate difference for each outcome
            home_odds_list = [odds.get("home_odds", 0) for odds in odds_dict.values() if odds.get("home_odds")]
            away_odds_list = [odds.get("away_odds", 0) for odds in odds_dict.values() if odds.get("away_odds")]

            max_diff = 0
            for odds_list in [home_odds_list, away_odds_list]:
                if len(odds_list) >= 2:
                    min_odds = min(odds_list)
                    max_odds = max(odds_list)
                    if min_odds > 0:
                        diff_percent = ((max_odds - min_odds) / min_odds) * 100
                        max_diff = max(max_diff, diff_percent)

            return max_diff
        else:
            # For other bet types, compare single odds
            odds_list = []
            for odds_data in odds_dict.values():
                for key in ["odds", "over_odds", "under_odds", "yes_odds", "no_odds"]:
                    if key in odds_data:
                        odds_list.append(odds_data[key])
                        break

            if len(odds_list) < 2:
                return 0.0

            min_odds = min(odds_list)
            max_odds = max(odds_list)
            if min_odds > 0:
                diff_percent = ((max_odds - min_odds) / min_odds) * 100
                return diff_percent

        return 0.0

    def detect_arbitrage(self, matches: List[Dict]) -> List[Dict]:
        """
        Find arbitrage opportunities across bookmakers

        Arbitrage = 1/odds_a + 1/odds_b < 1

        Args:
            matches: List of match dicts with id, home_team, away_team

        Returns:
            List of arbitrage opportunities sorted by arbitrage_percent
        """
        arbs = []

        for match in matches:
            match_id = match.get("id") or match.get("match_id")
            if not match_id:
                continue

            for bet_type in ["1X2", "OU2.5", "BTTS"]:
                try:
                    odds_data = self.get_best_odds(match_id, bet_type)

                    if bet_type == "1X2":
                        # Check 2-way arbitrage (home vs away across books)
                        all_odds = odds_data.get("all_odds", {})
                        
                        pinnacle_odds = all_odds.get("Pinnacle", {})
                        bet365_odds = all_odds.get("Bet365", {})

                        if pinnacle_odds and bet365_odds:
                            # Check home vs away arbitrage
                            home_odds_pin = pinnacle_odds.get("home_odds")
                            away_odds_bet365 = bet365_odds.get("away_odds")

                            if home_odds_pin and away_odds_bet365:
                                arb_value = 1/home_odds_pin + 1/away_odds_bet365

                                if arb_value < 0.99:  # < 100% = arbitrage exists
                                    arb_percent = (1 - arb_value) * 100
                                    arbs.append({
                                        "match_id": match_id,
                                        "match_name": f"{match.get('home_team', 'Home')} vs {match.get('away_team', 'Away')}",
                                        "bet_type": bet_type,
                                        "book_a": "Pinnacle",
                                        "odds_a": home_odds_pin,
                                        "selection_a": "home",
                                        "book_b": "Bet365",
                                        "odds_b": away_odds_bet365,
                                        "selection_b": "away",
                                        "arbitrage_percent": arb_percent,
                                        "guaranteed_profit_percent": arb_percent
                                    })

                            # Check reverse arbitrage (away vs home)
                            away_odds_pin = pinnacle_odds.get("away_odds")
                            home_odds_bet365 = bet365_odds.get("home_odds")

                            if away_odds_pin and home_odds_bet365:
                                arb_value = 1/away_odds_pin + 1/home_odds_bet365

                                if arb_value < 0.99:
                                    arb_percent = (1 - arb_value) * 100
                                    arbs.append({
                                        "match_id": match_id,
                                        "match_name": f"{match.get('home_team', 'Home')} vs {match.get('away_team', 'Away')}",
                                        "bet_type": bet_type,
                                        "book_a": "Pinnacle",
                                        "odds_a": away_odds_pin,
                                        "selection_a": "away",
                                        "book_b": "Bet365",
                                        "odds_b": home_odds_bet365,
                                        "selection_b": "home",
                                        "arbitrage_percent": arb_percent,
                                        "guaranteed_profit_percent": arb_percent
                                    })

                    elif bet_type in ["OU2.5", "BTTS"]:
                        # Check over/under or yes/no arbitrage
                        all_odds = odds_data.get("all_odds", {})
                        pinnacle_odds = all_odds.get("Pinnacle", {})
                        bet365_odds = all_odds.get("Bet365", {})

                        if pinnacle_odds and bet365_odds:
                            over_key = "over_odds" if bet_type == "OU2.5" else "yes_odds"
                            under_key = "under_odds" if bet_type == "OU2.5" else "no_odds"

                            over_odds_pin = pinnacle_odds.get(over_key)
                            under_odds_bet365 = bet365_odds.get(under_key)

                            if over_odds_pin and under_odds_bet365:
                                arb_value = 1/over_odds_pin + 1/under_odds_bet365

                                if arb_value < 0.99:
                                    arb_percent = (1 - arb_value) * 100
                                    arbs.append({
                                        "match_id": match_id,
                                        "match_name": f"{match.get('home_team', 'Home')} vs {match.get('away_team', 'Away')}",
                                        "bet_type": bet_type,
                                        "book_a": "Pinnacle",
                                        "odds_a": over_odds_pin,
                                        "selection_a": "over" if bet_type == "OU2.5" else "yes",
                                        "book_b": "Bet365",
                                        "odds_b": under_odds_bet365,
                                        "selection_b": "under" if bet_type == "OU2.5" else "no",
                                        "arbitrage_percent": arb_percent,
                                        "guaranteed_profit_percent": arb_percent
                                    })

                except Exception as e:
                    logger.error(f"Error detecting arbitrage for {match_id}: {e}")
                    continue

        return sorted(arbs, key=lambda x: x["arbitrage_percent"], reverse=True)

    def calculate_arbitrage_stakes(self, total_stake: float, odds_a: float, odds_b: float) -> Dict:
        """
        Calculate optimal stake distribution for arbitrage

        Args:
            total_stake: Total amount to stake
            odds_a: Odds for book A
            odds_b: Odds for book B

        Returns:
            Dict with stake_a, stake_b, guaranteed_profit
        """
        stake_a = total_stake / odds_a
        stake_b = total_stake / odds_b
        total_staked = stake_a + stake_b
        guaranteed_profit = total_stake - total_staked

        return {
            "stake_a": round(stake_a, 2),
            "stake_b": round(stake_b, 2),
            "total_staked": round(total_staked, 2),
            "guaranteed_profit": round(guaranteed_profit, 2),
            "profit_percent": round((guaranteed_profit / total_stake) * 100, 2)
        }

