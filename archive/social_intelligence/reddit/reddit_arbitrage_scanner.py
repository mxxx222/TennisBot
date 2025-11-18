"""
Reddit Arbitrage Scanner

Phase 1: Real-time arbitrage opportunity mining from Reddit
Scans r/sportsbook, r/sportsbetting, r/gambling for arbitrage mentions
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from .reddit_client import RedditClient
from .reddit_utils import (
    extract_odds_from_text,
    extract_bookmaker_names,
    extract_match_info,
    generate_post_id,
    is_recent_post,
    clean_reddit_text
)
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.reddit_config import RedditConfig

logger = logging.getLogger(__name__)

@dataclass
class RedditArbitrageOpportunity:
    """Arbitrage opportunity found on Reddit"""
    opportunity_id: str
    post_id: str
    post_title: str
    post_url: str
    subreddit: str
    match_info: Optional[Dict[str, str]]
    extracted_odds: List[Dict[str, Any]]
    bookmakers_mentioned: List[str]
    profit_percentage: float
    confidence_score: float
    post_score: int
    post_age_hours: float
    raw_text: str
    timestamp: str

class RedditArbitrageScanner:
    """Scan Reddit for arbitrage opportunities"""
    
    def __init__(self, config: Optional[RedditConfig] = None):
        self.config = config or RedditConfig
        self.reddit_client = RedditClient(self.config)
        self.scanned_posts = set()  # Track already scanned posts
        self.opportunities_found = []
        
        logger.info("🎯 Reddit Arbitrage Scanner initialized")
    
    async def scan_for_arbitrage_opportunities(
        self,
        max_posts_per_subreddit: int = 50
    ) -> List[RedditArbitrageOpportunity]:
        """
        Scan Reddit subreddits for arbitrage opportunities
        
        Args:
            max_posts_per_subreddit: Maximum posts to scan per subreddit
        
        Returns:
            List of arbitrage opportunities found
        """
        if not self.reddit_client.is_available:
            logger.warning("⚠️ Reddit API not available, skipping arbitrage scan")
            return []
        
        logger.info("🔍 Scanning Reddit for arbitrage opportunities...")
        
        all_opportunities = []
        
        for subreddit_name in self.config.ARBITRAGE_SUBREDDITS:
            try:
                logger.info(f"📊 Scanning r/{subreddit_name}...")
                
                # Get recent posts
                posts = self.reddit_client.get_subreddit_posts(
                    subreddit_name=subreddit_name,
                    limit=max_posts_per_subreddit,
                    sort='new',
                    time_filter='day'
                )
                
                # Also search for arbitrage keywords
                for keyword in self.config.ARBITRAGE_KEYWORDS[:3]:  # Top 3 keywords
                    search_posts = self.reddit_client.search_subreddit(
                        subreddit_name=subreddit_name,
                        query=keyword,
                        limit=25,
                        sort='new',
                        time_filter='day'
                    )
                    # Merge with main posts (deduplicate by ID)
                    existing_ids = {p['id'] for p in posts}
                    posts.extend([p for p in search_posts if p['id'] not in existing_ids])
                
                # Scan each post
                for post in posts:
                    # Skip if already scanned
                    post_key = f"{subreddit_name}_{post['id']}"
                    if post_key in self.scanned_posts:
                        continue
                    
                    # Only scan recent posts (last 24 hours)
                    if not is_recent_post(post, max_age_hours=24):
                        continue
                    
                    # Check if post contains arbitrage indicators
                    if self._contains_arbitrage_indicators(post):
                        opportunity = await self._extract_arbitrage_opportunity(post, subreddit_name)
                        if opportunity:
                            all_opportunities.append(opportunity)
                            self.scanned_posts.add(post_key)
                
                logger.info(f"✅ Scanned r/{subreddit_name}: {len(posts)} posts")
                
            except Exception as e:
                logger.error(f"❌ Error scanning r/{subreddit_name}: {e}")
                continue
        
        # Sort by profit percentage (highest first)
        all_opportunities.sort(key=lambda x: x.profit_percentage, reverse=True)
        
        # Filter by minimum margin
        filtered_opportunities = [
            opp for opp in all_opportunities
            if opp.profit_percentage >= (self.config.MIN_REDDIT_ARB_MARGIN * 100)
        ]
        
        logger.info(f"💰 Found {len(filtered_opportunities)} arbitrage opportunities from Reddit")
        self.opportunities_found.extend(filtered_opportunities)
        
        return filtered_opportunities
    
    def _contains_arbitrage_indicators(self, post: Dict[str, Any]) -> bool:
        """Check if post contains arbitrage-related keywords"""
        title = post.get('title', '').lower()
        text = post.get('selftext', '').lower()
        combined_text = f"{title} {text}"
        
        # Check for arbitrage keywords
        for keyword in self.config.ARBITRAGE_KEYWORDS:
            if keyword.lower() in combined_text:
                return True
        
        return False
    
    async def _extract_arbitrage_opportunity(
        self,
        post: Dict[str, Any],
        subreddit_name: str
    ) -> Optional[RedditArbitrageOpportunity]:
        """
        Extract arbitrage opportunity data from a Reddit post
        
        Args:
            post: Reddit post data
            subreddit_name: Name of subreddit
        
        Returns:
            Arbitrage opportunity if valid, None otherwise
        """
        try:
            title = post.get('title', '')
            text = post.get('selftext', '')
            combined_text = f"{title} {text}"
            cleaned_text = clean_reddit_text(combined_text)
            
            # Extract odds from text
            extracted_odds = extract_odds_from_text(cleaned_text)
            if not extracted_odds or len(extracted_odds) < 2:
                # Need at least 2 odds for arbitrage
                return None
            
            # Extract bookmaker names
            bookmakers = extract_bookmaker_names(cleaned_text)
            
            # Extract match information
            match_info = extract_match_info(cleaned_text)
            
            # Calculate potential profit percentage
            profit_percentage = self._calculate_profit_from_odds(extracted_odds)
            
            if profit_percentage < (self.config.MIN_REDDIT_ARB_MARGIN * 100):
                return None
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                post, extracted_odds, bookmakers, match_info
            )
            
            # Calculate post age
            created_utc = post.get('created_utc', 0)
            post_age_hours = (datetime.now().timestamp() - created_utc) / 3600 if created_utc else 0
            
            # Generate opportunity ID
            opportunity_id = generate_post_id(post)
            
            opportunity = RedditArbitrageOpportunity(
                opportunity_id=opportunity_id,
                post_id=post.get('id', ''),
                post_title=title[:200],  # Limit title length
                post_url=f"https://reddit.com{post.get('permalink', '')}",
                subreddit=subreddit_name,
                match_info=match_info,
                extracted_odds=extracted_odds,
                bookmakers_mentioned=bookmakers,
                profit_percentage=profit_percentage,
                confidence_score=confidence_score,
                post_score=post.get('score', 0),
                post_age_hours=round(post_age_hours, 2),
                raw_text=cleaned_text[:1000],  # Limit text length
                timestamp=datetime.now().isoformat()
            )
            
            return opportunity
            
        except Exception as e:
            logger.debug(f"Error extracting arbitrage from post {post.get('id', 'unknown')}: {e}")
            return None
    
    def _calculate_profit_from_odds(self, extracted_odds: List[Dict[str, Any]]) -> float:
        """
        Calculate potential profit percentage from extracted odds
        
        This is a simplified calculation - real arbitrage would need
        to match odds to specific outcomes (home/away/draw)
        """
        if len(extracted_odds) < 2:
            return 0.0
        
        # Get all odds values
        odds_values = []
        for odds_data in extracted_odds:
            if isinstance(odds_data['odds'], list):
                odds_values.extend(odds_data['odds'])
            else:
                odds_values.append(odds_data['odds'])
        
        if len(odds_values) < 2:
            return 0.0
        
        # Find best odds (highest values)
        best_odds = sorted(odds_values, reverse=True)[:3]  # Top 3 odds
        
        # Calculate implied probabilities
        probabilities = [1 / odds for odds in best_odds if odds > 1]
        
        if not probabilities:
            return 0.0
        
        # Calculate total probability (for arbitrage, should be < 1.0)
        total_probability = sum(probabilities[:2])  # For 2-way arbitrage
        
        if total_probability >= 1.0:
            return 0.0
        
        # Profit margin
        margin = 1.0 - total_probability
        profit_percentage = margin * 100
        
        return round(profit_percentage, 2)
    
    def _calculate_confidence_score(
        self,
        post: Dict[str, Any],
        extracted_odds: List[Dict[str, Any]],
        bookmakers: List[str],
        match_info: Optional[Dict[str, str]]
    ) -> float:
        """Calculate confidence score for the arbitrage opportunity"""
        score = 0.0
        
        # Base score for having odds
        if len(extracted_odds) >= 2:
            score += 0.3
        
        # Bonus for multiple odds
        if len(extracted_odds) >= 3:
            score += 0.2
        
        # Bonus for bookmaker mentions
        if bookmakers:
            score += 0.2
            if len(bookmakers) >= 2:
                score += 0.1
        
        # Bonus for match information
        if match_info:
            score += 0.1
        
        # Bonus for post score (upvotes)
        post_score = post.get('score', 0)
        if post_score > 5:
            score += 0.1
        if post_score > 20:
            score += 0.1
        
        # Penalty for very new posts (might be spam)
        post_age_hours = (datetime.now().timestamp() - post.get('created_utc', 0)) / 3600
        if post_age_hours < 0.5:  # Less than 30 minutes old
            score -= 0.1
        
        return min(1.0, max(0.0, score))
    
    def convert_to_roi_analyzer_format(
        self,
        opportunities: List[RedditArbitrageOpportunity]
    ) -> Dict[str, List[Dict]]:
        """
        Convert Reddit arbitrage opportunities to format expected by ROIAnalyzer
        
        Returns:
            Dictionary in format: {bookmaker: [match_odds_dict, ...]}
        """
        odds_data = {}
        
        for opp in opportunities:
            if not opp.match_info:
                continue
            
            home_team = opp.match_info.get('home_team', '')
            away_team = opp.match_info.get('away_team', '')
            
            if not home_team or not away_team:
                continue
            
            # Extract odds for each bookmaker mentioned
            for bookmaker in opp.bookmakers_mentioned or ['reddit_unknown']:
                if bookmaker not in odds_data:
                    odds_data[bookmaker] = []
                
                # Try to match odds to outcomes
                # This is simplified - real implementation would need better matching
                home_odds = None
                away_odds = None
                draw_odds = None
                
                for odds_info in opp.extracted_odds:
                    odds_value = odds_info.get('odds')
                    if isinstance(odds_value, list):
                        if len(odds_value) >= 2:
                            home_odds = odds_value[0]
                            away_odds = odds_value[1]
                    elif odds_value:
                        # Single odds - assign to home if not set
                        if home_odds is None:
                            home_odds = odds_value
                        elif away_odds is None:
                            away_odds = odds_value
                        elif draw_odds is None:
                            draw_odds = odds_value
                
                if home_odds and away_odds:
                    match_odds = {
                        'home_team': home_team,
                        'away_team': away_team,
                        'home_odds': home_odds,
                        'away_odds': away_odds,
                        'draw_odds': draw_odds,
                        'source': 'reddit',
                        'reddit_opportunity_id': opp.opportunity_id,
                        'reddit_url': opp.post_url
                    }
                    odds_data[bookmaker].append(match_odds)
        
        return odds_data
    
    def get_opportunities_summary(self) -> Dict[str, Any]:
        """Get summary of opportunities found"""
        if not self.opportunities_found:
            return {
                'total_opportunities': 0,
                'total_profit_potential': 0.0,
                'average_profit': 0.0,
                'highest_profit': 0.0
            }
        
        total_profit = sum(opp.profit_percentage for opp in self.opportunities_found)
        avg_profit = total_profit / len(self.opportunities_found)
        highest_profit = max(opp.profit_percentage for opp in self.opportunities_found)
        
        return {
            'total_opportunities': len(self.opportunities_found),
            'total_profit_potential': round(total_profit, 2),
            'average_profit': round(avg_profit, 2),
            'highest_profit': round(highest_profit, 2),
            'subreddits_scanned': self.config.ARBITRAGE_SUBREDDITS
        }

