#!/usr/bin/env python3
"""
Football OU2.5 Pre-Filter
Filters best AI analysis candidates for Over/Under 2.5 goals betting
Cost: €0 (no API calls)
"""

import os
import sys
from pathlib import Path
from notion_client import Client
from datetime import datetime
import json
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / 'telegram_secrets.env'
if env_path.exists():
    load_dotenv(env_path)

# CONFIG
NOTION_TOKEN = os.getenv('NOTION_API_KEY') or os.getenv('NOTION_TOKEN')
# TODO: Set your Football Prematch database ID
FOOTBALL_PREMATCH_DB_ID = os.getenv('NOTION_FOOTBALL_PREMATCH_DB_ID') or ""
MIN_SCORE = 50  # Cut-off points for filtering

if not NOTION_TOKEN:
    print("❌ ERROR: NOTION_API_KEY or NOTION_TOKEN not set")
    print("   Set it in telegram_secrets.env")
    exit(1)

if not FOOTBALL_PREMATCH_DB_ID:
    print("⚠️  WARNING: NOTION_FOOTBALL_PREMATCH_DB_ID not set")
    print("   Set it in telegram_secrets.env or update FOOTBALL_PREMATCH_DB_ID in this file")
    print("   For now, using mock data mode")

notion = Client(auth=NOTION_TOKEN) if NOTION_TOKEN else None

def get_football_matches():
    """Get all upcoming football matches from Notion"""
    if not FOOTBALL_PREMATCH_DB_ID or not notion:
        return []
    
    try:
        response = notion.databases.query(
            database_id=FOOTBALL_PREMATCH_DB_ID,
            filter={
                "property": "Match Status",
                "select": {"equals": "Upcoming"}
            },
            sorts=[{"property": "Date", "direction": "ascending"}]
        )
        return response['results']
    except Exception as e:
        print(f"⚠️  Error querying Notion: {e}")
        return []

def extract_match_data(page):
    """Extract match data from Notion page"""
    props = page['properties']
    
    def safe_get(prop_name, prop_type):
        try:
            if prop_type == 'text':
                rich_text = props.get(prop_name, {}).get('rich_text', [])
                return rich_text[0]['plain_text'] if rich_text else None
            elif prop_type == 'title':
                title = props.get(prop_name, {}).get('title', [])
                return title[0]['plain_text'] if title else None
            elif prop_type == 'select':
                select = props.get(prop_name, {}).get('select', {})
                return select.get('name') if select else None
            elif prop_type == 'number':
                return props.get(prop_name, {}).get('number')
            elif prop_type == 'date':
                date_obj = props.get(prop_name, {}).get('date', {})
                return date_obj.get('start') if date_obj else None
        except (KeyError, IndexError, TypeError):
            return None
    
    return {
        'page_id': page['id'],
        'page_url': page.get('url', ''),
        'home_team': safe_get('Home Team', 'title') or safe_get('Home Team', 'text') or 'Unknown',
        'away_team': safe_get('Away Team', 'title') or safe_get('Away Team', 'text') or 'Unknown',
        'league': safe_get('League', 'text') or safe_get('League', 'select') or 'Unknown',
        'home_goals_avg': safe_get('Home Goals Avg', 'number'),
        'away_goals_avg': safe_get('Away Goals Avg', 'number'),
        'home_conceded_avg': safe_get('Home Conceded Avg', 'number'),
        'away_conceded_avg': safe_get('Away Conceded Avg', 'number'),
        'home_form': safe_get('Home Form', 'text'),
        'away_form': safe_get('Away Form', 'text'),
        'status': safe_get('Match Status', 'select') or 'Unknown',
        'date': safe_get('Date', 'date')
    }

def calculate_score(match):
    """Calculate match score (0-100) for OU2.5 betting"""
    score = 0
    factors = []
    
    # 1. Goals Average (30p) - Key indicator for OU2.5
    home_goals = match.get('home_goals_avg', 0) or 0
    away_goals = match.get('away_goals_avg', 0) or 0
    total_avg_goals = home_goals + away_goals
    
    if total_avg_goals >= 2.8:
        score += 30
        factors.append(f"✅ High goal average: {total_avg_goals:.1f} goals/match")
    elif total_avg_goals >= 2.3:
        score += 20
        factors.append(f"✅ Good goal average: {total_avg_goals:.1f} goals/match")
    elif total_avg_goals >= 1.8:
        score += 10
        factors.append(f"⚠️ Moderate goal average: {total_avg_goals:.1f} goals/match")
    else:
        score += 5
        factors.append(f"⚠️ Low goal average: {total_avg_goals:.1f} goals/match")
    
    # 2. Defensive Stats (25p) - Weak defenses = more goals
    home_conceded = match.get('home_conceded_avg', 0) or 0
    away_conceded = match.get('away_conceded_avg', 0) or 0
    total_conceded = home_conceded + away_conceded
    
    if total_conceded >= 2.5:
        score += 25
        factors.append(f"✅ Weak defenses: {total_conceded:.1f} goals conceded/match")
    elif total_conceded >= 2.0:
        score += 15
        factors.append(f"✅ Moderate defenses: {total_conceded:.1f} goals conceded/match")
    elif total_conceded > 0:
        score += 5
        factors.append(f"⚠️ Strong defenses: {total_conceded:.1f} goals conceded/match")
    else:
        score += 10
        factors.append("➖ Defensive stats not available")
    
    # 3. League Quality (20p) - Top leagues have better data
    league = match.get('league', 'Unknown')
    top_leagues = ['Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1', 
                   'Champions League', 'Europa League']
    
    if any(top_league.lower() in league.lower() for top_league in top_leagues):
        score += 20
        factors.append(f"✅ Top league: {league}")
    elif league != 'Unknown':
        score += 10
        factors.append(f"✅ League: {league}")
    else:
        score += 5
        factors.append("⚠️ League unknown")
    
    # 4. Form Data (15p) - Recent form indicates current performance
    home_form = match.get('home_form', '')
    away_form = match.get('away_form', '')
    
    if home_form and away_form:
        score += 15
        factors.append("✅ Form data available")
    elif home_form or away_form:
        score += 8
        factors.append("⚠️ Partial form data")
    else:
        score += 3
        factors.append("➖ Form data not available")
    
    # 5. Data Quality (10p) - Essential fields
    missing_fields = 0
    essential_fields = ['home_team', 'away_team', 'league']
    
    for field in essential_fields:
        if match.get(field) in [None, 'Unknown', '']:
            missing_fields += 1
    
    if missing_fields == 0:
        score += 10
        factors.append("✅ Complete essential data")
    elif missing_fields == 1:
        score += 5
        factors.append(f"⚠️ {missing_fields} essential field missing")
    else:
        score += 2
        factors.append(f"❌ {missing_fields} essential fields missing")
    
    return score, factors

def filter_matches(matches_data):
    """Filter and score matches"""
    scored_matches = []
    
    for match in matches_data:
        score, factors = calculate_score(match)
        match['score'] = score
        match['factors'] = factors
        scored_matches.append(match)
    
    scored_matches.sort(key=lambda x: x['score'], reverse=True)
    filtered = [m for m in scored_matches if m['score'] >= MIN_SCORE]
    
    return filtered, scored_matches

def print_results(filtered, all_matches):
    """Print results"""
    print(f"\n{'='*80}")
    print(f"🎯 FOOTBALL OU2.5 PRE-FILTER RESULTS")
    print(f"{'='*80}\n")
    
    print(f"📊 Statistics:")
    print(f"   Total matches: {len(all_matches)}")
    print(f"   Qualified for AI analysis: {len(filtered)} (≥{MIN_SCORE} points)")
    if len(all_matches) > 0:
        print(f"   API cost savings: €{(len(all_matches) - len(filtered)) * 0.03:.2f}")
        print(f"   Time savings: ~{(len(all_matches) - len(filtered)) * 0.5:.0f} minutes\n")
    
    if filtered:
        print(f"\n🏆 TOP CANDIDATES FOR AI ANALYSIS:\n")
        for i, match in enumerate(filtered[:10], 1):
            print(f"{i}. {match['home_team']} vs {match['away_team']}")
            print(f"   Score: {match['score']}/100 | {match['league']}")
            for factor in match['factors']:
                print(f"   {factor}")
            print()
    
    return filtered

def save_to_json(filtered, filename=None):
    """Save results to JSON file"""
    if filename is None:
        filename = project_root / 'data' / 'football_ai' / 'ai_candidates.json'
    else:
        filename = project_root / 'data' / 'football_ai' / filename
    
    # Ensure directory exists
    filename.parent.mkdir(parents=True, exist_ok=True)
    
    output = {
        'generated_at': datetime.now().isoformat(),
        'total_candidates': len(filtered),
        'min_score': MIN_SCORE,
        'matches': filtered
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved to {filename}")

if __name__ == '__main__':
    print("🔍 Fetching football matches from Notion...")
    matches = get_football_matches()
    
    if not matches:
        print("⚠️  No matches found or Notion database not configured")
        print("   Set NOTION_FOOTBALL_PREMATCH_DB_ID in telegram_secrets.env")
        print("   Or update FOOTBALL_PREMATCH_DB_ID in this file")
        exit(1)
    
    print(f"📥 Found {len(matches)} football matches")
    
    print("\n⚙️ Extracting match data...")
    matches_data = [extract_match_data(m) for m in matches]
    
    print("\n🎯 Calculating scores and filtering...")
    filtered, all_matches = filter_matches(matches_data)
    
    results = print_results(filtered, all_matches)
    save_to_json(filtered)
    
    print(f"\n✅ Pre-filter complete!")
    print(f"\n📋 Next step: Run AI analyzer on {len(filtered)} matches")
    print(f"   Command: python3 scripts/football_ai/ai_analyzer.py")

