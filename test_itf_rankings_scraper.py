#!/usr/bin/env python3
"""
🧪 Test ITF Rankings Scraper
Tests the ITF Rankings scraper with mocked Playwright and Notion API
"""

import sys
import unittest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the scraper module
from src.scrapers.itf_rankings_scraper import (
    scrape_itf_rankings,
    update_player_cards,
    main
)


class TestITFRankingsScraper(unittest.TestCase):
    """Test ITF Rankings Scraper"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_rankings = [
            {'rank': 1, 'name': 'Emma Smith'},
            {'rank': 2, 'name': 'Anna Johnson'},
            {'rank': 3, 'name': 'Maria Garcia'},
        ]
    
    @patch('playwright.sync_api.sync_playwright')
    @patch('src.scrapers.itf_rankings_scraper.PLAYWRIGHT_AVAILABLE', True)
    def test_scrape_itf_rankings_success(self, mock_playwright):
        """Test successful scraping of ITF rankings"""
        # Mock Playwright browser
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        
        # Mock HTML content with rankings
        mock_html = """
        <html>
        <body>
        <table>
        <tr><td>1</td><td>Emma Smith</td></tr>
        <tr><td>2</td><td>Anna Johnson</td></tr>
        <tr><td>3</td><td>Maria Garcia</td></tr>
        </table>
        </body>
        </html>
        """
        
        mock_page.content.return_value = mock_html
        mock_context.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_context
        mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
        
        # Run scraper
        result = scrape_itf_rankings()
        
        # Verify results
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        
        # Verify browser was used
        mock_page.goto.assert_called_once()
        mock_page.content.assert_called_once()
        mock_browser.close.assert_called_once()
    
    @patch('src.scrapers.itf_rankings_scraper.PLAYWRIGHT_AVAILABLE', False)
    def test_scrape_itf_rankings_no_playwright(self):
        """Test scraping when Playwright is not available"""
        result = scrape_itf_rankings()
        self.assertEqual(result, [])
    
    @patch('notion_client.Client')
    def test_update_player_cards_success(self, mock_client_class):
        """Test successful update of Player Cards"""
        # Mock Notion client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock database query response
        mock_response = {
            'results': [
                {
                    'id': 'page_id_1',
                    'properties': {
                        'Player Name': {
                            'title': [{'plain_text': 'Emma Smith'}]
                        }
                    }
                }
            ]
        }
        mock_client.databases.query.return_value = mock_response
        
        # Run update
        update_player_cards(self.sample_rankings, mock_client, 'test_db_id')
        
        # Verify Notion API was called
        self.assertGreater(mock_client.databases.query.call_count, 0)
        self.assertGreater(mock_client.pages.update.call_count, 0)
    
    @patch('notion_client.Client')
    def test_update_player_cards_no_match(self, mock_client_class):
        """Test update when player is not found in database"""
        # Mock Notion client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock empty database query response
        mock_response = {'results': []}
        mock_client.databases.query.return_value = mock_response
        
        # Run update
        update_player_cards(self.sample_rankings, mock_client, 'test_db_id')
        
        # Verify query was called but no updates
        self.assertGreater(mock_client.databases.query.call_count, 0)
        # No updates should be made if no matches found
        self.assertEqual(mock_client.pages.update.call_count, 0)
    
    def test_update_player_cards_no_client(self):
        """Test update when Notion client is None"""
        # Should not crash
        update_player_cards(self.sample_rankings, None, 'test_db_id')
    
    @patch('src.scrapers.itf_rankings_scraper.scrape_itf_rankings')
    @patch('src.scrapers.itf_rankings_scraper.update_player_cards')
    @patch('notion_client.Client')
    @patch('src.scrapers.itf_rankings_scraper.NOTION_TOKEN', 'test_token')
    @patch('src.scrapers.itf_rankings_scraper.PLAYER_CARDS_DB_ID', 'test_db_id')
    @patch('src.scrapers.itf_rankings_scraper.PLAYWRIGHT_AVAILABLE', True)
    @patch('src.scrapers.itf_rankings_scraper.NOTION_AVAILABLE', True)
    def test_main_success(self, mock_client_class, mock_update, mock_scrape):
        """Test main function with successful execution"""
        # Mock scraper to return sample rankings
        mock_scrape.return_value = self.sample_rankings
        
        # Mock Notion client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Run main
        main()
        
        # Verify functions were called
        mock_scrape.assert_called_once()
        mock_update.assert_called_once()
    
    @patch('src.scrapers.itf_rankings_scraper.PLAYWRIGHT_AVAILABLE', False)
    def test_main_no_playwright(self):
        """Test main when Playwright is not available"""
        # Should exit early without crashing
        main()
    
    @patch('src.scrapers.itf_rankings_scraper.NOTION_TOKEN', None)
    @patch('src.scrapers.itf_rankings_scraper.PLAYWRIGHT_AVAILABLE', True)
    @patch('src.scrapers.itf_rankings_scraper.NOTION_AVAILABLE', True)
    def test_main_no_token(self):
        """Test main when NOTION_TOKEN is not set"""
        # Should exit early without crashing
        main()


class TestITFRankingsDataParsing(unittest.TestCase):
    """Test ITF Rankings data parsing logic"""
    
    def test_ranking_data_structure(self):
        """Test that ranking data has correct structure"""
        ranking = {'rank': 1, 'name': 'Emma Smith'}
        
        self.assertIn('rank', ranking)
        self.assertIn('name', ranking)
        self.assertIsInstance(ranking['rank'], int)
        self.assertIsInstance(ranking['name'], str)
        self.assertGreater(ranking['rank'], 0)
        self.assertGreater(len(ranking['name']), 0)
    
    def test_ranking_name_cleaning(self):
        """Test ranking name cleaning logic"""
        # This tests the regex pattern used in the scraper
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
    print("🧪 ITF RANKINGS SCRAPER - TESTS")
    print("="*80 + "\n")
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestITFRankingsScraper))
    suite.addTests(loader.loadTestsFromTestCase(TestITFRankingsDataParsing))
    
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

