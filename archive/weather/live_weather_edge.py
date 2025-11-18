"""
Live Weather Edge Detection System
Detects sudden weather changes that create betting edges
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from src.weather_service import WeatherAPIMaximizer


logger = logging.getLogger(__name__)


@dataclass
class WeatherEdge:
    """Represents a detected weather edge opportunity"""
    edge_type: str
    edge_strength: float
    market_delay_minutes: int
    recommendations: List[str]
    urgency: str
    expected_roi_boost: float
    time_window_minutes: int
    match_id: str
    weather_data: Dict
    confidence: float = 0.0


class LiveWeatherEdgeDetector:
    """
    Detects live weather changes that create betting edges
    Monitors active matches for sudden weather changes
    """
    
    def __init__(self, weather_api_key: str, alert_webhooks: List[str] = None):
        self.weather_service = WeatherAPIMaximizer(weather_api_key)
        self.alert_webhooks = alert_webhooks or []
        self.logger = logging.getLogger(__name__)
        
        # Weather tracking for change detection
        self.weather_snapshots: Dict[str, Dict] = {}
        self.last_api_calls: Dict[str, datetime] = {}
        self.significant_edges_found: List[Dict] = []
        
        # Critical thresholds for edge detection
        self.THRESHOLDS = {
            'rain_sudden_mm': 3.0,        # 3mm sudden rain increase
            'rain_heavy_mm': 8.0,         # 8mm+ = heavy rain edge
            'wind_sudden_mph': 8.0,       # 8mph sudden wind increase
            'wind_strong_mph': 15.0,      # 15mph+ = strong wind edge
            'temp_drop_c': 6.0,           # 6°C sudden drop
            'visibility_drop_percent': 30, # 30% visibility drop
            'storm_distance_km': 25,     # Storm within 25km
            'humidity_spike_percent': 20  # 20% humidity increase
        }
        
        # Edge strength calculations
        self.EDGE_MULTIPLIERS = {
            'sudden_heavy_rain': 0.22,    # 22% edge!
            'sudden_moderate_rain': 0.15, # 15% edge
            'sudden_light_rain': 0.08,    # 8% edge
            'strong_wind': 0.18,          # 18% edge
            'moderate_wind': 0.12,        # 12% edge
            'temperature_shock': 0.10,     # 10% edge
            'storm_approach': 0.25,       # 25% edge!
            'visibility_poor': 0.14,       # 14% edge
            'humidity_spike': 0.06        # 6% edge
        }
    
    async def monitor_active_matches(
        self, active_matches: List[Dict]
    ) -> List[WeatherEdge]:
        """
        Main monitoring loop - checks for live weather edges
        
        Args:
            active_matches: List of active or upcoming matches
            
        Returns:
            List of detected weather edges
        """
        detected_edges = []
        current_time = datetime.now()
        
        for match in active_matches:
            try:
                match_id = match.get(
                    'match_id',
                    f"{match.get('home_team', 'Team1')}-{match.get('away_team', 'Team2')}"
                )
                location = self.extract_location(match)
                
                # Rate limiting - don't call API too frequently for same location
                last_call = self.last_api_calls.get(location, datetime.min)
                if (current_time - last_call).total_seconds() < 90:  # 90 second cooldown
                    continue
                
                # Get current + forecast weather
                match_time = self.parse_match_time(match)
                current_weather, forecast = await asyncio.gather(
                    self.weather_service.get_current_weather(location),
                    self.weather_service.get_forecast_weather(location, match_time),
                    return_exceptions=True
                )
                
                if isinstance(current_weather, Exception) or isinstance(forecast, Exception):
                    self.logger.warning(f"Weather API error for {location}")
                    continue
                
                self.last_api_calls[location] = current_time
                
                # Detect weather changes and edges
                weather_edge = await self.detect_live_edge(
                    match_id, location, current_weather, forecast, match
                )
                
                if weather_edge and weather_edge.edge_strength > 0.05:  # 5%+ minimum edge
                    detected_edges.append(weather_edge)
                    
                    # Critical alert for big edges
                    if weather_edge.edge_strength > 0.15 and weather_edge.urgency == 'CRITICAL':
                        await self.send_instant_alert(weather_edge, match)
                
            except Exception as e:
                self.logger.error(f"Error monitoring match {match}: {e}")
        
        return detected_edges
    
    async def detect_live_edge(
        self, match_id: str, location: str,
        current_weather: Dict, forecast: Dict, match: Dict
    ) -> Optional[WeatherEdge]:
        """
        Detect live weather edge by comparing current vs previous conditions
        """
        current_conditions = current_weather.get('current', {})
        forecast_hours = (
            forecast.get('forecast', {})
            .get('forecastday', [{}])[0]
            .get('hour', [])
        )
        
        # Get previous snapshot
        snapshot_key = f"{match_id}_{location}"
        previous = self.weather_snapshots.get(snapshot_key)
        
        # Store current snapshot
        self.weather_snapshots[snapshot_key] = {
            'timestamp': datetime.now(),
            'conditions': current_conditions,
            'forecast_next_2h': forecast_hours[:2] if forecast_hours else []
        }
        
        # Need previous data for comparison
        if not previous or (datetime.now() - previous['timestamp']).total_seconds() < 300:
            return None
        
        # Calculate weather changes
        changes = self.calculate_weather_deltas(
            previous['conditions'],
            current_conditions
        )
        
        # Analyze forecast for incoming changes
        forecast_changes = self.analyze_forecast_changes(forecast_hours, match)
        
        # Combine current changes + forecast for edge detection
        return self.evaluate_weather_edge(
            match_id, match, changes, forecast_changes, current_conditions
        )
    
    def calculate_weather_deltas(
        self, previous: Dict, current: Dict
    ) -> Dict[str, float]:
        """Calculate changes in weather conditions"""
        return {
            'precip_change_mm': current.get('precip_mm', 0) - previous.get('precip_mm', 0),
            'wind_change_mph': current.get('wind_mph', 0) - previous.get('wind_mph', 0),
            'temp_change_c': current.get('temp_c', 15) - previous.get('temp_c', 15),
            'humidity_change': current.get('humidity', 50) - previous.get('humidity', 50),
            'visibility_change_km': current.get('vis_km', 10) - previous.get('vis_km', 10),
            'pressure_change_mb': current.get('pressure_mb', 1013) - previous.get('pressure_mb', 1013),
            'time_delta_minutes': 5  # Assuming 5-minute snapshots
        }
    
    def analyze_forecast_changes(
        self, forecast_hours: List[Dict], match: Dict
    ) -> Dict[str, Any]:
        """Analyze upcoming weather changes in next 1-2 hours"""
        if not forecast_hours:
            return {}
        
        current_hour = forecast_hours[0] if forecast_hours else {}
        next_hour = forecast_hours[1] if len(forecast_hours) > 1 else current_hour
        
        return {
            'rain_incoming_mm': next_hour.get('precip_mm', 0),
            'wind_forecast_mph': next_hour.get('wind_mph', 0),
            'temp_forecast_c': next_hour.get('temp_c', 15),
            'chance_of_rain': next_hour.get('chance_of_rain', 0),
            'will_it_rain': next_hour.get('will_it_rain', 0),
            'condition_text': next_hour.get('condition', {}).get('text', '').lower()
        }
    
    def evaluate_weather_edge(
        self, match_id: str, match: Dict,
        changes: Dict, forecast: Dict, current: Dict
    ) -> Optional[WeatherEdge]:
        """
        Main edge evaluation logic
        """
        edges = []
        sport = match.get('sport', 'soccer').lower()
        
        # 1. SUDDEN RAIN EDGE (Highest potential!)
        rain_edge = self.evaluate_rain_edge(changes, forecast, current, sport)
        if rain_edge:
            edges.append(rain_edge)
        
        # 2. WIND SURGE EDGE
        wind_edge = self.evaluate_wind_edge(changes, current, sport)
        if wind_edge:
            edges.append(wind_edge)
        
        # 3. TEMPERATURE SHOCK EDGE
        temp_edge = self.evaluate_temperature_edge(changes, current, sport)
        if temp_edge:
            edges.append(temp_edge)
        
        # 4. VISIBILITY/FOG EDGE
        visibility_edge = self.evaluate_visibility_edge(changes, current, sport)
        if visibility_edge:
            edges.append(visibility_edge)
        
        # 5. STORM APPROACH EDGE (Massive potential!)
        storm_edge = self.evaluate_storm_edge(forecast, current, sport)
        if storm_edge:
            edges.append(storm_edge)
        
        # Return the strongest edge
        if edges:
            strongest_edge = max(edges, key=lambda x: x['edge_strength'])
            return WeatherEdge(
                edge_type=strongest_edge['type'],
                edge_strength=strongest_edge['edge_strength'],
                market_delay_minutes=strongest_edge['market_delay'],
                recommendations=strongest_edge['recommendations'],
                urgency=strongest_edge['urgency'],
                expected_roi_boost=strongest_edge['edge_strength'] * 100,
                time_window_minutes=max(3, strongest_edge['market_delay'] - 2),
                match_id=match_id,
                weather_data={
                    'current': current,
                    'changes': changes,
                    'forecast': forecast
                },
                confidence=strongest_edge.get('confidence', 0.85)
            )
        
        return None
    
    def evaluate_rain_edge(
        self, changes: Dict, forecast: Dict, current: Dict, sport: str
    ) -> Optional[Dict]:
        """
        RAIN EDGE DETECTION - This is pure gold!
        """
        precip_change = changes.get('precip_change_mm', 0)
        incoming_rain = forecast.get('rain_incoming_mm', 0)
        rain_chance = forecast.get('chance_of_rain', 0)
        current_rain = current.get('precip_mm', 0)
        
        # Sudden rain increase detected
        if precip_change > self.THRESHOLDS['rain_sudden_mm']:
            if incoming_rain > 10 or current_rain > 8:  # Heavy rain
                return {
                    'type': 'SUDDEN_HEAVY_RAIN',
                    'edge_strength': self.EDGE_MULTIPLIERS['sudden_heavy_rain'],
                    'market_delay': 12 if sport == 'soccer' else 8,
                    'urgency': 'CRITICAL',
                    'recommendations': self.get_heavy_rain_recommendations(sport),
                    'confidence': 0.95
                }
            elif incoming_rain > 4 or current_rain > 3:  # Moderate rain
                return {
                    'type': 'SUDDEN_MODERATE_RAIN',
                    'edge_strength': self.EDGE_MULTIPLIERS['sudden_moderate_rain'],
                    'market_delay': 8 if sport == 'soccer' else 6,
                    'urgency': 'HIGH',
                    'recommendations': self.get_moderate_rain_recommendations(sport),
                    'confidence': 0.88
                }
        
        # Incoming rain (no current rain but forecast shows it)
        elif rain_chance > 80 and incoming_rain > 5:
            return {
                'type': 'INCOMING_RAIN',
                'edge_strength': self.EDGE_MULTIPLIERS['sudden_moderate_rain'] * 0.8,
                'market_delay': 10,
                'urgency': 'HIGH',
                'recommendations': self.get_incoming_rain_recommendations(sport),
                'confidence': 0.75
            }
        
        return None
    
    def evaluate_wind_edge(
        self, changes: Dict, current: Dict, sport: str
    ) -> Optional[Dict]:
        """WIND SURGE EDGE DETECTION"""
        wind_change = changes.get('wind_change_mph', 0)
        current_wind = current.get('wind_mph', 0)
        
        if (wind_change > self.THRESHOLDS['wind_sudden_mph'] and
                current_wind > self.THRESHOLDS['wind_strong_mph']):
            if current_wind > 20:  # Very strong wind
                return {
                    'type': 'STRONG_WIND_SURGE',
                    'edge_strength': self.EDGE_MULTIPLIERS['strong_wind'],
                    'market_delay': 6 if sport == 'tennis' else 8,
                    'urgency': 'HIGH',
                    'recommendations': self.get_strong_wind_recommendations(sport),
                    'confidence': 0.90
                }
            elif current_wind > 15:  # Strong wind
                return {
                    'type': 'MODERATE_WIND_SURGE',
                    'edge_strength': self.EDGE_MULTIPLIERS['moderate_wind'],
                    'market_delay': 5,
                    'urgency': 'MEDIUM',
                    'recommendations': self.get_moderate_wind_recommendations(sport),
                    'confidence': 0.82
                }
        
        return None
    
    def evaluate_temperature_edge(
        self, changes: Dict, current: Dict, sport: str
    ) -> Optional[Dict]:
        """TEMPERATURE SHOCK EDGE DETECTION"""
        temp_drop = abs(changes.get('temp_change_c', 0))
        
        if temp_drop > self.THRESHOLDS['temp_drop_c']:
            return {
                'type': 'TEMPERATURE_SHOCK',
                'edge_strength': self.EDGE_MULTIPLIERS['temperature_shock'],
                'market_delay': 7,
                'urgency': 'MEDIUM',
                'recommendations': self.get_temperature_shock_recommendations(sport),
                'confidence': 0.80
            }
        
        return None
    
    def evaluate_visibility_edge(
        self, changes: Dict, current: Dict, sport: str
    ) -> Optional[Dict]:
        """VISIBILITY/FOG EDGE DETECTION"""
        visibility_drop = abs(changes.get('visibility_change_km', 0))
        current_vis = current.get('vis_km', 10)
        
        if visibility_drop > 2 and current_vis < 5:  # Significant fog
            return {
                'type': 'POOR_VISIBILITY',
                'edge_strength': self.EDGE_MULTIPLIERS['visibility_poor'],
                'market_delay': 8,
                'urgency': 'HIGH',
                'recommendations': self.get_poor_visibility_recommendations(sport),
                'confidence': 0.85
            }
        
        return None
    
    def evaluate_storm_edge(
        self, forecast: Dict, current: Dict, sport: str
    ) -> Optional[Dict]:
        """STORM APPROACH DETECTION - Massive edge potential!"""
        condition_text = forecast.get('condition_text', '').lower()
        storm_indicators = ['storm', 'thunder', 'heavy rain', 'severe']
        
        if any(indicator in condition_text for indicator in storm_indicators):
            return {
                'type': 'STORM_APPROACH',
                'edge_strength': self.EDGE_MULTIPLIERS['storm_approach'],
                'market_delay': 15,  # Markets very slow to react to storms
                'urgency': 'CRITICAL',
                'recommendations': self.get_storm_recommendations(sport),
                'confidence': 0.92
            }
        
        return None
    
    def get_heavy_rain_recommendations(self, sport: str) -> List[str]:
        """Betting recommendations for heavy rain"""
        if sport == 'soccer':
            return [
                'BET UNDER total goals (PRIORITY)',
                'BET DRAW (rain increases draws by 40%)',
                'BACK UNDERDOG (chaos helps weaker teams)',
                'UNDER corner count',
                'UNDER total cards (referees more lenient)',
                'AVOID over 2.5 goals',
                'AVOID both teams to score'
            ]
        else:  # tennis
            return [
                'BACK defensive players (rain favors grinders)',
                'OVER total games (longer rallies)',
                'UNDER aces (serving harder in rain)',
                'Consider set betting (unpredictable)'
            ]
    
    def get_moderate_rain_recommendations(self, sport: str) -> List[str]:
        """Betting recommendations for moderate rain"""
        if sport == 'soccer':
            return [
                'BET UNDER total goals',
                'Consider draw bet',
                'UNDER corner count',
                'Reduce attacking play expectations'
            ]
        else:  # tennis
            return [
                'BACK consistent players',
                'AGAINST big servers',
                'OVER total games'
            ]
    
    def get_incoming_rain_recommendations(self, sport: str) -> List[str]:
        """Betting recommendations for incoming rain"""
        return self.get_moderate_rain_recommendations(sport)
    
    def get_strong_wind_recommendations(self, sport: str) -> List[str]:
        """Betting recommendations for strong wind"""
        if sport == 'soccer':
            return [
                'BET UNDER total goals',
                'UNDER corner count (poor crossing accuracy)',
                'BACK defensive teams',
                'Consider draw'
            ]
        else:  # tennis
            return [
                'BACK baseline players (wind hurts net play)',
                'AGAINST big servers (wind affects serve)',
                'OVER total games (wind = longer points)',
                'Consider set betting (unpredictable outcomes)'
            ]
    
    def get_moderate_wind_recommendations(self, sport: str) -> List[str]:
        """Betting recommendations for moderate wind"""
        if sport == 'soccer':
            return [
                'BET UNDER total goals',
                'UNDER corner count'
            ]
        else:  # tennis
            return [
                'BACK baseline players',
                'AGAINST big servers'
            ]
    
    def get_temperature_shock_recommendations(self, sport: str) -> List[str]:
        """Betting recommendations for temperature shock"""
        if sport == 'soccer':
            return [
                'BET UNDER total goals',
                'BACK experienced teams (better adaptation)',
                'More defensive play expected'
            ]
        else:  # tennis
            return [
                'BACK players with better fitness',
                'Expect slower pace',
                'Consider OVER total games'
            ]
    
    def get_poor_visibility_recommendations(self, sport: str) -> List[str]:
        """Betting recommendations for poor visibility/fog"""
        if sport == 'soccer':
            return [
                'BET UNDER total goals',
                'BACK defensive teams',
                'UNDER corner count',
                'Consider draw'
            ]
        else:  # tennis
            return [
                'BACK consistent players',
                'AGAINST aggressive players',
                'OVER total games'
            ]
    
    def get_storm_recommendations(self, sport: str) -> List[str]:
        """Betting recommendations for approaching storm"""
        return [
            'MAXIMUM EDGE OPPORTUNITY!',
            'BET UNDER total goals/games',
            'MASSIVE draw potential (soccer)',
            'BACK underdog (chaos factor)',
            'Markets very slow to adjust to storm approach',
            'ACT IMMEDIATELY - 15+ minute market delay expected'
        ]
    
    async def send_instant_alert(self, weather_edge: WeatherEdge, match: Dict):
        """
        INSTANT ALERT for critical weather edges
        """
        match_info = (
            f"{match.get('home_team', 'Team1')} vs "
            f"{match.get('away_team', 'Team2')}"
        )
        
        alert_message = f"""
CRITICAL WEATHER EDGE DETECTED!

Match: {match_info}
Edge Type: {weather_edge.edge_type}
Edge Strength: {weather_edge.edge_strength:.1%}
Market Delay: {weather_edge.market_delay_minutes} minutes

RECOMMENDATIONS:
{chr(10).join(weather_edge.recommendations)}

ACT WITHIN: {weather_edge.time_window_minutes} minutes
Expected ROI Boost: +{weather_edge.expected_roi_boost:.1f}%

TIME: {datetime.now().strftime('%H:%M:%S')}
        """
        
        # Send to all alert channels
        await self.broadcast_alert(alert_message)
        
        # Store for tracking
        self.significant_edges_found.append({
            'timestamp': datetime.now(),
            'match_id': weather_edge.match_id,
            'edge': weather_edge,
            'alert_sent': True
        })
        
        self.logger.critical(
            f"CRITICAL WEATHER EDGE: {weather_edge.edge_type} - "
            f"{weather_edge.edge_strength:.1%}"
        )
    
    async def broadcast_alert(self, message: str):
        """Send alert to all configured channels"""
        # Discord/Slack webhooks
        for webhook in self.alert_webhooks:
            try:
                await self.send_webhook_alert(webhook, message)
            except Exception as e:
                self.logger.error(f"Webhook alert failed: {e}")
        
        # Console output for immediate visibility
        print(f"\n{'='*60}")
        print(message)
        print(f"{'='*60}\n")
    
    async def send_webhook_alert(self, webhook_url: str, message: str):
        """Send alert via webhook"""
        payload = {
            'content': message,
            'username': 'WeatherEdgeBot'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url, json=payload, timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status not in [200, 204]:
                    raise Exception(f"Webhook failed with status {response.status}")
    
    def extract_location(self, match: Dict) -> str:
        """Extract location for weather API"""
        return self.weather_service.extract_location(match)
    
    def parse_match_time(self, match: Dict) -> datetime:
        """Parse match time from match data"""
        match_time = match.get('match_time')
        
        if isinstance(match_time, str):
            try:
                return datetime.fromisoformat(match_time.replace('Z', '+00:00'))
            except:
                return datetime.now() + timedelta(hours=1)
        elif isinstance(match_time, datetime):
            return match_time
        else:
            return datetime.now() + timedelta(hours=1)

