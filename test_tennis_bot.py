#!/usr/bin/env python3
"""
Tests for Tennis Bot functionality.
"""

import unittest
import sys
import os

# Add the parent directory to the path so we can import tennis_bot
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tennis_bot import TennisBot


class TestTennisBot(unittest.TestCase):
    """Test cases for TennisBot class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.bot = TennisBot("Alice", "Bob")
    
    def test_initial_state(self):
        """Test initial state of the tennis bot."""
        self.assertEqual(self.bot.player1, "Alice")
        self.assertEqual(self.bot.player2, "Bob")
        self.assertEqual(self.bot.sets, [0, 0])
        self.assertEqual(self.bot.games, [0, 0])
        self.assertEqual(self.bot.points, [0, 0])
        self.assertFalse(self.bot.match_complete)
        self.assertIsNone(self.bot.winner)
    
    def test_score_display_initial(self):
        """Test score display at start of match."""
        score = self.bot.get_score_display()
        self.assertIn("Alice: 0 sets, 0 games", score)
        self.assertIn("Bob: 0 sets, 0 games", score)
        self.assertIn("0 - 0", score)
    
    def test_point_progression(self):
        """Test tennis point progression (0, 15, 30, 40)."""
        # Test player 1 scoring
        self.bot.win_point(0)
        score = self.bot.get_score_display()
        self.assertIn("15 - 0", score)
        
        self.bot.win_point(0)
        score = self.bot.get_score_display()
        self.assertIn("30 - 0", score)
        
        self.bot.win_point(0)
        score = self.bot.get_score_display()
        self.assertIn("40 - 0", score)
    
    def test_game_win(self):
        """Test winning a game."""
        # Player 1 wins 4 points to win the game
        for _ in range(4):
            self.bot.win_point(0)
        
        self.assertEqual(self.bot.games[0], 1)
        self.assertEqual(self.bot.games[1], 0)
        self.assertEqual(self.bot.points, [0, 0])  # Points reset after game
    
    def test_deuce_situation(self):
        """Test deuce and advantage scenarios."""
        # Both players get to 40 (3 points each)
        for _ in range(3):
            self.bot.win_point(0)
            self.bot.win_point(1)
        
        score = self.bot.get_score_display()
        self.assertIn("Deuce", score)
        
        # Player 1 gets advantage
        self.bot.win_point(0)
        score = self.bot.get_score_display()
        self.assertIn("Advantage Alice", score)
        
        # Back to deuce
        self.bot.win_point(1)
        score = self.bot.get_score_display()
        self.assertIn("Deuce", score)
        
        # Player 2 gets advantage and wins
        self.bot.win_point(1)
        self.bot.win_point(1)
        self.assertEqual(self.bot.games[1], 1)
        self.assertEqual(self.bot.points, [0, 0])
    
    def test_set_win(self):
        """Test winning a set."""
        # Simulate player 1 winning 6 games
        for _ in range(6):
            for _ in range(4):  # 4 points to win each game
                self.bot.win_point(0)
        
        self.assertEqual(self.bot.sets[0], 1)
        self.assertEqual(self.bot.sets[1], 0)
        self.assertEqual(self.bot.games, [0, 0])  # Games reset after set
    
    def test_match_win(self):
        """Test winning a match (2 sets)."""
        # Simulate player 1 winning 2 sets
        for set_num in range(2):
            for game_num in range(6):
                for point_num in range(4):
                    self.bot.win_point(0)
        
        self.assertTrue(self.bot.match_complete)
        self.assertEqual(self.bot.winner, "Alice")
        self.assertEqual(self.bot.sets[0], 2)
    
    def test_reset_match(self):
        """Test resetting match state."""
        # Make some progress
        self.bot.win_point(0)
        self.bot.win_point(1)
        
        # Reset and verify
        self.bot.reset_match()
        self.assertEqual(self.bot.sets, [0, 0])
        self.assertEqual(self.bot.games, [0, 0])
        self.assertEqual(self.bot.points, [0, 0])
        self.assertFalse(self.bot.match_complete)
        self.assertIsNone(self.bot.winner)
    
    def test_simulate_point(self):
        """Test point simulation returns valid values."""
        for _ in range(10):
            result = self.bot.simulate_point()
            self.assertIn(result, [0, 1])
    
    def test_simulate_match(self):
        """Test full match simulation."""
        result = self.bot.simulate_match()
        self.assertIn("Match complete! Winner:", result)
        self.assertTrue(self.bot.match_complete)
        self.assertIsNotNone(self.bot.winner)
        self.assertIn(self.bot.winner, ["Alice", "Bob"])


if __name__ == "__main__":
    unittest.main()