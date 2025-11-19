#!/usr/bin/env python3
"""
🎾 Tennis Match Results Scraper
================================

Scrapes actual match results for tennis matches from September 17, 2025
using EventKey identifiers and outputs to CSV format.

Data Sources (priority order):
1. TennisExplorer.com (EventKey-based lookup)
2. FlashScore.com (player name + date search)
3. Tennis-Data.co.uk (historical data)
"""

import csv
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("❌ ERROR: requests and beautifulsoup4 required")
    print("   Install: pip install requests beautifulsoup4")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Match data - 21 matches from September 17, 2025
MATCHES = [
    {"EventKey": 12070966, "Match": "T. Seyboth Wild vs V. Kopriva", "Predicted": "Away"},
    {"EventKey": 12071014, "Match": "A. Molcan vs K. Coppejans", "Predicted": "Home"},
    {"EventKey": 12071066, "Match": "F. Bondioli vs A. Martin", "Predicted": "Away"},
    {"EventKey": 12071186, "Match": "N. D. Ionel vs D. Rincon", "Predicted": "Away"},
    {"EventKey": 12071190, "Match": "M. Mrva vs M. Erhard", "Predicted": "Home"},
    {"EventKey": 12071266, "Match": "S. Rokusek vs A. Smith", "Predicted": "Home"},
    {"EventKey": 12071267, "Match": "H. Sato vs N. McKenzie", "Predicted": "Away"},
    {"EventKey": 12071344, "Match": "D. Sumizawa vs J. Brumm", "Predicted": "Home"},
    {"EventKey": 12071345, "Match": "R. Taguchi vs S. Shin", "Predicted": "Away"},
    {"EventKey": 12071349, "Match": "J. Lu vs K. Pavlova", "Predicted": "Home"},
    {"EventKey": 12071360, "Match": "M. Dodig vs Z. Kolar", "Predicted": "Away"},
    {"EventKey": 12071361, "Match": "P. Martinez vs M. Topo", "Predicted": "Home"},
    {"EventKey": 12071364, "Match": "D. Novak vs R. Carballes Baena", "Predicted": "Away"},
    {"EventKey": 12071366, "Match": "C. Stebe vs J. J. Schwaerzler", "Predicted": "Away"},
    {"EventKey": 12071482, "Match": "R. Peniston vs L. Maxted", "Predicted": "Home"},
    {"EventKey": 12071495, "Match": "G. Pedone vs A. Prisacariu", "Predicted": "Home"},
    {"EventKey": 12071499, "Match": "K. Deichmann vs G. Ce", "Predicted": "Home"},
    {"EventKey": 12071542, "Match": "H. Wendelken vs Y. Ghazouani Durand", "Predicted": "Home"},
    {"EventKey": 12071557, "Match": "N. Kicker vs H. Casanova", "Predicted": "Home"},
    {"EventKey": 12071723, "Match": "C. Sinclair vs Je. Delaney", "Predicted": "Home"},
    {"EventKey": 12071729, "Match": "O. Anderson vs P. Brown", "Predicted": "Home"},
]

# Output file
OUTPUT_FILE = project_root / 'data' / 'results.csv'
MATCH_DATE = "2025-09-17"


class TennisResultsScraper:
    """Scraper for tennis match results from multiple sources"""
    
    def __init__(self, request_delay: float = 2.0):
        """
        Initialize scraper
        
        Args:
            request_delay: Delay between requests in seconds
        """
        self.request_delay = request_delay
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        self.results = []
    
    def _rate_limit(self):
        """Apply rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        self.last_request_time = time.time()
    
    def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch page with rate limiting
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None
        """
        self._rate_limit()
        
        try:
            logger.debug(f"🌐 Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            logger.error(f"❌ Error fetching {url}: {e}")
            return None
    
    def _parse_player_names(self, match_string: str) -> Tuple[str, str]:
        """
        Parse player names from match string
        
        Args:
            match_string: "Player A vs Player B"
            
        Returns:
            Tuple of (player1, player2)
        """
        if " vs " in match_string:
            parts = match_string.split(" vs ", 1)
            return parts[0].strip(), parts[1].strip()
        return "", ""
    
    def scrape_tennisexplorer(self, event_key: int, match_string: str) -> Optional[Dict]:
        """
        Try to scrape from TennisExplorer using EventKey
        
        Args:
            event_key: EventKey identifier
            match_string: Match string for logging
            
        Returns:
            Dict with 'winner' and 'score' or None
        """
        # Note: EventKey might be from api-tennis.com, not TennisExplorer
        # Try TennisExplorer match detail page format
        url = f"https://www.tennisexplorer.com/match-detail/?id={event_key}"
        
        logger.info(f"🔍 Trying TennisExplorer for EventKey {event_key}: {match_string}")
        soup = self._get_page(url)
        
        if not soup:
            return None
        
        # Look for match result indicators
        # TennisExplorer typically shows results in specific divs
        result_divs = soup.find_all(['div', 'span'], class_=re.compile(r'result|score|winner', re.I))
        
        # Try to find score patterns
        score_pattern = re.compile(r'(\d+)[-\s]+(\d+)')
        winner = None
        score = None
        
        # Look for final score
        for div in result_divs:
            text = div.get_text(strip=True)
            if score_pattern.search(text):
                # Found score-like text
                score_match = score_pattern.findall(text)
                if score_match:
                    # Format as "6-4 6-3" or "2-1"
                    if len(score_match) >= 2:
                        score = " ".join([f"{s[0]}-{s[1]}" for s in score_match[:2]])
                    else:
                        score = f"{score_match[0][0]}-{score_match[0][1]}"
        
        # Try to determine winner from page structure
        # This is a simplified approach - may need adjustment based on actual page structure
        if score:
            # For now, return None and try other sources
            # TennisExplorer structure varies, so we'll try FlashScore instead
            logger.debug(f"   Found score-like data but structure unclear")
        
        return None
    
    def scrape_flashscore(self, event_key: int, match_string: str) -> Optional[Dict]:
        """
        Try to scrape from FlashScore using player names and date
        
        Args:
            event_key: EventKey identifier
            match_string: Match string with player names
            
        Returns:
            Dict with 'winner' and 'score' or None
        """
        player1, player2 = self._parse_player_names(match_string)
        
        if not player1 or not player2:
            logger.warning(f"   Could not parse player names from: {match_string}")
            return None
        
        logger.info(f"🔍 Trying FlashScore for EventKey {event_key}: {player1} vs {player2}")
        
        # FlashScore search approach
        # Try to find match via search or results page
        # Note: FlashScore uses JavaScript heavily, so direct scraping is limited
        
        # Try results page for the date
        # Format: https://www.flashscore.com/tennis/results/?date=2025-09-17
        date_url = f"https://www.flashscore.com/tennis/results/?date={MATCH_DATE.replace('-', '')}"
        
        soup = self._get_page(date_url)
        if not soup:
            return None
        
        # FlashScore loads content via JavaScript, so static HTML may not have results
        # Look for player names in the page
        page_text = soup.get_text()
        
        # Check if both players appear on the page
        player1_found = player1.split()[-1].lower() in page_text.lower()
        player2_found = player2.split()[-1].lower() in page_text.lower()
        
        if player1_found and player2_found:
            logger.debug(f"   Found both players on FlashScore results page")
            # Would need Selenium for full extraction, but try basic parsing
            # For now, return None and log
            logger.warning(f"   FlashScore requires JavaScript - consider using Selenium")
        
        return None
    
    def scrape_api_tennis(self, event_key: int, match_string: str) -> Optional[Dict]:
        """
        Try to get result from api-tennis.com (if EventKey is from this API)
        
        Args:
            event_key: EventKey identifier
            match_string: Match string for logging
            
        Returns:
            Dict with 'winner' and 'score' or None
        """
        # Check if we have API key (optional)
        import os
        api_key = os.getenv('TENNIS_API_KEY') or os.getenv('API_TENNIS_KEY')
        
        if not api_key:
            logger.debug(f"   No API key for api-tennis.com, skipping")
            return None
        
        logger.info(f"🔍 Trying api-tennis.com for EventKey {event_key}")
        
        # Try to get fixture for specific event_key
        # Method 1: Get fixtures for the date and filter by event_key
        url = f"https://api.api-tennis.com/tennis/?method=get_fixtures&APIkey={api_key}&date_start={MATCH_DATE}&date_stop={MATCH_DATE}"
        
        try:
            self._rate_limit()
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get('success') == 1 and data.get('result'):
                # Find match with matching event_key
                for fixture in data['result']:
                    if fixture.get('event_key') == event_key:
                        # Found the match!
                        final_result = fixture.get('event_final_result', '')
                        game_result = fixture.get('event_game_result', '')
                        status = fixture.get('event_status', '')
                        
                        # Check if match is finished
                        if status and 'finished' in status.lower():
                            # Parse result
                            # event_final_result format: "2-1" or "2-0" (sets)
                            # event_game_result format: "6-4 6-3" or similar (detailed score)
                            
                            score = game_result if game_result else final_result
                            if not score:
                                score = "2-0"  # Default if no score available
                            
                            # Determine winner from fixture data
                            # event_final_result format: "2-1" or "2-0" (sets won by first player - sets won by second player)
                            # If format is "2-1", first player (Home) won 2 sets, second player (Away) won 1 set
                            winner = None
                            
                            # Try to parse winner from final_result
                            # Format: "2-1" means first player won (Home)
                            if final_result:
                                try:
                                    # Remove any whitespace and split by dash
                                    result_clean = final_result.strip()
                                    if '-' in result_clean:
                                        sets = result_clean.split('-')
                                        if len(sets) == 2:
                                            sets_first = int(sets[0].strip())
                                            sets_second = int(sets[1].strip())
                                            if sets_first > sets_second:
                                                winner = "Home"
                                            elif sets_second > sets_first:
                                                winner = "Away"
                                except (ValueError, IndexError, AttributeError):
                                    logger.debug(f"   Could not parse final_result: {final_result}")
                            
                            # If still no winner, try to infer from game_result
                            # Format: "6-4 6-3" means first player won both sets
                            if not winner and game_result:
                                try:
                                    # Count sets won by looking at game_result
                                    # Each "X-Y" represents a set
                                    sets = game_result.strip().split()
                                    sets_won_first = 0
                                    sets_won_second = 0
                                    
                                    for set_score in sets:
                                        if '-' in set_score:
                                            games = set_score.split('-')
                                            if len(games) == 2:
                                                try:
                                                    games_first = int(games[0])
                                                    games_second = int(games[1])
                                                    if games_first > games_second:
                                                        sets_won_first += 1
                                                    elif games_second > games_first:
                                                        sets_won_second += 1
                                                except ValueError:
                                                    pass
                                    
                                    if sets_won_first > sets_won_second:
                                        winner = "Home"
                                    elif sets_won_second > sets_won_first:
                                        winner = "Away"
                                except (IndexError, ValueError, AttributeError):
                                    logger.debug(f"   Could not parse game_result: {game_result}")
                            
                            # If we have a score, return result (even if winner is unknown, user can check manually)
                            if score:
                                if winner:
                                    return {
                                        'winner': winner,
                                        'score': score
                                    }
                                else:
                                    logger.warning(f"   Found match with score '{score}' but couldn't determine winner")
                                    logger.warning(f"   final_result: '{final_result}', game_result: '{game_result}'")
                                    # Return with placeholder - user will need to check manually
                                    return {
                                        'winner': "CHECK_MANUAL",  # Flag for manual check needed
                                        'score': score
                                    }
            
            logger.debug(f"   Match not found in API response for date {MATCH_DATE}")
            return None
            
        except Exception as e:
            logger.error(f"   Error calling api-tennis.com API: {e}")
            return None
    
    def scrape_match(self, event_key: int, match_string: str) -> Optional[Dict]:
        """
        Scrape match result from multiple sources with fallback
        
        Args:
            event_key: EventKey identifier
            match_string: Match string
            
        Returns:
            Dict with 'winner' ('Home' or 'Away') and 'score', or None
        """
        # Try sources in priority order
        result = None
        
        # 1. Try api-tennis.com first (EventKey likely from this API)
        result = self.scrape_api_tennis(event_key, match_string)
        if result:
            return result
        
        # 2. Try TennisExplorer
        result = self.scrape_tennisexplorer(event_key, match_string)
        if result:
            return result
        
        # 3. Try FlashScore
        result = self.scrape_flashscore(event_key, match_string)
        if result:
            return result
        
        logger.warning(f"❌ Could not find result for EventKey {event_key}: {match_string}")
        return None
    
    def determine_winner(self, match_string: str, winner_name: str) -> Optional[str]:
        """
        Determine if winner is Home or Away based on player name
        
        Args:
            match_string: "Player A vs Player B"
            winner_name: Name of the winning player
            
        Returns:
            "Home" or "Away" or None
        """
        player1, player2 = self._parse_player_names(match_string)
        
        if not player1 or not player2:
            return None
        
        # Normalize names for comparison (use last name)
        winner_last = winner_name.split()[-1].lower() if winner_name else ""
        player1_last = player1.split()[-1].lower()
        player2_last = player2.split()[-1].lower()
        
        if winner_last == player1_last:
            return "Home"
        elif winner_last == player2_last:
            return "Away"
        
        # Try full name match
        if winner_name.lower() in player1.lower():
            return "Home"
        elif winner_name.lower() in player2.lower():
            return "Away"
        
        return None
    
    def run(self) -> List[Dict]:
        """
        Run scraper for all matches
        
        Returns:
            List of result dicts with EventKey, Winner, Score
        """
        logger.info("=" * 70)
        logger.info("🎾 TENNIS MATCH RESULTS SCRAPER")
        logger.info("=" * 70)
        logger.info(f"📅 Date: {MATCH_DATE}")
        logger.info(f"📊 Matches to scrape: {len(MATCHES)}")
        logger.info("")
        
        results = []
        found_count = 0
        not_found = []
        
        for i, match in enumerate(MATCHES, 1):
            event_key = match['EventKey']
            match_string = match['Match']
            
            logger.info(f"[{i}/{len(MATCHES)}] Processing EventKey {event_key}: {match_string}")
            
            result = self.scrape_match(event_key, match_string)
            
            if result:
                results.append({
                    'EventKey': event_key,
                    'Winner': result['winner'],
                    'Score': result['score']
                })
                found_count += 1
                logger.info(f"   ✅ Found: {result['winner']} - {result['score']}")
            else:
                not_found.append({'EventKey': event_key, 'Match': match_string})
                logger.warning(f"   ❌ Not found")
            
            logger.info("")
        
        logger.info("=" * 70)
        logger.info(f"📊 SCRAPING SUMMARY")
        logger.info("=" * 70)
        logger.info(f"✅ Found: {found_count}/{len(MATCHES)}")
        logger.info(f"❌ Not found: {len(not_found)}/{len(MATCHES)}")
        
        if not_found:
            logger.info("\n⚠️  Matches not found:")
            for match in not_found:
                logger.info(f"   - EventKey {match['EventKey']}: {match['Match']}")
        
        return results
    
    def save_to_csv(self, results: List[Dict], output_file: Path):
        """
        Save results to CSV file (no headers, comma-separated)
        
        Args:
            results: List of result dicts
            output_file: Path to output CSV file
        """
        # Ensure data directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Validate unique EventKeys
        event_keys = [r['EventKey'] for r in results]
        if len(event_keys) != len(set(event_keys)):
            logger.warning("⚠️  Duplicate EventKeys found in results!")
        
        # Filter out results that need manual checking (or include them with note)
        valid_results = []
        manual_check_needed = []
        
        for result in results:
            if result['Winner'] == "CHECK_MANUAL":
                manual_check_needed.append(result)
                logger.warning(f"   ⚠️  EventKey {result['EventKey']} needs manual winner check (score: {result['Score']})")
            else:
                valid_results.append(result)
        
        # Write CSV without headers
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for result in valid_results:
                    writer.writerow([
                        result['EventKey'],
                        result['Winner'],
                        result['Score']
                    ])
            
            logger.info(f"\n💾 Results saved to: {output_file}")
            logger.info(f"   ✅ Valid results: {len(valid_results)}")
            if manual_check_needed:
                logger.info(f"   ⚠️  Manual check needed: {len(manual_check_needed)}")
                logger.info(f"   💡 Check these matches manually and add to CSV:")
                for result in manual_check_needed:
                    logger.info(f"      EventKey {result['EventKey']}: Score={result['Score']}")
        except Exception as e:
            logger.error(f"❌ Error saving CSV: {e}")
            raise


def main():
    """Main function"""
    scraper = TennisResultsScraper(request_delay=2.0)
    
    try:
        results = scraper.run()
        
        if results:
            scraper.save_to_csv(results, OUTPUT_FILE)
            logger.info("\n✅ Scraping completed successfully!")
            logger.info(f"\n📝 Next steps:")
            logger.info(f"   1. Review the CSV file: {OUTPUT_FILE}")
            logger.info(f"   2. If any matches need manual checking, update the CSV")
            logger.info(f"   3. Run validation: python scripts/tennis_ai/validate_predictions.py")
        else:
            logger.warning("\n⚠️  No results found. CSV file not created.")
            logger.info("\n💡 Suggestions:")
            logger.info("   1. Set TENNIS_API_KEY environment variable for api-tennis.com access")
            logger.info("      export TENNIS_API_KEY=your_api_key")
            logger.info("   2. Check if matches are from the correct date (2025-09-17)")
            logger.info("   3. Verify EventKey format (EventKeys are from api-tennis.com)")
            logger.info("   4. For manual scraping:")
            logger.info("      - FlashScore: https://www.flashscore.com/tennis/results/?date=20250917")
            logger.info("      - TennisExplorer: Search by player names and date")
            logger.info("   5. Consider using Selenium for JavaScript-heavy sites")
    
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

