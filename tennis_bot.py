#!/usr/bin/env python3
"""
Tennis Bot - A simple tennis game simulator and score tracker.

This bot can simulate tennis matches, track scores, and provide
an interactive tennis experience.
"""

import random
import sys
from typing import List, Tuple, Optional


class TennisBot:
    """A tennis bot that can simulate games and track scores."""
    
    def __init__(self, player1: str = "Player 1", player2: str = "Player 2"):
        self.player1 = player1
        self.player2 = player2
        self.reset_match()
    
    def reset_match(self):
        """Reset the match to initial state."""
        self.sets = [0, 0]  # Sets won by each player
        self.games = [0, 0]  # Games in current set
        self.points = [0, 0]  # Points in current game
        self.match_complete = False
        self.winner = None
    
    def get_score_display(self) -> str:
        """Get a formatted display of the current score."""
        point_names = ["0", "15", "30", "40"]
        
        # Handle deuce and advantage situations
        if self.points[0] >= 3 and self.points[1] >= 3:
            if self.points[0] == self.points[1]:
                point_display = "Deuce"
            elif self.points[0] > self.points[1]:
                point_display = f"Advantage {self.player1}"
            else:
                point_display = f"Advantage {self.player2}"
        else:
            p1_points = point_names[min(self.points[0], 3)]
            p2_points = point_names[min(self.points[1], 3)]
            point_display = f"{p1_points} - {p2_points}"
        
        return (f"{self.player1}: {self.sets[0]} sets, {self.games[0]} games\n"
                f"{self.player2}: {self.sets[1]} sets, {self.games[1]} games\n"
                f"Current game: {point_display}")
    
    def win_point(self, player_index: int):
        """Award a point to the specified player (0 or 1)."""
        if self.match_complete:
            return
        
        self.points[player_index] += 1
        
        # Check if game is won
        if self.points[player_index] >= 4 and self.points[player_index] - self.points[1-player_index] >= 2:
            self.win_game(player_index)
    
    def win_game(self, player_index: int):
        """Award a game to the specified player."""
        self.games[player_index] += 1
        self.points = [0, 0]  # Reset points for new game
        
        # Check if set is won (first to 6 games, must win by 2)
        if self.games[player_index] >= 6 and self.games[player_index] - self.games[1-player_index] >= 2:
            self.win_set(player_index)
        # Handle tiebreak at 6-6 (simplified - just need to win by 1)
        elif self.games[0] == 6 and self.games[1] == 6:
            if self.games[player_index] == 7:
                self.win_set(player_index)
    
    def win_set(self, player_index: int):
        """Award a set to the specified player."""
        self.sets[player_index] += 1
        self.games = [0, 0]  # Reset games for new set
        
        # Check if match is won (best of 3 sets)
        if self.sets[player_index] >= 2:
            self.match_complete = True
            self.winner = self.player1 if player_index == 0 else self.player2
    
    def simulate_point(self) -> int:
        """Simulate a point and return the winner (0 or 1)."""
        # Simple random simulation - could be enhanced with player skills
        return random.randint(0, 1)
    
    def simulate_game(self) -> str:
        """Simulate a complete game and return the result."""
        if self.match_complete:
            return "Match is already complete!"
        
        result = []
        while not self.match_complete and max(self.points) < 4:
            winner = self.simulate_point()
            self.win_point(winner)
            result.append(f"Point to {self.player1 if winner == 0 else self.player2}")
        
        return "\n".join(result)
    
    def simulate_match(self) -> str:
        """Simulate an entire match and return the summary."""
        self.reset_match()
        moves = []
        
        while not self.match_complete:
            winner = self.simulate_point()
            self.win_point(winner)
        
        return f"Match complete! Winner: {self.winner}"


def interactive_mode():
    """Run the tennis bot in interactive mode."""
    print("🎾 Welcome to Tennis Bot! 🎾")
    print("=" * 40)
    
    # Get player names
    player1 = input("Enter name for Player 1 (or press Enter for 'Player 1'): ").strip()
    if not player1:
        player1 = "Player 1"
    
    player2 = input("Enter name for Player 2 (or press Enter for 'Player 2'): ").strip()
    if not player2:
        player2 = "Player 2"
    
    bot = TennisBot(player1, player2)
    
    print(f"\nMatch: {player1} vs {player2}")
    print("Commands: 'p1' (point to player 1), 'p2' (point to player 2), 'sim' (simulate point), 'score', 'quit'")
    print("=" * 40)
    
    while not bot.match_complete:
        print(f"\n{bot.get_score_display()}")
        
        command = input("\nEnter command: ").strip().lower()
        
        if command == 'quit':
            break
        elif command == 'p1':
            bot.win_point(0)
            print(f"Point to {player1}!")
        elif command == 'p2':
            bot.win_point(1)
            print(f"Point to {player2}!")
        elif command == 'sim':
            winner = bot.simulate_point()
            bot.win_point(winner)
            winner_name = player1 if winner == 0 else player2
            print(f"Point to {winner_name}!")
        elif command == 'score':
            continue  # Score will be displayed at top of loop
        else:
            print("Invalid command. Use 'p1', 'p2', 'sim', 'score', or 'quit'")
    
    if bot.match_complete:
        print(f"\n🏆 MATCH COMPLETE! 🏆")
        print(f"Winner: {bot.winner}")
        print(f"Final Score: {bot.sets[0]}-{bot.sets[1]} sets")


def main():
    """Main entry point for the tennis bot."""
    if len(sys.argv) > 1:
        if sys.argv[1] == '--simulate':
            bot = TennisBot()
            result = bot.simulate_match()
            print(result)
            print(bot.get_score_display())
        elif sys.argv[1] == '--help':
            print("Tennis Bot - A tennis game simulator")
            print("Usage:")
            print("  python tennis_bot.py          # Interactive mode")
            print("  python tennis_bot.py --simulate  # Simulate a full match")
            print("  python tennis_bot.py --help      # Show this help")
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Use --help for usage information")
    else:
        interactive_mode()


if __name__ == "__main__":
    main()