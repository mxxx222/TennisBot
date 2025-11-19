"""
Historical odds data storage and management
Stores odds movements, opportunities, and performance data for analysis
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import os
from contextlib import contextmanager
import threading

from config.live_config import LiveMonitoringConfig
from monitors.odds_tracker import OddsSnapshot, OddsMovement
from monitors.value_detector import ValueOpportunity

logger = logging.getLogger(__name__)

@dataclass
class PerformanceRecord:
    """Record of betting performance for analysis"""
    opportunity_id: str
    match_id: str
    team: str
    odds: float
    stake: float
    result: Optional[str]  # 'WIN', 'LOSS', 'VOID', None (pending)
    profit: Optional[float]
    recorded_time: datetime
    league: str
    confidence: str
    edge_estimate: float

class OddsDatabase:
    """Manages historical odds data storage and retrieval with connection pooling"""
    
    def __init__(self, db_path: str = None):
        self.config = LiveMonitoringConfig()
        self.db_path = db_path or self.config.DATABASE_PATH
        self.connection: Optional[sqlite3.Connection] = None
        self._connection_lock = threading.Lock()  # Thread-safe connection access
        
        # Connection pool settings
        self.pool_size = 5
        self.pool: List[sqlite3.Connection] = []
        self._pool_lock = threading.Lock()
        
        # Initialize database
        self._initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Thread-safe connection context manager with connection pooling"""
        conn = None
        try:
            # Try to get connection from pool
            with self._pool_lock:
                if self.pool:
                    conn = self.pool.pop()
                else:
                    # Create new connection if pool is empty
                    conn = sqlite3.connect(self.db_path, check_same_thread=False)
                    conn.row_factory = sqlite3.Row
            
            yield conn
            conn.commit()  # Commit on successful completion
            
            # Return connection to pool
            with self._pool_lock:
                if len(self.pool) < self.pool_size:
                    self.pool.append(conn)
                    conn = None  # Don't close if returned to pool
        except Exception:
            if conn:
                conn.rollback()
            raise
        finally:
            # Close connection if not returned to pool
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    async def __aenter__(self):
        """Async context manager entry"""
        try:
            # Database is already initialized in __init__
            logger.info("✅ OddsDatabase async context initialized")
            return self
        except Exception as e:
            logger.error(f"❌ OddsDatabase initialization failed: {e}")
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
            logger.info("✅ OddsDatabase cleaned up successfully")
        except Exception as e:
            logger.error(f"⚠️ Error during OddsDatabase cleanup: {e}")
        return False
    
    def _initialize_database(self):
        """Create database tables if they don't exist"""
        
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            
            # Create tables
            self._create_tables()
            
            logger.info(f"Initialized odds database at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _create_tables(self):
        """Create all required database tables"""
        
        cursor = self.connection.cursor()
        
        # Odds snapshots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS odds_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id TEXT NOT NULL,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                home_odds REAL NOT NULL,
                away_odds REAL NOT NULL,
                timestamp TEXT NOT NULL,
                league TEXT NOT NULL,
                commence_time TEXT NOT NULL,
                bookmaker TEXT DEFAULT 'default'
            )
        ''')
        
        # Odds movements table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS odds_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id TEXT NOT NULL,
                team TEXT NOT NULL,
                old_odds REAL NOT NULL,
                new_odds REAL NOT NULL,
                change_amount REAL NOT NULL,
                change_percentage REAL NOT NULL,
                timestamp TEXT NOT NULL,
                movement_type TEXT NOT NULL,
                significance TEXT NOT NULL
            )
        ''')
        
        # Value opportunities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS value_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id TEXT UNIQUE NOT NULL,
                match_id TEXT NOT NULL,
                team TEXT NOT NULL,
                opponent TEXT NOT NULL,
                odds REAL NOT NULL,
                previous_odds REAL,
                league TEXT NOT NULL,
                commence_time TEXT NOT NULL,
                detected_time TEXT NOT NULL,
                recommended_stake REAL NOT NULL,
                confidence TEXT NOT NULL,
                edge_estimate REAL NOT NULL,
                kelly_fraction REAL NOT NULL,
                urgency_level TEXT NOT NULL,
                priority_score REAL NOT NULL,
                time_sensitivity REAL NOT NULL,
                movement_direction TEXT NOT NULL,
                odds_velocity REAL NOT NULL
            )
        ''')
        
        # Performance records table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id TEXT NOT NULL,
                match_id TEXT NOT NULL,
                team TEXT NOT NULL,
                odds REAL NOT NULL,
                stake REAL NOT NULL,
                result TEXT,
                profit REAL,
                recorded_time TEXT NOT NULL,
                league TEXT NOT NULL,
                confidence TEXT NOT NULL,
                edge_estimate REAL NOT NULL,
                FOREIGN KEY (opportunity_id) REFERENCES value_opportunities (opportunity_id)
            )
        ''')
        
        # System performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                metadata TEXT
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_match_time ON odds_snapshots (match_id, timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_movements_match_time ON odds_movements (match_id, timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_opportunities_detected ON value_opportunities (detected_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_performance_recorded ON performance_records (recorded_time)')
        
        self.connection.commit()
    
    def store_odds_snapshot(self, snapshot: OddsSnapshot):
        """Store an odds snapshot (optimized with connection pooling)"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO odds_snapshots 
                    (match_id, home_team, away_team, home_odds, away_odds, timestamp, 
                     league, commence_time, bookmaker)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    snapshot.match_id,
                    snapshot.home_team,
                    snapshot.away_team,
                    snapshot.home_odds,
                    snapshot.away_odds,
                    snapshot.timestamp.isoformat(),
                    snapshot.league,
                    snapshot.commence_time.isoformat(),
                    snapshot.bookmaker
                ))
            
        except Exception as e:
            logger.error(f"Failed to store odds snapshot: {e}")
    
    def store_odds_snapshots_batch(self, snapshots: List[OddsSnapshot]):
        """Store multiple odds snapshots in a single transaction (batch insert)"""
        
        if not snapshots:
            return
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany('''
                    INSERT INTO odds_snapshots 
                    (match_id, home_team, away_team, home_odds, away_odds, timestamp, 
                     league, commence_time, bookmaker)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', [(
                    s.match_id,
                    s.home_team,
                    s.away_team,
                    s.home_odds,
                    s.away_odds,
                    s.timestamp.isoformat(),
                    s.league,
                    s.commence_time.isoformat(),
                    s.bookmaker
                ) for s in snapshots])
            
            logger.info(f"✅ Batch inserted {len(snapshots)} odds snapshots")
            
        except Exception as e:
            logger.error(f"Failed to store odds snapshots batch: {e}")
    
    def store_odds_movement(self, movement: OddsMovement):
        """Store an odds movement (optimized with connection pooling)"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO odds_movements 
                    (match_id, team, old_odds, new_odds, change_amount, change_percentage,
                     timestamp, movement_type, significance)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    movement.match_id,
                    movement.team,
                    movement.old_odds,
                    movement.new_odds,
                    movement.change,
                    movement.change_percentage,
                    movement.timestamp.isoformat(),
                    movement.movement_type,
                    movement.significance
                ))
            
        except Exception as e:
            logger.error(f"Failed to store odds movement: {e}")
    
    def store_value_opportunity(self, opportunity: ValueOpportunity):
        """Store a value opportunity (optimized with connection pooling)"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO value_opportunities 
                    (opportunity_id, match_id, team, opponent, odds, previous_odds,
                     league, commence_time, detected_time, recommended_stake, confidence,
                     edge_estimate, kelly_fraction, urgency_level, priority_score,
                     time_sensitivity, movement_direction, odds_velocity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    opportunity.match_id,  # Using match_id as opportunity_id
                    opportunity.match_id.split('_')[0],  # Extract base match_id
                    opportunity.team,
                    opportunity.opponent,
                    opportunity.odds,
                    opportunity.previous_odds,
                    opportunity.league,
                    opportunity.commence_time.isoformat(),
                    opportunity.detected_time.isoformat(),
                    opportunity.recommended_stake,
                    opportunity.confidence,
                    opportunity.edge_estimate,
                    opportunity.kelly_fraction,
                    opportunity.urgency_level,
                    opportunity.priority_score,
                    opportunity.time_sensitivity,
                    opportunity.movement_direction,
                    opportunity.odds_velocity
                ))
            
        except Exception as e:
            logger.error(f"Failed to store value opportunity: {e}")
    
    def store_performance_record(self, record: PerformanceRecord):
        """Store a performance record (optimized with connection pooling)"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO performance_records 
                    (opportunity_id, match_id, team, odds, stake, result, profit,
                     recorded_time, league, confidence, edge_estimate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record.opportunity_id,
                    record.match_id,
                    record.team,
                    record.odds,
                    record.stake,
                    record.result,
                    record.profit,
                    record.recorded_time.isoformat(),
                    record.league,
                    record.confidence,
                    record.edge_estimate
                ))
            
        except Exception as e:
            logger.error(f"Failed to store performance record: {e}")
    
    def get_recent_opportunities(self, hours: int = 24) -> List[ValueOpportunity]:
        """Get value opportunities from the last N hours (optimized with connection pooling)"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
                
                cursor.execute('''
                    SELECT * FROM value_opportunities 
                    WHERE detected_time > ? 
                    ORDER BY detected_time DESC
                ''', (cutoff_time,))
                
                opportunities = []
                for row in cursor.fetchall():
                    opportunity = ValueOpportunity(
                        match_id=row['opportunity_id'],
                        team=row['team'],
                        opponent=row['opponent'],
                        odds=row['odds'],
                        previous_odds=row['previous_odds'],
                        league=row['league'],
                        commence_time=datetime.fromisoformat(row['commence_time']),
                        detected_time=datetime.fromisoformat(row['detected_time']),
                        recommended_stake=row['recommended_stake'],
                        confidence=row['confidence'],
                        edge_estimate=row['edge_estimate'],
                        kelly_fraction=row['kelly_fraction'],
                        urgency_level=row['urgency_level'],
                        priority_score=row['priority_score'],
                        time_sensitivity=row['time_sensitivity'],
                        movement_direction=row['movement_direction'],
                        odds_velocity=row['odds_velocity']
                    )
                    opportunities.append(opportunity)
                
                return opportunities
            
        except Exception as e:
            logger.error(f"Failed to get recent opportunities: {e}")
            return []
    
    def get_performance_summary(self, days: int = 30) -> Dict:
        """Get performance summary for the last N days (optimized with connection pooling)"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()
                
                # Get basic stats
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_bets,
                        COUNT(CASE WHEN result = 'WIN' THEN 1 END) as wins,
                        COUNT(CASE WHEN result = 'LOSS' THEN 1 END) as losses,
                        SUM(stake) as total_staked,
                        SUM(CASE WHEN profit IS NOT NULL THEN profit ELSE 0 END) as total_profit,
                        AVG(odds) as avg_odds,
                        AVG(edge_estimate) as avg_edge
                    FROM performance_records 
                    WHERE recorded_time > ?
                ''', (cutoff_time,))
                
                row = cursor.fetchone()
                
                total_bets = row['total_bets'] or 0
                wins = row['wins'] or 0
                losses = row['losses'] or 0
                total_staked = row['total_staked'] or 0
                total_profit = row['total_profit'] or 0
                
                # Calculate derived metrics
                win_rate = (wins / max(wins + losses, 1)) * 100
                roi = (total_profit / max(total_staked, 1)) * 100
                
                # Get league breakdown
                cursor.execute('''
                    SELECT league, COUNT(*) as count, AVG(edge_estimate) as avg_edge
                    FROM performance_records 
                    WHERE recorded_time > ?
                    GROUP BY league
                    ORDER BY count DESC
                ''', (cutoff_time,))
                
                league_breakdown = {}
                for row in cursor.fetchall():
                    league_breakdown[row['league']] = {
                        'count': row['count'],
                        'avg_edge': row['avg_edge']
                    }
                
                return {
                    'total_bets': total_bets,
                    'wins': wins,
                    'losses': losses,
                    'win_rate': round(win_rate, 2),
                    'total_staked': round(total_staked, 2),
                    'total_profit': round(total_profit, 2),
                    'roi': round(roi, 2),
                    'avg_odds': round(row['avg_odds'] or 0, 2),
                    'avg_edge': round(row['avg_edge'] or 0, 2),
                    'league_breakdown': league_breakdown
                }
            
        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {}
    
    def get_odds_history(self, match_id: str) -> List[OddsSnapshot]:
        """Get odds history for a specific match (optimized with connection pooling)"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM odds_snapshots 
                    WHERE match_id = ? 
                    ORDER BY timestamp ASC
                ''', (match_id,))
                
                snapshots = []
                for row in cursor.fetchall():
                    snapshot = OddsSnapshot(
                        match_id=row['match_id'],
                        home_team=row['home_team'],
                        away_team=row['away_team'],
                        home_odds=row['home_odds'],
                        away_odds=row['away_odds'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        league=row['league'],
                        commence_time=datetime.fromisoformat(row['commence_time']),
                        bookmaker=row['bookmaker']
                    )
                    snapshots.append(snapshot)
                
                return snapshots
            
        except Exception as e:
            logger.error(f"Failed to get odds history for {match_id}: {e}")
            return []
    
    def cleanup_old_data(self):
        """Clean up old data based on retention policy"""
        
        try:
            cursor = self.connection.cursor()
            cutoff_time = (datetime.now() - timedelta(days=self.config.MAX_HISTORY_DAYS)).isoformat()
            
            # Clean up old snapshots
            cursor.execute('DELETE FROM odds_snapshots WHERE timestamp < ?', (cutoff_time,))
            snapshots_deleted = cursor.rowcount
            
            # Clean up old movements
            cursor.execute('DELETE FROM odds_movements WHERE timestamp < ?', (cutoff_time,))
            movements_deleted = cursor.rowcount
            
            # Clean up old opportunities (keep performance records)
            cursor.execute('DELETE FROM value_opportunities WHERE detected_time < ?', (cutoff_time,))
            opportunities_deleted = cursor.rowcount
            
            self.connection.commit()
            
            logger.info(f"Cleaned up old data: {snapshots_deleted} snapshots, "
                       f"{movements_deleted} movements, {opportunities_deleted} opportunities")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
    
    def backup_database(self, backup_path: str = None):
        """Create a backup of the database"""
        
        if not backup_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"{self.db_path}.backup_{timestamp}"
        
        try:
            # Create backup using sqlite3 backup API
            backup_conn = sqlite3.connect(backup_path)
            self.connection.backup(backup_conn)
            backup_conn.close()
            
            logger.info(f"Database backed up to {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return None
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        
        try:
            cursor = self.connection.cursor()
            
            stats = {}
            
            # Count records in each table
            tables = ['odds_snapshots', 'odds_movements', 'value_opportunities', 'performance_records']
            for table in tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                stats[f'{table}_count'] = cursor.fetchone()[0]
            
            # Get database file size
            if os.path.exists(self.db_path):
                stats['database_size_mb'] = round(os.path.getsize(self.db_path) / (1024 * 1024), 2)
            
            # Get date range of data
            cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM odds_snapshots')
            row = cursor.fetchone()
            if row[0] and row[1]:
                stats['data_range_start'] = row[0]
                stats['data_range_end'] = row[1]
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
    
    def close(self):
        """Close database connection and connection pool"""
        # Close main connection
        if self.connection:
            self.connection.close()
            self.connection = None
        
        # Close all connections in pool
        with self._pool_lock:
            for conn in self.pool:
                try:
                    conn.close()
                except:
                    pass
            self.pool.clear()
        
        logger.info("Database connection and pool closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
