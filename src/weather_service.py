"""
WeatherAPI.com Integration Service
Provides comprehensive weather data for betting edge analysis
"""

import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class WeatherBettingFactors:
    """Weather factors that impact betting"""
    temperature_impact: Dict[str, Any]
    wind_impact: Dict[str, Any]
    precipitation_impact: Dict[str, Any]
    humidity_impact: Dict[str, Any]
    overall_weather_edge: float
    confidence_score: float


class WeatherAPIMaximizer:
    """
    Maximize value from WeatherAPI.com for betting edge detection
    Includes smart caching and comprehensive weather analysis
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://api.weatherapi.com/v1"
        self.logger = logging.getLogger(__name__)
        
        # Cache to maximize API efficiency
        self.weather_cache: Dict[str, Dict] = {}
        self.cache_duration = 300  # 5 minutes cache
        self.api_call_cooldown = 90  # 90 seconds cooldown per location
        self.last_api_calls: Dict[str, datetime] = {}
    
    def is_cached(self, cache_key: str) -> bool:
        """Check if weather data is cached and still valid"""
        if cache_key not in self.weather_cache:
            return False
        
        cached_data = self.weather_cache[cache_key]
        cached_at = cached_data.get('cached_at')
        
        if not cached_at:
            return False
        
        if isinstance(cached_at, str):
            cached_at = datetime.fromisoformat(cached_at)
        
        age = (datetime.now() - cached_at).total_seconds()
        return age < self.cache_duration
    
    def can_make_api_call(self, location: str) -> bool:
        """Check if enough time has passed since last API call for this location"""
        if location not in self.last_api_calls:
            return True
        
        last_call = self.last_api_calls[location]
        elapsed = (datetime.now() - last_call).total_seconds()
        return elapsed >= self.api_call_cooldown
    
    async def get_enhanced_match_weather(
        self, location: str, match_time: datetime
    ) -> Dict[str, Any]:
        """
        Get comprehensive weather data for betting edge
        
        Args:
            location: City name or coordinates
            match_time: When the match is scheduled
            
        Returns:
            Comprehensive weather data with betting factors
        """
        # Check cache first
        cache_key = f"{location}_{match_time.date()}"
        if self.is_cached(cache_key):
            self.logger.debug(f"Using cached weather data for {location}")
            return self.weather_cache[cache_key]['data']
        
        # Check API cooldown
        if not self.can_make_api_call(location):
            self.logger.debug(f"API cooldown active for {location}, using stale cache if available")
            if cache_key in self.weather_cache:
                return self.weather_cache[cache_key]['data']
        
        # Collect comprehensive weather data
        weather_data = await self.collect_comprehensive_weather(location, match_time)
        
        # Cache the result
        self.weather_cache[cache_key] = {
            'data': weather_data,
            'cached_at': datetime.now()
        }
        
        self.last_api_calls[location] = datetime.now()
        
        return weather_data
    
    async def collect_comprehensive_weather(
        self, location: str, match_time: datetime
    ) -> Dict[str, Any]:
        """
        Collect weather from multiple endpoints for maximum insight
        """
        try:
            # Current weather (if match is within 24h)
            time_to_match = (match_time - datetime.now()).total_seconds()
            use_current = time_to_match < 86400  # 24 hours
            
            tasks = []
            
            if use_current:
                tasks.append(self.get_current_weather(location))
            
            # Forecast for match time
            tasks.append(self.get_forecast_weather(location, match_time))
            
            # Execute requests concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            current = results[0] if use_current and not isinstance(results[0], Exception) else None
            forecast = results[-1] if not isinstance(results[-1], Exception) else None
            
            # Extract match hour forecast
            match_hour_forecast = self.extract_match_hour_weather(forecast, match_time) if forecast else {}
            
            return self.combine_weather_insights(
                current, forecast, match_hour_forecast, match_time
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting weather data: {e}")
            return self.get_fallback_weather()
    
    async def get_current_weather(self, location: str) -> Dict[str, Any]:
        """Get current weather conditions"""
        url = f"{self.base_url}/current.json"
        params = {
            'key': self.api_key,
            'q': location,
            'aqi': 'no'  # Don't need air quality for betting
        }
        
        return await self.make_api_request(url, params)
    
    async def get_forecast_weather(
        self, location: str, match_time: datetime
    ) -> Dict[str, Any]:
        """Get forecast for match time"""
        # Calculate days ahead
        days_ahead = (match_time.date() - datetime.now().date()).days + 1
        days_ahead = min(10, max(1, days_ahead))  # Limit to 1-10 days
        
        url = f"{self.base_url}/forecast.json"
        params = {
            'key': self.api_key,
            'q': location,
            'days': days_ahead,
            'aqi': 'no',
            'alerts': 'yes'  # Weather alerts could affect matches
        }
        
        return await self.make_api_request(url, params)
    
    def extract_match_hour_weather(
        self, forecast: Dict, match_time: datetime
    ) -> Dict[str, Any]:
        """Extract weather data for the specific hour of the match"""
        try:
            forecastday = forecast.get('forecast', {}).get('forecastday', [])
            if not forecastday:
                return {}
            
            # Find the forecast day
            match_date = match_time.date()
            match_hour = match_time.hour
            
            for day_data in forecastday:
                day_date = datetime.strptime(
                    day_data.get('date', ''), '%Y-%m-%d'
                ).date()
                
                if day_date == match_date:
                    # Find the hour
                    hours = day_data.get('hour', [])
                    for hour_data in hours:
                        hour_time = datetime.strptime(
                            hour_data.get('time', ''), '%Y-%m-%d %H:%M'
                        )
                        if hour_time.hour == match_hour:
                            return {
                                'temp_c': hour_data.get('temp_c'),
                                'wind_mph': hour_data.get('wind_mph', 0),
                                'wind_dir': hour_data.get('wind_dir', ''),
                                'precip_mm': hour_data.get('precip_mm', 0),
                                'humidity': hour_data.get('humidity', 50),
                                'vis_km': hour_data.get('vis_km', 10),
                                'pressure_mb': hour_data.get('pressure_mb', 1013),
                                'condition': hour_data.get('condition', {}).get('text', ''),
                                'chance_of_rain': hour_data.get('chance_of_rain', 0),
                                'will_it_rain': hour_data.get('will_it_rain', 0)
                            }
            
            # Fallback to day average
            if forecastday:
                day_avg = forecastday[0].get('day', {})
                return {
                    'temp_c': day_avg.get('avgtemp_c'),
                    'wind_mph': day_avg.get('maxwind_mph', 0),
                    'precip_mm': day_avg.get('totalprecip_mm', 0),
                    'humidity': day_avg.get('avghumidity', 50),
                    'condition': day_avg.get('condition', {}).get('text', '')
                }
            
        except Exception as e:
            self.logger.error(f"Error extracting match hour weather: {e}")
        
        return {}
    
    def combine_weather_insights(
        self, current: Optional[Dict], forecast: Optional[Dict],
        match_hour: Dict, match_time: datetime
    ) -> Dict[str, Any]:
        """
        Combine all weather data into betting-relevant insights
        """
        try:
            # Use match hour forecast as primary, fallback to current
            primary_weather = match_hour if match_hour else (current.get('current', {}) if current else {})
            
            combined_insights = {
                'match_time_weather': primary_weather,
                'current_conditions': current.get('current', {}) if current else {},
                'forecast_data': forecast.get('forecast', {}) if forecast else {},
                'betting_factors': self.calculate_betting_factors(primary_weather),
                'confidence_score': self.calculate_weather_confidence(current, forecast),
                'location': forecast.get('location', {}) if forecast else {},
                'alerts': forecast.get('alerts', {}).get('alert', []) if forecast else [],
                'last_updated': datetime.now().isoformat()
            }
            
            return combined_insights
            
        except Exception as e:
            self.logger.error(f"Error combining weather insights: {e}")
            return self.get_fallback_weather()
    
    def calculate_betting_factors(self, weather: Dict) -> Dict[str, Any]:
        """
        Calculate weather-based betting factors
        """
        temp_c = weather.get('temp_c', 15)
        wind_mph = weather.get('wind_mph', 0)
        precip_mm = weather.get('precip_mm', 0)
        humidity = weather.get('humidity', 50)
        
        factors = {
            'temperature_impact': self.get_temperature_factor(temp_c),
            'wind_impact': self.get_wind_factor(wind_mph),
            'precipitation_impact': self.get_precipitation_factor(precip_mm),
            'humidity_impact': self.get_humidity_factor(humidity),
            'overall_weather_edge': 0.0
        }
        
        # Calculate overall edge
        factors['overall_weather_edge'] = sum([
            factors['temperature_impact']['edge'],
            factors['wind_impact']['edge'],
            factors['precipitation_impact']['edge'],
            factors['humidity_impact']['edge']
        ])
        
        return factors
    
    def get_temperature_factor(self, temp_c: float) -> Dict[str, Any]:
        """Temperature impact on betting"""
        if temp_c < 5:
            return {
                'edge': 0.08,
                'factor': 'cold_weather',
                'description': 'Cold reduces accuracy and favors experienced teams'
            }
        elif temp_c > 30:
            return {
                'edge': 0.06,
                'factor': 'hot_weather',
                'description': 'Heat reduces stamina, favors fitter teams'
            }
        else:
            return {
                'edge': 0.0,
                'factor': 'neutral',
                'description': 'Ideal temperature range'
            }
    
    def get_wind_factor(self, wind_mph: float) -> Dict[str, Any]:
        """Wind impact on betting"""
        if wind_mph > 15:
            return {
                'edge': 0.12,
                'factor': 'strong_wind',
                'description': 'Strong wind affects passing, shooting, and long balls'
            }
        elif wind_mph > 10:
            return {
                'edge': 0.06,
                'factor': 'moderate_wind',
                'description': 'Moderate wind affects long balls and crosses'
            }
        else:
            return {
                'edge': 0.0,
                'factor': 'calm',
                'description': 'Minimal wind impact'
            }
    
    def get_precipitation_factor(self, precip_mm: float) -> Dict[str, Any]:
        """Rain impact on betting"""
        if precip_mm > 10:
            return {
                'edge': 0.15,
                'factor': 'heavy_rain',
                'description': 'Heavy rain - major game changer, favors underdogs'
            }
        elif precip_mm > 2:
            return {
                'edge': 0.08,
                'factor': 'light_rain',
                'description': 'Light rain affects ball control and passing'
            }
        else:
            return {
                'edge': 0.0,
                'factor': 'dry',
                'description': 'No precipitation impact'
            }
    
    def get_humidity_factor(self, humidity: float) -> Dict[str, Any]:
        """Humidity impact on betting"""
        if humidity > 80:
            return {
                'edge': 0.04,
                'factor': 'high_humidity',
                'description': 'High humidity affects stamina and ball movement'
            }
        elif humidity < 30:
            return {
                'edge': 0.02,
                'factor': 'low_humidity',
                'description': 'Low humidity may affect ball bounce'
            }
        else:
            return {
                'edge': 0.0,
                'factor': 'normal',
                'description': 'Normal humidity levels'
            }
    
    def calculate_weather_confidence(
        self, current: Optional[Dict], forecast: Optional[Dict]
    ) -> float:
        """Calculate confidence in weather data"""
        confidence = 0.5  # Base confidence
        
        if current:
            confidence += 0.2
        
        if forecast:
            confidence += 0.3
        
        return min(confidence, 1.0)
    
    async def make_api_request(
        self, url: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make API request with error handling"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, params=params, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        self.logger.error(
                            f"Weather API error {response.status}: {error_text}"
                        )
                        raise Exception(f"Weather API error: {response.status}")
        except aiohttp.ClientError as e:
            self.logger.error(f"Weather API request failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in weather API request: {e}")
            raise
    
    def get_fallback_weather(self) -> Dict[str, Any]:
        """Return fallback weather data when API fails"""
        return {
            'match_time_weather': {
                'temp_c': 15,
                'wind_mph': 5,
                'precip_mm': 0,
                'humidity': 50
            },
            'betting_factors': {
                'overall_weather_edge': 0.0,
                'temperature_impact': {'edge': 0.0},
                'wind_impact': {'edge': 0.0},
                'precipitation_impact': {'edge': 0.0},
                'humidity_impact': {'edge': 0.0}
            },
            'confidence_score': 0.0,
            'last_updated': datetime.now().isoformat(),
            'fallback': True
        }
    
    def extract_location(self, match_data: Dict[str, Any]) -> str:
        """
        Extract location for weather API from match data
        
        Uses LocationMapper for intelligent city mapping
        """
        try:
            from src.location_mapper import get_location_mapper
            mapper = get_location_mapper()
            return mapper.map_to_city(match_data)
        except ImportError:
            # Fallback to simple extraction if mapper not available
            location = (
                match_data.get('venue') or
                match_data.get('city') or
                match_data.get('stadium_city') or
                match_data.get('venue_city') or
                match_data.get('location') or
                match_data.get('league') or
                match_data.get('tournament')
            )
            
            if not location:
                home_team = match_data.get('home_team', '')
                if home_team:
                    location = home_team.split()[-1]
            
            return location or 'London'  # Ultimate fallback

