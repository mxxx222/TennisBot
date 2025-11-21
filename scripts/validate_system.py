#!/usr/bin/env python3
"""
Daily System Validation
========================

Checks all workflows and database states after morning automation.

Usage:
    python scripts/validate_system.py
    
Output:
    - Workflow statuses (✅/❌)
    - Database statistics
    - Health score (0-100)
    - Issues found (if any)
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / 'telegram_secrets.env'
if env_path.exists():
    load_dotenv(env_path)

# Notion API
try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    print("❌ ERROR: notion-client not installed")
    print("Install with: pip install notion-client")
    sys.exit(1)

# Configuration
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
RAW_MATCH_FEED_DB_ID = os.getenv("RAW_MATCH_FEED_DB_ID")
TENNIS_PREMATCH_DB_ID = os.getenv("TENNIS_PREMATCH_DB_ID") or os.getenv("NOTION_TENNIS_PREMATCH_DB_ID")
PLAYER_CARDS_DB_ID = os.getenv("PLAYER_CARDS_DB_ID") or os.getenv("NOTION_ITF_PLAYER_CARDS_DB_ID")

# Expected workflows (exact names from GitHub Actions workflow files)
# Note: These must match the 'name:' field in .github/workflows/*.yml files
EXPECTED_WORKFLOWS = [
    "Daily Tennis Abstract ELO Scraper",  # tennis_abstract_elo.yml
    "Daily Momentum Calculator",  # daily-momentum.yml
    "BetExplorer Scraper",  # betexplorer-scraper.yml
    "AI Match Filter",  # ai-match-filter.yml
    "Weather Enrichment"  # weather-enricher.yml
]


class SystemValidator:
    """
    Validates all production systems and databases.
    """
    
    def __init__(self):
        if not NOTION_TOKEN:
            print("❌ ERROR: NOTION_TOKEN not set")
            sys.exit(1)
        
        try:
            self.client = Client(auth=NOTION_TOKEN)
        except Exception as e:
            print(f"❌ ERROR: Failed to initialize Notion client: {e}")
            sys.exit(1)
        
        self.issues = []
        self.health_score = 100
        
    def check_github_workflows(self) -> Dict[str, str]:
        """
        Check status of recent GitHub Actions runs.
        
        Returns:
            Dictionary mapping workflow names to status strings
        """
        print("\n🔍 Checking GitHub Actions workflows...")
        
        try:
            # Get recent workflow runs using gh CLI
            result = subprocess.run(
                ["gh", "run", "list", "--limit", "10", "--json", "name,status,conclusion,createdAt,workflowName"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            
            runs = json.loads(result.stdout)
            
            # Group by workflow name (get most recent for each)
            latest_runs = {}
            for run in runs:
                # Use workflowName (from gh CLI JSON) or name field
                # The 'name' field is the workflow run title, 'workflowName' is the workflow file name
                workflow_name = run.get("workflowName") or run.get("name", "")
                if workflow_name and workflow_name not in latest_runs:
                    latest_runs[workflow_name] = run
                elif not workflow_name:
                    # Fallback: try to match by checking if any expected workflow name matches
                    # This handles cases where the JSON format is different
                    for expected in EXPECTED_WORKFLOWS:
                        if expected.lower() in str(run).lower():
                            latest_runs[expected] = run
                            break
            
            # Check expected workflows
            workflow_status = {}
            for workflow in EXPECTED_WORKFLOWS:
                if workflow in latest_runs:
                    run = latest_runs[workflow]
                    conclusion = run.get("conclusion") or run.get("status", "")
                    status = run.get("status", "")
                    
                    # Determine status
                    if conclusion == "success" or (not conclusion and status == "completed"):
                        workflow_status[workflow] = "✅ Success"
                        print(f"  ✅ {workflow}: Success")
                    elif conclusion == "failure":
                        workflow_status[workflow] = "❌ Failed"
                        print(f"  ❌ {workflow}: FAILED")
                        self.issues.append(f"{workflow} failed")
                        self.health_score -= 20
                    elif status == "in_progress" or status == "queued":
                        workflow_status[workflow] = f"⚠️ {status.title()}"
                        print(f"  ⚠️ {workflow}: {status.title()}")
                        # Don't penalize if still running
                    else:
                        workflow_status[workflow] = f"⚠️ {conclusion or status}"
                        print(f"  ⚠️ {workflow}: {conclusion or status}")
                        self.issues.append(f"{workflow} status: {conclusion or status}")
                        self.health_score -= 10
                else:
                    workflow_status[workflow] = "❓ Not found"
                    print(f"  ❓ {workflow}: Not found in recent runs")
                    self.issues.append(f"{workflow} not found in recent runs")
                    self.health_score -= 15
            
            return workflow_status
            
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Error running gh command: {e}")
            print(f"  📝 Output: {e.stdout}")
            print(f"  📝 Error: {e.stderr}")
            self.issues.append("GitHub CLI error - gh command failed")
            self.health_score -= 30
            return {}
        except FileNotFoundError:
            print(f"  ⚠️ WARNING: gh CLI not found (skipping workflow checks)")
            print(f"  💡 Install: brew install gh (Mac) or apt-get install gh (Linux)")
            self.issues.append("GitHub CLI not installed - workflow checks skipped")
            self.health_score -= 10
            return {}
        except subprocess.TimeoutExpired:
            print(f"  ❌ ERROR: gh command timed out")
            self.issues.append("GitHub CLI timeout")
            self.health_score -= 15
            return {}
        except json.JSONDecodeError as e:
            print(f"  ❌ Error parsing gh output: {e}")
            self.issues.append("GitHub CLI output parse error")
            self.health_score -= 15
            return {}
    
    def check_raw_match_feed(self) -> Dict:
        """
        Check Raw Match Feed database status.
        
        Returns:
            Dictionary with statistics
        """
        print("\n🔍 Checking Raw Match Feed...")
        
        if not RAW_MATCH_FEED_DB_ID:
            print("  ⚠️ RAW_MATCH_FEED_DB_ID not set (skipping)")
            self.issues.append("RAW_MATCH_FEED_DB_ID not configured")
            self.health_score -= 10
            return {}
        
        try:
            # Count total matches
            total_response = self.client.databases.query(
                database_id=RAW_MATCH_FEED_DB_ID,
                page_size=100  # Get first page to check connection
            )
            total_matches = len(total_response.get("results", []))
            
            # Check if there are more pages
            has_more = total_response.get("has_more", False)
            if has_more:
                # For now, just note that there are more
                print(f"  ℹ️ INFO: More than 100 matches (getting full count...)")
            
            # Count unprocessed matches
            unprocessed_response = self.client.databases.query(
                database_id=RAW_MATCH_FEED_DB_ID,
                filter={
                    "property": "AI Processed",
                    "checkbox": {"equals": False}
                },
                page_size=100
            )
            unprocessed_count = len(unprocessed_response.get("results", []))
            
            # Count approved matches
            approved_response = self.client.databases.query(
                database_id=RAW_MATCH_FEED_DB_ID,
                filter={
                    "property": "AI Approved",
                    "checkbox": {"equals": True}
                },
                page_size=100
            )
            approved_count = len(approved_response.get("results", []))
            
            print(f"  📊 Total matches: {total_matches}{'+' if has_more else ''}")
            print(f"  ⏳ Unprocessed: {unprocessed_count}")
            print(f"  ✅ Approved: {approved_count}")
            
            # Validate
            if unprocessed_count > 10:
                self.issues.append(f"Too many unprocessed matches: {unprocessed_count}")
                self.health_score -= 10
                print(f"  ⚠️ WARNING: {unprocessed_count} unprocessed matches (should be ~0)")
            elif unprocessed_count > 0:
                print(f"  ⚠️ INFO: {unprocessed_count} unprocessed matches (acceptable)")
            else:
                print(f"  ✅ Unprocessed queue healthy")
            
            if total_matches == 0:
                print(f"  ℹ️ INFO: Database is empty (may be first run)")
            
            approval_rate = (approved_count / total_matches * 100) if total_matches > 0 else 0
            
            return {
                "total": total_matches,
                "unprocessed": unprocessed_count,
                "approved": approved_count,
                "approval_rate": f"{approval_rate:.1f}%" if total_matches > 0 else "N/A"
            }
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.issues.append(f"Raw Match Feed error: {str(e)}")
            self.health_score -= 20
            return {}
    
    def check_tennis_prematch_db(self) -> Dict:
        """
        Check Tennis Prematch DB status.
        
        Returns:
            Dictionary with statistics
        """
        print("\n🔍 Checking Tennis Prematch DB...")
        
        if not TENNIS_PREMATCH_DB_ID:
            print("  ⚠️ TENNIS_PREMATCH_DB_ID not set (skipping)")
            self.issues.append("TENNIS_PREMATCH_DB_ID not configured")
            self.health_score -= 10
            return {}
        
        try:
            # Count total matches
            total_response = self.client.databases.query(
                database_id=TENNIS_PREMATCH_DB_ID,
                page_size=100
            )
            total_matches = len(total_response.get("results", []))
            
            # Count matches with ROI Score (check for different possible field names)
            try:
                roi_response = self.client.databases.query(
                    database_id=TENNIS_PREMATCH_DB_ID,
                    filter={
                        "property": "ROI Score",
                        "number": {"is_not_empty": True}
                    },
                    page_size=100
                )
                roi_count = len(roi_response.get("results", []))
            except:
                # ROI Score field might not exist or have different name
                roi_count = 0
                print(f"  ℹ️ INFO: ROI Score field not found or empty")
            
            # Count matches with weather data
            try:
                weather_response = self.client.databases.query(
                    database_id=TENNIS_PREMATCH_DB_ID,
                    filter={
                        "property": "Weather Temp",
                        "number": {"is_not_empty": True}
                    },
                    page_size=100
                )
                weather_count = len(weather_response.get("results", []))
            except:
                weather_count = 0
                print(f"  ℹ️ INFO: Weather Temp field not found or empty")
            
            print(f"  📊 Total matches: {total_matches}")
            print(f"  🎯 With ROI Score: {roi_count}")
            print(f"  ☁️ With weather data: {weather_count}")
            
            # Calculate averages if data exists
            if roi_count > 0 and "results" in roi_response:
                try:
                    roi_values = [
                        r["properties"]["ROI Score"]["number"] 
                        for r in roi_response["results"] 
                        if r.get("properties", {}).get("ROI Score", {}).get("number")
                    ]
                    if roi_values:
                        avg_roi = sum(roi_values) / len(roi_values)
                        print(f"  📈 Average ROI Score: {avg_roi:.1f}")
                except:
                    pass
            
            # Validate weather coverage
            if total_matches > 0:
                weather_coverage = weather_count / total_matches * 100
                print(f"  🌤️ Weather coverage: {weather_coverage:.1f}%")
                
                if weather_coverage < 80 and weather_count > 0:
                    # Only warn if some weather data exists but coverage is low
                    self.issues.append(f"Low weather coverage: {weather_coverage:.1f}%")
                    self.health_score -= 5
                elif weather_coverage == 0 and total_matches > 5:
                    # No weather data at all might indicate an issue
                    print(f"  ⚠️ INFO: No weather data found (may be first run)")
            
            if total_matches == 0:
                print(f"  ℹ️ INFO: Database is empty (may be first run)")
            
            return {
                "total": total_matches,
                "with_roi": roi_count,
                "with_weather": weather_count,
                "weather_coverage": f"{weather_coverage:.1f}%" if total_matches > 0 else "N/A"
            }
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.issues.append(f"Tennis Prematch DB error: {str(e)}")
            self.health_score -= 20
            return {}
    
    def check_player_cards(self) -> Dict:
        """
        Check Player Cards database status.
        
        Returns:
            Dictionary with statistics
        """
        print("\n🔍 Checking Player Cards...")
        
        if not PLAYER_CARDS_DB_ID:
            print("  ⚠️ PLAYER_CARDS_DB_ID not set (skipping)")
            self.issues.append("PLAYER_CARDS_DB_ID not configured")
            self.health_score -= 10
            return {}
        
        try:
            # Count total players
            total_response = self.client.databases.query(
                database_id=PLAYER_CARDS_DB_ID,
                page_size=100
            )
            total_players = len(total_response.get("results", []))
            
            # Count players with ELO (check for different possible field names)
            try:
                elo_response = self.client.databases.query(
                    database_id=PLAYER_CARDS_DB_ID,
                    filter={
                        "property": "Overall ELO",
                        "number": {"is_not_empty": True}
                    },
                    page_size=100
                )
                elo_count = len(elo_response.get("results", []))
            except:
                elo_count = 0
                print(f"  ℹ️ INFO: Overall ELO field not found")
            
            # Count Hot Hand players
            try:
                hot_hand_response = self.client.databases.query(
                    database_id=PLAYER_CARDS_DB_ID,
                    filter={
                        "property": "Hot Hand",
                        "checkbox": {"equals": True}
                    },
                    page_size=100
                )
                hot_hand_count = len(hot_hand_response.get("results", []))
            except:
                hot_hand_count = 0
            
            # Count Rising Talent players
            try:
                rising_response = self.client.databases.query(
                    database_id=PLAYER_CARDS_DB_ID,
                    filter={
                        "property": "Rising Talent",
                        "checkbox": {"equals": True}
                    },
                    page_size=100
                )
                rising_count = len(rising_response.get("results", []))
            except:
                rising_count = 0
            
            print(f"  📊 Total players: {total_players}")
            print(f"  🎾 With ELO: {elo_count}")
            print(f"  🔥 Hot Hand: {hot_hand_count}")
            print(f"  ⭐ Rising Talent: {rising_count}")
            
            # Validate
            if total_players > 0:
                elo_coverage = (elo_count / total_players * 100) if total_players > 0 else 0
                if elo_coverage < 80 and elo_count < 80:
                    self.issues.append(f"Low ELO coverage: {elo_count}/{total_players} ({elo_coverage:.1f}%)")
                    self.health_score -= 5
                else:
                    print(f"  ✅ ELO coverage healthy ({elo_coverage:.1f}%)")
            
            if hot_hand_count < 5 and total_players > 50:
                print(f"  ℹ️ INFO: Few Hot Hand players ({hot_hand_count})")
            
            return {
                "total": total_players,
                "with_elo": elo_count,
                "hot_hand": hot_hand_count,
                "rising_talent": rising_count
            }
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.issues.append(f"Player Cards error: {str(e)}")
            self.health_score -= 15
            return {}
    
    def generate_report(self, workflow_status: Dict, raw_feed_stats: Dict, 
                       prematch_stats: Dict, player_stats: Dict):
        """
        Generate summary report.
        """
        print("\n" + "="*60)
        print("📊 SYSTEM VALIDATION SUMMARY")
        print("="*60)
        print(f"\n🕐 Validation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S EET')}")
        print(f"\n🏥 Overall Health Score: {self.health_score}/100")
        
        # Ensure health score doesn't go negative
        self.health_score = max(0, self.health_score)
        
        if self.health_score >= 90:
            print("   Status: 🟢 EXCELLENT")
        elif self.health_score >= 75:
            print("   Status: 🟡 GOOD")
        elif self.health_score >= 60:
            print("   Status: 🟠 FAIR (needs attention)")
        else:
            print("   Status: 🔴 POOR (immediate action required)")
        
        # Issues
        if self.issues:
            print(f"\n⚠️ Issues Found ({len(self.issues)}):")
            for issue in self.issues:
                print(f"   - {issue}")
        else:
            print(f"\n✅ No issues found!")
        
        # Quick stats
        print(f"\n📈 Quick Stats:")
        successful_workflows = sum(1 for s in workflow_status.values() if "✅" in s)
        print(f"   Workflows: {successful_workflows}/{len(EXPECTED_WORKFLOWS)} successful")
        print(f"   Raw Feed: {raw_feed_stats.get('total', 0)} matches, {raw_feed_stats.get('unprocessed', 0)} unprocessed")
        print(f"   Prematch DB: {prematch_stats.get('total', 0)} matches, {prematch_stats.get('weather_coverage', 'N/A')} weather coverage")
        print(f"   Players: {player_stats.get('with_elo', 0)} with ELO, {player_stats.get('hot_hand', 0)} hot hands")
        
        print("\n" + "="*60)
        
        # Recommendations
        if self.health_score < 90:
            print("\n💡 Recommendations:")
            if any("failed" in issue.lower() for issue in self.issues):
                print("   - Check failed workflow logs: gh run view <run-id> --log")
            if any("unprocessed" in issue.lower() for issue in self.issues):
                print("   - AI Filter may need attention: check RAW_MATCH_FEED_DB_ID")
            if any("weather" in issue.lower() for issue in self.issues):
                print("   - Weather Enricher may need attention: check WEATHER_API_KEY")
            if any("elo" in issue.lower() for issue in self.issues):
                print("   - Tennis Abstract scraper may need attention")
        
        print("\n✅ Validation complete!\n")
    
    def run(self):
        """
        Run full system validation.
        """
        print("🔍 Starting Daily System Validation...")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S EET')}")
        
        # Check all components
        workflow_status = self.check_github_workflows()
        raw_feed_stats = self.check_raw_match_feed()
        prematch_stats = self.check_tennis_prematch_db()
        player_stats = self.check_player_cards()
        
        # Generate report
        self.generate_report(workflow_status, raw_feed_stats, prematch_stats, player_stats)
        
        # Exit code based on health
        if self.health_score >= 75:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure (needs attention)


def main():
    """Main entry point"""
    # Check required environment variables
    missing_vars = []
    if not NOTION_TOKEN:
        missing_vars.append("NOTION_TOKEN")
    
    if missing_vars:
        print("❌ Error: Missing required environment variables")
        print(f"Required: {', '.join(missing_vars)}")
        print("\n💡 Setup:")
        print("1. Add to telegram_secrets.env file")
        print("2. Or export as environment variables")
        sys.exit(1)
    
    validator = SystemValidator()
    validator.run()


if __name__ == "__main__":
    main()

