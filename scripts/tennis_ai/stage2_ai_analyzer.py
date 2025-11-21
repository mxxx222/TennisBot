#!/usr/bin/env python3
"""
Stage 2: OpenAI Deep Analysis
===============================

Analyzes candidates from Candidates DB using GPT-4.
Promotes high-score candidates (score >= 80) to Bets DB.
"""

import os
import sys
import json
import re
from datetime import datetime, timedelta
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

# Notion API
try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    print("⚠️ notion-client not installed. Install with: pip install notion-client")

# OpenAI API
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ openai library not installed. Install with: pip install openai")


class Stage2AIAnalyzer:
    """Stage 2: GPT-4 deep analysis of candidates"""
    
    def __init__(self):
        self.notion = None
        self.openai = None
        self.candidates_db_id = os.getenv('NOTION_CANDIDATES_DB_ID')
        self.bets_db_id = os.getenv('NOTION_BETS_DATABASE_ID') or os.getenv('NOTION_TENNIS_PREMATCH_DB_ID')
        
        if NOTION_AVAILABLE:
            notion_token = os.getenv('NOTION_API_KEY') or os.getenv('NOTION_TOKEN')
            if notion_token:
                self.notion = Client(auth=notion_token)
            else:
                print("⚠️ NOTION_API_KEY not set")
        
        if OPENAI_AVAILABLE:
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                self.openai = OpenAI(api_key=openai_key)
            else:
                print("⚠️ OPENAI_API_KEY not set")
        
        if not self.candidates_db_id:
            print("⚠️ NOTION_CANDIDATES_DB_ID not set")
    
    def get_pending_candidates(self) -> List[Dict]:
        """
        Get candidates with status='Scanned' from last 24h.
        """
        if not self.notion or not self.candidates_db_id:
            return []
        
        cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
        
        try:
            # Try to query with date filter
            filter_conditions = {
                "and": [
                    {"property": "Status", "select": {"equals": "Scanned"}}
                ]
            }
            
            # Add date filter if Scan Date property exists
            try:
                filter_conditions["and"].append(
                    {"property": "Scan Date", "date": {"on_or_after": cutoff}}
                )
            except:
                # If date filter fails, just use status filter
                pass
            
            results = self.notion.databases.query(
                database_id=self.candidates_db_id,
                filter=filter_conditions,
                sorts=[{"property": "Odds", "direction": "ascending"}]
            )
            
            candidates = []
            for page in results['results']:
                candidates.append(self._parse_candidate_page(page))
            
            return candidates
        
        except Exception as e:
            print(f"❌ Error fetching candidates: {e}")
            return []
    
    def _parse_candidate_page(self, page: Dict) -> Dict:
        """Parse Notion candidate page to dict"""
        props = page['properties']
        
        return {
            'page_id': page['id'],
            'match_name': self._get_title(props.get('Match Name')),
            'player_a': self._get_text(props.get('Player A')),
            'player_b': self._get_text(props.get('Player B')),
            'odds': self._get_number(props.get('Odds')),
            'rank_a': self._get_number(props.get('Rank A')),
            'rank_b': self._get_number(props.get('Rank B')),
            'rank_delta': self._get_number(props.get('Rank Delta')),
            'elo_a': self._get_number(props.get('ELO A')),
            'elo_b': self._get_number(props.get('ELO B')),
            'elo_delta': self._get_number(props.get('ELO Delta')),
            'surface': self._get_select(props.get('Surface')),
            'h2h_record': self._get_text(props.get('H2H Record')),
            'form_a': self._get_text(props.get('Form A')),
            'form_b': self._get_text(props.get('Form B')),
            'tournament_tier': self._get_select(props.get('Tournament Tier')),
            'tournament': self._get_text(props.get('Tournament'))
        }
    
    def analyze_candidate(self, candidate: Dict) -> Optional[Dict]:
        """
        Use GPT-4 to deeply analyze a candidate.
        Returns analysis dict with score, recommendation, etc.
        """
        if not self.openai:
            return None
        
        print(f"🤖 Analyzing: {candidate['match_name']}")
        
        # Build analysis prompt
        prompt = self._build_analysis_prompt(candidate)
        
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o",  # or "gpt-4-turbo"
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            analysis_text = response.choices[0].message.content
            
            # Parse GPT response
            analysis = self._parse_gpt_response(analysis_text, candidate)
            
            print(f"  Score: {analysis['score']}/100 | {analysis['recommendation']}")
            
            return analysis
        
        except Exception as e:
            print(f"  ❌ OpenAI error: {e}")
            return None
    
    def _get_system_prompt(self) -> str:
        """System prompt for GPT-4 analyst"""
        return """
You are a professional ITF Women's tennis betting analyst with 20% equity stake.
Your goal: Maximize ROI by identifying value bets with high win probability.

Key expertise:
- ITF W15/W25 markets are inefficient - bookmakers overweight rankings
- Best edge: Ranking delta 80-150 where skill gap is real but odds undervalue favorite
- Low odds (1.25-1.50) are acceptable IF ranking + ELO + form all confirm
- Surface matters: Clay is more predictable, hard court has more variance
- Age matters: 20-24 is prime ITF age, watch for burnout in 26+
- Form is critical: Recent wins > ranking number

Output format (JSON):
{
  "score": 0-100,
  "recommendation": "Strong Bet" | "Good Bet" | "Pass" | "Avoid",
  "confidence": "Very High" | "High" | "Medium" | "Low",
  "ranking_edge_type": "Massive (>100)" | "Strong (50-100)" | "Medium (20-50)" | "Weak (<20)",
  "expected_ev_pct": float,
  "suggested_stake_pct": float,
  "value_flag": boolean,
  "red_flags": "comma,separated,concerns",
  "analysis": "2-3 sentence summary"
}
"""
    
    def _build_analysis_prompt(self, c: Dict) -> str:
        """Build detailed analysis prompt"""
        return f"""
Analyze this ITF Women's tennis match:

Match: {c['player_a']} vs {c['player_b']}
Tournament: {c['tournament']} ({c['tournament_tier']})
Odds (favorite): {c['odds']}

Player A (Favorite):
- Ranking: {c['rank_a'] or 'Unknown'}
- ELO: {c['elo_a'] or 'Unknown'}
- Form: {c['form_a'] or 'Unknown'}

Player B (Underdog):
- Ranking: {c['rank_b'] or 'Unknown'}
- ELO: {c['elo_b'] or 'Unknown'}
- Form: {c['form_b'] or 'Unknown'}

Ranking Delta: {c['rank_delta'] or 'Unknown'}
ELO Delta: {c['elo_delta'] or 'Unknown'}
Surface: {c['surface'] or 'Unknown'}
H2H Record: {c['h2h_record'] or 'No history'}

Key questions:
1. Is the ranking delta real or misleading?
2. Do ELO and form confirm the ranking advantage?
3. Are these odds too low (no value) or acceptable (good value)?
4. Any red flags (injury, surface mismatch, fatigue)?

Provide your analysis in the specified JSON format.
"""
    
    def _parse_gpt_response(self, response_text: str, candidate: Dict) -> Dict:
        """
        Parse GPT-4 response into structured analysis.
        """
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                analysis = self._fallback_parse(response_text)
            
            # Ensure required fields
            return {
                'score': analysis.get('score', 50),
                'recommendation': analysis.get('recommendation', 'Pass'),
                'confidence': analysis.get('confidence', 'Medium'),
                'ranking_edge_type': analysis.get('ranking_edge_type', 'Medium (20-50)'),
                'expected_ev_pct': analysis.get('expected_ev_pct', 0),
                'suggested_stake_pct': analysis.get('suggested_stake_pct', 0),
                'value_flag': analysis.get('value_flag', False),
                'red_flags': analysis.get('red_flags', ''),
                'analysis': analysis.get('analysis', response_text[:500])
            }
        
        except Exception as e:
            print(f"  ⚠️ Parse error: {e}")
            return {
                'score': 40,
                'recommendation': 'Pass',
                'confidence': 'Low',
                'ranking_edge_type': 'Weak (<20)',
                'expected_ev_pct': 0,
                'suggested_stake_pct': 0,
                'value_flag': False,
                'red_flags': 'Analysis failed',
                'analysis': response_text[:500]
            }
    
    def _fallback_parse(self, text: str) -> Dict:
        """Fallback text parsing"""
        score = 50
        if 'strong bet' in text.lower():
            score = 85
            recommendation = 'Strong Bet'
        elif 'good bet' in text.lower():
            score = 70
            recommendation = 'Good Bet'
        elif 'avoid' in text.lower():
            score = 30
            recommendation = 'Avoid'
        else:
            recommendation = 'Pass'
        
        return {
            'score': score,
            'recommendation': recommendation,
            'confidence': 'Medium',
            'ranking_edge_type': 'Medium (20-50)',
            'analysis': text[:500]
        }
    
    def update_candidate(self, page_id: str, analysis: Dict):
        """Update candidate page with AI analysis"""
        if not self.notion:
            return
        
        try:
            properties = {
                'Status': {'select': {'name': 'Analyzed'}},
                'AI Score': {'number': analysis['score']},
                'AI Recommendation': {'select': {'name': analysis['recommendation']}},
                'Confidence': {'select': {'name': analysis['confidence']}},
                'Ranking Edge Type': {'select': {'name': analysis['ranking_edge_type']}},
                'Expected EV %': {'number': analysis['expected_ev_pct']},
                'Suggested Stake %': {'number': analysis['suggested_stake_pct']},
                'Value Flag': {'checkbox': analysis['value_flag']},
                'Red Flags': {'rich_text': [{'text': {'content': analysis['red_flags'][:2000]}}]},
                'AI Analysis': {'rich_text': [{'text': {'content': analysis['analysis'][:2000]}}]}
            }
            
            self.notion.pages.update(
                page_id=page_id,
                properties=properties
            )
        except Exception as e:
            print(f"  ❌ Error updating candidate: {e}")
    
    def promote_to_bets_db(self, candidate: Dict, analysis: Dict):
        """Promote high-score candidates to Bets DB"""
        if not self.notion or not self.bets_db_id:
            return
        
        if analysis['score'] < 80:
            return
        
        print(f"  🎯 Promoting to Bets DB (score: {analysis['score']})")
        
        try:
            self.notion.pages.create(
                parent={'database_id': self.bets_db_id},
                properties={
                    'Name': {'title': [{'text': {'content': candidate['match_name']}}]},
                    'Sport': {'select': {'name': 'Tennis'}},
                    'League': {'select': {'name': 'ITF'}},
                    'Tournament': {'rich_text': [{'text': {'content': candidate['tournament'][:2000]}}]},
                    'Odds (Placed)': {'number': candidate['odds']},
                    'Confidence': {'select': {'name': analysis['confidence']}},
                    'EV %': {'number': analysis['expected_ev_pct']},
                    'Result': {'select': {'name': 'Pending'}},
                    'Strategy': {'select': {'name': 'Prematch'}},
                    'Tags': {'multi_select': [{'name': 'Tennis_screener'}, {'name': 'Automated'}]},
                    'Notes': {'rich_text': [{'text': {'content': f"AI Score: {analysis['score']}/100. {analysis['analysis'][:2000]}"}}]},
                    'Source': {'rich_text': [{'text': {'content': 'Stage 2 AI Analysis'}}]}
                }
            )
            
            # Update candidate status
            self.notion.pages.update(
                page_id=candidate['page_id'],
                properties={'Status': {'select': {'name': 'Promoted'}}}
            )
        
        except Exception as e:
            print(f"  ❌ Error promoting: {e}")
    
    # Helper methods
    def _get_title(self, prop):
        if prop and prop.get('title'):
            return prop['title'][0]['text']['content'] if prop['title'] else ''
        return ''
    
    def _get_text(self, prop):
        if prop and prop.get('rich_text'):
            return prop['rich_text'][0]['text']['content'] if prop['rich_text'] else ''
        return ''
    
    def _get_select(self, prop):
        if prop and prop.get('select'):
            return prop['select']['name']
        return ''
    
    def _get_number(self, prop):
        if prop and 'number' in prop:
            return prop['number']
        return None


def main():
    print("🤖 Stage 2: OpenAI Deep Analysis")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    analyzer = Stage2AIAnalyzer()
    candidates = analyzer.get_pending_candidates()
    
    if not candidates:
        print("⚠️ No candidates to analyze")
        return
    
    print(f"📋 Analyzing {len(candidates)} candidates...\n")
    
    promoted_count = 0
    
    for candidate in candidates:
        analysis = analyzer.analyze_candidate(candidate)
        
        if analysis:
            analyzer.update_candidate(candidate['page_id'], analysis)
            
            if analysis['score'] >= 80:
                analyzer.promote_to_bets_db(candidate, analysis)
                promoted_count += 1
        
        print("")  # Newline
    
    print("="*60)
    print(f"✅ Analysis complete: {len(candidates)} analyzed, {promoted_count} promoted")
    print(f"📊 Next: Review promoted bets in Bets DB")


if __name__ == "__main__":
    main()

