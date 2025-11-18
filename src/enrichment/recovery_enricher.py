#!/usr/bin/env python3
"""
🚗 TRAVEL & RECOVERY CALCULATOR
================================

Calculates travel distance, recovery time, and fatigue risk for players.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

# Try to import geopy for distance calculation
try:
    from geopy.distance import geodesic
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False
    logger.warning("⚠️ geopy not available, distance calculation will be limited")


@dataclass
class RecoveryData:
    """Travel and recovery data for a player"""
    player_name: str
    match_id: str
    days_since_last_match: Optional[float] = None
    travel_distance_km: Optional[float] = None
    timezone_difference_hours: Optional[int] = None
    fatigue_risk_score: int = 0  # 0-100
    last_tournament_location: Optional[str] = None
    current_tournament_location: Optional[str] = None
    calculated_at: datetime = None
    
    def __post_init__(self):
        if self.calculated_at is None:
            self.calculated_at = datetime.now()


class RecoveryEnricher:
    """
    Travel and recovery calculator
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize recovery enricher
        
        Args:
            config: Configuration dict
        """
        self.config = config or {}
        self.recovery_cache: Dict[str, RecoveryData] = {}
        
        logger.info("🚗 Recovery Enricher initialized")
    
    def get_recovery_data(self, player_name: str, match_id: str, 
                         current_tournament_location: str) -> Optional[RecoveryData]:
        """
        Get recovery data for a player
        
        Args:
            player_name: Player name
            match_id: Current match ID
            current_tournament_location: Current tournament location
            
        Returns:
            RecoveryData object or None
        """
        cache_key = f"{player_name}_{match_id}"
        if cache_key in self.recovery_cache:
            return self.recovery_cache[cache_key]
        
        logger.info(f"🚗 Calculating recovery data for {player_name}")
        
        # Get player's recent match schedule
        recent_matches = self._get_recent_matches(player_name)
        
        if not recent_matches:
            logger.warning(f"⚠️ No recent matches found for {player_name}")
            return None
        
        # Get last match
        last_match = recent_matches[0] if recent_matches else None
        if not last_match:
            return None
        
        # Calculate recovery metrics
        recovery = self._calculate_recovery(
            player_name, match_id, last_match, current_tournament_location
        )
        
        if recovery:
            self.recovery_cache[cache_key] = recovery
        
        return recovery
    
    def _get_recent_matches(self, player_name: str) -> List[Dict]:
        """
        Get player's recent match schedule from database
        
        Args:
            player_name: Player name
            
        Returns:
            List of recent match dictionaries
        """
        # This would query the database for player's recent matches
        # Return matches with tournament location and date
        return []
    
    def _calculate_recovery(self, player_name: str, match_id: str, 
                           last_match: Dict, current_location: str) -> Optional[RecoveryData]:
        """
        Calculate recovery metrics
        
        Args:
            player_name: Player name
            match_id: Current match ID
            last_match: Last match dictionary
            current_location: Current tournament location
            
        Returns:
            RecoveryData object
        """
        last_match_date = last_match.get('date')
        last_location = last_match.get('tournament_location')
        
        if not last_match_date or not last_location:
            return None
        
        # Calculate days since last match
        if isinstance(last_match_date, str):
            try:
                last_date = datetime.fromisoformat(last_match_date)
            except:
                last_date = datetime.now() - timedelta(days=7)  # Default
        else:
            last_date = last_match_date
        
        days_since = (datetime.now() - last_date).total_seconds() / 86400
        
        # Calculate travel distance
        travel_distance = self._calculate_distance(last_location, current_location)
        
        # Calculate timezone difference (simplified)
        timezone_diff = self._calculate_timezone_diff(last_location, current_location)
        
        # Calculate fatigue risk score (0-100)
        fatigue_risk = self._calculate_fatigue_risk(days_since, travel_distance, timezone_diff)
        
        recovery = RecoveryData(
            player_name=player_name,
            match_id=match_id,
            days_since_last_match=round(days_since, 1),
            travel_distance_km=round(travel_distance, 2) if travel_distance else None,
            timezone_difference_hours=timezone_diff,
            fatigue_risk_score=fatigue_risk,
            last_tournament_location=last_location,
            current_tournament_location=current_location
        )
        
        logger.debug(f"✅ Calculated recovery for {player_name}: {days_since:.1f} days, {travel_distance:.0f}km, risk={fatigue_risk}")
        return recovery
    
    def _calculate_distance(self, location1: str, location2: str) -> Optional[float]:
        """
        Calculate distance between two locations in km
        
        Args:
            location1: First location
            location2: Second location
            
        Returns:
            Distance in km or None
        """
        if not GEOPY_AVAILABLE:
            # Simple approximation (not accurate but better than nothing)
            return None
        
        try:
            # Get coordinates (would need geocoding)
            # For now, return None (placeholder)
            # In production, would geocode both locations and calculate distance
            coords1 = self._geocode_location(location1)
            coords2 = self._geocode_location(location2)
            
            if coords1 and coords2:
                distance = geodesic(coords1, coords2).kilometers
                return distance
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error calculating distance: {e}")
            return None
    
    def _geocode_location(self, location: str) -> Optional[tuple]:
        """Geocode location to coordinates (placeholder)"""
        # Would use geocoding service
        return None
    
    def _calculate_timezone_diff(self, location1: str, location2: str) -> Optional[int]:
        """
        Calculate timezone difference in hours
        
        Args:
            location1: First location
            location2: Second location
            
        Returns:
            Timezone difference in hours or None
        """
        # Simplified: would need timezone database
        # For now, return None (placeholder)
        return None
    
    def _calculate_fatigue_risk(self, days_since: float, travel_distance: Optional[float], 
                               timezone_diff: Optional[int]) -> int:
        """
        Calculate fatigue risk score (0-100)
        
        Args:
            days_since: Days since last match
            travel_distance: Travel distance in km
            timezone_diff: Timezone difference in hours
            
        Returns:
            Fatigue risk score (0-100)
        """
        risk = 0
        
        # Days since last match (lower = higher risk)
        if days_since < 1:
            risk += 50  # Very high risk
        elif days_since < 2:
            risk += 30
        elif days_since < 3:
            risk += 15
        
        # Travel distance (higher = higher risk)
        if travel_distance:
            if travel_distance > 10000:
                risk += 30
            elif travel_distance > 5000:
                risk += 20
            elif travel_distance > 2000:
                risk += 10
        
        # Timezone difference (higher = higher risk)
        if timezone_diff:
            if abs(timezone_diff) > 8:
                risk += 20
            elif abs(timezone_diff) > 4:
                risk += 10
        
        return min(risk, 100)  # Cap at 100
    
    def store_recovery(self, recovery: RecoveryData, db_connection=None) -> bool:
        """Store recovery data in database"""
        if not db_connection:
            return False
        
        try:
            cursor = db_connection.cursor()
            is_sqlite = isinstance(db_connection, type(__import__('sqlite3').connect('')))
            
            if is_sqlite:
                cursor.execute("""
                    INSERT OR REPLACE INTO player_recovery 
                    (player_name, match_id, days_since_last_match, travel_distance_km,
                     timezone_difference_hours, fatigue_risk_score, last_tournament_location,
                     current_tournament_location, calculated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (recovery.player_name, recovery.match_id, recovery.days_since_last_match,
                      recovery.travel_distance_km, recovery.timezone_difference_hours,
                      recovery.fatigue_risk_score, recovery.last_tournament_location,
                      recovery.current_tournament_location, recovery.calculated_at))
            else:
                cursor.execute("""
                    INSERT INTO player_recovery 
                    (player_name, match_id, days_since_last_match, travel_distance_km,
                     timezone_difference_hours, fatigue_risk_score, last_tournament_location,
                     current_tournament_location, calculated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (player_name, match_id) DO UPDATE SET
                        days_since_last_match = EXCLUDED.days_since_last_match,
                        travel_distance_km = EXCLUDED.travel_distance_km,
                        timezone_difference_hours = EXCLUDED.timezone_difference_hours,
                        fatigue_risk_score = EXCLUDED.fatigue_risk_score,
                        calculated_at = EXCLUDED.calculated_at
                """, (recovery.player_name, recovery.match_id, recovery.days_since_last_match,
                      recovery.travel_distance_km, recovery.timezone_difference_hours,
                      recovery.fatigue_risk_score, recovery.last_tournament_location,
                      recovery.current_tournament_location, recovery.calculated_at))
            
            db_connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing recovery data: {e}")
            if db_connection:
                db_connection.rollback()
            return False

