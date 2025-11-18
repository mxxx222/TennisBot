#!/usr/bin/env python3
"""
📊 SERVICE & RETURN STATS ENRICHER
===================================

Enriches player data with service and return statistics.
Calculates from match history: aces/match, DFs/match, hold%, break%, etc.
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
class PlayerStats:
    """Player service and return statistics"""
    player_name: str
    surface: Optional[str] = None  # 'hard', 'clay', 'grass', None for overall
    period: str = 'last_10'  # 'career', 'last_10', 'last_30'
    aces_per_match: float = 0.0
    double_faults_per_match: float = 0.0
    hold_percentage: float = 0.0  # Service games won %
    break_percentage: float = 0.0  # Return games won %
    second_serve_win_percentage: float = 0.0
    break_points_saved_percentage: float = 0.0
    break_points_converted_percentage: float = 0.0
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = datetime.now()


class StatsEnricher:
    """
    Service and return stats enricher
    
    Calculates stats from match history or scrapes from TennisExplorer player profiles
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize stats enricher
        
        Args:
            config: Configuration dict
        """
        self.config = config or {}
        self.stats_cache: Dict[str, PlayerStats] = {}
        
        logger.info("📊 Stats Enricher initialized")
    
    def get_stats(self, player_name: str, surface: Optional[str] = None, 
                  period: str = 'last_10') -> Optional[PlayerStats]:
        """
        Get service/return stats for a player
        
        Args:
            player_name: Player name
            surface: Optional surface filter
            period: Period to calculate ('career', 'last_10', 'last_30')
            
        Returns:
            PlayerStats object or None
        """
        cache_key = f"{player_name}_{surface or 'overall'}_{period}"
        if cache_key in self.stats_cache:
            return self.stats_cache[cache_key]
        
        logger.info(f"📊 Calculating stats for {player_name} (surface: {surface or 'overall'}, period: {period})")
        
        # Get match history
        matches = self._get_match_history(player_name, surface, period)
        
        if not matches:
            logger.warning(f"⚠️ No match history found for {player_name}")
            return None
        
        # Calculate stats from match history
        stats = self._calculate_stats_from_matches(player_name, matches, surface, period)
        
        if stats:
            self.stats_cache[cache_key] = stats
        
        return stats
    
    def _get_match_history(self, player_name: str, surface: Optional[str] = None, 
                          period: str = 'last_10') -> List[Dict]:
        """
        Get match history from database or scraper
        
        Args:
            player_name: Player name
            surface: Optional surface filter
            period: Period to get matches for
            
        Returns:
            List of match dictionaries with stats
        """
        # This would query the database for match history
        # For now, return empty list (placeholder)
        # In production, this would:
        # 1. Query database for player's matches
        # 2. Filter by surface if specified
        # 3. Filter by period (last 10, last 30, etc.)
        # 4. Include match stats (aces, DFs, service games, etc.)
        
        return []
    
    def _calculate_stats_from_matches(self, player_name: str, matches: List[Dict], 
                                     surface: Optional[str], period: str) -> Optional[PlayerStats]:
        """
        Calculate stats from match data
        
        Args:
            player_name: Player name
            matches: List of match dictionaries
            surface: Surface filter
            period: Period identifier
            
        Returns:
            PlayerStats object
        """
        if not matches:
            return None
        
        total_matches = len(matches)
        total_aces = 0
        total_dfs = 0
        total_service_games = 0
        total_service_games_won = 0
        total_return_games = 0
        total_return_games_won = 0
        total_second_serves = 0
        total_second_serves_won = 0
        total_bp_faced = 0
        total_bp_saved = 0
        total_bp_opportunities = 0
        total_bp_converted = 0
        
        for match in matches:
            # Aggregate stats from match
            # These would come from match detail pages or database
            total_aces += match.get('aces', 0)
            total_dfs += match.get('double_faults', 0)
            total_service_games += match.get('service_games', 0)
            total_service_games_won += match.get('service_games_won', 0)
            total_return_games += match.get('return_games', 0)
            total_return_games_won += match.get('return_games_won', 0)
            total_second_serves += match.get('second_serves', 0)
            total_second_serves_won += match.get('second_serves_won', 0)
            total_bp_faced += match.get('break_points_faced', 0)
            total_bp_saved += match.get('break_points_saved', 0)
            total_bp_opportunities += match.get('break_point_opportunities', 0)
            total_bp_converted += match.get('break_points_converted', 0)
        
        # Calculate percentages
        aces_per_match = total_aces / total_matches if total_matches > 0 else 0.0
        dfs_per_match = total_dfs / total_matches if total_matches > 0 else 0.0
        hold_pct = (total_service_games_won / total_service_games * 100) if total_service_games > 0 else 0.0
        break_pct = (total_return_games_won / total_return_games * 100) if total_return_games > 0 else 0.0
        second_serve_win_pct = (total_second_serves_won / total_second_serves * 100) if total_second_serves > 0 else 0.0
        bp_saved_pct = (total_bp_saved / total_bp_faced * 100) if total_bp_faced > 0 else 0.0
        bp_converted_pct = (total_bp_converted / total_bp_opportunities * 100) if total_bp_opportunities > 0 else 0.0
        
        stats = PlayerStats(
            player_name=player_name,
            surface=surface,
            period=period,
            aces_per_match=round(aces_per_match, 2),
            double_faults_per_match=round(dfs_per_match, 2),
            hold_percentage=round(hold_pct, 2),
            break_percentage=round(break_pct, 2),
            second_serve_win_percentage=round(second_serve_win_pct, 2),
            break_points_saved_percentage=round(bp_saved_pct, 2),
            break_points_converted_percentage=round(bp_converted_pct, 2)
        )
        
        logger.debug(f"✅ Calculated stats for {player_name}: Hold%={hold_pct:.2f}%, Break%={break_pct:.2f}%")
        return stats
    
    def store_stats(self, stats: PlayerStats, db_connection=None) -> bool:
        """
        Store stats in database
        
        Args:
            stats: PlayerStats object
            db_connection: Database connection
            
        Returns:
            True if successful
        """
        if not db_connection:
            return False
        
        try:
            cursor = db_connection.cursor()
            is_sqlite = isinstance(db_connection, type(__import__('sqlite3').connect('')))
            
            if is_sqlite:
                cursor.execute("""
                    INSERT OR REPLACE INTO player_stats 
                    (player_name, surface, period, aces_per_match, double_faults_per_match,
                     hold_percentage, break_percentage, second_serve_win_percentage,
                     break_points_saved_percentage, break_points_converted_percentage, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (stats.player_name, stats.surface, stats.period, stats.aces_per_match,
                      stats.double_faults_per_match, stats.hold_percentage, stats.break_percentage,
                      stats.second_serve_win_percentage, stats.break_points_saved_percentage,
                      stats.break_points_converted_percentage, stats.updated_at))
            else:
                cursor.execute("""
                    INSERT INTO player_stats 
                    (player_name, surface, period, aces_per_match, double_faults_per_match,
                     hold_percentage, break_percentage, second_serve_win_percentage,
                     break_points_saved_percentage, break_points_converted_percentage, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (player_name, surface, period) DO UPDATE SET
                        aces_per_match = EXCLUDED.aces_per_match,
                        double_faults_per_match = EXCLUDED.double_faults_per_match,
                        hold_percentage = EXCLUDED.hold_percentage,
                        break_percentage = EXCLUDED.break_percentage,
                        second_serve_win_percentage = EXCLUDED.second_serve_win_percentage,
                        break_points_saved_percentage = EXCLUDED.break_points_saved_percentage,
                        break_points_converted_percentage = EXCLUDED.break_points_converted_percentage,
                        updated_at = EXCLUDED.updated_at
                """, (stats.player_name, stats.surface, stats.period, stats.aces_per_match,
                      stats.double_faults_per_match, stats.hold_percentage, stats.break_percentage,
                      stats.second_serve_win_percentage, stats.break_points_saved_percentage,
                      stats.break_points_converted_percentage, stats.updated_at))
            
            db_connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing stats: {e}")
            if db_connection:
                db_connection.rollback()
            return False


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    enricher = StatsEnricher()
    
    # Test getting stats
    stats = enricher.get_stats("Player Name", surface="hard", period="last_10")
    if stats:
        print(f"\n📊 Stats for {stats.player_name}:")
        print(f"   Aces/match: {stats.aces_per_match}")
        print(f"   DFs/match: {stats.double_faults_per_match}")
        print(f"   Hold %: {stats.hold_percentage}%")
        print(f"   Break %: {stats.break_percentage}%")

