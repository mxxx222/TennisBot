#!/usr/bin/env python3
"""
Track tennis match results and update Notion database.
Fetches results from FlashScore or Notion match data and updates Actual Result field.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
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
    print("❌ ERROR: notion-client not installed")
    print("   Install: pip install notion-client")
    NOTION_AVAILABLE = False
    exit(1)

# CONFIG
NOTION_TOKEN = os.getenv('NOTION_API_KEY') or os.getenv('NOTION_TOKEN')
NOTION_DB_ID = os.getenv('NOTION_AI_PREDICTIONS_DB_ID') or "f114ed7edffc4e799a05280ca89bc63e"
NOTION_PREMATCH_DB_ID = os.getenv('NOTION_TENNIS_PREMATCH_DB_ID') or os.getenv('NOTION_PREMATCH_DB_ID') or "81a70fea5de140d384c77abee225436d"

def get_pending_matches(notion_client):
    """Query Notion for matches with Pending status"""
    try:
        response = notion_client.databases.query(
            database_id=NOTION_DB_ID,
            filter={
                "property": "Actual Result",
                "select": {
                    "equals": "Pending"
                }
            }
        )
        return response['results']
    except Exception as e:
        print(f"❌ Error querying Notion: {e}")
        return []

def get_match_from_prematch_db(notion_client, match_name):
    """Try to find match in prematch database to get current status"""
    try:
        # Search for match by player names
        # This is a simplified search - in production you'd want better matching
        response = notion_client.databases.query(
            database_id=NOTION_PREMATCH_DB_ID,
            page_size=100
        )
        
        # Try to find matching match
        for page in response['results']:
            props = page.get('properties', {})
            name = props.get('Name', {}).get('title', [])
            if name and match_name.lower() in name[0].get('plain_text', '').lower():
                return page
        
        return None
    except Exception as e:
        print(f"   ⚠️  Error searching prematch DB: {e}")
        return None

def determine_result_from_status(status):
    """Determine result from match status"""
    if not status:
        return None
    
    status_lower = status.lower()
    
    # Completed matches
    if 'finished' in status_lower or 'completed' in status_lower or 'won' in status_lower:
        return "Completed"  # Need to determine W/L
    
    # Pending/upcoming
    if 'upcoming' in status_lower or 'pending' in status_lower or 'scheduled' in status_lower:
        return "Pending"
    
    # Cancelled/postponed
    if 'cancelled' in status_lower or 'postponed' in status_lower:
        return "Cancelled"
    
    return None

def parse_match_result(match_data, prematch_page=None):
    """
    Parse match result from available data.
    Returns: 'W', 'L', 'PUSH', 'Pending', or None
    """
    # Check if we have prematch data with status
    if prematch_page:
        props = prematch_page.get('properties', {})
        status = props.get('Match Status', {}).get('select', {})
        status_name = status.get('name', '') if status else ''
        
        if status_name and status_name != 'Upcoming':
            # Match has a status - check if we can determine result
            if 'Finished' in status_name or 'Completed' in status_name:
                # Need to determine winner from score or other data
                # For now, return None - will need score parsing
                return None
    
    # Check match date to see if it should be completed
    match_date_str = match_data.get('date')
    if match_date_str:
        try:
            # Parse date
            if 'T' in match_date_str:
                match_date = datetime.fromisoformat(match_date_str.replace('Z', '+00:00'))
            else:
                match_date = datetime.fromisoformat(match_date_str)
            
            # Check if match date has passed (add 3 hours for match duration)
            now = datetime.now(match_date.tzinfo) if match_date.tzinfo else datetime.now()
            match_end = match_date + timedelta(hours=3)
            
            if now > match_end:
                # Match should be completed, but we don't have result
                # Return None to indicate we need to fetch result
                return None
            else:
                # Match hasn't happened yet
                return "Pending"
        except Exception as e:
            print(f"   ⚠️  Error parsing date: {e}")
    
    return "Pending"

def calculate_profit_loss(ai_recommendation, actual_result, stake_pct, actual_odds):
    """
    Calculate profit/loss for a bet.
    
    Args:
        ai_recommendation: 'Player A' or 'Player B'
        actual_result: 'W', 'L', 'PUSH', or 'Pending'
        stake_pct: Stake percentage (0-5)
        actual_odds: Actual odds (decimal, e.g. 2.5)
    
    Returns:
        Profit/Loss amount (positive for win, negative for loss, 0 for push)
    """
    if actual_result == 'Pending' or actual_result is None:
        return None
    
    if actual_result == 'PUSH':
        return 0.0
    
    if actual_odds is None or actual_odds <= 0:
        return None
    
    # Determine if we won
    if actual_result == 'W':
        # Win: profit = stake * (odds - 1)
        # Assuming stake_pct is percentage of bankroll (e.g., 2% = 0.02)
        # For calculation, we'll use stake_pct as multiplier
        # If stake is 2% and bankroll is 100, stake = 2
        # Profit = 2 * (2.5 - 1) = 2 * 1.5 = 3
        profit = stake_pct * (actual_odds - 1)
        return profit
    elif actual_result == 'L':
        # Loss: lose the stake
        loss = -stake_pct
        return loss
    
    return None

def update_match_result(notion_client, page_id, result, actual_odds=None, profit_loss=None):
    """Update match result in Notion"""
    try:
        properties = {
            "Actual Result": {
                "select": {"name": result}
            }
        }
        
        # Try to add Result Updated At if property exists
        try:
            properties["Result Updated At"] = {
                "date": {
                    "start": datetime.now().isoformat()
                }
            }
        except:
            pass  # Property might not exist
        
        if actual_odds is not None:
            properties["Actual Odds"] = {"number": actual_odds}
        
        if profit_loss is not None:
            properties["Profit/Loss"] = {"number": profit_loss}
        
        notion_client.pages.update(
            page_id=page_id,
            properties=properties
        )
        
        return True
    except Exception as e:
        print(f"   ❌ Error updating Notion: {e}")
        return False

def track_results():
    """Main function to track match results"""
    if not NOTION_AVAILABLE:
        print("❌ Notion client not available")
        return
    
    if not NOTION_TOKEN:
        print("❌ NOTION_TOKEN not set")
        print("   Set NOTION_API_KEY or NOTION_TOKEN in telegram_secrets.env")
        return
    
    print("🔍 Tracking Match Results...")
    print("=" * 70)
    
    notion = Client(auth=NOTION_TOKEN)
    
    # Get pending matches
    pending_matches = get_pending_matches(notion)
    
    if not pending_matches:
        print("✅ No pending matches found")
        return
    
    print(f"📊 Found {len(pending_matches)} pending matches\n")
    
    updated_count = 0
    still_pending = 0
    error_count = 0
    
    for i, page in enumerate(pending_matches, 1):
        props = page.get('properties', {})
        
        # Get match info
        match_name = props.get('Match', {}).get('title', [])
        match_name_str = match_name[0].get('plain_text', 'Unknown') if match_name else 'Unknown'
        
        # Get match date
        match_date = props.get('Match Date', {}).get('date', {})
        match_date_str = match_date.get('start') if match_date else None
        
        # Get AI recommendation
        ai_rec = props.get('AI Recommendation', {}).get('select', {})
        ai_rec_str = ai_rec.get('name', 'Skip') if ai_rec else 'Skip'
        
        # Get stake percentage
        stake_prop = props.get('Suggested Stake', {})
        stake_pct = stake_prop.get('number') if stake_prop.get('type') == 'number' else None
        if stake_pct is None or stake_pct == 0:
            # Try to get from analysis if available
            # Default to 2% if not specified
            stake_pct = 2.0
        
        # Get actual odds if available
        actual_odds_prop = props.get('Actual Odds', {})
        actual_odds = actual_odds_prop.get('number') if actual_odds_prop.get('type') == 'number' else None
        
        print(f"[{i}/{len(pending_matches)}] {match_name_str}")
        
        # Skip if recommendation was Skip
        if ai_rec_str == 'Skip':
            print(f"   ⏭️  Skipped (was Skip recommendation)")
            continue
        
        # Try to get match from prematch database
        prematch_page = get_match_from_prematch_db(notion, match_name_str)
        
        # Parse result
        match_data = {
            'date': match_date_str,
            'name': match_name_str
        }
        
        result = parse_match_result(match_data, prematch_page)
        
        if result == "Pending":
            still_pending += 1
            print(f"   ⏳ Still pending (match not completed yet)")
        elif result is None:
            # Match should be completed but we don't have result
            # For now, mark as needs manual check
            print(f"   ⚠️  Match should be completed - needs manual check")
            print(f"      Check FlashScore or update manually in Notion")
        else:
            # Calculate P/L if we have result and odds
            profit_loss = None
            if result in ['W', 'L', 'PUSH'] and actual_odds:
                profit_loss = calculate_profit_loss(ai_rec_str, result, stake_pct, actual_odds)
                if profit_loss is not None:
                    print(f"   💰 P/L: ${profit_loss:.2f}")
            
            # Update result
            if update_match_result(notion, page['id'], result, actual_odds, profit_loss):
                updated_count += 1
                print(f"   ✅ Updated: {result}")
            else:
                error_count += 1
    
    print(f"\n{'='*70}")
    print(f"📊 Summary:")
    print(f"   ✅ Updated: {updated_count}")
    print(f"   ⏳ Still pending: {still_pending}")
    print(f"   ❌ Errors: {error_count}")
    
    if updated_count > 0:
        print(f"\n💡 Note: P/L calculation will be done separately")
        print(f"   Run: python3 scripts/tennis_ai/calculate_roi.py")

if __name__ == '__main__':
    track_results()

