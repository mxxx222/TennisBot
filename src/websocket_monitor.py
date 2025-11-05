"""
WebSocket Monitoring System for Real-time Data (Educational Purpose)
====================================================================

This module provides WebSocket monitoring capabilities for educational research
of real-time sports data streams.

DISCLAIMER: This is for educational/research purposes only.
WebSocket connections are for learning and analysis, not actual betting.
"""

import asyncio
import json
import websockets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import logging
from urllib.parse import urlparse
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class WebSocketMessage:
    """WebSocket message structure"""
    timestamp: str
    message_type: str
    data: Dict[str, Any]
    connection_id: str
    educational_note: str

@dataclass
class ConnectionConfig:
    """WebSocket connection configuration"""
    url: str
    protocols: List[str]
    max_reconnects: int
    reconnect_delay: float
    message_timeout: float
    ping_interval: float

class EducationalWebSocketMonitor:
    """WebSocket monitoring system for educational research"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        
        # Connection management
        self.connections = {}
        self.message_handlers = {}
        self.rate_limiter = RateLimiter()
        
        # Educational monitoring
        self.educational_mode = True
        self.data_collection = True
        self.anonymize_data = True
        
        # Statistics
        self.stats = {
            'connections_established': 0,
            'messages_received': 0,
            'messages_sent': 0,
            'reconnections': 0,
            'errors': 0,
            'data_points_collected': 0
        }
        
        self._setup_logging()
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for educational use"""
        return {
            'websocket': {
                'enabled': True,
                'max_connections': 3,  # Conservative limit
                'connection_timeout': 10,
                'message_timeout': 30,
                'ping_interval': 20,
                'max_reconnect_attempts': 5
            },
            'educational_endpoints': {
                # These are examples for educational purposes
                'sports_stream': 'wss://example.com/sports/stream',
                'odds_updates': 'wss://example.com/odds/updates'
            },
            'rate_limits': {
                'messages_per_minute': 100,
                'connections_per_hour': 10
            }
        }
    
    def _setup_logging(self):
        """Setup logging for WebSocket monitoring"""
        logger.setLevel(logging.INFO)
        
        # Don't add duplicate handlers if they already exist
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    
    def add_message_handler(self, message_type: str, handler: Callable):
        """Add handler for specific message types"""
        self.message_handlers[message_type] = handler
        logger.info(f"Added handler for message type: {message_type}")
    
    async def monitor_websocket(self, name: str, config: ConnectionConfig) -> bool:
        """
        Monitor a WebSocket connection for educational purposes
        
        Args:
            name: Identifier for the connection
            config: Connection configuration
            
        Returns:
            True if connection established successfully
        """
        try:
            logger.info(f"Setting up WebSocket monitoring: {name}")
            
            # Create unique connection ID
            connection_id = self._generate_connection_id(name, config.url)
            
            # Initialize connection state
            self.connections[connection_id] = {
                'name': name,
                'config': config,
                'status': 'connecting',
                'last_message': None,
                'message_count': 0,
                'reconnect_count': 0,
                'educational_purpose': True
            }
            
            # Start monitoring task
            asyncio.create_task(self._monitor_connection(connection_id))
            
            self.stats['connections_established'] += 1
            logger.info(f"WebSocket monitoring started: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup WebSocket monitoring {name}: {e}")
            self.stats['errors'] += 1
            return False
    
    async def _monitor_connection(self, connection_id: str):
        """Monitor individual WebSocket connection"""
        conn = self.connections[connection_id]
        config = conn['config']
        reconnect_attempts = 0
        
        while reconnect_attempts < config.max_reconnects:
            try:
                # Connect to WebSocket
                async with websockets.connect(
                    config.url,
                    protocols=config.protocols,
                    timeout=config.message_timeout
                ) as websocket:
                    
                    conn['status'] = 'connected'
                    logger.info(f"WebSocket connected: {connection_id}")
                    
                    # Start ping task
                    ping_task = asyncio.create_task(
                        self._ping_websocket(websocket, config.ping_interval, connection_id)
                    )
                    
                    # Handle messages
                    try:
                        async for message in websocket:
                            await self._handle_message(websocket, message, connection_id)
                            
                    except websockets.exceptions.ConnectionClosed:
                        logger.info(f"WebSocket connection closed: {connection_id}")
                        break
                    
                    except Exception as e:
                        logger.error(f"WebSocket error for {connection_id}: {e}")
                        self.stats['errors'] += 1
                        break
                    
                    finally:
                        ping_task.cancel()
                        
            except Exception as e:
                reconnect_attempts += 1
                conn['reconnect_count'] = reconnect_attempts
                
                logger.warning(
                    f"WebSocket connection failed {connection_id} "
                    f"(attempt {reconnect_attempts}/{config.max_reconnects}): {e}"
                )
                
                if reconnect_attempts < config.max_reconnects:
                    # Exponential backoff with educational delay
                    delay = min(config.reconnect_delay * (2 ** reconnect_attempts), 60)
                    logger.info(f"Reconnecting in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Max reconnection attempts reached for {connection_id}")
                    conn['status'] = 'failed'
                    break
        
        # Cleanup
        if connection_id in self.connections:
            self.connections[connection_id]['status'] = 'disconnected'
    
    async def _handle_message(self, websocket, message: str, connection_id: str):
        """Handle incoming WebSocket message"""
        try:
            # Parse message
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON message from {connection_id}")
                return
            
            # Create WebSocket message object
            ws_message = WebSocketMessage(
                timestamp=datetime.now().isoformat(),
                message_type=data.get('type', 'unknown'),
                data=self._anonymize_data(data),
                connection_id=connection_id,
                educational_note="Educational research data"
            )
            
            # Update statistics
            self.connections[connection_id]['message_count'] += 1
            self.stats['messages_received'] += 1
            self.stats['data_points_collected'] += 1
            
            # Check rate limits
            if not await self.rate_limiter.check_rate_limit(connection_id):
                logger.warning(f"Rate limit exceeded for {connection_id}")
                return
            
            # Handle message by type
            message_type = ws_message.message_type
            if message_type in self.message_handlers:
                await self.message_handlers[message_type](ws_message)
            else:
                logger.debug(f"No handler for message type: {message_type}")
            
            # Log for educational purposes
            logger.debug(f"Processed message from {connection_id}: {message_type}")
            
            # Update last message time
            self.connections[connection_id]['last_message'] = ws_message.timestamp
            
        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")
            self.stats['errors'] += 1
    
    async def _ping_websocket(self, websocket, interval: float, connection_id: str):
        """Send periodic ping messages"""
        try:
            while True:
                await asyncio.sleep(interval)
                if websocket.open:
                    await websocket.ping()
                    self.stats['messages_sent'] += 1
                else:
                    break
        except Exception as e:
            logger.debug(f"Ping error for {connection_id}: {e}")
    
    def _anonymize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize data for educational privacy"""
        if not self.anonymize_data:
            return data
        
        # Create a copy to avoid modifying original
        anonymized = data.copy()
        
        # Anonymize identifiers
        for key, value in anonymized.items():
            if 'id' in key.lower() and isinstance(value, str):
                anonymized[key] = f"anon_{hash(value) % 10000:04d}"
            elif 'team' in key.lower() and isinstance(value, str):
                anonymized[key] = f"Team_{hash(value) % 100:02d}"
        
        return anonymized
    
    def _generate_connection_id(self, name: str, url: str) -> str:
        """Generate unique connection identifier"""
        combined = f"{name}_{url}_{datetime.now().timestamp()}"
        return hashlib.md5(combined.encode()).hexdigest()[:8]
    
    async def send_educational_message(self, connection_id: str, message_type: str, 
                                     data: Dict[str, Any]) -> bool:
        """
        Send educational message to WebSocket
        
        Args:
            connection_id: Target connection
            message_type: Type of message
            data: Message data
            
        Returns:
            True if sent successfully
        """
        try:
            # Check if connection exists and is active
            if connection_id not in self.connections:
                logger.warning(f"Connection {connection_id} not found")
                return False
            
            conn = self.connections[connection_id]
            if conn['status'] != 'connected':
                logger.warning(f"Connection {connection_id} not active")
                return False
            
            # Educational message structure
            educational_message = {
                'type': message_type,
                'data': data,
                'educational_purpose': True,
                'timestamp': datetime.now().isoformat(),
                'note': 'Educational research communication'
            }
            
            message_json = json.dumps(educational_message)
            
            # Send message (implementation would use actual websocket connection)
            # For educational purposes, we'll simulate this
            logger.info(f"Sending educational message to {connection_id}: {message_type}")
            
            self.stats['messages_sent'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to {connection_id}: {e}")
            self.stats['errors'] += 1
            return False
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get status of all WebSocket connections"""
        status = {}
        
        for conn_id, conn_data in self.connections.items():
            status[conn_id] = {
                'name': conn_data['name'],
                'status': conn_data['status'],
                'url': conn_data['config'].url,
                'message_count': conn_data['message_count'],
                'reconnect_count': conn_data['reconnect_count'],
                'last_message': conn_data['last_message'],
                'educational_purpose': conn_data.get('educational_purpose', True)
            }
        
        return status
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get WebSocket monitoring statistics"""
        return {
            'connections': self.stats.copy(),
            'active_connections': len([c for c in self.connections.values() 
                                     if c['status'] == 'connected']),
            'rate_limiter_status': self.rate_limiter.get_status(),
            'educational_mode': self.educational_mode
        }

class RateLimiter:
    """Rate limiter for WebSocket messages"""
    
    def __init__(self, messages_per_minute: int = 100):
        self.messages_per_minute = messages_per_minute
        self.message_counts = {}
        self.last_reset = datetime.now()
    
    async def check_rate_limit(self, connection_id: str) -> bool:
        """Check if message is within rate limits"""
        now = datetime.now()
        
        # Reset counter every minute
        if (now - self.last_reset).total_seconds() >= 60:
            self.message_counts.clear()
            self.last_reset = now
        
        # Check connection limit
        current_count = self.message_counts.get(connection_id, 0)
        
        if current_count >= self.messages_per_minute:
            return False
        
        # Increment counter
        self.message_counts[connection_id] = current_count + 1
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get rate limiter status"""
        return {
            'messages_per_minute': self.messages_per_minute,
            'active_connections': len(self.message_counts),
            'last_reset': self.last_reset.isoformat()
        }

class SportsDataAnalyzer:
    """Analyze sports data from WebSocket streams (educational)"""
    
    def __init__(self, monitor: EducationalWebSocketMonitor):
        self.monitor = monitor
        self.data_buffer = []
        self.analysis_results = {}
        
        # Register message handlers
        monitor.add_message_handler('odds_update', self._handle_odds_update)
        monitor.add_message_handler('match_event', self._handle_match_event)
        monitor.add_message_handler('score_update', self._handle_score_update)
    
    async def _handle_odds_update(self, message: WebSocketMessage):
        """Handle odds update messages"""
        try:
            data = message.data
            
            # Educational analysis of odds movements
            analysis = {
                'timestamp': message.timestamp,
                'match_id': data.get('match_id', 'unknown'),
                'odds_change': self._calculate_odds_change(data),
                'market': data.get('market', 'unknown'),
                'educational_note': 'Odds movement analysis for research'
            }
            
            self.data_buffer.append(analysis)
            self.analysis_results['odds_updates'] = len(self.data_buffer)
            
            logger.info(f"Processed odds update: {analysis['match_id']}")
            
        except Exception as e:
            logger.error(f"Error handling odds update: {e}")
    
    async def _handle_match_event(self, message: WebSocketMessage):
        """Handle match event messages"""
        try:
            data = message.data
            
            # Educational event analysis
            event_analysis = {
                'timestamp': message.timestamp,
                'event_type': data.get('event_type', 'unknown'),
                'match_id': data.get('match_id', 'unknown'),
                'minute': data.get('minute', 0),
                'educational_analysis': 'Event pattern analysis'
            }
            
            self.data_buffer.append(event_analysis)
            
            logger.info(f"Processed match event: {data.get('event_type', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Error handling match event: {e}")
    
    async def _handle_score_update(self, message: WebSocketMessage):
        """Handle score update messages"""
        try:
            data = message.data
            
            # Educational score analysis
            score_analysis = {
                'timestamp': message.timestamp,
                'match_id': data.get('match_id', 'unknown'),
                'home_score': data.get('home_score', 0),
                'away_score': data.get('away_score', 0),
                'total_goals': data.get('home_score', 0) + data.get('away_score', 0),
                'educational_note': 'Score progression analysis'
            }
            
            self.data_buffer.append(score_analysis)
            
            logger.info(f"Processed score update: {score_analysis['home_score']}-{score_analysis['away_score']}")
            
        except Exception as e:
            logger.error(f"Error handling score update: {e}")
    
    def _calculate_odds_change(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate odds changes (educational algorithm)"""
        current_odds = data.get('current_odds', {})
        previous_odds = data.get('previous_odds', {})
        
        changes = {}
        for market in current_odds:
            if market in previous_odds:
                changes[market] = current_odds[market] - previous_odds[market]
        
        return changes
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of analysis results"""
        return {
            'total_data_points': len(self.data_buffer),
            'analysis_types': list(self.analysis_results.keys()),
            'buffer_size': len(self.data_buffer),
            'educational_purpose': 'Sports data pattern analysis'
        }

# Educational example
async def educational_websocket_example():
    """Demonstrate WebSocket monitoring for educational purposes"""
    
    print("🔌 Starting educational WebSocket monitoring demonstration...")
    print("⚠️  This is for learning purposes only!")
    
    # Create WebSocket monitor
    monitor = EducationalWebSocketMonitor()
    
    # Create sports data analyzer
    analyzer = SportsDataAnalyzer(monitor)
    
    print("✅ WebSocket monitoring system initialized")
    print("   • Educational mode: Active")
    print("   • Rate limiting: Enabled")
    print("   • Data anonymization: Active")
    
    # Example connection configuration (educational endpoints)
    config = ConnectionConfig(
        url="wss://example.com/educational/sports",  # Example URL
        protocols=["sports-stream"],
        max_reconnects=3,
        reconnect_delay=5.0,
        message_timeout=30.0,
        ping_interval=20.0
    )
    
    # Start monitoring (in demo mode, this would be simulated)
    print("\n📡 Starting WebSocket monitoring simulation...")
    
    # Simulate connection status
    status = monitor.get_connection_status()
    print(f"   Connection status: {len(status)} active")
    
    # Show statistics
    stats = monitor.get_statistics()
    print(f"   Statistics: {stats}")
    
    # Show analysis summary
    summary = analyzer.get_analysis_summary()
    print(f"   Analysis summary: {summary}")
    
    print("\n💡 Educational Notes:")
    print("   • WebSocket monitoring for real-time data streams")
    print("   • Rate limiting prevents system overload")
    print("   • Data anonymization protects privacy")
    print("   • Educational analysis only, no actual betting")

if __name__ == "__main__":
    # Run educational example
    asyncio.run(educational_websocket_example())