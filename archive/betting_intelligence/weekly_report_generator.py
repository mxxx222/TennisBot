#!/usr/bin/env python3
"""
📊 WEEKLY REPORT GENERATOR
===========================

Generates weekly reports and stores them in Notion database.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.notion.project_status_manager import ProjectStatusManager

logger = logging.getLogger(__name__)


class WeeklyReportGenerator:
    """Generates weekly reports for historical analysis"""
    
    def __init__(self, status_manager: Optional[ProjectStatusManager] = None):
        """
        Initialize weekly report generator
        
        Args:
            status_manager: ProjectStatusManager instance
        """
        self.status_manager = status_manager or ProjectStatusManager()
        logger.info("📊 Weekly Report Generator initialized")
    
    def generate_weekly_report(self, metrics: Dict, start_date: datetime, end_date: datetime) -> Dict:
        """
        Generate weekly report from metrics
        
        Args:
            metrics: Dictionary with weekly metrics
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Dictionary with report data
        """
        logger.info(f"📊 Generating weekly report: {start_date.date()} to {end_date.date()}")
        
        # Calculate averages and totals
        total_matches = metrics.get('matches_scraped', 0)
        total_opportunities = metrics.get('roi_opportunities', 0)
        total_alerts = metrics.get('alerts_sent', 0)
        total_errors = metrics.get('errors', 0)
        
        days = (end_date - start_date).days or 1
        avg_matches_per_day = total_matches / days
        avg_opportunities_per_day = total_opportunities / days
        
        # Calculate success rates
        enrichment_success_rate = metrics.get('enrichment_success_rate', 0)
        error_rate = (total_errors / max(total_matches, 1)) * 100
        
        # Generate insights
        insights = self._generate_insights(metrics, days)
        
        report = {
            'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            'total_matches': total_matches,
            'avg_matches_per_day': round(avg_matches_per_day, 1),
            'total_opportunities': total_opportunities,
            'avg_opportunities_per_day': round(avg_opportunities_per_day, 1),
            'total_alerts': total_alerts,
            'enrichment_success_rate': round(enrichment_success_rate, 1),
            'error_rate': round(error_rate, 2),
            'uptime_hours': metrics.get('uptime_hours', 0),
            'insights': insights,
            'generated_at': datetime.now().isoformat()
        }
        
        return report
    
    def _generate_insights(self, metrics: Dict, days: int) -> List[str]:
        """Generate insights from metrics"""
        insights = []
        
        total_matches = metrics.get('matches_scraped', 0)
        total_opportunities = metrics.get('roi_opportunities', 0)
        error_rate = (metrics.get('errors', 0) / max(total_matches, 1)) * 100
        
        # Match volume insight
        if total_matches > 500:
            insights.append(f"High match volume: {total_matches} matches scraped ({total_matches/days:.0f}/day)")
        elif total_matches < 100:
            insights.append(f"Low match volume: {total_matches} matches scraped - consider expanding tournament coverage")
        
        # Opportunity rate insight
        if total_opportunities > 0:
            opp_rate = (total_opportunities / max(total_matches, 1)) * 100
            if opp_rate > 10:
                insights.append(f"Excellent opportunity rate: {opp_rate:.1f}% of matches flagged as high-value")
            elif opp_rate < 2:
                insights.append(f"Low opportunity rate: {opp_rate:.1f}% - may need to adjust detection thresholds")
        
        # Error rate insight
        if error_rate > 10:
            insights.append(f"⚠️ High error rate: {error_rate:.1f}% - review scraper stability")
        elif error_rate < 1:
            insights.append(f"✅ Excellent stability: {error_rate:.1f}% error rate")
        
        # Enrichment insight
        enrichment_rate = metrics.get('enrichment_success_rate', 0)
        if enrichment_rate < 70:
            insights.append(f"⚠️ Low enrichment success: {enrichment_rate:.1f}% - check API availability")
        
        return insights
    
    def store_weekly_report(self, report: Dict, parent_page_id: Optional[str] = None) -> Optional[str]:
        """
        Store weekly report in Notion
        
        Args:
            report: Report dictionary
            parent_page_id: Optional parent page ID
            
        Returns:
            Page ID if successful
        """
        if not self.status_manager or not self.status_manager.client:
            logger.warning("⚠️ Cannot store report: Notion client not available")
            return None
        
        try:
            # Create report page
            page_properties = {
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": f"📊 Weekly Report: {report['period']}"
                            }
                        }
                    ]
                }
            }
            
            parent = {}
            if parent_page_id:
                parent = {"page_id": parent_page_id}
            elif self.status_manager.parent_page_id:
                parent = {"page_id": self.status_manager.parent_page_id}
            else:
                parent = {"type": "workspace"}
            
            page = self.status_manager.client.pages.create(
                parent=parent,
                properties=page_properties
            )
            
            page_id = page['id']
            
            # Add report content
            blocks = [
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": f"Weekly Report: {report['period']}"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "📈 Key Metrics"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": f"Total Matches: {report['total_matches']}"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": f"Avg Matches/Day: {report['avg_matches_per_day']}"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": f"ROI Opportunities: {report['total_opportunities']}"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": f"Avg Opportunities/Day: {report['avg_opportunities_per_day']}"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": f"Alerts Sent: {report['total_alerts']}"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": f"Enrichment Success: {report['enrichment_success_rate']}%"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": f"Error Rate: {report['error_rate']}%"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": f"Uptime: {report['uptime_hours']:.1f} hours"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "💡 Insights"}}]
                    }
                }
            ]
            
            # Add insights
            for insight in report.get('insights', []):
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": insight}}]
                    }
                })
            
            self.status_manager.client.blocks.children.append(
                block_id=page_id,
                children=blocks
            )
            
            logger.info(f"✅ Stored weekly report: {page_id}")
            return page_id
            
        except Exception as e:
            logger.error(f"❌ Error storing weekly report: {e}")
            return None


def main():
    """Generate test weekly report"""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("📊 Generating Weekly Report...")
    print("=" * 60)
    
    generator = WeeklyReportGenerator()
    
    # Test data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    test_metrics = {
        'matches_scraped': 350,
        'matches_stored': 340,
        'h2h_scraped': 200,
        'form_scraped': 300,
        'odds_scraped': 280,
        'enrichment_success_rate': 85.5,
        'roi_opportunities': 25,
        'alerts_sent': 18,
        'errors': 5,
        'uptime_hours': 168
    }
    
    report = generator.generate_weekly_report(test_metrics, start_date, end_date)
    
    print("\n📊 Report Summary:")
    print(f"   Period: {report['period']}")
    print(f"   Matches: {report['total_matches']} ({report['avg_matches_per_day']}/day)")
    print(f"   Opportunities: {report['total_opportunities']} ({report['avg_opportunities_per_day']}/day)")
    print(f"   Error Rate: {report['error_rate']}%")
    print(f"\n💡 Insights:")
    for insight in report['insights']:
        print(f"   • {insight}")
    
    # Store in Notion (optional)
    # page_id = generator.store_weekly_report(report)
    # if page_id:
    #     print(f"\n✅ Report stored in Notion: {page_id}")


if __name__ == "__main__":
    main()

