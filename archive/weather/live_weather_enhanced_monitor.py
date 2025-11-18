"""
Live Weather Enhanced Monitor
Integrates weather edge detection with match monitoring and betting recommendations
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from src.live_weather_edge import LiveWeatherEdgeDetector, WeatherEdge
from src.database_manager import DatabaseManager


logger = logging.getLogger(__name__)


class BetCalculator:
    """Simple bet calculator for Kelly criterion"""
    
    @staticmethod
    def calculate_kelly_stake(
        bankroll: float,
        odds: float,
        win_probability: float,
        max_stake_percent: float = 0.04
    ) -> float:
        """
        Calculate optimal stake using Kelly Criterion
        
        Args:
            bankroll: Total bankroll
            odds: Decimal odds
            win_probability: Probability of winning (0-1)
            max_stake_percent: Maximum stake as percentage of bankroll
            
        Returns:
            Recommended stake amount
        """
        if odds <= 1 or win_probability <= 0:
            return 0.0
        
        # Kelly formula: f = (bp - q) / b
        # where b = odds - 1, p = win_probability, q = 1 - p
        b = odds - 1
        p = win_probability
        q = 1 - p
        
        kelly_fraction = (b * p - q) / b
        
        # Conservative Kelly (quarter Kelly)
        conservative_kelly = kelly_fraction * 0.25
        
        # Apply max stake limit
        max_stake = bankroll * max_stake_percent
        optimal_stake = min(conservative_kelly * bankroll, max_stake)
        
        return max(0.0, optimal_stake)


class LiveWeatherEnhancedMonitor:
    """
    Enhanced monitor that integrates weather edge detection with match monitoring
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize weather edge detector
        self.weather_detector = LiveWeatherEdgeDetector(
            weather_api_key=config['weather_api_key'],
            alert_webhooks=config.get('alert_webhooks', [])
        )
        
        self.bet_calculator = BetCalculator()
        self.monitoring_active = False
        
        # Performance tracking
        self.session_stats = {
            'edges_detected': 0,
            'critical_alerts_sent': 0,
            'opportunities_processed': 0,
            'total_potential_profit': 0.0,
            'session_start': datetime.now()
        }
    
    async def start_live_monitoring(self):
        """
        Start continuous live weather edge monitoring
        This runs during active match periods
        """
        self.monitoring_active = True
        self.logger.info("Live Weather Edge Monitoring STARTED")
        
        try:
            while self.monitoring_active:
                # Get currently active matches
                active_matches = await self.get_active_matches()
                
                if active_matches:
                    self.logger.info(
                        f"Monitoring {len(active_matches)} active matches for weather edges"
                    )
                    
                    # Detect weather edges
                    weather_edges = await self.weather_detector.monitor_active_matches(
                        active_matches
                    )
                    
                    # Process any detected edges
                    if weather_edges:
                        await self.process_weather_edges(weather_edges, active_matches)
                    
                    # Monitor every 2 minutes during active periods
                    await asyncio.sleep(120)
                else:
                    # No active matches - check every 10 minutes
                    self.logger.debug(
                        "No active matches - reducing monitoring frequency"
                    )
                    await asyncio.sleep(600)
                
        except Exception as e:
            self.logger.error(f"Live weather monitoring error: {e}")
            # Restart after error
            await asyncio.sleep(300)
            if self.monitoring_active:
                await self.start_live_monitoring()
    
    async def process_weather_edges(
        self, weather_edges: List[WeatherEdge], matches: List[Dict]
    ):
        """
        Process detected weather edges and generate betting recommendations
        """
        for edge in weather_edges:
            try:
                # Find the corresponding match
                match = next(
                    (m for m in matches
                     if m.get('match_id') == edge.match_id or
                     f"{m.get('home_team', '')}-{m.get('away_team', '')}" == edge.match_id),
                    None
                )
                
                if not match:
                    self.logger.warning(
                        f"Could not find match for edge {edge.match_id}"
                    )
                    continue
                
                # Calculate betting recommendations
                betting_recommendation = await self.calculate_weather_betting_recommendation(
                    edge, match
                )
                
                # Store in database
                await self.store_weather_edge_opportunity(
                    edge, match, betting_recommendation
                )
                
                # Send detailed alert for high-value edges
                if edge.edge_strength > 0.12:  # 12%+ edge
                    await self.send_detailed_betting_alert(
                        edge, match, betting_recommendation
                    )
                
                # Update session stats
                self.session_stats['edges_detected'] += 1
                self.session_stats['total_potential_profit'] += (
                    betting_recommendation.get('expected_profit', 0)
                )
                
                if edge.urgency == 'CRITICAL':
                    self.session_stats['critical_alerts_sent'] += 1
                
            except Exception as e:
                self.logger.error(f"Error processing weather edge: {e}")
    
    async def calculate_weather_betting_recommendation(
        self, edge: WeatherEdge, match: Dict
    ) -> Dict[str, Any]:
        """
        Calculate specific betting recommendations based on weather edge
        """
        bankroll = self.config.get('bankroll', 5000.0)
        max_stake_percent = self.config.get('max_weather_edge_stake_percent', 0.04)
        
        # Base stake calculation using Kelly criterion
        implied_edge = edge.edge_strength
        estimated_odds = self.estimate_odds_for_edge_type(edge.edge_type)
        
        # Calculate optimal stake
        optimal_stake = self.bet_calculator.calculate_kelly_stake(
            bankroll=bankroll,
            odds=estimated_odds,
            win_probability=0.5 + (implied_edge / 2),  # Conservative probability adjustment
            max_stake_percent=max_stake_percent
        )
        
        # Adjust stake based on urgency and confidence
        urgency_multiplier = {
            'CRITICAL': 1.2,
            'HIGH': 1.0,
            'MEDIUM': 0.8,
            'LOW': 0.6
        }.get(edge.urgency, 1.0)
        
        final_stake = optimal_stake * urgency_multiplier
        
        # Calculate expected profit
        expected_profit = final_stake * implied_edge
        
        return {
            'edge_type': edge.edge_type,
            'edge_strength': edge.edge_strength,
            'recommended_stake': round(final_stake, 2),
            'estimated_odds': estimated_odds,
            'expected_profit': round(expected_profit, 2),
            'time_window_minutes': edge.time_window_minutes,
            'urgency': edge.urgency,
            'specific_bets': self.get_specific_bet_recommendations(edge, final_stake),
            'risk_level': self.calculate_risk_level(
                edge.edge_strength, final_stake, bankroll
            ),
            'weather_data': {
                'current_conditions': edge.weather_data.get('current', {}),
                'key_changes': edge.weather_data.get('changes', {})
            }
        }
    
    def get_specific_bet_recommendations(
        self, edge: WeatherEdge, total_stake: float
    ) -> List[Dict]:
        """
        Convert general recommendations into specific bet suggestions with stakes
        """
        recommendations = edge.recommendations
        num_bets = min(len(recommendations), 3)  # Max 3 specific bets
        stake_per_bet = total_stake / num_bets if num_bets > 0 else 0
        
        specific_bets = []
        
        for i, rec in enumerate(recommendations[:num_bets]):
            if 'PRIORITY' in rec or 'BET' in rec:  # Priority recommendations
                bet_stake = stake_per_bet * 1.2  # 20% more stake for priority bets
            else:
                bet_stake = stake_per_bet * 0.8
            
            # Parse recommendation into structured bet
            bet = self.parse_recommendation_to_bet(rec, bet_stake, edge.edge_type)
            if bet:
                specific_bets.append(bet)
        
        return specific_bets
    
    def parse_recommendation_to_bet(
        self, recommendation: str, stake: float, edge_type: str
    ) -> Optional[Dict]:
        """Parse text recommendation into structured bet"""
        rec_lower = recommendation.lower()
        
        # Under/Over goals
        if 'under total goals' in rec_lower:
            return {
                'bet_type': 'under_goals',
                'market': 'Total Goals',
                'selection': 'Under 2.5',
                'stake': round(stake, 2),
                'reasoning': f"Weather edge: {edge_type} favors low-scoring games"
            }
        elif 'over total goals' in rec_lower or 'over total games' in rec_lower:
            return {
                'bet_type': 'over_goals_games',
                'market': 'Total Goals/Games',
                'selection': 'Over 2.5',
                'stake': round(stake, 2),
                'reasoning': f"Weather edge: {edge_type} leads to extended play"
            }
        
        # Draw bets
        elif 'draw' in rec_lower and 'consider' not in rec_lower:
            return {
                'bet_type': 'draw',
                'market': 'Match Result',
                'selection': 'Draw',
                'stake': round(stake, 2),
                'reasoning': f"Weather edge: {edge_type} increases draw probability"
            }
        
        # Underdog backing
        elif 'underdog' in rec_lower or 'back underdog' in rec_lower:
            return {
                'bet_type': 'underdog',
                'market': 'Match Result',
                'selection': 'Underdog Win',
                'stake': round(stake, 2),
                'reasoning': f"Weather edge: {edge_type} creates chaos favoring underdog"
            }
        
        # Corner bets
        elif 'corner' in rec_lower and 'under' in rec_lower:
            return {
                'bet_type': 'under_corners',
                'market': 'Total Corners',
                'selection': 'Under 9.5',
                'stake': round(stake, 2),
                'reasoning': f"Weather edge: {edge_type} reduces crossing accuracy"
            }
        
        return None
    
    def estimate_odds_for_edge_type(self, edge_type: str) -> float:
        """Estimate typical odds for different edge types"""
        odds_estimates = {
            'SUDDEN_HEAVY_RAIN': 2.2,      # Under goals, draw bets
            'SUDDEN_MODERATE_RAIN': 2.0,
            'STRONG_WIND_SURGE': 2.1,
            'STORM_APPROACH': 2.5,         # Higher odds due to unpredictability
            'TEMPERATURE_SHOCK': 1.9,
            'VISIBILITY_POOR': 2.3,
            'POOR_VISIBILITY': 2.3
        }
        
        return odds_estimates.get(edge_type, 2.0)
    
    def calculate_risk_level(
        self, edge_strength: float, stake: float, bankroll: float
    ) -> str:
        """Calculate risk level for the weather edge bet"""
        stake_percent = (stake / bankroll) * 100
        
        if edge_strength > 0.20 and stake_percent < 3:
            return 'LOW'  # High edge, reasonable stake
        elif edge_strength > 0.15 and stake_percent < 4:
            return 'MEDIUM'
        elif edge_strength > 0.10 and stake_percent < 5:
            return 'MEDIUM'
        else:
            return 'HIGH'
    
    async def send_detailed_betting_alert(
        self, edge: WeatherEdge, match: Dict, betting_rec: Dict
    ):
        """Send detailed betting alert with specific recommendations"""
        match_info = (
            f"{match.get('home_team', 'Team1')} vs "
            f"{match.get('away_team', 'Team2')}"
        )
        
        detailed_alert = f"""
LIVE WEATHER EDGE - BETTING OPPORTUNITY

MATCH: {match_info}
SPORT: {match.get('sport', 'soccer').upper()}
EDGE: {edge.edge_type} ({edge.edge_strength:.1%})

BETTING RECOMMENDATIONS:
Total Stake: €{betting_rec['recommended_stake']}
Expected Profit: €{betting_rec['expected_profit']}
Risk Level: {betting_rec['risk_level']}

SPECIFIC BETS:
{self.format_specific_bets(betting_rec['specific_bets'])}

WEATHER CONDITIONS:
{self.format_weather_conditions(edge.weather_data)}

TIME WINDOW: {edge.time_window_minutes} minutes
Expected ROI Boost: +{edge.expected_roi_boost:.1f}%

TIME: {datetime.now().strftime('%H:%M:%S')}
ACT FAST - Market adjustment expected soon!
        """
        
        await self.weather_detector.broadcast_alert(detailed_alert)
        
        self.logger.info(f"Detailed betting alert sent for {edge.edge_type} edge")
    
    def format_specific_bets(self, bets: List[Dict]) -> str:
        """Format specific bet recommendations for alert"""
        if not bets:
            return "No specific bets available"
        
        formatted = []
        for bet in bets:
            formatted.append(
                f"• {bet['market']}: {bet['selection']} - €{bet['stake']}"
            )
        
        return '\n'.join(formatted)
    
    def format_weather_conditions(self, weather_data: Dict) -> str:
        """Format weather conditions for alert"""
        current = weather_data.get('current', {})
        changes = weather_data.get('changes', {})
        
        conditions = []
        
        if current.get('temp_c'):
            conditions.append(f"Temperature: {current['temp_c']:.1f}°C")
        
        if current.get('wind_mph'):
            conditions.append(f"Wind: {current['wind_mph']:.1f} mph")
        
        if current.get('precip_mm'):
            conditions.append(f"Precipitation: {current['precip_mm']:.1f} mm")
        
        if changes.get('precip_change_mm', 0) > 0:
            conditions.append(
                f"Rain increase: +{changes['precip_change_mm']:.1f} mm"
            )
        
        if changes.get('wind_change_mph', 0) > 0:
            conditions.append(
                f"Wind increase: +{changes['wind_change_mph']:.1f} mph"
            )
        
        return '\n'.join(conditions) if conditions else "Weather data unavailable"
    
    async def get_active_matches(self) -> List[Dict]:
        """Get currently active or upcoming matches (within 3 hours)"""
        try:
            async with DatabaseManager() as db:
                # Get matches starting within next 3 hours or currently live
                current_time = datetime.now()
                time_window = current_time + timedelta(hours=3)
                
                query = """
                SELECT * FROM (
                    SELECT 
                        (home_team || '-' || away_team) as match_id,
                        'soccer' as sport,
                        home_team, 
                        away_team,
                        league as stadium_city,
                        match_time,
                        status,
                        odds_home,
                        odds_draw, 
                        odds_away
                    FROM soccer_matches 
                    WHERE match_time BETWEEN ? AND ?
                    
                    UNION ALL
                    
                    SELECT
                        (player1 || '-' || player2) as match_id, 
                        'tennis' as sport,
                        player1 as home_team,
                        player2 as away_team,
                        tournament as stadium_city,
                        match_time,
                        status,
                        odds_player1 as odds_home,
                        NULL as odds_draw,
                        odds_player2 as odds_away
                    FROM tennis_matches
                    WHERE match_time BETWEEN ? AND ?
                ) as all_matches
                ORDER BY match_time ASC
                """
                
                results = await db.execute_query(
                    query,
                    (
                        current_time.isoformat(), time_window.isoformat(),
                        current_time.isoformat(), time_window.isoformat()
                    )
                )
                
                self.logger.debug(f"Found {len(results)} active/upcoming matches")
                return results
                
        except Exception as e:
            self.logger.error(f"Error getting active matches: {e}")
            return []
    
    async def store_weather_edge_opportunity(
        self, edge: WeatherEdge, match: Dict, betting_rec: Dict
    ):
        """Store weather edge opportunity in database"""
        try:
            async with DatabaseManager() as db:
                query = """
                INSERT INTO weather_edge_opportunities 
                (match_id, sport, edge_type, edge_strength, urgency, 
                 recommended_stake, expected_profit, time_window_minutes,
                 weather_conditions, betting_recommendations, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                params = (
                    edge.match_id,
                    match.get('sport', 'soccer'),
                    edge.edge_type,
                    edge.edge_strength,
                    edge.urgency,
                    betting_rec['recommended_stake'],
                    betting_rec['expected_profit'],
                    edge.time_window_minutes,
                    json.dumps(edge.weather_data),
                    json.dumps(betting_rec['specific_bets']),
                    datetime.now().isoformat()
                )
                
                await db.execute_non_query(query, params)
                
                self.logger.info(f"Stored weather edge opportunity: {edge.edge_type}")
                
        except Exception as e:
            self.logger.error(f"Error storing weather edge opportunity: {e}")
    
    async def get_session_statistics(self) -> Dict:
        """Get current session statistics"""
        session_duration = datetime.now() - self.session_stats['session_start']
        
        return {
            'session_duration_minutes': int(session_duration.total_seconds() / 60),
            'edges_detected': self.session_stats['edges_detected'],
            'critical_alerts_sent': self.session_stats['critical_alerts_sent'],
            'opportunities_processed': self.session_stats['opportunities_processed'],
            'total_potential_profit': self.session_stats['total_potential_profit'],
            'edges_per_hour': round(
                self.session_stats['edges_detected'] /
                max(1, session_duration.total_seconds() / 3600), 2
            ),
            'monitoring_status': 'ACTIVE' if self.monitoring_active else 'STOPPED'
        }
    
    async def stop_monitoring(self):
        """Stop live weather monitoring"""
        self.monitoring_active = False
        stats = await self.get_session_statistics()
        
        self.logger.info("Live Weather Edge Monitoring STOPPED")
        self.logger.info(f"Session Stats: {stats}")

