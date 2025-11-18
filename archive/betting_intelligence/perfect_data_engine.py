#!/usr/bin/env python3
"""
🎯 LAYER 1: PERFECT DATA ENGINE
===============================
Täydellinen datan keräysrakenne joka toimittaa standardoidun MatchDataPackage:n Layer 2:lle.

Vastuualue:
- Ottelujen löytäminen (7 päivää eteenpäin)
- Tilastojen keräys (100+ per ottelu)
- Kertoimien aggregaatio (10+ vedonvälittäjää)
- Datan laadun validointi
- Historiallisen datan hallinta

Lähteet: FlashScore, SofaScore, OddsPortal, Understat
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TeamStats:
    """Joukkueen tilastot"""
    team_name: str
    sport: str
    
    # Perusstatistiikka
    matches_played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    win_percentage: float = 0.0
    
    # Laji-spesifiset tilastot
    goals_scored: Optional[int] = None
    goals_conceded: Optional[int] = None
    clean_sheets: Optional[int] = None
    
    # Muoto-analyysi
    recent_form: List[str] = field(default_factory=list)  # ['W', 'L', 'D', 'W', 'L']
    home_form: List[str] = field(default_factory=list)
    away_form: List[str] = field(default_factory=list)
    
    # Laajennetut tilastot
    extended_stats: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlayerStats:
    """Pelaajan tilastot (tennis)"""
    player_name: str
    ranking: Optional[int] = None
    
    # Tennis-spesifiset
    serve_percentage: Optional[float] = None
    break_points_saved: Optional[float] = None
    aces_per_match: Optional[float] = None
    double_faults_per_match: Optional[float] = None
    
    # Kenttäspesifiset tilastot
    hard_court_record: Dict[str, int] = field(default_factory=dict)
    clay_court_record: Dict[str, int] = field(default_factory=dict)
    grass_court_record: Dict[str, int] = field(default_factory=dict)
    
    # Muoto
    recent_form: List[str] = field(default_factory=list)
    
    # Laajennetut tilastot
    extended_stats: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OddsData:
    """Kertoimet eri vedonvälittäjiltä"""
    bookmaker: str
    market: str  # 'h2h', 'over_under', 'handicap', etc.
    outcomes: Dict[str, float]  # {'home': 2.10, 'away': 1.85}
    timestamp: datetime
    
    # Lisätiedot
    margin: Optional[float] = None
    liquidity_score: Optional[float] = None


@dataclass
class HeadToHeadData:
    """Head-to-head tilastot"""
    team1: str
    team2: str
    total_matches: int
    team1_wins: int
    team2_wins: int
    draws: int
    
    # Viimeisimmät ottelut
    recent_matches: List[Dict[str, Any]] = field(default_factory=list)
    
    # Venue-spesifiset tilastot
    home_advantage: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MatchDataPackage:
    """
    Standardoitu ottelu-paketti Layer 2:lle
    Sisältää kaiken tarvittavan datan ML-päätöksentekoa varten
    """
    # Perusinfo
    match_id: str
    sport: str
    league: str
    home_team: str
    away_team: str
    match_time: datetime
    venue: Optional[str] = None
    
    # Tilastot
    home_team_stats: Optional[TeamStats] = None
    away_team_stats: Optional[TeamStats] = None
    home_player_stats: Optional[PlayerStats] = None  # Tennis
    away_player_stats: Optional[PlayerStats] = None  # Tennis
    
    # Historiallinen data
    head_to_head: Optional[HeadToHeadData] = None
    
    # Kertoimet
    odds_data: List[OddsData] = field(default_factory=list)
    best_odds: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Ulkoiset tekijät
    weather: Optional[Dict[str, Any]] = None
    injuries: List[str] = field(default_factory=list)
    suspensions: List[str] = field(default_factory=list)
    
    # Datan laatu
    data_quality_score: float = 0.0
    data_sources: List[str] = field(default_factory=list)
    completeness_score: float = 0.0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


class PerfectDataEngine:
    """
    Layer 1: Perfect Data Engine
    
    Kerää täydellisen datan useista lähteistä ja toimittaa standardoidun
    MatchDataPackage:n Layer 2:lle päätöksentekoa varten.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Perfect Data Engine
        
        Args:
            config: Configuration dictionary
        """
        logger.info("🎯 Initializing Perfect Data Engine (Layer 1)...")
        
        self.config = config or self._load_default_config()
        
        # Data sources
        self.data_sources = {
            'flashscore': True,
            'sofascore': True,
            'oddsportal': True,
            'understat': True  # Football only
        }
        
        # Supported sports
        self.supported_sports = ['tennis', 'football', 'basketball', 'ice_hockey']
        
        # Cache for performance
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        logger.info("✅ Perfect Data Engine initialized")
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        return {
            'lookback_days': 7,
            'min_data_quality': 0.7,
            'max_concurrent_requests': 5,
            'request_delay': 1.0,
            'cache_enabled': True
        }
    
    async def discover_matches(self, sports: List[str] = None, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Löytää tulevat ottelut seuraavalle viikolle
        
        Args:
            sports: Lista lajeista (jos None, käytä kaikkia)
            days_ahead: Montako päivää eteenpäin
            
        Returns:
            Lista perusottelutiedoista
        """
        logger.info(f"🔍 Discovering matches for next {days_ahead} days...")
        
        if sports is None:
            sports = self.supported_sports
        
        all_matches = []
        
        for sport in sports:
            try:
                sport_matches = await self._discover_sport_matches(sport, days_ahead)
                all_matches.extend(sport_matches)
                logger.info(f"✅ {sport}: Found {len(sport_matches)} matches")
            except Exception as e:
                logger.error(f"❌ Error discovering {sport} matches: {e}")
        
        logger.info(f"🎯 Total matches discovered: {len(all_matches)}")
        return all_matches
    
    async def _discover_sport_matches(self, sport: str, days_ahead: int) -> List[Dict[str, Any]]:
        """Löytää ottelut tietylle lajille"""
        
        # Tässä olisi integraatio oikeisiin scrapereihin
        # Nyt palautetaan demo-dataa
        
        matches = []
        
        if sport == 'tennis':
            matches = [
                {
                    'match_id': f'tennis_atp_001_{datetime.now().strftime("%Y%m%d")}',
                    'sport': 'tennis',
                    'league': 'ATP Masters',
                    'home_team': 'Novak Djokovic',
                    'away_team': 'Carlos Alcaraz',
                    'match_time': datetime.now() + timedelta(hours=24),
                    'venue': 'Center Court'
                },
                {
                    'match_id': f'tennis_wta_001_{datetime.now().strftime("%Y%m%d")}',
                    'sport': 'tennis',
                    'league': 'WTA Premier',
                    'home_team': 'Iga Swiatek',
                    'away_team': 'Coco Gauff',
                    'match_time': datetime.now() + timedelta(hours=30),
                    'venue': 'Court 1'
                }
            ]
        elif sport == 'football':
            matches = [
                {
                    'match_id': f'football_epl_001_{datetime.now().strftime("%Y%m%d")}',
                    'sport': 'football',
                    'league': 'Premier League',
                    'home_team': 'Manchester City',
                    'away_team': 'Arsenal',
                    'match_time': datetime.now() + timedelta(hours=48),
                    'venue': 'Etihad Stadium'
                },
                {
                    'match_id': f'football_laliga_001_{datetime.now().strftime("%Y%m%d")}',
                    'sport': 'football',
                    'league': 'La Liga',
                    'home_team': 'Real Madrid',
                    'away_team': 'Barcelona',
                    'match_time': datetime.now() + timedelta(hours=72),
                    'venue': 'Santiago Bernabeu'
                }
            ]
        
        return matches
    
    async def create_match_package(self, match_info: Dict[str, Any]) -> MatchDataPackage:
        """
        Luo täydellinen MatchDataPackage yhdelle ottelulle
        
        Args:
            match_info: Perusottelutiedot
            
        Returns:
            Täydellinen MatchDataPackage
        """
        logger.info(f"📦 Creating match package for {match_info['home_team']} vs {match_info['away_team']}")
        
        # Luo perus-package
        package = MatchDataPackage(
            match_id=match_info['match_id'],
            sport=match_info['sport'],
            league=match_info['league'],
            home_team=match_info['home_team'],
            away_team=match_info['away_team'],
            match_time=match_info['match_time'],
            venue=match_info.get('venue')
        )
        
        # Kerää data rinnakkain
        tasks = [
            self._collect_team_stats(package),
            self._collect_odds_data(package),
            self._collect_head_to_head(package),
            self._collect_external_factors(package)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Käsittele tulokset
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"⚠️ Task {i} failed: {result}")
        
        # Laske datan laatu
        package.data_quality_score = self._calculate_data_quality(package)
        package.completeness_score = self._calculate_completeness(package)
        
        logger.info(f"✅ Match package created - Quality: {package.data_quality_score:.2f}")
        return package
    
    async def _collect_team_stats(self, package: MatchDataPackage):
        """Kerää joukkueiden/pelaajien tilastot"""
        logger.info(f"📊 Collecting team stats for {package.sport}...")
        
        if package.sport == 'tennis':
            # Tennis: kerää pelaajatilastot
            package.home_player_stats = await self._get_player_stats(package.home_team, package.sport)
            package.away_player_stats = await self._get_player_stats(package.away_team, package.sport)
        else:
            # Muut lajit: kerää joukkuetilastot
            package.home_team_stats = await self._get_team_stats(package.home_team, package.sport, package.league)
            package.away_team_stats = await self._get_team_stats(package.away_team, package.sport, package.league)
        
        package.data_sources.append('team_stats')
    
    async def _get_team_stats(self, team_name: str, sport: str, league: str) -> TeamStats:
        """Hae joukkueen tilastot"""
        
        # Tässä olisi integraatio oikeisiin API:hin/scrapereihin
        # Nyt palautetaan demo-dataa
        
        stats = TeamStats(
            team_name=team_name,
            sport=sport,
            matches_played=20,
            wins=12,
            draws=4,
            losses=4,
            win_percentage=0.60,
            recent_form=['W', 'W', 'D', 'W', 'L']
        )
        
        if sport == 'football':
            stats.goals_scored = 35
            stats.goals_conceded = 18
            stats.clean_sheets = 8
            stats.extended_stats = {
                'shots_per_game': 15.2,
                'possession_avg': 58.5,
                'pass_accuracy': 87.3,
                'corners_per_game': 6.8
            }
        
        return stats
    
    async def _get_player_stats(self, player_name: str, sport: str) -> PlayerStats:
        """Hae pelaajan tilastot (tennis)"""
        
        stats = PlayerStats(
            player_name=player_name,
            ranking=5,
            serve_percentage=65.2,
            break_points_saved=68.5,
            aces_per_match=8.3,
            double_faults_per_match=2.1,
            recent_form=['W', 'W', 'W', 'L', 'W']
        )
        
        stats.hard_court_record = {'wins': 25, 'losses': 8}
        stats.clay_court_record = {'wins': 18, 'losses': 12}
        stats.grass_court_record = {'wins': 12, 'losses': 5}
        
        return stats
    
    async def _collect_odds_data(self, package: MatchDataPackage):
        """Kerää kertoimet useista lähteistä"""
        logger.info("💰 Collecting odds data...")
        
        # Simuloi kertoimien keräys useista lähteistä
        bookmakers = ['Bet365', 'Pinnacle', 'Betfair', 'Unibet', 'William Hill']
        
        for bookmaker in bookmakers:
            odds = OddsData(
                bookmaker=bookmaker,
                market='h2h',
                outcomes={
                    package.home_team: 2.10 + (hash(bookmaker) % 20) / 100,
                    package.away_team: 1.85 + (hash(bookmaker) % 15) / 100
                },
                timestamp=datetime.now(),
                margin=5.2,
                liquidity_score=0.85
            )
            package.odds_data.append(odds)
        
        # Laske parhaat kertoimet
        package.best_odds = self._calculate_best_odds(package.odds_data)
        package.data_sources.append('odds_data')
    
    def _calculate_best_odds(self, odds_data: List[OddsData]) -> Dict[str, Dict[str, float]]:
        """Laske parhaat kertoimet jokaiselle tulokselle"""
        best_odds = {}
        
        for odds in odds_data:
            market = odds.market
            if market not in best_odds:
                best_odds[market] = {}
            
            for outcome, odd_value in odds.outcomes.items():
                if outcome not in best_odds[market] or odd_value > best_odds[market][outcome]:
                    best_odds[market][outcome] = odd_value
        
        return best_odds
    
    async def _collect_head_to_head(self, package: MatchDataPackage):
        """Kerää head-to-head tilastot"""
        logger.info("📜 Collecting head-to-head data...")
        
        # Simuloi H2H-datan keräys
        h2h = HeadToHeadData(
            team1=package.home_team,
            team2=package.away_team,
            total_matches=10,
            team1_wins=6,
            team2_wins=3,
            draws=1
        )
        
        # Lisää viimeisimmät ottelut
        h2h.recent_matches = [
            {'date': '2024-10-15', 'result': f'{package.home_team} 2-1 {package.away_team}'},
            {'date': '2024-05-20', 'result': f'{package.away_team} 0-3 {package.home_team}'},
            {'date': '2023-12-10', 'result': f'{package.home_team} 1-1 {package.away_team}'}
        ]
        
        package.head_to_head = h2h
        package.data_sources.append('head_to_head')
    
    async def _collect_external_factors(self, package: MatchDataPackage):
        """Kerää ulkoiset tekijät (sää, loukkaantumiset, jne.)"""
        logger.info("🌤️ Collecting external factors...")
        
        # Simuloi ulkoisten tekijöiden keräys
        if package.venue:
            package.weather = {
                'temperature': 18,
                'humidity': 65,
                'wind_speed': 12,
                'conditions': 'partly_cloudy'
            }
        
        # Simuloi loukkaantumiset/suspensiot
        package.injuries = []
        package.suspensions = []
        
        package.data_sources.append('external_factors')
    
    def _calculate_data_quality(self, package: MatchDataPackage) -> float:
        """Laske datan laatupisteet"""
        quality_score = 0.0
        max_score = 0.0
        
        # Tilastot (30%)
        if package.home_team_stats or package.home_player_stats:
            quality_score += 0.3
        max_score += 0.3
        
        # Kertoimet (25%)
        if package.odds_data:
            odds_quality = min(len(package.odds_data) / 5, 1.0)  # Max 5 bookmakers
            quality_score += 0.25 * odds_quality
        max_score += 0.25
        
        # Head-to-head (20%)
        if package.head_to_head:
            h2h_quality = min(package.head_to_head.total_matches / 10, 1.0)  # Max 10 matches
            quality_score += 0.20 * h2h_quality
        max_score += 0.20
        
        # Ulkoiset tekijät (15%)
        if package.weather or package.injuries or package.suspensions:
            quality_score += 0.15
        max_score += 0.15
        
        # Datalähteet (10%)
        sources_quality = min(len(package.data_sources) / 4, 1.0)  # Max 4 sources
        quality_score += 0.10 * sources_quality
        max_score += 0.10
        
        return quality_score / max_score if max_score > 0 else 0.0
    
    def _calculate_completeness(self, package: MatchDataPackage) -> float:
        """Laske datan täydellisyys"""
        total_fields = 0
        filled_fields = 0
        
        # Perusinfo (aina täytetty)
        total_fields += 6
        filled_fields += 6
        
        # Tilastot
        total_fields += 2
        if package.home_team_stats or package.home_player_stats:
            filled_fields += 1
        if package.away_team_stats or package.away_player_stats:
            filled_fields += 1
        
        # Muut kentät
        total_fields += 4
        if package.head_to_head:
            filled_fields += 1
        if package.odds_data:
            filled_fields += 1
        if package.weather:
            filled_fields += 1
        if package.injuries or package.suspensions:
            filled_fields += 1
        
        return filled_fields / total_fields
    
    async def get_match_packages(self, sports: List[str] = None, days_ahead: int = 7) -> List[MatchDataPackage]:
        """
        Hae täydelliset ottelu-paketit
        
        Args:
            sports: Lista lajeista
            days_ahead: Montako päivää eteenpäin
            
        Returns:
            Lista MatchDataPackage-objekteja
        """
        logger.info("🎯 Creating complete match packages...")
        
        # Löydä ottelut
        matches = await self.discover_matches(sports, days_ahead)
        
        # Luo paketit rinnakkain
        tasks = [self.create_match_package(match) for match in matches]
        packages = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Suodata onnistuneet paketit
        valid_packages = []
        for package in packages:
            if isinstance(package, MatchDataPackage):
                if package.data_quality_score >= self.config['min_data_quality']:
                    valid_packages.append(package)
                else:
                    logger.warning(f"⚠️ Package quality too low: {package.data_quality_score:.2f}")
            else:
                logger.error(f"❌ Package creation failed: {package}")
        
        logger.info(f"✅ Created {len(valid_packages)} high-quality match packages")
        return valid_packages
    
    def save_package(self, package: MatchDataPackage, filepath: str):
        """Tallenna paketti tiedostoon"""
        try:
            # Convert to dict for JSON serialization
            package_dict = {
                'match_id': package.match_id,
                'sport': package.sport,
                'league': package.league,
                'home_team': package.home_team,
                'away_team': package.away_team,
                'match_time': package.match_time.isoformat(),
                'venue': package.venue,
                'data_quality_score': package.data_quality_score,
                'completeness_score': package.completeness_score,
                'data_sources': package.data_sources,
                'created_at': package.created_at.isoformat()
            }
            
            with open(filepath, 'w') as f:
                json.dump(package_dict, f, indent=2)
            
            logger.info(f"💾 Package saved to {filepath}")
        except Exception as e:
            logger.error(f"❌ Error saving package: {e}")


async def main():
    """Test Perfect Data Engine"""
    print("🎯 PERFECT DATA ENGINE (LAYER 1) TEST")
    print("=" * 50)
    
    engine = PerfectDataEngine()
    
    # Test 1: Discover matches
    print("\n🔍 Test 1: Discovering matches...")
    matches = await engine.discover_matches(['tennis', 'football'], days_ahead=3)
    print(f"✅ Found {len(matches)} matches")
    
    if matches:
        print("\n📋 Sample matches:")
        for match in matches[:2]:
            print(f"  • {match['home_team']} vs {match['away_team']} ({match['sport']})")
    
    # Test 2: Create match packages
    print("\n📦 Test 2: Creating match packages...")
    packages = await engine.get_match_packages(['tennis'], days_ahead=2)
    print(f"✅ Created {len(packages)} packages")
    
    if packages:
        package = packages[0]
        print(f"\n📊 Sample package:")
        print(f"  • Match: {package.home_team} vs {package.away_team}")
        print(f"  • Sport: {package.sport}")
        print(f"  • Quality: {package.data_quality_score:.2f}")
        print(f"  • Completeness: {package.completeness_score:.2f}")
        print(f"  • Sources: {', '.join(package.data_sources)}")
        print(f"  • Odds available: {len(package.odds_data)} bookmakers")


if __name__ == "__main__":
    asyncio.run(main())
