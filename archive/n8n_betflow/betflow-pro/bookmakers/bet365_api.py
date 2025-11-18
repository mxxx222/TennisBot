"""
Bet365 API client
"""
import requests
import time
from typing import Dict, Optional
import logging
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import BET365_API_KEY, USE_MOCK_APIS, API_RATE_LIMIT_DELAY
from .mock_odds import MockOddsGenerator

logger = logging.getLogger(__name__)


class Bet365API:
    """Bet365 API client"""

    def __init__(self):
        self.api_key = BET365_API_KEY
        self.base_url = "https://api.bet365.com/v1"
        self.use_mock = USE_MOCK_APIS or not self.api_key
        self.mock_generator = MockOddsGenerator()
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < API_RATE_LIMIT_DELAY:
            time.sleep(API_RATE_LIMIT_DELAY - time_since_last)
        self.last_request_time = time.time()

    def get_odds(self, match_id: str, bet_type: str = "1X2") -> Optional[Dict]:
        """
        Fetch odds from Bet365
        
        Args:
            match_id: Match identifier
            bet_type: Type of bet (1X2, OU2.5, BTTS, etc.)
        
        Returns:
            Dict with odds data or None if error
        """
        if self.use_mock:
            logger.info(f"Using mock odds for match {match_id}")
            # Bet365 typically has slightly lower odds than Pinnacle
            mock_odds = self.mock_generator.generate_match_odds(match_id, "Home", "Away", bet_type)
            if "home_odds" in mock_odds:
                mock_odds["home_odds"] = round(mock_odds["home_odds"] * 0.98, 2)
                mock_odds["away_odds"] = round(mock_odds["away_odds"] * 0.98, 2)
                if "draw_odds" in mock_odds:
                    mock_odds["draw_odds"] = round(mock_odds["draw_odds"] * 0.98, 2)
            return mock_odds

        self._rate_limit()

        try:
            url = f"{self.base_url}/odds"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            params = {
                "matchId": match_id,
                "betType": bet_type
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            return self._parse_bet365_response(data, bet_type)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Bet365 odds: {e}")
            # Fallback to mock
            logger.info("Falling back to mock odds")
            mock_odds = self.mock_generator.generate_match_odds(match_id, "Home", "Away", bet_type)
            if "home_odds" in mock_odds:
                mock_odds["home_odds"] = round(mock_odds["home_odds"] * 0.98, 2)
                mock_odds["away_odds"] = round(mock_odds["away_odds"] * 0.98, 2)
            return mock_odds

    def _parse_bet365_response(self, data: Dict, bet_type: str) -> Dict:
        """Parse Bet365 API response"""
        # This is a simplified parser - actual implementation depends on Bet365 API structure
        try:
            if bet_type == "1X2":
                return {
                    "match_id": data.get("matchId", ""),
                    "bet_type": bet_type,
                    "home_odds": data.get("homeOdds", 0),
                    "draw_odds": data.get("drawOdds", 0),
                    "away_odds": data.get("awayOdds", 0),
                    "timestamp": data.get("timestamp", "")
                }
            else:
                return {
                    "match_id": data.get("matchId", ""),
                    "bet_type": bet_type,
                    "odds": data.get("odds", 0),
                    "timestamp": data.get("timestamp", "")
                }
        except Exception as e:
            logger.error(f"Error parsing Bet365 response: {e}")
            return {}

    def place_bet(self, match_id: str, bet_type: str, selection: str, stake: float) -> Dict:
        """
        Place a bet on Bet365 (mock implementation)
        
        Args:
            match_id: Match identifier
            bet_type: Type of bet
            selection: Selection (e.g., "home", "away", "over")
            stake: Stake amount
        
        Returns:
            Bet confirmation dict
        """
        if self.use_mock:
            logger.info(f"Mock bet placed: {match_id} - {bet_type} - {selection} - €{stake}")
            return {
                "success": True,
                "bet_id": f"BET365_{match_id}_{int(time.time())}",
                "stake": stake,
                "status": "pending"
            }

        # Real implementation would call Bet365 betting API
        logger.warning("Real bet placement not implemented - use mock mode")
        return {
            "success": False,
            "error": "Real API not implemented"
        }

