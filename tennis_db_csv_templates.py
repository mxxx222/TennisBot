#!/usr/bin/env python3
"""
📊 TENNIS DATABASE CSV TEMPLATES
=================================

Luo CSV-pohjat kaikille Notion-taululle bulk-importtia varten.

Author: TennisBot Advanced Analytics
Version: 1.0.0
"""

import csv
from pathlib import Path
from datetime import datetime


class CSVTemplatesGenerator:
    """Generoi CSV-pohjat kaikille tauluille"""
    
    def __init__(self, output_dir: str = "data/csv_templates"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Output directory: {self.output_dir}")
    
    def generate_all_templates(self):
        """Generoi kaikki CSV-pohjat"""
        print("\n📊 Generating CSV Templates...")
        print("=" * 60)
        
        # Perustaulut
        self.generate_players_template()
        self.generate_tournaments_template()
        self.generate_events_template()
        self.generate_matches_template()
        
        # Tilastotaulut
        self.generate_player_stats_template()
        self.generate_surface_stats_template()
        self.generate_serve_stats_template()
        self.generate_return_stats_template()
        self.generate_quality_stats_template()
        self.generate_h2h_stats_template()
        self.generate_ratings_template()
        self.generate_odds_template()
        self.generate_roi_analysis_template()
        self.generate_environment_template()
        self.generate_health_template()
        
        print("\n✅ All CSV templates generated!")
        print(f"📁 Location: {self.output_dir}")
    
    def generate_players_template(self):
        """Luo Players CSV-pohja"""
        filename = self.output_dir / "01_players_template.csv"
        headers = [
            "Name",
            "ATP/WTA",
            "Ranking",
            "Ranking Points",
            "Career High Ranking",
            "Age",
            "Country",
            "Prize Money (Career)",
            "Prize Money (Season)",
            "Wins (Career)",
            "Losses (Career)",
            "Win % (Career)",
            "Wins (Season)",
            "Losses (Season)",
            "Win % (Season)",
            "Current Streak",
            "Last Updated"
        ]
        
        example_rows = [
            [
                "Novak Djokovic",
                "ATP",
                "1",
                "9795",
                "1",
                "37",
                "Serbia",
                "180000000",
                "8500000",
                "1089",
                "219",
                "0.833",
                "45",
                "8",
                "0.849",
                "W5",
                datetime.now().strftime("%Y-%m-%d")
            ],
            [
                "Iga Swiatek",
                "WTA",
                "1",
                "9850",
                "1",
                "23",
                "Poland",
                "25000000",
                "6500000",
                "280",
                "45",
                "0.862",
                "68",
                "11",
                "0.861",
                "W3",
                datetime.now().strftime("%Y-%m-%d")
            ]
        ]
        
        self._write_csv(filename, headers, example_rows)
        print(f"   ✅ Players: {filename.name}")
    
    def generate_tournaments_template(self):
        """Luo Tournaments CSV-pohja"""
        filename = self.output_dir / "02_tournaments_template.csv"
        headers = [
            "Name",
            "Type",
            "Surface",
            "Location",
            "Country",
            "Start Date",
            "End Date",
            "Prize Money",
            "Points",
            "Players Count",
            "Defending Champion"
        ]
        
        example_rows = [
            [
                "Wimbledon",
                "Grand Slam",
                "Grass",
                "London",
                "United Kingdom",
                "2025-06-23",
                "2025-07-06",
                "50000000",
                "2000",
                "128",
                "Carlos Alcaraz"
            ],
            [
                "Roland Garros",
                "Grand Slam",
                "Clay",
                "Paris",
                "France",
                "2025-05-26",
                "2025-06-08",
                "50000000",
                "2000",
                "128",
                "Iga Swiatek"
            ]
        ]
        
        self._write_csv(filename, headers, example_rows)
        print(f"   ✅ Tournaments: {filename.name}")
    
    def generate_events_template(self):
        """Luo Events CSV-pohja"""
        filename = self.output_dir / "03_events_template.csv"
        headers = [
            "Name",
            "Tournament",
            "Round",
            "Date",
            "Status",
            "Surface",
            "Venue"
        ]
        
        example_rows = [
            [
                "Wimbledon 2025 - Men's Singles",
                "Wimbledon",
                "Final",
                "2025-07-06",
                "Scheduled",
                "Grass",
                "Centre Court"
            ],
            [
                "Roland Garros 2025 - Women's Singles",
                "Roland Garros",
                "Semifinal",
                "2025-06-06",
                "Finished",
                "Clay",
                "Court Philippe-Chatrier"
            ]
        ]
        
        self._write_csv(filename, headers, example_rows)
        print(f"   ✅ Events: {filename.name}")
    
    def generate_matches_template(self):
        """Luo Matches CSV-pohja"""
        filename = self.output_dir / "04_matches_template.csv"
        headers = [
            "Match",
            "Player 1",
            "Player 2",
            "Event",
            "Tournament",
            "Date",
            "Status",
            "Surface",
            "Score",
            "Sets Score",
            "Games Score",
            "Duration"
        ]
        
        example_rows = [
            [
                "Djokovic vs Alcaraz",
                "Novak Djokovic",
                "Carlos Alcaraz",
                "Wimbledon 2025 - Men's Singles",
                "Wimbledon",
                "2025-07-06",
                "Scheduled",
                "Grass",
                "",
                "",
                "",
                ""
            ],
            [
                "Swiatek vs Sabalenka",
                "Iga Swiatek",
                "Aryna Sabalenka",
                "Roland Garros 2025 - Women's Singles",
                "Roland Garros",
                "2025-06-06",
                "Finished",
                "Clay",
                "6-4, 6-2",
                "2-0",
                "12-6",
                "1h 25m"
            ]
        ]
        
        self._write_csv(filename, headers, example_rows)
        print(f"   ✅ Matches: {filename.name}")
    
    def generate_player_stats_template(self):
        """Luo Player Stats CSV-pohja"""
        filename = self.output_dir / "05_player_stats_template.csv"
        headers = [
            "Player",
            "Season",
            "Matches Played",
            "Wins",
            "Losses",
            "Win %",
            "Last Updated"
        ]
        
        example_rows = [
            [
                "Novak Djokovic",
                "2025",
                "53",
                "45",
                "8",
                "0.849",
                datetime.now().strftime("%Y-%m-%d")
            ]
        ]
        
        self._write_csv(filename, headers, example_rows)
        print(f"   ✅ Player Stats: {filename.name}")
    
    def generate_surface_stats_template(self):
        """Luo Surface Stats CSV-pohja (Option 1: Unified)"""
        filename = self.output_dir / "06_surface_stats_template.csv"
        headers = [
            "Player",
            "Surface",
            "Hard Wins",
            "Hard Losses",
            "Hard Win %",
            "Clay Wins",
            "Clay Losses",
            "Clay Win %",
            "Grass Wins",
            "Grass Losses",
            "Grass Win %",
            "Last Updated"
        ]
        
        example_rows = [
            [
                "Novak Djokovic",
                "Hard",
                "450",
                "85",
                "0.841",
                "280",
                "75",
                "0.789",
                "120",
                "25",
                "0.828",
                datetime.now().strftime("%Y-%m-%d")
            ]
        ]
        
        self._write_csv(filename, headers, example_rows)
        print(f"   ✅ Surface Stats: {filename.name}")
    
    def generate_serve_stats_template(self):
        """Luo Serve Stats CSV-pohja"""
        filename = self.output_dir / "07_serve_stats_template.csv"
        headers = [
            "Player",
            "Match",
            "Serve %",
            "First Serve %",
            "Second Serve %",
            "First Serve Points Won %",
            "Second Serve Points Won %",
            "Service Games Won %",
            "Aces",
            "Double Faults",
            "Break Points Saved %",
            "Break Points Faced",
            "Last Updated"
        ]
        
        example_rows = [
            [
                "Novak Djokovic",
                "Djokovic vs Alcaraz",
                "0.68",
                "0.72",
                "0.64",
                "0.78",
                "0.55",
                "0.88",
                "12",
                "3",
                "0.75",
                "8",
                datetime.now().strftime("%Y-%m-%d")
            ]
        ]
        
        self._write_csv(filename, headers, example_rows)
        print(f"   ✅ Serve Stats: {filename.name}")
    
    def generate_return_stats_template(self):
        """Luo Return Stats CSV-pohja"""
        filename = self.output_dir / "08_return_stats_template.csv"
        headers = [
            "Player",
            "Match",
            "Return Games Won %",
            "Return Points Won %",
            "Break Points Converted %",
            "Break Points Opportunities",
            "Return Points Won vs First Serve %",
            "Return Points Won vs Second Serve %",
            "Last Updated"
        ]
        
        example_rows = [
            [
                "Novak Djokovic",
                "Djokovic vs Alcaraz",
                "0.32",
                "0.42",
                "0.45",
                "11",
                "0.28",
                "0.58",
                datetime.now().strftime("%Y-%m-%d")
            ]
        ]
        
        self._write_csv(filename, headers, example_rows)
        print(f"   ✅ Return Stats: {filename.name}")
    
    def generate_quality_stats_template(self):
        """Luo Quality Stats CSV-pohja"""
        filename = self.output_dir / "09_quality_stats_template.csv"
        headers = [
            "Player",
            "Match",
            "Winners",
            "Unforced Errors",
            "Forced Errors",
            "Winners to Errors Ratio",
            "Net Points Won %",
            "Net Points Played",
            "Last Updated"
        ]
        
        example_rows = [
            [
                "Novak Djokovic",
                "Djokovic vs Alcaraz",
                "35",
                "18",
                "12",
                "1.94",
                "0.75",
                "20",
                datetime.now().strftime("%Y-%m-%d")
            ]
        ]
        
        self._write_csv(filename, headers, example_rows)
        print(f"   ✅ Quality Stats: {filename.name}")
    
    def generate_h2h_stats_template(self):
        """Luo H2H Stats CSV-pohja"""
        filename = self.output_dir / "10_h2h_stats_template.csv"
        headers = [
            "Player 1",
            "Player 2",
            "Total Matches",
            "Player 1 Wins",
            "Player 2 Wins",
            "Player 1 Win %",
            "Last Meeting Date",
            "Last Meeting Result",
            "Hard H2H",
            "Clay H2H",
            "Grass H2H",
            "Recent Form (Last 5)",
            "Last Updated"
        ]
        
        example_rows = [
            [
                "Novak Djokovic",
                "Carlos Alcaraz",
                "5",
                "3",
                "2",
                "0.60",
                "2024-07-14",
                "Djokovic 6-3, 6-4",
                "2-1",
                "1-1",
                "0-0",
                "W-L-W-W-L",
                datetime.now().strftime("%Y-%m-%d")
            ]
        ]
        
        self._write_csv(filename, headers, example_rows)
        print(f"   ✅ H2H Stats: {filename.name}")
    
    def generate_ratings_template(self):
        """Luo Ratings CSV-pohja"""
        filename = self.output_dir / "11_ratings_template.csv"
        headers = [
            "Player",
            "Match",
            "ELO Rating",
            "ELO Change",
            "TrueSkill Rating",
            "Expected Win Probability %",
            "Statistical Edge %",
            "Last Updated"
        ]
        
        example_rows = [
            [
                "Novak Djokovic",
                "Djokovic vs Alcaraz",
                "2150",
                "+15",
                "45.2",
                "0.65",
                "0.08",
                datetime.now().strftime("%Y-%m-%d")
            ]
        ]
        
        self._write_csv(filename, headers, example_rows)
        print(f"   ✅ Ratings: {filename.name}")
    
    def generate_odds_template(self):
        """Luo Odds CSV-pohja"""
        filename = self.output_dir / "12_odds_template.csv"
        headers = [
            "Match",
            "Player",
            "Odds",
            "Best Odds",
            "Bookmaker",
            "Odds Movement",
            "Market Margin %",
            "Implied Probability %",
            "Last Updated"
        ]
        
        example_rows = [
            [
                "Djokovic vs Alcaraz",
                "Player 1",
                "1.85",
                "1.90",
                "Bet365",
                "1.80 → 1.85",
                "0.05",
                "0.541",
                datetime.now().strftime("%Y-%m-%d")
            ],
            [
                "Djokovic vs Alcaraz",
                "Player 2",
                "2.10",
                "2.15",
                "Bet365",
                "2.05 → 2.10",
                "0.05",
                "0.476",
                datetime.now().strftime("%Y-%m-%d")
            ]
        ]
        
        self._write_csv(filename, headers, example_rows)
        print(f"   ✅ Odds: {filename.name}")
    
    def generate_roi_analysis_template(self):
        """Luo ROI Analysis CSV-pohja"""
        filename = self.output_dir / "13_roi_analysis_template.csv"
        headers = [
            "Match",
            "Player",
            "True Probability %",
            "Market Probability %",
            "Edge %",
            "Expected Value %",
            "Recommended Stake €",
            "Kelly %",
            "ROI %",
            "Confidence",
            "Risk Score",
            "Result",
            "Profit/Loss €",
            "Last Updated"
        ]
        
        example_rows = [
            [
                "Djokovic vs Alcaraz",
                "Player 1",
                "0.65",
                "0.541",
                "0.109",
                "0.20",
                "25.50",
                "0.25",
                "0.20",
                "High",
                "0.15",
                "Pending",
                "0",
                datetime.now().strftime("%Y-%m-%d")
            ]
        ]
        
        self._write_csv(filename, headers, example_rows)
        print(f"   ✅ ROI Analysis: {filename.name}")
    
    def generate_environment_template(self):
        """Luo Environment CSV-pohja"""
        filename = self.output_dir / "14_environment_template.csv"
        headers = [
            "Match",
            "Weather",
            "Temperature °C",
            "Humidity %",
            "Wind Speed km/h",
            "Precipitation mm",
            "Court Speed",
            "Altitude m",
            "Time Zone",
            "Last Updated"
        ]
        
        example_rows = [
            [
                "Djokovic vs Alcaraz",
                "Sunny",
                "22",
                "0.65",
                "8",
                "0",
                "Medium",
                "50",
                "UTC+1",
                datetime.now().strftime("%Y-%m-%d")
            ]
        ]
        
        self._write_csv(filename, headers, example_rows)
        print(f"   ✅ Environment: {filename.name}")
    
    def generate_health_template(self):
        """Luo Health CSV-pohja"""
        filename = self.output_dir / "15_health_template.csv"
        headers = [
            "Player",
            "Match",
            "Injury Status",
            "Injuries",
            "Recent Injuries",
            "Rest Days",
            "Fatigue Level",
            "Match Load (7 days)",
            "Last Updated"
        ]
        
        example_rows = [
            [
                "Novak Djokovic",
                "Djokovic vs Alcaraz",
                "Healthy",
                "",
                "",
                "2",
                "0.2",
                "3",
                datetime.now().strftime("%Y-%m-%d")
            ]
        ]
        
        self._write_csv(filename, headers, example_rows)
        print(f"   ✅ Health: {filename.name}")
    
    def _write_csv(self, filename: Path, headers: list, example_rows: list):
        """Kirjoita CSV-tiedosto"""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(example_rows)


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║  📊 TENNIS DATABASE CSV TEMPLATES GENERATOR                 ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    generator = CSVTemplatesGenerator()
    generator.generate_all_templates()
    
    print(f"\n✅ CSV templates ready for bulk import!")
    print(f"📁 Location: {generator.output_dir}")
    print("\n💡 Usage:")
    print("   1. Fill templates with your data")
    print("   2. Import to Notion via CSV import")
    print("   3. Link relations manually or via API")


if __name__ == "__main__":
    main()







