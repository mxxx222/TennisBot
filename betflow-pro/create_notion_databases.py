"""
Create Notion databases for BetFlow Pro system
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from notion_client import Client
sys.path.insert(0, str(Path(__file__).parent))
from config import NOTION_TOKEN
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_master_control_panel(client: Client, parent_page_id: str) -> str:
    """
    Create Master Control Panel database
    
    Properties:
    - Real-time ROI metrics
    - Bankroll tracking
    - Win rate, Sharpe ratio
    - Alerts and notifications
    """
    try:
        database = client.databases.create(
            parent={"page_id": parent_page_id},
            title=[{"type": "text", "text": {"content": "Master Control Panel"}}],
            properties={
                "Metric": {
                    "title": {}
                },
                "Value": {
                    "number": {}
                },
                "Unit": {
                    "select": {
                        "options": [
                            {"name": "%", "color": "blue"},
                            {"name": "€", "color": "green"},
                            {"name": "ratio", "color": "purple"},
                            {"name": "count", "color": "orange"}
                        ]
                    }
                },
                "Status": {
                    "select": {
                        "options": [
                            {"name": "✅ EXCELLENT", "color": "green"},
                            {"name": "⚠️ WARNING", "color": "yellow"},
                            {"name": "🔴 CRITICAL", "color": "red"}
                        ]
                    }
                },
                "Last Updated": {
                    "date": {}
                }
            }
        )
        logger.info(f"✅ Created Master Control Panel: {database['id']}")
        return database['id']
    except Exception as e:
        logger.error(f"❌ Error creating Master Control Panel: {e}")
        return None


def create_advanced_analytiikka(client: Client, parent_page_id: str) -> str:
    """
    Create Advanced Analytiikka database
    
    Properties with formulas:
    - Edge detection (Base, Arbitrage, Movement, ML, Total)
    - Booking optimization
    - Risk management (Kelly, stakes)
    - Proprietary metrics
    """
    try:
        database = client.databases.create(
            parent={"page_id": parent_page_id},
            title=[{"type": "text", "text": {"content": "Advanced Analytiikka"}}],
            properties={
                "Match": {
                    "title": {}
                },
                "Match ID": {
                    "rich_text": {}
                },
                "Base Edge %": {
                    "number": {
                        "format": "number_with_commas"
                    }
                },
                "Arbitrage Edge %": {
                    "number": {
                        "format": "number_with_commas"
                    }
                },
                "Movement Edge %": {
                    "number": {
                        "format": "number_with_commas"
                    }
                },
                "ML Edge %": {
                    "number": {
                        "format": "number_with_commas"
                    }
                },
                "Total Edge %": {
                    "formula": {
                        "expression": "prop(\"Base Edge %\") * 0.6 + prop(\"Arbitrage Edge %\") * 0.2 + prop(\"Movement Edge %\") * 0.1 + prop(\"ML Edge %\") * 0.1"
                    }
                },
                "Confidence (1-10)": {
                    "number": {}
                },
                "Best Book": {
                    "select": {
                        "options": [
                            {"name": "Pinnacle", "color": "blue"},
                            {"name": "Bet365", "color": "green"},
                            {"name": "1xBet", "color": "purple"},
                            {"name": "William Hill", "color": "orange"}
                        ]
                    }
                },
                "Best Odds": {
                    "number": {
                        "format": "number_with_commas"
                    }
                },
                "Kelly %": {
                    "formula": {
                        "expression": "if(prop(\"Total Edge %\") > 8, (prop(\"Total Edge %\") * (prop(\"Best Odds\") - 1)) / (prop(\"Best Odds\") - 1) * 0.75, if(prop(\"Total Edge %\") > 4, (prop(\"Total Edge %\") * (prop(\"Best Odds\") - 1)) / (prop(\"Best Odds\") - 1) * 0.5, 0))"
                    }
                },
                "Stake (€)": {
                    "formula": {
                        "expression": "if(prop(\"Total Edge %\") > 4, 5000 * prop(\"Kelly %\") / 100, 0)"
                    }
                },
                "Potential Win (€)": {
                    "formula": {
                        "expression": "prop(\"Stake (€)\") * (prop(\"Best Odds\") - 1)"
                    }
                },
                "Recommendation": {
                    "select": {
                        "options": [
                            {"name": "PLAY", "color": "green"},
                            {"name": "WAIT", "color": "yellow"},
                            {"name": "SKIP", "color": "red"}
                        ]
                    }
                },
                "Date": {
                    "date": {}
                }
            }
        )
        logger.info(f"✅ Created Advanced Analytiikka: {database['id']}")
        return database['id']
    except Exception as e:
        logger.error(f"❌ Error creating Advanced Analytiikka: {e}")
        return None


def create_real_time_arbitrage(client: Client, parent_page_id: str) -> str:
    """
    Create Real-Time Arbitrage database
    
    Properties:
    - Match information
    - Book A and Book B odds
    - Arbitrage percentage (formula)
    - Execution details
    """
    try:
        database = client.databases.create(
            parent={"page_id": parent_page_id},
            title=[{"type": "text", "text": {"content": "Real-Time Arbitrage"}}],
            properties={
                "Match": {
                    "title": {}
                },
                "Match ID": {
                    "rich_text": {}
                },
                "Bet Type": {
                    "select": {
                        "options": [
                            {"name": "1X2", "color": "blue"},
                            {"name": "OU2.5", "color": "green"},
                            {"name": "BTTS", "color": "purple"}
                        ]
                    }
                },
                "Book A": {
                    "select": {
                        "options": [
                            {"name": "Pinnacle", "color": "blue"},
                            {"name": "Bet365", "color": "green"},
                            {"name": "1xBet", "color": "purple"}
                        ]
                    }
                },
                "Odds A": {
                    "number": {
                        "format": "number_with_commas"
                    }
                },
                "Book B": {
                    "select": {
                        "options": [
                            {"name": "Pinnacle", "color": "blue"},
                            {"name": "Bet365", "color": "green"},
                            {"name": "1xBet", "color": "purple"}
                        ]
                    }
                },
                "Odds B": {
                    "number": {
                        "format": "number_with_commas"
                    }
                },
                "Arbitrage %": {
                    "formula": {
                        "expression": "(1 / prop(\"Odds A\") + 1 / prop(\"Odds B\") - 1) * 100"
                    }
                },
                "Min Stake (€)": {
                    "number": {}
                },
                "Expected Profit (€)": {
                    "formula": {
                        "expression": "prop(\"Min Stake (€)\") * prop(\"Arbitrage %\") / 100"
                    }
                },
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Identified", "color": "yellow"},
                            {"name": "Placed", "color": "blue"},
                            {"name": "Completed", "color": "green"},
                            {"name": "Expired", "color": "red"}
                        ]
                    }
                },
                "Identified At": {
                    "date": {}
                }
            }
        )
        logger.info(f"✅ Created Real-Time Arbitrage: {database['id']}")
        return database['id']
    except Exception as e:
        logger.error(f"❌ Error creating Real-Time Arbitrage: {e}")
        return None


def create_all_databases(parent_page_id: str, notion_token: str = None) -> dict:
    """
    Create all three databases
    
    Args:
        parent_page_id: Notion page ID where databases will be created
        notion_token: Notion API token (optional, uses config if not provided)
    
    Returns:
        Dict with database IDs
    """
    token = notion_token or NOTION_TOKEN
    
    if not token:
        logger.error("❌ Notion token required!")
        return {}
    
    client = Client(auth=token)
    
    databases = {}
    
    logger.info("📊 Creating BetFlow Pro databases...")
    
    # Create Master Control Panel
    control_panel_id = create_master_control_panel(client, parent_page_id)
    if control_panel_id:
        databases['control_panel'] = control_panel_id
    
    # Create Advanced Analytiikka
    analytiikka_id = create_advanced_analytiikka(client, parent_page_id)
    if analytiikka_id:
        databases['analytiikka'] = analytiikka_id
    
    # Create Real-Time Arbitrage
    arbitrage_id = create_real_time_arbitrage(client, parent_page_id)
    if arbitrage_id:
        databases['arbitrage'] = arbitrage_id
    
    # Save to config file
    config_file = Path(__file__).parent / 'notion_databases.json'
    config_data = {
        'databases': databases,
        'created_at': datetime.now().isoformat(),
        'parent_page_id': parent_page_id
    }
    
    with open(config_file, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    logger.info(f"💾 Config saved to {config_file}")
    
    return databases


def main():
    parser = argparse.ArgumentParser(
        description='Create Notion databases for BetFlow Pro',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--page-id', '-p', required=True,
                       help='Notion parent page ID')
    parser.add_argument('--token', '-t',
                       help='Notion API token (optional if set in .env)')
    
    args = parser.parse_args()
    
    databases = create_all_databases(args.page_id, args.token)
    
    if databases:
        print("\n✅ Successfully created databases:")
        for name, db_id in databases.items():
            print(f"   • {name}: {db_id}")
    else:
        print("\n❌ Failed to create databases")
        sys.exit(1)


if __name__ == "__main__":
    main()

