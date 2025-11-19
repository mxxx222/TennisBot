#!/usr/bin/env python3
"""
Quick test script for snippet parser
Tests various snippet formats to validate parsing accuracy
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.tennis_ai.snippet_parser import parse_snippet


def test_parser():
    """Test parser with various snippet formats"""
    
    test_cases = [
        # Format: (snippet_text, player1, player2, expected_winner)
        {
            'snippet': "Cedrik-Marcel Stebe 5 1 J. Schwaerzler 7 6",
            'player1': "C. Stebe",
            'player2': "J. J. Schwaerzler",
            'expected': "Away",  # Schwaerzler wins 7-5, 6-1
            'description': "Space-separated format with mixed names"
        },
        {
            'snippet': "Seyboth Wild 3 6 6 1 6 2 Kopriva",
            'player1': "T. Seyboth Wild",
            'player2': "V. Kopriva",
            'expected': "Home",  # Seyboth Wild wins
            'description': "Space-separated 3-set match"
        },
        {
            'snippet': "Player1 defeats Player2 6-3, 6-4",
            'player1': "Player1",
            'player2': "Player2",
            'expected': "Home",  # Player1 wins
            'description': "Dash format with explicit winner"
        },
        {
            'snippet': "Score: 6-4, 6-3 Winner: Player1",
            'player1': "Player1",
            'player2': "Player2",
            'expected': "Home",  # Player1 wins
            'description': "Explicit winner format"
        },
        {
            'snippet': "Molcan beats Coppejans 7-5, 6-1",
            'player1': "A. Molcan",
            'player2': "K. Coppejans",
            'expected': "Home",  # Molcan wins
            'description': "Dash format with 'beats' keyword"
        },
    ]
    
    print("=" * 70)
    print("🧪 SNIPPET PARSER TEST")
    print("=" * 70)
    print()
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['description']}")
        print(f"  Snippet: {test['snippet']}")
        print(f"  Players: {test['player1']} vs {test['player2']}")
        
        result = parse_snippet(
            test['snippet'],
            test['player1'],
            test['player2']
        )
        
        if result and result.get('winner'):
            winner = result['winner']
            score = result.get('score', 'N/A')
            confidence = result.get('confidence', 0)
            
            print(f"  Result: {winner} - {score} (confidence: {confidence}%)")
            
            if winner == test['expected']:
                print(f"  ✅ PASSED")
                passed += 1
            else:
                print(f"  ❌ FAILED - Expected {test['expected']}, got {winner}")
                failed += 1
        else:
            print(f"  ❌ FAILED - Could not parse snippet")
            failed += 1
        
        print()
    
    print("=" * 70)
    print(f"📊 RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == '__main__':
    success = test_parser()
    sys.exit(0 if success else 1)

