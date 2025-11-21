#!/usr/bin/env python3
"""
Universal Data Collector
========================

Collects ALL ITF matches daily (100+ matches) for ML training.
Not just played bets (2-3), but all available matches.

This is Layer 1 of the Self-Learning AI Engine.
"""

import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scrapers.sportbex_client import SportbexClient, SportbexMatch

logger = logging.getLogger(__name__)


class MatchResultsDB:
    """SQLite database for storing match results and training data"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize Match Results database
        
        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / 'data' / 'match_results.db'
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        logger.info(f"✅ Match Results DB initialized: {self.db_path}")
    
    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Matches table - stores all match data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                match_id TEXT PRIMARY KEY,
                tournament TEXT,
                tournament_tier TEXT,
                player1 TEXT NOT NULL,
                player2 TEXT NOT NULL,
                player1_ranking INTEGER,
                player2_ranking INTEGER,
                player1_odds REAL,
                player2_odds REAL,
                commence_time TIMESTAMP,
                surface TEXT,
                match_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Results table - stores match results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results (
                match_id TEXT PRIMARY KEY,
                winner TEXT,
                score TEXT,
                result_date TIMESTAMP,
                player1_won BOOLEAN,
                player2_won BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (match_id) REFERENCES matches(match_id)
            )
        """)
        
        # Features table - stores extracted features for ML
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS features (
                match_id TEXT PRIMARY KEY,
                features_json TEXT,
                feature_version INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (match_id) REFERENCES matches(match_id)
            )
        """)
        
        # Training data view - combines matches, results, and features
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS training_data AS
            SELECT 
                m.match_id,
                m.tournament,
                m.tournament_tier,
                m.player1,
                m.player2,
                m.player1_ranking,
                m.player2_ranking,
                m.player1_odds,
                m.player2_odds,
                m.commence_time,
                m.surface,
                m.match_date,
                r.winner,
                r.score,
                r.player1_won,
                r.player2_won,
                f.features_json,
                f.feature_version
            FROM matches m
            LEFT JOIN results r ON m.match_id = r.match_id
            LEFT JOIN features f ON m.match_id = f.match_id
        """)
        
        # Indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_tournament ON matches(tournament_tier)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_date ON results(result_date)")
        
        conn.commit()
        conn.close()
    
    def insert_match(self, match: SportbexMatch) -> bool:
        """
        Insert or update match data
        
        Args:
            match: SportbexMatch object
            
        Returns:
            True if successful
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            match_date = match.commence_time.date() if match.commence_time else None
            
            cursor.execute("""
                INSERT OR REPLACE INTO matches (
                    match_id, tournament, tournament_tier, player1, player2,
                    player1_ranking, player2_ranking, player1_odds, player2_odds,
                    commence_time, surface, match_date, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                match.match_id,
                match.tournament,
                match.tournament_tier,
                match.player1,
                match.player2,
                match.player1_ranking,
                match.player2_ranking,
                match.player1_odds,
                match.player2_odds,
                match.commence_time.isoformat() if match.commence_time else None,
                match.surface,
                match_date.isoformat() if match_date else None,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error inserting match {match.match_id}: {e}")
            return False
    
    def insert_result(self, match_id: str, winner: str, score: Optional[str] = None) -> bool:
        """
        Insert match result
        
        Args:
            match_id: Match ID
            winner: Winner name (player1 or player2)
            score: Match score (optional)
            
        Returns:
            True if successful
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Determine which player won
            cursor.execute("SELECT player1, player2 FROM matches WHERE match_id = ?", (match_id,))
            row = cursor.fetchone()
            if not row:
                logger.warning(f"Match {match_id} not found in database")
                conn.close()
                return False
            
            player1, player2 = row
            player1_won = (winner == player1)
            player2_won = (winner == player2)
            
            cursor.execute("""
                INSERT OR REPLACE INTO results (
                    match_id, winner, score, result_date, player1_won, player2_won
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                match_id,
                winner,
                score,
                datetime.now().isoformat(),
                player1_won,
                player2_won
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error inserting result for {match_id}: {e}")
            return False
    
    def get_matches_without_results(self, days_back: int = 7) -> List[Dict]:
        """
        Get matches without results (for result validation)
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of match dictionaries
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days_back)).date()
        
        cursor.execute("""
            SELECT m.*
            FROM matches m
            LEFT JOIN results r ON m.match_id = r.match_id
            WHERE r.match_id IS NULL
            AND m.match_date < ?
            ORDER BY m.match_date DESC
        """, (cutoff_date.isoformat(),))
        
        rows = cursor.fetchall()
        matches = [dict(row) for row in rows]
        
        conn.close()
        return matches
    
    def get_training_data(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get training data (matches with results and features)
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of training data dictionaries
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM training_data WHERE player1_won IS NOT NULL"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        
        conn.close()
        return data
    
    def count_matches(self) -> int:
        """Get total number of matches"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM matches")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def count_results(self) -> int:
        """Get total number of results"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM results")
        count = cursor.fetchone()[0]
        conn.close()
        return count


class UniversalDataCollector:
    """Collects ALL ITF matches daily for ML training"""
    
    def __init__(self, api_key: Optional[str] = None, db_path: Optional[str] = None):
        """
        Initialize data collector
        
        Args:
            api_key: Sportbex API key
            db_path: Path to Match Results database
        """
        self.client = SportbexClient(api_key)
        self.db = MatchResultsDB(db_path)
    
    async def collect_daily_matches(self, days_ahead: int = 2) -> Dict[str, Any]:
        """
        Collect all matches for the next N days
        
        Args:
            days_ahead: Number of days ahead to fetch
            
        Returns:
            Dictionary with collection results
        """
        logger.info(f"📥 Collecting matches for next {days_ahead} days...")
        
        matches_collected = 0
        matches_updated = 0
        errors = 0
        
        try:
            async with self.client:
                matches = await self.client.get_matches(
                    hours_ahead=days_ahead * 24,
                    sport_id=2  # Tennis
                )
            
            logger.info(f"✅ Fetched {len(matches)} matches from Sportbex API")
            
            for match in matches:
                try:
                    # Check if match already exists
                    existing_count = self.db.count_matches()
                    
                    if self.db.insert_match(match):
                        matches_collected += 1
                        if existing_count < self.db.count_matches():
                            matches_updated += 1
                except Exception as e:
                    logger.error(f"Error processing match {match.match_id}: {e}")
                    errors += 1
            
            total_matches = self.db.count_matches()
            
            logger.info("=" * 80)
            logger.info("✅ DATA COLLECTION COMPLETED")
            logger.info("=" * 80)
            logger.info(f"📊 Matches fetched: {len(matches)}")
            logger.info(f"💾 Matches stored: {matches_collected}")
            logger.info(f"🔄 Matches updated: {matches_updated}")
            logger.info(f"❌ Errors: {errors}")
            logger.info(f"📈 Total matches in DB: {total_matches}")
            logger.info("=" * 80)
            
            return {
                'success': True,
                'matches_fetched': len(matches),
                'matches_collected': matches_collected,
                'matches_updated': matches_updated,
                'errors': errors,
                'total_matches_in_db': total_matches,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Data collection failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


async def main():
    """Main entry point for data collection"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Universal Data Collector')
    parser.add_argument('--days-ahead', type=int, default=2, help='Days ahead to fetch')
    parser.add_argument('--api-key', type=str, help='Sportbex API key')
    
    args = parser.parse_args()
    
    collector = UniversalDataCollector(api_key=args.api_key)
    result = await collector.collect_daily_matches(days_ahead=args.days_ahead)
    
    if result.get('success'):
        print(f"\n✅ Collected {result['matches_collected']} matches")
        print(f"📈 Total matches in DB: {result['total_matches_in_db']}")
    else:
        print(f"\n❌ Collection failed: {result.get('error')}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())

