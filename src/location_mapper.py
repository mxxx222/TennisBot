"""
Location Mapping System
Maps stadium names, team names, and venues to cities for weather API lookups
"""

import logging
from typing import Dict, Optional


logger = logging.getLogger(__name__)


class LocationMapper:
    """
    Maps various location identifiers to city names for weather API
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Stadium to city mappings (common stadiums)
        self.stadium_to_city: Dict[str, str] = {
            # Premier League
            'Old Trafford': 'Manchester',
            'Etihad Stadium': 'Manchester',
            'Anfield': 'Liverpool',
            'Stamford Bridge': 'London',
            'Emirates Stadium': 'London',
            'Tottenham Hotspur Stadium': 'London',
            'London Stadium': 'London',
            'Selhurst Park': 'London',
            'Craven Cottage': 'London',
            'Villa Park': 'Birmingham',
            'St. James\' Park': 'Newcastle',
            'Stadium of Light': 'Sunderland',
            'Goodison Park': 'Liverpool',
            'Elland Road': 'Leeds',
            'Molineux': 'Wolverhampton',
            'King Power Stadium': 'Leicester',
            'Vicarage Road': 'Watford',
            'Turf Moor': 'Burnley',
            'The Hawthorns': 'West Bromwich',
            'Bramall Lane': 'Sheffield',
            
            # La Liga
            'Santiago Bernabéu': 'Madrid',
            'Camp Nou': 'Barcelona',
            'Wanda Metropolitano': 'Madrid',
            'Estadio Ramón Sánchez-Pizjuán': 'Seville',
            'Estadio Mestalla': 'Valencia',
            'San Mamés': 'Bilbao',
            
            # Serie A
            'San Siro': 'Milan',
            'Stadio Olimpico': 'Rome',
            'Allianz Stadium': 'Turin',
            'Stadio Diego Armando Maradona': 'Naples',
            
            # Bundesliga
            'Allianz Arena': 'Munich',
            'Signal Iduna Park': 'Dortmund',
            'Olympiastadion': 'Berlin',
            
            # Other major cities
            'Parc des Princes': 'Paris',
            'Stade de France': 'Paris',
            'Amsterdam Arena': 'Amsterdam',
            'Johan Cruyff Arena': 'Amsterdam'
        }
        
        # Team name to city mappings (common patterns)
        self.team_to_city: Dict[str, str] = {
            'Manchester United': 'Manchester',
            'Manchester City': 'Manchester',
            'Liverpool': 'Liverpool',
            'Chelsea': 'London',
            'Arsenal': 'London',
            'Tottenham': 'London',
            'West Ham': 'London',
            'Crystal Palace': 'London',
            'Fulham': 'London',
            'Aston Villa': 'Birmingham',
            'Newcastle': 'Newcastle',
            'Leeds': 'Leeds',
            'Leicester': 'Leicester',
            'Real Madrid': 'Madrid',
            'Atletico Madrid': 'Madrid',
            'Barcelona': 'Barcelona',
            'Sevilla': 'Seville',
            'Valencia': 'Valencia',
            'AC Milan': 'Milan',
            'Inter Milan': 'Milan',
            'Roma': 'Rome',
            'Juventus': 'Turin',
            'Bayern Munich': 'Munich',
            'Borussia Dortmund': 'Dortmund',
            'Paris Saint-Germain': 'Paris',
            'PSG': 'Paris',
            'Ajax': 'Amsterdam'
        }
        
        # League/tournament to default city mappings
        self.league_defaults: Dict[str, str] = {
            'Premier League': 'London',
            'La Liga': 'Madrid',
            'Serie A': 'Milan',
            'Bundesliga': 'Munich',
            'Ligue 1': 'Paris',
            'Champions League': 'London',  # Default to London
            'Europa League': 'London',
            'Wimbledon': 'London',
            'US Open': 'New York',
            'French Open': 'Paris',
            'Australian Open': 'Melbourne'
        }
    
    def map_to_city(self, match_data: Dict) -> str:
        """
        Map match data to a city name for weather API
        
        Args:
            match_data: Dictionary containing match information
            
        Returns:
            City name for weather API lookup
        """
        # Try venue/stadium first
        venue = match_data.get('venue') or match_data.get('stadium')
        if venue and venue in self.stadium_to_city:
            city = self.stadium_to_city[venue]
            self.logger.debug(f"Mapped venue '{venue}' to city '{city}'")
            return city
        
        # Try city field directly
        city = match_data.get('city') or match_data.get('venue_city') or match_data.get('stadium_city')
        if city:
            self.logger.debug(f"Using direct city field: '{city}'")
            return city
        
        # Try team name mapping
        home_team = match_data.get('home_team', '')
        if home_team in self.team_to_city:
            city = self.team_to_city[home_team]
            self.logger.debug(f"Mapped team '{home_team}' to city '{city}'")
            return city
        
        # Try extracting city from team name (common patterns)
        city = self._extract_city_from_team_name(home_team)
        if city:
            self.logger.debug(f"Extracted city '{city}' from team name '{home_team}'")
            return city
        
        # Try league/tournament default
        league = match_data.get('league') or match_data.get('tournament')
        if league and league in self.league_defaults:
            city = self.league_defaults[league]
            self.logger.debug(f"Using league default '{city}' for '{league}'")
            return city
        
        # Fallback: try to extract from any text field
        for field in ['venue', 'league', 'tournament', 'home_team', 'away_team']:
            value = match_data.get(field, '')
            if value:
                city = self._extract_city_from_text(value)
                if city:
                    self.logger.debug(f"Extracted city '{city}' from field '{field}': '{value}'")
                    return city
        
        # Ultimate fallback
        self.logger.warning(f"Could not map location for match, using default 'London'")
        return 'London'
    
    def _extract_city_from_team_name(self, team_name: str) -> Optional[str]:
        """Extract city name from team name using common patterns"""
        if not team_name:
            return None
        
        # Common patterns: "City FC", "City United", etc.
        common_cities = [
            'London', 'Manchester', 'Liverpool', 'Birmingham', 'Leeds',
            'Newcastle', 'Leicester', 'Sheffield', 'Nottingham', 'Norwich',
            'Southampton', 'Brighton', 'Bournemouth', 'Cardiff', 'Swansea',
            'Madrid', 'Barcelona', 'Valencia', 'Seville', 'Bilbao',
            'Milan', 'Rome', 'Turin', 'Naples', 'Florence',
            'Munich', 'Berlin', 'Dortmund', 'Hamburg', 'Frankfurt',
            'Paris', 'Lyon', 'Marseille', 'Amsterdam', 'Rotterdam'
        ]
        
        team_lower = team_name.lower()
        for city in common_cities:
            if city.lower() in team_lower:
                return city
        
        return None
    
    def _extract_city_from_text(self, text: str) -> Optional[str]:
        """Extract city name from any text"""
        return self._extract_city_from_team_name(text)
    
    def add_stadium_mapping(self, stadium: str, city: str):
        """Add a custom stadium to city mapping"""
        self.stadium_to_city[stadium] = city
        self.logger.info(f"Added stadium mapping: {stadium} -> {city}")
    
    def add_team_mapping(self, team: str, city: str):
        """Add a custom team to city mapping"""
        self.team_to_city[team] = city
        self.logger.info(f"Added team mapping: {team} -> {city}")


# Global instance
_location_mapper = None


def get_location_mapper() -> LocationMapper:
    """Get or create global location mapper instance"""
    global _location_mapper
    if _location_mapper is None:
        _location_mapper = LocationMapper()
    return _location_mapper

