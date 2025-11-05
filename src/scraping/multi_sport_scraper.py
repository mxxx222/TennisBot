#!/usr/bin/env python3
"""
🏀 MULTI-SPORT DATA SCRAPER
==========================

Comprehensive scraping system for multiple sports
Maximizes data coverage across different sports and leagues

Supported Sports:
- Tennis (ATP, WTA, ITF)
- Football/Soccer (Premier League, La Liga, etc.)
- Basketball (NBA, EuroLeague)
- American Football (NFL)
- Baseball (MLB)
- Hockey (NHL)
- Golf (PGA Tour)
- Formula 1
- Cricket (ICC)
- Rugby

Author: Advanced Sports Analytics
Version: 3.0.0
"""

import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
import json
import re
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging
from urllib.parse import urljoin, urlparse, quote
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import numpy as np

@dataclass
class SportEvent:
    sport: str
    league: str
    event_id: str
    home_team: str
    away_team: str
    date: str
    status: str
    score: str
    odds: Dict[str, float]
    statistics: Dict
    weather: Dict
    venue: str

@dataclass
class PlayerProfile:
    sport: str
    name: str
    team: str
    position: str
    age: int
    nationality: str
    statistics: Dict
    market_value: float
    form: List[str]

@dataclass
class TeamProfile:
    sport: str
    name: str
    league: str
    founded: int
    stadium: str
    manager: str
    players: List[str]
    statistics: Dict
    form: List[str]

class MultiSportScraper:
    """Advanced multi-sport data scraper"""
    
    def __init__(self):
        self.setup_session()
        self.setup_logging()
        self.setup_sport_sources()
        
    def setup_session(self):
        """Setup HTTP session with rotation"""
        self.session = requests.Session()
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('multi_sport_scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_sport_sources(self):
        """Setup sport-specific data sources"""
        self.sport_sources = {
            'tennis': {
                'atp': 'https://www.atptour.com',
                'wta': 'https://www.wtatennis.com',
                'flashscore': 'https://www.flashscore.com/tennis',
                'tennisexplorer': 'https://www.tennisexplorer.com'
            },
            'football': {
                'espn': 'https://www.espn.com/soccer',
                'bbc': 'https://www.bbc.com/sport/football',
                'transfermarkt': 'https://www.transfermarkt.com',
                'flashscore': 'https://www.flashscore.com/football',
                'whoscored': 'https://www.whoscored.com'
            },
            'basketball': {
                'espn': 'https://www.espn.com/nba',
                'nba': 'https://www.nba.com',
                'euroleague': 'https://www.euroleague.net',
                'flashscore': 'https://www.flashscore.com/basketball'
            },
            'american_football': {
                'espn': 'https://www.espn.com/nfl',
                'nfl': 'https://www.nfl.com',
                'pro_football_reference': 'https://www.pro-football-reference.com'
            },
            'baseball': {
                'espn': 'https://www.espn.com/mlb',
                'mlb': 'https://www.mlb.com',
                'baseball_reference': 'https://www.baseball-reference.com'
            },
            'hockey': {
                'espn': 'https://www.espn.com/nhl',
                'nhl': 'https://www.nhl.com',
                'hockey_reference': 'https://www.hockey-reference.com'
            },
            'golf': {
                'pga': 'https://www.pgatour.com',
                'espn': 'https://www.espn.com/golf',
                'golfdigest': 'https://www.golfdigest.com'
            },
            'formula1': {
                'f1': 'https://www.formula1.com',
                'espn': 'https://www.espn.com/f1',
                'autosport': 'https://www.autosport.com'
            },
            'cricket': {
                'espn': 'https://www.espncricinfo.com',
                'icc': 'https://www.icc-cricket.com',
                'cricbuzz': 'https://www.cricbuzz.com'
            },
            'rugby': {
                'world_rugby': 'https://www.world.rugby',
                'espn': 'https://www.espn.com/rugby',
                'bbc': 'https://www.bbc.com/sport/rugby-union'
            }
        }
        
        # Betting odds sources
        self.betting_sources = {
            'odds_api': 'https://api.the-odds-api.com/v4/sports',
            'oddsportal': 'https://www.oddsportal.com',
            'bet365': 'https://www.bet365.com',
            'pinnacle': 'https://www.pinnacle.com',
            'betfair': 'https://www.betfair.com'
        }
    
    # TENNIS SCRAPING
    async def scrape_tennis_comprehensive(self) -> Dict:
        """Comprehensive tennis data scraping"""
        tennis_data = {
            'atp_rankings': await self.scrape_atp_rankings(),
            'wta_rankings': await self.scrape_wta_rankings(),
            'live_matches': await self.scrape_tennis_live_matches(),
            'upcoming_tournaments': await self.scrape_upcoming_tournaments(),
            'player_head_to_head': await self.scrape_h2h_records(),
            'injury_reports': await self.scrape_tennis_injuries()
        }
        return tennis_data
    
    async def scrape_atp_rankings(self) -> List[Dict]:
        """Scrape ATP rankings with detailed stats"""
        url = f"{self.sport_sources['tennis']['atp']}/en/rankings/singles"
        
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            players = []
            ranking_table = soup.find('table', class_='mega-table')
            
            if ranking_table:
                rows = ranking_table.find_all('tr')[1:]  # Skip header
                
                for i, row in enumerate(rows[:50], 1):  # Top 50
                    try:
                        cells = row.find_all('td')
                        if len(cells) >= 4:
                            player_data = {
                                'rank': i,
                                'name': cells[1].get_text(strip=True),
                                'country': self._extract_country_from_cell(cells[1]),
                                'points': self._extract_points(cells[2]),
                                'tournaments_played': self._extract_tournaments(cells[3]),
                                'prize_money': await self._get_player_prize_money(cells[1].get_text(strip=True))
                            }
                            players.append(player_data)
                    except Exception as e:
                        self.logger.error(f"Error processing ATP player {i}: {e}")
                        continue
            
            self.logger.info(f"Scraped {len(players)} ATP players")
            return players
            
        except Exception as e:
            self.logger.error(f"Error scraping ATP rankings: {e}")
            return []
    
    async def scrape_wta_rankings(self) -> List[Dict]:
        """Scrape WTA rankings"""
        url = f"{self.sport_sources['tennis']['wta']}/rankings/singles"
        
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            players = []
            ranking_rows = soup.find_all('tr', class_='ranking-row')
            
            for i, row in enumerate(ranking_rows[:50], 1):
                try:
                    player_name = row.find('span', class_='player-name')
                    points_elem = row.find('span', class_='ranking-points')
                    
                    if player_name and points_elem:
                        player_data = {
                            'rank': i,
                            'name': player_name.get_text(strip=True),
                            'points': int(points_elem.get_text(strip=True).replace(',', '')),
                            'country': self._extract_wta_country(row)
                        }
                        players.append(player_data)
                except Exception as e:
                    self.logger.error(f"Error processing WTA player {i}: {e}")
                    continue
            
            return players
            
        except Exception as e:
            self.logger.error(f"Error scraping WTA rankings: {e}")
            return []
    
    # FOOTBALL SCRAPING
    async def scrape_football_comprehensive(self) -> Dict:
        """Comprehensive football data scraping"""
        football_data = {
            'premier_league': await self.scrape_premier_league(),
            'la_liga': await self.scrape_la_liga(),
            'champions_league': await self.scrape_champions_league(),
            'live_matches': await self.scrape_football_live(),
            'transfer_news': await self.scrape_transfer_market(),
            'player_stats': await self.scrape_player_statistics()
        }
        return football_data
    
    async def scrape_premier_league(self) -> Dict:
        """Scrape Premier League data"""
        url = f"{self.sport_sources['football']['bbc']}/premier-league/table"
        
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract league table
            table = soup.find('table', class_='league-table')
            teams = []
            
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 10:
                        team_data = {
                            'position': cells[0].get_text(strip=True),
                            'team': cells[1].get_text(strip=True),
                            'played': int(cells[2].get_text(strip=True)),
                            'won': int(cells[3].get_text(strip=True)),
                            'drawn': int(cells[4].get_text(strip=True)),
                            'lost': int(cells[5].get_text(strip=True)),
                            'goals_for': int(cells[6].get_text(strip=True)),
                            'goals_against': int(cells[7].get_text(strip=True)),
                            'goal_difference': int(cells[8].get_text(strip=True)),
                            'points': int(cells[9].get_text(strip=True))
                        }
                        teams.append(team_data)
            
            return {
                'league': 'Premier League',
                'season': '2024-25',
                'table': teams,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error scraping Premier League: {e}")
            return {}
    
    # BASKETBALL SCRAPING
    async def scrape_basketball_comprehensive(self) -> Dict:
        """Comprehensive basketball data scraping"""
        basketball_data = {
            'nba_standings': await self.scrape_nba_standings(),
            'nba_stats': await self.scrape_nba_player_stats(),
            'euroleague': await self.scrape_euroleague(),
            'live_scores': await self.scrape_basketball_live()
        }
        return basketball_data
    
    async def scrape_nba_standings(self) -> Dict:
        """Scrape NBA standings"""
        url = f"{self.sport_sources['basketball']['espn']}/standings"
        
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract standings data
            standings_table = soup.find('table', class_='standings')
            teams = []
            
            if standings_table:
                rows = standings_table.find_all('tr')[1:]
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 8:
                        team_data = {
                            'team': cells[0].get_text(strip=True),
                            'wins': int(cells[1].get_text(strip=True)),
                            'losses': int(cells[2].get_text(strip=True)),
                            'win_percentage': float(cells[3].get_text(strip=True)),
                            'games_behind': cells[4].get_text(strip=True),
                            'home_record': cells[5].get_text(strip=True),
                            'away_record': cells[6].get_text(strip=True),
                            'conference': cells[7].get_text(strip=True)
                        }
                        teams.append(team_data)
            
            return {
                'league': 'NBA',
                'season': '2024-25',
                'standings': teams,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error scraping NBA standings: {e}")
            return {}
    
    # LIVE SCORES SCRAPING
    async def scrape_live_scores_all_sports(self) -> Dict:
        """Scrape live scores across all sports"""
        live_data = {}
        
        sports = ['tennis', 'football', 'basketball', 'american_football', 'baseball', 'hockey']
        
        for sport in sports:
            try:
                live_data[sport] = await self._scrape_sport_live_scores(sport)
                await asyncio.sleep(1)  # Rate limiting
            except Exception as e:
                self.logger.error(f"Error scraping live scores for {sport}: {e}")
                live_data[sport] = []
        
        return live_data
    
    async def _scrape_sport_live_scores(self, sport: str) -> List[Dict]:
        """Scrape live scores for specific sport"""
        if sport not in self.sport_sources:
            return []
        
        # Use Flashscore as primary source for live scores
        flashscore_url = f"https://www.flashscore.com/{sport}"
        
        try:
            # Setup Selenium for dynamic content
            driver = self._setup_selenium_driver()
            driver.get(flashscore_url)
            
            # Wait for content to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "event"))
            )
            
            live_matches = []
            match_elements = driver.find_elements(By.CLASS_NAME, "event")[:20]
            
            for element in match_elements:
                try:
                    match_data = self._extract_flashscore_match_data(element, sport)
                    if match_data:
                        live_matches.append(match_data)
                except Exception as e:
                    continue
            
            driver.quit()
            return live_matches
            
        except Exception as e:
            self.logger.error(f"Error scraping live scores for {sport}: {e}")
            return []
    
    def _setup_selenium_driver(self):
        """Setup Selenium driver with options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(f"--user-agent={random.choice(self.user_agents)}")
        
        return webdriver.Chrome(options=chrome_options)
    
    def _extract_flashscore_match_data(self, element, sport: str) -> Dict:
        """Extract match data from Flashscore element"""
        try:
            home_team = element.find_element(By.CLASS_NAME, "participant--home").text
            away_team = element.find_element(By.CLASS_NAME, "participant--away").text
            score = element.find_element(By.CLASS_NAME, "score").text
            status = element.find_element(By.CLASS_NAME, "status").text
            
            return {
                'sport': sport,
                'home_team': home_team,
                'away_team': away_team,
                'score': score,
                'status': status,
                'timestamp': datetime.now().isoformat()
            }
        except:
            return None
    
    # BETTING ODDS SCRAPING
    async def scrape_comprehensive_odds(self) -> Dict:
        """Scrape betting odds from multiple sources"""
        odds_data = {}
        
        try:
            # Scrape from multiple betting sites
            odds_data['oddsportal'] = await self._scrape_oddsportal_odds()
            odds_data['pinnacle'] = await self._scrape_pinnacle_odds()
            # Add more betting sources
            
        except Exception as e:
            self.logger.error(f"Error scraping betting odds: {e}")
        
        return odds_data
    
    async def _scrape_oddsportal_odds(self) -> Dict:
        """Scrape odds from OddsPortal"""
        base_url = self.betting_sources['oddsportal']
        sports_odds = {}
        
        sports = ['tennis', 'football', 'basketball']
        
        for sport in sports:
            try:
                url = f"{base_url}/{sport}"
                response = self.session.get(url)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                odds_tables = soup.find_all('table', class_='table-main')
                sport_odds = []
                
                for table in odds_tables:
                    rows = table.find_all('tr')[1:]  # Skip header
                    
                    for row in rows:
                        odds_data = self._extract_odds_row(row)
                        if odds_data:
                            sport_odds.append(odds_data)
                
                sports_odds[sport] = sport_odds
                await asyncio.sleep(2)  # Rate limiting
                
            except Exception as e:
                self.logger.error(f"Error scraping {sport} odds: {e}")
                sports_odds[sport] = []
        
        return sports_odds
    
    def _extract_odds_row(self, row) -> Dict:
        """Extract odds data from table row"""
        try:
            cells = row.find_all('td')
            if len(cells) >= 4:
                return {
                    'match': cells[0].get_text(strip=True),
                    'home_odds': float(cells[1].get_text(strip=True)),
                    'draw_odds': float(cells[2].get_text(strip=True)) if cells[2].get_text(strip=True) != '-' else None,
                    'away_odds': float(cells[3].get_text(strip=True)),
                    'timestamp': datetime.now().isoformat()
                }
        except:
            return None
    
    # NEWS AND ANALYSIS SCRAPING
    async def scrape_sports_news(self) -> Dict:
        """Scrape sports news from multiple sources"""
        news_data = {}
        
        news_sources = {
            'espn': 'https://www.espn.com',
            'bbc_sport': 'https://www.bbc.com/sport',
            'sky_sports': 'https://www.skysports.com',
            'reuters_sports': 'https://www.reuters.com/sports'
        }
        
        for source_name, base_url in news_sources.items():
            try:
                news_data[source_name] = await self._scrape_source_news(base_url)
                await asyncio.sleep(1)
            except Exception as e:
                self.logger.error(f"Error scraping news from {source_name}: {e}")
                news_data[source_name] = []
        
        return news_data
    
    async def _scrape_source_news(self, base_url: str) -> List[Dict]:
        """Scrape news from specific source"""
        try:
            response = self.session.get(base_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract news articles
            article_elements = soup.find_all(['article', 'div'], class_=re.compile(r'.*article.*|.*news.*|.*story.*'))
            
            news_articles = []
            
            for element in article_elements[:20]:  # Limit to 20 articles
                try:
                    title_elem = element.find(['h1', 'h2', 'h3'], class_=re.compile(r'.*title.*|.*headline.*'))
                    link_elem = element.find('a')
                    
                    if title_elem and link_elem:
                        article_data = {
                            'title': title_elem.get_text(strip=True),
                            'url': urljoin(base_url, link_elem.get('href')),
                            'timestamp': datetime.now().isoformat(),
                            'source': urlparse(base_url).netloc
                        }
                        news_articles.append(article_data)
                except:
                    continue
            
            return news_articles
            
        except Exception as e:
            self.logger.error(f"Error scraping news from {base_url}: {e}")
            return []
    
    # INJURY AND TEAM NEWS SCRAPING
    async def scrape_injury_reports(self) -> Dict:
        """Scrape injury reports across sports"""
        injury_data = {}
        
        sports = ['tennis', 'football', 'basketball', 'american_football']
        
        for sport in sports:
            try:
                injury_data[sport] = await self._scrape_sport_injuries(sport)
            except Exception as e:
                self.logger.error(f"Error scraping injuries for {sport}: {e}")
                injury_data[sport] = []
        
        return injury_data
    
    async def _scrape_sport_injuries(self, sport: str) -> List[Dict]:
        """Scrape injury reports for specific sport"""
        # Mock injury data - in production, scrape from official sources
        injuries = [
            {
                'player': f"Player {i}",
                'team': f"Team {i%10}",
                'injury': random.choice(['Knee', 'Ankle', 'Shoulder', 'Back', 'Hamstring']),
                'status': random.choice(['Day-to-day', 'Week-to-week', 'Out indefinitely']),
                'expected_return': (datetime.now() + timedelta(days=random.randint(1, 30))).isoformat()
            }
            for i in range(5)
        ]
        
        return injuries
    
    # WEATHER DATA SCRAPING
    async def scrape_weather_data(self) -> Dict:
        """Scrape weather data for outdoor sports"""
        weather_data = {}
        
        # Major sporting cities
        cities = ['London', 'Paris', 'Madrid', 'Milan', 'Munich', 'Barcelona']
        
        for city in cities:
            try:
                weather_data[city] = await self._get_city_weather(city)
            except Exception as e:
                self.logger.error(f"Error getting weather for {city}: {e}")
                weather_data[city] = {}
        
        return weather_data
    
    async def _get_city_weather(self, city: str) -> Dict:
        """Get weather data for specific city"""
        # Mock weather data - in production, use weather API
        return {
            'city': city,
            'temperature': random.randint(-5, 35),
            'humidity': random.randint(30, 90),
            'wind_speed': random.randint(0, 30),
            'conditions': random.choice(['Sunny', 'Cloudy', 'Rainy', 'Snow', 'Partly Cloudy']),
            'precipitation': random.randint(0, 100),
            'timestamp': datetime.now().isoformat()
        }
    
    # DATA PROCESSING AND STORAGE
    def process_scraped_data(self, raw_data: Dict) -> Dict:
        """Process and clean scraped data"""
        processed_data = {
            'metadata': {
                'scraping_timestamp': datetime.now().isoformat(),
                'sources_count': len(raw_data),
                'total_records': sum(len(v) if isinstance(v, list) else 1 for v in raw_data.values())
            },
            'sports_data': raw_data
        }
        
        return processed_data
    
    def save_data_to_files(self, data: Dict, base_filename: str):
        """Save scraped data to multiple formats"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save as JSON
        json_filename = f"data/scraped/{base_filename}_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        # Save as CSV for each sport
        for sport, sport_data in data.get('sports_data', {}).items():
            if isinstance(sport_data, list) and sport_data:
                df = pd.DataFrame(sport_data)
                csv_filename = f"data/scraped/{sport}_{timestamp}.csv"
                df.to_csv(csv_filename, index=False)
        
        self.logger.info(f"Data saved to {json_filename} and CSV files")
    
    # MAIN SCRAPING ORCHESTRATOR
    async def run_comprehensive_sports_scraping(self) -> Dict:
        """Run comprehensive scraping across all sports"""
        self.logger.info("Starting comprehensive multi-sport data scraping...")
        
        all_data = {
            'scraping_start': datetime.now().isoformat(),
            'tennis': {},
            'football': {},
            'basketball': {},
            'live_scores': {},
            'betting_odds': {},
            'news': {},
            'injuries': {},
            'weather': {}
        }
        
        try:
            # Tennis data
            self.logger.info("Scraping tennis data...")
            all_data['tennis'] = await self.scrape_tennis_comprehensive()
            
            # Football data
            self.logger.info("Scraping football data...")
            all_data['football'] = await self.scrape_football_comprehensive()
            
            # Basketball data
            self.logger.info("Scraping basketball data...")
            all_data['basketball'] = await self.scrape_basketball_comprehensive()
            
            # Live scores across all sports
            self.logger.info("Scraping live scores...")
            all_data['live_scores'] = await self.scrape_live_scores_all_sports()
            
            # Betting odds
            self.logger.info("Scraping betting odds...")
            all_data['betting_odds'] = await self.scrape_comprehensive_odds()
            
            # Sports news
            self.logger.info("Scraping sports news...")
            all_data['news'] = await self.scrape_sports_news()
            
            # Injury reports
            self.logger.info("Scraping injury reports...")
            all_data['injuries'] = await self.scrape_injury_reports()
            
            # Weather data
            self.logger.info("Scraping weather data...")
            all_data['weather'] = await self.scrape_weather_data()
            
            all_data['scraping_end'] = datetime.now().isoformat()
            all_data['status'] = 'completed'
            
            # Process and save data
            processed_data = self.process_scraped_data(all_data)
            self.save_data_to_files(processed_data, 'comprehensive_sports_data')
            
            self.logger.info("Comprehensive sports scraping completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive scraping: {e}")
            all_data['status'] = 'error'
            all_data['error'] = str(e)
        
        return all_data

# Usage example
async def main():
    """Main function to run comprehensive sports scraping"""
    scraper = MultiSportScraper()
    
    print("🏈 COMPREHENSIVE MULTI-SPORT DATA SCRAPING")
    print("=" * 60)
    
    # Run comprehensive scraping
    data = await scraper.run_comprehensive_sports_scraping()
    
    print(f"\n📊 SCRAPING RESULTS:")
    print(f"Status: {data.get('status', 'unknown')}")
    print(f"Start time: {data.get('scraping_start')}")
    print(f"End time: {data.get('scraping_end')}")
    
    print(f"\n🎾 Tennis data sources: {len(data.get('tennis', {}))}")
    print(f"⚽ Football data sources: {len(data.get('football', {}))}")
    print(f"🏀 Basketball data sources: {len(data.get('basketball', {}))}")
    print(f"🔴 Live scores: {len(data.get('live_scores', {}))}")
    print(f"💰 Betting sources: {len(data.get('betting_odds', {}))}")
    print(f"📰 News sources: {len(data.get('news', {}))}")
    print(f"🏥 Injury reports: {len(data.get('injuries', {}))}")
    print(f"🌤️ Weather data: {len(data.get('weather', {}))}")
    
    return data

if __name__ == "__main__":
    asyncio.run(main())