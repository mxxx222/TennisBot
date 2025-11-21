#!/usr/bin/env python3
"""
Save Football OU2.5 AI analysis results to Notion database.
Integrates with the feedback loop for calibration.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / 'telegram_secrets.env'
if env_path.exists():
    load_dotenv(env_path)

try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    print("⚠️  notion-client not installed. Install with: pip install notion-client")
    NOTION_AVAILABLE = False

# CONFIG
NOTION_TOKEN = os.getenv('NOTION_API_KEY') or os.getenv('NOTION_TOKEN')
# TODO: Set your Football OU2.5 Predictions database ID
NOTION_DB_ID = os.getenv('NOTION_FOOTBALL_AI_PREDICTIONS_DB_ID') or ""
INPUT_FILE = project_root / 'data' / 'football_ai' / 'ai_analysis_results.json'

# FILTERING THRESHOLD
# Based on validation: 100% win rate (12/12) for 70%+ impliedP bets
# ROI: +39.3% with 70% threshold vs +5.8% without filter
MIN_IMPLIEDP_THRESHOLD = 70.0  # Minimum impliedP percentage to save prediction

def save_prediction_to_notion(notion_client, match_data, analysis_result):
    """
    Save a single prediction to Notion.
    
    Args:
        notion_client: Notion Client instance
        match_data: Dict with match info (teams, league, date, url)
        analysis_result: Dict with AI analysis (recommendation, confidence, edge, reasoning)
    
    Returns:
        page_id if successful, None otherwise
    """
    try:
        # Create match name
        match_name = f"{match_data.get('home_team', 'Unknown')} vs {match_data.get('away_team', 'Unknown')}"
        
        # Parse date if available
        date_value = None
        if match_data.get('date'):
            try:
                # Try parsing ISO format
                date_value = match_data['date'].split('T')[0]  # Get date part only
            except:
                pass
        
        # Map recommendation (OVER/UNDER/Skip)
        recommendation = analysis_result.get('recommended_bet', 'Skip')
        if recommendation not in ['OVER', 'UNDER', 'Skip']:
            recommendation = 'Skip'
        
        # Get confidence as number (0-1)
        confidence_value = 0.0
        confidence_str = analysis_result.get('confidence', 'Low')
        confidence_map = {'High': 0.8, 'Medium': 0.6, 'Low': 0.4}
        confidence_value = confidence_map.get(confidence_str, 0.4)
        
        # Get edge as number (percentage to decimal)
        edge_value = analysis_result.get('expected_value_pct', 0) / 100.0
        
        # Get pre-filter score
        prefilter_score = match_data.get('score', 0)
        
        # Build properties
        properties = {
            "Match": {
                "title": [{"text": {"content": match_name}}]
            },
            "League": {
                "rich_text": [{"text": {"content": match_data.get('league', 'Unknown')[:2000]}}]
            },
            "Pre-filter Score": {
                "number": prefilter_score
            },
            "AI Recommendation": {
                "select": {"name": recommendation}
            },
            "AI Confidence": {
                "number": confidence_value
            },
            "Predicted Edge": {
                "number": edge_value
            },
            "Actual Result": {
                "select": {"name": "Pending"}
            }
        }
        
        # Add date if available
        if date_value:
            properties["Match Date"] = {
                "date": {
                    "start": date_value
                }
            }
        
        # Add reasoning (truncate to 2000 chars for Notion limit)
        reasoning = analysis_result.get('reasoning', 'No reasoning provided')
        if len(reasoning) > 2000:
            reasoning = reasoning[:1997] + "..."
        properties["Reasoning"] = {
            "rich_text": [{"text": {"content": reasoning}}]
        }
        
        # Add match URL if available
        if match_data.get('page_url'):
            properties["Match URL"] = {
                "url": match_data['page_url']
            }
        
        # Create page
        page = notion_client.pages.create(
            parent={"database_id": NOTION_DB_ID},
            properties=properties
        )
        
        return page["id"]
        
    except Exception as e:
        print(f"   ❌ Error saving {match_name}: {str(e)}")
        return None

def save_batch_to_notion(results_file=None):
    """
    Save all predictions from AI analysis file to Notion.
    """
    if results_file is None:
        results_file = INPUT_FILE
    
    results_file = Path(results_file)
    
    if not results_file.exists():
        print(f"❌ ERROR: Results file not found: {results_file}")
        print("   Run ai_analyzer.py first")
        return 0, 0
    
    if not NOTION_AVAILABLE:
        print("❌ ERROR: notion-client not installed")
        print("   Install: pip install notion-client")
        return 0, 0
    
    if not NOTION_TOKEN:
        print("⚠️  NOTION_TOKEN not set - skipping Notion save")
        print("   Set NOTION_API_KEY or NOTION_TOKEN in telegram_secrets.env")
        return 0, 0
    
    if not NOTION_DB_ID:
        print("⚠️  NOTION_FOOTBALL_AI_PREDICTIONS_DB_ID not set")
        print("   Set it in telegram_secrets.env or update NOTION_DB_ID in this file")
        return 0, 0
    
    print("💾 Saving predictions to Notion...")
    print("=" * 70)
    
    # Load results
    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Initialize Notion client
    try:
        notion = Client(auth=NOTION_TOKEN)
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize Notion client: {e}")
        return 0, 0
    
    # Get all analyses
    analyses = data.get('all_analyses', [])
    
    if not analyses:
        print("⚠️  No analyses found in results file")
        return 0, 0
    
    print(f"📊 Found {len(analyses)} analyses to save\n")
    
    saved_count = 0
    bet_count = 0
    skip_count = 0
    error_count = 0
    filtered_count = 0
    
    for i, analysis in enumerate(analyses, 1):
        match_data = analysis.get('match_data', {})
        recommendation = analysis.get('recommended_bet', 'Skip')
        match_name = f"{match_data.get('home_team', 'Unknown')} vs {match_data.get('away_team', 'Unknown')}"
        
        # Check impliedP threshold (only for bet recommendations)
        if recommendation in ['OVER', 'UNDER']:
            # Get impliedP from match_data if available
            impliedp = match_data.get('impliedP') or match_data.get('impliedp') or match_data.get('implied_probability')
            
            # If not available, use win_probability as proxy (convert to percentage)
            if impliedp is None:
                win_prob = analysis.get('win_probability', 0)
                if win_prob:
                    impliedp = win_prob * 100  # Convert 0-1 to percentage
                else:
                    impliedp = None
            
            # Filter out bets below threshold
            if impliedp is not None and impliedp < MIN_IMPLIEDP_THRESHOLD:
                filtered_count += 1
                print(f"[{i}/{len(analyses)}] {match_name}... ⏭️  FILTERED (impliedP {impliedp:.1f}% < {MIN_IMPLIEDP_THRESHOLD}%)")
                continue
        
        print(f"[{i}/{len(analyses)}] {match_name}...", end=" ")
        
        page_id = save_prediction_to_notion(notion, match_data, analysis)
        
        if page_id:
            saved_count += 1
            if recommendation in ['OVER', 'UNDER']:
                bet_count += 1
                print(f"✅ Saved (BET)")
            else:
                skip_count += 1
                print(f"✅ Saved (SKIP)")
        else:
            error_count += 1
            print(f"❌ Failed")
    
    print(f"\n{'='*70}")
    print(f"📊 Summary:")
    print(f"   ✅ Saved: {saved_count}")
    print(f"   🎯 BET recommendations: {bet_count}")
    print(f"   ⏭️  SKIP: {skip_count}")
    if filtered_count > 0:
        print(f"   🚫 FILTERED (impliedP < {MIN_IMPLIEDP_THRESHOLD}%): {filtered_count}")
    print(f"   ❌ Errors: {error_count}")
    
    if filtered_count > 0:
        print(f"\n💡 Filtered {filtered_count} bets below {MIN_IMPLIEDP_THRESHOLD}% impliedP threshold")
        print(f"   Based on validation: 100% win rate for 70%+ impliedP (12/12)")
        print(f"   Expected ROI improvement: +39.3% (vs +5.8% without filter)")
    
    if saved_count > 0:
        print(f"\n🔗 View in Notion: https://www.notion.so/{NOTION_DB_ID.replace('-', '')}")
    
    return saved_count, bet_count

if __name__ == "__main__":
    saved, bets = save_batch_to_notion()
    
    if saved > 0:
        print(f"\n✅ Successfully saved {saved} predictions to Notion!")
    else:
        print(f"\n⚠️  No predictions saved. Check errors above.")

