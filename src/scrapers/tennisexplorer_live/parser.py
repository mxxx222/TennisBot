#!/usr/bin/env python3
"""
🎾 TENNISEXPLORER HTML PARSER
=============================

HTML parsing logic for TennisExplorer live matches.
Handles multiple selector strategies and fallback mechanisms.
"""

import re
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from bs4 import BeautifulSoup

from .models import LiveMatch

logger = logging.getLogger(__name__)


class TennisExplorerParser:
    """Parser for TennisExplorer HTML content"""
    
    def __init__(self):
        """Initialize parser"""
        logger.debug("🎾 TennisExplorer Parser initialized")
    
    def parse_live_matches(self, html: str) -> List[LiveMatch]:
        """
        Parse live matches from main live page HTML
        
        Args:
            html: HTML content from /live-tennis/ or /live/
            
        Returns:
            List of LiveMatch objects
        """
        soup = BeautifulSoup(html, 'html.parser')
        matches = []
        
        # Strategy 1: Find match detail links (most reliable)
        match_links = soup.find_all('a', href=lambda x: x and 'match-detail' in str(x).lower())
        logger.info(f"Found {len(match_links)} match detail links")
        
        seen_match_ids = set()
        
        for link in match_links:
            try:
                # Extract match ID from URL
                href = link.get('href', '')
                match_id = self._extract_match_id(href)
                
                if not match_id or match_id in seen_match_ids:
                    continue
                
                # Find parent container (TR or DIV)
                container = link.find_parent(['tr', 'div', 'li'])
                if not container:
                    container = link.find_parent()
                
                match = self._parse_match_from_container(container, match_id, href, is_live=True)
                
                if match and match.validate()["is_valid"]:
                    matches.append(match)
                    seen_match_ids.add(match_id)
                    logger.debug(f"✅ Parsed match {match_id}: {match.player_a} vs {match.player_b}")
                
            except Exception as e:
                logger.debug(f"⚠️ Error parsing match link: {e}")
                continue
        
        # Strategy 2: Fallback - find table rows with player links
        if not matches:
            logger.debug("Trying fallback: parsing table rows directly")
            rows = soup.find_all('tr')
            for row in rows:
                try:
                    player_links = row.find_all('a', href=lambda x: x and '/player/' in str(x))
                    if len(player_links) >= 2:
                        player_a = player_links[0].get_text(strip=True)
                        player_b = player_links[1].get_text(strip=True)
                        
                        if player_a and player_b and player_a != player_b:
                            match_id = f"te_{hash(f'{player_a}_{player_b}_{datetime.now()}') % 100000}"
                            match = self._parse_match_from_container(row, match_id, None, is_live=True)
                            if match and match.validate()["is_valid"]:
                                matches.append(match)
                                logger.debug(f"✅ Parsed match via fallback: {match_id}")
                except Exception as e:
                    logger.debug(f"⚠️ Error parsing row: {e}")
                    continue
        
        logger.info(f"✅ Parsed {len(matches)} live matches total")
        return matches
    
    def parse_match_stats(self, html: str) -> Dict[str, Any]:
        """
        Parse detailed match statistics from match detail page
        
        Args:
            html: HTML content from match detail page
            
        Returns:
            Dictionary with stats: service_pct_a, service_pct_b, break_points_a, break_points_b, momentum
        """
        soup = BeautifulSoup(html, 'html.parser')
        stats = {
            'service_pct_a': None,
            'service_pct_b': None,
            'break_points_a': None,
            'break_points_b': None,
            'momentum': None
        }
        
        try:
            # Look for stats table or div
            stats_table = soup.find('table', class_=lambda x: x and 'stat' in str(x).lower())
            if not stats_table:
                stats_table = soup.find('div', class_=lambda x: x and 'stat' in str(x).lower())
            
            if stats_table:
                # Parse service percentage
                service_cells = stats_table.find_all(['td', 'th'], string=re.compile(r'Service', re.I))
                for cell in service_cells:
                    # Look for percentage values nearby
                    parent = cell.find_parent(['tr', 'div'])
                    if parent:
                        pct_text = parent.get_text()
                        pct_matches = re.findall(r'(\d+(?:\.\d+)?)%', pct_text)
                        if len(pct_matches) >= 2:
                            stats['service_pct_a'] = float(pct_matches[0])
                            stats['service_pct_b'] = float(pct_matches[1])
                
                # Parse break points
                bp_cells = stats_table.find_all(['td', 'th'], string=re.compile(r'Break', re.I))
                for cell in bp_cells:
                    parent = cell.find_parent(['tr', 'div'])
                    if parent:
                        bp_text = parent.get_text()
                        bp_matches = re.findall(r'(\d+/\d+)', bp_text)
                        if len(bp_matches) >= 2:
                            stats['break_points_a'] = bp_matches[0]
                            stats['break_points_b'] = bp_matches[1]
            
            # Calculate momentum (simple heuristic: who's winning more sets)
            score_elem = soup.find(['div', 'span', 'td'], class_=lambda x: x and 'score' in str(x).lower())
            if score_elem:
                score_text = score_elem.get_text(strip=True)
                momentum = self._calculate_momentum(score_text)
                if momentum:
                    stats['momentum'] = momentum
            
        except Exception as e:
            logger.debug(f"⚠️ Error parsing match stats: {e}")
        
        return stats
    
    def _parse_match_from_container(self, container, match_id: str, href: Optional[str], is_live: bool) -> Optional[LiveMatch]:
        """Parse a match from container element"""
        try:
            # Extract player names
            player_a, player_b = self._extract_players(container)
            if not player_a or not player_b:
                return None
            
            # Extract tournament
            tournament = self._extract_tournament(container)
            
            # Extract surface
            surface = self._extract_surface(container, tournament)
            
            # Extract score (for live matches)
            score = None
            if is_live:
                score = self._extract_score(container)
            
            # Extract tournament tier
            tournament_tier = self._extract_tournament_tier(tournament)
            
            # Build match URL
            match_url = None
            if href:
                if href.startswith('http'):
                    match_url = href
                else:
                    match_url = f"https://www.tennisexplorer.com{href}" if not href.startswith('/') else f"https://www.tennisexplorer.com{href}"
            
            # Determine match status
            match_status = "live" if is_live else "upcoming"
            if score:
                # Check if match is finished (score ends with final set)
                score_parts = score.split(',')
                if len(score_parts) >= 2:
                    # Check if last set is complete (e.g., "6-4" not "3-2")
                    last_set = score_parts[-1].strip()
                    if re.match(r'^\d+-\d+$', last_set):
                        # Could be finished, but we'll assume live if we're on live page
                        pass
            
            return LiveMatch(
                match_id=match_id,
                player_a=player_a,
                player_b=player_b,
                tournament=tournament or "Unknown Tournament",
                surface=surface or "Hard",
                score=score or "",
                start_time=datetime.now(),
                match_status=match_status,
                tournament_tier=tournament_tier,
                match_url=match_url
            )
            
        except Exception as e:
            logger.debug(f"⚠️ Error parsing match container: {e}")
            return None
    
    def _extract_match_id(self, href: str) -> Optional[str]:
        """Extract match ID from URL"""
        if not href:
            return None
        
        # Pattern: /match-detail/?id=3074806
        if 'id=' in href:
            match_id = href.split('id=')[-1].split('&')[0].split('#')[0]
            if match_id.isdigit():
                return match_id
        
        # Pattern: /match-detail/3074806
        match = re.search(r'/match-detail[/-]?(\d+)', href)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_players(self, container) -> Tuple[Optional[str], Optional[str]]:
        """Extract player names from container"""
        # Strategy 1: Find player links
        player_links = container.find_all('a', href=lambda x: x and '/player/' in str(x))
        if len(player_links) >= 2:
            player_a = player_links[0].get_text(strip=True)
            player_b = player_links[1].get_text(strip=True)
            if player_a and player_b and len(player_a) > 1 and len(player_b) > 1:
                return player_a, player_b
        
        # Strategy 2: Find text that looks like player names
        text_elements = container.find_all(['span', 'div', 'td'], class_=lambda x: x and 'player' in str(x).lower())
        if len(text_elements) >= 2:
            player_a = text_elements[0].get_text(strip=True)
            player_b = text_elements[1].get_text(strip=True)
            if player_a and player_b and len(player_a) > 1 and len(player_b) > 1:
                return player_a, player_b
        
        # Strategy 3: Extract from all text, filter out common words
        all_text = container.get_text()
        lines = [line.strip() for line in all_text.split('\n') if line.strip()]
        names = [line for line in lines 
                if len(line) > 2 
                and line.lower() not in ['vs', 'v', '–', '-', 'live', 'finished', 'upcoming', 'match', 'set']
                and not re.match(r'^\d+[-:]\d+', line)]  # Exclude scores
        
        if len(names) >= 2:
            return names[0], names[1]
        
        return None, None
    
    def _extract_tournament(self, container) -> Optional[str]:
        """Extract tournament name"""
        # Look for tournament link
        tournament_link = container.find('a', href=lambda x: x and '/tournament/' in str(x))
        if tournament_link:
            return tournament_link.get_text(strip=True)
        
        # Look for tournament text
        tournament_elem = container.find(['span', 'div', 'td'], class_=lambda x: x and 'tournament' in str(x).lower())
        if tournament_elem:
            return tournament_elem.get_text(strip=True)
        
        # Try to find tournament in parent elements
        parent = container.find_parent(['tr', 'div', 'table'])
        if parent:
            tournament_link = parent.find('a', href=lambda x: x and '/tournament/' in str(x))
            if tournament_link:
                return tournament_link.get_text(strip=True)
        
        return None
    
    def _extract_surface(self, container, tournament: Optional[str]) -> Optional[str]:
        """Extract surface type"""
        # Check tournament name
        if tournament:
            tournament_lower = tournament.lower()
            if 'hard' in tournament_lower or 'indoor' in tournament_lower:
                return "Hard"
            elif 'clay' in tournament_lower:
                return "Clay"
            elif 'grass' in tournament_lower:
                return "Grass"
        
        # Check container text
        text = container.get_text().lower()
        if 'hard' in text or 'indoor' in text:
            return "Hard"
        elif 'clay' in text:
            return "Clay"
        elif 'grass' in text:
            return "Grass"
        
        return None
    
    def _extract_score(self, container) -> Optional[str]:
        """Extract current score"""
        # Look for score element
        score_elem = container.find(['td', 'div', 'span'], class_=lambda x: x and 'score' in str(x).lower())
        if score_elem:
            score_text = score_elem.get_text(strip=True)
            if score_text:
                return score_text
        
        # Look for score pattern in text
        text = container.get_text()
        score_match = re.search(r'(\d+[-:]\d+(?:\s*,\s*\d+[-:]\d+)*)', text)
        if score_match:
            return score_match.group(1).replace(':', '-')
        
        return None
    
    def _extract_tournament_tier(self, tournament: Optional[str]) -> Optional[str]:
        """Extract tournament tier (ATP, WTA, ITF, Challenger)"""
        if not tournament:
            return None
        
        tournament_upper = tournament.upper()
        
        if 'ATP' in tournament_upper:
            return "ATP"
        elif 'WTA' in tournament_upper:
            return "WTA"
        elif 'ITF' in tournament_upper:
            return "ITF"
        elif 'CHALLENGER' in tournament_upper:
            return "Challenger"
        elif re.search(r'\bW\d+\b', tournament_upper):  # W15, W25, W35, etc.
            return "ITF"
        
        return None
    
    def _calculate_momentum(self, score_text: str) -> Optional[str]:
        """Calculate which player has momentum based on score"""
        if not score_text:
            return None
        
        # Parse sets
        sets = score_text.split(',')
        if len(sets) < 2:
            return None
        
        # Count sets won by each player (simplified)
        # This is a basic heuristic - can be improved
        player_a_sets = 0
        player_b_sets = 0
        
        for set_score in sets:
            set_score = set_score.strip()
            match = re.match(r'(\d+)[-:](\d+)', set_score)
            if match:
                games_a = int(match.group(1))
                games_b = int(match.group(2))
                if games_a > games_b:
                    player_a_sets += 1
                elif games_b > games_a:
                    player_b_sets += 1
        
        # Check current set (last one)
        if sets:
            last_set = sets[-1].strip()
            match = re.match(r'(\d+)[-:](\d+)', last_set)
            if match:
                games_a = int(match.group(1))
                games_b = int(match.group(2))
                # If current set is close, momentum goes to set leader
                if abs(games_a - games_b) <= 2:
                    if games_a > games_b:
                        return "Player A"
                    elif games_b > games_a:
                        return "Player B"
        
        # Overall momentum
        if player_a_sets > player_b_sets:
            return "Player A"
        elif player_b_sets > player_a_sets:
            return "Player B"
        
        return None

