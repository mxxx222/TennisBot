#!/usr/bin/env python3
"""
🎾 TENNIS RELATIONAL DATABASE - NOTION CREATION
===============================================

Luo täydellinen relaatiomalli Notioniin:
- 4 perustaulua (Players, Tournaments, Events, Matches)
- 11 tilastotaulua
- Relaatiot taulujen välille
- Näkymät ja suodattimet

Author: TennisBot Advanced Analytics
Version: 1.0.0
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

try:
    from notion_client import Client
    NOTION_API_AVAILABLE = True
except ImportError:
    NOTION_API_AVAILABLE = False
    print("⚠️ notion-client not installed. Install with: pip install notion-client")


class TennisRelationalDBCreator:
    """
    Luo täydellinen tennis-relaatiomalli Notioniin
    """
    
    def __init__(self, notion_token: str, parent_page_id: str):
        """
        Initialize creator
        
        Args:
            notion_token: Notion API token
            parent_page_id: Parent page ID
        """
        if not NOTION_API_AVAILABLE:
            raise ImportError("notion-client not available")
        
        self.notion = Client(auth=notion_token)
        self.parent_page_id = parent_page_id
        self.databases = {}
        
        print("🎾 Tennis Relational Database Creator initialized")
    
    def create_all_databases(self, surface_stats_option: int = 1):
        """
        Luo kaikki tietokannat
        
        Args:
            surface_stats_option: 1 = Yksi taulu, 2 = Kolme erillistä taulua
        """
        print("\n🏗️ Creating Tennis Relational Database Structure...")
        print("=" * 60)
        
        # 1. PERUSTAULUT
        print("\n📊 Creating Base Tables...")
        
        # Players
        players_db = self.create_players_database()
        if players_db:
            self.databases['players'] = players_db
            print(f"   ✅ Players: {players_db}")
        
        # Tournaments
        tournaments_db = self.create_tournaments_database()
        if tournaments_db:
            self.databases['tournaments'] = tournaments_db
            print(f"   ✅ Tournaments: {tournaments_db}")
        
        # Events
        events_db = self.create_events_database()
        if events_db:
            self.databases['events'] = events_db
            print(f"   ✅ Events: {events_db}")
        
        # Matches
        matches_db = self.create_matches_database()
        if matches_db:
            self.databases['matches'] = matches_db
            print(f"   ✅ Matches: {matches_db}")
        
        # 2. TILASTOTAULUT
        print("\n📈 Creating Statistics Tables...")
        
        # Player Stats
        player_stats_db = self.create_player_stats_database()
        if player_stats_db:
            self.databases['player_stats'] = player_stats_db
            print(f"   ✅ Player Stats: {player_stats_db}")
        
        # Surface Stats (Option 1 or 2)
        if surface_stats_option == 1:
            surface_stats_db = self.create_surface_stats_unified_database()
            if surface_stats_db:
                self.databases['surface_stats'] = surface_stats_db
                print(f"   ✅ Surface Stats (Unified): {surface_stats_db}")
        else:
            hard_db = self.create_surface_stats_database('Hard')
            clay_db = self.create_surface_stats_database('Clay')
            grass_db = self.create_surface_stats_database('Grass')
            if hard_db:
                self.databases['surface_stats_hard'] = hard_db
                print(f"   ✅ Surface Stats Hard: {hard_db}")
            if clay_db:
                self.databases['surface_stats_clay'] = clay_db
                print(f"   ✅ Surface Stats Clay: {clay_db}")
            if grass_db:
                self.databases['surface_stats_grass'] = grass_db
                print(f"   ✅ Surface Stats Grass: {grass_db}")
        
        # Serve Stats
        serve_stats_db = self.create_serve_stats_database()
        if serve_stats_db:
            self.databases['serve_stats'] = serve_stats_db
            print(f"   ✅ Serve Stats: {serve_stats_db}")
        
        # Return Stats
        return_stats_db = self.create_return_stats_database()
        if return_stats_db:
            self.databases['return_stats'] = return_stats_db
            print(f"   ✅ Return Stats: {return_stats_db}")
        
        # Quality Stats
        quality_stats_db = self.create_quality_stats_database()
        if quality_stats_db:
            self.databases['quality_stats'] = quality_stats_db
            print(f"   ✅ Quality Stats: {quality_stats_db}")
        
        # H2H Stats
        h2h_stats_db = self.create_h2h_stats_database()
        if h2h_stats_db:
            self.databases['h2h_stats'] = h2h_stats_db
            print(f"   ✅ H2H Stats: {h2h_stats_db}")
        
        # Ratings
        ratings_db = self.create_ratings_database()
        if ratings_db:
            self.databases['ratings'] = ratings_db
            print(f"   ✅ Ratings: {ratings_db}")
        
        # Odds
        odds_db = self.create_odds_database()
        if odds_db:
            self.databases['odds'] = odds_db
            print(f"   ✅ Odds: {odds_db}")
        
        # ROI Analysis
        roi_db = self.create_roi_analysis_database()
        if roi_db:
            self.databases['roi_analysis'] = roi_db
            print(f"   ✅ ROI Analysis: {roi_db}")
        
        # Environment
        environment_db = self.create_environment_database()
        if environment_db:
            self.databases['environment'] = environment_db
            print(f"   ✅ Environment: {environment_db}")
        
        # Health
        health_db = self.create_health_database()
        if health_db:
            self.databases['health'] = health_db
            print(f"   ✅ Health: {health_db}")
        
        # Summary
        print("\n" + "=" * 60)
        print(f"✅ Created {len(self.databases)} databases")
        
        # Save to config
        self.save_config()
        
        return self.databases
    
    def create_players_database(self) -> Optional[str]:
        """Luo Players-tietokanta"""
        try:
            db = self.notion.databases.create(
                parent={"page_id": self.parent_page_id},
                title=[{"type": "text", "text": {"content": "👤 Players"}}],
                properties={
                    "Name": {"title": {}},
                    "ATP/WTA": {"select": {"options": [
                        {"name": "ATP", "color": "blue"},
                        {"name": "WTA", "color": "pink"}
                    ]}},
                    "Ranking": {"number": {"format": "number"}},
                    "Ranking Points": {"number": {"format": "number"}},
                    "Career High Ranking": {"number": {"format": "number"}},
                    "Age": {"number": {"format": "number"}},
                    "Country": {"select": {}},
                    "Prize Money (Career)": {"number": {"format": "currency"}},
                    "Prize Money (Season)": {"number": {"format": "currency"}},
                    "Wins (Career)": {"number": {"format": "number"}},
                    "Losses (Career)": {"number": {"format": "number"}},
                    "Win % (Career)": {"number": {"format": "percent"}},
                    "Wins (Season)": {"number": {"format": "number"}},
                    "Losses (Season)": {"number": {"format": "number"}},
                    "Win % (Season)": {"number": {"format": "percent"}},
                    "Current Streak": {"rich_text": {}},
                    "Last Updated": {"date": {}}
                }
            )
            return db['id']
        except Exception as e:
            print(f"   ❌ Error creating Players: {e}")
            return None
    
    def create_tournaments_database(self) -> Optional[str]:
        """Luo Tournaments-tietokanta"""
        try:
            db = self.notion.databases.create(
                parent={"page_id": self.parent_page_id},
                title=[{"type": "text", "text": {"content": "🏆 Tournaments"}}],
                properties={
                    "Name": {"title": {}},
                    "Type": {"select": {"options": [
                        {"name": "Grand Slam", "color": "red"},
                        {"name": "ATP Masters 1000", "color": "blue"},
                        {"name": "WTA 1000", "color": "pink"},
                        {"name": "ATP 500", "color": "yellow"},
                        {"name": "WTA 500", "color": "orange"},
                        {"name": "ATP 250", "color": "green"},
                        {"name": "WTA 250", "color": "purple"},
                        {"name": "ITF", "color": "gray"}
                    ]}},
                    "Surface": {"select": {"options": [
                        {"name": "Hard", "color": "blue"},
                        {"name": "Clay", "color": "brown"},
                        {"name": "Grass", "color": "green"}
                    ]}},
                    "Location": {"rich_text": {}},
                    "Country": {"select": {}},
                    "Start Date": {"date": {}},
                    "End Date": {"date": {}},
                    "Prize Money": {"number": {"format": "currency"}},
                    "Points": {"number": {"format": "number"}},
                    "Players Count": {"number": {"format": "number"}},
                    "Defending Champion": {"relation": {"database_id": self.databases.get('players', '')}} if self.databases.get('players') else {"rich_text": {}}
                }
            )
            return db['id']
        except Exception as e:
            print(f"   ❌ Error creating Tournaments: {e}")
            return None
    
    def create_events_database(self) -> Optional[str]:
        """Luo Events-tietokanta (Round/Stage)"""
        try:
            db = self.notion.databases.create(
                parent={"page_id": self.parent_page_id},
                title=[{"type": "text", "text": {"content": "📅 Events"}}],
                properties={
                    "Name": {"title": {}},
                    "Tournament": {"relation": {"database_id": self.databases.get('tournaments', '')}} if self.databases.get('tournaments') else {"rich_text": {}},
                    "Round": {"select": {"options": [
                        {"name": "1st Round", "color": "gray"},
                        {"name": "2nd Round", "color": "gray"},
                        {"name": "3rd Round", "color": "yellow"},
                        {"name": "Round of 16", "color": "orange"},
                        {"name": "Quarterfinal", "color": "red"},
                        {"name": "Semifinal", "color": "purple"},
                        {"name": "Final", "color": "blue"}
                    ]}},
                    "Date": {"date": {}},
                    "Status": {"select": {"options": [
                        {"name": "Scheduled", "color": "gray"},
                        {"name": "Live", "color": "red"},
                        {"name": "Finished", "color": "green"},
                        {"name": "Postponed", "color": "yellow"},
                        {"name": "Cancelled", "color": "red"}
                    ]}},
                    "Surface": {"select": {"options": [
                        {"name": "Hard", "color": "blue"},
                        {"name": "Clay", "color": "brown"},
                        {"name": "Grass", "color": "green"}
                    ]}},
                    "Venue": {"rich_text": {}}
                }
            )
            return db['id']
        except Exception as e:
            print(f"   ❌ Error creating Events: {e}")
            return None
    
    def create_matches_database(self) -> Optional[str]:
        """Luo Matches-tietokanta"""
        try:
            db = self.notion.databases.create(
                parent={"page_id": self.parent_page_id},
                title=[{"type": "text", "text": {"content": "🎾 Matches"}}],
                properties={
                    "Match": {"title": {}},
                    "Player 1": {"relation": {"database_id": self.databases.get('players', '')}} if self.databases.get('players') else {"rich_text": {}},
                    "Player 2": {"relation": {"database_id": self.databases.get('players', '')}} if self.databases.get('players') else {"rich_text": {}},
                    "Event": {"relation": {"database_id": self.databases.get('events', '')}} if self.databases.get('events') else {"rich_text": {}},
                    "Tournament": {"relation": {"database_id": self.databases.get('tournaments', '')}} if self.databases.get('tournaments') else {"rich_text": {}},
                    "Date": {"date": {}},
                    "Status": {"select": {"options": [
                        {"name": "Scheduled", "color": "gray"},
                        {"name": "Live", "color": "red"},
                        {"name": "Finished", "color": "green"},
                        {"name": "Retired", "color": "yellow"},
                        {"name": "Walkover", "color": "orange"}
                    ]}},
                    "Surface": {"select": {"options": [
                        {"name": "Hard", "color": "blue"},
                        {"name": "Clay", "color": "brown"},
                        {"name": "Grass", "color": "green"}
                    ]}},
                    "Score": {"rich_text": {}},
                    "Sets Score": {"rich_text": {}},
                    "Games Score": {"rich_text": {}},
                    "Duration": {"rich_text": {}}
                }
            )
            return db['id']
        except Exception as e:
            print(f"   ❌ Error creating Matches: {e}")
            return None
    
    def create_player_stats_database(self) -> Optional[str]:
        """Luo Player Stats -tietokanta"""
        try:
            db = self.notion.databases.create(
                parent={"page_id": self.parent_page_id},
                title=[{"type": "text", "text": {"content": "📊 Player Stats"}}],
                properties={
                    "Player": {"relation": {"database_id": self.databases.get('players', '')}} if self.databases.get('players') else {"rich_text": {}},
                    "Season": {"rich_text": {}},
                    "Matches Played": {"number": {"format": "number"}},
                    "Wins": {"number": {"format": "number"}},
                    "Losses": {"number": {"format": "number"}},
                    "Win %": {"number": {"format": "percent"}},
                    "Last Updated": {"date": {}}
                }
            )
            return db['id']
        except Exception as e:
            print(f"   ❌ Error creating Player Stats: {e}")
            return None
    
    def create_surface_stats_unified_database(self) -> Optional[str]:
        """Luo yhdistetty Surface Stats -tietokanta (Option 1)"""
        try:
            db = self.notion.databases.create(
                parent={"page_id": self.parent_page_id},
                title=[{"type": "text", "text": {"content": "🏟️ Surface Stats"}}],
                properties={
                    "Player": {"relation": {"database_id": self.databases.get('players', '')}} if self.databases.get('players') else {"rich_text": {}},
                    "Surface": {"select": {"options": [
                        {"name": "Hard", "color": "blue"},
                        {"name": "Clay", "color": "brown"},
                        {"name": "Grass", "color": "green"}
                    ]}},
                    "Hard Wins": {"number": {"format": "number"}},
                    "Hard Losses": {"number": {"format": "number"}},
                    "Hard Win %": {"number": {"format": "percent"}},
                    "Clay Wins": {"number": {"format": "number"}},
                    "Clay Losses": {"number": {"format": "number"}},
                    "Clay Win %": {"number": {"format": "percent"}},
                    "Grass Wins": {"number": {"format": "number"}},
                    "Grass Losses": {"number": {"format": "number"}},
                    "Grass Win %": {"number": {"format": "percent"}},
                    "Last Updated": {"date": {}}
                }
            )
            return db['id']
        except Exception as e:
            print(f"   ❌ Error creating Surface Stats: {e}")
            return None
    
    def create_surface_stats_database(self, surface: str) -> Optional[str]:
        """Luo erillinen Surface Stats -tietokanta (Option 2)"""
        try:
            db = self.notion.databases.create(
                parent={"page_id": self.parent_page_id},
                title=[{"type": "text", "text": {"content": f"🏟️ {surface} Stats"}}],
                properties={
                    "Player": {"relation": {"database_id": self.databases.get('players', '')}} if self.databases.get('players') else {"rich_text": {}},
                    "Wins": {"number": {"format": "number"}},
                    "Losses": {"number": {"format": "number"}},
                    "Win %": {"number": {"format": "percent"}},
                    "Matches Played": {"number": {"format": "number"}},
                    "Ranking": {"number": {"format": "number"}},
                    "Last Updated": {"date": {}}
                }
            )
            return db['id']
        except Exception as e:
            print(f"   ❌ Error creating {surface} Stats: {e}")
            return None
    
    def create_serve_stats_database(self) -> Optional[str]:
        """Luo Serve Stats -tietokanta"""
        try:
            db = self.notion.databases.create(
                parent={"page_id": self.parent_page_id},
                title=[{"type": "text", "text": {"content": "🎯 Serve Stats"}}],
                properties={
                    "Player": {"relation": {"database_id": self.databases.get('players', '')}} if self.databases.get('players') else {"rich_text": {}},
                    "Match": {"relation": {"database_id": self.databases.get('matches', '')}} if self.databases.get('matches') else {"rich_text": {}},
                    "Serve %": {"number": {"format": "percent"}},
                    "First Serve %": {"number": {"format": "percent"}},
                    "Second Serve %": {"number": {"format": "percent"}},
                    "First Serve Points Won %": {"number": {"format": "percent"}},
                    "Second Serve Points Won %": {"number": {"format": "percent"}},
                    "Service Games Won %": {"number": {"format": "percent"}},
                    "Aces": {"number": {"format": "number"}},
                    "Double Faults": {"number": {"format": "number"}},
                    "Break Points Saved %": {"number": {"format": "percent"}},
                    "Break Points Faced": {"number": {"format": "number"}},
                    "Last Updated": {"date": {}}
                }
            )
            return db['id']
        except Exception as e:
            print(f"   ❌ Error creating Serve Stats: {e}")
            return None
    
    def create_return_stats_database(self) -> Optional[str]:
        """Luo Return Stats -tietokanta"""
        try:
            db = self.notion.databases.create(
                parent={"page_id": self.parent_page_id},
                title=[{"type": "text", "text": {"content": "🔄 Return Stats"}}],
                properties={
                    "Player": {"relation": {"database_id": self.databases.get('players', '')}} if self.databases.get('players') else {"rich_text": {}},
                    "Match": {"relation": {"database_id": self.databases.get('matches', '')}} if self.databases.get('matches') else {"rich_text": {}},
                    "Return Games Won %": {"number": {"format": "percent"}},
                    "Return Points Won %": {"number": {"format": "percent"}},
                    "Break Points Converted %": {"number": {"format": "percent"}},
                    "Break Points Opportunities": {"number": {"format": "number"}},
                    "Return Points Won vs First Serve %": {"number": {"format": "percent"}},
                    "Return Points Won vs Second Serve %": {"number": {"format": "percent"}},
                    "Last Updated": {"date": {}}
                }
            )
            return db['id']
        except Exception as e:
            print(f"   ❌ Error creating Return Stats: {e}")
            return None
    
    def create_quality_stats_database(self) -> Optional[str]:
        """Luo Quality Stats -tietokanta"""
        try:
            db = self.notion.databases.create(
                parent={"page_id": self.parent_page_id},
                title=[{"type": "text", "text": {"content": "⭐ Quality Stats"}}],
                properties={
                    "Player": {"relation": {"database_id": self.databases.get('players', '')}} if self.databases.get('players') else {"rich_text": {}},
                    "Match": {"relation": {"database_id": self.databases.get('matches', '')}} if self.databases.get('matches') else {"rich_text": {}},
                    "Winners": {"number": {"format": "number"}},
                    "Unforced Errors": {"number": {"format": "number"}},
                    "Forced Errors": {"number": {"format": "number"}},
                    "Winners to Errors Ratio": {"number": {"format": "number"}},
                    "Net Points Won %": {"number": {"format": "percent"}},
                    "Net Points Played": {"number": {"format": "number"}},
                    "Last Updated": {"date": {}}
                }
            )
            return db['id']
        except Exception as e:
            print(f"   ❌ Error creating Quality Stats: {e}")
            return None
    
    def create_h2h_stats_database(self) -> Optional[str]:
        """Luo H2H Stats -tietokanta"""
        try:
            db = self.notion.databases.create(
                parent={"page_id": self.parent_page_id},
                title=[{"type": "text", "text": {"content": "⚔️ H2H Stats"}}],
                properties={
                    "Player 1": {"relation": {"database_id": self.databases.get('players', '')}} if self.databases.get('players') else {"rich_text": {}},
                    "Player 2": {"relation": {"database_id": self.databases.get('players', '')}} if self.databases.get('players') else {"rich_text": {}},
                    "Total Matches": {"number": {"format": "number"}},
                    "Player 1 Wins": {"number": {"format": "number"}},
                    "Player 2 Wins": {"number": {"format": "number"}},
                    "Player 1 Win %": {"number": {"format": "percent"}},
                    "Last Meeting Date": {"date": {}},
                    "Last Meeting Result": {"rich_text": {}},
                    "Hard H2H": {"rich_text": {}},
                    "Clay H2H": {"rich_text": {}},
                    "Grass H2H": {"rich_text": {}},
                    "Recent Form (Last 5)": {"rich_text": {}},
                    "Last Updated": {"date": {}}
                }
            )
            return db['id']
        except Exception as e:
            print(f"   ❌ Error creating H2H Stats: {e}")
            return None
    
    def create_ratings_database(self) -> Optional[str]:
        """Luo Ratings -tietokanta"""
        try:
            db = self.notion.databases.create(
                parent={"page_id": self.parent_page_id},
                title=[{"type": "text", "text": {"content": "📈 Ratings"}}],
                properties={
                    "Player": {"relation": {"database_id": self.databases.get('players', '')}} if self.databases.get('players') else {"rich_text": {}},
                    "Match": {"relation": {"database_id": self.databases.get('matches', '')}} if self.databases.get('matches') else {"rich_text": {}},
                    "ELO Rating": {"number": {"format": "number"}},
                    "ELO Change": {"number": {"format": "number"}},
                    "TrueSkill Rating": {"number": {"format": "number"}},
                    "Expected Win Probability %": {"number": {"format": "percent"}},
                    "Statistical Edge %": {"number": {"format": "percent"}},
                    "Last Updated": {"date": {}}
                }
            )
            return db['id']
        except Exception as e:
            print(f"   ❌ Error creating Ratings: {e}")
            return None
    
    def create_odds_database(self) -> Optional[str]:
        """Luo Odds -tietokanta"""
        try:
            db = self.notion.databases.create(
                parent={"page_id": self.parent_page_id},
                title=[{"type": "text", "text": {"content": "💰 Odds"}}],
                properties={
                    "Match": {"relation": {"database_id": self.databases.get('matches', '')}} if self.databases.get('matches') else {"rich_text": {}},
                    "Player": {"select": {"options": [
                        {"name": "Player 1", "color": "blue"},
                        {"name": "Player 2", "color": "red"}
                    ]}},
                    "Odds": {"number": {"format": "number"}},
                    "Best Odds": {"number": {"format": "number"}},
                    "Bookmaker": {"select": {}},
                    "Odds Movement": {"rich_text": {}},
                    "Market Margin %": {"number": {"format": "percent"}},
                    "Implied Probability %": {"number": {"format": "percent"}},
                    "Last Updated": {"date": {}}
                }
            )
            return db['id']
        except Exception as e:
            print(f"   ❌ Error creating Odds: {e}")
            return None
    
    def create_roi_analysis_database(self) -> Optional[str]:
        """Luo ROI Analysis -tietokanta"""
        try:
            db = self.notion.databases.create(
                parent={"page_id": self.parent_page_id},
                title=[{"type": "text", "text": {"content": "💎 ROI Analysis"}}],
                properties={
                    "Match": {"relation": {"database_id": self.databases.get('matches', '')}} if self.databases.get('matches') else {"rich_text": {}},
                    "Player": {"select": {"options": [
                        {"name": "Player 1", "color": "blue"},
                        {"name": "Player 2", "color": "red"}
                    ]}},
                    "True Probability %": {"number": {"format": "percent"}},
                    "Market Probability %": {"number": {"format": "percent"}},
                    "Edge %": {"number": {"format": "percent"}},
                    "Expected Value %": {"number": {"format": "percent"}},
                    "Recommended Stake €": {"number": {"format": "currency"}},
                    "Kelly %": {"number": {"format": "percent"}},
                    "ROI %": {"number": {"format": "percent"}},
                    "Confidence": {"select": {"options": [
                        {"name": "High", "color": "green"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Low", "color": "red"}
                    ]}},
                    "Risk Score": {"number": {"format": "number"}},
                    "Result": {"select": {"options": [
                        {"name": "Win", "color": "green"},
                        {"name": "Loss", "color": "red"},
                        {"name": "Pending", "color": "gray"}
                    ]}},
                    "Profit/Loss €": {"number": {"format": "currency"}},
                    "Last Updated": {"date": {}}
                }
            )
            return db['id']
        except Exception as e:
            print(f"   ❌ Error creating ROI Analysis: {e}")
            return None
    
    def create_environment_database(self) -> Optional[str]:
        """Luo Environment -tietokanta"""
        try:
            db = self.notion.databases.create(
                parent={"page_id": self.parent_page_id},
                title=[{"type": "text", "text": {"content": "🌤️ Environment"}}],
                properties={
                    "Match": {"relation": {"database_id": self.databases.get('matches', '')}} if self.databases.get('matches') else {"rich_text": {}},
                    "Weather": {"select": {"options": [
                        {"name": "Sunny", "color": "yellow"},
                        {"name": "Cloudy", "color": "gray"},
                        {"name": "Rainy", "color": "blue"},
                        {"name": "Windy", "color": "orange"}
                    ]}},
                    "Temperature °C": {"number": {"format": "number"}},
                    "Humidity %": {"number": {"format": "percent"}},
                    "Wind Speed km/h": {"number": {"format": "number"}},
                    "Precipitation mm": {"number": {"format": "number"}},
                    "Court Speed": {"select": {"options": [
                        {"name": "Slow", "color": "red"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Fast", "color": "green"}
                    ]}},
                    "Altitude m": {"number": {"format": "number"}},
                    "Time Zone": {"rich_text": {}},
                    "Last Updated": {"date": {}}
                }
            )
            return db['id']
        except Exception as e:
            print(f"   ❌ Error creating Environment: {e}")
            return None
    
    def create_health_database(self) -> Optional[str]:
        """Luo Health -tietokanta"""
        try:
            db = self.notion.databases.create(
                parent={"page_id": self.parent_page_id},
                title=[{"type": "text", "text": {"content": "🏥 Health"}}],
                properties={
                    "Player": {"relation": {"database_id": self.databases.get('players', '')}} if self.databases.get('players') else {"rich_text": {}},
                    "Match": {"relation": {"database_id": self.databases.get('matches', '')}} if self.databases.get('matches') else {"rich_text": {}},
                    "Injury Status": {"select": {"options": [
                        {"name": "Healthy", "color": "green"},
                        {"name": "Questionable", "color": "yellow"},
                        {"name": "Out", "color": "red"}
                    ]}},
                    "Injuries": {"rich_text": {}},
                    "Recent Injuries": {"rich_text": {}},
                    "Rest Days": {"number": {"format": "number"}},
                    "Fatigue Level": {"number": {"format": "number"}},
                    "Match Load (7 days)": {"number": {"format": "number"}},
                    "Last Updated": {"date": {}}
                }
            )
            return db['id']
        except Exception as e:
            print(f"   ❌ Error creating Health: {e}")
            return None
    
    def save_config(self):
        """Tallenna konfiguraatio"""
        config_file = Path('config/tennis_relational_db.json')
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        config = {
            'created_at': datetime.now().isoformat(),
            'parent_page_id': self.parent_page_id,
            'databases': self.databases
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\n💾 Config saved to {config_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Create Tennis Relational Database in Notion')
    parser.add_argument('--token', '-t', required=True, help='Notion API token')
    parser.add_argument('--page-id', '-p', required=True, help='Notion parent page ID')
    parser.add_argument('--surface-option', '-s', type=int, default=1, choices=[1, 2],
                       help='Surface Stats option: 1=Unified table, 2=Separate tables')
    
    args = parser.parse_args()
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║  🎾 TENNIS RELATIONAL DATABASE CREATOR                      ║
║  ==========================================================  ║
║                                                              ║
║  Creates complete relational model in Notion:               ║
║  - 4 Base Tables (Players, Tournaments, Events, Matches)     ║
║  - 11 Statistics Tables                                     ║
║  - Relations between tables                                 ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    creator = TennisRelationalDBCreator(args.token, args.page_id)
    databases = creator.create_all_databases(surface_stats_option=args.surface_option)
    
    if databases:
        print(f"\n✅ Successfully created {len(databases)} databases!")
        print("\n📊 Database IDs:")
        for name, db_id in databases.items():
            print(f"   • {name}: {db_id}")
    else:
        print("\n❌ Failed to create databases")


if __name__ == "__main__":
    main()






