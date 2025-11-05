"""
Ultimate Multi-Source Web Scraping System
=========================================

Advanced scraping system that integrates:
- SofaScore (xG, momentum, detailed stats)
- FotMob (lineups, injuries, form)
- FlashScore (fastest live updates)
- Betfury (live odds, movements)
- Understat (advanced xG models)
- API Football (base statistics)

Enhanced with:
- GPT-4 analysis
- Data validation and cross-referencing
- Rate limiting and error handling
- Unified data merge
"""

import asyncio
import aiohttp
import time
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass, asdict
import random
import hashlib

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import all scrapers
from src.scrapers.sofascore_scraper import SofaScoreScraper
from src.scrapers.fotmob_scraper import FotMobScraper
from src.scrapers.flashscore_scraper import FlashScoreScraper
from src.scrapers.betfury_scraper import BetfuryScraper
from src.scrapers.understat_scraper import UnderstatScraper
from src.scrapers.api_football_scraper import APIFootballScraper

@dataclass
class UnifiedMatchData:
    """Unified data structure for all scraped information"""
    
    # Basic match info
    match_id: str
    home_team: str
    away_team: str
    league: str
    timestamp: str
    source_confidence: float  # How confident we are in this data (0-1)
    
    # Live match data
    score: Dict[str, int]
    minute: int
    status: str  # LIVE, FINISHED, PAUSED
    
    # Advanced statistics
    xG: Dict[str, float]
    xA: Dict[str, float] 
    shots: Dict[str, int]
    shots_on_target: Dict[str, int]
    possession: Dict[str, float]
    corners: Dict[str, int]
    dangerous_attacks: Dict[str, int]
    
    # Momentum indicators
    momentum: Dict[str, float]
    pressure_index: Dict[str, float]
    big_chances: Dict[str, int]
    shot_quality_avg: Dict[str, float]
    
    # Team information
    lineups: Dict[str, List[Dict[str, Any]]]
    injuries: Dict[str, List[str]]
    key_players_missing: Dict[str, List[str]]
    form: Dict[str, List[str]]
    elo: Dict[str, float]
    
    # Odds and value
    odds: Dict[str, float]
    odds_movement: List[Dict[str, Any]]
    sharp_money_indicator: Optional[float]
    value_indicators: Dict[str, float]
    
    # Event timeline
    events: List[Dict[str, Any]]
    last_update: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    def get_confidence_score(self) -> float:
        """Calculate overall confidence score based on data completeness"""
        required_fields = [
            'xG', 'shots', 'possession', 'momentum', 
            'lineups', 'odds', 'events'
        ]
        
        complete_count = 0
        for field in required_fields:
            if hasattr(self, field) and getattr(self, field) is not None:
                if isinstance(getattr(self, field), dict):
                    if any(getattr(self, field).values()):
                        complete_count += 1
                elif isinstance(getattr(self, field), list):
                    if getattr(self, field):
                        complete_count += 1
        
        return complete_count / len(required_fields)

class UnifiedDataScraper:
    """
    Main orchestrator for multi-source scraping
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize all scrapers
        self.scrapers = {
            'sofascore': SofaScoreScraper(config.get('sofascore', {})),
            'fotmob': FotMobScraper(config.get('fotmob', {})),
            'flashscore': FlashScoreScraper(config.get('flashscore', {})),
            'betfury': BetfuryScraper(config.get('betfury', {})),
            'understat': UnderstatScraper(config.get('understat', {})),
            'api_football': APIFootballScraper(config.get('api_football', {}))
        }
        
        # Rate limiting per source
        self.rate_limits = {
            'sofascore': config.get('rate_limits', {}).get('sofascore', 2.0),
            'fotmob': config.get('rate_limits', {}).get('fotmob', 3.0),
            'flashscore': config.get('rate_limits', {}).get('flashscore', 2.5),
            'betfury': config.get('rate_limits', {}).get('betfury', 5.0),
            'understat': config.get('rate_limits', {}).get('understat', 4.0),
            'api_football': config.get('rate_limits', {}).get('api_football', 1.0)
        }
        
        # User agent rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)',
            'Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X)'
        ]
        
        self.last_request = {}
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get_unified_match_data(
        self, 
        match_info: Dict[str, Any],
        timeout: int = 30
    ) -> Optional[UnifiedMatchData]:
        """
        Get comprehensive match data from all sources
        """
        match_id = match_info.get('id')
        home_team = match_info.get('home_team', '')
        away_team = match_info.get('away_team', '')
        league = match_info.get('league', '')
        
        logger.info(f"🔍 Scraping: {home_team} vs {away_team} (ID: {match_id})")
        
        try:
            # Scrape all sources in parallel with timeout
            tasks = []
            for source_name, scraper in self.scrapers.items():
                task = asyncio.create_task(
                    self.safe_scrape(source_name, scraper, match_info, timeout)
                )
                tasks.append(task)
            
            # Wait for all tasks with overall timeout
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout
            )
            
            # Process results
            source_data = {}
            for i, result in enumerate(results):
                source_name = list(self.scrapers.keys())[i]
                if isinstance(result, Exception):
                    logger.warning(f"❌ {source_name} failed: {result}")
                    source_data[source_name] = None
                else:
                    source_data[source_name] = result
            
            # Merge all data
            unified_data = await self.merge_unified_data(
                source_data, match_id, home_team, away_team, league
            )
            
            if unified_data:
                logger.info(f"✅ Unified data: {unified_data.get_confidence_score():.2%} confidence")
                
            return unified_data
            
        except asyncio.TimeoutError:
            logger.error(f"⏰ Timeout scraping match {match_id}")
            return None
        except Exception as e:
            logger.error(f"💥 Error in unified scraping: {e}")
            return None
    
    async def safe_scrape(
        self, 
        source_name: str, 
        scraper: Any, 
        match_info: Dict[str, Any],
        timeout: int
    ) -> Optional[Dict[str, Any]]:
        """
        Scrape with rate limiting, retries, and error handling
        """
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Rate limiting
                await self.enforce_rate_limit(source_name)
                
                # Scrape with timeout
                data = await asyncio.wait_for(
                    scraper.scrape_match(match_info),
                    timeout=timeout
                )
                
                if data:
                    logger.info(f"✅ {source_name}: Success")
                    return data
                else:
                    logger.warning(f"⚠️ {source_name}: No data returned")
                    
            except asyncio.TimeoutError:
                logger.warning(f"⏰ {source_name}: Timeout (attempt {attempt + 1})")
            except Exception as e:
                logger.warning(f"❌ {source_name}: Error (attempt {attempt + 1}) - {e}")
                
            # Exponential backoff
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(wait_time)
        
        logger.error(f"💀 {source_name}: All attempts failed")
        return None
    
    async def enforce_rate_limit(self, source_name: str):
        """Enforce rate limiting per source"""
        current_time = time.time()
        
        if source_name in self.last_request:
            elapsed = current_time - self.last_request[source_name]
            required_delay = self.rate_limits[source_name]
            
            if elapsed < required_delay:
                wait_time = required_delay - elapsed
                logger.debug(f"🕐 Rate limiting {source_name}: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
        
        self.last_request[source_name] = time.time()
    
    async def merge_unified_data(
        self,
        source_data: Dict[str, Optional[Dict]],
        match_id: str,
        home_team: str,
        away_team: str,
        league: str
    ) -> Optional[UnifiedMatchData]:
        """
        Merge data from all sources with priority system
        """
        try:
            # Create base unified data structure
            unified = UnifiedMatchData(
                match_id=match_id,
                home_team=home_team,
                away_team=away_team,
                league=league,
                timestamp=datetime.now().isoformat(),
                source_confidence=0.0,
                
                # Live match data
                score={'home': 0, 'away': 0},
                minute=0,
                status='UNKNOWN',
                
                # Advanced statistics (initialized empty)
                xG={'home': 0.0, 'away': 0.0},
                xA={'home': 0.0, 'away': 0.0},
                shots={'home': 0, 'away': 0},
                shots_on_target={'home': 0, 'away': 0},
                possession={'home': 50.0, 'away': 50.0},
                corners={'home': 0, 'away': 0},
                dangerous_attacks={'home': 0, 'away': 0},
                
                # Momentum indicators
                momentum={'home': 0.0, 'away': 0.0},
                pressure_index={'home': 0.0, 'away': 0.0},
                big_chances={'home': 0, 'away': 0},
                shot_quality_avg={'home': 0.0, 'away': 0.0},
                
                # Team information
                lineups={'home': [], 'away': []},
                injuries={'home': [], 'away': []},
                key_players_missing={'home': [], 'away': []},
                form={'home': [], 'away': []},
                elo={'home': 1500.0, 'away': 1500.0},
                
                # Odds and value
                odds={},
                odds_movement=[],
                sharp_money_indicator=None,
                value_indicators={},
                
                # Event timeline
                events=[],
                last_update=datetime.now().isoformat()
            )
            
            # Source priorities for different data types
            priorities = {
                'sofascore': {'xG': 10, 'momentum': 10, 'live_stats': 9},
                'understat': {'xG': 10, 'shot_analysis': 10},
                'fotmob': {'lineups': 10, 'injuries': 9, 'form': 8},
                'flashscore': {'live_updates': 10, 'events': 9},
                'betfury': {'odds': 10, 'odds_movement': 10},
                'api_football': {'base_stats': 7, 'prematch': 6}
            }
            
            # Apply data from each source
            for source_name, data in source_data.items():
                if data:
                    unified = self.apply_source_data(unified, source_name, data, priorities)
            
            # Calculate derived metrics
            unified = self.calculate_derived_metrics(unified)
            
            # Update confidence score
            unified.source_confidence = unified.get_confidence_score()
            
            return unified
            
        except Exception as e:
            logger.error(f"💥 Error merging data: {e}")
            return None
    
    def apply_source_data(
        self,
        unified: UnifiedMatchData,
        source_name: str,
        data: Dict[str, Any],
        priorities: Dict[str, Dict[str, int]]
    ) -> UnifiedMatchData:
        """
        Apply data from specific source with priority system
        """
        source_priorities = priorities.get(source_name, {})
        
        # Update basic match info (usually from first available source)
        if not unified.score['home'] and 'score' in data:
            unified.score = data['score']
        
        if not unified.minute and 'minute' in data:
            unified.minute = data['minute']
            
        if not unified.status or unified.status == 'UNKNOWN':
            if 'status' in data:
                unified.status = data['status']
        
        # xG data (prefer SofaScore/Understat)
        if 'xG' in data and 'xG' in source_priorities:
            xg_home = data['xG'].get('home')
            xg_away = data['xG'].get('away')
            
            if xg_home is not None and xg_away is not None:
                # Use highest priority source for xG
                if (source_priorities.get('xG', 0) >= 
                    (priorities.get('sofascore', {}).get('xG', 0) if unified.xG['home'] else 0)):
                    unified.xG = {'home': xg_home, 'away': xg_away}
        
        # Live statistics
        if 'shots' in data:
            unified.shots = {**unified.shots, **data['shots']}
            
        if 'shots_on_target' in data:
            unified.shots_on_target = {**unified.shots_on_target, **data['shots_on_target']}
            
        if 'possession' in data:
            unified.possession = {**unified.possession, **data['possession']}
            
        if 'corners' in data:
            unified.corners = {**unified.corners, **data['corners']}
        
        # Lineups (prefer FotMob)
        if 'lineups' in data and source_name == 'fotmob':
            unified.lineups = data['lineups']
            if 'injuries' in data:
                unified.injuries = data['injuries']
        
        # Odds (prefer Betfury)
        if 'odds' in data and source_name == 'betfury':
            unified.odds = data['odds']
            if 'odds_movement' in data:
                unified.odds_movement = data['odds_movement']
        
        # Events (prefer FlashScore)
        if 'events' in data and source_name == 'flashscore':
            unified.events = data['events']
        
        return unified
    
    def calculate_derived_metrics(self, unified: UnifiedMatchData) -> UnifiedMatchData:
        """
        Calculate advanced metrics from merged data
        """
        # Momentum trend
        if unified.momentum['home'] and unified.momentum['away']:
            unified.momentum['trend'] = unified.momentum['home'] - unified.momentum['away']
        
        # Shot quality average
        if unified.xG['home'] and unified.shots['home']:
            unified.shot_quality_avg['home'] = unified.xG['home'] / unified.shots['home']
        if unified.xG['away'] and unified.shots['away']:
            unified.shot_quality_avg['away'] = unified.xG['away'] / unified.shots['away']
        
        # Big chances conversion
        if unified.big_chances['home'] and unified.shots['home']:
            unified.big_chances['conversion_rate'] = (
                unified.score['home'] / unified.big_chances['home'] 
                if unified.big_chances['home'] > 0 else 0
            )
        
        # Value indicators (xG vs odds)
        if unified.xG['home'] > 0 and unified.odds.get('home'):
            # Simple value calculation
            xg_prob = self.xg_to_probability(unified.xG['home'], unified.xG['away'])
            odds_prob = 1 / unified.odds['home']
            unified.value_indicators['home_value'] = xg_prob - odds_prob
        
        if unified.xG['away'] > 0 and unified.odds.get('away'):
            xg_prob = self.xg_to_probability(unified.xG['away'], unified.xG['home'])
            odds_prob = 1 / unified.odds['away']
            unified.value_indicators['away_value'] = xg_prob - odds_prob
        
        return unified
    
    def xg_to_probability(self, team_xg: float, opponent_xg: float) -> float:
        """
        Convert xG to win probability using Poisson distribution
        """
        try:
            import scipy.stats as stats
            
            # Calculate win probability (simplified Poisson model)
            prob_win = 0
            max_goals = 10
            
            for team_goals in range(max_goals + 1):
                for opp_goals in range(max_goals):
                    if team_goals > opp_goals:
                        prob_win += (stats.poisson.pmf(team_goals, team_xg) * 
                                   stats.poisson.pmf(opp_goals, opponent_xg))
            
            return prob_win
            
        except ImportError:
            # Fallback without scipy
            return team_xg / (team_xg + opponent_xg)
    
    async def quick_filter_matches(
        self, 
        matches: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Quick filter to identify promising matches before deep scraping
        """
        promising = []
        
        for match in matches:
            score = 0
            
            # Score based on match characteristics
            minute = match.get('minute', 0)
            
            # Active matches (not too early, not finished)
            if 15 <= minute <= 85:
                score += 3
            
            # High-scoring matches
            home_score = match.get('home_score', 0)
            away_score = match.get('away_score', 0)
            total_goals = home_score + away_score
            
            if total_goals >= 2:
                score += 2
            
            # Competitive matches
            if abs(home_score - away_score) <= 1:
                score += 2
            
            # Major leagues get priority
            league = match.get('league', '').lower()
            major_leagues = ['premier', 'champions', 'bundesliga', 'serie', 'ligue']
            if any(major in league for major in major_leagues):
                score += 2
            
            # Strong teams
            home_team = match.get('home_team', '')
            away_team = match.get('away_team', '')
            if self.is_strong_team(home_team) and self.is_strong_team(away_team):
                score += 2
            
            if score >= 5:  # Threshold for promising matches
                promising.append(match)
        
        # Sort by score
        promising.sort(key=lambda x: x.get('promising_score', 0), reverse=True)
        
        logger.info(f"📊 Filtered {len(promising)} promising matches from {len(matches)} total")
        return promising[:10]  # Return top 10
    
    def is_strong_team(self, team_name: str) -> bool:
        """
        Quick check if team is considered strong (simplified)
        """
        strong_teams = [
            'manchester', 'liverpool', 'arsenal', 'chelsea', 'tottenham',
            'real madrid', 'barcelona', 'atletico madrid',
            'bayern', 'borussia', 'psg', 'marseille',
            'juventus', 'inter', 'milan', 'napoli'
        ]
        
        team_lower = team_name.lower()
        return any(team in team_lower for team in strong_teams)