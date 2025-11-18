#!/usr/bin/env python3
"""
Analytics Dashboard for Live Odds Monitoring
Provides real-time insights and performance tracking
"""

import asyncio
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from storage.odds_database import OddsDatabase
from storage.analytics import LiveAnalytics
from config.live_config import LiveMonitoringConfig

def print_header(title: str):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_section(title: str):
    """Print formatted section header"""
    print(f"\n📊 {title}")
    print("-" * 40)

def format_percentage(value: float) -> str:
    """Format percentage with color coding"""
    if value >= 15:
        return f"🟢 {value:.1f}%"
    elif value >= 10:
        return f"🟡 {value:.1f}%"
    elif value >= 5:
        return f"🟠 {value:.1f}%"
    else:
        return f"🔴 {value:.1f}%"

def format_trend(current: float, previous: float) -> str:
    """Format trend indicator"""
    if current > previous:
        return f"📈 +{current - previous:.1f}"
    elif current < previous:
        return f"📉 {current - previous:.1f}"
    else:
        return "➡️ 0.0"

class AnalyticsDashboard:
    """Interactive analytics dashboard"""
    
    def __init__(self):
        self.config = LiveMonitoringConfig()
        self.database = OddsDatabase()
        self.analytics = LiveAnalytics(self.database)
    
    def show_overview(self, days: int = 7):
        """Show system overview"""
        
        print_header("LIVE ODDS MONITOR - ANALYTICS DASHBOARD")
        
        # Get real-time metrics
        real_time = self.analytics.get_real_time_metrics()
        
        print(f"🕐 Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S EET')}")
        print(f"⚡ System Status: {'🟢 ACTIVE' if real_time.get('system_active') else '🟡 STANDBY'}")
        print(f"📊 Analysis Period: Last {days} days")
        
        # Today's activity
        print_section("Today's Activity")
        print(f"Opportunities Detected: {real_time.get('today_opportunities', 0)}")
        print(f"Last Hour Activity: {real_time.get('last_hour_opportunities', 0)}")
        print(f"Average Edge Today: {format_percentage(real_time.get('today_avg_edge', 0))}")
    
    def show_performance_summary(self, days: int = 7):
        """Show performance summary"""
        
        print_section("Performance Summary")
        
        summary = self.database.get_performance_summary(days)
        
        if not summary:
            print("❌ No performance data available")
            return
        
        print(f"Total Bets: {summary.get('total_bets', 0)}")
        print(f"Win Rate: {format_percentage(summary.get('win_rate', 0))}")
        print(f"ROI: {format_percentage(summary.get('roi', 0))}")
        print(f"Total Staked: ${summary.get('total_staked', 0):.2f}")
        print(f"Total Profit: ${summary.get('total_profit', 0):.2f}")
        print(f"Average Odds: {summary.get('avg_odds', 0):.2f}")
        print(f"Average Edge: {format_percentage(summary.get('avg_edge', 0))}")
    
    def show_opportunities_analysis(self, days: int = 7):
        """Show opportunities analysis"""
        
        print_section("Opportunities Analysis")
        
        opportunities = self.database.get_recent_opportunities(days * 24)
        
        if not opportunities:
            print("❌ No opportunities data available")
            return
        
        # Basic stats
        print(f"Total Opportunities: {len(opportunities)}")
        print(f"Opportunities/Day: {len(opportunities) / days:.1f}")
        
        # Urgency breakdown
        urgency_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for opp in opportunities:
            urgency_counts[opp.urgency_level] += 1
        
        print(f"\nUrgency Distribution:")
        for level, count in urgency_counts.items():
            percentage = (count / len(opportunities)) * 100
            print(f"  {level}: {count} ({percentage:.1f}%)")
        
        # League breakdown
        league_counts = {}
        for opp in opportunities:
            league = opp.league.replace('soccer_', '').replace('_', ' ').title()
            league_counts[league] = league_counts.get(league, 0) + 1
        
        print(f"\nTop Leagues:")
        sorted_leagues = sorted(league_counts.items(), key=lambda x: x[1], reverse=True)
        for league, count in sorted_leagues[:5]:
            print(f"  {league}: {count}")
    
    def show_trends_analysis(self, days: int = 7):
        """Show trends analysis"""
        
        print_section("Trends Analysis")
        
        # Compare current period with previous period
        current_summary = self.database.get_performance_summary(days)
        previous_summary = self.database.get_performance_summary(days * 2)
        
        if not current_summary or not previous_summary:
            print("❌ Insufficient data for trend analysis")
            return
        
        current_roi = current_summary.get('roi', 0)
        current_bets = current_summary.get('total_bets', 0)
        current_win_rate = current_summary.get('win_rate', 0)
        
        # Rough estimation of previous period
        prev_roi = previous_summary.get('roi', 0)
        prev_bets = previous_summary.get('total_bets', 0) - current_bets
        prev_win_rate = previous_summary.get('win_rate', 0)
        
        print(f"ROI Trend: {format_percentage(current_roi)} {format_trend(current_roi, prev_roi)}")
        print(f"Volume Trend: {current_bets} bets {format_trend(current_bets, prev_bets)}")
        print(f"Win Rate Trend: {format_percentage(current_win_rate)} {format_trend(current_win_rate, prev_win_rate)}")
    
    def show_recommendations(self, days: int = 7):
        """Show system recommendations"""
        
        print_section("System Recommendations")
        
        report = self.analytics.generate_performance_report(days)
        recommendations = report.get('recommendations', [])
        
        if not recommendations:
            print("✅ No specific recommendations - system performing optimally")
            return
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
    
    def show_database_stats(self):
        """Show database statistics"""
        
        print_section("Database Statistics")
        
        stats = self.database.get_database_stats()
        
        if not stats:
            print("❌ Unable to retrieve database statistics")
            return
        
        print(f"Odds Snapshots: {stats.get('odds_snapshots_count', 0):,}")
        print(f"Odds Movements: {stats.get('odds_movements_count', 0):,}")
        print(f"Value Opportunities: {stats.get('value_opportunities_count', 0):,}")
        print(f"Performance Records: {stats.get('performance_records_count', 0):,}")
        print(f"Database Size: {stats.get('database_size_mb', 0):.1f} MB")
        
        if stats.get('data_range_start') and stats.get('data_range_end'):
            print(f"Data Range: {stats['data_range_start'][:10]} to {stats['data_range_end'][:10]}")
    
    def interactive_mode(self):
        """Run interactive dashboard"""
        
        while True:
            print_header("INTERACTIVE ANALYTICS DASHBOARD")
            print("1. System Overview")
            print("2. Performance Summary (7 days)")
            print("3. Performance Summary (30 days)")
            print("4. Opportunities Analysis")
            print("5. Trends Analysis")
            print("6. System Recommendations")
            print("7. Database Statistics")
            print("8. Export Data")
            print("9. Exit")
            
            try:
                choice = input("\nSelect option (1-9): ").strip()
                
                if choice == '1':
                    self.show_overview()
                elif choice == '2':
                    self.show_performance_summary(7)
                elif choice == '3':
                    self.show_performance_summary(30)
                elif choice == '4':
                    self.show_opportunities_analysis(7)
                elif choice == '5':
                    self.show_trends_analysis(7)
                elif choice == '6':
                    self.show_recommendations(7)
                elif choice == '7':
                    self.show_database_stats()
                elif choice == '8':
                    self.export_data()
                elif choice == '9':
                    print("\n👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid option. Please try again.")
                
                input("\nPress Enter to continue...")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                input("Press Enter to continue...")
    
    def export_data(self):
        """Export analytics data"""
        
        print_section("Data Export")
        
        try:
            days = int(input("Enter number of days to export (default 30): ") or "30")
            
            print("📊 Generating export...")
            data = self.analytics.export_data(days)
            
            if data:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"analytics_export_{timestamp}.json"
                
                with open(filename, 'w') as f:
                    f.write(data)
                
                print(f"✅ Data exported to {filename}")
            else:
                print("❌ Failed to export data")
                
        except ValueError:
            print("❌ Invalid number of days")
        except Exception as e:
            print(f"❌ Export failed: {e}")

def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(description='Live Odds Monitor Analytics Dashboard')
    parser.add_argument('--days', type=int, default=7,
                       help='Number of days for analysis (default: 7)')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Run in interactive mode')
    parser.add_argument('--export', action='store_true',
                       help='Export data and exit')
    
    args = parser.parse_args()
    
    try:
        dashboard = AnalyticsDashboard()
        
        if args.interactive:
            dashboard.interactive_mode()
        elif args.export:
            dashboard.export_data()
        else:
            # Show full dashboard
            dashboard.show_overview(args.days)
            dashboard.show_performance_summary(args.days)
            dashboard.show_opportunities_analysis(args.days)
            dashboard.show_trends_analysis(args.days)
            dashboard.show_recommendations(args.days)
            dashboard.show_database_stats()
    
    except KeyboardInterrupt:
        print("\n👋 Dashboard interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Dashboard error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
