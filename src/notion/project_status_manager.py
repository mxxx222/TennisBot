#!/usr/bin/env python3
"""
📊 PROJECT STATUS MANAGER
=========================

Creates and updates a Project Status page in Notion for tracking
TennisExplorer scraper implementation progress and metrics.
"""

import os
import logging
from typing import Dict, Optional, Any, List
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(Path(__file__).parent.parent.parent, 'telegram_secrets.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

# Notion API
try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False

logger = logging.getLogger(__name__)


class ProjectStatusManager:
    """Manages Project Status page in Notion"""
    
    def __init__(self, parent_page_id: Optional[str] = None):
        """
        Initialize Project Status Manager
        
        Args:
            parent_page_id: Notion page ID where to create status page (optional)
        """
        if not NOTION_AVAILABLE:
            logger.warning("⚠️ notion-client not available")
            self.client = None
            return
        
        api_key = os.getenv('NOTION_API_KEY')
        if not api_key:
            logger.warning("⚠️ NOTION_API_KEY not found in environment")
            self.client = None
            return
        
        self.client = Client(auth=api_key)
        self.parent_page_id = parent_page_id or os.getenv('NOTION_PROJECT_STATUS_PARENT_ID')
        
        # Try multiple env var names for status page ID
        self.status_page_id = (
            os.getenv('NOTION_PROJECT_STATUS_PAGE_ID') or
            os.getenv('NOTION_STATUS_PAGE_ID') or
            os.getenv('TENNISEXPLORER_STATUS_PAGE_ID')
        )
        
        # Database IDs for cross-referencing
        self.tennisexplorer_db_id = (
            os.getenv('NOTION_TENNISEXPLORER_DB_ID') or
            os.getenv('NOTION_LIVE_FEED_DB_ID')
        )
        
        logger.info("📊 Project Status Manager initialized")
        if self.status_page_id:
            logger.info(f"✅ Using existing status page: {self.status_page_id[:20]}...")
    
    def create_status_page(self) -> Optional[str]:
        """
        Create Project Status page in Notion
        
        Returns:
            Page ID if successful, None otherwise
        """
        if not self.client:
            logger.warning("⚠️ Notion client not available")
            return None
        
        try:
            # Create page with initial content
            page_properties = {
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": "🎾 TennisExplorer Scraper - Project Status"
                            }
                        }
                    ]
                }
            }
            
            parent = {}
            if self.parent_page_id:
                parent = {"page_id": self.parent_page_id}
            else:
                # Create as standalone page (requires workspace)
                parent = {"type": "workspace"}
            
            page = self.client.pages.create(
                parent=parent,
                properties=page_properties
            )
            
            self.status_page_id = page['id']
            
            # Add initial content blocks
            self._add_initial_content(self.status_page_id)
            
            logger.info(f"✅ Created Project Status page: {self.status_page_id}")
            return self.status_page_id
            
        except Exception as e:
            logger.error(f"❌ Error creating status page: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _add_initial_content(self, page_id: str):
        """Add initial content blocks to status page"""
        if not self.client:
            return
        
        try:
            blocks = [
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": "📊 Implementation Status"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": "TennisExplorer Scraper implementation tracking and metrics."}}]
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
                        "rich_text": [{"type": "text", "text": {"content": "✅ Implementation Checklist"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": "Core Scraper Module"}}],
                        "checked": True
                    }
                },
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": "Database Schema"}}],
                        "checked": True
                    }
                },
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": "Pipeline Orchestrator"}}],
                        "checked": True
                    }
                },
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": "Enrichment Modules (5)"}}],
                        "checked": True
                    }
                },
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": "ROI Detection (4 modules)"}}],
                        "checked": True
                    }
                },
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": "Notion Integration"}}],
                        "checked": True
                    }
                },
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": "Alerting System"}}],
                        "checked": True
                    }
                },
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": "Scheduler & Monitoring"}}],
                        "checked": True
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
                        "rich_text": [{"type": "text", "text": {"content": "📈 Daily Metrics"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": "Updated automatically by scraper."}}]
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
                        "rich_text": [{"type": "text", "text": {"content": "🚨 ROI Opportunities"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": "High-value betting opportunities detected."}}]
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
                        "rich_text": [{"type": "text", "text": {"content": "🔗 Related Resources"}}]
                    }
                }
            ]
            
            # Add links to related databases if available
            if self.tennisexplorer_db_id:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "🎾 TennisExplorer Live Feed Database: ",
                                }
                            },
                            {
                                "type": "mention",
                                "mention": {
                                    "database": {"id": self.tennisexplorer_db_id}
                                }
                            }
                        ]
                    }
                })
            
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "📚 Implementation Documentation: ",
                            }
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": "TennisExplorer Scraper — Implementation",
                                "link": {
                                    "url": "https://www.notion.so/TennisExplorer-Scraper-Implementation-b43b6e61619b423c8d9d34f2164b7605"
                                }
                            }
                        }
                    ]
                }
            })
            
            blocks.append({
                "object": "block",
                "type": "divider",
                "divider": {}
            })
            
            self.client.blocks.children.append(
                block_id=page_id,
                children=blocks
            )
            
            logger.info("✅ Added initial content to status page")
            
        except Exception as e:
            logger.error(f"❌ Error adding initial content: {e}")
    
    def update_metrics(self, metrics: Dict[str, Any]):
        """
        Update metrics section on status page
        
        Args:
            metrics: Dictionary with metrics data
        """
        if not self.client:
            logger.warning("⚠️ Cannot update metrics: Notion client not available")
            return False
        
        # If no status_page_id, try to get it from env or skip
        if not self.status_page_id:
            self.status_page_id = (
                os.getenv('NOTION_PROJECT_STATUS_PAGE_ID') or
                os.getenv('NOTION_STATUS_PAGE_ID') or
                os.getenv('TENNISEXPLORER_STATUS_PAGE_ID')
            )
        
        if not self.status_page_id:
            logger.debug("⚠️ Cannot update metrics: status page ID not set")
            return False
        
        try:
            # Get current page blocks
            blocks = self.client.blocks.children.list(block_id=self.status_page_id)
            
            # Find metrics section and update
            # This is a simplified version - in production, would need to find and replace specific blocks
            
            # For now, append new metrics block
            metrics_text = f"""
📊 **Daily Metrics** ({datetime.now().strftime('%Y-%m-%d %H:%M')})

- Matches Scraped: {metrics.get('matches_scraped', 0)}
- Matches Stored: {metrics.get('matches_stored', 0)}
- H2H Scraped: {metrics.get('h2h_scraped', 0)}
- Form Scraped: {metrics.get('form_scraped', 0)}
- Odds Scraped: {metrics.get('odds_scraped', 0)}
- Enrichment Success Rate: {metrics.get('enrichment_success_rate', 0):.1f}%
- ROI Opportunities: {metrics.get('roi_opportunities', 0)}
- Alerts Sent: {metrics.get('alerts_sent', 0)}
- Errors: {metrics.get('errors', 0)}
- Uptime: {metrics.get('uptime_hours', 0):.1f} hours
            """.strip()
            
            # Append metrics block
            self.client.blocks.children.append(
                block_id=self.status_page_id,
                children=[{
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": metrics_text}
                            }
                        ]
                    }
                }]
            )
            
            logger.info("✅ Updated metrics on status page")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating metrics: {e}")
            return False
    
    def add_roi_opportunity(self, opportunity: Dict[str, Any]):
        """
        Add ROI opportunity to status page
        
        Args:
            opportunity: ROI opportunity dictionary
        """
        if not self.client or not self.status_page_id:
            return False
        
        try:
            opp_text = (
                f"🎯 **{opportunity.get('strategy', 'Opportunity')}** - "
                f"{opportunity.get('player_a', 'Player A')} vs {opportunity.get('player_b', 'Player B')}\n"
                f"EV: {opportunity.get('expected_value_pct', 0):.1f}% | "
                f"Kelly: {opportunity.get('kelly_stake_pct', 0):.2f}% | "
                f"Tournament: {opportunity.get('tournament', 'Unknown')}"
            )
            
            self.client.blocks.children.append(
                block_id=self.status_page_id,
                children=[{
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": opp_text}
                            }
                        ]
                    }
                }]
            )
            
            logger.info("✅ Added ROI opportunity to status page")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error adding ROI opportunity: {e}")
            return False
    
    def get_or_create_status_page(self) -> Optional[str]:
        """
        Get existing status page or create new one
        
        Returns:
            Page ID
        """
        if hasattr(self, 'status_page_id') and self.status_page_id:
            # Verify page exists
            if self.client:
                try:
                    self.client.pages.retrieve(page_id=self.status_page_id)
                    logger.info(f"✅ Using existing status page: {self.status_page_id[:20]}...")
                    return self.status_page_id
                except Exception as e:
                    logger.warning(f"⚠️  Status page {self.status_page_id[:20]}... not accessible: {str(e)[:50]}")
                    # Continue to create new one
        
        # Try to create new one (if no existing page ID)
        return self.create_status_page()


def main():
    """Create Project Status page"""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("📊 Creating Project Status page in Notion...")
    print("=" * 60)
    
    manager = ProjectStatusManager()
    
    page_id = manager.get_or_create_status_page()
    
    if page_id:
        print(f"✅ Status page created/updated: {page_id}")
        print(f"\n🔗 View page: https://notion.so/{page_id.replace('-', '')}")
        print("\n💡 Next steps:")
        print("   1. Share the page with your team (if needed)")
        print("   2. The scraper will automatically update metrics")
        print("   3. ROI opportunities will be added as detected")
    else:
        print("❌ Failed to create status page")
        print("\n💡 Troubleshooting:")
        print("   1. Check NOTION_API_KEY in telegram_secrets.env")
        print("   2. Ensure API key has page creation permissions")
        print("   3. If using parent page, set NOTION_PROJECT_STATUS_PARENT_ID")


if __name__ == "__main__":
    main()

