#!/usr/bin/env python3
"""
Sportbex API Client - Simple Synchronous Version
================================================

Simple synchronous wrapper for Sportbex API calls.
Used by Stage 1 scanner for basic match scanning.
"""

import os
import requests
import time
from typing import List, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / 'telegram_secrets.env'
if env_path.exists():
    load_dotenv(env_path)

class SportbexClient:
    """Simple synchronous Sportbex API client"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Sportbex API client
        
        Args:
            api_key: Sportbex API key (defaults to env var SPORTBEX_API_KEY)
        """
        self.api_key = api_key or os.getenv('SPORTBEX_API_KEY', 'Fbmm5Xt57NzVjdKdGwPIQY7EXKOmYAt2MfFWXVCb')
        self.base_url = 'https://trial-api.sportbex.com/api/v1'
        self.headers = {'sportbex-api-key': self.api_key}
        self.last_request_time = 0.0
        self.min_request_delay = 0.2  # 200ms between requests
    
    def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_delay:
            time.sleep(self.min_request_delay - elapsed)
        self.last_request_time = time.time()
    
    def _request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make API request with rate limiting"""
        self._rate_limit()
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ API Error: {e}")
            return {}
    
    def get_tennis_sport_id(self) -> str:
        """Get tennis sport ID"""
        data = self._request('sports')
        sports = data.get('sports', [])
        for sport in sports:
            if sport.get('name', '').lower() == 'tennis':
                return sport.get('id')
        return '2'  # Default
    
    def get_tennis_competitions(self) -> List[Dict]:
        """Get tennis competitions"""
        sport_id = self.get_tennis_sport_id()
        data = self._request('competitions', {'sportId': sport_id})
        return data.get('competitions', [])
    
    def get_events(self, competition_id: str) -> List[Dict]:
        """Get events for competition"""
        data = self._request(f'events/{competition_id}')
        return data if isinstance(data, list) else []

