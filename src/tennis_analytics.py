import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

# Ensure project root is on the import path for `src.*` imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

try:
    from src.bet_calculator import BetCalculator
    from src.database_manager import DatabaseManager
except Exception as exc:  # pragma: no cover - fallback mainly for isolated tests
    logging.warning("Import warning in tennis_analytics: %s", exc)

    class BetCalculator:  # type: ignore[no-redef]
        @staticmethod
        def calculate_kelly_stake(
            bankroll: float,
            odds: float,
            win_probability: float,
            max_stake_percent: float = 0.05,
        ) -> float:
            # Conservative fallback: flat 2% stake
            return round(bankroll * 0.02, 2)

        @staticmethod
        def calculate_expected_value(
            odds: float, win_probability: float, stake: float
        ) -> float:
            return 0.0


logger = logging.getLogger(__name__)


class TennisAnalytics:
    """
    Tennis analytics utilities used to evaluate match value, especially ITF level.
    """

    def __init__(self) -> None:
        self.logger = logger
        self.calculator = BetCalculator()

    def calculate_serve_dominance(self, player_stats: Dict[str, Any]) -> float:
        """
        Calculate serve dominance score (0.0 to 1.0) based on ace rate and serve metrics.
        """
        try:
            ace_rate = float(player_stats.get("ace_percentage", 5.0))
            first_serve_in = float(player_stats.get("first_serve_percentage", 60.0))
            first_serve_won = float(player_stats.get("first_serve_won", 70.0))

            ace_score = min(ace_rate / 15.0, 1.0)  # 15% aces = max score
            serve_in_score = first_serve_in / 100.0
            serve_won_score = first_serve_won / 100.0

            serve_dominance = (
                ace_score * 0.3 + serve_in_score * 0.3 + serve_won_score * 0.4
            )
            return round(min(1.0, max(0.0, serve_dominance)), 3)
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Error calculating serve dominance: %s", exc)
            return 0.5

    def analyze_surface_advantage(
        self,
        player1_stats: Dict[str, Any],
        player2_stats: Dict[str, Any],
        surface: str,
    ) -> Tuple[float, float]:
        """
        Analyze surface-specific advantages for two players.
        """
        try:
            surface_multipliers = {
                "hard": {"baseline": 1.0, "serve": 1.1, "net": 0.9},
                "clay": {"baseline": 1.3, "serve": 0.8, "net": 0.7},
                "grass": {"baseline": 0.8, "serve": 1.4, "net": 1.2},
                "indoor": {"baseline": 0.9, "serve": 1.2, "net": 1.0},
            }

            multiplier = surface_multipliers.get(
                surface.lower(), surface_multipliers["hard"]
            )

            def calculate_surface_rating(stats: Dict[str, Any]) -> float:
                baseline = float(stats.get("baseline_rating", 0.5))
                serve = float(stats.get("serve_rating", 0.5))
                net = float(stats.get("net_rating", 0.5))

                adjusted_rating = (
                    baseline * multiplier["baseline"]
                    + serve * multiplier["serve"]
                    + net * multiplier["net"]
                ) / 3.0

                return min(1.0, max(0.0, adjusted_rating))

            p1_surface = calculate_surface_rating(player1_stats)
            p2_surface = calculate_surface_rating(player2_stats)

            return p1_surface, p2_surface
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Error analyzing surface advantage: %s", exc)
            return 0.5, 0.5

    def calculate_form_momentum(
        self, recent_matches: List[Dict[str, Any]], weight_recent: bool = True
    ) -> float:
        """
        Calculate player form and momentum based on recent matches.
        """
        try:
            if not recent_matches:
                return 0.5

            total_weight = 0.0
            weighted_score = 0.0

            for i, match in enumerate(recent_matches[:10]):
                weight = 1.0 if not weight_recent else (10 - i) / 10.0

                if match.get("result") == "won":
                    match_score = 1.0
                    opponent_ranking = int(match.get("opponent_ranking", 100))
                    if opponent_ranking <= 20:
                        match_score = 1.4
                    elif opponent_ranking <= 50:
                        match_score = 1.2
                else:
                    match_score = 0.0

                weighted_score += match_score * weight
                total_weight += weight

            form_score = weighted_score / total_weight if total_weight > 0 else 0.5
            return round(min(1.0, max(0.0, form_score)), 3)
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Error calculating form momentum: %s", exc)
            return 0.5

    def analyze_head_to_head(
        self, h2h_matches: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze head-to-head matchup statistics.
        """
        try:
            if not h2h_matches:
                return {
                    "total_matches": 0,
                    "player1_wins": 0,
                    "player2_wins": 0,
                    "player1_win_rate": 0.5,
                    "recent_form_advantage": 0.0,
                    "surface_h2h": {},
                }

            total_matches = len(h2h_matches)
            player1_wins = sum(
                1 for match in h2h_matches if match.get("winner") == "player1"
            )
            player2_wins = total_matches - player1_wins

            recent_matches = h2h_matches[:3]
            recent_p1_wins = sum(
                1 for match in recent_matches if match.get("winner") == "player1"
            )
            recent_form_advantage = (
                (recent_p1_wins / len(recent_matches)) - 0.5 if recent_matches else 0.0
            )

            surface_h2h: Dict[str, Dict[str, int]] = {}
            for match in h2h_matches:
                surface = match.get("surface", "hard")
                if surface not in surface_h2h:
                    surface_h2h[surface] = {"player1": 0, "player2": 0}

                if match.get("winner") == "player1":
                    surface_h2h[surface]["player1"] += 1
                else:
                    surface_h2h[surface]["player2"] += 1

            return {
                "total_matches": total_matches,
                "player1_wins": player1_wins,
                "player2_wins": player2_wins,
                "player1_win_rate": player1_wins / total_matches,
                "recent_form_advantage": recent_form_advantage,
                "surface_h2h": surface_h2h,
            }
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Error analyzing H2H: %s", exc)
            return {
                "total_matches": 0,
                "player1_win_rate": 0.5,
                "recent_form_advantage": 0.0,
            }

    def calculate_itf_value(
        self, match_data: Dict[str, Any], bankroll: float = 1000.0
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate ITF betting value using original proven logic.

        Focus on odds range 1.30-1.80 for consistent profits.
        """
        try:
            odds_p1 = float(match_data.get("odds_player1", 0.0))
            odds_p2 = float(match_data.get("odds_player2", 0.0))

            # ITF filter: focus on 1.30–1.80 odds range
            if not (1.30 <= odds_p1 <= 1.80 or 1.30 <= odds_p2 <= 1.80):
                return None

            if 1.30 <= odds_p1 <= 1.80:
                target_odds = odds_p1
                target_player = "player1"
                implied_prob = 1.0 / target_odds
            elif 1.30 <= odds_p2 <= 1.80:
                target_odds = odds_p2
                target_player = "player2"
                implied_prob = 1.0 / target_odds
            else:
                return None

            player1_stats = match_data.get("player1_stats", {}) or {}
            player2_stats = match_data.get("player2_stats", {}) or {}
            surface = match_data.get("surface", "hard")

            # Surface advantage
            p1_surface, p2_surface = self.analyze_surface_advantage(
                player1_stats, player2_stats, surface
            )

            # Form momentum
            p1_form = self.calculate_form_momentum(
                player1_stats.get("recent_matches", [])
            )
            p2_form = self.calculate_form_momentum(
                player2_stats.get("recent_matches", [])
            )

            # Serve dominance
            p1_serve = self.calculate_serve_dominance(player1_stats)
            p2_serve = self.calculate_serve_dominance(player2_stats)

            p1_total = (p1_surface + p1_form + p1_serve) / 3.0
            p2_total = (p2_surface + p2_form + p2_serve) / 3.0

            total_score = p1_total + p2_total
            if total_score > 0:
                true_p1_prob = p1_total / total_score
                true_p2_prob = p2_total / total_score
            else:
                true_p1_prob = true_p2_prob = 0.5

            true_prob = true_p1_prob if target_player == "player1" else true_p2_prob
            edge = true_prob - implied_prob

            # Require at least 5% edge
            if edge < 0.05:
                return None

            kelly_stake = self.calculator.calculate_kelly_stake(
                bankroll=bankroll,
                odds=target_odds,
                win_probability=true_prob,
                max_stake_percent=0.03,
            )

            expected_value = self.calculator.calculate_expected_value(
                odds=target_odds, win_probability=true_prob, stake=kelly_stake
            )

            confidence = min(0.95, max(0.6, true_prob))

            return {
                "recommended_bet": target_player,
                "odds": target_odds,
                "true_probability": round(true_prob, 3),
                "implied_probability": round(implied_prob, 3),
                "edge_percentage": round(edge * 100.0, 2),
                "kelly_stake": kelly_stake,
                "expected_value": expected_value,
                "confidence": confidence,
                "reasoning": {
                    "surface_advantage": (
                        f"{target_player} surface rating: "
                        f"{p1_surface if target_player == 'player1' else p2_surface}"
                    ),
                    "form_momentum": (
                        f"{target_player} form score: "
                        f"{p1_form if target_player == 'player1' else p2_form}"
                    ),
                    "serve_dominance": (
                        f"{target_player} serve score: "
                        f"{p1_serve if target_player == 'player1' else p2_serve}"
                    ),
                    "itf_filter": (
                        f"Odds {target_odds} in optimal range 1.30-1.80"
                    ),
                },
            }
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Error calculating ITF value: %s", exc)
            return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    analytics = TennisAnalytics()

    test_match = {
        "odds_player1": 1.65,
        "odds_player2": 2.25,
        "surface": "hard",
        "player1_stats": {
            "baseline_rating": 0.7,
            "serve_rating": 0.8,
            "recent_matches": [{"result": "won", "opponent_ranking": 45}],
        },
        "player2_stats": {
            "baseline_rating": 0.6,
            "serve_rating": 0.6,
            "recent_matches": [{"result": "lost", "opponent_ranking": 30}],
        },
    }

    result = analytics.calculate_itf_value(test_match)
    print(f"✅ Tennis analytics test: {result is not None}")


