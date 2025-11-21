#!/usr/bin/env python3
"""
Daily Learning Loop
===================

Scans matches from Stage 1 or other sources, collects comprehensive data,
and saves to Match Results DB for ML training.

Workflow: Scanned → Predicted → Resulted
Collects 100+ matches per day for ML training dataset (1000+ matches total).
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / 'telegram_secrets.env'
if env_path.exists():
    load_dotenv(env_path)

# Import components
from scripts.tennis_ai.stage1_scanner import Stage1Scanner
from scripts.tennis_ai.stage2_ai_analyzer import Stage2AIAnalyzer
from src.notion.match_results_logger import MatchResultsLogger
from scripts.tennis_ai.sportbex_client_simple import SportbexClient

logging_enabled = True
try:
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
except:
    logging_enabled = False
    logger = None


class DailyLearningLoop:
    """Daily learning loop for collecting ML training data"""
    
    def __init__(self):
        self.scanner = Stage1Scanner()
        self.analyzer = None  # Will initialize if needed
        self.logger = MatchResultsLogger()
        self.sportbex = SportbexClient()
    
    def run_daily_scan(self) -> Dict[str, Any]:
        """
        Run daily scan and collect match data
        
        Returns:
            Dictionary with scan results
        """
        print("🔄 Daily Learning Loop - Starting scan...")
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        start_time = datetime.now()
        
        try:
            # Step 1: Scan ITF matches
            print("\n📋 Step 1: Scanning ITF matches...")
            candidates = self.scanner.scan_itf_matches()
            
            if not candidates:
                print("⚠️ No candidates found")
                return {
                    'success': False,
                    'error': 'No candidates found',
                    'timestamp': datetime.now().isoformat()
                }
            
            print(f"✅ Found {len(candidates)} candidates")
            
            # Step 2: Enrich with comprehensive data
            print("\n📊 Step 2: Enriching match data...")
            enriched_matches = []
            
            for candidate in candidates:
                match_data = self._enrich_match_data(candidate)
                enriched_matches.append(match_data)
            
            # Step 3: Save to Match Results DB
            print("\n💾 Step 3: Saving to Match Results DB...")
            results = self.logger.log_matches_batch(enriched_matches)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print("\n" + "="*60)
            print("✅ DAILY LEARNING LOOP COMPLETED")
            print("="*60)
            print(f"📊 Candidates scanned: {len(candidates)}")
            print(f"💾 Matches logged: {results['created']}")
            print(f"⏭️ Duplicates: {results['duplicates']}")
            print(f"❌ Errors: {results['errors']}")
            print(f"⏱️ Duration: {duration:.1f}s")
            print("="*60)
            
            return {
                'success': True,
                'timestamp': end_time.isoformat(),
                'duration_seconds': duration,
                'candidates_scanned': len(candidates),
                'matches_logged': results['created'],
                'duplicates': results['duplicates'],
                'errors': results['errors']
            }
        
        except Exception as e:
            print(f"❌ Error in daily learning loop: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _enrich_match_data(self, candidate: Dict) -> Dict[str, Any]:
        """
        Enrich candidate data with comprehensive match information
        
        Args:
            candidate: Candidate dictionary from Stage 1 scanner
            
        Returns:
            Enriched match data dictionary
        """
        match_data = {
            # Basic Data
            'match_name': candidate.get('match_name', ''),
            'player_a': candidate.get('player_a', ''),
            'player_b': candidate.get('player_b', ''),
            'tournament': candidate.get('tournament', ''),
            'tournament_tier': candidate.get('tournament_tier', ''),
            'event_id': candidate.get('event_id', ''),
            'source': candidate.get('source', 'Stage 1 Scanner'),
            
            # Dates
            'scan_date': datetime.now().isoformat(),
            'match_date': candidate.get('match_time', datetime.now().isoformat()),
            
            # Odds Data (initial - will be updated later)
            'opening_odds_a': candidate.get('odds'),
            'opening_odds_b': None,  # Will be calculated
            'closing_odds_a': None,  # Will be updated when match closes
            'closing_odds_b': None,
            
            # Status
            'status': 'Scanned',
            'data_quality': True,
            
            # Player Stats (will be enriched if available)
            'rank_a': None,
            'rank_b': None,
            'rank_delta': None,
            'elo_a': None,
            'elo_b': None,
            'elo_delta': None,
            'age_a': None,
            'age_b': None,
            'form_a': None,
            'form_b': None,
            'h2h_record': None,
            
            # Surface (if available)
            'surface': None,
            
            # AI Predictions (will be added in Stage 2)
            'gpt4_prediction': None,
            'gpt4_confidence': None,
            'gpt4_score': None,
            'xgboost_probability': None,
            'lightgbm_probability': None,
            'ensemble_score': None,
            'ensemble_prediction': None,
            'model_agreement': None,
            
            # Betting Info (will be added if bet is placed)
            'bet_placed': False,
            'bet_side': None,
            'bet_odds': None,
            'stake_eur': None,
            'stake_pct': None,
            'pnl_eur': None,
            'clv_pct': None,
            
            # Results (will be added when match completes)
            'actual_winner': None,
            'actual_score': None,
            'result_date': None,
        }
        
        # Calculate implied odds for player B
        if match_data['opening_odds_a']:
            match_data['opening_odds_b'] = 1 / (1 - (1 / match_data['opening_odds_a']))
        
        return match_data
    
    def update_with_ai_predictions(self, page_id: str, ai_analysis: Dict[str, Any]) -> bool:
        """
        Update match with AI predictions from Stage 2
        
        Args:
            page_id: Notion page ID
            ai_analysis: AI analysis dictionary from Stage 2
            
        Returns:
            True if successful
        """
        updates = {
            'gpt4_prediction': ai_analysis.get('recommendation', 'Pass'),
            'gpt4_confidence': ai_analysis.get('confidence', 'Medium'),
            'gpt4_score': ai_analysis.get('score', 0),
            'status': 'Predicted'
        }
        
        return self.logger.update_match(page_id, updates)
    
    def update_with_results(self, page_id: str, result_data: Dict[str, Any]) -> bool:
        """
        Update match with actual results
        
        Args:
            page_id: Notion page ID
            result_data: Dictionary with result information
            
        Returns:
            True if successful
        """
        updates = {
            'actual_winner': result_data.get('winner'),
            'actual_score': result_data.get('score'),
            'result_date': result_data.get('result_date', datetime.now().isoformat()),
            'status': 'Resulted',
            'closing_odds_a': result_data.get('closing_odds_a'),
            'closing_odds_b': result_data.get('closing_odds_b'),
        }
        
        # Calculate PnL if bet was placed
        if result_data.get('bet_placed'):
            updates['pnl_eur'] = result_data.get('pnl_eur', 0)
            updates['clv_pct'] = result_data.get('clv_pct', 0)
        
        return self.logger.update_match(page_id, updates)


def main():
    """Main entry point"""
    loop = DailyLearningLoop()
    result = loop.run_daily_scan()
    
    if result.get('success'):
        print("\n✅ Daily learning loop completed successfully!")
        print(f"   Matches logged: {result.get('matches_logged', 0)}")
        sys.exit(0)
    else:
        print(f"\n❌ Daily learning loop failed: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()

