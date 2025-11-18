"""
Pinnacle API client
"""
import requests
import time
from typing import Dict, Optional
import logging
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import PINNACLE_API_KEY, PINNACLE_USERNAME, PINNACLE_PASSWORD, USE_MOCK_APIS, API_RATE_LIMIT_DELAY
from .mock_odds import MockOddsGenerator

logger = logging.getLogger(__name__)


class PinnacleAPI:
    """Pinnacle Sports API client"""

    def __init__(self):
        self.api_key = PINNACLE_API_KEY
        self.username = PINNACLE_USERNAME
        self.password = PINNACLE_PASSWORD
        self.base_url = "https://api.pinnacle.com/v2"
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
        Fetch odds from Pinnacle
        
        Args:
            match_id: Match identifier
            bet_type: Type of bet (1X2, OU2.5, BTTS, etc.)
        
        Returns:
            Dict with odds data or None if error
        """
        if self.use_mock:
            logger.info(f"Using mock odds for match {match_id}")
            return self.mock_generator.generate_match_odds(match_id, "Home", "Away", bet_type)

        self._rate_limit()

        try:
            url = f"{self.base_url}/odds"
            headers = {
                "Authorization": f"Basic {self.api_key}",
                "Content-Type": "application/json"
            }
            params = {
                "matchId": match_id,
                "betType": bet_type
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            return self._parse_pinnacle_response(data, bet_type)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Pinnacle odds: {e}")
            # Fallback to mock
            logger.info("Falling back to mock odds")
            return self.mock_generator.generate_match_odds(match_id, "Home", "Away", bet_type)

    def _parse_pinnacle_response(self, data: Dict, bet_type: str) -> Dict:
        """Parse Pinnacle API response"""
        # This is a simplified parser - actual implementation depends on Pinnacle API structure
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
            logger.error(f"Error parsing Pinnacle response: {e}")
            return {}

    def place_bet(self, match_id: str, bet_type: str, selection: str, stake: float) -> Dict:
        """
        Place a bet on Pinnacle (mock implementation)
        
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
                "bet_id": f"PINNACLE_{match_id}_{int(time.time())}",
                "stake": stake,
                "status": "pending"
            }

        # Real implementation would call Pinnacle betting API
        logger.warning("Real bet placement not implemented - use mock mode")
        return {
            "success": False,
            "error": "Real API not implemented"
        }

