"""
Analytics and performance tracking for live odds monitoring
Provides insights, trends, and optimization recommendations
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import statistics
import json

from storage.odds_database import OddsDatabase, PerformanceRecord
from monitors.value_detector import ValueOpportunity
from config.live_config import LiveMonitoringConfig

logger = logging.getLogger(__name__)

class LiveAnalytics:
    """Analytics engine for live monitoring performance"""
    
    def __init__(self, database: OddsDatabase = None):
        self.config = LiveMonitoringConfig()
        self.db = database or OddsDatabase()
        
    def generate_performance_report(self, days: int = 7) -> Dict:
        """Generate comprehensive performance report"""
        
        try:
            # Get basic performance summary
            summary = self.db.get_performance_summary(days)
            
            # Get recent opportunities for analysis
            opportunities = self.db.get_recent_opportunities(hours=days * 24)
            
            # Calculate advanced metrics
            advanced_metrics = self._calculate_advanced_metrics(opportunities, days)
            
            # Get trend analysis
            trends = self._analyze_trends(days)
            
            # Get league performance breakdown
            league_analysis = self._analyze_league_performance(days)
            
            # Get timing analysis
            timing_analysis = self._analyze_timing_patterns(opportunities)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(summary, advanced_metrics, trends)
            
            report = {
                'report_period': f"Last {days} days",
                'generated_at': datetime.now().isoformat(),
                'summary': summary,
                'advanced_metrics': advanced_metrics,
                'trends': trends,
                'league_analysis': league_analysis,
                'timing_analysis': timing_analysis,
                'recommendations': recommendations
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
            return {}
    
    def _calculate_advanced_metrics(self, opportunities: List[ValueOpportunity], days: int) -> Dict:
        """Calculate advanced performance metrics"""
        
        if not opportunities:
            return {}
        
        # Opportunity quality metrics
        edge_estimates = [opp.edge_estimate for opp in opportunities]
        priority_scores = [opp.priority_score for opp in opportunities]
        time_sensitivities = [opp.time_sensitivity for opp in opportunities]
        
        # Urgency distribution
        urgency_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for opp in opportunities:
            urgency_counts[opp.urgency_level] += 1
        
        # Movement analysis
        entering_count = sum(1 for opp in opportunities if opp.movement_direction == 'entering')
        stable_count = sum(1 for opp in opportunities if opp.movement_direction == 'stable')
        
        # League tier distribution
        tier_counts = {1: 0, 2: 0, 3: 0}
        for opp in opportunities:
            tier = self.config.get_league_tier(opp.league)
            tier_counts[tier] += 1
        
        return {
            'total_opportunities': len(opportunities),
            'opportunities_per_day': round(len(opportunities) / days, 2),
            'avg_edge_estimate': round(statistics.mean(edge_estimates), 2),
            'median_edge_estimate': round(statistics.median(edge_estimates), 2),
            'avg_priority_score': round(statistics.mean(priority_scores), 2),
            'avg_time_sensitivity': round(statistics.mean(time_sensitivities), 2),
            'urgency_distribution': urgency_counts,
            'urgency_percentage': {
                level: round((count / len(opportunities)) * 100, 1)
                for level, count in urgency_counts.items()
            },
            'movement_analysis': {
                'entering_range': entering_count,
                'stable_in_range': stable_count,
                'entering_percentage': round((entering_count / len(opportunities)) * 100, 1)
            },
            'league_tier_distribution': tier_counts,
            'quality_score': self._calculate_quality_score(opportunities)
        }
    
    def _calculate_quality_score(self, opportunities: List[ValueOpportunity]) -> float:
        """Calculate overall quality score (0-100)"""
        
        if not opportunities:
            return 0.0
        
        score = 0.0
        
        # Edge quality (0-40 points)
        avg_edge = statistics.mean([opp.edge_estimate for opp in opportunities])
        edge_score = min(avg_edge * 8, 40)  # Max 40 points for 5%+ edge
        score += edge_score
        
        # Urgency quality (0-30 points)
        high_urgency_pct = sum(1 for opp in opportunities 
                              if opp.urgency_level in ['HIGH', 'CRITICAL']) / len(opportunities)
        urgency_score = high_urgency_pct * 30
        score += urgency_score
        
        # League quality (0-20 points)
        tier1_pct = sum(1 for opp in opportunities 
                       if self.config.get_league_tier(opp.league) == 1) / len(opportunities)
        league_score = tier1_pct * 20
        score += league_score
        
        # Movement quality (0-10 points)
        entering_pct = sum(1 for opp in opportunities 
                          if opp.movement_direction == 'entering') / len(opportunities)
        movement_score = entering_pct * 10
        score += movement_score
        
        return round(score, 1)
    
    def _analyze_trends(self, days: int) -> Dict:
        """Analyze trends over time"""
        
        try:
            trends = {}
            
            # Compare with previous period
            current_summary = self.db.get_performance_summary(days)
            previous_summary = self.db.get_performance_summary(days * 2)
            
            if current_summary and previous_summary:
                # Calculate period-over-period changes
                current_roi = current_summary.get('roi', 0)
                current_bets = current_summary.get('total_bets', 0)
                current_win_rate = current_summary.get('win_rate', 0)
                
                # Estimate previous period values (rough approximation)
                prev_roi = previous_summary.get('roi', 0)
                prev_bets = previous_summary.get('total_bets', 0) - current_bets
                prev_win_rate = previous_summary.get('win_rate', 0)
                
                trends = {
                    'roi_trend': {
                        'current': current_roi,
                        'previous': prev_roi,
                        'change': round(current_roi - prev_roi, 2),
                        'direction': 'up' if current_roi > prev_roi else 'down' if current_roi < prev_roi else 'stable'
                    },
                    'volume_trend': {
                        'current': current_bets,
                        'previous': max(prev_bets, 1),
                        'change': current_bets - prev_bets,
                        'direction': 'up' if current_bets > prev_bets else 'down' if current_bets < prev_bets else 'stable'
                    },
                    'win_rate_trend': {
                        'current': current_win_rate,
                        'previous': prev_win_rate,
                        'change': round(current_win_rate - prev_win_rate, 2),
                        'direction': 'up' if current_win_rate > prev_win_rate else 'down' if current_win_rate < prev_win_rate else 'stable'
                    }
                }
            
            return trends
            
        except Exception as e:
            logger.error(f"Failed to analyze trends: {e}")
            return {}
    
    def _analyze_league_performance(self, days: int) -> Dict:
        """Analyze performance by league"""
        
        try:
            summary = self.db.get_performance_summary(days)
            league_breakdown = summary.get('league_breakdown', {})
            
            # Rank leagues by performance
            league_rankings = []
            for league, data in league_breakdown.items():
                league_rankings.append({
                    'league': league,
                    'count': data['count'],
                    'avg_edge': data['avg_edge'],
                    'tier': self.config.get_league_tier(league)
                })
            
            # Sort by average edge
            league_rankings.sort(key=lambda x: x['avg_edge'], reverse=True)
            
            # Identify best and worst performing leagues
            best_league = league_rankings[0] if league_rankings else None
            worst_league = league_rankings[-1] if league_rankings else None
            
            return {
                'league_rankings': league_rankings,
                'best_performing': best_league,
                'worst_performing': worst_league,
                'tier_performance': self._calculate_tier_performance(league_rankings)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze league performance: {e}")
            return {}
    
    def _calculate_tier_performance(self, league_rankings: List[Dict]) -> Dict:
        """Calculate performance by league tier"""
        
        tier_data = {1: [], 2: [], 3: []}
        
        for league in league_rankings:
            tier = league['tier']
            if tier in tier_data:
                tier_data[tier].append(league['avg_edge'])
        
        tier_performance = {}
        for tier, edges in tier_data.items():
            if edges:
                tier_performance[f'tier_{tier}'] = {
                    'avg_edge': round(statistics.mean(edges), 2),
                    'league_count': len(edges),
                    'best_edge': round(max(edges), 2),
                    'worst_edge': round(min(edges), 2)
                }
        
        return tier_performance
    
    def _analyze_timing_patterns(self, opportunities: List[ValueOpportunity]) -> Dict:
        """Analyze timing patterns in opportunities"""
        
        if not opportunities:
            return {}
        
        # Hour of day analysis
        hour_counts = {}
        for opp in opportunities:
            hour = opp.detected_time.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        # Day of week analysis
        day_counts = {}
        for opp in opportunities:
            day = opp.detected_time.strftime('%A')
            day_counts[day] = day_counts.get(day, 0) + 1
        
        # Find peak hours and days
        peak_hour = max(hour_counts.items(), key=lambda x: x[1]) if hour_counts else (0, 0)
        peak_day = max(day_counts.items(), key=lambda x: x[1]) if day_counts else ('Unknown', 0)
        
        # Time to match analysis
        time_to_match_hours = []
        for opp in opportunities:
            hours_to_match = (opp.commence_time - opp.detected_time).total_seconds() / 3600
            time_to_match_hours.append(hours_to_match)
        
        return {
            'hourly_distribution': hour_counts,
            'daily_distribution': day_counts,
            'peak_hour': {'hour': peak_hour[0], 'count': peak_hour[1]},
            'peak_day': {'day': peak_day[0], 'count': peak_day[1]},
            'avg_time_to_match_hours': round(statistics.mean(time_to_match_hours), 2) if time_to_match_hours else 0,
            'median_time_to_match_hours': round(statistics.median(time_to_match_hours), 2) if time_to_match_hours else 0
        }
    
    def _generate_recommendations(self, summary: Dict, advanced_metrics: Dict, trends: Dict) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        
        recommendations = []
        
        # ROI recommendations
        roi = summary.get('roi', 0)
        if roi < 10:
            recommendations.append("🔴 ROI below target (10%). Consider tightening edge requirements or improving league selection.")
        elif roi > 20:
            recommendations.append("🟢 Excellent ROI! Consider increasing bet volume to maximize profits.")
        
        # Volume recommendations
        opportunities_per_day = advanced_metrics.get('opportunities_per_day', 0)
        if opportunities_per_day < 3:
            recommendations.append("📈 Low opportunity volume. Consider expanding to more leagues or adjusting filters.")
        elif opportunities_per_day > 15:
            recommendations.append("⚠️ High opportunity volume. Ensure quality over quantity - consider raising edge threshold.")
        
        # Quality recommendations
        quality_score = advanced_metrics.get('quality_score', 0)
        if quality_score < 50:
            recommendations.append("🎯 Opportunity quality below optimal. Focus on higher-tier leagues and better edge detection.")
        
        # Urgency recommendations
        urgency_dist = advanced_metrics.get('urgency_percentage', {})
        high_urgency_pct = urgency_dist.get('HIGH', 0) + urgency_dist.get('CRITICAL', 0)
        if high_urgency_pct < 30:
            recommendations.append("⚡ Low urgency opportunities. Consider faster detection or better movement analysis.")
        
        # Trend recommendations
        if trends:
            roi_trend = trends.get('roi_trend', {})
            if roi_trend.get('direction') == 'down':
                recommendations.append("📉 ROI trending down. Review recent betting decisions and market conditions.")
            
            volume_trend = trends.get('volume_trend', {})
            if volume_trend.get('direction') == 'down':
                recommendations.append("📊 Volume trending down. Check system performance and API connectivity.")
        
        # League recommendations
        avg_edge = advanced_metrics.get('avg_edge_estimate', 0)
        if avg_edge < 2:
            recommendations.append("🎲 Low average edge. Focus on Championship and Bundesliga 2 for better opportunities.")
        
        # Default recommendation if none generated
        if not recommendations:
            recommendations.append("✅ System performing well. Continue current strategy and monitor for changes.")
        
        return recommendations
    
    def get_real_time_metrics(self) -> Dict:
        """Get real-time performance metrics"""
        
        try:
            # Get today's data
            today_summary = self.db.get_performance_summary(1)
            today_opportunities = self.db.get_recent_opportunities(24)
            
            # Calculate real-time metrics
            current_hour = datetime.now().hour
            recent_opportunities = [
                opp for opp in today_opportunities 
                if (datetime.now() - opp.detected_time).total_seconds() < 3600
            ]
            
            return {
                'today_opportunities': len(today_opportunities),
                'last_hour_opportunities': len(recent_opportunities),
                'today_avg_edge': round(statistics.mean([opp.edge_estimate for opp in today_opportunities]), 2) if today_opportunities else 0,
                'current_hour': current_hour,
                'system_active': len(recent_opportunities) > 0 or current_hour in [h for start, end in self.config.PEAK_HOURS for h in range(start, end + 1)],
                'last_update': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get real-time metrics: {e}")
            return {}
    
    def export_data(self, days: int = 30, format: str = 'json') -> Optional[str]:
        """Export analytics data for external analysis"""
        
        try:
            # Get comprehensive data
            report = self.generate_performance_report(days)
            opportunities = self.db.get_recent_opportunities(days * 24)
            
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'period_days': days,
                'performance_report': report,
                'raw_opportunities': [
                    {
                        'match_id': opp.match_id,
                        'team': opp.team,
                        'odds': opp.odds,
                        'edge_estimate': opp.edge_estimate,
                        'urgency_level': opp.urgency_level,
                        'league': opp.league,
                        'detected_time': opp.detected_time.isoformat(),
                        'commence_time': opp.commence_time.isoformat()
                    }
                    for opp in opportunities
                ]
            }
            
            if format.lower() == 'json':
                return json.dumps(export_data, indent=2)
            else:
                # Could add CSV, Excel formats here
                return json.dumps(export_data, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return None
