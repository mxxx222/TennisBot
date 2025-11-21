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


# NOTE: UniversalDataCollector removed - use daily_learning_loop.py + notion_sync.py instead
# MatchResultsDB class is kept for SQLite database operations used by ML training

