"""
Reddit Utilities

Shared utilities for Reddit integration
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)

def extract_odds_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Extract odds information from text using regex patterns
    
    Looks for patterns like:
    - "odds of 2.5"
    - "2.50 odds"
    - "1.85/2.10"
    - "Bet365: 1.90"
    """
    odds_patterns = [
        # Decimal odds patterns
        (r'(\d+\.\d+)\s*(?:odds|@|to|/)', 'decimal'),
        (r'odds?\s*(?:of|are|at)?\s*(\d+\.\d+)', 'decimal'),
        (r'(\d+\.\d+)\s*/\s*(\d+\.\d+)', 'decimal_pair'),
        # Bookmaker: odds patterns
        (r'([A-Za-z0-9]+)\s*[:]\s*(\d+\.\d+)', 'bookmaker_odds'),
        # Fractional odds (convert to decimal)
        (r'(\d+)/(\d+)', 'fractional'),
    ]
    
    extracted_odds = []
    text_lower = text.lower()
    
    for pattern, pattern_type in odds_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                if pattern_type == 'decimal':
                    odds_value = float(match.group(1))
                    if 1.01 <= odds_value <= 100:  # Valid odds range
                        extracted_odds.append({
                            'odds': odds_value,
                            'type': 'decimal',
                            'context': match.group(0),
                            'position': match.start()
                        })
                
                elif pattern_type == 'decimal_pair':
                    odds1 = float(match.group(1))
                    odds2 = float(match.group(2))
                    if 1.01 <= odds1 <= 100 and 1.01 <= odds2 <= 100:
                        extracted_odds.append({
                            'odds': [odds1, odds2],
                            'type': 'decimal_pair',
                            'context': match.group(0),
                            'position': match.start()
                        })
                
                elif pattern_type == 'bookmaker_odds':
                    bookmaker = match.group(1)
                    odds_value = float(match.group(2))
                    if 1.01 <= odds_value <= 100:
                        extracted_odds.append({
                            'bookmaker': bookmaker,
                            'odds': odds_value,
                            'type': 'bookmaker_odds',
                            'context': match.group(0),
                            'position': match.start()
                        })
                
                elif pattern_type == 'fractional':
                    numerator = float(match.group(1))
                    denominator = float(match.group(2))
                    if denominator > 0:
                        decimal_odds = (numerator / denominator) + 1
                        if 1.01 <= decimal_odds <= 100:
                            extracted_odds.append({
                                'odds': decimal_odds,
                                'type': 'fractional',
                                'original': f"{numerator}/{denominator}",
                                'context': match.group(0),
                                'position': match.start()
                            })
            except (ValueError, IndexError) as e:
                logger.debug(f"Error parsing odds from match {match.group(0)}: {e}")
                continue
    
    return extracted_odds

def extract_bookmaker_names(text: str) -> List[str]:
    """Extract bookmaker names from text"""
    common_bookmakers = [
        'bet365', 'pinnacle', 'betfair', 'unibet', 'bwin', 'betway',
        'draftkings', 'fanduel', 'caesars', 'betmgm', 'william hill',
        'ladbrokes', 'coral', 'betvictor', 'skybet', 'betfury', 'rollbit'
    ]
    
    found_bookmakers = []
    text_lower = text.lower()
    
    for bookmaker in common_bookmakers:
        if bookmaker in text_lower:
            found_bookmakers.append(bookmaker)
    
    return found_bookmakers

def extract_match_info(text: str) -> Optional[Dict[str, str]]:
    """
    Extract match information from text
    Looks for team names, match format, etc.
    """
    # Common patterns for match descriptions
    vs_patterns = [
        r'([A-Z][a-zA-Z\s]+)\s+vs\s+([A-Z][a-zA-Z\s]+)',
        r'([A-Z][a-zA-Z\s]+)\s+@\s+([A-Z][a-zA-Z\s]+)',
        r'([A-Z][a-zA-Z\s]+)\s+v\s+([A-Z][a-zA-Z\s]+)',
    ]
    
    for pattern in vs_patterns:
        match = re.search(pattern, text)
        if match:
            home_team = match.group(1).strip()
            away_team = match.group(2).strip()
            
            # Clean up team names
            home_team = re.sub(r'\s+', ' ', home_team)
            away_team = re.sub(r'\s+', ' ', away_team)
            
            if len(home_team) > 2 and len(away_team) > 2:
                return {
                    'home_team': home_team,
                    'away_team': away_team,
                    'match_text': f"{home_team} vs {away_team}"
                }
    
    return None

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate simple similarity between two texts"""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)

def generate_post_id(post_data: Dict[str, Any]) -> str:
    """Generate unique ID for Reddit post"""
    post_id = post_data.get('id', '')
    subreddit = post_data.get('subreddit', '')
    created = post_data.get('created_utc', 0)
    
    if post_id:
        return f"reddit_{subreddit}_{post_id}"
    
    # Fallback: hash based on content
    content = f"{subreddit}_{post_data.get('title', '')}_{post_data.get('selftext', '')}"
    return f"reddit_{hashlib.md5(content.encode()).hexdigest()[:12]}"

def is_recent_post(post_data: Dict[str, Any], max_age_hours: int = 24) -> bool:
    """Check if post is recent enough"""
    created_utc = post_data.get('created_utc', 0)
    if not created_utc:
        return False
    
    post_time = datetime.fromtimestamp(created_utc)
    age = datetime.now() - post_time
    
    return age.total_seconds() < (max_age_hours * 3600)

def clean_reddit_text(text: str) -> str:
    """Clean Reddit text (remove markdown, links, etc.)"""
    if not text:
        return ""
    
    # Remove markdown links [text](url)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def extract_sport_from_text(text: str) -> Optional[str]:
    """Extract sport type from text"""
    sports_keywords = {
        'tennis': ['tennis', 'atp', 'wta', 'grand slam', 'french open', 'wimbledon', 'us open', 'australian open'],
        'football': ['football', 'soccer', 'premier league', 'la liga', 'bundesliga', 'serie a', 'champions league'],
        'basketball': ['basketball', 'nba', 'euroleague', 'basket'],
        'ice_hockey': ['hockey', 'nhl', 'khl', 'ice hockey'],
    }
    
    text_lower = text.lower()
    
    for sport, keywords in sports_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            return sport
    
    return None

