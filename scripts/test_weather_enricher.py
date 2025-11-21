#!/usr/bin/env python3
"""
Test WeatherAPI integration with sample cities.
"""

import os
import requests

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

TEST_LOCATIONS = [
    "London,UK",
    "Paris,France",
    "Dubai,UAE",
    "New York,USA",
    "Tokyo,Japan"
]


def test_weather_api():
    if not WEATHER_API_KEY:
        print("❌ WEATHER_API_KEY not set!")
        print("Set it with: export WEATHER_API_KEY='your-key'")
        return
    
    print("Testing WeatherAPI.com integration\n")
    print("="*60)
    
    for location in TEST_LOCATIONS:
        print(f"\nTesting: {location}")
        
        url = "http://api.weatherapi.com/v1/forecast.json"
        params = {
            "key": WEATHER_API_KEY,
            "q": location,
            "days": 1,
            "aqi": "no"
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            current = data["current"]
            forecast = data["forecast"]["forecastday"][0]["day"]
            
            print(f"  ✓ Temp: {current['temp_c']:.1f}°C")
            print(f"  ✓ Wind: {current['wind_kph']:.0f} km/h")
            print(f"  ✓ Humidity: {current['humidity']:.0f}%")
            print(f"  ✓ Condition: {current['condition']['text']}")
            print(f"  ✓ Rain chance: {forecast['daily_chance_of_rain']:.0f}%")
            
        except requests.exceptions.HTTPError as e:
            print(f"  ✗ HTTP Error: {e.response.status_code}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print(f"\n{'='*60}")
    print("\n✅ Test complete")
    print("\nIf all tests passed, your API key is working correctly!")


if __name__ == "__main__":
    test_weather_api()

