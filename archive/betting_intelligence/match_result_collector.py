#!/usr/bin/env python3
"""
📊 MATCH RESULT COLLECTOR
=========================
Monitors completed matches and updates virtual bets with actual outcomes.
Automatically collects results from scrapers and updates betting tracker.

Author: TennisBot Result Collection System
Version: 1.0.0
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys

# Add project paths
sys.path.append(str(Path(__file__).parent.parent))

from src.virtual_betting_tracker import VirtualBettingTracker

logger = logging.getLogger(__name__)

class MatchResultCollector:
    """Collects match results and updates virtual bets"""
    
    def __init__(
        self,
        virtual_tracker: VirtualBettingTracker,
        check_interval: int = 300,  # 5 minutes
        max_retry_attempts: int = 10,
        retry_delay: int = 600  # 10 minutes
    ):
        """
        Initialize match result collector
        
        Args:
            virtual_tracker: VirtualBettingTracker instance
            check_interval: Seconds between result checks
            max_retry_attempts: Maximum retry attempts for missing results
            retry_delay: Delay between retry attempts (seconds)
        """
        self.tracker = virtual_tracker
        self.check_interval = check_interval
        self.max_retry_attempts = max_retry_attempts
        self.retry_delay = retry_delay
        self.running = False
        
        # Track retry attempts for each match
        self.retry_counts: Dict[str, int] = {}
        
        logger.info("✅ MatchResultCollector initialized")
    
    async def start_collecting(self):
        """Start continuous result collection"""
        self.running = True
        logger.info(f"🔄 Starting match result collection (interval: {self.check_interval}s)")
        
        while self.running:
            try:
                await self._collect_results_cycle()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"❌ Error in result collection cycle: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    def stop_collecting(self):
        """Stop result collection"""
        self.running = False
        logger.info("🛑 Stopping match result collection")
    
    async def _collect_results_cycle(self):
        """Single cycle of result collection"""
        # Get pending bets
        pending_bets = self.tracker.get_pending_bets()
        
        if not pending_bets:
            logger.debug("ℹ️ No pending bets to check")
            return
        
        logger.info(f"🔍 Checking results for {len(pending_bets)} pending bets")
        
        # Check each pending bet
        for bet in pending_bets:
            try:
                # Check if match is old enough to have results (at least 30 minutes after prediction)
                bet_time = datetime.fromisoformat(bet.timestamp)
                time_since_bet = datetime.now() - bet_time
                
                if time_since_bet < timedelta(minutes=30):
                    # Too recent, skip for now
                    continue
                
                # Try to get match result
                result = await self._get_match_result(bet.match_id, bet)
                
                if result:
                    # Update virtual bet with result
                    updated_bet = self.tracker.update_bet_outcome(
                        bet.match_id,
                        result['winner'],
                        force_update=False
                    )
                    
                    if updated_bet:
                        # Reset retry count on success
                        self.retry_counts.pop(bet.match_id, None)
                        logger.info(f"✅ Updated bet for match {bet.match_id}")
                else:
                    # No result found, increment retry count
                    retry_count = self.retry_counts.get(bet.match_id, 0)
                    
                    if retry_count < self.max_retry_attempts:
                        self.retry_counts[bet.match_id] = retry_count + 1
                        logger.debug(
                            f"⏳ No result yet for match {bet.match_id} "
                            f"(retry {retry_count + 1}/{self.max_retry_attempts})"
                        )
                    else:
                        logger.warning(
                            f"⚠️ Max retries reached for match {bet.match_id}, "
                            f"marking as void"
                        )
                        # Mark as void after max retries
                        self._mark_bet_as_void(bet.match_id)
                        self.retry_counts.pop(bet.match_id, None)
                
                # Small delay between matches
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Error processing bet {bet.match_id}: {e}")
                continue
    
    async def _get_match_result(
        self,
        match_id: str,
        bet: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Get match result from available sources
        
        Args:
            match_id: Match identifier
            bet: VirtualBet object with match details
            
        Returns:
            Dict with 'winner' key, or None if not found
        """
        # Try multiple methods to get result
        
        # Method 1: Try to extract from match_id if it contains result info
        # (This depends on your match_id format)
        
        # Method 2: Try scraping from betfury or other sources
        try:
            result = await self._scrape_match_result(match_id, bet)
            if result:
                return result
        except Exception as e:
            logger.debug(f"Scraping failed for {match_id}: {e}")
        
        # Method 3: Try API sources if available
        try:
            result = await self._get_result_from_api(match_id, bet)
            if result:
                return result
        except Exception as e:
            logger.debug(f"API lookup failed for {match_id}: {e}")
        
        return None
    
    async def _scrape_match_result(
        self,
        match_id: str,
        bet: Any
    ) -> Optional[Dict[str, Any]]:
        """Try to scrape match result from web sources"""
        try:
            # Import scrapers dynamically to avoid circular imports
            from src.scrapers.betfury_scraper import BetfuryScraper
            from src.scrapers.flashscore_scraper import FlashscoreScraper
            
            # Try Betfury scraper first
            try:
                scraper = BetfuryScraper()
                # This would need to be implemented in the scraper
                # result = await scraper.get_match_result(match_id)
                # if result:
                #     return {'winner': result['winner']}
            except Exception as e:
                logger.debug(f"Betfury scraper error: {e}")
            
            # Try Flashscore scraper
            try:
                scraper = FlashscoreScraper()
                # result = await scraper.get_match_result(match_id)
                # if result:
                #     return {'winner': result['winner']}
            except Exception as e:
                logger.debug(f"Flashscore scraper error: {e}")
            
        except ImportError:
            logger.debug("Scrapers not available")
        
        return None
    
    async def _get_result_from_api(
        self,
        match_id: str,
        bet: Any
    ) -> Optional[Dict[str, Any]]:
        """Try to get match result from API sources"""
        try:
            # Try Odds API if available
            from src.odds_api_integration import OddsAPIIntegration
            
            odds_api = OddsAPIIntegration()
            # This would need to be implemented
            # result = await odds_api.get_match_result(match_id)
            # if result:
            #     return {'winner': result['winner']}
            
        except ImportError:
            logger.debug("Odds API not available")
        except Exception as e:
            logger.debug(f"API lookup error: {e}")
        
        return None
    
    def _mark_bet_as_void(self, match_id: str):
        """Mark a bet as void (no result found after max retries)"""
        try:
            import sqlite3
            from datetime import datetime
            
            with sqlite3.connect(self.tracker.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE virtual_bets
                    SET status = 'void', updated_at = ?
                    WHERE match_id = ? AND status = 'pending'
                ''', (datetime.now().isoformat(), match_id))
                conn.commit()
            
            logger.info(f"✅ Marked bet {match_id} as void")
        except Exception as e:
            logger.error(f"❌ Error marking bet as void: {e}")
    
    async def update_result_manually(
        self,
        match_id: str,
        winner: str
    ) -> bool:
        """
        Manually update match result (useful for testing or manual entry)
        
        Args:
            match_id: Match identifier
            winner: Actual winner name
            
        Returns:
            True if successful
        """
        try:
            updated_bet = self.tracker.update_bet_outcome(match_id, winner, force_update=True)
            if updated_bet:
                logger.info(f"✅ Manually updated result for {match_id}: {winner}")
                return True
            else:
                logger.warning(f"⚠️ No bet found for match {match_id}")
                return False
        except Exception as e:
            logger.error(f"❌ Error manually updating result: {e}")
            return False
    
    def get_pending_matches(self) -> List[Dict[str, Any]]:
        """Get list of matches with pending bets"""
        pending_bets = self.tracker.get_pending_bets()
        return [
            {
                'match_id': bet.match_id,
                'prediction': bet.prediction,
                'home_player': bet.home_player,
                'away_player': bet.away_player,
                'surface': bet.surface,
                'tournament': bet.tournament,
                'timestamp': bet.timestamp,
                'retry_count': self.retry_counts.get(bet.match_id, 0)
            }
            for bet in pending_bets
        ]

