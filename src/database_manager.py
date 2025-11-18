import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

import aiosqlite


class DatabaseManager:
    """
    Async SQLite database manager for the betting intelligence system.

    Usage:

        async with DatabaseManager() as db:
            rows = await db.execute_query("SELECT 1 AS value")
    """

    def __init__(self, db_path: str = "data/betting_system.db") -> None:
        self.db_path = Path(db_path)
        # Ensure the parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.connection: aiosqlite.Connection | None = None

    async def __aenter__(self) -> "DatabaseManager":
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        await self.close()
        # Do not suppress exceptions
        return False

    async def initialize(self) -> None:
        """
        Initialize database connection and ensure required tables exist.
        """
        try:
            self.connection = await aiosqlite.connect(str(self.db_path))
            # Row factory to make results easier to work with if needed
            self.connection.row_factory = aiosqlite.Row
            await self.create_tables()
            self.logger.info("✅ Database initialized successfully at %s", self.db_path)
        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.error("❌ Database initialization failed: %s", exc)
            raise

    async def create_tables(self) -> None:
        """
        Create all necessary tables if they do not already exist.
        """
        assert self.connection is not None, "Database not initialized"

        tables: Tuple[str, ...] = (
            """
            CREATE TABLE IF NOT EXISTS soccer_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                league TEXT,
                match_time TIMESTAMP,
                odds_home REAL,
                odds_draw REAL,
                odds_away REAL,
                status TEXT DEFAULT 'scheduled',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS tennis_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player1 TEXT NOT NULL,
                player2 TEXT NOT NULL,
                tournament TEXT,
                surface TEXT,
                match_time TIMESTAMP,
                odds_player1 REAL,
                odds_player2 REAL,
                status TEXT DEFAULT 'scheduled',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER,
                sport TEXT,
                prediction_type TEXT,
                predicted_outcome TEXT,
                confidence REAL,
                expected_value REAL,
                kelly_stake REAL,
                ai_reasoning TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE,
                sport TEXT,
                opportunities_found INTEGER DEFAULT 0,
                bets_placed INTEGER DEFAULT 0,
                profit_loss REAL DEFAULT 0.0,
                roi_percentage REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
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
            """,
            """
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
            """,
        )

        for sql in tables:
            await self.connection.execute(sql)

        await self.connection.commit()
        self.logger.info("✅ Database tables created/verified")

    async def close(self) -> None:
        """
        Close the underlying database connection.
        """
        if self.connection is not None:
            await self.connection.close()
            self.logger.info("✅ Database connection closed")
            self.connection = None

    async def execute_query(self, query: str, params: Tuple[Any, ...] = ()) -> List[Dict]:
        """
        Execute a SELECT-style query and return rows as a list of dicts.
        """
        if self.connection is None:
            raise RuntimeError("Database not initialized")

        async with self.connection.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            # aiosqlite.Row supports dict-like access; convert explicitly to dicts
            return [dict(row) for row in rows]

    async def execute_non_query(
        self, query: str, params: Tuple[Any, ...] = ()
    ) -> None:
        """
        Execute a non-SELECT query (INSERT/UPDATE/DELETE).
        """
        if self.connection is None:
            raise RuntimeError("Database not initialized")

        await self.connection.execute(query, params)
        await self.connection.commit()

    async def insert_match(self, sport: str, match_data: Dict[str, Any]) -> int:
        """
        Insert match data and return the new match ID.

        Args:
            sport: 'soccer' or 'tennis'.
            match_data: dict containing the relevant match fields.
        """
        if self.connection is None:
            raise RuntimeError("Database not initialized")

        if sport.lower() == "soccer":
            query = """
                INSERT INTO soccer_matches
                    (home_team, away_team, league, match_time,
                     odds_home, odds_draw, odds_away)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params: Tuple[Any, ...] = (
                match_data["home_team"],
                match_data["away_team"],
                match_data.get("league"),
                match_data.get("match_time"),
                match_data.get("odds_home"),
                match_data.get("odds_draw"),
                match_data.get("odds_away"),
            )
        else:
            # Default to tennis if not explicitly soccer
            query = """
                INSERT INTO tennis_matches
                    (player1, player2, tournament, surface, match_time,
                     odds_player1, odds_player2)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                match_data["player1"],
                match_data["player2"],
                match_data.get("tournament"),
                match_data.get("surface"),
                match_data.get("match_time"),
                match_data.get("odds_player1"),
                match_data.get("odds_player2"),
            )

        cursor = await self.connection.execute(query, params)
        await self.connection.commit()
        return cursor.lastrowid


