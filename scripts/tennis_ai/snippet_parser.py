#!/usr/bin/env python3
"""
Google Snippet Tennis Result Parser
====================================

Parses tennis match results from Google search snippets in multiple formats.
Supports various score formats, validates tennis scores, matches player names,
and provides confidence scoring.

Usage:
    from snippet_parser import parse_snippet
    
    result = parse_snippet(
        snippet_text="Cedrik-Marcel Stebe 5 1 J. Schwaerzler 7 6",
        player1="C. Stebe",
        player2="J. J. Schwaerzler"
    )
"""

import re
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher


def normalize_player_name(name: str) -> str:
    """
    Normalize player name for matching.
    Removes common prefixes, handles abbreviations.
    
    Examples:
        "T. Seyboth Wild" -> "Seyboth Wild"
        "C. Stebe" -> "Stebe"
        "J. J. Schwaerzler" -> "Schwaerzler"
    """
    # Remove initials (single letters followed by period)
    name = re.sub(r'\b[A-Z]\.\s*', '', name)
    # Remove multiple initials
    name = re.sub(r'\b[A-Z]\.\s*[A-Z]\.\s*', '', name)
    # Get last name (last word)
    parts = name.strip().split()
    if parts:
        return parts[-1]
    return name.strip()


def fuzzy_match_name(name1: str, name2: str, threshold: float = 0.6) -> bool:
    """
    Check if two player names match (fuzzy matching).
    Handles abbreviations and variations.
    """
    norm1 = normalize_player_name(name1).lower()
    norm2 = normalize_player_name(name2).lower()
    
    # Exact match after normalization
    if norm1 == norm2:
        return True
    
    # Check if one name contains the other
    if norm1 in norm2 or norm2 in norm1:
        return True
    
    # Sequence similarity
    similarity = SequenceMatcher(None, norm1, norm2).ratio()
    return similarity >= threshold


def validate_tennis_score(games: int) -> bool:
    """
    Validate that a games score is within tennis rules.
    - Regular set: 0-6 (or 7 if tiebreak)
    - Tiebreak: up to 7
    """
    return 0 <= games <= 7


def parse_space_separated_scores(text: str, player1: str, player2: str) -> Optional[Dict]:
    """
    Parse space-separated score format.
    
    Examples:
        "Player1 6 4 Player2 3 6" → 2 sets
        "Player1 6 4 3 6 6 2 Player2" → 3 sets
        "Cedrik-Marcel Stebe 5 1 J. Schwaerzler 7 6" → 2 sets
    """
    # Normalize player names
    p1_normalized = normalize_player_name(player1).lower()
    p2_normalized = normalize_player_name(player2).lower()
    text_lower = text.lower()
    
    # Find player positions
    p1_pos = text_lower.find(p1_normalized)
    p2_pos = text_lower.find(p2_normalized)
    
    # Check if names are interspersed with scores (e.g., "Stebe 5 1 Schwaerzler 7 6")
    if p1_pos != -1 and p2_pos != -1:
        # Find numbers near each player name
        # Pattern: "PlayerName number number"
        p1_pattern = rf'{re.escape(p1_normalized)}\s+(\d{{1,2}})\s+(\d{{1,2}})'
        p2_pattern = rf'{re.escape(p2_normalized)}\s+(\d{{1,2}})\s+(\d{{1,2}})'
        
        p1_match = re.search(p1_pattern, text_lower)
        p2_match = re.search(p2_pattern, text_lower)
        
        if p1_match and p2_match:
            # Both players have scores after their names
            # Extract scores for each player
            p1_scores = [int(p1_match.group(1)), int(p1_match.group(2))]
            p2_scores = [int(p2_match.group(1)), int(p2_match.group(2))]
            
            # Validate scores
            if all(validate_tennis_score(s) for s in p1_scores + p2_scores):
                # Determine which player appears first (home)
                if p1_pos < p2_pos:
                    # Player1 is home
                    sets = [(p1_scores[i], p2_scores[i]) for i in range(len(p1_scores))]
                else:
                    # Player2 is home
                    sets = [(p2_scores[i], p1_scores[i]) for i in range(len(p2_scores))]
                
                if len(sets) >= 2:
                    home_sets = sum(1 for s1, s2 in sets if s1 > s2)
                    away_sets = sum(1 for s1, s2 in sets if s2 > s1)
                    
                    if home_sets != away_sets:
                        winner = "Home" if home_sets > away_sets else "Away"
                        score_str = " ".join([f"{s1}-{s2}" for s1, s2 in sets])
                        return {
                            'winner': winner,
                            'score': score_str,
                            'sets_parsed': len(sets),
                            'format': 'space_separated'
                        }
    
    # Fallback: Find all numbers and group into pairs
    numbers = re.findall(r'\b\d{1,2}\b', text)
    
    if len(numbers) < 4:  # Need at least 2 sets (4 numbers)
        return None
    
    # Group numbers into sets (pairs)
    sets = []
    for i in range(0, len(numbers) - 1, 2):
        try:
            score1 = int(numbers[i])
            score2 = int(numbers[i + 1])
            
            # Validate tennis scores
            if validate_tennis_score(score1) and validate_tennis_score(score2):
                sets.append((score1, score2))
        except (ValueError, IndexError):
            continue
    
    if len(sets) < 2:  # Need at least 2 sets
        return None
    
    # Determine which player is "home" based on name order
    # If player1 appears before player2, first score in each set is player1
    if p1_pos != -1 and p2_pos != -1 and p1_pos < p2_pos:
        # Player1 is first (home)
        home_sets = sum(1 for s1, s2 in sets if s1 > s2)
        away_sets = sum(1 for s1, s2 in sets if s2 > s1)
    else:
        # Player2 might be first, or order unclear
        # Try both interpretations and pick the one that makes sense
        home_sets = sum(1 for s1, s2 in sets if s1 > s2)
        away_sets = sum(1 for s1, s2 in sets if s2 > s1)
        
        # If tied, try reverse
        if home_sets == away_sets:
            home_sets = sum(1 for s1, s2 in sets if s2 > s1)
            away_sets = sum(1 for s1, s2 in sets if s1 > s2)
    
    if home_sets == away_sets:  # Shouldn't happen in completed match
        return None
    
    winner = "Home" if home_sets > away_sets else "Away"
    score_str = " ".join([f"{s1}-{s2}" for s1, s2 in sets])
    
    return {
        'winner': winner,
        'score': score_str,
        'sets_parsed': len(sets),
        'format': 'space_separated'
    }


def parse_dash_format_scores(text: str, player1: str, player2: str) -> Optional[Dict]:
    """
    Parse dash-format scores.
    
    Examples:
        "Player1 defeats Player2 6-3, 6-4"
        "Player1 beats Player2 7-5, 6-1"
        "Score: 6-4, 6-3 Winner: Player1"
    """
    # Pattern: numbers with dashes, possibly separated by commas
    # Match patterns like "6-3", "7-5", "6-4, 6-3"
    score_pattern = r'\b(\d{1,2})-(\d{1,2})\b'
    matches = re.findall(score_pattern, text)
    
    if len(matches) < 2:  # Need at least 2 sets
        return None
    
    sets = []
    for match in matches:
        try:
            score1 = int(match[0])
            score2 = int(match[1])
            
            if validate_tennis_score(score1) and validate_tennis_score(score2):
                sets.append((score1, score2))
        except (ValueError, IndexError):
            continue
    
    if len(sets) < 2:
        return None
    
    # Check for explicit winner mention
    text_lower = text.lower()
    p1_normalized = normalize_player_name(player1).lower()
    p2_normalized = normalize_player_name(player2).lower()
    
    # Look for winner indicators
    winner_mentioned = None
    if 'winner' in text_lower or 'defeats' in text_lower or 'beats' in text_lower:
        if p1_normalized in text_lower and text_lower.find(p1_normalized) < text_lower.find('defeats'):
            winner_mentioned = "Home"
        elif p2_normalized in text_lower and text_lower.find(p2_normalized) < text_lower.find('defeats'):
            winner_mentioned = "Away"
        elif 'winner' in text_lower:
            # Check which player is mentioned after "winner"
            winner_idx = text_lower.find('winner')
            if p1_normalized in text_lower[winner_idx:]:
                winner_mentioned = "Home"
            elif p2_normalized in text_lower[winner_idx:]:
                winner_mentioned = "Away"
    
    # Count sets won
    home_sets = sum(1 for s1, s2 in sets if s1 > s2)
    away_sets = sum(1 for s1, s2 in sets if s2 > s1)
    
    # Use explicit winner if available, otherwise calculate
    if winner_mentioned:
        winner = winner_mentioned
    elif home_sets > away_sets:
        winner = "Home"
    elif away_sets > home_sets:
        winner = "Away"
    else:
        return None
    
    score_str = " ".join([f"{s1}-{s2}" for s1, s2 in sets])
    
    return {
        'winner': winner,
        'score': score_str,
        'sets_parsed': len(sets),
        'format': 'dash_format'
    }


def calculate_confidence(result: Dict, snippet_text: str, player1: str, player2: str) -> int:
    """
    Calculate confidence score (50-90%).
    
    Higher confidence:
    - Clear score format
    - Player names match
    - Valid tennis scores
    - Complete match (2-3 sets)
    
    Lower confidence:
    - Ambiguous format
    - Missing player names
    - Incomplete scores
    """
    confidence = 50  # Base confidence
    
    # Format clarity (+10)
    if result.get('format') in ['space_separated', 'dash_format']:
        confidence += 10
    
    # Player name matching (+15)
    snippet_lower = snippet_text.lower()
    p1_normalized = normalize_player_name(player1).lower()
    p2_normalized = normalize_player_name(player2).lower()
    
    p1_found = p1_normalized in snippet_lower or fuzzy_match_name(player1, snippet_text)
    p2_found = p2_normalized in snippet_lower or fuzzy_match_name(player2, snippet_text)
    
    if p1_found and p2_found:
        confidence += 15
    elif p1_found or p2_found:
        confidence += 5
    
    # Score validation (+10)
    if result.get('sets_parsed', 0) >= 2:
        confidence += 10
    
    # Complete match (2-3 sets) (+5)
    sets_count = result.get('sets_parsed', 0)
    if 2 <= sets_count <= 3:
        confidence += 5
    
    # Explicit winner mention (+10)
    if 'winner' in snippet_text.lower() or 'defeats' in snippet_text.lower():
        confidence += 10
    
    # Cap at 90%
    return min(confidence, 90)


def parse_snippet(snippet_text: str, player1: str, player2: str) -> Optional[Dict]:
    """
    Parse tennis match result from Google snippet text.
    
    Supports multiple formats:
    - Space-separated: "Player1 6 4 Player2 3 6"
    - Dash-format: "Player1 defeats Player2 6-3, 6-4"
    - Winner format: "Score: 6-4, 6-3 Winner: Player1"
    
    Args:
        snippet_text: The snippet text from Google search
        player1: First player name (Home)
        player2: Second player name (Away)
    
    Returns:
        Dict with winner, score, sets_parsed, format, confidence
        or None if parsing fails
    """
    if not snippet_text or not snippet_text.strip():
        return None
    
    # Try different parsing methods
    result = None
    
    # Try dash format first (usually more explicit)
    result = parse_dash_format_scores(snippet_text, player1, player2)
    if result:
        result['confidence'] = calculate_confidence(result, snippet_text, player1, player2)
        return result
    
    # Try space-separated format
    result = parse_space_separated_scores(snippet_text, player1, player2)
    if result:
        result['confidence'] = calculate_confidence(result, snippet_text, player1, player2)
        return result
    
    # If both fail, return None
    return None


def parse_snippet_with_fallback(snippet_text: str, player1: str, player2: str) -> Dict:
    """
    Parse snippet with fallback to manual interpretation.
    Always returns a dict, but may have low confidence.
    """
    result = parse_snippet(snippet_text, player1, player2)
    
    if result:
        return result
    
    # Fallback: return None result with low confidence
    return {
        'winner': None,
        'score': None,
        'sets_parsed': 0,
        'format': 'unknown',
        'confidence': 0,
        'raw_text': snippet_text
    }

