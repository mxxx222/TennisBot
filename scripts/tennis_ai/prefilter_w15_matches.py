#!/usr/bin/env python3
"""
W15 Tennis Pre-Filter
Suodattaa parhaat AI-analyysi kandidaatit Notion-datasta
Kustannus: €0 (ei API-kutsuja)
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
PREMATCH_DB_ID = os.getenv('NOTION_TENNIS_PREMATCH_DB_ID') or os.getenv('NOTION_PREMATCH_DB_ID') or "81a70fea5de140d384c77abee225436d"
MIN_SCORE = 50  # Cut-off pisteet (lowered since ranking data may be missing)

if not NOTION_TOKEN:
    print("❌ ERROR: NOTION_API_KEY or NOTION_TOKEN not set")
    print("   Set it in telegram_secrets.env")
    exit(1)

notion = Client(auth=NOTION_TOKEN)

def get_w15_matches():
    """Hae kaikki upcoming W15-ottelut"""
    response = notion.databases.query(
        database_id=PREMATCH_DB_ID,
        filter={
            "and": [
                {"property": "Tournament Tier", "select": {"equals": "W15"}},
                {"property": "Match Status", "select": {"equals": "Upcoming"}}
            ]
        },
        sorts=[{"property": "Päivämäärä", "direction": "ascending"}]
    )
    return response['results']

def extract_match_data(page):
    """Pura ottelun data Notion-sivulta"""
    props = page['properties']
    
    def safe_get(prop_name, prop_type):
        try:
            if prop_type == 'text':
                rich_text = props.get(prop_name, {}).get('rich_text', [])
                return rich_text[0]['plain_text'] if rich_text else None
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
        'player_a': safe_get('Pelaaja A nimi', 'text') or 'Unknown',
        'player_b': safe_get('Pelaaja B nimi', 'text') or 'Unknown',
        'ranking_a': safe_get('Ranking A', 'number'),
        'ranking_b': safe_get('Ranking B', 'number'),
        'tournament': safe_get('Turnaus', 'text') or 'Unknown',
        'surface': safe_get('Kenttä', 'select') or 'Unknown',
        'status': safe_get('Match Status', 'select') or 'Unknown',
        'date': safe_get('Päivämäärä', 'date')
    }

def calculate_score(match):
    """Laske ottelun pisteet (0-100)"""
    score = 0
    factors = []
    
    # 1. Ranking Gap (30p) - Optional, don't penalize if missing
    if match.get('ranking_a') and match.get('ranking_b'):
        gap = abs(match['ranking_a'] - match['ranking_b'])
        if 20 <= gap <= 80:
            score += 30
            factors.append(f"✅ Optimal ranking gap: {gap}")
        elif gap < 20:
            score += 10
            factors.append(f"⚠️ Small ranking gap: {gap}")
        else:
            score += 5
            factors.append(f"⚠️ Large ranking gap: {gap}")
    else:
        # Don't penalize - ranking data may not be available yet
        score += 15  # Base points for having match data
        factors.append("➖ Ranking data not available (will use AI analysis)")
    
    # 2. Surface Match (25p)
    if match.get('surface') and match['surface'] != 'Unknown':
        score += 25
        factors.append(f"✅ Surface: {match['surface']}")
    else:
        score += 10
        factors.append("⚠️ Surface unknown")
    
    # 3. W15 Experience (20p) - All matches are W15
    score += 20
    factors.append("✅ W15 tournament")
    
    # 4. Data Quality (25p) - Focus on essential fields
    missing_fields = 0
    essential_fields = ['player_a', 'player_b', 'tournament']
    optional_fields = ['ranking_a', 'ranking_b', 'surface']
    
    # Check essential fields
    for field in essential_fields:
        if match.get(field) in [None, 'Unknown', '']:
            missing_fields += 1
    
    if missing_fields == 0:
        score += 25
        factors.append("✅ Complete essential data")
    elif missing_fields == 1:
        score += 15
        factors.append(f"⚠️ {missing_fields} essential field missing")
    else:
        score += 5
        factors.append(f"❌ {missing_fields} essential fields missing")
    
    # Bonus for having optional data
    optional_count = sum(1 for field in optional_fields if match.get(field) not in [None, 'Unknown', ''])
    if optional_count >= 2:
        score += 5
        factors.append(f"✅ Bonus: {optional_count} optional fields available")
    
    return score, factors

def filter_matches(matches_data):
    """Suodata ja pisteyä ottelut"""
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
    """Tulosta tulokset"""
    print(f"\n{'='*80}")
    print(f"🎯 W15 PRE-FILTER RESULTS")
    print(f"{'='*80}\n")
    
    print(f"📊 Statistics:")
    print(f"   Total matches: {len(all_matches)}")
    print(f"   Qualified for AI analysis: {len(filtered)} (≥{MIN_SCORE} points)")
    print(f"   API cost savings: €{(len(all_matches) - len(filtered)) * 0.03:.2f}")
    print(f"   Time savings: ~{(len(all_matches) - len(filtered)) * 0.5:.0f} minutes\n")
    
    if filtered:
        print(f"\n🏆 TOP CANDIDATES FOR AI ANALYSIS:\n")
        for i, match in enumerate(filtered[:10], 1):
            print(f"{i}. {match['player_a']} vs {match['player_b']}")
            print(f"   Score: {match['score']}/100 | {match['tournament']} | {match['surface']}")
            for factor in match['factors']:
                print(f"   {factor}")
            print()
    
    return filtered

def save_to_json(filtered, filename=None):
    """Tallenna tulokset JSON-tiedostoon"""
    if filename is None:
        filename = project_root / 'data' / 'tennis_ai' / 'ai_candidates.json'
    else:
        filename = project_root / 'data' / 'tennis_ai' / filename
    
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
    print("🔍 Fetching W15 matches from Notion...")
    matches = get_w15_matches()
    
    print(f"📥 Found {len(matches)} W15 matches")
    
    print("\n⚙️ Extracting match data...")
    matches_data = [extract_match_data(m) for m in matches]
    
    print("\n🎯 Calculating scores and filtering...")
    filtered, all_matches = filter_matches(matches_data)
    
    results = print_results(filtered, all_matches)
    save_to_json(filtered)
    
    print(f"\n✅ Pre-filter complete!")
    print(f"\n📋 Next step: Run AI analyzer on {len(filtered)} matches")
    print(f"   Command: python3 scripts/tennis_ai/ai_analyzer.py")

