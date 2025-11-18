#!/usr/bin/env python3
"""
Calculate ROI from completed matches in Notion database.
Generates comprehensive ROI report with metrics and insights.
"""

import os
import sys
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
    print("❌ ERROR: notion-client not installed")
    print("   Install: pip install notion-client")
    NOTION_AVAILABLE = False
    exit(1)

# CONFIG
NOTION_TOKEN = os.getenv('NOTION_API_KEY') or os.getenv('NOTION_TOKEN')
NOTION_DB_ID = os.getenv('NOTION_AI_PREDICTIONS_DB_ID') or "f114ed7edffc4e799a05280ca89bc63e"

def get_completed_matches(notion_client):
    """Get all matches with completed results (W, L, or PUSH)"""
    try:
        # Get all matches
        all_matches = []
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
            
            all_matches.extend(response['results'])
            has_more = response.get('has_more', False)
            start_cursor = response.get('next_cursor')
        
        # Filter for completed matches
        completed = []
        for page in all_matches:
            props = page.get('properties', {})
            actual_result = props.get('Actual Result', {}).get('select', {})
            result_name = actual_result.get('name', '') if actual_result else ''
            
            if result_name in ['W', 'L', 'PUSH']:
                completed.append(page)
        
        return completed
    except Exception as e:
        print(f"❌ Error querying Notion: {e}")
        return []

def extract_match_data(page):
    """Extract match data from Notion page"""
    props = page.get('properties', {})
    
    def safe_get(prop_name, prop_type):
        try:
            if prop_type == 'title':
                title = props.get(prop_name, {}).get('title', [])
                return title[0].get('plain_text', '') if title else ''
            elif prop_type == 'select':
                select = props.get(prop_name, {}).get('select', {})
                return select.get('name', '') if select else ''
            elif prop_type == 'number':
                return props.get(prop_name, {}).get('number')
            elif prop_type == 'date':
                date_obj = props.get(prop_name, {}).get('date', {})
                return date_obj.get('start') if date_obj else None
        except:
            return None
    
    return {
        'page_id': page['id'],
        'match_name': safe_get('Match', 'title'),
        'ai_recommendation': safe_get('AI Recommendation', 'select'),
        'actual_result': safe_get('Actual Result', 'select'),
        'profit_loss': safe_get('Profit/Loss', 'number'),
        'actual_odds': safe_get('Actual Odds', 'number'),
        'confidence': safe_get('AI Confidence', 'number'),
        'predicted_edge': safe_get('Predicted Edge', 'number'),
        'stake_pct': safe_get('Suggested Stake', 'number') or 2.0,
        'match_date': safe_get('Match Date', 'date'),
        'tournament': safe_get('Tournament', 'title') or safe_get('Tournament', 'select')
    }

def calculate_roi_metrics(completed_matches):
    """Calculate ROI metrics from completed matches"""
    if not completed_matches:
        return None
    
    total_bets = 0
    wins = 0
    losses = 0
    pushes = 0
    total_profit_loss = 0.0
    total_stake = 0.0
    
    # Filter only bets (not Skip)
    bets = [m for m in completed_matches if m['ai_recommendation'] != 'Skip']
    
    for match in bets:
        total_bets += 1
        result = match['actual_result']
        profit_loss = match['profit_loss'] or 0.0
        stake = match['stake_pct'] or 2.0
        
        total_stake += stake
        total_profit_loss += profit_loss
        
        if result == 'W':
            wins += 1
        elif result == 'L':
            losses += 1
        elif result == 'PUSH':
            pushes += 1
    
    # Calculate metrics
    win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
    roi = (total_profit_loss / total_stake * 100) if total_stake > 0 else 0
    
    return {
        'total_bets': total_bets,
        'wins': wins,
        'losses': losses,
        'pushes': pushes,
        'win_rate': win_rate,
        'total_profit_loss': total_profit_loss,
        'total_stake': total_stake,
        'roi': roi,
        'avg_profit_per_bet': total_profit_loss / total_bets if total_bets > 0 else 0
    }

def generate_roi_report(metrics, matches):
    """Generate human-readable ROI report"""
    if not metrics:
        return "No completed matches found."
    
    report = []
    report.append("=" * 80)
    report.append("📊 TENNIS AI - ROI REPORT")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Summary
    report.append("📈 SUMMARY")
    report.append("-" * 80)
    report.append(f"Total Bets: {metrics['total_bets']}")
    report.append(f"Wins: {metrics['wins']} | Losses: {metrics['losses']} | Pushes: {metrics['pushes']}")
    report.append(f"Win Rate: {metrics['win_rate']:.1f}%")
    report.append("")
    
    # Financial
    report.append("💰 FINANCIAL")
    report.append("-" * 80)
    report.append(f"Total Stake: ${metrics['total_stake']:.2f}")
    report.append(f"Total P/L: ${metrics['total_profit_loss']:.2f}")
    report.append(f"ROI: {metrics['roi']:.2f}%")
    report.append(f"Avg Profit/Bet: ${metrics['avg_profit_per_bet']:.2f}")
    report.append("")
    
    # Performance by confidence
    if matches:
        confidence_buckets = {'High': [], 'Medium': [], 'Low': []}
        for match in matches:
            conf = match.get('confidence', 0)
            if conf >= 0.7:
                confidence_buckets['High'].append(match)
            elif conf >= 0.5:
                confidence_buckets['Medium'].append(match)
            else:
                confidence_buckets['Low'].append(match)
        
        report.append("🎯 PERFORMANCE BY CONFIDENCE")
        report.append("-" * 80)
        for conf_level, matches_list in confidence_buckets.items():
            if matches_list:
                conf_bets = [m for m in matches_list if m['ai_recommendation'] != 'Skip']
                if conf_bets:
                    conf_wins = sum(1 for m in conf_bets if m['actual_result'] == 'W')
                    conf_pl = sum(m['profit_loss'] or 0 for m in conf_bets)
                    conf_stake = sum(m['stake_pct'] or 2.0 for m in conf_bets)
                    conf_roi = (conf_pl / conf_stake * 100) if conf_stake > 0 else 0
                    report.append(f"{conf_level}: {len(conf_bets)} bets | {conf_wins}W/{len(conf_bets)-conf_wins}L | ROI: {conf_roi:.1f}%")
        report.append("")
    
    # Recent matches
    report.append("📋 RECENT MATCHES (Last 10)")
    report.append("-" * 80)
    recent = sorted([m for m in matches if m['ai_recommendation'] != 'Skip'], 
                    key=lambda x: x.get('match_date', ''), reverse=True)[:10]
    
    for i, match in enumerate(recent, 1):
        result_emoji = "✅" if match['actual_result'] == 'W' else "❌" if match['actual_result'] == 'L' else "➖"
        pl_str = f"${match['profit_loss']:.2f}" if match['profit_loss'] is not None else "N/A"
        report.append(f"{i}. {result_emoji} {match['match_name']}")
        report.append(f"   Bet: {match['ai_recommendation']} | Result: {match['actual_result']} | P/L: {pl_str}")
    
    report.append("")
    report.append("=" * 80)
    
    return "\n".join(report)

def calculate_roi():
    """Main function to calculate ROI"""
    if not NOTION_AVAILABLE:
        print("❌ Notion client not available")
        return
    
    if not NOTION_TOKEN:
        print("❌ NOTION_TOKEN not set")
        return
    
    print("📊 Calculating ROI...")
    print("=" * 70)
    
    notion = Client(auth=NOTION_TOKEN)
    
    # Get completed matches
    completed_pages = get_completed_matches(notion)
    
    if not completed_pages:
        print("⚠️  No completed matches found")
        print("   Run track_results.py first to update match results")
        return
    
    print(f"📈 Found {len(completed_pages)} completed matches\n")
    
    # Extract match data
    matches = [extract_match_data(page) for page in completed_pages]
    
    # Calculate metrics
    metrics = calculate_roi_metrics(matches)
    
    if not metrics:
        print("⚠️  No bets found (all were Skip)")
        return
    
    # Generate report
    report = generate_roi_report(metrics, matches)
    
    # Print report
    print(report)
    
    # Save to file
    report_file = project_root / 'data' / 'tennis_ai' / 'roi_report.txt'
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Report saved to: {report_file}")
    
    return metrics

if __name__ == '__main__':
    calculate_roi()


