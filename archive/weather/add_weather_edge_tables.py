"""
Database migration: Add weather edge tracking tables
"""

import asyncio
import logging
from src.database_manager import DatabaseManager


logger = logging.getLogger(__name__)


async def create_weather_edge_tables():
    """Create tables for weather edge tracking"""
    
    try:
        async with DatabaseManager() as db:
            # Weather edge opportunities table
            await db.execute_non_query("""
                CREATE TABLE IF NOT EXISTS weather_edge_opportunities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id TEXT NOT NULL,
                    sport TEXT NOT NULL,
                    edge_type TEXT NOT NULL,
                    edge_strength REAL NOT NULL,
                    urgency TEXT NOT NULL,
                    recommended_stake REAL,
                    expected_profit REAL,
                    time_window_minutes INTEGER,
                    weather_conditions TEXT,
                    betting_recommendations TEXT,
                    actual_outcome TEXT,
                    actual_profit REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP
                )
            """)
            
            # Weather edge performance tracking
            await db.execute_non_query("""
                CREATE TABLE IF NOT EXISTS weather_edge_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    total_edges_detected INTEGER DEFAULT 0,
                    critical_edges INTEGER DEFAULT 0,
                    edges_acted_on INTEGER DEFAULT 0,
                    total_stake_deployed REAL DEFAULT 0.0,
                    total_profit REAL DEFAULT 0.0,
                    roi_percentage REAL DEFAULT 0.0,
                    best_edge_type TEXT,
                    best_edge_strength REAL,
                    session_duration_minutes INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Add location/venue fields to existing tables if they don't exist
            # Check if columns exist first (SQLite doesn't support IF NOT EXISTS for columns)
            try:
                await db.execute_non_query("""
                    ALTER TABLE soccer_matches ADD COLUMN venue TEXT
                """)
            except Exception:
                pass  # Column might already exist
            
            try:
                await db.execute_non_query("""
                    ALTER TABLE soccer_matches ADD COLUMN city TEXT
                """)
            except Exception:
                pass  # Column might already exist
            
            try:
                await db.execute_non_query("""
                    ALTER TABLE tennis_matches ADD COLUMN venue TEXT
                """)
            except Exception:
                pass  # Column might already exist
            
            try:
                await db.execute_non_query("""
                    ALTER TABLE tennis_matches ADD COLUMN city TEXT
                """)
            except Exception:
                pass  # Column might already exist
            
            logger.info("✅ Weather edge tracking tables created successfully")
            print("✅ Weather edge tracking tables created successfully")
            
    except Exception as e:
        logger.error(f"❌ Error creating weather edge tables: {e}")
        print(f"❌ Error creating weather edge tables: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(create_weather_edge_tables())

