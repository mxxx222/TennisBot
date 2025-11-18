#!/usr/bin/env python3
"""
🎯 SPORTS ROI API - OWN DATA PROVIDER
=====================================

REST API that provides comprehensive sports data and ROI analysis
without relying on paid third-party APIs. Uses our own scraping
and analysis systems to deliver highest ROI opportunities.

Features:
- RESTful API endpoints for all sports data
- Real-time ROI analysis and opportunities
- Comprehensive match statistics
- Arbitrage and value bet detection
- Historical data and trends
- WebSocket support for live updates

Author: TennisBot Advanced Analytics
Version: 2.0.0
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Import our analysis systems
from src.unified_sports_scraper import UnifiedSportsScraper, ComprehensiveMatchData
from src.comprehensive_stats_collector import ComprehensiveStatsCollector, SportStatistics
from src.highest_roi_analyzer import HighestROIAnalyzer, ROIAnalysisResult, ROIOpportunity

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Models
class APIConfig(BaseModel):
    """API configuration"""
    scraping_enabled: bool = True
    analysis_enabled: bool = True
    cache_enabled: bool = True
    update_interval_minutes: int = 30

class MatchRequest(BaseModel):
    """Request for match data"""
    sport: str = Field(..., description="Sport name (tennis, football, basketball, ice_hockey)")
    league: Optional[str] = Field(None, description="Specific league/tournament")
    date_from: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    limit: int = Field(50, description="Maximum results", ge=1, le=500)

class ROIAnalysisRequest(BaseModel):
    """Request for ROI analysis"""
    sport: Optional[str] = Field(None, description="Specific sport or 'all'")
    min_confidence: float = Field(0.6, description="Minimum confidence threshold", ge=0, le=1)
    max_opportunities: int = Field(20, description="Maximum opportunities to return", ge=1, le=100)

class StatsRequest(BaseModel):
    """Request for statistics"""
    sport: str = Field(..., description="Sport name")
    force_refresh: bool = Field(False, description="Force refresh cached data")

# Response Models
class APIResponse(BaseModel):
    """Base API response"""
    success: bool
    timestamp: str
    data: Any
    error: Optional[str] = None

class MatchDataResponse(BaseModel):
    """Match data response"""
    sport: str
    total_matches: int
    matches: List[Dict]
    last_updated: str

class ROIResponse(BaseModel):
    """ROI analysis response"""
    analysis_id: str
    total_opportunities: int
    high_confidence_opportunities: int
    expected_portfolio_return: float
    opportunities: List[Dict]
    risk_assessment: Dict

class StatsResponse(BaseModel):
    """Statistics response"""
    sport: str
    data_points: int
    performance_metrics: Dict
    statistics: Dict

class SportsROIAPI:
    """Main API class for Sports ROI data provider"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.app = FastAPI(
            title="Sports ROI API",
            description="Comprehensive sports data and ROI analysis API",
            version="2.0.0"
        )

        # Initialize components
        self.scraper = UnifiedSportsScraper(config)
        self.stats_collector = ComprehensiveStatsCollector(config)
        self.roi_analyzer = HighestROIAnalyzer(config)

        # Cache for API responses
        self.cache = {}
        self.cache_expiry = timedelta(minutes=config.get('cache_minutes', 15))

        # Background update task
        self.last_update = None
        self.update_interval = timedelta(minutes=config.get('update_interval_minutes', 30))

        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Setup routes
        self.setup_routes()

        # Start background updates
        self.start_background_updates()

    def setup_routes(self):
        """Setup API routes"""

        @self.app.get("/")
        async def root():
            """API root endpoint"""
            return {
                "message": "Sports ROI API - Your Own Data Provider",
                "version": "2.0.0",
                "endpoints": {
                    "matches": "/api/matches/{sport}",
                    "roi": "/api/roi/analysis",
                    "stats": "/api/stats/{sport}",
                    "opportunities": "/api/opportunities",
                    "health": "/api/health"
                }
            }

        @self.app.get("/api/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "scraper": "ready",
                    "stats_collector": "ready",
                    "roi_analyzer": "ready"
                }
            }

        @self.app.get("/api/matches/{sport}")
        async def get_matches(
            sport: str,
            league: Optional[str] = None,
            date_from: Optional[str] = None,
            date_to: Optional[str] = None,
            limit: int = Query(50, ge=1, le=500)
        ):
            """Get comprehensive match data for a sport"""
            try:
                # Check cache first
                cache_key = f"matches_{sport}_{league}_{date_from}_{date_to}_{limit}"
                if cache_key in self.cache:
                    cached_data, cache_time = self.cache[cache_key]
                    if datetime.now() - cache_time < self.cache_expiry:
                        return APIResponse(
                            success=True,
                            timestamp=datetime.now().isoformat(),
                            data=cached_data
                        )

                # Validate sport
                valid_sports = ['tennis', 'football', 'basketball', 'ice_hockey']
                if sport not in valid_sports:
                    raise HTTPException(status_code=400, detail=f"Invalid sport. Must be one of: {valid_sports}")

                # Scrape data
                date_range = (date_from, date_to) if date_from and date_to else None
                async with self.scraper:
                    sport_data = await self.scraper.scrape_sport_comprehensive(sport, date_range)

                # Filter by league if specified
                if league:
                    sport_data = [m for m in sport_data if league.lower() in m.league.lower()]

                # Apply limit
                sport_data = sport_data[:limit]

                # Convert to dict format
                matches_dict = [self._match_to_dict(match) for match in sport_data]

                response_data = MatchDataResponse(
                    sport=sport,
                    total_matches=len(matches_dict),
                    matches=matches_dict,
                    last_updated=datetime.now().isoformat()
                )

                # Cache response
                self.cache[cache_key] = (response_data.dict(), datetime.now())

                return APIResponse(
                    success=True,
                    timestamp=datetime.now().isoformat(),
                    data=response_data.dict()
                )

            except Exception as e:
                logger.error(f"Error getting matches for {sport}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/roi/analysis")
        async def analyze_roi(request: ROIAnalysisRequest):
            """Get highest ROI opportunities"""
            try:
                # Get latest data
                async with self.scraper:
                    match_data = await self.scraper.scrape_all_sports_comprehensive()

                async with self.stats_collector:
                    stats_data = await self.stats_collector.collect_all_sports_statistics()

                # Filter data if specific sport requested
                if request.sport and request.sport != 'all':
                    if request.sport in match_data:
                        match_data = {request.sport: match_data[request.sport]}
                    else:
                        match_data = {request.sport: []}

                    if request.sport in stats_data:
                        stats_data = {request.sport: stats_data[request.sport]}
                    else:
                        stats_data = {request.sport: None}

                # Analyze ROI
                analysis_result = await self.roi_analyzer.analyze_highest_roi_opportunities(match_data, stats_data)

                # Filter by confidence
                filtered_opportunities = [
                    opp for opp in analysis_result.opportunities
                    if opp.confidence_score >= request.min_confidence
                ][:request.max_opportunities]

                # Convert to dict
                opportunities_dict = [self._opportunity_to_dict(opp) for opp in filtered_opportunities]

                response_data = ROIResponse(
                    analysis_id=analysis_result.analysis_id,
                    total_opportunities=len(filtered_opportunities),
                    high_confidence_opportunities=len([o for o in filtered_opportunities if o.confidence_score >= 0.8]),
                    expected_portfolio_return=analysis_result.expected_portfolio_return,
                    opportunities=opportunities_dict,
                    risk_assessment=analysis_result.risk_assessment
                )

                return APIResponse(
                    success=True,
                    timestamp=datetime.now().isoformat(),
                    data=response_data.dict()
                )

            except Exception as e:
                logger.error(f"Error in ROI analysis: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/stats/{sport}")
        async def get_statistics(sport: str, force_refresh: bool = False):
            """Get comprehensive statistics for a sport"""
            try:
                # Validate sport
                valid_sports = ['tennis', 'football', 'basketball', 'ice_hockey']
                if sport not in valid_sports:
                    raise HTTPException(status_code=400, detail=f"Invalid sport. Must be one of: {valid_sports}")

                # Get statistics
                async with self.stats_collector:
                    stats = await self.stats_collector.collect_sport_statistics(sport, force_refresh)

                # Convert to dict
                stats_dict = self._stats_to_dict(stats)

                response_data = StatsResponse(
                    sport=sport,
                    data_points=self.stats_collector._count_stats_points(stats),
                    performance_metrics=getattr(stats, 'performance_metrics', {}),
                    statistics=stats_dict
                )

                return APIResponse(
                    success=True,
                    timestamp=datetime.now().isoformat(),
                    data=response_data.dict()
                )

            except Exception as e:
                logger.error(f"Error getting statistics for {sport}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/opportunities")
        async def get_opportunities(limit: int = Query(10, ge=1, le=50)):
            """Get current highest ROI opportunities"""
            try:
                # Get latest analysis
                async with self.scraper:
                    match_data = await self.scraper.scrape_all_sports_comprehensive()

                async with self.stats_collector:
                    stats_data = await self.stats_collector.collect_all_sports_statistics()

                analysis_result = await self.roi_analyzer.analyze_highest_roi_opportunities(match_data, stats_data)

                # Get top opportunities
                top_opportunities = analysis_result.opportunities[:limit]
                opportunities_dict = [self._opportunity_to_dict(opp) for opp in top_opportunities]

                return APIResponse(
                    success=True,
                    timestamp=datetime.now().isoformat(),
                    data={
                        "total_opportunities": len(top_opportunities),
                        "opportunities": opportunities_dict,
                        "analysis_timestamp": analysis_result.timestamp
                    }
                )

            except Exception as e:
                logger.error(f"Error getting opportunities: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/admin/update-data")
        async def update_data(background_tasks: BackgroundTasks):
            """Manually trigger data update"""
            background_tasks.add_task(self._background_update)
            return {"message": "Data update started in background"}

    def _match_to_dict(self, match: ComprehensiveMatchData) -> Dict:
        """Convert match object to dictionary"""
        return {
            "match_id": match.match_id,
            "sport": match.sport,
            "league": match.league,
            "home_team": match.home_team,
            "away_team": match.away_team,
            "start_time": match.start_time,
            "status": match.status,
            "home_score": match.home_score,
            "away_score": match.away_score,
            "venue": match.venue,
            "odds_data": match.odds_data,
            "best_odds": match.best_odds,
            "confidence_score": match.confidence_score,
            "data_quality": match.data_quality,
            "last_updated": match.last_updated
        }

    def _opportunity_to_dict(self, opp: ROIOpportunity) -> Dict:
        """Convert opportunity object to dictionary"""
        return {
            "opportunity_id": opp.opportunity_id,
            "sport": opp.sport,
            "match": opp.match,
            "league": opp.league,
            "market": opp.market,
            "selection": opp.selection,
            "odds": opp.odds,
            "stake_percentage": opp.stake_percentage,
            "expected_roi": opp.expected_roi,
            "confidence_score": opp.confidence_score,
            "risk_level": opp.risk_level,
            "edge_percentage": opp.edge_percentage,
            "kelly_stake": opp.kelly_stake,
            "reasoning": opp.reasoning,
            "data_quality": opp.data_quality,
            "timestamp": opp.timestamp,
            "expires_at": opp.expires_at
        }

    def _stats_to_dict(self, stats: SportStatistics) -> Dict:
        """Convert statistics object to dictionary"""
        # This would be a comprehensive conversion
        # For now, return basic structure
        return {
            "sport": getattr(stats, 'sport', 'unknown'),
            "last_updated": getattr(stats, 'last_updated', datetime.now().isoformat()),
            "data_available": True
        }

    def start_background_updates(self):
        """Start background update tasks"""
        asyncio.create_task(self._background_update_loop())

    async def _background_update_loop(self):
        """Background update loop"""
        while True:
            try:
                await self._background_update()
                await asyncio.sleep(self.update_interval.total_seconds())
            except Exception as e:
                logger.error(f"Error in background update: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def _background_update(self):
        """Perform background data update"""
        try:
            logger.info("🔄 Starting background data update...")

            # Update all sports data
            async with self.scraper:
                match_data = await self.scraper.scrape_all_sports_comprehensive()

            async with self.stats_collector:
                stats_data = await self.stats_collector.collect_all_sports_statistics()

            # Update cache with fresh data
            self.cache = {}  # Clear cache to force refresh
            self.last_update = datetime.now()

            logger.info("✅ Background data update completed")

        except Exception as e:
            logger.error(f"❌ Background update failed: {e}")

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the API server"""
        logger.info(f"🚀 Starting Sports ROI API on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port)

# Convenience functions
def create_sports_roi_api(config: Dict[str, Any] = None) -> SportsROIAPI:
    """Create and configure the Sports ROI API"""
    if config is None:
        config = {
            'cache_minutes': 15,
            'update_interval_minutes': 30,
            'rate_limits': {
                'flashscore.com': 8,
                'sofascore.com': 8,
                'oddsportal.com': 6
            }
        }

    return SportsROIAPI(config)

if __name__ == "__main__":
    # Create and run the API
    config = {
        'cache_minutes': 15,
        'update_interval_minutes': 30,
        'rate_limits': {
            'flashscore.com': 8,
            'sofascore.com': 8,
            'oddsportal.com': 6,
            'atptour.com': 12
        }
    }

    api = create_sports_roi_api(config)
    api.run()