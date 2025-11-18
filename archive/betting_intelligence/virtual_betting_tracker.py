#!/usr/bin/env python3
"""
🎯 VIRTUAL BETTING TRACKER
==========================
Automatically locks every prediction as a virtual bet and tracks outcomes
for ML model calibration and self-improvement.

Author: TennisBot Virtual Betting System
Version: 1.0.0
"""

import sqlite3
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import threading

logger = logging.getLogger(__name__)

@dataclass
class VirtualBet:
    """Virtual bet data structure"""
    match_id: str
    prediction: str  # predicted winner
    confidence: float
    stake: float  # virtual stake amount
    odds: float
    timestamp: str
    status: str = "pending"  # pending, won, lost, void
    outcome: Optional[str] = None  # actual winner
    profit_loss: Optional[float] = None
    calibration_used: bool = False
    surface: Optional[str] = None
    tournament: Optional[str] = None
    home_player: Optional[str] = None
    away_player: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return asdict(self)

class VirtualBettingTracker:
    """Tracks all predictions as virtual bets for calibration"""
    
    def __init__(self, db_path: str = None, virtual_bankroll: float = 10000.0):
        """
        Initialize virtual betting tracker
        
        Args:
            db_path: Path to SQLite database file
            virtual_bankroll: Starting virtual bankroll amount
        """
        if db_path is None:
            data_dir = Path(__file__).parent.parent / 'data'
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / 'virtual_bets.db')
        
        self.db_path = db_path
        self.virtual_bankroll = virtual_bankroll
        self.current_bankroll = virtual_bankroll
        self._lock = threading.Lock()
        
        # Initialize database
        self._init_database()
        
        logger.info(f"✅ VirtualBettingTracker initialized with bankroll: {virtual_bankroll}")
    
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Virtual bets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS virtual_bets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id TEXT NOT NULL,
                    prediction TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    stake REAL NOT NULL,
                    odds REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    outcome TEXT,
                    profit_loss REAL,
                    calibration_used INTEGER DEFAULT 0,
                    surface TEXT,
                    tournament TEXT,
                    home_player TEXT,
                    away_player TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(match_id, timestamp)
                )
            ''')
            
            # Calibration data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS calibration_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id TEXT NOT NULL,
                    predicted_confidence REAL NOT NULL,
                    actual_outcome TEXT NOT NULL,
                    predicted_outcome TEXT NOT NULL,
                    accuracy INTEGER NOT NULL,  -- 1 if correct, 0 if wrong
                    calibration_error REAL,
                    confidence_bucket TEXT,
                    surface TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Model performance table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_version TEXT NOT NULL,
                    training_date TEXT NOT NULL,
                    accuracy REAL,
                    calibration_score REAL,
                    brier_score REAL,
                    test_period_start TEXT,
                    test_period_end TEXT,
                    total_predictions INTEGER,
                    correct_predictions INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_match_id ON virtual_bets(match_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON virtual_bets(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON virtual_bets(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_calibration_used ON virtual_bets(calibration_used)')
            
            conn.commit()
            logger.info("✅ Database tables initialized")
    
    def place_virtual_bet(
        self,
        match_id: str,
        prediction: str,
        confidence: float,
        odds: float,
        stake_method: str = "kelly",
        surface: str = None,
        tournament: str = None,
        home_player: str = None,
        away_player: str = None
    ) -> Optional[VirtualBet]:
        """
        Automatically place a virtual bet for a prediction
        
        Args:
            match_id: Unique match identifier
            prediction: Predicted winner
            confidence: Prediction confidence (0-1)
            odds: Betting odds for the prediction
            stake_method: Method to calculate stake (kelly, fixed, confidence)
            surface: Court surface
            tournament: Tournament name
            home_player: Home player name
            away_player: Away player name
            
        Returns:
            VirtualBet object if successful, None otherwise
        """
        with self._lock:
            try:
                # Calculate stake based on method
                stake = self._calculate_stake(confidence, odds, stake_method)
                
                # Check if bet already exists for this match
                existing = self._get_bet_by_match_id(match_id)
                if existing and existing.status == "pending":
                    logger.warning(f"⚠️ Virtual bet already exists for match {match_id}")
                    return existing
                
                # Create virtual bet
                virtual_bet = VirtualBet(
                    match_id=match_id,
                    prediction=prediction,
                    confidence=confidence,
                    stake=stake,
                    odds=odds,
                    timestamp=datetime.now().isoformat(),
                    status="pending",
                    surface=surface,
                    tournament=tournament,
                    home_player=home_player,
                    away_player=away_player
                )
                
                # Save to database
                self._save_bet(virtual_bet)
                
                # Update bankroll (reserve stake)
                self.current_bankroll -= stake
                
                logger.info(
                    f"✅ Virtual bet placed: {prediction} @ {odds:.2f} "
                    f"(stake: {stake:.2f}, confidence: {confidence:.2%})"
                )
                
                return virtual_bet
                
            except Exception as e:
                logger.error(f"❌ Error placing virtual bet: {e}")
                return None
    
    def _calculate_stake(
        self,
        confidence: float,
        odds: float,
        method: str = "kelly"
    ) -> float:
        """
        Calculate virtual stake amount
        
        Args:
            confidence: Prediction confidence
            odds: Betting odds
            method: Calculation method (kelly, fixed, confidence)
            
        Returns:
            Stake amount
        """
        if method == "kelly":
            # Kelly Criterion: f = (p * b - q) / b
            # where p = win probability, b = odds - 1, q = 1 - p
            p = confidence
            b = odds - 1
            q = 1 - p
            kelly_fraction = (p * b - q) / b if b > 0 else 0
            # Use fractional Kelly (25% of full Kelly for safety)
            kelly_fraction = max(0, min(kelly_fraction * 0.25, 0.05))  # Max 5% of bankroll
            stake = self.current_bankroll * kelly_fraction
            
        elif method == "fixed":
            # Fixed percentage of bankroll
            stake = self.current_bankroll * 0.02  # 2% fixed
            
        elif method == "confidence":
            # Confidence-based: 1-3% based on confidence
            confidence_multiplier = 0.01 + (confidence - 0.5) * 0.04  # 1-3% range
            stake = self.current_bankroll * confidence_multiplier
            
        else:
            # Default: 2% of bankroll
            stake = self.current_bankroll * 0.02
        
        # Minimum and maximum limits
        stake = max(10.0, min(stake, self.current_bankroll * 0.05))  # Min 10, Max 5%
        
        return round(stake, 2)
    
    def _save_bet(self, bet: VirtualBet):
        """Save virtual bet to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO virtual_bets
                (match_id, prediction, confidence, stake, odds, timestamp, status,
                 outcome, profit_loss, calibration_used, surface, tournament,
                 home_player, away_player, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                bet.match_id,
                bet.prediction,
                bet.confidence,
                bet.stake,
                bet.odds,
                bet.timestamp,
                bet.status,
                bet.outcome,
                bet.profit_loss,
                1 if bet.calibration_used else 0,
                bet.surface,
                bet.tournament,
                bet.home_player,
                bet.away_player,
                datetime.now().isoformat()
            ))
            conn.commit()
    
    def update_bet_outcome(
        self,
        match_id: str,
        actual_outcome: str,
        force_update: bool = False
    ) -> Optional[VirtualBet]:
        """
        Update virtual bet with actual match outcome
        
        Args:
            match_id: Match identifier
            actual_outcome: Actual winner
            force_update: Force update even if already processed
            
        Returns:
            Updated VirtualBet object
        """
        with self._lock:
            try:
                bet = self._get_bet_by_match_id(match_id)
                if not bet:
                    logger.warning(f"⚠️ No virtual bet found for match {match_id}")
                    return None
                
                if bet.status != "pending" and not force_update:
                    logger.info(f"ℹ️ Bet for match {match_id} already processed")
                    return bet
                
                # Determine result
                is_winner = (bet.prediction.lower() == actual_outcome.lower())
                
                if is_winner:
                    bet.status = "won"
                    bet.profit_loss = (bet.stake * bet.odds) - bet.stake
                    self.current_bankroll += bet.stake * bet.odds
                else:
                    bet.status = "lost"
                    bet.profit_loss = -bet.stake
                    # Stake already deducted, no need to subtract again
                
                bet.outcome = actual_outcome
                
                # Update database
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE virtual_bets
                        SET status = ?, outcome = ?, profit_loss = ?, updated_at = ?
                        WHERE match_id = ? AND timestamp = ?
                    ''', (
                        bet.status,
                        bet.outcome,
                        bet.profit_loss,
                        datetime.now().isoformat(),
                        bet.match_id,
                        bet.timestamp
                    ))
                    conn.commit()
                
                # Record calibration data
                self._record_calibration_data(bet, actual_outcome, is_winner)
                
                logger.info(
                    f"✅ Bet updated: {bet.match_id} - "
                    f"Predicted: {bet.prediction}, Actual: {actual_outcome}, "
                    f"Result: {bet.status}, P&L: {bet.profit_loss:.2f}"
                )
                
                return bet
                
            except Exception as e:
                logger.error(f"❌ Error updating bet outcome: {e}")
                return None
    
    def _record_calibration_data(self, bet: VirtualBet, actual_outcome: str, is_correct: bool):
        """Record calibration data for ML model improvement"""
        try:
            # Calculate calibration error
            calibration_error = abs(bet.confidence - (1.0 if is_correct else 0.0))
            
            # Determine confidence bucket
            if bet.confidence < 0.60:
                bucket = "0.50-0.60"
            elif bet.confidence < 0.65:
                bucket = "0.60-0.65"
            elif bet.confidence < 0.70:
                bucket = "0.65-0.70"
            elif bet.confidence < 0.75:
                bucket = "0.70-0.75"
            elif bet.confidence < 0.80:
                bucket = "0.75-0.80"
            else:
                bucket = "0.80+"
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO calibration_data
                    (match_id, predicted_confidence, actual_outcome, predicted_outcome,
                     accuracy, calibration_error, confidence_bucket, surface)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    bet.match_id,
                    bet.confidence,
                    actual_outcome,
                    bet.prediction,
                    1 if is_correct else 0,
                    calibration_error,
                    bucket,
                    bet.surface
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Error recording calibration data: {e}")
    
    def _get_bet_by_match_id(self, match_id: str) -> Optional[VirtualBet]:
        """Get virtual bet by match ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM virtual_bets
                    WHERE match_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                ''', (match_id,))
                
                row = cursor.fetchone()
                if row:
                    return VirtualBet(
                        match_id=row['match_id'],
                        prediction=row['prediction'],
                        confidence=row['confidence'],
                        stake=row['stake'],
                        odds=row['odds'],
                        timestamp=row['timestamp'],
                        status=row['status'],
                        outcome=row['outcome'],
                        profit_loss=row['profit_loss'],
                        calibration_used=bool(row['calibration_used']),
                        surface=row['surface'],
                        tournament=row['tournament'],
                        home_player=row['home_player'],
                        away_player=row['away_player']
                    )
                return None
        except Exception as e:
            logger.error(f"❌ Error getting bet: {e}")
            return None
    
    def get_pending_bets(self) -> List[VirtualBet]:
        """Get all pending virtual bets"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM virtual_bets
                    WHERE status = 'pending'
                    ORDER BY timestamp DESC
                ''')
                
                bets = []
                for row in cursor.fetchall():
                    bets.append(VirtualBet(
                        match_id=row['match_id'],
                        prediction=row['prediction'],
                        confidence=row['confidence'],
                        stake=row['stake'],
                        odds=row['odds'],
                        timestamp=row['timestamp'],
                        status=row['status'],
                        outcome=row['outcome'],
                        profit_loss=row['profit_loss'],
                        calibration_used=bool(row['calibration_used']),
                        surface=row['surface'],
                        tournament=row['tournament'],
                        home_player=row['home_player'],
                        away_player=row['away_player']
                    ))
                return bets
        except Exception as e:
            logger.error(f"❌ Error getting pending bets: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get virtual betting statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total bets
                cursor.execute('SELECT COUNT(*) FROM virtual_bets')
                total_bets = cursor.fetchone()[0]
                
                # Pending bets
                cursor.execute("SELECT COUNT(*) FROM virtual_bets WHERE status = 'pending'")
                pending_bets = cursor.fetchone()[0]
                
                # Won bets
                cursor.execute("SELECT COUNT(*) FROM virtual_bets WHERE status = 'won'")
                won_bets = cursor.fetchone()[0]
                
                # Lost bets
                cursor.execute("SELECT COUNT(*) FROM virtual_bets WHERE status = 'lost'")
                lost_bets = cursor.fetchone()[0]
                
                # Total P&L
                cursor.execute('SELECT COALESCE(SUM(profit_loss), 0) FROM virtual_bets WHERE profit_loss IS NOT NULL')
                total_pl = cursor.fetchone()[0] or 0.0
                
                # Win rate
                resolved_bets = won_bets + lost_bets
                win_rate = (won_bets / resolved_bets * 100) if resolved_bets > 0 else 0.0
                
                # ROI
                cursor.execute('SELECT COALESCE(SUM(stake), 0) FROM virtual_bets WHERE status IN ("won", "lost")')
                total_staked = cursor.fetchone()[0] or 0.0
                roi = (total_pl / total_staked * 100) if total_staked > 0 else 0.0
                
                return {
                    'total_bets': total_bets,
                    'pending_bets': pending_bets,
                    'won_bets': won_bets,
                    'lost_bets': lost_bets,
                    'win_rate': round(win_rate, 2),
                    'total_profit_loss': round(total_pl, 2),
                    'roi': round(roi, 2),
                    'current_bankroll': round(self.current_bankroll, 2),
                    'initial_bankroll': self.virtual_bankroll,
                    'bankroll_change': round(self.current_bankroll - self.virtual_bankroll, 2),
                    'bankroll_change_pct': round(
                        ((self.current_bankroll - self.virtual_bankroll) / self.virtual_bankroll) * 100, 2
                    )
                }
        except Exception as e:
            logger.error(f"❌ Error getting statistics: {e}")
            return {}
    
    def get_calibration_data(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get calibration data for analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM calibration_data
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (limit,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"❌ Error getting calibration data: {e}")
            return []

