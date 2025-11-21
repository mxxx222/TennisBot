#!/usr/bin/env python3
"""
Google Snippet Tennis Results Scraper
=====================================

Parses results directly from Google search snippets - no website scraping needed!

Usage:
    python scripts/tennis_ai/google_snippet_scraper.py [auto|manual|hybrid]
"""

import re
import time
import csv
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import snippet parser
from scripts.tennis_ai.snippet_parser import parse_snippet, parse_snippet_with_fallback

# Try to import web scraping dependencies
try:
    import requests
    from bs4 import BeautifulSoup
    from fake_useragent import UserAgent
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  Note: requests/beautifulsoup4 not available - web scraping disabled")
    print("   Install: pip install requests beautifulsoup4 fake-useragent")

# Match data
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

MATCH_DATE = "17.9.2025"
OUTPUT_FILE = project_root / 'data' / 'results.csv'

# Rate limiting
REQUEST_DELAY = 2.0  # seconds between requests


def manual_google_search_instructions(player1: str, player2: str, match_date: str = None) -> str:
    """Generate Google search URL for manual lookup"""
    if match_date is None:
        match_date = MATCH_DATE
    
    # Get last names only for cleaner search
    p1_last = player1.split()[-1]
    p2_last = player2.split()[-1]
    
    query = f"{p1_last} {p2_last} {match_date} tennis result"
    # URL encode spaces as +
    from urllib.parse import quote_plus
    query_encoded = quote_plus(query)
    return f"https://www.google.com/search?q={query_encoded}"


def fetch_google_snippet(search_url: str, delay: float = REQUEST_DELAY) -> Optional[str]:
    """
    Fetch Google search results and extract snippet text.
    
    Args:
        search_url: Google search URL
        delay: Delay before request (rate limiting)
    
    Returns:
        Snippet text or None if failed
    """
    if not REQUESTS_AVAILABLE:
        return None
    
    try:
        # Rate limiting
        time.sleep(delay)
        
        # Use fake user agent to avoid bot detection
        ua = UserAgent()
        headers = {
            'User-Agent': ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # Fetch page
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try multiple selectors for Google snippet
        # Google uses various classes for snippets
        snippet_selectors = [
            '.VwiC3b',  # Common snippet class
            '.s',  # Another snippet class
            '.IsZvec',  # Alternative snippet class
            '[data-sncf="1"]',  # Snippet container
        ]
        
        snippet_text = None
        for selector in snippet_selectors:
            elements = soup.select(selector)
            if elements:
                # Get first snippet
                snippet_text = elements[0].get_text(strip=True)
                if snippet_text and len(snippet_text) > 20:  # Valid snippet
                    break
        
        # Fallback: look for any text containing numbers and player names
        if not snippet_text:
            # Search in all text content
            all_text = soup.get_text()
            # Look for patterns that might be scores
            if re.search(r'\d{1,2}[\s-]\d{1,2}', all_text):
                # Extract relevant portion
                lines = all_text.split('\n')
                for line in lines:
                    if re.search(r'\d{1,2}[\s-]\d{1,2}', line) and len(line) < 200:
                        snippet_text = line.strip()
                        break
        
        return snippet_text if snippet_text else None
        
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️  Request failed: {e}")
        return None
    except Exception as e:
        print(f"   ⚠️  Parsing failed: {e}")
        return None
    

def auto_search_match(player1: str, player2: str, match_date: str = None) -> Optional[Dict]:
    """
    Automatically search for match result via Google and parse snippet.
    
    Args:
        player1: First player name (Home)
        player2: Second player name (Away)
        match_date: Match date string
    
    Returns:
        Dict with winner, score, confidence, etc. or None if failed
    """
    if not REQUESTS_AVAILABLE:
        return None
    
    if match_date is None:
        match_date = MATCH_DATE
    
    # Generate search URL
    search_url = manual_google_search_instructions(player1, player2, match_date)
    
    # Fetch snippet
    snippet_text = fetch_google_snippet(search_url)
    
    if not snippet_text:
    return None
    
    # Parse snippet using the parser
    result = parse_snippet(snippet_text, player1, player2)
    
    return result


def main():
    import sys
    
    print("=" * 70)
    print("🔍 GOOGLE SNIPPET TENNIS RESULTS SCRAPER")
    print("=" * 70)
    print(f"📅 Date: {MATCH_DATE}")
    print(f"📊 Matches: {len(MATCHES)}")
    print()
    
    # Determine mode
    mode = "auto"
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    
    if mode not in ["auto", "manual", "hybrid"]:
        print("⚠️  Invalid mode. Use: auto, manual, or hybrid")
        print("   Defaulting to 'auto'")
        mode = "auto"
    
    print(f"⚡ Mode: {mode.upper()}")
    print("=" * 70)
    print()
    
    if mode == "auto":
        print("🤖 AUTO MODE: Attempting automatic result lookup...")
        print("   (Note: Web search API not configured, showing Google links for manual check)")
        print()
    elif mode == "manual":
        print("👤 MANUAL MODE: You will enter results for each match")
        print()
    else:  # hybrid
        print("🤝 HYBRID MODE: Auto-attempt first, then manual if needed")
        print()
    
    results = []
    not_found = []
    
    for i, match in enumerate(MATCHES, 1):
        player1, player2 = match['Match'].split(' vs ')
        p1_last = player1.split()[-1]
        p2_last = player2.split()[-1]
        
        print(f"\n[{i}/21] {match['Match']}")
        print(f"   EventKey: {match['EventKey']}")
        
        result = None
        
        # Try auto mode first
        if mode in ["auto", "hybrid"]:
            if REQUESTS_AVAILABLE:
                print(f"   🔍 Searching Google...")
            result = auto_search_match(player1, player2)
                if result and result.get('winner'):
                    confidence = result.get('confidence', 0)
                    print(f"   ✅ Auto-found: {result['winner']} - {result['score']} (confidence: {confidence}%)")
            else:
                if mode == "auto":
                    # In auto mode, show Google link but mark as not found
                    search_url = manual_google_search_instructions(player1, player2)
                    print(f"   🔍 Google: {search_url}")
                    print(f"   ⚠️  Auto-search failed - check Google snippet manually")
                    not_found.append(match)
                else:
                    # In hybrid mode, fall through to manual input
                        search_url = manual_google_search_instructions(player1, player2)
                        print(f"   🔍 Google: {search_url}")
                        print(f"   ⚠️  Auto-search failed, falling back to manual input")
            else:
                # Web scraping not available
                if mode == "auto":
                    search_url = manual_google_search_instructions(player1, player2)
                    print(f"   🔍 Google: {search_url}")
                    print(f"   ⚠️  Web scraping not available - check Google snippet manually")
                    not_found.append(match)
                else:
                    # In hybrid mode, fall through to manual input
                    search_url = manual_google_search_instructions(player1, player2)
                    print(f"   🔍 Google: {search_url}")
                    print(f"   ⚠️  Web scraping not available, using manual input")
        
        # Manual input (manual mode or hybrid fallback)
        if not result and mode in ["manual", "hybrid"]:
            search_url = manual_google_search_instructions(player1, player2)
            print(f"   🔍 Google: {search_url}")
            print(f"   👉 Option 1: Copy snippet text and paste here")
            print(f"   👉 Option 2: Enter winner and score manually")
            print(f"      Winner: Home (if {p1_last} won) or Away (if {p2_last} won)")
            print(f"      Score: e.g., '6-4 6-3' or '7-5 6-1'")
            
            try:
                snippet_input = input(f"   Paste snippet text (or press Enter to enter manually): ").strip()
                
                if snippet_input:
                    # Try to parse the snippet
                    parsed = parse_snippet(snippet_input, player1, player2)
                    if parsed and parsed.get('winner'):
                        result = {
                            'winner': parsed['winner'],
                            'score': parsed['score'],
                            'confidence': parsed.get('confidence', 0)
                        }
                        print(f"   ✅ Parsed from snippet: {result['winner']} - {result['score']}")
                    else:
                        print(f"   ⚠️  Could not parse snippet, enter manually:")
                        winner = input(f"   Winner (Home/Away): ").strip()
                        score = input(f"   Score: ").strip()
                        
                        if winner and score:
                            result = {
                                'winner': winner.capitalize(),
                                'score': score
                            }
                else:
                    # Manual entry
                winner = input(f"   Winner (Home/Away): ").strip()
                score = input(f"   Score: ").strip()
                
                if winner and score:
                    result = {
                        'winner': winner.capitalize(),
                        'score': score
                    }
            except (EOFError, KeyboardInterrupt):
                print(f"   ⏭️  Skipped (interrupted)")
                not_found.append(match)
                continue
        
        # Save result
        if result:
            results.append({
                'EventKey': match['EventKey'],
                'Winner': result['winner'],
                'Score': result['score']
            })
            print(f"   ✅ Recorded")
        else:
            if mode == "auto":
                # Already logged above
                pass
            else:
                print(f"   ⏭️  Skipped")
                not_found.append(match)
    
    # Save to CSV
    print()
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"✅ Found: {len(results)}/{len(MATCHES)}")
    print(f"❌ Not found: {len(not_found)}/{len(MATCHES)}")
    
    if results:
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for result in results:
                writer.writerow([
                    result['EventKey'],
                    result['Winner'],
                    result['Score']
                ])
        
        print()
        print(f"💾 Saved {len(results)} results to {OUTPUT_FILE}")
        
        if not_found and mode == "auto":
            print()
            print("⚠️  Matches not found automatically:")
            for match in not_found:
                print(f"   - EventKey {match['EventKey']}: {match['Match']}")
            print()
            print("💡 Run in 'hybrid' or 'manual' mode to fill missing results:")
            print("   python scripts/tennis_ai/google_snippet_scraper.py hybrid")
        
        print()
        print("Next steps:")
        print("1. python scripts/tennis_ai/validate_predictions.py")
        print("2. Check accuracy report")
    else:
        print("\n⚠️  No results recorded")
        print("💡 Try running in 'manual' or 'hybrid' mode")


if __name__ == '__main__':
    main()

