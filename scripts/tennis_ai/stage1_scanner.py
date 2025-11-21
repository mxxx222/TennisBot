#!/usr/bin/env python3
"""
Stage 1: Scan & Filter
======================

Scans Sportbex API for ITF matches and pushes to Candidates DB.
Basic filtering: odds 1.20-1.80, tournament tiers W15/W25/W35.
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / 'telegram_secrets.env'
if env_path.exists():
    load_dotenv(env_path)

# Import simple client
from scripts.tennis_ai.sportbex_client_simple import SportbexClient

# Notion API
try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    print("⚠️ notion-client not installed. Install with: pip install notion-client")


class Stage1Scanner:
    """Stage 1: Basic scan and filter to Candidates DB"""
    
    def __init__(self):
        self.sportbex = SportbexClient()
        self.notion = None
        self.candidates_db_id = os.getenv('NOTION_CANDIDATES_DB_ID')
        
        if NOTION_AVAILABLE:
            notion_token = os.getenv('NOTION_API_KEY') or os.getenv('NOTION_TOKEN')
            if notion_token:
                self.notion = Client(auth=notion_token)
            else:
                print("⚠️ NOTION_API_KEY not set")
        
        if not self.candidates_db_id:
            print("⚠️ NOTION_CANDIDATES_DB_ID not set")
    
    def scan_itf_matches(self) -> List[Dict]:
        """
        Scan all ITF matches from Sportbex.
        Returns list of candidate dicts.
        """
        print("🔍 Stage 1: Scanning ITF matches...")
        
        comps = self.sportbex.get_tennis_competitions()
        itf_comps = [
            c for c in comps 
            if 'ITF' in c.get('competition', {}).get('name', '')
        ]
        
        print(f"  Found {len(itf_comps)} ITF competitions")
        
        candidates = []
        
        for comp in itf_comps:
            comp_id = comp.get('competition', {}).get('id')
            comp_name = comp.get('competition', {}).get('name', '')
            
            if not comp_id:
                continue
            
            events = self.sportbex.get_events(comp_id)
            print(f"  Scanning {comp_name}: {len(events)} matches")
            
            for event in events:
                candidate = self._parse_event(event, comp)
                if candidate and self._passes_stage1_filter(candidate):
                    candidates.append(candidate)
        
        print(f"\n✅ Found {len(candidates)} candidates passing Stage 1")
        return candidates
    
    def _parse_event(self, event: Dict, comp: Dict) -> Optional[Dict]:
        """Parse Sportbex event into candidate dict"""
        try:
            event_data = event.get('event', {})
            markets = event.get('markets', [])
            
            if not markets:
                return None
            
            market = markets[0]
            runners = market.get('runners', [])
            
            if len(runners) != 2:
                return None
            
            # Get odds
            odds_a = runners[0].get('ex', {}).get('availableToBack', [{}])[0].get('price')
            odds_b = runners[1].get('ex', {}).get('availableToBack', [{}])[0].get('price')
            
            if not odds_a or not odds_b:
                return None
            
            # Determine favorite (lower odds)
            if odds_a < odds_b:
                player_a = runners[0].get('runnerName')
                player_b = runners[1].get('runnerName')
                pick_side = 'Player A'
                odds = odds_a
            else:
                player_a = runners[1].get('runnerName')
                player_b = runners[0].get('runnerName')
                pick_side = 'Player A'  # A is always favorite
                odds = odds_b
            
            # Extract tournament tier
            comp_name = comp.get('competition', {}).get('name', '')
            tier = self._extract_tier(comp_name)
            
            return {
                'match_name': f"{player_a} vs {player_b}",
                'league': 'ITF',
                'tournament': comp_name,
                'tournament_tier': tier,
                'player_a': player_a,
                'player_b': player_b,
                'pick_side': pick_side,
                'odds': odds,
                'implied_prob': (1 / odds * 100) if odds else None,
                'match_time': event_data.get('openDate'),
                'event_id': str(event_data.get('id', '')),
                'source': 'Sportbex API',
                'status': 'Scanned'
            }
        
        except Exception as e:
            print(f"  ⚠️ Error parsing event: {e}")
            return None
    
    def _extract_tier(self, comp_name: str) -> str:
        """Extract tournament tier from name"""
        tiers = ['W15', 'W25', 'W35', 'W50', 'M15', 'M25']
        for tier in tiers:
            if tier in comp_name:
                return tier
        return 'W15'  # Default
    
    def _passes_stage1_filter(self, candidate: Dict) -> bool:
        """Stage 1 basic filters"""
        odds = candidate.get('odds', 0)
        tier = candidate.get('tournament_tier', '')
        
        # Odds range: 1.20-1.80 (wider range, will narrow in Stage 2)
        if not (1.20 <= odds <= 1.80):
            return False
        
        # Tournament tier: W15, W25, W35 only
        if tier not in ['W15', 'W25', 'W35']:
            return False
        
        return True
    
    def push_to_candidates_db(self, candidates: List[Dict]) -> List[str]:
        """Push candidates to Notion Candidates DB"""
        if not self.notion:
            print("❌ Notion client not available")
            return []
        
        if not self.candidates_db_id:
            print("❌ NOTION_CANDIDATES_DB_ID not set")
            return []
        
        print(f"📝 Pushing {len(candidates)} candidates to DB...")
        
        urls = []
        for c in candidates:
            try:
                # Parse match time
                date_value = None
                if c.get('match_time'):
                    try:
                        from datetime import datetime
                        date_value = c['match_time']
                    except:
                        pass
                
                properties = {
                    'Match Name': {'title': [{'text': {'content': c['match_name']}}]},
                    'League': {'select': {'name': c['league']}},
                    'Tournament': {'rich_text': [{'text': {'content': c['tournament'][:2000]}}]},
                    'Tournament Tier': {'select': {'name': c['tournament_tier']}},
                    'Player A': {'rich_text': [{'text': {'content': c['player_a']}}]},
                    'Player B': {'rich_text': [{'text': {'content': c['player_b']}}]},
                    'Pick Side': {'select': {'name': c['pick_side']}},
                    'Odds': {'number': c['odds']},
                    'Implied Prob %': {'number': c['implied_prob']},
                    'Event ID': {'rich_text': [{'text': {'content': c['event_id']}}]},
                    'Source': {'rich_text': [{'text': {'content': c['source']}}]},
                    'Status': {'select': {'name': c['status']}}
                }
                
                # Add date if available
                if date_value:
                    properties['Scan Date'] = {'date': {'start': date_value}}
                
                page = self.notion.pages.create(
                    parent={'database_id': self.candidates_db_id},
                    properties=properties
                )
                urls.append(page['url'])
            except Exception as e:
                print(f"  ❌ Error pushing candidate: {e}")
        
        print(f"  ✅ Pushed {len(urls)} candidates")
        return urls


def main():
    print("🚀 Stage 1: Daily ITF Scanner")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    scanner = Stage1Scanner()
    candidates = scanner.scan_itf_matches()
    
    if candidates:
        scanner.push_to_candidates_db(candidates)
    else:
        print("⚠️ No candidates found")
    
    print("\n✅ Stage 1 complete. Next: Stage 2 AI analysis.")


if __name__ == "__main__":
    main()

