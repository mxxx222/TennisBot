#!/usr/bin/env python3
"""
Weather Enrichment Service
Fetches weather data for upcoming tennis matches from WeatherAPI.com
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional
from notion_client import Client
import time

# Configuration
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
TENNIS_PREMATCH_DB_ID = os.getenv("TENNIS_PREMATCH_DB_ID") or os.getenv("NOTION_TENNIS_PREMATCH_DB_ID") or os.getenv("NOTION_PREMATCH_DB_ID")

notion_client = Client(auth=NOTION_TOKEN) if NOTION_TOKEN else None


class WeatherEnricher:
    """
    Enriches tennis matches with weather data.
    """
    
    def __init__(self):
        self.api_key = WEATHER_API_KEY
        # Initialize Notion client in __init__ to avoid module-level issues
        if NOTION_TOKEN:
            self.notion = Client(auth=NOTION_TOKEN)
        else:
            self.notion = None
        self.location_cache = {}  # Cache geocoding results
        
    def get_upcoming_matches(self) -> list:
        """
        Get matches in next 48 hours without weather data.
        """
        if not self.notion or not TENNIS_PREMATCH_DB_ID:
            return []
        
        now = datetime.now()
        end = now + timedelta(days=2)
        
        matches = []
        has_more = True
        start_cursor = None
        
        while has_more:
            try:
                response = self.notion.databases.query(
                    database_id=TENNIS_PREMATCH_DB_ID,
                    filter={
                        "and": [
                            {"property": "Match Status", "select": {"equals": "Scheduled"}},
                            {"property": "Match Date", "date": {"on_or_after": now.isoformat()}},
                            {"property": "Match Date", "date": {"on_or_before": end.isoformat()}}
                        ]
                    },
                    start_cursor=start_cursor
                )
                
                matches.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")
            except Exception as e:
                print(f"❌ Error fetching matches: {e}")
                break
            
        print(f"📥 Found {len(matches)} upcoming matches")
        return matches
    
    def fetch_weather(self, location: str, match_date: str) -> Optional[Dict]:
        """
        Fetch weather forecast for location and date.
        
        Args:
            location: City name or "City, Country"
            match_date: ISO-8601 datetime string
        
        Returns:
            Dict with weather data or None if error
        """
        url = "http://api.weatherapi.com/v1/forecast.json"
        
        # Extract date for forecast (YYYY-MM-DD)
        forecast_date = match_date[:10]
        
        params = {
            "key": self.api_key,
            "q": location,
            "dt": forecast_date,
            "aqi": "no"
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract relevant data from forecast
            forecast_day = data["forecast"]["forecastday"][0]
            day_data = forecast_day["day"]
            
            # Get hourly data for match time (default to noon if no time)
            hour_data = forecast_day["hour"][12]  # Noon by default
            
            return {
                "temp_c": day_data["avgtemp_c"],
                "wind_kph": day_data["maxwind_kph"],
                "humidity": day_data["avghumidity"],
                "rain_chance": hour_data.get("chance_of_rain", 0),
                "condition": day_data["condition"]["text"]
            }
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                print(f"  ⚠️ Invalid location: {location}")
            else:
                print(f"  ⚠️ Weather API error: {e}")
            return None
        except Exception as e:
            print(f"  ⚠️ Error fetching weather: {e}")
            return None
    
    def classify_condition(self, weather: Dict) -> str:
        """
        Classify weather into simple categories.
        """
        if weather["rain_chance"] > 50:
            return "Rainy"
        elif weather["wind_kph"] > 25:
            return "Windy"
        elif "cloud" in weather["condition"].lower() or "overcast" in weather["condition"].lower():
            return "Cloudy"
        else:
            return "Sunny"
    
    def update_match_weather(self, match_id: str, weather: Dict):
        """
        Update match with weather data in Notion.
        """
        condition = self.classify_condition(weather)
        
        self.notion.pages.update(
            page_id=match_id,
            properties={
                "Weather Temp": {"number": weather["temp_c"]},
                "Weather Wind": {"number": weather["wind_kph"]},
                "Weather Humidity": {"number": weather["humidity"]},
                "Weather Rain Prob": {"number": weather["rain_chance"]},
                "Weather Condition": {"select": {"name": condition}},
                "Weather Updated": {
                    "date": {"start": datetime.now().isoformat()}
                }
            }
        )
    
    def extract_location(self, props: Dict) -> Optional[str]:
        """
        Extract location from match properties.
        Try Venue City + Country, fallback to tournament name parsing.
        """
        # Try venue city + country
        city_prop = props.get("Venue City", {}).get("rich_text", [])
        country_prop = props.get("Venue Country", {}).get("rich_text", [])
        
        city = city_prop[0]["text"]["content"] if city_prop else ""
        country = country_prop[0]["text"]["content"] if country_prop else ""
        
        if city:
            return f"{city},{country}" if country else city
        
        # Fallback: parse tournament name
        tournament_prop = props.get("Tournament", {}).get("rich_text", [])
        if not tournament_prop:
            tournament_prop = props.get("Turnaus", {}).get("rich_text", [])
        
        if tournament_prop:
            tournament = tournament_prop[0]["text"]["content"]
            # Extract city from tournament name (e.g., "W15 Phan Thiet" -> "Phan Thiet")
            # This is best-effort parsing
            parts = tournament.split()
            if len(parts) >= 2:
                # Skip tier (W15, W25, etc) and get city
                city = " ".join(parts[1:3])  # Take next 1-2 words as city
                return city
        
        # Try Location field
        location_prop = props.get("Location", {}).get("rich_text", [])
        if location_prop:
            return location_prop[0]["text"]["content"]
        
        return None
    
    def process_matches(self):
        """
        Main processing loop.
        """
        print("☁️ Weather Enrichment Starting...")
        print(f"Time: {datetime.now().isoformat()}\n")
        
        if not self.api_key:
            print("❌ WEATHER_API_KEY not set!")
            return
        
        if not TENNIS_PREMATCH_DB_ID:
            print("❌ TENNIS_PREMATCH_DB_ID not set!")
            return
        
        matches = self.get_upcoming_matches()
        
        if not matches:
            print("✅ No matches to enrich")
            return
        
        success_count = 0
        skipped_count = 0
        
        for i, match in enumerate(matches, 1):
            props = match["properties"]
            match_id_prop = props.get("Match ID", {}).get("title", [])
            match_id_text = match_id_prop[0]["text"]["content"] if match_id_prop else "Unknown"
            
            print(f"[{i}/{len(matches)}] {match_id_text}")
            
            # Extract location
            location = self.extract_location(props)
            if not location:
                print("  ⚠️ No location found, skipping")
                skipped_count += 1
                continue
            
            print(f"  📍 Location: {location}")
            
            # Get match date
            match_date_prop = props.get("Match Date", {}).get("date")
            if not match_date_prop:
                match_date_prop = props.get("Päivämäärä", {}).get("date")
            
            if not match_date_prop:
                print("  ⚠️ No match date, skipping")
                skipped_count += 1
                continue
            
            match_date = match_date_prop["start"]
            
            # Fetch weather
            weather = self.fetch_weather(location, match_date)
            
            if weather:
                print(f"  🌡️ {weather['temp_c']:.1f}°C, 💨 {weather['wind_kph']:.0f} km/h, "
                      f"💧 {weather['humidity']:.0f}%, 🌧️ {weather['rain_chance']:.0f}%")
                
                try:
                    self.update_match_weather(match["id"], weather)
                    print("  ✅ Updated")
                    success_count += 1
                except Exception as e:
                    print(f"  ❌ Update error: {e}")
            else:
                print("  ❌ Weather fetch failed")
                skipped_count += 1
            
            # Rate limiting (WeatherAPI allows ~60 req/min on free tier)
            time.sleep(1)
        
        print(f"\n{'='*50}")
        print(f"✅ Complete!")
        print(f"Updated: {success_count}")
        print(f"Skipped: {skipped_count}")
        print(f"Total: {len(matches)}")


if __name__ == "__main__":
    enricher = WeatherEnricher()
    enricher.process_matches()

