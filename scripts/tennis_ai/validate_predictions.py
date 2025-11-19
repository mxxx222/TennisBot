#!/usr/bin/env python3
"""
Tennis Prediction Validator Script
===================================

Validates 21 GPT tennis predictions by matching EventKey identifiers with results
from a manually created CSV file, calculates accuracy metrics, and updates the Notion database.

Usage:
    python scripts/tennis_ai/validate_predictions.py
"""

import os
import sys
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
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
# Database ID - user specified: 271a20e3a65b80d38ca4fe96abf26e91
# Format as UUID: 271a20e3-a65b-80d3-8ca4-fe96abf26e91
NOTION_DB_ID = os.getenv('NOTION_BETTING_TRACKER_DB_ID') or "271a20e3-a65b-80d3-8ca4-fe96abf26e91"  # Betting Tracker database
RESULTS_CSV = project_root / 'data' / 'results.csv'
SUMMARY_JSON = project_root / 'data' / 'validation_summary.json'
SUMMARY_CSV = project_root / 'data' / 'validation_summary.csv'

# ANSI color codes for console output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def parse_impliedp(impliedp_text: str) -> Optional[float]:
    """
    Parse ImpliedP text format to float.
    
    Examples:
        "66,3 %" -> 66.3
        "70.5%" -> 70.5
        "75 %" -> 75.0
    
    Args:
        impliedp_text: ImpliedP text (e.g., "66,3 %")
    
    Returns:
        Float value or None if parsing fails
    """
    if not impliedp_text:
        return None
    
    try:
        # Remove % and whitespace
        text = impliedp_text.strip().replace('%', '').strip()
        
        # Replace comma with dot for decimal separator
        text = text.replace(',', '.')
        
        # Extract numeric value
        return float(text)
    except (ValueError, AttributeError):
        return None


def get_impliedp_range(impliedp: Optional[float]) -> str:
    """
    Categorize ImpliedP into ranges.
    
    Args:
        impliedp: ImpliedP value (0-100)
    
    Returns:
        Range string: "60-65%", "65-70%", "70-75%", "75%+", or "Unknown"
    """
    if impliedp is None:
        return "Unknown"
    
    if 60 <= impliedp < 65:
        return "60-65%"
    elif 65 <= impliedp < 70:
        return "65-70%"
    elif 70 <= impliedp < 75:
        return "70-75%"
    elif impliedp >= 75:
        return "75%+"
    else:
        return "Unknown"


def read_predictions_from_notion(notion_client: Client) -> List[Dict]:
    """
    Read all predictions from Notion database.
    
    Args:
        notion_client: Notion API client
    
    Returns:
        List of prediction dictionaries with EventKey, Match, Side, ImpliedP, Status, page_id
    """
    try:
        # Query all pages from the database
        response = notion_client.databases.query(
            database_id=NOTION_DB_ID,
            page_size=100
        )
        
        predictions = []
        for page in response['results']:
            props = page.get('properties', {})
            
            # Extract EventKey
            event_key_prop = props.get('EventKey', {})
            event_key = None
            if event_key_prop.get('type') == 'number':
                event_key = event_key_prop.get('number')
            
            if event_key is None:
                continue  # Skip if no EventKey
            
            # Extract Match (title)
            match_prop = props.get('Match', {})
            match_title = ""
            if match_prop.get('type') == 'title' and match_prop.get('title'):
                match_title = match_prop['title'][0].get('plain_text', '')
            
            # Extract Side (select: Home/Away)
            side_prop = props.get('Side', {})
            side = None
            if side_prop.get('type') == 'select' and side_prop.get('select'):
                side = side_prop['select'].get('name')
            
            # Extract ImpliedP (text)
            impliedp_prop = props.get('ImpliedP', {})
            impliedp_text = ""
            if impliedp_prop.get('type') == 'rich_text' and impliedp_prop.get('rich_text'):
                impliedp_text = impliedp_prop['rich_text'][0].get('plain_text', '')
            elif impliedp_prop.get('type') == 'title' and impliedp_prop.get('title'):
                impliedp_text = impliedp_prop['title'][0].get('plain_text', '')
            
            # Extract Status
            status_prop = props.get('Status', {})
            status = None
            if status_prop.get('type') == 'select' and status_prop.get('select'):
                status = status_prop['select'].get('name')
            
            predictions.append({
                'page_id': page['id'],
                'event_key': int(event_key),
                'match': match_title,
                'side': side,  # Prediction: Home or Away
                'impliedp_text': impliedp_text,
                'impliedp': parse_impliedp(impliedp_text),
                'status': status
            })
        
        return predictions
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error reading predictions from Notion: {error_msg}")
        
        if "Could not find database" in error_msg or "404" in error_msg:
            print("\n💡 Troubleshooting:")
            print("   1. Verify the database ID is correct")
            print("   2. Make sure your Notion integration has access to the database")
            print("   3. In Notion: Click '...' on database → 'Connections' → Add your integration")
            print(f"   4. Current database ID: {NOTION_DB_ID}")
        
        import traceback
        traceback.print_exc()
        return []


def read_results_from_csv(csv_path: Path) -> Dict[int, Dict]:
    """
    Read match results from CSV file.
    
    Args:
        csv_path: Path to results.csv file
    
    Returns:
        Dictionary mapping EventKey to result dict (Winner, Score)
    """
    results = {}
    
    if not csv_path.exists():
        print(f"⚠️  Results CSV not found: {csv_path}")
        print("   Create it with format: EventKey,Winner,Score")
        return results
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                event_key = int(row['EventKey'])
                results[event_key] = {
                    'winner': row['Winner'].strip(),  # Home or Away
                    'score': row['Score'].strip()
                }
    except Exception as e:
        print(f"❌ Error reading results CSV: {e}")
        import traceback
        traceback.print_exc()
    
    return results


def calculate_accuracy(predictions: List[Dict], results: Dict[int, Dict]) -> Dict:
    """
    Calculate accuracy metrics for predictions.
    
    Args:
        predictions: List of prediction dictionaries
        results: Dictionary of results by EventKey
    
    Returns:
        Dictionary with accuracy metrics
    """
    # Overall stats
    total = 0
    correct = 0
    missing_results = []
    
    # Range-based stats
    range_stats = {
        "60-65%": {'total': 0, 'correct': 0},
        "65-70%": {'total': 0, 'correct': 0},
        "70-75%": {'total': 0, 'correct': 0},
        "75%+": {'total': 0, 'correct': 0},
        "Unknown": {'total': 0, 'correct': 0}
    }
    
    # Detailed results for each prediction
    detailed_results = []
    
    for pred in predictions:
        event_key = pred['event_key']
        predicted_side = pred['side']
        
        if event_key not in results:
            missing_results.append({
                'event_key': event_key,
                'match': pred['match'],
                'predicted_side': predicted_side
            })
            continue
        
        result = results[event_key]
        actual_winner = result['winner']
        
        # Check if prediction is correct
        is_correct = (predicted_side == actual_winner)
        
        # Get ImpliedP range
        impliedp_range = get_impliedp_range(pred['impliedp'])
        
        # Update stats
        total += 1
        if is_correct:
            correct += 1
            range_stats[impliedp_range]['correct'] += 1
        
        range_stats[impliedp_range]['total'] += 1
        
        # Store detailed result
        detailed_results.append({
            'event_key': event_key,
            'match': pred['match'],
            'predicted_side': predicted_side,
            'actual_winner': actual_winner,
            'score': result['score'],
            'impliedp': pred['impliedp'],
            'impliedp_range': impliedp_range,
            'correct': is_correct,
            'page_id': pred['page_id']
        })
    
    # Calculate accuracy percentages
    overall_accuracy = (correct / total * 100) if total > 0 else 0
    
    range_accuracies = {}
    for range_name, stats in range_stats.items():
        if stats['total'] > 0:
            range_accuracies[range_name] = {
                'total': stats['total'],
                'correct': stats['correct'],
                'accuracy': stats['correct'] / stats['total'] * 100
            }
        else:
            range_accuracies[range_name] = {
                'total': 0,
                'correct': 0,
                'accuracy': 0
            }
    
    return {
        'overall': {
            'total': total,
            'correct': correct,
            'accuracy': overall_accuracy
        },
        'by_range': range_accuracies,
        'missing_results': missing_results,
        'detailed_results': detailed_results
    }


def update_notion_with_results(notion_client: Client, detailed_results: List[Dict]) -> Tuple[int, int]:
    """
    Update Notion database with validation results.
    
    Args:
        notion_client: Notion API client
        detailed_results: List of detailed validation results
    
    Returns:
        Tuple of (success_count, error_count)
    """
    success_count = 0
    error_count = 0
    
    for result in detailed_results:
        try:
            # Prepare properties to update
            properties = {
                "Actual Winner": {
                    "select": {"name": result['actual_winner']}
                },
                "Correct": {
                    "checkbox": result['correct']
                },
                "Result": {
                    "rich_text": [{"text": {"content": result['score']}}]
                },
                "Validated At": {
                    "date": {
                        "start": datetime.now().isoformat()
                    }
                },
                "Status": {
                    "select": {"name": "Validated"}
                }
            }
            
            # Update page
            notion_client.pages.update(
                page_id=result['page_id'],
                properties=properties
            )
            
            success_count += 1
        
        except Exception as e:
            print(f"   ❌ Error updating {result['match']} (EventKey: {result['event_key']}): {e}")
            error_count += 1
    
    return success_count, error_count


def print_console_report(metrics: Dict):
    """
    Print color-coded console report with accuracy breakdown.
    
    Args:
        metrics: Accuracy metrics dictionary
    """
    overall = metrics['overall']
    by_range = metrics['by_range']
    
    print("\n" + "=" * 70)
    print(f"{Colors.BOLD}{Colors.CYAN}📊 TENNIS PREDICTION VALIDATION REPORT{Colors.END}")
    print("=" * 70)
    
    # Overall accuracy
    accuracy_color = Colors.GREEN if overall['accuracy'] >= 65 else Colors.RED
    print(f"\n{Colors.BOLD}Overall Accuracy:{Colors.END}")
    print(f"   {accuracy_color}{overall['accuracy']:.1f}%{Colors.END} ({overall['correct']}/{overall['total']} correct)")
    
    if overall['accuracy'] >= 65:
        print(f"   {Colors.GREEN}✅ Strong edge detected! Consider scaling logic.{Colors.END}")
    else:
        print(f"   {Colors.RED}⚠️  Accuracy below 65% threshold.{Colors.END}")
    
    # Breakdown by ImpliedP range
    print(f"\n{Colors.BOLD}Accuracy by ImpliedP Range:{Colors.END}")
    for range_name in ["60-65%", "65-70%", "70-75%", "75%+"]:
        stats = by_range[range_name]
        if stats['total'] > 0:
            acc = stats['accuracy']
            color = Colors.GREEN if acc >= 65 else Colors.YELLOW if acc >= 50 else Colors.RED
            print(f"   {range_name:8s}: {color}{acc:5.1f}%{Colors.END} ({stats['correct']}/{stats['total']})")
        else:
            print(f"   {range_name:8s}: {Colors.YELLOW}No data{Colors.END}")
    
    # Missing results
    if metrics['missing_results']:
        print(f"\n{Colors.YELLOW}⚠️  Missing Results ({len(metrics['missing_results'])}):{Colors.END}")
        for missing in metrics['missing_results']:
            print(f"   EventKey {missing['event_key']}: {missing['match']} (Predicted: {missing['predicted_side']})")
    
    # Incorrect predictions
    incorrect = [r for r in metrics['detailed_results'] if not r['correct']]
    if incorrect:
        print(f"\n{Colors.RED}❌ Incorrect Predictions ({len(incorrect)}):{Colors.END}")
        for result in incorrect:
            print(f"   {result['match']}: Predicted {result['predicted_side']}, Actual {result['actual_winner']} ({result['score']})")
    
    print("\n" + "=" * 70)


def save_summary_files(metrics: Dict):
    """
    Save validation summary to JSON and CSV files.
    
    Args:
        metrics: Accuracy metrics dictionary
    """
    # Save JSON summary
    try:
        with open(SUMMARY_JSON, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Summary saved to: {SUMMARY_JSON}")
    except Exception as e:
        print(f"⚠️  Error saving JSON summary: {e}")
    
    # Save CSV summary
    try:
        with open(SUMMARY_CSV, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Range', 'Total', 'Correct', 'Accuracy %'])
            
            # Overall
            overall = metrics['overall']
            writer.writerow(['Overall', overall['total'], overall['correct'], f"{overall['accuracy']:.1f}"])
            
            # By range
            for range_name in ["60-65%", "65-70%", "70-75%", "75%+"]:
                stats = metrics['by_range'][range_name]
                if stats['total'] > 0:
                    writer.writerow([range_name, stats['total'], stats['correct'], f"{stats['accuracy']:.1f}"])
        
        print(f"💾 Summary saved to: {SUMMARY_CSV}")
    except Exception as e:
        print(f"⚠️  Error saving CSV summary: {e}")


def get_test_predictions() -> List[Dict]:
    """Get test predictions for demo/testing without Notion"""
    return [
        {'page_id': 'test1', 'event_key': 12070966, 'match': 'Player A vs Player B', 'side': 'Away', 'impliedp_text': '66,3 %', 'impliedp': 66.3, 'status': 'Pending'},
        {'page_id': 'test2', 'event_key': 12071014, 'match': 'Player C vs Player D', 'side': 'Home', 'impliedp_text': '72,1 %', 'impliedp': 72.1, 'status': 'Pending'},
        {'page_id': 'test3', 'event_key': 12071015, 'match': 'Player E vs Player F', 'side': 'Home', 'impliedp_text': '63,5 %', 'impliedp': 63.5, 'status': 'Pending'},
    ]


def main():
    """Main validation function"""
    
    # Check for test mode
    import sys
    test_mode = '--test' in sys.argv or '--demo' in sys.argv
    
    if test_mode:
        print("🧪 TEST MODE - Using mock data")
        print("=" * 70)
        predictions = get_test_predictions()
        print(f"   ✅ Using {len(predictions)} test predictions")
    else:
        if not NOTION_AVAILABLE:
            print("❌ Notion client not available")
            return
        
        if not NOTION_TOKEN:
            print("❌ NOTION_TOKEN not set")
            print("   Set NOTION_API_KEY or NOTION_TOKEN in telegram_secrets.env")
            print("   Or run with --test flag for demo mode")
            return
        
        print("🔍 Validating Tennis Predictions...")
        print("=" * 70)
        
        # Initialize Notion client
        notion = Client(auth=NOTION_TOKEN)
        
        # Read predictions from Notion
        print("\n📖 Reading predictions from Notion...")
        predictions = read_predictions_from_notion(notion)
        
        if not predictions:
            print("❌ No predictions found in Notion database")
            print("   💡 Try running with --test flag for demo mode")
            return
    
    print(f"   ✅ Found {len(predictions)} predictions")
    
    # Read results from CSV
    print("\n📖 Reading results from CSV...")
    results = read_results_from_csv(RESULTS_CSV)
    
    if not results:
        print("❌ No results found in CSV file")
        print(f"   Please populate {RESULTS_CSV} with match results")
        return
    
    print(f"   ✅ Found {len(results)} results")
    
    # Calculate accuracy
    print("\n📊 Calculating accuracy metrics...")
    metrics = calculate_accuracy(predictions, results)
    
    # Print console report
    print_console_report(metrics)
    
    # Update Notion with results (skip in test mode)
    if not test_mode:
        print("\n💾 Updating Notion database...")
        notion = Client(auth=NOTION_TOKEN)
        success_count, error_count = update_notion_with_results(notion, metrics['detailed_results'])
        print(f"   ✅ Updated: {success_count}")
        if error_count > 0:
            print(f"   ❌ Errors: {error_count}")
    else:
        print("\n💾 Skipping Notion update (test mode)")
    
    # Save summary files
    save_summary_files(metrics)
    
    print(f"\n✅ Validation complete!")
    print(f"   View updated predictions in Notion database")


if __name__ == '__main__':
    main()

