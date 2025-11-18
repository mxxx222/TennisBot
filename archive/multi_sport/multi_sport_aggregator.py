#!/usr/bin/env python3
"""
🏀 MULTI-SPORT DATA AGGREGATOR
==============================

Comprehensive data aggregation from multiple sports APIs and scraping sources
Combines official APIs, web scraping, and data validation

Author: TennisBot Advanced Analytics
Version: 2.0.0
"""

import asyncio
import aiohttp
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass, asdict
import os
import numpy as np
from concurrent.futures import ThreadPoolExecutor

@dataclass
class SportEvent:
    """Universal sport event data structure"""
    event_id: str
    sport: str
    league: str
    home_team: str
    away_team: str
    start_time: str
    status: str
    home_score: Optional[str] = None
    away_score: Optional[str] = None
    home_odds: Optional[float] = None
    away_odds: Optional[float] = None
    draw_odds: Optional[float] = None
    total_over: Optional[float] = None
    total_under: Optional[float] = None
    venue: Optional[str] = None
    weather: Optional[Dict] = None
    statistics: Optional[Dict] = None
    team_stats: Optional[Dict] = None
    player_stats: Optional[Dict] = None
    injuries: Optional[List[str]] = None
    recent_form: Optional[Dict] = None
    head_to_head: Optional[Dict] = None
    prediction_confidence: Optional[float] = None

class MultiSportAggregator:
    """Aggregates data from multiple sports sources"""
    
    def __init__(self):
        self.setup_logging()
        self.api_keys = self.load_api_keys()
        self.data_sources = self.configure_data_sources()
        self.session_timeout = aiohttp.ClientTimeout(total=30)
        
    def setup_logging(self):
        """Setup comprehensive logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment variables"""
        return {
            'sports_api': os.getenv('SPORTS_API_KEY', ''),
            'rapid_api': os.getenv('RAPID_API_KEY', ''),
            'football_api': os.getenv('FOOTBALL_API_KEY', ''),
            'basketball_api': os.getenv('BASKETBALL_API_KEY', ''),
            'tennis_api': os.getenv('TENNIS_API_KEY', ''),
            'weather_api': os.getenv('WEATHER_API_KEY', ''),
            'odds_api': os.getenv('ODDS_API_KEY', '')
        }
    
    def configure_data_sources(self) -> Dict[str, Dict]:
        """Configure all data sources and their endpoints"""
        return {
            'tennis': {
                'official_apis': {
                    'atp_tour': {
                        'base_url': 'https://www.atptour.com/en/scores/current',
                        'endpoints': {
                            'matches': '/matches',
                            'players': '/players',
                            'tournaments': '/tournaments'
                        }
                    },
                    'wta_tour': {
                        'base_url': 'https://www.wtatennis.com/scores',
                        'endpoints': {
                            'matches': '/matches',
                            'players': '/players'
                        }
                    }
                },
                'third_party_apis': {
                    'tennis_api': {
                        'base_url': 'https://v1.tennis.api-sports.io',
                        'headers': {'x-rapidapi-key': self.api_keys.get('tennis_api', '')},
                        'endpoints': {
                            'fixtures': '/fixtures',
                            'players': '/players',
                            'statistics': '/statistics'
                        }
                    }
                },
                'scraping_targets': [
                    'https://www.flashscore.com/tennis/',
                    'https://www.tennisexplorer.com/',
                    'https://www.oddsportal.com/tennis/'
                ]
            },
            'football': {
                'official_apis': {
                    'premier_league': {
                        'base_url': 'https://footballapi.pulselive.com/football',
                        'endpoints': {
                            'fixtures': '/fixtures',
                            'tables': '/compseasons/489/tables',
                            'teams': '/teams'
                        }
                    }
                },
                'third_party_apis': {
                    'football_api': {
                        'base_url': 'https://v3.football.api-sports.io',
                        'headers': {'x-rapidapi-key': self.api_keys.get('football_api', '')},
                        'endpoints': {
                            'fixtures': '/fixtures',
                            'teams': '/teams',
                            'players': '/players'
                        }
                    }
                }
            },
            'basketball': {
                'official_apis': {
                    'nba_api': {
                        'base_url': 'https://stats.nba.com/stats',
                        'endpoints': {
                            'scoreboard': '/scoreboard',
                            'teams': '/teams',
                            'players': '/players'
                        }
                    }
                },
                'third_party_apis': {
                    'basketball_api': {
                        'base_url': 'https://v1.basketball.api-sports.io',
                        'headers': {'x-rapidapi-key': self.api_keys.get('basketball_api', '')},
                        'endpoints': {
                            'games': '/games',
                            'teams': '/teams'
                        }
                    }
                }
            },
            'odds': {
                'the_odds_api': {
                    'base_url': 'https://api.the-odds-api.com/v4',
                    'key': self.api_keys.get('odds_api', ''),
                    'endpoints': {
                        'sports': '/sports',
                        'odds': '/sports/{sport}/odds'
                    }
                }
            }
        }
    
    async def fetch_tennis_data(self) -> List[SportEvent]:
        """Comprehensive tennis data aggregation"""
        self.logger.info("🎾 Fetching comprehensive tennis data...")
        
        tennis_events = []
        
        # Fetch from multiple sources in parallel
        tasks = [
            self.fetch_atp_data(),
            self.fetch_wta_data(),
            self.fetch_tennis_api_data(),
            self.scrape_tennis_sites()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                tennis_events.extend(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Tennis data fetch error: {result}")
        
        # Remove duplicates and validate
        unique_events = self.remove_duplicates(tennis_events)
        validated_events = self.validate_events(unique_events)
        
        self.logger.info(f"✅ Tennis: {len(validated_events)} validated events")
        return validated_events
    
    async def fetch_atp_data(self) -> List[SportEvent]:
        """Fetch ATP Tour data"""
        events = []
        
        try:
            # Mock ATP data for demonstration
            atp_matches = [
                {
                    'event_id': 'atp_001',
                    'player1': 'Novak Djokovic',
                    'player2': 'Carlos Alcaraz',
                    'tournament': 'ATP Masters 1000 Paris',
                    'date': datetime.now().isoformat(),
                    'status': 'Scheduled',
                    'surface': 'Hard'
                },
                {
                    'event_id': 'atp_002',
                    'player1': 'Jannik Sinner',
                    'player2': 'Daniil Medvedev',
                    'tournament': 'ATP Finals',
                    'date': (datetime.now() + timedelta(hours=2)).isoformat(),
                    'status': 'Scheduled',
                    'surface': 'Hard'
                }
            ]
            
            for match in atp_matches:
                event = SportEvent(
                    event_id=match['event_id'],
                    sport='tennis',
                    league=match['tournament'],
                    home_team=match['player1'],
                    away_team=match['player2'],
                    start_time=match['date'],
                    status=match['status'],
                    statistics={'surface': match['surface']},
                    prediction_confidence=0.75
                )
                events.append(event)
        
        except Exception as e:
            self.logger.error(f"ATP data fetch error: {e}")
        
        return events
    
    async def fetch_wta_data(self) -> List[SportEvent]:
        """Fetch WTA Tour data"""
        events = []
        
        try:
            # Mock WTA data
            wta_matches = [
                {
                    'event_id': 'wta_001',
                    'player1': 'Iga Swiatek',
                    'player2': 'Aryna Sabalenka',
                    'tournament': 'WTA Finals',
                    'date': datetime.now().isoformat(),
                    'status': 'Live',
                    'score': '6-4, 2-1'
                }
            ]
            
            for match in wta_matches:
                event = SportEvent(
                    event_id=match['event_id'],
                    sport='tennis',
                    league=match['tournament'],
                    home_team=match['player1'],
                    away_team=match['player2'],
                    start_time=match['date'],
                    status=match['status'],
                    home_score=match.get('score', ''),
                    prediction_confidence=0.78
                )
                events.append(event)
        
        except Exception as e:
            self.logger.error(f"WTA data fetch error: {e}")
        
        return events
    
    async def fetch_tennis_api_data(self) -> List[SportEvent]:
        """Fetch data from Tennis API"""
        events = []
        
        if not self.api_keys.get('tennis_api'):
            self.logger.warning("Tennis API key not found")
            return events
        
        try:
            async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
                headers = {'x-rapidapi-key': self.api_keys['tennis_api']}
                url = f"{self.data_sources['tennis']['third_party_apis']['tennis_api']['base_url']}/fixtures"
                
                params = {
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'timezone': 'Europe/London'
                }
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for match in data.get('response', [])[:10]:  # Limit to 10 matches
                            event = self.parse_tennis_api_match(match)
                            if event:
                                events.append(event)
                    else:
                        self.logger.warning(f"Tennis API returned status: {response.status}")
        
        except Exception as e:
            self.logger.error(f"Tennis API fetch error: {e}")
        
        return events
    
    def parse_tennis_api_match(self, match_data: Dict) -> Optional[SportEvent]:
        """Parse Tennis API match data"""
        try:
            players = match_data.get('players', {})
            fixture = match_data.get('fixture', {})
            league = match_data.get('league', {})
            
            event = SportEvent(
                event_id=f"tennis_api_{fixture.get('id', 'unknown')}",
                sport='tennis',
                league=league.get('name', 'Unknown Tournament'),
                home_team=players.get('first', {}).get('name', 'Unknown'),
                away_team=players.get('second', {}).get('name', 'Unknown'),
                start_time=fixture.get('date', datetime.now().isoformat()),
                status=fixture.get('status', {}).get('long', 'Scheduled'),
                venue=match_data.get('venue', {}).get('name'),
                statistics=match_data.get('statistics', {}),
                prediction_confidence=0.70
            )
            
            return event
        
        except Exception as e:
            self.logger.warning(f"Error parsing Tennis API match: {e}")
            return None
    
    async def scrape_tennis_sites(self) -> List[SportEvent]:
        """Scrape additional tennis sites"""
        events = []
        
        # Mock scraping data for demonstration
        scraped_matches = [
            {
                'event_id': 'scraped_001',
                'player1': 'Rafael Nadal',
                'player2': 'Alexander Zverev',
                'tournament': 'Roland Garros',
                'odds': {'player1': 1.65, 'player2': 2.25}
            }
        ]
        
        for match in scraped_matches:
            event = SportEvent(
                event_id=match['event_id'],
                sport='tennis',
                league=match['tournament'],
                home_team=match['player1'],
                away_team=match['player2'],
                start_time=datetime.now().isoformat(),
                status='Scheduled',
                home_odds=match['odds']['player1'],
                away_odds=match['odds']['player2'],
                prediction_confidence=0.72
            )
            events.append(event)
        
        return events
    
    async def fetch_football_data(self) -> List[SportEvent]:
        """Comprehensive football data aggregation"""
        self.logger.info("⚽ Fetching comprehensive football data...")
        
        football_events = []
        
        tasks = [
            self.fetch_premier_league_data(),
            self.fetch_champions_league_data(),
            self.fetch_football_api_data()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                football_events.extend(result)
        
        validated_events = self.validate_events(football_events)
        self.logger.info(f"✅ Football: {len(validated_events)} validated events")
        return validated_events
    
    async def fetch_premier_league_data(self) -> List[SportEvent]:
        """Fetch Premier League data"""
        events = []
        
        # Mock Premier League data
        pl_matches = [
            {
                'event_id': 'pl_001',
                'home_team': 'Manchester City',
                'away_team': 'Liverpool',
                'date': datetime.now().isoformat(),
                'venue': 'Etihad Stadium'
            },
            {
                'event_id': 'pl_002',
                'home_team': 'Arsenal',
                'away_team': 'Chelsea',
                'date': (datetime.now() + timedelta(days=1)).isoformat(),
                'venue': 'Emirates Stadium'
            }
        ]
        
        for match in pl_matches:
            event = SportEvent(
                event_id=match['event_id'],
                sport='football',
                league='Premier League',
                home_team=match['home_team'],
                away_team=match['away_team'],
                start_time=match['date'],
                status='Scheduled',
                venue=match['venue'],
                prediction_confidence=0.68
            )
            events.append(event)
        
        return events
    
    async def fetch_basketball_data(self) -> List[SportEvent]:
        """Comprehensive basketball data aggregation"""
        self.logger.info("🏀 Fetching comprehensive basketball data...")
        
        basketball_events = []
        
        tasks = [
            self.fetch_nba_data(),
            self.fetch_euroleague_data()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                basketball_events.extend(result)
        
        validated_events = self.validate_events(basketball_events)
        self.logger.info(f"✅ Basketball: {len(validated_events)} validated events")
        return validated_events
    
    async def fetch_nba_data(self) -> List[SportEvent]:
        """Fetch NBA data"""
        events = []
        
        # Mock NBA data
        nba_games = [
            {
                'event_id': 'nba_001',
                'home_team': 'Los Angeles Lakers',
                'away_team': 'Boston Celtics',
                'date': datetime.now().isoformat(),
                'venue': 'Crypto.com Arena'
            }
        ]
        
        for game in nba_games:
            event = SportEvent(
                event_id=game['event_id'],
                sport='basketball',
                league='NBA',
                home_team=game['home_team'],
                away_team=game['away_team'],
                start_time=game['date'],
                status='Scheduled',
                venue=game['venue'],
                prediction_confidence=0.71
            )
            events.append(event)
        
        return events
    
    async def fetch_comprehensive_odds(self, events: List[SportEvent]) -> List[SportEvent]:
        """Fetch odds for all events"""
        self.logger.info("💰 Fetching comprehensive odds data...")
        
        if not self.api_keys.get('odds_api'):
            self.logger.warning("Odds API key not found, using mock data")
            return self.add_mock_odds(events)
        
        # Enhance events with odds data
        enhanced_events = []
        
        for event in events:
            try:
                odds_data = await self.fetch_event_odds(event)
                if odds_data:
                    event.home_odds = odds_data.get('home_odds')
                    event.away_odds = odds_data.get('away_odds')
                    event.draw_odds = odds_data.get('draw_odds')
                    event.total_over = odds_data.get('total_over')
                    event.total_under = odds_data.get('total_under')
                
                enhanced_events.append(event)
            
            except Exception as e:
                self.logger.warning(f"Error fetching odds for {event.event_id}: {e}")
                enhanced_events.append(event)
        
        return enhanced_events
    
    def add_mock_odds(self, events: List[SportEvent]) -> List[SportEvent]:
        """Add mock odds data for testing"""
        for event in events:
            if event.sport == 'tennis':
                event.home_odds = np.random.uniform(1.50, 2.50)
                event.away_odds = np.random.uniform(1.50, 2.50)
                event.total_over = np.random.uniform(1.80, 2.20)
                event.total_under = np.random.uniform(1.80, 2.20)
            elif event.sport == 'football':
                event.home_odds = np.random.uniform(1.80, 3.50)
                event.away_odds = np.random.uniform(2.00, 4.00)
                event.draw_odds = np.random.uniform(2.80, 4.50)
            elif event.sport == 'basketball':
                event.home_odds = np.random.uniform(1.70, 2.30)
                event.away_odds = np.random.uniform(1.70, 2.30)
                event.total_over = np.random.uniform(1.85, 2.15)
                event.total_under = np.random.uniform(1.85, 2.15)
        
        return events
    
    def remove_duplicates(self, events: List[SportEvent]) -> List[SportEvent]:
        """Remove duplicate events based on teams and time"""
        seen = set()
        unique_events = []
        
        for event in events:
            # Create a unique identifier
            identifier = f"{event.sport}_{event.home_team}_{event.away_team}_{event.start_time[:10]}"
            
            if identifier not in seen:
                seen.add(identifier)
                unique_events.append(event)
        
        return unique_events
    
    def validate_events(self, events: List[SportEvent]) -> List[SportEvent]:
        """Validate and clean event data"""
        validated_events = []
        
        for event in events:
            try:
                # Basic validation
                if not event.home_team or not event.away_team:
                    continue
                
                if event.home_team == event.away_team:
                    continue
                
                # Validate odds if present
                if event.home_odds and (event.home_odds < 1.01 or event.home_odds > 100):
                    event.home_odds = None
                
                if event.away_odds and (event.away_odds < 1.01 or event.away_odds > 100):
                    event.away_odds = None
                
                # Clean team names
                event.home_team = event.home_team.strip()
                event.away_team = event.away_team.strip()
                
                validated_events.append(event)
            
            except Exception as e:
                self.logger.warning(f"Event validation error: {e}")
                continue
        
        return validated_events
    
    async def aggregate_all_sports(self) -> Dict[str, List[SportEvent]]:
        """Master aggregation function for all sports"""
        self.logger.info("🔄 Starting comprehensive sports data aggregation...")
        
        start_time = datetime.now()
        
        # Fetch all sports data in parallel
        tasks = [
            self.fetch_tennis_data(),
            self.fetch_football_data(),
            self.fetch_basketball_data()
        ]
        
        tennis_data, football_data, basketball_data = await asyncio.gather(
            *tasks, return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(tennis_data, Exception):
            self.logger.error(f"Tennis aggregation error: {tennis_data}")
            tennis_data = []
        
        if isinstance(football_data, Exception):
            self.logger.error(f"Football aggregation error: {football_data}")
            football_data = []
        
        if isinstance(basketball_data, Exception):
            self.logger.error(f"Basketball aggregation error: {basketball_data}")
            basketball_data = []
        
        # Combine all events for odds fetching
        all_events = tennis_data + football_data + basketball_data
        
        # Fetch comprehensive odds
        events_with_odds = await self.fetch_comprehensive_odds(all_events)
        
        # Separate back by sport
        final_data = {
            'tennis': [e for e in events_with_odds if e.sport == 'tennis'],
            'football': [e for e in events_with_odds if e.sport == 'football'],
            'basketball': [e for e in events_with_odds if e.sport == 'basketball']
        }
        
        # Calculate statistics
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        total_events = sum(len(events) for events in final_data.values())
        
        self.logger.info(f"✅ Aggregation completed in {duration:.2f}s")
        self.logger.info(f"📊 Total events aggregated: {total_events}")
        self.logger.info(f"🎾 Tennis: {len(final_data['tennis'])}")
        self.logger.info(f"⚽ Football: {len(final_data['football'])}")
        self.logger.info(f"🏀 Basketball: {len(final_data['basketball'])}")
        
        return final_data
    
    def export_to_formats(self, data: Dict[str, List[SportEvent]], base_filename: str = None):
        """Export data to multiple formats"""
        if base_filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_filename = f"sports_data_{timestamp}"
        
        # Convert to dictionaries
        export_data = {}
        for sport, events in data.items():
            export_data[sport] = [asdict(event) for event in events]
        
        # Export to JSON
        json_filename = f"{base_filename}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        # Export to CSV (flatten data)
        csv_data = []
        for sport, events in data.items():
            for event in events:
                event_dict = asdict(event)
                csv_data.append(event_dict)
        
        if csv_data:
            df = pd.json_normalize(csv_data)
            csv_filename = f"{base_filename}.csv"
            df.to_csv(csv_filename, index=False)
            
            # Also create sport-specific CSVs
            for sport, events in data.items():
                if events:
                    sport_data = [asdict(event) for event in events]
                    sport_df = pd.json_normalize(sport_data)
                    sport_csv = f"{base_filename}_{sport}.csv"
                    sport_df.to_csv(sport_csv, index=False)
        
        self.logger.info(f"📁 Data exported to {json_filename} and CSV files")
        return json_filename

# Additional placeholder methods
async def fetch_champions_league_data(self) -> List[SportEvent]:
    """Fetch Champions League data"""
    return []

async def fetch_football_api_data(self) -> List[SportEvent]:
    """Fetch data from Football API"""
    return []

async def fetch_euroleague_data(self) -> List[SportEvent]:
    """Fetch Euroleague data"""
    return []

async def fetch_event_odds(self, event: SportEvent) -> Optional[Dict]:
    """Fetch odds for specific event"""
    return None

if __name__ == "__main__":
    async def main():
        aggregator = MultiSportAggregator()
        
        print("🏟️ MULTI-SPORT DATA AGGREGATOR")
        print("=" * 50)
        
        # Aggregate all sports data
        all_data = await aggregator.aggregate_all_sports()
        
        # Export data
        filename = aggregator.export_to_formats(all_data)
        
        print(f"\n✅ Data aggregation completed successfully!")
        print(f"📁 Data exported to: {filename}")
        
        # Display sample data
        for sport, events in all_data.items():
            if events:
                print(f"\n{sport.upper()} SAMPLE:")
                for i, event in enumerate(events[:2], 1):
                    print(f"{i}. {event.home_team} vs {event.away_team}")
                    print(f"   League: {event.league}")
                    print(f"   Odds: {event.home_odds} | {event.away_odds}")
    
    asyncio.run(main())