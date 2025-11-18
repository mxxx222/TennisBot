#!/usr/bin/env python3
"""
📊 TIEBREAK & DECIDING SET STATS ENRICHER
=========================================

Calculates tiebreak and deciding set statistics from match history.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from pathlib import Path
import sys
import re

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


@dataclass
class TiebreakStats:
    """Tiebreak and deciding set statistics"""
    player_name: str
    period: str = 'last_12_months'  # 'career', 'last_12_months'
    tiebreak_wins: int = 0
    tiebreak_losses: int = 0
    tiebreak_win_percentage: float = 0.0
    deciding_set_wins: int = 0
    deciding_set_losses: int = 0
    deciding_set_win_percentage: float = 0.0
    clutch_factor: float = 0.0  # Performance under pressure score (0-100)
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = datetime.now()


class TiebreakEnricher:
    """
    Tiebreak and deciding set stats enricher
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize tiebreak enricher
        
        Args:
            config: Configuration dict
        """
        self.config = config or {}
        self.stats_cache: Dict[str, TiebreakStats] = {}
        
        logger.info("📊 Tiebreak Enricher initialized")
    
    def get_tiebreak_stats(self, player_name: str, period: str = 'last_12_months') -> Optional[TiebreakStats]:
        """
        Get tiebreak and deciding set stats for a player
        
        Args:
            player_name: Player name
            period: Period to calculate ('career', 'last_12_months')
            
        Returns:
            TiebreakStats object or None
        """
        cache_key = f"{player_name}_{period}"
        if cache_key in self.stats_cache:
            return self.stats_cache[cache_key]
        
        logger.info(f"📊 Calculating tiebreak stats for {player_name} (period: {period})")
        
        # Get match history
        matches = self._get_match_history(player_name, period)
        
        if not matches:
            logger.warning(f"⚠️ No match history found for {player_name}")
            return None
        
        # Calculate stats
        stats = self._calculate_tiebreak_stats(player_name, matches, period)
        
        if stats:
            self.stats_cache[cache_key] = stats
        
        return stats
    
    def _get_match_history(self, player_name: str, period: str) -> List[Dict]:
        """
        Get match history from database
        
        Args:
            player_name: Player name
            period: Period to get matches for
            
        Returns:
            List of match dictionaries with scores
        """
        # This would query the database for match history
        # Filter by period (last 12 months if specified)
        # Return matches with scores
        
        return []
    
    def _calculate_tiebreak_stats(self, player_name: str, matches: List[Dict], 
                                  period: str) -> Optional[TiebreakStats]:
        """
        Calculate tiebreak and deciding set stats from matches
        
        Args:
            player_name: Player name
            matches: List of match dictionaries
            period: Period identifier
            
        Returns:
            TiebreakStats object
        """
        if not matches:
            return None
        
        tiebreak_wins = 0
        tiebreak_losses = 0
        deciding_set_wins = 0
        deciding_set_losses = 0
        
        for match in matches:
            score = match.get('score', '')
            won = match.get('won', False)  # Whether player won the match
            
            # Parse tiebreak scores (e.g., "7-6(5)", "6-7(3)")
            tiebreak_pattern = r'(\d+)-(\d+)\((\d+)\)'
            tiebreak_matches = re.findall(tiebreak_pattern, score)
            
            for tb_match in tiebreak_matches:
                set_score = int(tb_match[0])
                opponent_score = int(tb_match[1])
                
                # Determine who won the tiebreak
                if set_score > opponent_score:
                    tiebreak_wins += 1
                else:
                    tiebreak_losses += 1
            
            # Check if match went to deciding set (3rd set)
            sets = score.split(',')
            if len(sets) >= 3:
                # Match went to 3rd set
                if won:
                    deciding_set_wins += 1
                else:
                    deciding_set_losses += 1
        
        # Calculate percentages
        total_tiebreaks = tiebreak_wins + tiebreak_losses
        tiebreak_win_pct = (tiebreak_wins / total_tiebreaks * 100) if total_tiebreaks > 0 else 0.0
        
        total_deciding_sets = deciding_set_wins + deciding_set_losses
        deciding_set_win_pct = (deciding_set_wins / total_deciding_sets * 100) if total_deciding_sets > 0 else 0.0
        
        # Calculate clutch factor (weighted combination)
        # Higher weight on deciding set performance
        clutch_factor = (tiebreak_win_pct * 0.4 + deciding_set_win_pct * 0.6)
        
        stats = TiebreakStats(
            player_name=player_name,
            period=period,
            tiebreak_wins=tiebreak_wins,
            tiebreak_losses=tiebreak_losses,
            tiebreak_win_percentage=round(tiebreak_win_pct, 2),
            deciding_set_wins=deciding_set_wins,
            deciding_set_losses=deciding_set_losses,
            deciding_set_win_percentage=round(deciding_set_win_pct, 2),
            clutch_factor=round(clutch_factor, 2)
        )
        
        logger.debug(f"✅ Calculated tiebreak stats for {player_name}: TB={tiebreak_win_pct:.2f}%, DS={deciding_set_win_pct:.2f}%")
        return stats
    
    def store_stats(self, stats: TiebreakStats, db_connection=None) -> bool:
        """Store tiebreak stats in database"""
        if not db_connection:
            return False
        
        try:
            cursor = db_connection.cursor()
            is_sqlite = isinstance(db_connection, type(__import__('sqlite3').connect('')))
            
            if is_sqlite:
                cursor.execute("""
                    INSERT OR REPLACE INTO player_tiebreak_stats 
                    (player_name, period, tiebreak_wins, tiebreak_losses, tiebreak_win_percentage,
                     deciding_set_wins, deciding_set_losses, deciding_set_win_percentage,
                     clutch_factor, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (stats.player_name, stats.period, stats.tiebreak_wins, stats.tiebreak_losses,
                      stats.tiebreak_win_percentage, stats.deciding_set_wins, stats.deciding_set_losses,
                      stats.deciding_set_win_percentage, stats.clutch_factor, stats.updated_at))
            else:
                cursor.execute("""
                    INSERT INTO player_tiebreak_stats 
                    (player_name, period, tiebreak_wins, tiebreak_losses, tiebreak_win_percentage,
                     deciding_set_wins, deciding_set_losses, deciding_set_win_percentage,
                     clutch_factor, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (player_name, period) DO UPDATE SET
                        tiebreak_wins = EXCLUDED.tiebreak_wins,
                        tiebreak_losses = EXCLUDED.tiebreak_losses,
                        tiebreak_win_percentage = EXCLUDED.tiebreak_win_percentage,
                        deciding_set_wins = EXCLUDED.deciding_set_wins,
                        deciding_set_losses = EXCLUDED.deciding_set_losses,
                        deciding_set_win_percentage = EXCLUDED.deciding_set_win_percentage,
                        clutch_factor = EXCLUDED.clutch_factor,
                        updated_at = EXCLUDED.updated_at
                """, (stats.player_name, stats.period, stats.tiebreak_wins, stats.tiebreak_losses,
                      stats.tiebreak_win_percentage, stats.deciding_set_wins, stats.deciding_set_losses,
                      stats.deciding_set_win_percentage, stats.clutch_factor, stats.updated_at))
            
            db_connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing tiebreak stats: {e}")
            if db_connection:
                db_connection.rollback()
            return False

