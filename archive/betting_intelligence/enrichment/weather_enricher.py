#!/usr/bin/env python3
"""
🌤️ WEATHER DATA ENRICHER
=========================

Enriches match data with weather information from OpenWeatherMap API.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

# Try to import geopy for geocoding
try:
    from geopy.geocoders import Nominatim
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False
    logger.warning("⚠️ geopy not available, geocoding will be limited")

# Try to import requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("⚠️ requests not available")


@dataclass
class WeatherData:
    """Weather data for a match"""
    match_id: str
    temperature_celsius: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    humidity_percent: Optional[float] = None
    rain_probability: Optional[float] = None
    weather_conditions: Optional[str] = None  # 'sunny', 'cloudy', 'rain', etc.
    forecast_time: Optional[datetime] = None
    location: Optional[str] = None
    scraped_at: datetime = None
    
    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.now()


class WeatherEnricher:
    """
    Weather data enricher using OpenWeatherMap API
    """
    
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize weather enricher
        
        Args:
            config: Configuration dict with API key
        """
        self.config = config or {}
        self.api_key = self.config.get('openweather_api_key')
        
        if not self.api_key:
            logger.warning("⚠️ OpenWeatherMap API key not provided")
        
        # Geocoder for location lookup
        self.geocoder = None
        if GEOPY_AVAILABLE:
            try:
                self.geocoder = Nominatim(user_agent="tennisbot")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize geocoder: {e}")
        
        # Cache for location coordinates
        self.location_cache: Dict[str, tuple] = {}  # {location: (lat, lon)}
        
        logger.info("🌤️ Weather Enricher initialized")
    
    def get_weather(self, match_id: str, location: str, 
                   forecast_time: Optional[datetime] = None) -> Optional[WeatherData]:
        """
        Get weather data for a match location
        
        Args:
            match_id: Match ID
            location: Tournament location (city name or coordinates)
            forecast_time: Optional forecast time (defaults to current time)
            
        Returns:
            WeatherData object or None
        """
        if not self.api_key:
            logger.warning("⚠️ OpenWeatherMap API key not available")
            return None
        
        if forecast_time is None:
            forecast_time = datetime.now()
        
        logger.info(f"🌤️ Fetching weather for {location} at {forecast_time}")
        
        # Get coordinates for location
        lat, lon = self._get_coordinates(location)
        if not lat or not lon:
            logger.warning(f"⚠️ Could not geocode location: {location}")
            return None
        
        # Fetch weather from API
        weather_data = self._fetch_weather_api(lat, lon, forecast_time)
        if not weather_data:
            return None
        
        return WeatherData(
            match_id=match_id,
            temperature_celsius=weather_data.get('temp_c'),
            wind_speed_kmh=weather_data.get('wind_kmh'),
            humidity_percent=weather_data.get('humidity'),
            rain_probability=weather_data.get('rain_probability'),
            weather_conditions=weather_data.get('conditions'),
            forecast_time=forecast_time,
            location=location
        )
    
    def _get_coordinates(self, location: str) -> tuple:
        """
        Get latitude and longitude for a location
        
        Args:
            location: Location name or coordinates
            
        Returns:
            Tuple of (latitude, longitude) or (None, None)
        """
        # Check cache first
        if location in self.location_cache:
            return self.location_cache[location]
        
        # Try parsing as coordinates
        try:
            if ',' in location:
                parts = location.split(',')
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                self.location_cache[location] = (lat, lon)
                return (lat, lon)
        except ValueError:
            pass
        
        # Geocode location name
        if self.geocoder:
            try:
                result = self.geocoder.geocode(location, timeout=10)
                if result:
                    lat, lon = result.latitude, result.longitude
                    self.location_cache[location] = (lat, lon)
                    return (lat, lon)
            except Exception as e:
                logger.error(f"❌ Error geocoding {location}: {e}")
        
        return (None, None)
    
    def _fetch_weather_api(self, lat: float, lon: float, 
                          forecast_time: datetime) -> Optional[Dict]:
        """
        Fetch weather data from OpenWeatherMap API
        
        Args:
            lat: Latitude
            lon: Longitude
            forecast_time: Forecast time
            
        Returns:
            Dictionary with weather data or None
        """
        if not REQUESTS_AVAILABLE:
            return None
        
        try:
            # Use current weather endpoint (free tier)
            # For forecast, would need forecast endpoint
            url = f"{self.BASE_URL}/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'  # Get temperature in Celsius
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract weather data
            weather_data = {
                'temp_c': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'wind_kmh': data['wind'].get('speed', 0) * 3.6,  # Convert m/s to km/h
                'conditions': data['weather'][0]['main'].lower() if data.get('weather') else 'unknown',
                'rain_probability': None  # Not available in current weather endpoint
            }
            
            # Check for rain in weather description
            if data.get('weather'):
                weather_desc = data['weather'][0]['description'].lower()
                if 'rain' in weather_desc:
                    weather_data['rain_probability'] = 100.0
                elif 'drizzle' in weather_desc:
                    weather_data['rain_probability'] = 50.0
            
            logger.debug(f"✅ Fetched weather: {weather_data['temp_c']}°C, {weather_data['conditions']}")
            return weather_data
            
        except Exception as e:
            logger.error(f"❌ Error fetching weather from API: {e}")
            return None
    
    def store_weather(self, weather: WeatherData, db_connection=None) -> bool:
        """
        Store weather data in database
        
        Args:
            weather: WeatherData object
            db_connection: Database connection
            
        Returns:
            True if successful
        """
        if not db_connection:
            return False
        
        try:
            cursor = db_connection.cursor()
            is_sqlite = isinstance(db_connection, type(__import__('sqlite3').connect('')))
            
            if is_sqlite:
                cursor.execute("""
                    INSERT OR REPLACE INTO match_weather 
                    (match_id, temperature_celsius, wind_speed_kmh, humidity_percent,
                     rain_probability, weather_conditions, forecast_time, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (weather.match_id, weather.temperature_celsius, weather.wind_speed_kmh,
                      weather.humidity_percent, weather.rain_probability, weather.weather_conditions,
                      weather.forecast_time, weather.scraped_at))
            else:
                cursor.execute("""
                    INSERT INTO match_weather 
                    (match_id, temperature_celsius, wind_speed_kmh, humidity_percent,
                     rain_probability, weather_conditions, forecast_time, scraped_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (match_id, forecast_time) DO UPDATE SET
                        temperature_celsius = EXCLUDED.temperature_celsius,
                        wind_speed_kmh = EXCLUDED.wind_speed_kmh,
                        humidity_percent = EXCLUDED.humidity_percent,
                        rain_probability = EXCLUDED.rain_probability,
                        weather_conditions = EXCLUDED.weather_conditions,
                        scraped_at = EXCLUDED.scraped_at
                """, (weather.match_id, weather.temperature_celsius, weather.wind_speed_kmh,
                      weather.humidity_percent, weather.rain_probability, weather.weather_conditions,
                      weather.forecast_time, weather.scraped_at))
            
            db_connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing weather: {e}")
            if db_connection:
                db_connection.rollback()
            return False


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    config = {
        'openweather_api_key': None  # Set if available
    }
    
    enricher = WeatherEnricher(config)
    
    # Test getting weather
    weather = enricher.get_weather("test_match", "London, UK")
    if weather:
        print(f"\n🌤️ Weather for {weather.location}:")
        print(f"   Temperature: {weather.temperature_celsius}°C")
        print(f"   Wind: {weather.wind_speed_kmh} km/h")
        print(f"   Humidity: {weather.humidity_percent}%")
        print(f"   Conditions: {weather.weather_conditions}")

