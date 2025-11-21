#!/usr/bin/env python3
"""
🎾 TENNISEXPLORER LIVE MATCH MODELS
===================================

Data models for TennisExplorer live match scraping.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class LiveMatch:
    """TennisExplorer live match data structure"""
    match_id: str
    player_a: str
    player_b: str
    tournament: str
    surface: str
    score: str  # e.g., "6-4, 3-2" or "6-4, 3-2, 1-0"
    start_time: datetime
    match_status: str = "live"  # live, upcoming, finished
    
    # Optional stats
    service_pct_a: Optional[float] = None
    service_pct_b: Optional[float] = None
    break_points_a: Optional[str] = None  # e.g., "2/5" (converted/total)
    break_points_b: Optional[str] = None
    momentum: Optional[str] = None  # "Player A" or "Player B"
    live_odds_a: Optional[float] = None
    live_odds_b: Optional[float] = None
    match_url: Optional[str] = None
    scraped_at: datetime = field(default_factory=datetime.now)
    tournament_tier: Optional[str] = None  # ATP, WTA, ITF, Challenger
    
    def update_stats(self, stats: Dict[str, Any]):
        """Update match with parsed stats"""
        for key, value in stats.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)
    
    def stats_summary(self) -> str:
        """Generate summary string for Notes field"""
        parts = []
        
        if self.service_pct_a is not None and self.service_pct_b is not None:
            parts.append(f"Service: {self.service_pct_a:.1f}% vs {self.service_pct_b:.1f}%")
        
        if self.break_points_a and self.break_points_b:
            parts.append(f"BP: {self.break_points_a} vs {self.break_points_b}")
        
        if self.momentum:
            parts.append(f"Momentum: {self.momentum}")
        
        if self.live_odds_a and self.live_odds_b:
            parts.append(f"Odds: {self.live_odds_a:.2f} / {self.live_odds_b:.2f}")
        
        return " | ".join(parts) if parts else "Live match tracking"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for validation and Notion integration"""
        return {
            "match_id": self.match_id,
            "player_a": self.player_a,
            "player_b": self.player_b,
            "tournament": self.tournament,
            "surface": self.surface,
            "score": self.score,
            "match_status": self.match_status,
            "tournament_tier": self.tournament_tier,
            "start_time": self.start_time.isoformat() if isinstance(self.start_time, datetime) else str(self.start_time),
            "service_pct_a": self.service_pct_a,
            "service_pct_b": self.service_pct_b,
            "break_points_a": self.break_points_a,
            "break_points_b": self.break_points_b,
            "momentum": self.momentum,
            "live_odds_a": self.live_odds_a,
            "live_odds_b": self.live_odds_b,
            "match_url": self.match_url,
            "scraped_at": self.scraped_at.isoformat() if isinstance(self.scraped_at, datetime) else str(self.scraped_at)
        }
    
    def validate(self) -> Dict[str, Any]:
        """Validate match data"""
        errors = []
        warnings = []
        
        # Required fields
        if not self.match_id:
            errors.append({"field": "match_id", "message": "Match ID is required"})
        
        if not self.player_a or len(self.player_a) < 2:
            errors.append({"field": "player_a", "message": "Player A name is required and must be at least 2 characters"})
        
        if not self.player_b or len(self.player_b) < 2:
            errors.append({"field": "player_b", "message": "Player B name is required and must be at least 2 characters"})
        
        if self.player_a == self.player_b:
            errors.append({"field": "players", "message": "Players must be different"})
        
        if not self.tournament:
            warnings.append({"field": "tournament", "message": "Tournament name is missing"})
        
        if not self.surface:
            warnings.append({"field": "surface", "message": "Surface type is missing"})
        
        # Score validation
        if self.match_status == "live" and not self.score:
            warnings.append({"field": "score", "message": "Live match should have a score"})
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

