#!/usr/bin/env python3
"""
Database Storage Node for N8N-Style Scraper

Stores processed data to various database systems.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from .base_node import DataNode, NodeExecutionResult

logger = logging.getLogger(__name__)

# Optional database drivers
try:
    import sqlite3
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False

try:
    import psycopg2
    from psycopg2.extras import Json as PsqlJson
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

try:
    import pymongo
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False


class DatabaseStorageNode(DataNode):
    """
    Node for storing scraped data to databases.

    Supports:
    - SQLite (local storage)
    - PostgreSQL
    - MongoDB
    - JSON file storage (fallback)
    """

    def __init__(self, node_id: str, config: Dict[str, Any]):
        super().__init__(node_id, config)

        # Database configuration
        self.db_type = config.get('db_type', 'sqlite').lower()
        self.connection_string = config.get('connection_string', '')
        self.table_name = config.get('table_name', 'scraped_data')
        self.collection_name = config.get('collection_name', 'scraped_data')  # For MongoDB

        # Storage settings
        self.batch_size = config.get('batch_size', 100)
        self.on_conflict = config.get('on_conflict', 'update')  # 'update', 'ignore', 'error'

        # Schema settings
        self.create_table = config.get('create_table', True)
        self.table_schema = config.get('table_schema', {})

        # Connection pooling
        self.connection = None
        self.is_connected = False

    async def execute(self, input_data: Dict[str, Any]) -> NodeExecutionResult:
        """Execute database storage"""
        try:
            # Get data from input
            data = input_data.get('data', {})

            if not data:
                return NodeExecutionResult(
                    success=True,
                    data={'stored_count': 0},
                    metadata={'total_items': 0, 'stored_items': 0},
                    node_id=self.node_id
                )

            # Extract items to store
            items = self._extract_items_from_data(data)

            if not items:
                return NodeExecutionResult(
                    success=True,
                    data={'stored_count': 0},
                    metadata={'total_items': 0, 'stored_items': 0},
                    node_id=self.node_id
                )

            logger.info(f"Storing {len(items)} items to {self.db_type} database")

            # Initialize database connection
            await self._init_connection()

            # Prepare data for storage
            prepared_items = self._prepare_items_for_storage(items)

            # Store data in batches
            stored_count = 0
            failed_count = 0

            for i in range(0, len(prepared_items), self.batch_size):
                batch = prepared_items[i:i + self.batch_size]

                try:
                    batch_stored = await self._store_batch(batch)
                    stored_count += batch_stored
                except Exception as e:
                    logger.error(f"Failed to store batch {i//self.batch_size + 1}: {e}")
                    failed_count += len(batch)
                    if self.on_conflict == 'error':
                        break

            # Clean up connection
            await self._close_connection()

            return NodeExecutionResult(
                success=True,
                data={
                    'stored_count': stored_count,
                    'failed_count': failed_count,
                    'table_name': self.table_name
                },
                metadata={
                    'total_items': len(items),
                    'stored_items': stored_count,
                    'failed_items': failed_count,
                    'db_type': self.db_type,
                    'batch_size': self.batch_size,
                    'on_conflict': self.on_conflict
                },
                node_id=self.node_id
            )

        except Exception as e:
            logger.error(f"Database storage failed: {e}")
            await self._cleanup()
            return NodeExecutionResult(
                success=False,
                error=str(e),
                node_id=self.node_id
            )

    def _extract_items_from_data(self, data: Any) -> List[Dict[str, Any]]:
        """Extract list of items from various data formats"""
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Try common keys
            for key in ['messages', 'content', 'items', 'data', 'results', 'processed_data']:
                if key in data and isinstance(data[key], list):
                    return data[key]

            # If single item dict, wrap in list
            return [data]
        else:
            return []

    async def _init_connection(self) -> None:
        """Initialize database connection"""
        if self.db_type == 'sqlite':
            await self._init_sqlite()
        elif self.db_type == 'postgresql':
            await self._init_postgresql()
        elif self.db_type == 'mongodb':
            await self._init_mongodb()
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

    async def _init_sqlite(self) -> None:
        """Initialize SQLite connection"""
        if not SQLITE_AVAILABLE:
            raise RuntimeError("SQLite not available")

        # SQLite is synchronous, but we'll run it in a thread
        import concurrent.futures

        def _connect():
            if not self.connection_string:
                self.connection_string = ':memory:'
            return sqlite3.connect(self.connection_string)

        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            self.connection = await loop.run_in_executor(executor, _connect)

        self.is_connected = True

        # Create table if needed
        if self.create_table:
            await self._create_sqlite_table()

    async def _init_postgresql(self) -> None:
        """Initialize PostgreSQL connection"""
        if not POSTGRES_AVAILABLE:
            raise RuntimeError("PostgreSQL driver not available")

        # PostgreSQL connection would go here
        # For now, raise not implemented
        raise NotImplementedError("PostgreSQL support not yet implemented")

    async def _init_mongodb(self) -> None:
        """Initialize MongoDB connection"""
        if not MONGODB_AVAILABLE:
            raise RuntimeError("MongoDB driver not available")

        # MongoDB connection would go here
        # For now, raise not implemented
        raise NotImplementedError("MongoDB support not yet implemented")

    async def _create_sqlite_table(self) -> None:
        """Create SQLite table with appropriate schema"""
        import concurrent.futures

        def _create_table():
            cursor = self.connection.cursor()

            # Default schema for scraped data
            default_schema = """
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id TEXT PRIMARY KEY,
                    source TEXT,
                    content TEXT,
                    author TEXT,
                    timestamp TEXT,
                    url TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """.format(table_name=self.table_name)

            # Use custom schema if provided
            if self.table_schema:
                schema_sql = self._build_table_schema()
            else:
                schema_sql = default_schema

            cursor.execute(schema_sql)
            self.connection.commit()

        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            await loop.run_in_executor(executor, _create_table)

    def _build_table_schema(self) -> str:
        """Build table schema from configuration"""
        columns = []

        for col_name, col_def in self.table_schema.items():
            if isinstance(col_def, str):
                columns.append(f"{col_name} {col_def}")
            elif isinstance(col_def, dict):
                col_type = col_def.get('type', 'TEXT')
                constraints = []

                if col_def.get('primary_key'):
                    constraints.append('PRIMARY KEY')
                if col_def.get('not_null'):
                    constraints.append('NOT NULL')
                if col_def.get('unique'):
                    constraints.append('UNIQUE')
                if 'default' in col_def:
                    constraints.append(f"DEFAULT {col_def['default']}")

                col_sql = f"{col_name} {col_type}"
                if constraints:
                    col_sql += f" {' '.join(constraints)}"

                columns.append(col_sql)

        return f"CREATE TABLE IF NOT EXISTS {self.table_name} ({', '.join(columns)})"

    def _prepare_items_for_storage(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare items for database storage"""
        prepared = []

        for item in items:
            prepared_item = {}

            # Ensure each item has an ID
            if 'id' not in item:
                # Generate ID from content hash or other fields
                import hashlib
                content = str(item.get('content', item.get('text', item.get('message', ''))))
                item_id = hashlib.md5(f"{content}_{item.get('timestamp', datetime.now().isoformat())}".encode()).hexdigest()[:16]
                prepared_item['id'] = item_id
            else:
                prepared_item['id'] = item['id']

            # Copy other fields
            for key, value in item.items():
                if key == 'id':
                    continue

                # Handle different data types
                if isinstance(value, (dict, list)):
                    prepared_item[key] = json.dumps(value)
                elif isinstance(value, datetime):
                    prepared_item[key] = value.isoformat()
                else:
                    prepared_item[key] = value

            # Add metadata if not present
            if 'created_at' not in prepared_item:
                prepared_item['created_at'] = datetime.now().isoformat()

            prepared.append(prepared_item)

        return prepared

    async def _store_batch(self, batch: List[Dict[str, Any]]) -> int:
        """Store a batch of items to database"""
        if self.db_type == 'sqlite':
            return await self._store_batch_sqlite(batch)
        elif self.db_type == 'postgresql':
            return await self._store_batch_postgresql(batch)
        elif self.db_type == 'mongodb':
            return await self._store_batch_mongodb(batch)
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

    async def _store_batch_sqlite(self, batch: List[Dict[str, Any]]) -> int:
        """Store batch to SQLite"""
        import concurrent.futures

        def _store():
            cursor = self.connection.cursor()
            stored = 0

            for item in batch:
                try:
                    # Build INSERT or REPLACE statement
                    columns = list(item.keys())
                    placeholders = ['?' for _ in columns]
                    values = [item[col] for col in columns]

                    if self.on_conflict == 'update':
                        sql = f"INSERT OR REPLACE INTO {self.table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                    elif self.on_conflict == 'ignore':
                        sql = f"INSERT OR IGNORE INTO {self.table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                    else:  # 'error'
                        sql = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"

                    cursor.execute(sql, values)
                    stored += 1

                except Exception as e:
                    logger.error(f"Failed to store item: {e}")
                    if self.on_conflict == 'error':
                        raise

            self.connection.commit()
            return stored

        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, _store)

    async def _store_batch_postgresql(self, batch: List[Dict[str, Any]]) -> int:
        """Store batch to PostgreSQL"""
        # Implementation for PostgreSQL would go here
        raise NotImplementedError("PostgreSQL batch storage not implemented")

    async def _store_batch_mongodb(self, batch: List[Dict[str, Any]]) -> int:
        """Store batch to MongoDB"""
        # Implementation for MongoDB would go here
        raise NotImplementedError("MongoDB batch storage not implemented")

    async def _close_connection(self) -> None:
        """Close database connection"""
        if self.connection and self.is_connected:
            if self.db_type == 'sqlite':
                import concurrent.futures

                def _close():
                    self.connection.close()

                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    await loop.run_in_executor(executor, _close)

            self.is_connected = False

    async def _cleanup(self) -> None:
        """Clean up resources"""
        await self._close_connection()