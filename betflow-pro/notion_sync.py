"""
Sync analysis and betting data to Notion
"""
from notion_client import Client
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from config import NOTION_TOKEN, NOTION_DB_ANALYSIS, NOTION_DB_BETS, NOTION_DB_ARBITRAGE
from typing import Dict, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class NotionSync:
    """Sync analysis + betting data to Notion"""

    def __init__(self, notion_token: Optional[str] = None):
        """
        Initialize Notion sync
        
        Args:
            notion_token: Notion API token (optional, uses config if not provided)
        """
        token = notion_token or NOTION_TOKEN
        if not token:
            raise ValueError("Notion token required. Set NOTION_TOKEN in .env or pass as argument.")
        
        self.client = Client(auth=token)
        self.db_analysis = NOTION_DB_ANALYSIS
        self.db_bets = NOTION_DB_BETS
        self.db_arbitrage = NOTION_DB_ARBITRAGE

    def update_analysis(self, match_id: str, analysis_data: Dict) -> bool:
        """
        Update Analytiikka database with edge detection

        Args:
            match_id: Match identifier
            analysis_data: Dict with analysis results:
                {
                    'base_edge': 8.5,
                    'arb_edge': 2.1,
                    'movement_edge': 1.5,
                    'ml_edge': 0.8,
                    'total_edge': 12.1,
                    'confidence': 8,
                    'best_book': 'Pinnacle',
                    'best_odds': 1.95,
                    'match_name': 'Team A vs Team B',
                    'recommendation': 'PLAY'
                }

        Returns:
            True if successful
        """
        if not self.db_analysis:
            logger.warning("Analysis database ID not configured")
            return False

        try:
            # Check if page already exists
            existing_pages = self.client.databases.query(
                database_id=self.db_analysis,
                filter={
                    "property": "Match ID",
                    "rich_text": {
                        "equals": match_id
                    }
                }
            )

            properties = {
                "Match": {
                    "title": [
                        {
                            "text": {
                                "content": analysis_data.get('match_name', match_id)
                            }
                        }
                    ]
                },
                "Match ID": {
                    "rich_text": [
                        {
                            "text": {
                                "content": match_id
                            }
                        }
                    ]
                },
                "Base Edge %": {
                    "number": analysis_data.get('base_edge', 0)
                },
                "Arbitrage Edge %": {
                    "number": analysis_data.get('arb_edge', 0)
                },
                "Movement Edge %": {
                    "number": analysis_data.get('movement_edge', 0)
                },
                "ML Edge %": {
                    "number": analysis_data.get('ml_edge', 0)
                },
                "Confidence (1-10)": {
                    "number": analysis_data.get('confidence', 0)
                },
                "Best Book": {
                    "select": {
                        "name": analysis_data.get('best_book', 'Pinnacle')
                    }
                },
                "Best Odds": {
                    "number": analysis_data.get('best_odds', 0)
                },
                "Recommendation": {
                    "select": {
                        "name": analysis_data.get('recommendation', 'WAIT')
                    }
                },
                "Date": {
                    "date": {
                        "start": datetime.now().isoformat()
                    }
                }
            }

            if existing_pages.get('results'):
                # Update existing page
                page_id = existing_pages['results'][0]['id']
                self.client.pages.update(
                    page_id=page_id,
                    properties=properties
                )
                logger.info(f"Updated analysis for match {match_id}")
            else:
                # Create new page
                self.client.pages.create(
                    parent={"database_id": self.db_analysis},
                    properties=properties
                )
                logger.info(f"Created analysis for match {match_id}")

            return True

        except Exception as e:
            logger.error(f"Error updating analysis: {e}")
            return False

    def log_bet(self, bet_data: Dict) -> Optional[str]:
        """
        Log bet to Vedot database

        Args:
            bet_data: Dict with bet information:
                {
                    'match_id': 'match123',
                    'match_name': 'Team A vs Team B',
                    'bet_type': '1X2',
                    'selection': 'home',
                    'odds': 1.95,
                    'stake': 245.0,
                    'potential_win': 477.75,
                    'book': 'Pinnacle',
                    'status': 'Pending'
                }

        Returns:
            Page ID if successful, None otherwise
        """
        if not self.db_bets:
            logger.warning("Bets database ID not configured")
            return None

        try:
            properties = {
                "Match": {
                    "title": [
                        {
                            "text": {
                                "content": bet_data.get('match_name', bet_data.get('match_id', ''))
                            }
                        }
                    ]
                },
                "Match ID": {
                    "rich_text": [
                        {
                            "text": {
                                "content": bet_data.get('match_id', '')
                            }
                        }
                    ]
                },
                "Bet Type": {
                    "select": {
                        "name": bet_data.get('bet_type', '1X2')
                    }
                },
                "Selection": {
                    "rich_text": [
                        {
                            "text": {
                                "content": bet_data.get('selection', '')
                            }
                        }
                    ]
                },
                "Odds": {
                    "number": bet_data.get('odds', 0)
                },
                "Stake (€)": {
                    "number": bet_data.get('stake', 0)
                },
                "Potential Win (€)": {
                    "number": bet_data.get('potential_win', 0)
                },
                "Book": {
                    "select": {
                        "name": bet_data.get('book', 'Pinnacle')
                    }
                },
                "Status": {
                    "select": {
                        "name": bet_data.get('status', 'Pending')
                    }
                },
                "Date": {
                    "date": {
                        "start": datetime.now().isoformat()
                    }
                }
            }

            response = self.client.pages.create(
                parent={"database_id": self.db_bets},
                properties=properties
            )

            logger.info(f"Logged bet: {bet_data.get('match_id')}")
            return response['id']

        except Exception as e:
            logger.error(f"Error logging bet: {e}")
            return None

    def log_arbitrage(self, arb_data: Dict) -> Optional[str]:
        """
        Log arbitrage opportunity

        Args:
            arb_data: Dict with arbitrage information:
                {
                    'match_id': 'match123',
                    'match_name': 'Team A vs Team B',
                    'bet_type': '1X2',
                    'book_a': 'Pinnacle',
                    'odds_a': 1.95,
                    'book_b': 'Bet365',
                    'odds_b': 2.05,
                    'arbitrage_percent': 2.1,
                    'min_stake': 1000,
                    'expected_profit': 21
                }

        Returns:
            Page ID if successful, None otherwise
        """
        if not self.db_arbitrage:
            logger.warning("Arbitrage database ID not configured")
            return None

        try:
            properties = {
                "Match": {
                    "title": [
                        {
                            "text": {
                                "content": arb_data.get('match_name', arb_data.get('match_id', ''))
                            }
                        }
                    ]
                },
                "Match ID": {
                    "rich_text": [
                        {
                            "text": {
                                "content": arb_data.get('match_id', '')
                            }
                        }
                    ]
                },
                "Bet Type": {
                    "select": {
                        "name": arb_data.get('bet_type', '1X2')
                    }
                },
                "Book A": {
                    "select": {
                        "name": arb_data.get('book_a', 'Pinnacle')
                    }
                },
                "Odds A": {
                    "number": arb_data.get('odds_a', 0)
                },
                "Book B": {
                    "select": {
                        "name": arb_data.get('book_b', 'Bet365')
                    }
                },
                "Odds B": {
                    "number": arb_data.get('odds_b', 0)
                },
                "Min Stake (€)": {
                    "number": arb_data.get('min_stake', 0)
                },
                "Status": {
                    "select": {
                        "name": "Identified"
                    }
                },
                "Identified At": {
                    "date": {
                        "start": datetime.now().isoformat()
                    }
                }
            }

            response = self.client.pages.create(
                parent={"database_id": self.db_arbitrage},
                properties=properties
            )

            logger.info(f"Logged arbitrage: {arb_data.get('match_id')}")
            return response['id']

        except Exception as e:
            logger.error(f"Error logging arbitrage: {e}")
            return None

    def fetch_pending_bets(self) -> List[Dict]:
        """Get all pending bets from Notion"""
        if not self.db_bets:
            return []

        try:
            response = self.client.databases.query(
                database_id=self.db_bets,
                filter={
                    "property": "Status",
                    "select": {
                        "equals": "Pending"
                    }
                }
            )

            return response.get('results', [])

        except Exception as e:
            logger.error(f"Error fetching pending bets: {e}")
            return []

