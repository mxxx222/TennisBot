#!/usr/bin/env python3
"""
🎾 TENNIS SCRAPING EXAMPLE
=========================

Example script demonstrating how to use the enhanced live betting scraper
with the TennisBot infrastructure.

This script shows:
- How to scrape live matches
- How to scrape upcoming matches  
- How to save data in different formats
- How to get summary statistics

Usage:
    python example_scraping.py
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / 'src' / 'scrapers'))

try:
    from live_betting_scraper import LiveBettingScraper, scrape_live_tennis_matches, scrape_upcoming_tennis_matches
    print("✅ Successfully imported live betting scraper")
except ImportError as e:
    print(f"❌ Failed to import scraper: {e}")
    print("Make sure you're in the virtual environment and all packages are installed")
    sys.exit(1)

def demo_live_scraping():
    """Demonstrate live match scraping"""
    print("\n" + "="*60)
    print("🔴 LIVE MATCHES SCRAPING DEMO")
    print("="*60)
    
    try:
        # Method 1: Using convenience function
        print("\n📊 Method 1: Using convenience function...")
        live_matches = scrape_live_tennis_matches(max_matches=10)
        
        if live_matches:
            print(f"✅ Found {len(live_matches)} live matches")
            
            # Display first few matches
            for i, match in enumerate(live_matches[:3], 1):
                print(f"\n🎾 Match {i}:")
                print(f"   Players: {match.home_team} vs {match.away_team}")
                print(f"   Status: {match.status}")
                print(f"   Score: {match.score or 'N/A'}")
                print(f"   Odds: {match.home_odds} / {match.away_odds}")
                print(f"   Source: {match.source}")
        else:
            print("❌ No live matches found")
            
    except Exception as e:
        print(f"❌ Error in live scraping demo: {e}")

def demo_upcoming_scraping():
    """Demonstrate upcoming match scraping"""
    print("\n" + "="*60)
    print("⏰ UPCOMING MATCHES SCRAPING DEMO")
    print("="*60)
    
    try:
        # Method 2: Using scraper class directly
        print("\n📊 Method 2: Using scraper class directly...")
        
        with LiveBettingScraper() as scraper:
            upcoming_matches = scraper.scrape_upcoming_matches(max_matches=15)
            
            if upcoming_matches:
                print(f"✅ Found {len(upcoming_matches)} upcoming matches")
                
                # Display first few matches
                for i, match in enumerate(upcoming_matches[:5], 1):
                    print(f"\n🎾 Match {i}:")
                    print(f"   Players: {match.home_team} vs {match.away_team}")
                    print(f"   League: {match.league}")
                    print(f"   Time: {match.start_time or 'TBD'}")
                    print(f"   Source: {match.source}")
                
                # Save data
                print(f"\n💾 Saving data...")
                csv_file = scraper.save_to_csv(upcoming_matches, "demo_upcoming_matches.csv")
                json_file = scraper.save_to_json(upcoming_matches, "demo_upcoming_matches.json")
                
                print(f"   📄 CSV saved: {csv_file}")
                print(f"   📄 JSON saved: {json_file}")
                
                # Get statistics
                stats = scraper.get_summary_stats(upcoming_matches)
                print(f"\n📊 Summary Statistics:")
                for key, value in stats.items():
                    if isinstance(value, list):
                        print(f"   {key}: {', '.join(map(str, value))}")
                    elif isinstance(value, float):
                        print(f"   {key}: {value:.2f}")
                    else:
                        print(f"   {key}: {value}")
            else:
                print("❌ No upcoming matches found")
                
    except Exception as e:
        print(f"❌ Error in upcoming scraping demo: {e}")

def demo_comprehensive_scraping():
    """Demonstrate comprehensive scraping with both live and upcoming matches"""
    print("\n" + "="*60)
    print("🎯 COMPREHENSIVE SCRAPING DEMO")
    print("="*60)
    
    try:
        with LiveBettingScraper() as scraper:
            print("\n📊 Scraping both live and upcoming matches...")
            
            # Scrape live matches
            live_matches = scraper.scrape_live_matches(max_matches=20)
            print(f"🔴 Live matches: {len(live_matches)}")
            
            # Scrape upcoming matches
            upcoming_matches = scraper.scrape_upcoming_matches(max_matches=30)
            print(f"⏰ Upcoming matches: {len(upcoming_matches)}")
            
            # Combine all matches
            all_matches = live_matches + upcoming_matches
            print(f"📊 Total matches: {len(all_matches)}")
            
            if all_matches:
                # Save combined data
                csv_file = scraper.save_to_csv(all_matches, "demo_all_matches.csv")
                json_file = scraper.save_to_json(all_matches, "demo_all_matches.json")
                
                print(f"\n💾 Combined data saved:")
                print(f"   📄 CSV: {csv_file}")
                print(f"   📄 JSON: {json_file}")
                
                # Comprehensive statistics
                stats = scraper.get_summary_stats(all_matches)
                print(f"\n📊 Comprehensive Statistics:")
                print(f"   Total matches: {stats.get('total_matches', 0)}")
                print(f"   Live matches: {stats.get('live_matches', 0)}")
                print(f"   Upcoming matches: {stats.get('upcoming_matches', 0)}")
                print(f"   Matches with odds: {stats.get('matches_with_odds', 0)}")
                print(f"   Unique sources: {stats.get('unique_sources', 0)}")
                print(f"   Average home odds: {stats.get('avg_home_odds', 0):.2f}")
                print(f"   Average away odds: {stats.get('avg_away_odds', 0):.2f}")
                
                # Show leagues
                leagues = stats.get('leagues', [])
                if leagues:
                    print(f"   Leagues covered: {', '.join(leagues)}")
                
                # Show some interesting matches
                print(f"\n🎯 Interesting matches:")
                
                # Matches with good odds
                odds_matches = [m for m in all_matches if m.home_odds and m.away_odds]
                if odds_matches:
                    # Sort by odds difference (closest matches)
                    odds_matches.sort(key=lambda x: abs(x.home_odds - x.away_odds))
                    
                    print(f"\n   🔥 Closest odds (most competitive):")
                    for match in odds_matches[:3]:
                        odds_diff = abs(match.home_odds - match.away_odds)
                        print(f"      {match.home_team} vs {match.away_team}")
                        print(f"      Odds: {match.home_odds} / {match.away_odds} (diff: {odds_diff:.2f})")
                
                # Live matches with scores
                live_with_scores = [m for m in live_matches if m.score]
                if live_with_scores:
                    print(f"\n   ⚡ Live matches with scores:")
                    for match in live_with_scores[:3]:
                        print(f"      {match.home_team} vs {match.away_team}: {match.score}")
            
            else:
                print("❌ No matches found in comprehensive scraping")
                
    except Exception as e:
        print(f"❌ Error in comprehensive scraping demo: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main demo function"""
    print("🎾 TENNIS BOT SCRAPING DEMONSTRATION")
    print("=" * 60)
    print("This demo will show you how to use the enhanced live betting scraper")
    print("with anti-detection features and comprehensive data collection.")
    print("=" * 60)
    
    # Check if we're in the virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
    else:
        print("⚠️  Warning: Not in virtual environment. Make sure to activate it first:")
        print("   source venv/bin/activate")
    
    try:
        # Run all demos
        demo_live_scraping()
        demo_upcoming_scraping()
        demo_comprehensive_scraping()
        
        print("\n" + "="*60)
        print("✅ DEMO COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\n📁 Check the 'data' directory for saved files:")
        print("   - demo_upcoming_matches.csv")
        print("   - demo_upcoming_matches.json") 
        print("   - demo_all_matches.csv")
        print("   - demo_all_matches.json")
        
        print("\n🚀 Next steps:")
        print("   1. Integrate this scraper into your main TennisBot workflow")
        print("   2. Set up scheduled scraping with the automated_scheduler.py")
        print("   3. Add the scraped data to your AI analysis pipeline")
        print("   4. Configure proxy rotation for production use")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
