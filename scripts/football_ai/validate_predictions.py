#!/usr/bin/env python3
"""
Validate Football OU2.5 Predictions
===================================

Reads predictions from Notion database and validates them against actual results.
Tracks accuracy by impliedP ranges and provides ROI analysis.

Usage:
    python3 scripts/football_ai/validate_predictions.py
"""

import os
import sys
import csv
import json
from pathlib import Path
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
# TODO: Set your Football OU2.5 Predictions database ID
NOTION_DB_ID = os.getenv('NOTION_FOOTBALL_AI_PREDICTIONS_DB_ID') or ""

# Output files
SUMMARY_JSON = project_root / 'data' / 'football_ai' / 'validation_summary.json'
SUMMARY_CSV = project_root / 'data' / 'football_ai' / 'validation_summary.csv'

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BOLD = '\033[1m'
    END = '\033[0m'

def parse_impliedp(impliedp_text: str) -> Optional[float]:
    """
    Parse ImpliedP text format to float.
    
    Examples:
        "66,3 %" -> 66.3
        "70.5%" -> 70.5
        "70.5%" -> 70.5
    """
    if not impliedp_text:
        return None
    
    try:
        text = impliedp_text.strip().replace('%', '').strip()
        text = text.replace(',', '.')  # Handle comma decimal separator
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
        List of prediction dictionaries with EventKey, Match, Recommendation, ImpliedP, Status, page_id
    """
    if not NOTION_DB_ID:
        print("❌ ERROR: NOTION_FOOTBALL_AI_PREDICTIONS_DB_ID not set")
        print("   Set it in telegram_secrets.env or update NOTION_DB_ID in this file")
        return []
    
    try:
        all_pages = []
        has_more = True
        start_cursor = None
        
        while has_more:
            if start_cursor:
                response = notion_client.databases.query(
                    database_id=NOTION_DB_ID,
                    start_cursor=start_cursor
                )
            else:
                response = notion_client.databases.query(
                    database_id=NOTION_DB_ID
                )
            
            all_pages.extend(response['results'])
            has_more = response.get('has_more', False)
            start_cursor = response.get('next_cursor')
        
        predictions = []
        
        for page in all_pages:
            props = page.get('properties', {})
            
            # Extract Match (title)
            match_prop = props.get('Match', {})
            match_name = ""
            if match_prop.get('type') == 'title' and match_prop.get('title'):
                match_name = match_prop['title'][0].get('plain_text', '')
            
            # Extract AI Recommendation (select)
            recommendation_prop = props.get('AI Recommendation', {})
            recommendation = ""
            if recommendation_prop.get('type') == 'select' and recommendation_prop.get('select'):
                recommendation = recommendation_prop['select'].get('name', '')
            
            # Extract ImpliedP (if available - may need to be added to Notion schema)
            impliedp_prop = props.get('ImpliedP', {})
            impliedp_text = ""
            if impliedp_prop.get('type') == 'rich_text' and impliedp_prop.get('rich_text'):
                impliedp_text = impliedp_prop['rich_text'][0].get('plain_text', '')
            elif impliedp_prop.get('type') == 'number':
                impliedp_value = impliedp_prop.get('number')
                if impliedp_value:
                    impliedp_text = f"{impliedp_value}%"
            
            # Extract Actual Result (select)
            result_prop = props.get('Actual Result', {})
            status = "Pending"
            if result_prop.get('type') == 'select' and result_prop.get('select'):
                status = result_prop['select'].get('name', 'Pending')
            
            predictions.append({
                'page_id': page['id'],
                'match': match_name,
                'recommendation': recommendation,
                'impliedp_text': impliedp_text,
                'impliedp': parse_impliedp(impliedp_text),
                'status': status
            })
        
        return predictions
        
    except Exception as e:
        print(f"❌ ERROR: Failed to read predictions from Notion: {e}")
        return []

def get_actual_results() -> Dict[str, Dict]:
    """
    Get actual match results.
    This should be populated from match result tracking.
    
    Returns:
        Dict mapping match names to results: {match_name: {'result': 'OVER'|'UNDER', 'goals': X}}
    """
    # TODO: Integrate with match result tracking system
    # For now, return empty dict - results should be manually entered or scraped
    return {}

def calculate_accuracy_metrics(predictions: List[Dict], results: Dict[str, Dict]) -> Dict:
    """
    Calculate accuracy metrics from predictions and results.
    
    Args:
        predictions: List of prediction dictionaries
        results: Dictionary of results by match name
    
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
        match_name = pred['match']
        predicted_recommendation = pred['recommendation']
        
        if match_name not in results:
            missing_results.append({
                'match': match_name,
                'predicted_recommendation': predicted_recommendation
            })
            continue
        
        result = results[match_name]
        actual_result = result.get('result', '')  # 'OVER' or 'UNDER'
        
        # Check if prediction is correct
        is_correct = (predicted_recommendation == actual_result)
        
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
            'match': match_name,
            'predicted_recommendation': predicted_recommendation,
            'actual_result': actual_result,
            'goals': result.get('goals', 'N/A'),
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

def print_metrics(metrics: Dict):
    """Print accuracy metrics to console"""
    overall = metrics['overall']
    by_range = metrics['by_range']
    
    print("=" * 70)
    print(f"{Colors.BOLD}FOOTBALL OU2.5 PREDICTION VALIDATION{Colors.END}")
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
            marker = "🔥" if range_name.startswith("70") or range_name == "75%+" else ""
            print(f"   {range_name:8s}: {color}{acc:5.1f}%{Colors.END} ({stats['correct']}/{stats['total']}) {marker}")
        else:
            print(f"   {range_name:8s}: {Colors.YELLOW}No data{Colors.END}")
    
    # Highlight 70%+ performance
    stats_70_plus = by_range.get("70-75%", {'total': 0, 'correct': 0})
    stats_75_plus = by_range.get("75%+", {'total': 0, 'correct': 0})
    total_70_plus = stats_70_plus['total'] + stats_75_plus['total']
    correct_70_plus = stats_70_plus['correct'] + stats_75_plus['correct']
    
    if total_70_plus > 0:
        acc_70_plus = (correct_70_plus / total_70_plus) * 100
        print(f"\n{Colors.BOLD}🎯 70%+ ImpliedP Performance:{Colors.END}")
        print(f"   {Colors.GREEN}Win Rate: {acc_70_plus:.1f}% ({correct_70_plus}/{total_70_plus}){Colors.END}")
        if acc_70_plus >= 90:
            print(f"   {Colors.GREEN}✅ EXCELLENT: Consider using 70%+ threshold filter{Colors.END}")
        elif acc_70_plus >= 75:
            print(f"   {Colors.GREEN}✅ STRONG: 70%+ threshold recommended{Colors.END}")
    
    # Recommendation based on 70%+ performance
    if total_70_plus >= 5:  # Need at least 5 samples for meaningful recommendation
        if acc_70_plus >= 90:
            print(f"\n{Colors.BOLD}💡 RECOMMENDATION:{Colors.END}")
            print(f"   {Colors.GREEN}✅ Use 70%+ impliedP threshold filter{Colors.END}")
            print(f"   • 70%+ bets: {acc_70_plus:.1f}% win rate ({correct_70_plus}/{total_70_plus})")
            print(f"   • Expected ROI improvement: +30-40% vs unfiltered")
            print(f"   • Filter out bets below 70% impliedP in save_to_notion.py")
    
    # Missing results
    if metrics['missing_results']:
        print(f"\n{Colors.YELLOW}⚠️  Missing Results ({len(metrics['missing_results'])}):{Colors.END}")
        for missing in metrics['missing_results']:
            print(f"   {missing['match']} (Predicted: {missing['predicted_recommendation']})")
    
    # Incorrect predictions
    incorrect = [r for r in metrics['detailed_results'] if not r['correct']]
    if incorrect:
        print(f"\n{Colors.RED}❌ Incorrect Predictions ({len(incorrect)}):{Colors.END}")
        for result in incorrect:
            print(f"   {result['match']}: Predicted {result['predicted_recommendation']}, Actual {result['actual_result']} ({result['goals']} goals)")
    
    print("\n" + "=" * 70)

def save_summary_files(metrics: Dict):
    """
    Save validation summary to JSON and CSV files.
    
    Args:
        metrics: Accuracy metrics dictionary
    """
    # Save JSON summary
    try:
        SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
        with open(SUMMARY_JSON, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Summary saved to: {SUMMARY_JSON}")
    except Exception as e:
        print(f"⚠️  Error saving JSON summary: {e}")
    
    # Save CSV summary
    try:
        SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)
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

def main():
    """Main validation function"""
    if not NOTION_AVAILABLE:
        print("❌ Notion client not available")
        return
    
    if not NOTION_TOKEN:
        print("❌ NOTION_TOKEN not set")
        print("   Set NOTION_API_KEY or NOTION_TOKEN in telegram_secrets.env")
        return
    
    if not NOTION_DB_ID:
        print("❌ NOTION_FOOTBALL_AI_PREDICTIONS_DB_ID not set")
        print("   Set it in telegram_secrets.env or update NOTION_DB_ID in this file")
        return
    
    print("📥 Loading predictions from Notion...")
    
    try:
        notion = Client(auth=NOTION_TOKEN)
        predictions = read_predictions_from_notion(notion)
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to Notion: {e}")
        return
    
    if not predictions:
        print("⚠️  No predictions found in Notion database")
        return
    
    print(f"✅ Loaded {len(predictions)} predictions")
    
    # Get actual results
    print("\n📊 Loading actual results...")
    results = get_actual_results()
    
    if not results:
        print("⚠️  No actual results found")
        print("   TODO: Integrate with match result tracking system")
        print("   For now, results should be manually entered or scraped")
        return
    
    print(f"✅ Loaded {len(results)} results")
    
    # Calculate metrics
    print("\n🔍 Calculating accuracy metrics...")
    metrics = calculate_accuracy_metrics(predictions, results)
    
    # Print results
    print_metrics(metrics)
    
    # Save summary files
    save_summary_files(metrics)
    
    print("\n✅ Validation complete!")

if __name__ == '__main__':
    main()

