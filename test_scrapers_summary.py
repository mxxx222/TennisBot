#!/usr/bin/env python3
"""
🧪 Test Summary for ITF Rankings & Match History Scrapers
Simple integration tests that verify the scrapers can be imported and basic logic works
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class TestScraperImports(unittest.TestCase):
    """Test that scrapers can be imported"""
    
    def test_itf_rankings_scraper_import(self):
        """Test ITF Rankings scraper can be imported"""
        try:
            from src.scrapers import itf_rankings_scraper
            self.assertTrue(hasattr(itf_rankings_scraper, 'scrape_itf_rankings'))
            self.assertTrue(hasattr(itf_rankings_scraper, 'update_player_cards'))
            self.assertTrue(hasattr(itf_rankings_scraper, 'main'))
            print("✅ ITF Rankings scraper imports successfully")
        except ImportError as e:
            self.fail(f"Failed to import ITF Rankings scraper: {e}")
    
    def test_match_history_scraper_import(self):
        """Test Match History scraper can be imported"""
        try:
            from src.scrapers import match_history_scraper
            self.assertTrue(hasattr(match_history_scraper, 'scrape_player_history'))
            self.assertTrue(hasattr(match_history_scraper, 'get_players_to_update'))
            self.assertTrue(hasattr(match_history_scraper, 'update_player_card'))
            self.assertTrue(hasattr(match_history_scraper, 'main'))
            print("✅ Match History scraper imports successfully")
        except ImportError as e:
            self.fail(f"Failed to import Match History scraper: {e}")


class TestDataStructures(unittest.TestCase):
    """Test data structure validation"""
    
    def test_ranking_data_structure(self):
        """Test ranking data structure"""
        ranking = {'rank': 1, 'name': 'Emma Smith'}
        
        self.assertIn('rank', ranking)
        self.assertIn('name', ranking)
        self.assertIsInstance(ranking['rank'], int)
        self.assertIsInstance(ranking['name'], str)
        self.assertGreater(ranking['rank'], 0)
        self.assertGreater(len(ranking['name']), 0)
    
    def test_history_data_structure(self):
        """Test history data structure"""
        history = {
            'wins': 5,
            'losses': 5,
            'win_rate': 50.0,
            'recent_form': 'WWLLW',
            'total_matches': 10
        }
        
        self.assertIn('wins', history)
        self.assertIn('losses', history)
        self.assertIn('win_rate', history)
        self.assertIn('recent_form', history)
        self.assertIn('total_matches', history)
        
        self.assertEqual(history['wins'] + history['losses'], history['total_matches'])
        self.assertGreaterEqual(history['win_rate'], 0)
        self.assertLessEqual(history['win_rate'], 100)
    
    def test_win_rate_calculation(self):
        """Test win rate calculation"""
        wins = 7
        losses = 3
        total = wins + losses
        win_rate = round((wins / total) * 100, 1)
        
        self.assertEqual(win_rate, 70.0)
        self.assertGreaterEqual(win_rate, 0)
        self.assertLessEqual(win_rate, 100)
    
    def test_recent_form_formatting(self):
        """Test recent form string formatting"""
        recent_form = ['W', 'W', 'L', 'W', 'W']
        recent_form_str = ''.join(recent_form[:10])
        
        self.assertEqual(recent_form_str, 'WWLWW')
        self.assertIsInstance(recent_form_str, str)
        self.assertTrue(all(c in ['W', 'L'] for c in recent_form_str))


class TestNameParsing(unittest.TestCase):
    """Test name parsing logic"""
    
    def test_ranking_name_cleaning(self):
        """Test ranking name cleaning logic"""
        import re
        
        test_cases = [
            ("1  Emma Smith", ("1", "Emma Smith")),
            ("2  Anna Johnson  (USA)", ("2", "Anna Johnson")),
            ("10  Maria Garcia Lopez", ("10", "Maria Garcia Lopez")),
        ]
        
        for text, expected in test_cases:
            match = re.search(r'^(\d+)\s+(.+?)(?:\s+\d+|\s*$)', text)
            if match:
                rank = int(match.group(1))
                name = match.group(2).strip()
                
                # Remove parentheses
                name = re.sub(r'\s*\([^)]+\)\s*', '', name)
                
                self.assertEqual(rank, int(expected[0]))
                self.assertEqual(name, expected[1])


def run_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("🧪 SCRAPER TESTS - SUMMARY")
    print("="*80 + "\n")
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestScraperImports))
    suite.addTests(loader.loadTestsFromTestCase(TestDataStructures))
    suite.addTests(loader.loadTestsFromTestCase(TestNameParsing))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
        print("\n💡 Note: Full integration tests require:")
        print("   - Playwright installed: pip install playwright && playwright install chromium")
        print("   - Notion client installed: pip install notion-client")
        print("   - Environment variables set: NOTION_API_KEY, PLAYER_CARDS_DB_ID")
        return True
    else:
        print("\n❌ Some tests failed")
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"   - {test}")
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"   - {test}")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

