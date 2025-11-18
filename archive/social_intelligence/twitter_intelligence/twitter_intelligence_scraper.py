"""
Twitter Intelligence Scraper

Main scraper for Twitter betting intelligence
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.twitter_config import TwitterConfig

from .twitter_client import TwitterIntelligenceClient
from .verified_capper_tracker import VerifiedCapperTracker, CapperPick
from .hashtag_monitor import HashtagMonitor, HashtagOpportunity
from .performance_tracker import PerformanceTracker

logger = logging.getLogger(__name__)

class TwitterIntelligenceScraper:
    """Scrape betting intelligence from Twitter"""
    
    def __init__(self, config: Optional[TwitterConfig] = None):
        self.config = config or TwitterConfig
        self.client = TwitterIntelligenceClient(self.config)
        self.capper_tracker = VerifiedCapperTracker()
        self.hashtag_monitor = HashtagMonitor()
        self.performance_tracker = PerformanceTracker()
        
        logger.info("🎯 Twitter Intelligence Scraper initialized")
    
    async def scrape_verified_cappers(self) -> List[CapperPick]:
        """Scrape picks from verified cappers"""
        if not self.client.is_available:
            return []
        
        logger.info("🔍 Scraping verified capper picks...")
        
        picks = await self.capper_tracker.track_verified_cappers(
            self.config.VERIFIED_CAPPERS
        )
        
        logger.info(f"✅ Found {len(picks)} picks from verified cappers")
        return picks
    
    async def scrape_hashtag_opportunities(self) -> List[HashtagOpportunity]:
        """Scrape opportunities from hashtags"""
        if not self.client.is_available:
            return []
        
        logger.info("🔍 Scraping hashtag opportunities...")
        
        opportunities = await self.hashtag_monitor.monitor_hashtags(
            self.config.HASHTAGS
        )
        
        logger.info(f"✅ Found {len(opportunities)} hashtag opportunities")
        return opportunities
    
    async def cross_validate_capper_picks(
        self,
        capper_picks: List[CapperPick],
        our_predictions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Cross-validate capper picks with our predictions"""
        validated = []
        
        for pick in capper_picks:
            # Find matching prediction
            for prediction in our_predictions:
                pred_match = prediction.get('match_info', {})
                if isinstance(pred_match, dict):
                    if (pick.match_info.get('home_team', '').lower() in 
                        pred_match.get('home_team', '').lower()):
                        
                        # Check agreement
                        our_selection = prediction.get('recommended_bet', '').lower()
                        pick_selection = pick.selection.lower()
                        
                        if pick_selection in our_selection or our_selection in pick_selection:
                            # Capper agrees - boost confidence
                            enhanced = prediction.copy()
                            from config.twitter_config import TwitterConfig
                            
                            original_confidence = enhanced.get('confidence_score', 0.5)
                            
                            # Higher boost for high engagement
                            boost_multiplier = TwitterConfig.VERIFIED_CAPPER_BOOST
                            if pick.engagement_rate > 0.1:  # High engagement
                                boost_multiplier = TwitterConfig.HIGH_ENGAGEMENT_BOOST
                            
                            enhanced['confidence_score'] = min(
                                1.0,
                                original_confidence * boost_multiplier
                            )
                            enhanced['twitter_validation'] = {
                                'capper': pick.username,
                                'engagement_rate': pick.engagement_rate,
                                'pick_id': pick.pick_id
                            }
                            
                            validated.append(enhanced)
        
        return validated
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of Twitter intelligence"""
        top_cappers = self.performance_tracker.get_top_cappers(limit=5)
        
        return {
            'top_cappers': [
                {
                    'username': c.username,
                    'win_rate': c.win_rate,
                    'roi': c.roi,
                    'total_picks': c.total_picks
                }
                for c in top_cappers
            ],
            'total_tracked_cappers': len(self.performance_tracker.capper_performance),
            'profitable_cappers': len([
                c for c in self.performance_tracker.capper_performance.values()
                if self.performance_tracker.is_profitable_capper(c.username)
            ])
        }

