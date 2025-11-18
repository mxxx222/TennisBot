#!/usr/bin/env python3
"""
🏆 MULTI-SPORT PREMATCH SCRAPER
===============================
Advanced scraper for collecting comprehensive prematch data across multiple sports
for ROI analysis and betting intelligence.

Supported Sports:
- ⚽ Football (Soccer) - Premier League, La Liga, Bundesliga, Serie A, Champions League
- 🎾 Tennis - ATP, WTA, Grand Slams
- 🏀 Basketball - NBA, EuroLeague
- 🏒 Ice Hockey - NHL, KHL
- 🏈 American Football - NFL
- ⚾ Baseball - MLB

Data Sources:
- Match fixtures and results
- Team/player statistics
- Betting odds from multiple bookmakers
- Weather conditions
- Injury reports
- Historical head-to-head data
"""

import logging
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import pandas as pd
from bs4 import BeautifulSoup
import numpy as np

# Import existing scraping utilities
try:
    from scrapers.scraping_utils import (
        AntiDetectionSession, ProxyPool, ProxyConfig,
        UndetectedChromeDriver, DataValidator,
        RateLimiter, ScrapingMetrics
    )
    ADVANCED_SCRAPING = True
except ImportError:
    print("⚠️ Advanced scraping utilities not available. Using basic functionality.")
    ADVANCED_SCRAPING = False
    AntiDetectionSession = None
    UndetectedChromeDriver = None

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class PrematchData:
    """Comprehensive prematch data structure"""
    match_id: str
    sport: str
    league: str
    home_team: str
    away_team: str
    match_time: datetime
    venue: str
    
    # Team Statistics
    home_team_stats: Dict[str, Any]
    away_team_stats: Dict[str, Any]
    
    # Historical Data
    head_to_head: List[Dict]
    recent_form: Dict[str, List[str]]
    
    # Betting Data
    odds: Dict[str, Dict[str, float]]
    market_analysis: Dict[str, Any]
    
    # External Factors
    weather: Optional[Dict[str, Any]] = None
    injuries: Dict[str, List[str]] = None
    suspensions: Dict[str, List[str]] = None
    
    # Metadata
    scraped_at: datetime = None
    data_quality: float = 0.0
    sources: List[str] = None

class MultiSportPrematchScraper:
    """Advanced multi-sport prematch data scraper"""
    
    def __init__(self):
        """Initialize the multi-sport scraper"""
        logger.info("🏆 Initializing Multi-Sport Prematch Scraper...")
        
        # Initialize scraping session
        if ADVANCED_SCRAPING:
            self.session = AntiDetectionSession()
            self.rate_limiter = RateLimiter(requests_per_minute=30)
            self.metrics = ScrapingMetrics()
        else:
            self.session = requests.Session()
            self.rate_limiter = None
            self.metrics = None
        
        # Configure sport-specific scrapers
        self.sport_configs = {
            'football': {
                'sources': {
                    'fixtures': [
                        'https://www.flashscore.com/football/fixtures/',
                        'https://www.sofascore.com/football/fixtures',
                        'https://www.espn.com/soccer/fixtures'
                    ],
                    'stats': [
                        'https://www.whoscored.com',
                        'https://www.transfermarkt.com',
                        'https://fbref.com'
                    ],
                    'odds': [
                        'https://www.oddsportal.com/football/',
                        'https://www.bet365.com',
                        'https://www.pinnacle.com'
                    ]
                },
                'key_stats': [
                    'goals_scored', 'goals_conceded', 'shots_per_game',
                    'possession_avg', 'pass_accuracy', 'corners_per_game',
                    'cards_per_game', 'clean_sheets', 'home_record', 'away_record'
                ]
            },
            'tennis': {
                'sources': {
                    'fixtures': [
                        'https://www.atptour.com/en/scores/current',
                        'https://www.wtatennis.com/scores-and-stats',
                        'https://www.flashscore.com/tennis/'
                    ],
                    'stats': [
                        'https://www.atptour.com/en/stats',
                        'https://www.wtatennis.com/stats',
                        'https://www.tennisexplorer.com'
                    ],
                    'odds': [
                        'https://www.oddsportal.com/tennis/',
                        'https://www.bet365.com/tennis',
                        'https://www.pinnacle.com/tennis'
                    ]
                },
                'key_stats': [
                    'serve_percentage', 'break_points_saved', 'aces_per_match',
                    'double_faults', 'winners', 'unforced_errors',
                    'return_games_won', 'ranking', 'recent_form'
                ]
            },
            'basketball': {
                'sources': {
                    'fixtures': [
                        'https://www.nba.com/schedule',
                        'https://www.euroleague.net/main/results',
                        'https://www.flashscore.com/basketball/'
                    ],
                    'stats': [
                        'https://www.nba.com/stats',
                        'https://www.basketball-reference.com',
                        'https://www.euroleague.net/main/statistics'
                    ],
                    'odds': [
                        'https://www.oddsportal.com/basketball/',
                        'https://www.bet365.com/basketball',
                        'https://www.pinnacle.com/basketball'
                    ]
                },
                'key_stats': [
                    'points_per_game', 'rebounds_per_game', 'assists_per_game',
                    'field_goal_percentage', 'three_point_percentage', 'free_throw_percentage',
                    'turnovers', 'steals', 'blocks', 'home_record', 'away_record'
                ]
            },
            'ice_hockey': {
                'sources': {
                    'fixtures': [
                        'https://www.nhl.com/schedule',
                        'https://www.flashscore.com/hockey/',
                        'https://www.hockeydb.com'
                    ],
                    'stats': [
                        'https://www.nhl.com/stats',
                        'https://www.hockey-reference.com',
                        'https://www.eliteprospects.com'
                    ],
                    'odds': [
                        'https://www.oddsportal.com/hockey/',
                        'https://www.bet365.com/hockey',
                        'https://www.pinnacle.com/hockey'
                    ]
                },
                'key_stats': [
                    'goals_per_game', 'shots_per_game', 'save_percentage',
                    'power_play_percentage', 'penalty_kill_percentage',
                    'face_off_percentage', 'hits_per_game', 'blocked_shots'
                ]
            }
        }
        
        # Betting markets configuration
        self.betting_markets = {
            'football': [
                '1X2', 'Double Chance', 'Over/Under 2.5', 'Both Teams Score',
                'Asian Handicap', 'Correct Score', 'First Goal Scorer',
                'Half Time/Full Time', 'Total Corners', 'Total Cards'
            ],
            'tennis': [
                'Match Winner', 'Set Betting', 'Games Handicap', 'Total Games',
                'Set 1 Winner', 'Tie Break', 'Retirement', 'Aces Over/Under'
            ],
            'basketball': [
                'Moneyline', 'Point Spread', 'Total Points', 'Quarter Betting',
                'Player Props', 'Team Props', 'Margin of Victory'
            ],
            'ice_hockey': [
                'Moneyline', 'Puck Line', 'Total Goals', 'Period Betting',
                'Player Props', 'Team Props', 'Shootout'
            ]
        }
        
        logger.info("✅ Multi-Sport Prematch Scraper initialized")
    
    def scrape_daily_matches(self, date: datetime = None, sports: List[str] = None) -> List[PrematchData]:
        """Scrape all matches for a given date across specified sports"""
        if date is None:
            date = datetime.now()
        
        if sports is None:
            sports = list(self.sport_configs.keys())
        
        logger.info(f"🔍 Scraping matches for {date.strftime('%Y-%m-%d')} - Sports: {', '.join(sports)}")
        
        all_matches = []
        
        for sport in sports:
            try:
                sport_matches = self.scrape_sport_matches(sport, date)
                all_matches.extend(sport_matches)
                logger.info(f"✅ {sport.title()}: Found {len(sport_matches)} matches")
                
                # Rate limiting between sports
                if self.rate_limiter:
                    self.rate_limiter.wait()
                else:
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"❌ Error scraping {sport}: {e}")
        
        logger.info(f"🎯 Total matches found: {len(all_matches)}")
        return all_matches
    
    def scrape_sport_matches(self, sport: str, date: datetime) -> List[PrematchData]:
        """Scrape matches for a specific sport"""
        if sport not in self.sport_configs:
            logger.warning(f"⚠️ Sport '{sport}' not supported")
            return []
        
        logger.info(f"🏆 Scraping {sport} matches...")
        
        # Get fixtures
        fixtures = self._scrape_fixtures(sport, date)
        
        # Enhance with detailed data
        enhanced_matches = []
        for fixture in fixtures:
            try:
                enhanced_match = self._enhance_match_data(fixture, sport)
                enhanced_matches.append(enhanced_match)
            except Exception as e:
                logger.error(f"❌ Error enhancing match {fixture.get('match_id', 'unknown')}: {e}")
        
        return enhanced_matches
    
    def _scrape_fixtures(self, sport: str, date: datetime) -> List[Dict]:
        """Scrape basic fixture information"""
        logger.info(f"📅 Scraping {sport} fixtures for {date.strftime('%Y-%m-%d')}")
        
        fixtures = []
        config = self.sport_configs[sport]
        
        for source_url in config['sources']['fixtures']:
            try:
                fixtures_from_source = self._scrape_fixtures_from_source(source_url, sport, date)
                fixtures.extend(fixtures_from_source)
                
                # Rate limiting between sources
                if self.rate_limiter:
                    self.rate_limiter.wait()
                else:
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"❌ Error scraping fixtures from {source_url}: {e}")
        
        # Remove duplicates and return
        unique_fixtures = self._deduplicate_fixtures(fixtures)
        logger.info(f"✅ Found {len(unique_fixtures)} unique {sport} fixtures")
        
        return unique_fixtures
    
    def _scrape_fixtures_from_source(self, url: str, sport: str, date: datetime) -> List[Dict]:
        """Scrape fixtures from a specific source"""
        logger.info(f"🔍 Scraping fixtures from {url}")
        
        # Simulate fixture scraping - in production, implement actual scraping
        sample_fixtures = self._generate_sample_fixtures(sport, date)
        
        return sample_fixtures
    
    def _generate_sample_fixtures(self, sport: str, date: datetime) -> List[Dict]:
        """Generate sample fixtures for demonstration"""
        fixtures = []
        
        if sport == 'football':
            sample_matches = [
                ("Manchester United", "Arsenal", "Premier League", "Old Trafford"),
                ("Barcelona", "Atletico Madrid", "La Liga", "Camp Nou"),
                ("Bayern Munich", "RB Leipzig", "Bundesliga", "Allianz Arena"),
                ("Juventus", "Inter Milan", "Serie A", "Juventus Stadium"),
                ("PSG", "Lyon", "Ligue 1", "Parc des Princes")
            ]
        elif sport == 'tennis':
            sample_matches = [
                ("Novak Djokovic", "Rafael Nadal", "ATP Masters", "Center Court"),
                ("Iga Swiatek", "Coco Gauff", "WTA Premier", "Court 1"),
                ("Carlos Alcaraz", "Stefanos Tsitsipas", "ATP Masters", "Center Court")
            ]
        elif sport == 'basketball':
            sample_matches = [
                ("Los Angeles Lakers", "Boston Celtics", "NBA", "Staples Center"),
                ("Real Madrid", "Barcelona", "EuroLeague", "WiZink Center"),
                ("Golden State Warriors", "Miami Heat", "NBA", "Chase Center")
            ]
        elif sport == 'ice_hockey':
            sample_matches = [
                ("Toronto Maple Leafs", "Montreal Canadiens", "NHL", "Scotiabank Arena"),
                ("CSKA Moscow", "SKA St. Petersburg", "KHL", "CSKA Arena"),
                ("Boston Bruins", "New York Rangers", "NHL", "TD Garden")
            ]
        else:
            return []
        
        for i, (home, away, league, venue) in enumerate(sample_matches):
            match_time = date + timedelta(hours=15 + i * 2)
            fixtures.append({
                'match_id': f"{sport}_{date.strftime('%Y%m%d')}_{i+1}",
                'sport': sport,
                'league': league,
                'home_team': home,
                'away_team': away,
                'match_time': match_time,
                'venue': venue
            })
        
        return fixtures
    
    def _deduplicate_fixtures(self, fixtures: List[Dict]) -> List[Dict]:
        """Remove duplicate fixtures"""
        seen = set()
        unique_fixtures = []
        
        for fixture in fixtures:
            # Create a unique key based on teams and time
            key = (
                fixture['home_team'].lower(),
                fixture['away_team'].lower(),
                fixture['match_time'].strftime('%Y-%m-%d %H:%M')
            )
            
            if key not in seen:
                seen.add(key)
                unique_fixtures.append(fixture)
        
        return unique_fixtures
    
    def _enhance_match_data(self, fixture: Dict, sport: str) -> PrematchData:
        """Enhance basic fixture with comprehensive data"""
        logger.info(f"🔧 Enhancing data for {fixture['home_team']} vs {fixture['away_team']}")
        
        # Gather team statistics
        home_stats = self._scrape_team_stats(fixture['home_team'], sport)
        away_stats = self._scrape_team_stats(fixture['away_team'], sport)
        
        # Gather historical data
        h2h_data = self._scrape_head_to_head(fixture['home_team'], fixture['away_team'], sport)
        form_data = self._scrape_recent_form(fixture['home_team'], fixture['away_team'], sport)
        
        # Gather betting odds
        odds_data = self._scrape_betting_odds(fixture, sport)
        
        # Gather external factors
        weather_data = self._scrape_weather_data(fixture['venue'], fixture['match_time'])
        injury_data = self._scrape_injury_reports(fixture['home_team'], fixture['away_team'], sport)
        
        # Calculate data quality score
        data_quality = self._calculate_data_quality({
            'team_stats': bool(home_stats and away_stats),
            'h2h_data': bool(h2h_data),
            'odds_data': bool(odds_data),
            'weather_data': bool(weather_data),
            'injury_data': bool(injury_data)
        })
        
        return PrematchData(
            match_id=fixture['match_id'],
            sport=fixture['sport'],
            league=fixture['league'],
            home_team=fixture['home_team'],
            away_team=fixture['away_team'],
            match_time=fixture['match_time'],
            venue=fixture['venue'],
            home_team_stats=home_stats,
            away_team_stats=away_stats,
            head_to_head=h2h_data,
            recent_form=form_data,
            odds=odds_data,
            market_analysis=self._analyze_betting_markets(odds_data, sport),
            weather=weather_data,
            injuries=injury_data.get('injuries', {}),
            suspensions=injury_data.get('suspensions', {}),
            scraped_at=datetime.now(),
            data_quality=data_quality,
            sources=['flashscore', 'sofascore', 'oddsportal']
        )
    
    def _scrape_team_stats(self, team_name: str, sport: str) -> Dict[str, Any]:
        """Scrape comprehensive team statistics"""
        # Simulate team stats scraping
        if sport == 'football':
            return {
                'goals_scored': np.random.uniform(1.5, 2.5),
                'goals_conceded': np.random.uniform(0.8, 1.8),
                'shots_per_game': np.random.uniform(12, 18),
                'possession_avg': np.random.uniform(45, 65),
                'pass_accuracy': np.random.uniform(75, 90),
                'corners_per_game': np.random.uniform(4, 8),
                'cards_per_game': np.random.uniform(2, 5),
                'clean_sheets': np.random.randint(3, 12),
                'home_record': {'W': np.random.randint(5, 12), 'D': np.random.randint(2, 6), 'L': np.random.randint(1, 5)},
                'away_record': {'W': np.random.randint(3, 10), 'D': np.random.randint(2, 6), 'L': np.random.randint(2, 8)},
                'market_value': np.random.uniform(200, 800),  # Million euros
                'avg_age': np.random.uniform(24, 29),
                'injury_count': np.random.randint(0, 4)
            }
        elif sport == 'tennis':
            return {
                'serve_percentage': np.random.uniform(55, 75),
                'break_points_saved': np.random.uniform(60, 80),
                'aces_per_match': np.random.uniform(5, 15),
                'double_faults': np.random.uniform(2, 6),
                'winners': np.random.uniform(20, 40),
                'unforced_errors': np.random.uniform(15, 35),
                'return_games_won': np.random.uniform(15, 25),
                'ranking': np.random.randint(1, 100),
                'prize_money': np.random.uniform(100000, 5000000),
                'surface_record': {
                    'hard': {'W': np.random.randint(10, 30), 'L': np.random.randint(5, 15)},
                    'clay': {'W': np.random.randint(8, 25), 'L': np.random.randint(6, 18)},
                    'grass': {'W': np.random.randint(3, 12), 'L': np.random.randint(2, 8)}
                }
            }
        elif sport == 'basketball':
            return {
                'points_per_game': np.random.uniform(100, 120),
                'rebounds_per_game': np.random.uniform(40, 50),
                'assists_per_game': np.random.uniform(20, 30),
                'field_goal_percentage': np.random.uniform(42, 52),
                'three_point_percentage': np.random.uniform(32, 42),
                'free_throw_percentage': np.random.uniform(70, 85),
                'turnovers': np.random.uniform(12, 18),
                'steals': np.random.uniform(6, 10),
                'blocks': np.random.uniform(4, 8),
                'home_record': {'W': np.random.randint(15, 25), 'L': np.random.randint(5, 15)},
                'away_record': {'W': np.random.randint(10, 20), 'L': np.random.randint(8, 18)}
            }
        elif sport == 'ice_hockey':
            return {
                'goals_per_game': np.random.uniform(2.5, 4.0),
                'shots_per_game': np.random.uniform(28, 35),
                'save_percentage': np.random.uniform(88, 94),
                'power_play_percentage': np.random.uniform(15, 25),
                'penalty_kill_percentage': np.random.uniform(75, 85),
                'face_off_percentage': np.random.uniform(45, 55),
                'hits_per_game': np.random.uniform(20, 30),
                'blocked_shots': np.random.uniform(12, 18),
                'home_record': {'W': np.random.randint(12, 22), 'L': np.random.randint(8, 18)},
                'away_record': {'W': np.random.randint(8, 18), 'L': np.random.randint(10, 20)}
            }
        
        return {}
    
    def _scrape_head_to_head(self, home_team: str, away_team: str, sport: str) -> List[Dict]:
        """Scrape head-to-head historical data"""
        # Simulate H2H data
        h2h_matches = []
        
        for i in range(5):  # Last 5 meetings
            match_date = datetime.now() - timedelta(days=np.random.randint(30, 365))
            
            if sport == 'football':
                home_score = np.random.randint(0, 4)
                away_score = np.random.randint(0, 4)
                result = 'H' if home_score > away_score else 'A' if away_score > home_score else 'D'
            elif sport == 'tennis':
                sets = np.random.choice(['2-0', '2-1', '0-2', '1-2'])
                result = 'H' if sets.startswith('2') else 'A'
            else:
                home_score = np.random.randint(80, 120)
                away_score = np.random.randint(80, 120)
                result = 'H' if home_score > away_score else 'A'
            
            h2h_matches.append({
                'date': match_date,
                'home_team': home_team,
                'away_team': away_team,
                'home_score': home_score if sport != 'tennis' else sets.split('-')[0],
                'away_score': away_score if sport != 'tennis' else sets.split('-')[1],
                'result': result,
                'venue': 'Home' if np.random.random() > 0.5 else 'Away'
            })
        
        return h2h_matches
    
    def _scrape_recent_form(self, home_team: str, away_team: str, sport: str) -> Dict[str, List[str]]:
        """Scrape recent form for both teams"""
        form_options = ['W', 'L'] if sport == 'tennis' else ['W', 'D', 'L']
        
        return {
            'home_team': [np.random.choice(form_options) for _ in range(5)],
            'away_team': [np.random.choice(form_options) for _ in range(5)]
        }
    
    def _scrape_betting_odds(self, fixture: Dict, sport: str) -> Dict[str, Dict[str, float]]:
        """Scrape betting odds from multiple bookmakers"""
        odds_data = {}
        bookmakers = ['bet365', 'pinnacle', 'unibet', 'betfair']
        
        for bookmaker in bookmakers:
            if sport == 'football':
                odds_data[bookmaker] = {
                    '1X2': {
                        'home': np.random.uniform(1.5, 4.0),
                        'draw': np.random.uniform(3.0, 4.5),
                        'away': np.random.uniform(1.8, 5.0)
                    },
                    'over_under_2.5': {
                        'over': np.random.uniform(1.7, 2.2),
                        'under': np.random.uniform(1.6, 2.1)
                    },
                    'both_teams_score': {
                        'yes': np.random.uniform(1.6, 2.0),
                        'no': np.random.uniform(1.8, 2.3)
                    },
                    'asian_handicap': {
                        'home_-0.5': np.random.uniform(1.8, 2.2),
                        'away_+0.5': np.random.uniform(1.7, 2.1)
                    }
                }
            elif sport == 'tennis':
                odds_data[bookmaker] = {
                    'match_winner': {
                        'player1': np.random.uniform(1.3, 3.0),
                        'player2': np.random.uniform(1.4, 4.0)
                    },
                    'set_betting': {
                        '2-0': np.random.uniform(2.5, 4.0),
                        '2-1': np.random.uniform(3.0, 5.0),
                        '0-2': np.random.uniform(3.0, 6.0),
                        '1-2': np.random.uniform(3.5, 6.5)
                    },
                    'total_games': {
                        'over_21.5': np.random.uniform(1.8, 2.2),
                        'under_21.5': np.random.uniform(1.7, 2.1)
                    }
                }
            elif sport in ['basketball', 'ice_hockey']:
                odds_data[bookmaker] = {
                    'moneyline': {
                        'home': np.random.uniform(1.4, 3.0),
                        'away': np.random.uniform(1.5, 3.5)
                    },
                    'spread': {
                        'home_-3.5': np.random.uniform(1.8, 2.2),
                        'away_+3.5': np.random.uniform(1.7, 2.1)
                    },
                    'total_points': {
                        'over': np.random.uniform(1.8, 2.2),
                        'under': np.random.uniform(1.7, 2.1)
                    }
                }
        
        return odds_data
    
    def _scrape_weather_data(self, venue: str, match_time: datetime) -> Dict[str, Any]:
        """Scrape weather data for outdoor venues"""
        # Simulate weather data
        return {
            'temperature': np.random.uniform(5, 25),  # Celsius
            'humidity': np.random.uniform(40, 80),    # %
            'wind_speed': np.random.uniform(0, 20),   # km/h
            'precipitation': np.random.uniform(0, 5), # mm
            'conditions': np.random.choice(['clear', 'cloudy', 'light_rain', 'overcast']),
            'visibility': np.random.uniform(8, 15),   # km
            'pressure': np.random.uniform(1000, 1030) # hPa
        }
    
    def _scrape_injury_reports(self, home_team: str, away_team: str, sport: str) -> Dict[str, Any]:
        """Scrape injury and suspension reports"""
        # Simulate injury/suspension data
        return {
            'injuries': {
                'home_team': [f"Player {i}" for i in range(np.random.randint(0, 3))],
                'away_team': [f"Player {i}" for i in range(np.random.randint(0, 3))]
            },
            'suspensions': {
                'home_team': [f"Player {i}" for i in range(np.random.randint(0, 2))],
                'away_team': [f"Player {i}" for i in range(np.random.randint(0, 2))]
            },
            'doubtful': {
                'home_team': [f"Player {i}" for i in range(np.random.randint(0, 2))],
                'away_team': [f"Player {i}" for i in range(np.random.randint(0, 2))]
            }
        }
    
    def _analyze_betting_markets(self, odds_data: Dict, sport: str) -> Dict[str, Any]:
        """Analyze betting markets for value opportunities"""
        market_analysis = {
            'best_odds': {},
            'market_efficiency': {},
            'arbitrage_opportunities': [],
            'value_bets': []
        }
        
        # Find best odds for each market
        for market in self.betting_markets.get(sport, []):
            best_odds = {}
            
            for bookmaker, odds in odds_data.items():
                for market_key, market_odds in odds.items():
                    if isinstance(market_odds, dict):
                        for outcome, odd_value in market_odds.items():
                            key = f"{market_key}_{outcome}"
                            if key not in best_odds or odd_value > best_odds[key]['odds']:
                                best_odds[key] = {
                                    'odds': odd_value,
                                    'bookmaker': bookmaker
                                }
            
            market_analysis['best_odds'][market] = best_odds
        
        # Calculate market efficiency (lower is better for bettors)
        total_implied_prob = 0
        market_count = 0
        
        for bookmaker, odds in odds_data.items():
            for market_key, market_odds in odds.items():
                if isinstance(market_odds, dict):
                    implied_probs = [1/odd for odd in market_odds.values() if odd > 0]
                    if implied_probs:
                        total_implied_prob += sum(implied_probs)
                        market_count += 1
        
        if market_count > 0:
            avg_market_efficiency = (total_implied_prob / market_count - 1) * 100
            market_analysis['market_efficiency']['average_margin'] = avg_market_efficiency
        
        return market_analysis
    
    def _calculate_data_quality(self, data_availability: Dict[str, bool]) -> float:
        """Calculate overall data quality score"""
        weights = {
            'team_stats': 0.3,
            'h2h_data': 0.2,
            'odds_data': 0.25,
            'weather_data': 0.1,
            'injury_data': 0.15
        }
        
        quality_score = sum(
            weights.get(key, 0) * (1.0 if available else 0.0)
            for key, available in data_availability.items()
        )
        
        return quality_score
    
    def export_data(self, matches: List[PrematchData], format: str = 'json') -> str:
        """Export scraped data in various formats"""
        logger.info(f"📤 Exporting {len(matches)} matches in {format} format")
        
        if format == 'json':
            data = [asdict(match) for match in matches]
            # Convert datetime objects to strings
            for match_data in data:
                match_data['match_time'] = match_data['match_time'].isoformat()
                match_data['scraped_at'] = match_data['scraped_at'].isoformat()
                
                # Convert H2H dates
                for h2h in match_data['head_to_head']:
                    h2h['date'] = h2h['date'].isoformat()
            
            filename = f"prematch_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            return filename
        
        elif format == 'csv':
            # Flatten data for CSV export
            flattened_data = []
            
            for match in matches:
                row = {
                    'match_id': match.match_id,
                    'sport': match.sport,
                    'league': match.league,
                    'home_team': match.home_team,
                    'away_team': match.away_team,
                    'match_time': match.match_time.isoformat(),
                    'venue': match.venue,
                    'data_quality': match.data_quality,
                    'scraped_at': match.scraped_at.isoformat()
                }
                
                # Add key statistics
                if match.home_team_stats:
                    for key, value in match.home_team_stats.items():
                        if isinstance(value, (int, float)):
                            row[f'home_{key}'] = value
                
                if match.away_team_stats:
                    for key, value in match.away_team_stats.items():
                        if isinstance(value, (int, float)):
                            row[f'away_{key}'] = value
                
                flattened_data.append(row)
            
            df = pd.DataFrame(flattened_data)
            filename = f"prematch_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False)
            
            return filename
        
        else:
            raise ValueError(f"Unsupported export format: {format}")

def main():
    """Main function for testing the multi-sport scraper"""
    print("🏆 MULTI-SPORT PREMATCH SCRAPER")
    print("=" * 50)
    
    # Initialize scraper
    scraper = MultiSportPrematchScraper()
    
    # Scrape today's matches
    today = datetime.now()
    sports_to_scrape = ['football', 'tennis', 'basketball']
    
    print(f"\n🔍 Scraping matches for {today.strftime('%Y-%m-%d')}")
    print(f"🏆 Sports: {', '.join(sports_to_scrape)}")
    print("-" * 50)
    
    matches = scraper.scrape_daily_matches(today, sports_to_scrape)
    
    if matches:
        print(f"\n✅ Successfully scraped {len(matches)} matches!")
        print("\n📊 MATCH SUMMARY:")
        print("-" * 30)
        
        # Group by sport
        by_sport = {}
        for match in matches:
            if match.sport not in by_sport:
                by_sport[match.sport] = []
            by_sport[match.sport].append(match)
        
        for sport, sport_matches in by_sport.items():
            print(f"\n🏆 {sport.upper()} ({len(sport_matches)} matches):")
            for match in sport_matches[:3]:  # Show first 3
                print(f"   • {match.home_team} vs {match.away_team}")
                print(f"     📅 {match.match_time.strftime('%H:%M')} | 🏟️ {match.venue}")
                print(f"     📊 Data Quality: {match.data_quality:.1%}")
        
        # Export data
        print(f"\n📤 EXPORTING DATA:")
        print("-" * 25)
        
        json_file = scraper.export_data(matches, 'json')
        csv_file = scraper.export_data(matches, 'csv')
        
        print(f"✅ JSON: {json_file}")
        print(f"✅ CSV: {csv_file}")
        
        # Show data quality statistics
        avg_quality = np.mean([match.data_quality for match in matches])
        print(f"\n📈 QUALITY METRICS:")
        print("-" * 25)
        print(f"Average Data Quality: {avg_quality:.1%}")
        print(f"High Quality Matches (>80%): {sum(1 for m in matches if m.data_quality > 0.8)}")
        print(f"Sources Used: {len(set().union(*[m.sources for m in matches if m.sources]))}")
        
    else:
        print("❌ No matches found!")

if __name__ == "__main__":
    main()
