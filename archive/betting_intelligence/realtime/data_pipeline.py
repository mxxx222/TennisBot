#!/usr/bin/env python3
"""
🎯 REAL-TIME DATA PIPELINE
==========================

Advanced real-time data pipeline for sports analytics
Combines web scraping, API calls, and live data streams

Features:
- Real-time live score updates
- Streaming odds changes
- Social media sentiment analysis
- News feed aggregation
- Weather and venue updates
- Player tracking and statistics
- Market movement analysis

Author: Advanced Analytics Pipeline
Version: 4.0.0
"""

import asyncio
import aiohttp
import websockets
import json
import time
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque
import threading
import queue
import redis
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd
import numpy as np
from kafka import KafkaProducer, KafkaConsumer
import tweepy
import requests
from bs4 import BeautifulSoup
import re

Base = declarative_base()

@dataclass
class RealTimeEvent:
    event_id: str
    sport: str
    event_type: str  # 'score_update', 'odds_change', 'news', 'social'
    timestamp: datetime
    data: Dict[str, Any]
    priority: int = 1  # 1=low, 5=critical
    source: str = ""
    processed: bool = False

@dataclass
class LiveMatch:
    match_id: str
    sport: str
    home_team: str
    away_team: str
    score: str
    status: str
    minute: int
    odds: Dict[str, float]
    last_update: datetime
    events: List[Dict] = field(default_factory=list)

@dataclass
class OddsMovement:
    match_id: str
    bookmaker: str
    market: str
    old_odds: float
    new_odds: float
    movement: float
    timestamp: datetime
    volume: Optional[float] = None

class RealTimeDataPipeline:
    """Advanced real-time sports data pipeline"""
    
    def __init__(self):
        self.setup_logging()
        self.setup_database()
        self.setup_redis()
        self.setup_kafka()
        self.setup_apis()
        
        # Data streams
        self.live_matches = {}
        self.odds_history = defaultdict(deque)
        self.event_queue = queue.PriorityQueue()
        self.subscribers = defaultdict(list)
        
        # Real-time processors
        self.processors = {
            'score_update': self.process_score_update,
            'odds_change': self.process_odds_change,
            'news': self.process_news_update,
            'social': self.process_social_update,
            'weather': self.process_weather_update,
            'injury': self.process_injury_update
        }
        
        # Rate limiting
        self.rate_limits = defaultdict(lambda: {'count': 0, 'reset_time': time.time()})
        
        # Running state
        self.running = False
        self.threads = []
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('realtime_pipeline.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_database(self):
        """Setup database for historical data"""
        try:
            self.engine = create_engine('sqlite:///realtime_sports.db')
            Base.metadata.create_all(self.engine)
            Session = sessionmaker(bind=self.engine)
            self.db_session = Session()
            self.logger.info("Database connection established")
        except Exception as e:
            self.logger.error(f"Database setup error: {e}")
            self.db_session = None
    
    def setup_redis(self):
        """Setup Redis for caching and pub/sub"""
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            self.redis_client.ping()
            self.logger.info("Redis connection established")
        except Exception as e:
            self.logger.warning(f"Redis not available: {e}")
            self.redis_client = None
    
    def setup_kafka(self):
        """Setup Kafka for message streaming"""
        try:
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=['localhost:9092'],
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
            )
            self.logger.info("Kafka producer initialized")
        except Exception as e:
            self.logger.warning(f"Kafka not available: {e}")
            self.kafka_producer = None
    
    def setup_apis(self):
        """Setup API connections"""
        self.api_keys = {
            'odds_api': 'your_odds_api_key',
            'sports_data': 'your_sports_data_key',
            'twitter': {
                'bearer_token': 'your_twitter_bearer_token'
            },
            'weather': 'your_weather_api_key'
        }
        
        # Setup Twitter API
        try:
            if self.api_keys['twitter']['bearer_token'] != 'your_twitter_bearer_token':
                self.twitter_api = tweepy.Client(bearer_token=self.api_keys['twitter']['bearer_token'])
            else:
                self.twitter_api = None
        except Exception as e:
            self.logger.warning(f"Twitter API not available: {e}")
            self.twitter_api = None
    
    # REAL-TIME DATA SOURCES
    async def start_live_score_stream(self):
        """Start live score streaming"""
        self.logger.info("Starting live score stream...")
        
        while self.running:
            try:
                # Simulate multiple data sources
                await self._stream_flashscore_data()
                await self._stream_espn_data()
                await self._stream_bet365_data()
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error in live score stream: {e}")
                await asyncio.sleep(10)
    
    async def _stream_flashscore_data(self):
        """Stream data from Flashscore"""
        try:
            async with aiohttp.ClientSession() as session:
                # Simulate real API call
                url = "https://www.flashscore.com/x/feed/df_dos_1_1_cs"
                
                # Mock live data for demonstration
                live_data = {
                    'matches': [
                        {
                            'id': 'fs_001',
                            'sport': 'tennis',
                            'home': 'Novak Djokovic',
                            'away': 'Carlos Alcaraz',
                            'score': '6-4, 3-2',
                            'status': 'Live',
                            'minute': 0,
                            'odds': {'home': 1.75, 'away': 2.05},
                            'events': [
                                {'type': 'game_won', 'player': 'Djokovic', 'score': '6-4, 3-2'}
                            ]
                        },
                        {
                            'id': 'fs_002',
                            'sport': 'football',
                            'home': 'Arsenal',
                            'away': 'Chelsea',
                            'score': '2-1',
                            'status': 'Live',
                            'minute': 78,
                            'odds': {'home': 1.65, 'away': 2.25, 'draw': 3.80},
                            'events': [
                                {'type': 'goal', 'player': 'Havertz', 'minute': 77, 'team': 'Arsenal'}
                            ]
                        }
                    ]
                }
                
                for match in live_data['matches']:
                    await self._process_live_match_update(match, 'flashscore')
                
        except Exception as e:
            self.logger.error(f"Error streaming Flashscore data: {e}")
    
    async def _stream_espn_data(self):
        """Stream data from ESPN"""
        try:
            # Mock ESPN data
            espn_data = {
                'nba_games': [
                    {
                        'id': 'espn_nba_001',
                        'sport': 'basketball',
                        'home': 'Lakers',
                        'away': 'Warriors',
                        'score': '98-102',
                        'quarter': 4,
                        'time_remaining': '2:45',
                        'status': 'Live'
                    }
                ],
                'nfl_games': [
                    {
                        'id': 'espn_nfl_001',
                        'sport': 'american_football',
                        'home': 'Chiefs',
                        'away': 'Bills',
                        'score': '21-14',
                        'quarter': 3,
                        'time_remaining': '8:32',
                        'status': 'Live'
                    }
                ]
            }
            
            # Process NBA games
            for game in espn_data['nba_games']:
                await self._process_live_match_update(game, 'espn')
            
            # Process NFL games
            for game in espn_data['nfl_games']:
                await self._process_live_match_update(game, 'espn')
                
        except Exception as e:
            self.logger.error(f"Error streaming ESPN data: {e}")
    
    async def _stream_bet365_data(self):
        """Stream betting odds from Bet365"""
        try:
            # Mock betting odds data
            odds_data = {
                'tennis_odds': [
                    {
                        'match_id': 'fs_001',
                        'bookmaker': 'bet365',
                        'odds': {'home': 1.73, 'away': 2.07},
                        'volume': 125000
                    }
                ],
                'football_odds': [
                    {
                        'match_id': 'fs_002',
                        'bookmaker': 'bet365',
                        'odds': {'home': 1.62, 'away': 2.30, 'draw': 3.85},
                        'volume': 89000
                    }
                ]
            }
            
            for category in odds_data.values():
                for odds in category:
                    await self._process_odds_update(odds)
                    
        except Exception as e:
            self.logger.error(f"Error streaming Bet365 data: {e}")
    
    async def _process_live_match_update(self, match_data: Dict, source: str):
        """Process live match update"""
        match_id = match_data['id']
        
        # Update live matches cache
        if match_id in self.live_matches:
            old_match = self.live_matches[match_id]
            
            # Check for score changes
            if old_match.score != match_data.get('score', ''):
                await self._emit_score_change_event(match_id, old_match.score, match_data.get('score', ''), source)
        
        # Update match data
        live_match = LiveMatch(
            match_id=match_id,
            sport=match_data['sport'],
            home_team=match_data['home'],
            away_team=match_data['away'],
            score=match_data.get('score', ''),
            status=match_data.get('status', 'Unknown'),
            minute=match_data.get('minute', 0),
            odds=match_data.get('odds', {}),
            last_update=datetime.now(),
            events=match_data.get('events', [])
        )
        
        self.live_matches[match_id] = live_match
        
        # Cache in Redis if available
        if self.redis_client:
            self.redis_client.setex(
                f"live_match:{match_id}",
                300,  # 5 minutes expiry
                json.dumps(asdict(live_match), default=str)
            )
        
        # Publish to Kafka if available
        if self.kafka_producer:
            self.kafka_producer.send('live_matches', asdict(live_match))
    
    async def _process_odds_update(self, odds_data: Dict):
        """Process betting odds update"""
        match_id = odds_data['match_id']
        bookmaker = odds_data['bookmaker']
        new_odds = odds_data['odds']
        
        # Check for odds movement
        cache_key = f"odds:{match_id}:{bookmaker}"
        
        if self.redis_client:
            old_odds_json = self.redis_client.get(cache_key)
            if old_odds_json:
                old_odds = json.loads(old_odds_json)
                
                # Detect significant movement (>5% change)
                for market, new_value in new_odds.items():
                    if market in old_odds:
                        old_value = old_odds[market]
                        movement = ((new_value - old_value) / old_value) * 100
                        
                        if abs(movement) > 5:  # 5% threshold
                            odds_movement = OddsMovement(
                                match_id=match_id,
                                bookmaker=bookmaker,
                                market=market,
                                old_odds=old_value,
                                new_odds=new_value,
                                movement=movement,
                                timestamp=datetime.now(),
                                volume=odds_data.get('volume')
                            )
                            
                            await self._emit_odds_movement_event(odds_movement)
            
            # Update odds in cache
            self.redis_client.setex(cache_key, 300, json.dumps(new_odds))
    
    # EVENT PROCESSING
    async def _emit_score_change_event(self, match_id: str, old_score: str, new_score: str, source: str):
        """Emit score change event"""
        event = RealTimeEvent(
            event_id=f"score_{match_id}_{int(time.time())}",
            sport=self.live_matches[match_id].sport,
            event_type='score_update',
            timestamp=datetime.now(),
            data={
                'match_id': match_id,
                'old_score': old_score,
                'new_score': new_score,
                'home_team': self.live_matches[match_id].home_team,
                'away_team': self.live_matches[match_id].away_team
            },
            priority=4,  # High priority
            source=source
        )
        
        await self._process_event(event)
    
    async def _emit_odds_movement_event(self, odds_movement: OddsMovement):
        """Emit odds movement event"""
        event = RealTimeEvent(
            event_id=f"odds_{odds_movement.match_id}_{int(time.time())}",
            sport=self.live_matches.get(odds_movement.match_id, LiveMatch('', '', '', '', '', '', 0, {}, datetime.now())).sport,
            event_type='odds_change',
            timestamp=odds_movement.timestamp,
            data=asdict(odds_movement),
            priority=3,  # Medium-high priority
            source=odds_movement.bookmaker
        )
        
        await self._process_event(event)
    
    async def _process_event(self, event: RealTimeEvent):
        """Process real-time event"""
        try:
            # Log event
            self.logger.info(f"Processing {event.event_type} event: {event.event_id}")
            
            # Call appropriate processor
            if event.event_type in self.processors:
                await self.processors[event.event_type](event)
            
            # Notify subscribers
            await self._notify_subscribers(event)
            
            # Store in database
            if self.db_session:
                await self._store_event_in_db(event)
            
            # Mark as processed
            event.processed = True
            
        except Exception as e:
            self.logger.error(f"Error processing event {event.event_id}: {e}")
    
    # EVENT PROCESSORS
    async def process_score_update(self, event: RealTimeEvent):
        """Process score update"""
        data = event.data
        match_id = data['match_id']
        
        # Update live match
        if match_id in self.live_matches:
            self.live_matches[match_id].score = data['new_score']
            self.live_matches[match_id].last_update = event.timestamp
        
        # Trigger analysis
        await self._trigger_score_analysis(event)
    
    async def process_odds_change(self, event: RealTimeEvent):
        """Process odds change"""
        data = event.data
        
        # Store odds movement history
        match_id = data['match_id']
        self.odds_history[match_id].append(data)
        
        # Keep only last 100 movements
        if len(self.odds_history[match_id]) > 100:
            self.odds_history[match_id].popleft()
        
        # Trigger market analysis
        await self._trigger_market_analysis(event)
    
    async def process_news_update(self, event: RealTimeEvent):
        """Process news update"""
        # Analyze sentiment and impact
        await self._analyze_news_impact(event)
    
    async def process_social_update(self, event: RealTimeEvent):
        """Process social media update"""
        # Analyze social sentiment
        await self._analyze_social_sentiment(event)
    
    async def process_weather_update(self, event: RealTimeEvent):
        """Process weather update"""
        # Check impact on outdoor sports
        await self._analyze_weather_impact(event)
    
    async def process_injury_update(self, event: RealTimeEvent):
        """Process injury update"""
        # Analyze player impact and odds changes
        await self._analyze_injury_impact(event)
    
    # ANALYSIS TRIGGERS
    async def _trigger_score_analysis(self, event: RealTimeEvent):
        """Trigger analysis based on score change"""
        data = event.data
        match_id = data['match_id']
        
        # Get current odds
        if match_id in self.live_matches:
            current_odds = self.live_matches[match_id].odds
            
            # Analyze momentum shift
            momentum_analysis = await self._analyze_momentum_shift(match_id, data['new_score'], current_odds)
            
            # Generate live betting recommendation
            if momentum_analysis.get('significant_shift', False):
                recommendation_event = RealTimeEvent(
                    event_id=f"rec_{match_id}_{int(time.time())}",
                    sport=event.sport,
                    event_type='recommendation',
                    timestamp=datetime.now(),
                    data={
                        'match_id': match_id,
                        'type': 'momentum_shift',
                        'analysis': momentum_analysis,
                        'recommendation': momentum_analysis.get('recommendation', 'Hold')
                    },
                    priority=5,  # Critical priority
                    source='ai_analysis'
                )
                
                await self._process_event(recommendation_event)
    
    async def _trigger_market_analysis(self, event: RealTimeEvent):
        """Trigger market analysis based on odds movement"""
        data = event.data
        match_id = data['match_id']
        
        # Analyze odds movement pattern
        movement_pattern = await self._analyze_odds_pattern(match_id)
        
        if movement_pattern.get('suspicious_activity', False):
            alert_event = RealTimeEvent(
                event_id=f"alert_{match_id}_{int(time.time())}",
                sport=event.sport,
                event_type='market_alert',
                timestamp=datetime.now(),
                data={
                    'match_id': match_id,
                    'alert_type': 'suspicious_movement',
                    'pattern': movement_pattern
                },
                priority=5,
                source='market_analysis'
            )
            
            await self._process_event(alert_event)
    
    async def _analyze_momentum_shift(self, match_id: str, new_score: str, current_odds: Dict) -> Dict:
        """Analyze momentum shift based on score change"""
        # Mock analysis - in production, use advanced ML models
        analysis = {
            'match_id': match_id,
            'score': new_score,
            'momentum_direction': 'home' if hash(new_score) % 2 == 0 else 'away',
            'confidence': 0.75,
            'significant_shift': hash(new_score) % 3 == 0,
            'recommendation': 'Buy' if hash(new_score) % 2 == 0 else 'Hold',
            'expected_odds_change': 0.1,
            'timestamp': datetime.now().isoformat()
        }
        
        return analysis
    
    async def _analyze_odds_pattern(self, match_id: str) -> Dict:
        """Analyze odds movement pattern"""
        movements = list(self.odds_history[match_id])
        
        if len(movements) < 5:
            return {'insufficient_data': True}
        
        # Analyze pattern
        recent_movements = movements[-5:]
        total_movement = sum(m.get('movement', 0) for m in recent_movements)
        
        analysis = {
            'match_id': match_id,
            'total_movement': total_movement,
            'movement_count': len(recent_movements),
            'suspicious_activity': abs(total_movement) > 20,  # 20% threshold
            'pattern_type': 'sharp_movement' if abs(total_movement) > 20 else 'normal',
            'timestamp': datetime.now().isoformat()
        }
        
        return analysis
    
    # SUBSCRIPTION MANAGEMENT
    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to specific event type"""
        self.subscribers[event_type].append(callback)
        self.logger.info(f"New subscriber for {event_type} events")
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from event type"""
        if callback in self.subscribers[event_type]:
            self.subscribers[event_type].remove(callback)
            self.logger.info(f"Unsubscribed from {event_type} events")
    
    async def _notify_subscribers(self, event: RealTimeEvent):
        """Notify event subscribers"""
        if event.event_type in self.subscribers:
            for callback in self.subscribers[event.event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    self.logger.error(f"Error notifying subscriber: {e}")
    
    # DATA STORAGE
    async def _store_event_in_db(self, event: RealTimeEvent):
        """Store event in database"""
        try:
            # In production, use proper SQLAlchemy models
            # For now, just log the event
            self.logger.info(f"Storing event {event.event_id} in database")
        except Exception as e:
            self.logger.error(f"Error storing event in database: {e}")
    
    # PIPELINE CONTROL
    async def start(self):
        """Start the real-time pipeline"""
        self.running = True
        self.logger.info("Starting real-time data pipeline...")
        
        # Start data streams
        tasks = [
            asyncio.create_task(self.start_live_score_stream()),
            asyncio.create_task(self._start_news_stream()),
            asyncio.create_task(self._start_social_stream()),
            asyncio.create_task(self._start_weather_stream())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"Error in pipeline: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the real-time pipeline"""
        self.running = False
        self.logger.info("Stopping real-time data pipeline...")
        
        # Close connections
        if self.kafka_producer:
            self.kafka_producer.close()
        
        if self.db_session:
            self.db_session.close()
    
    async def _start_news_stream(self):
        """Start news feed stream"""
        while self.running:
            try:
                # Mock news updates
                await asyncio.sleep(30)  # Every 30 seconds
                
                news_event = RealTimeEvent(
                    event_id=f"news_{int(time.time())}",
                    sport='general',
                    event_type='news',
                    timestamp=datetime.now(),
                    data={
                        'headline': 'Breaking: Player injury update',
                        'content': 'Mock news content...',
                        'impact_score': 0.7,
                        'affected_matches': ['fs_001']
                    },
                    priority=2,
                    source='news_feed'
                )
                
                await self._process_event(news_event)
                
            except Exception as e:
                self.logger.error(f"Error in news stream: {e}")
                await asyncio.sleep(60)
    
    async def _start_social_stream(self):
        """Start social media stream"""
        while self.running:
            try:
                # Mock social updates
                await asyncio.sleep(45)  # Every 45 seconds
                
                social_event = RealTimeEvent(
                    event_id=f"social_{int(time.time())}",
                    sport='tennis',
                    event_type='social',
                    timestamp=datetime.now(),
                    data={
                        'platform': 'twitter',
                        'sentiment': 'positive',
                        'mentions': 150,
                        'trending_topics': ['#TennisMatch', '#Djokovic'],
                        'sentiment_score': 0.6
                    },
                    priority=1,
                    source='social_media'
                )
                
                await self._process_event(social_event)
                
            except Exception as e:
                self.logger.error(f"Error in social stream: {e}")
                await asyncio.sleep(60)
    
    async def _start_weather_stream(self):
        """Start weather updates stream"""
        while self.running:
            try:
                # Mock weather updates
                await asyncio.sleep(120)  # Every 2 minutes
                
                weather_event = RealTimeEvent(
                    event_id=f"weather_{int(time.time())}",
                    sport='tennis',
                    event_type='weather',
                    timestamp=datetime.now(),
                    data={
                        'location': 'Paris',
                        'temperature': 22,
                        'humidity': 65,
                        'wind_speed': 15,
                        'conditions': 'Partly Cloudy',
                        'impact_level': 'low'
                    },
                    priority=1,
                    source='weather_api'
                )
                
                await self._process_event(weather_event)
                
            except Exception as e:
                self.logger.error(f"Error in weather stream: {e}")
                await asyncio.sleep(180)
    
    # API ENDPOINTS
    def get_live_matches(self) -> List[Dict]:
        """Get current live matches"""
        return [asdict(match) for match in self.live_matches.values()]
    
    def get_odds_history(self, match_id: str) -> List[Dict]:
        """Get odds history for specific match"""
        return list(self.odds_history.get(match_id, []))
    
    def get_pipeline_status(self) -> Dict:
        """Get pipeline status"""
        return {
            'running': self.running,
            'live_matches_count': len(self.live_matches),
            'total_events_processed': sum(len(movements) for movements in self.odds_history.values()),
            'active_subscribers': sum(len(subs) for subs in self.subscribers.values()),
            'uptime': time.time() - getattr(self, 'start_time', time.time()),
            'last_update': datetime.now().isoformat()
        }

# Example usage and testing
async def main():
    """Main function to test the real-time pipeline"""
    pipeline = RealTimeDataPipeline()
    
    # Example subscribers
    async def score_subscriber(event: RealTimeEvent):
        print(f"🎯 SCORE UPDATE: {event.data}")
    
    async def odds_subscriber(event: RealTimeEvent):
        print(f"💰 ODDS CHANGE: {event.data}")
    
    def recommendation_subscriber(event: RealTimeEvent):
        print(f"🚨 RECOMMENDATION: {event.data}")
    
    # Subscribe to events
    pipeline.subscribe('score_update', score_subscriber)
    pipeline.subscribe('odds_change', odds_subscriber)
    pipeline.subscribe('recommendation', recommendation_subscriber)
    
    print("🚀 STARTING REAL-TIME SPORTS DATA PIPELINE")
    print("=" * 60)
    
    try:
        # Run pipeline for 60 seconds for demo
        await asyncio.wait_for(pipeline.start(), timeout=60)
    except asyncio.TimeoutError:
        print("\n⏰ Demo completed - stopping pipeline")
        await pipeline.stop()
    
    # Show final status
    status = pipeline.get_pipeline_status()
    print(f"\n📊 PIPELINE STATUS:")
    print(f"Live matches: {status['live_matches_count']}")
    print(f"Events processed: {status['total_events_processed']}")
    print(f"Active subscribers: {status['active_subscribers']}")

if __name__ == "__main__":
    asyncio.run(main())