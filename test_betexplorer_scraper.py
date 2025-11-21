#!/usr/bin/env python3
"""
🧪 Test BetExplorer Scraper
Tests the BetExplorer scraper, pipeline, and database updater
"""

import asyncio
import logging
import sys
import inspect
from pathlib import Path
from dotenv import load_dotenv
import os
from datetime import datetime

# Load environment variables
env_path = Path(__file__).parent / 'telegram_secrets.env'
if env_path.exists():
    load_dotenv(env_path)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.scrapers.betexplorer_scraper import BetExplorerScraper
from src.pipelines.betexplorer_notion_pipeline import BetExplorerNotionPipeline
from src.notion.betexplorer_database_updater import BetExplorerDatabaseUpdater

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_scraper_initialization():
    """Test BetExplorer scraper initialization"""
    print("\n" + "="*80)
    print("🧪 TEST 1: Scraper Initialization")
    print("="*80)
    
    try:
        config = {
            'request_delay': 2.0,
            'max_retries': 3,
            'timeout': 30
        }
        
        scraper = BetExplorerScraper(config, use_selenium=False)  # Don't use Selenium for quick test
        
        print("✅ Scraper initialized successfully")
        print(f"   Use Selenium: {scraper.use_selenium}")
        print(f"   Request delay: {scraper.request_delay}")
        print(f"   Max retries: {scraper.max_retries}")
        
        return True
        
    except Exception as e:
        print(f"❌ Scraper initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tournament_name_parsing():
    """Test tournament name parsing"""
    print("\n" + "="*80)
    print("🧪 TEST 2: Tournament Name Parsing")
    print("="*80)
    
    try:
        scraper = BetExplorerScraper(use_selenium=False)
        
        test_cases = [
            ("W15 Alcala de Henares, hard", {
                'tier': 'W15',
                'location': 'Alcala de Henares',
                'surface': 'Hard'
            }),
            ("W25 Hua Hin 2, hard", {
                'tier': 'W25',
                'location': 'Hua Hin 2',
                'surface': 'Hard'
            }),
            ("W15 Mogi das Cruzes, clay", {
                'tier': 'W15',
                'location': 'Mogi das Cruzes',
                'surface': 'Clay'
            }),
        ]
        
        all_passed = True
        for name, expected in test_cases:
            result = scraper.parse_tournament_name(name)
            if result:
                tier_match = result['tier'] == expected['tier']
                surface_match = result['surface'] == expected['surface']
                
                if tier_match and surface_match:
                    print(f"✅ '{name}' → Tier: {result['tier']}, Surface: {result['surface']}")
                else:
                    print(f"❌ '{name}' → Expected: {expected}, Got: {result}")
                    all_passed = False
            else:
                print(f"❌ '{name}' → Failed to parse")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Tournament name parsing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_odds_parsing():
    """Test odds parsing (decimal and fractional)"""
    print("\n" + "="*80)
    print("🧪 TEST 3: Odds Parsing")
    print("="*80)
    
    try:
        scraper = BetExplorerScraper(use_selenium=False)
        
        test_cases = [
            ("1.75", 1.75),
            ("2.10", 2.10),
            ("7/4", 2.75),  # 7/4 = 1.75 + 1 = 2.75
            ("3/2", 2.50),  # 3/2 = 1.5 + 1 = 2.5
        ]
        
        all_passed = True
        for odds_text, expected in test_cases:
            result = scraper._parse_odds(odds_text)
            if result:
                if abs(result - expected) < 0.01:  # Allow small floating point differences
                    print(f"✅ '{odds_text}' → {result}")
                else:
                    print(f"❌ '{odds_text}' → Expected: {expected}, Got: {result}")
                    all_passed = False
            else:
                print(f"❌ '{odds_text}' → Failed to parse")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Odds parsing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_find_best_odds():
    """Test best odds selection"""
    print("\n" + "="*80)
    print("🧪 TEST 4: Best Odds Selection")
    print("="*80)
    
    try:
        scraper = BetExplorerScraper(use_selenium=False)
        
        # Sample odds data
        odds_data = [
            {'bookmaker': 'Bet365', 'odds_home': 1.75, 'odds_away': 2.10},
            {'bookmaker': 'Pinnacle', 'odds_home': 1.83, 'odds_away': 2.05},
            {'bookmaker': 'Unibet', 'odds_home': 1.72, 'odds_away': 2.15},
        ]
        
        best_odds = scraper.find_best_odds(odds_data)
        
        expected_p1_odds = 1.83  # Pinnacle has best for player 1
        expected_p2_odds = 2.15  # Unibet has best for player 2
        
        p1_correct = best_odds['player_1']['odds'] == expected_p1_odds
        p2_correct = best_odds['player_2']['odds'] == expected_p2_odds
        p1_bookmaker_correct = best_odds['player_1']['bookmaker'] == 'Pinnacle'
        p2_bookmaker_correct = best_odds['player_2']['bookmaker'] == 'Unibet'
        
        if p1_correct and p2_correct and p1_bookmaker_correct and p2_bookmaker_correct:
            print(f"✅ Best odds P1: {best_odds['player_1']['odds']} ({best_odds['player_1']['bookmaker']})")
            print(f"✅ Best odds P2: {best_odds['player_2']['odds']} ({best_odds['player_2']['bookmaker']})")
            return True
        else:
            print(f"❌ Expected P1: {expected_p1_odds} (Pinnacle), Got: {best_odds['player_1']}")
            print(f"❌ Expected P2: {expected_p2_odds} (Unibet), Got: {best_odds['player_2']}")
            return False
        
    except Exception as e:
        print(f"❌ Best odds selection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_match_validation():
    """Test match validation"""
    print("\n" + "="*80)
    print("🧪 TEST 5: Match Validation")
    print("="*80)
    
    try:
        scraper = BetExplorerScraper(use_selenium=False)
        
        # Valid match
        valid_match = {
            'player1': 'Maria Garcia',
            'player2': 'Anna Smith',
            'match_time': '10:00'
        }
        
        # Invalid matches
        invalid_matches = [
            {'player1': '', 'player2': 'Anna Smith'},  # Missing player1
            {'player1': 'Maria Garcia', 'player2': ''},  # Missing player2
            {'player1': 'Maria Garcia', 'player2': 'Maria Garcia'},  # Same player
            {'player1': 'vs', 'player2': 'Anna Smith'},  # Invalid name
        ]
        
        valid_result = scraper._validate_match(valid_match)
        if not valid_result:
            print(f"❌ Valid match rejected: {valid_match}")
            return False
        print(f"✅ Valid match accepted: {valid_match['player1']} vs {valid_match['player2']}")
        
        all_invalid_rejected = True
        for invalid_match in invalid_matches:
            result = scraper._validate_match(invalid_match)
            if result:
                print(f"❌ Invalid match accepted: {invalid_match}")
                all_invalid_rejected = False
            else:
                print(f"✅ Invalid match rejected: {invalid_match}")
        
        return all_invalid_rejected
        
    except Exception as e:
        print(f"❌ Match validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_pipeline_transformation():
    """Test pipeline data transformation"""
    print("\n" + "="*80)
    print("🧪 TEST 6: Pipeline Data Transformation")
    print("="*80)
    
    try:
        config = {
            'scraper': {
                'target_tiers': ['W15'],
                'request_delay': 2.0,
            },
            'notion': {
                'tennis_prematch_db_id': None,  # Not needed for transformation test
            }
        }
        
        pipeline = BetExplorerNotionPipeline(config)
        
        # Sample match data from scraper
        sample_match = {
            'match_id': 'test_match_001',
            'tournament': 'W15 Alcala de Henares, hard',
            'tier': 'W15',
            'location': 'Alcala de Henares',
            'surface': 'hard',
            'player1': 'Maria Garcia',
            'player2': 'Anna Smith',
            'match_time': '10:00',
            'best_odds_p1': 1.83,
            'bookmaker_p1': 'Pinnacle',
            'best_odds_p2': 2.15,
            'bookmaker_p2': 'Unibet',
            'data_source': 'BetExplorer',
            'scraped_at': datetime.now().isoformat()
        }
        
        notion_data = pipeline.transform_match_to_notion(sample_match)
        
        # Check required fields
        required_fields = [
            'Turnaus', 'Pelaaja A nimi', 'Pelaaja B nimi', 'Päivämäärä',
            'Match Status', 'Kenttä', 'Tournament Tier',
            'Best Odds P1', 'Bookmaker P1', 'Best Odds P2', 'Bookmaker P2',
            'Data Source'
        ]
        
        missing_fields = [f for f in required_fields if f not in notion_data['properties']]
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
        
        print("✅ All required fields present!")
        print(f"   Title: {notion_data['title']}")
        print("\n   Properties:")
        for key in required_fields:
            prop = notion_data['properties'].get(key)
            if prop:
                if 'select' in prop:
                    print(f"      {key}: {prop['select']['name']}")
                elif 'rich_text' in prop:
                    print(f"      {key}: {prop['rich_text'][0]['text']['content']}")
                elif 'number' in prop or 'number' in str(prop):
                    # Number property
                    if 'number' in prop:
                        print(f"      {key}: {prop['number']}")
                    else:
                        # It's a number field, check the value
                        print(f"      {key}: {prop}")
                elif 'date' in prop:
                    print(f"      {key}: {prop['date']['start']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline transformation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_updater_initialization():
    """Test database updater initialization"""
    print("\n" + "="*80)
    print("🧪 TEST 7: Database Updater Initialization")
    print("="*80)
    
    try:
        updater = BetExplorerDatabaseUpdater()
        
        print("✅ Database updater initialized successfully")
        
        # Check if it has the methods we need
        required_methods = [
            'add_best_odds_properties',
            'add_data_source_property',
            'add_odds_advantage_formula',
            'update_all_properties'
        ]
        
        missing_methods = [m for m in required_methods if not hasattr(updater, m)]
        
        if missing_methods:
            print(f"❌ Missing required methods: {missing_methods}")
            return False
        
        print("✅ All required methods present!")
        
        return True
        
    except Exception as e:
        print(f"❌ Database updater initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🎯 BETEXPLORER SCRAPER - COMPREHENSIVE TESTS")
    print("="*80)
    
    tests = [
        ("Scraper Initialization", test_scraper_initialization),
        ("Tournament Name Parsing", test_tournament_name_parsing),
        ("Odds Parsing", test_odds_parsing),
        ("Best Odds Selection", test_find_best_odds),
        ("Match Validation", test_match_validation),
        ("Pipeline Transformation", test_pipeline_transformation),
        ("Database Updater Initialization", test_database_updater_initialization),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            if inspect.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The BetExplorer scraper is working correctly.")
        print("\nNext steps:")
        print("1. Test with real website (use Selenium): python src/scrapers/betexplorer_scraper.py")
        print("2. Update Notion database schema: python -m src.notion.betexplorer_database_updater")
        print("3. Run full pipeline: python run_betexplorer_scraper.py")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

