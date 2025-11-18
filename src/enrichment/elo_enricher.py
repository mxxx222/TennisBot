#!/usr/bin/env python3
"""
📊 ELO RATINGS ENRICHER
=======================

Enriches player data with ELO ratings.
Sources: Tennis Abstract API (if available) or calculation from match history.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


@dataclass
class PlayerELO:
    """Player ELO ratings"""
    player_name: str
    overall_elo: float = 1500.0
    hard_elo: float = 1500.0
    clay_elo: float = 1500.0
    grass_elo: float = 1500.0
    career_high_elo: float = 1500.0
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = datetime.now()


class ELOEnricher:
    """
    ELO ratings enricher
    
    Supports:
    - Tennis Abstract API (if available)
    - Calculation from match history (fallback)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize ELO enricher
        
        Args:
            config: Configuration dict with API keys, etc.
        """
        self.config = config or {}
        self.api_key = self.config.get('tennis_abstract_api_key')
        self.api_available = False
        
        # ELO calculation parameters
        self.k_factor = self.config.get('k_factor', 32)  # Standard K=32
        self.initial_elo = self.config.get('initial_elo', 1500.0)
        
        # Cache
        self.elo_cache: Dict[str, PlayerELO] = {}
        
        # Try to initialize API
        self._init_api()
        
        logger.info("📊 ELO Enricher initialized")
    
    def _init_api(self):
        """Initialize Tennis Abstract API if available"""
        if not self.api_key:
            logger.info("ℹ️ Tennis Abstract API key not provided, will use calculation method")
            return
        
        try:
            # Test API connection
            # Note: Tennis Abstract API structure may vary
            # This is a placeholder for actual API integration
            self.api_available = True
            logger.info("✅ Tennis Abstract API initialized")
        except Exception as e:
            logger.warning(f"⚠️ Tennis Abstract API not available: {e}, using calculation method")
            self.api_available = False
    
    def get_elo(self, player_name: str, surface: Optional[str] = None) -> Optional[PlayerELO]:
        """
        Get ELO rating for a player
        
        Args:
            player_name: Player name
            surface: Optional surface filter ('hard', 'clay', 'grass')
            
        Returns:
            PlayerELO object or None
        """
        # Check cache first
        cache_key = f"{player_name}_{surface or 'overall'}"
        if cache_key in self.elo_cache:
            return self.elo_cache[cache_key]
        
        # Try API first
        if self.api_available:
            elo = self._fetch_from_api(player_name, surface)
            if elo:
                self.elo_cache[cache_key] = elo
                return elo
        
        # Fallback to calculation
        elo = self._calculate_elo(player_name, surface)
        if elo:
            self.elo_cache[cache_key] = elo
        
        return elo
    
    def _fetch_from_api(self, player_name: str, surface: Optional[str] = None) -> Optional[PlayerELO]:
        """
        Fetch ELO from Tennis Abstract API
        
        Args:
            player_name: Player name
            surface: Optional surface filter
            
        Returns:
            PlayerELO object or None
        """
        # Placeholder for actual API integration
        # Tennis Abstract API structure needs to be determined
        logger.debug(f"📡 Fetching ELO from API for {player_name}")
        
        try:
            # Example API call structure (needs actual implementation)
            # response = requests.get(
            #     f"https://api.tennisabstract.com/player/{player_name}/elo",
            #     headers={"Authorization": f"Bearer {self.api_key}"}
            # )
            # data = response.json()
            
            # For now, return None to trigger calculation
            return None
            
        except Exception as e:
            logger.error(f"❌ Error fetching ELO from API: {e}")
            return None
    
    def _calculate_elo(self, player_name: str, surface: Optional[str] = None) -> Optional[PlayerELO]:
        """
        Calculate ELO from match history
        
        Args:
            player_name: Player name
            surface: Optional surface filter
            
        Returns:
            PlayerELO object or None
        """
        logger.info(f"📊 Calculating ELO for {player_name} (surface: {surface or 'overall'})")
        
        # This would need match history from database
        # For now, return default ELO
        # In production, this would:
        # 1. Query match history from database
        # 2. Filter by surface if specified
        # 3. Calculate ELO using standard formula
        # 4. Track career high
        
        try:
            # Placeholder: would query database for match history
            # matches = self._get_match_history(player_name, surface)
            
            # Standard ELO calculation:
            # new_elo = old_elo + K * (actual_score - expected_score)
            # expected_score = 1 / (1 + 10^((opponent_elo - player_elo) / 400))
            
            # For MVP, return default
            elo = PlayerELO(
                player_name=player_name,
                overall_elo=self.initial_elo,
                hard_elo=self.initial_elo,
                clay_elo=self.initial_elo,
                grass_elo=self.initial_elo,
                career_high_elo=self.initial_elo
            )
            
            logger.debug(f"✅ Calculated ELO for {player_name}: {elo.overall_elo}")
            return elo
            
        except Exception as e:
            logger.error(f"❌ Error calculating ELO: {e}")
            return None
    
    def _get_match_history(self, player_name: str, surface: Optional[str] = None) -> List[Dict]:
        """
        Get match history from database
        
        Args:
            player_name: Player name
            surface: Optional surface filter
            
        Returns:
            List of match dictionaries
        """
        # This would query the database for match history
        # Implementation depends on database structure
        return []
    
    def update_elo_after_match(self, player_name: str, opponent_elo: float, 
                               won: bool, surface: Optional[str] = None):
        """
        Update ELO rating after a match
        
        Args:
            player_name: Player name
            opponent_elo: Opponent's ELO rating
            won: Whether player won
            surface: Optional surface filter
        """
        elo = self.get_elo(player_name, surface)
        if not elo:
            return
        
        # Get current ELO for the surface
        current_elo = getattr(elo, f"{surface}_elo" if surface else "overall_elo", self.initial_elo)
        
        # Calculate expected score
        expected_score = 1 / (1 + 10 ** ((opponent_elo - current_elo) / 400))
        
        # Actual score (1 for win, 0 for loss)
        actual_score = 1.0 if won else 0.0
        
        # Calculate new ELO
        new_elo = current_elo + self.k_factor * (actual_score - expected_score)
        
        # Update ELO
        if surface:
            setattr(elo, f"{surface}_elo", new_elo)
        else:
            elo.overall_elo = new_elo
        
        # Update career high
        if new_elo > elo.career_high_elo:
            elo.career_high_elo = new_elo
        
        elo.updated_at = datetime.now()
        
        logger.debug(f"✅ Updated ELO for {player_name}: {current_elo:.2f} → {new_elo:.2f}")
    
    def store_elo(self, elo: PlayerELO, db_connection=None) -> bool:
        """
        Store ELO rating in database
        
        Args:
            elo: PlayerELO object
            db_connection: Database connection
            
        Returns:
            True if successful
        """
        if not db_connection:
            return False
        
        try:
            cursor = db_connection.cursor()
            
            # Check if SQLite or PostgreSQL
            is_sqlite = isinstance(db_connection, type(__import__('sqlite3').connect('')))
            
            if is_sqlite:
                cursor.execute("""
                    INSERT OR REPLACE INTO player_elo_ratings 
                    (player_name, overall_elo, hard_elo, clay_elo, grass_elo, 
                     career_high_elo, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (elo.player_name, elo.overall_elo, elo.hard_elo, elo.clay_elo, 
                      elo.grass_elo, elo.career_high_elo, elo.updated_at))
            else:
                cursor.execute("""
                    INSERT INTO player_elo_ratings 
                    (player_name, overall_elo, hard_elo, clay_elo, grass_elo, 
                     career_high_elo, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (player_name) DO UPDATE SET
                        overall_elo = EXCLUDED.overall_elo,
                        hard_elo = EXCLUDED.hard_elo,
                        clay_elo = EXCLUDED.clay_elo,
                        grass_elo = EXCLUDED.grass_elo,
                        career_high_elo = EXCLUDED.career_high_elo,
                        updated_at = EXCLUDED.updated_at
                """, (elo.player_name, elo.overall_elo, elo.hard_elo, elo.clay_elo, 
                      elo.grass_elo, elo.career_high_elo, elo.updated_at))
            
            db_connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing ELO: {e}")
            if db_connection:
                db_connection.rollback()
            return False


# USAGE EXAMPLE
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    config = {
        'tennis_abstract_api_key': None,  # Set if available
        'k_factor': 32,
        'initial_elo': 1500.0
    }
    
    enricher = ELOEnricher(config)
    
    # Test getting ELO
    elo = enricher.get_elo("Player Name")
    if elo:
        print(f"\n📊 ELO for {elo.player_name}:")
        print(f"   Overall: {elo.overall_elo:.2f}")
        print(f"   Hard: {elo.hard_elo:.2f}")
        print(f"   Clay: {elo.clay_elo:.2f}")
        print(f"   Grass: {elo.grass_elo:.2f}")
        print(f"   Career High: {elo.career_high_elo:.2f}")

