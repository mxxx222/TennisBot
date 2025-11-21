#!/usr/bin/env python3
"""
🤖 AI MATCH FILTER
==================

Filters Raw Match Feed → Tennis Prematch DB based on quality, ROI score, and player momentum.

Schedule: Daily 09:00 EET (07:00 UTC) - after all scrapers complete
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / 'telegram_secrets.env'
if env_path.exists():
    load_dotenv(env_path)

# Notion API
try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    print("❌ ERROR: notion-client not installed")
    exit(1)

logger = logging.getLogger(__name__)

# Configuration
NOTION_TOKEN = os.getenv("NOTION_TOKEN") or os.getenv("NOTION_API_KEY")
RAW_MATCH_FEED_DB_ID = os.getenv("RAW_MATCH_FEED_DB_ID")
TENNIS_PREMATCH_DB_ID = os.getenv("TENNIS_PREMATCH_DB_ID") or os.getenv("NOTION_TENNIS_PREMATCH_DB_ID") or os.getenv("NOTION_PREMATCH_DB_ID")
PLAYER_CARDS_DB_ID = os.getenv("PLAYER_CARDS_DB_ID") or os.getenv("NOTION_ITF_PLAYER_CARDS_DB_ID")

# Target tournament tiers
TARGET_TIERS = ["ITF W15", "ITF W25", "ITF W35", "ITF W50"]
SECONDARY_TIERS = ["Challenger", "WTA 250", "WTA 500"]


class MatchFilter:
    """
    AI-powered match filtering and enrichment.
    """
    
    def __init__(self):
        if not NOTION_TOKEN:
            logger.error("❌ NOTION_TOKEN not set")
            raise ValueError("NOTION_TOKEN environment variable required")
        
        try:
            if not NOTION_TOKEN:
                raise ValueError("NOTION_TOKEN not set")
            self.notion = Client(auth=NOTION_TOKEN)
        except Exception as e:
            logger.error(f"❌ Failed to initialize Notion client: {e}")
            raise
        
        self.raw_feed_db = RAW_MATCH_FEED_DB_ID
        self.prematch_db = TENNIS_PREMATCH_DB_ID
        self.player_cards_db = PLAYER_CARDS_DB_ID
        self.player_cache = {}  # Cache player lookups
        
        if not self.raw_feed_db:
            logger.error("❌ RAW_MATCH_FEED_DB_ID not set")
        if not self.prematch_db:
            logger.error("❌ TENNIS_PREMATCH_DB_ID not set")
        if not self.player_cards_db:
            logger.warning("⚠️ PLAYER_CARDS_DB_ID not set - player enrichment disabled")
        
        logger.info("🤖 AI Match Filter initialized")
    
    def get_unprocessed_matches(self) -> List[Dict]:
        """
        Fetch all unprocessed matches from Raw Match Feed.
        
        Returns:
            List of match page dictionaries
        """
        if not self.raw_feed_db:
            return []
        
        matches = []
        has_more = True
        start_cursor = None
        
        while has_more:
            try:
                if not self.raw_feed_db:
                    break
                
                response = self.notion.databases.query(
                    database_id=self.raw_feed_db,
                    filter={
                        "and": [
                            {"property": "AI Processed", "checkbox": {"equals": False}},
                            {"property": "Match Status", "select": {"equals": "Upcoming"}}
                        ]
                    },
                    start_cursor=start_cursor
                )
                
                matches.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")
                
            except Exception as e:
                logger.error(f"❌ Error fetching unprocessed matches: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                break
        
        logger.info(f"📥 Found {len(matches)} unprocessed matches")
        return matches
    
    def get_player_data(self, player_name: str) -> Optional[Dict]:
        """
        Lookup player in Player Cards DB with caching.
        
        Args:
            player_name: Player name to lookup
            
        Returns:
            Dictionary with player data (elo, momentum, hot_hand, etc.) or None
        """
        if not self.player_cards_db:
            return None
        
        # Check cache first
        if player_name in self.player_cache:
            return self.player_cache[player_name]
        
        try:
            if not self.player_cards_db:
                return None
            
            response = self.notion.databases.query(
                database_id=self.player_cards_db,
                filter={
                    "or": [
                        {"property": "Player Name", "title": {"equals": player_name}},
                        {"property": "Name", "title": {"equals": player_name}}
                    ]
                }
            )
            
            if response.get("results"):
                props = response["results"][0]["properties"]
                player_data = {
                    "elo": props.get("Overall ELO", {}).get("number") or props.get("ELO", {}).get("number") or 1500,
                    "momentum": props.get("Momentum Score", {}).get("number") or props.get("Momentum", {}).get("number") or 50,
                    "hot_hand": props.get("Hot Hand", {}).get("checkbox", False),
                    "rising_talent": props.get("Rising Talent", {}).get("checkbox", False),
                    "l10_win_rate": props.get("L10 Win %", {}).get("number") or props.get("Last 10 Win %", {}).get("number") or 0.5
                }
                self.player_cache[player_name] = player_data
                return player_data
            
            return None
            
        except Exception as e:
            logger.debug(f"⚠️ Error looking up player {player_name}: {e}")
            return None
    
    def check_data_quality(self, match: Dict) -> Tuple[str, List[str]]:
        """
        Check data quality and return (quality_level, missing_fields).
        
        Args:
            match: Match page dictionary from Notion
            
        Returns:
            Tuple of (quality_level, list of missing fields)
        """
        props = match.get("properties", {})
        missing = []
        
        # Critical fields
        if not props.get("Player A Name", {}).get("rich_text"):
            missing.append("Player A Name")
        if not props.get("Player B Name", {}).get("rich_text"):
            missing.append("Player B Name")
        if not props.get("Tournament Tier", {}).get("select"):
            missing.append("Tournament Tier")
        if not props.get("Player A Odds", {}).get("number"):
            missing.append("Player A Odds")
        if not props.get("Player B Odds", {}).get("number"):
            missing.append("Player B Odds")
        
        if missing:
            return ("Missing Data", missing)
        
        # Non-critical fields
        if not props.get("Surface", {}).get("select"):
            missing.append("Surface")
        if not props.get("Round", {}).get("select"):
            missing.append("Round")
        
        if missing:
            return ("Partial", missing)
        
        return ("Complete", [])
    
    def calculate_roi_score(self, match: Dict, player_a_data: Optional[Dict], 
                           player_b_data: Optional[Dict], quality: str) -> Tuple[int, str]:
        """
        Calculate ROI score (0-100) and explanation.
        
        Args:
            match: Match page dictionary
            player_a_data: Player A data from Player Cards DB
            player_b_data: Player B data from Player Cards DB
            quality: Data quality level ("Complete", "Partial", "Missing Data")
            
        Returns:
            Tuple of (roi_score, explanation_string)
        """
        props = match.get("properties", {})
        score = 0
        reasons = []
        
        # 1. Tournament Weight (0-30)
        tier = props.get("Tournament Tier", {}).get("select", {}).get("name", "")
        if tier in ["ITF W15", "ITF W25"]:
            score += 30
            reasons.append("Target tier (30)")
        elif tier in ["ITF W35", "ITF W50"]:
            score += 25
            reasons.append("Secondary tier (25)")
        elif tier in SECONDARY_TIERS:
            score += 15
            reasons.append("Monitoring tier (15)")
        else:
            score += 5
            reasons.append("Low priority tier (5)")
        
        # 2. Momentum Weight (0-25)
        if player_a_data and player_b_data:
            if player_a_data.get("hot_hand") and player_b_data.get("hot_hand"):
                score += 25
                reasons.append("Both hot (25)")
            elif player_a_data.get("hot_hand") or player_b_data.get("hot_hand"):
                score += 20
                reasons.append("One hot (20)")
            elif player_a_data.get("rising_talent") or player_b_data.get("rising_talent"):
                score += 15
                reasons.append("Rising talent (15)")
            else:
                score += 10
                reasons.append("Both tracked (10)")
        elif player_a_data or player_b_data:
            score += 5
            reasons.append("One tracked (5)")
        else:
            score += 0
            reasons.append("Neither tracked (0)")
        
        # 3. Odds Value Weight (0-20)
        best_odds_a = props.get("Best Odds A", {}).get("number") or props.get("Player A Odds", {}).get("number", 0)
        best_odds_b = props.get("Best Odds B", {}).get("number") or props.get("Player B Odds", {}).get("number", 0)
        
        odds_value_added = False
        for odds in [best_odds_a, best_odds_b]:
            if odds and 1.40 <= odds <= 1.80:
                score += 10
                reasons.append(f"Sweet spot odds {odds:.2f} (10)")
                odds_value_added = True
                break
            elif odds and ((1.30 <= odds < 1.40) or (1.80 < odds <= 2.20)):
                score += 7
                reasons.append(f"Good odds {odds:.2f} (7)")
                odds_value_added = True
                break
            elif odds and ((1.20 <= odds < 1.30) or (2.20 < odds <= 3.00)):
                score += 5
                reasons.append(f"OK odds {odds:.2f} (5)")
                odds_value_added = True
                break
        
        if not odds_value_added:
            score += 0
            reasons.append("Odds outside range (0)")
        
        # 4. Data Quality Weight (0-15)
        if quality == "Complete":
            score += 15
            reasons.append("Complete data (15)")
        elif quality == "Partial":
            score += 10
            reasons.append("Partial data (10)")
        else:
            score += 0
            reasons.append("Missing data (0)")
        
        # 5. Player Coverage Weight (0-10)
        if player_a_data and player_b_data:
            score += 10
            reasons.append("Both in DB (10)")
        elif player_a_data or player_b_data:
            score += 5
            reasons.append("One in DB (5)")
        else:
            score += 0
            reasons.append("Neither in DB (0)")
        
        explanation = "; ".join(reasons)
        return (score, explanation)
    
    def should_approve(self, roi_score: int, quality: str, tier: str) -> bool:
        """
        Decide if match should be approved for Tennis Prematch DB.
        
        Args:
            roi_score: Calculated ROI score (0-100)
            quality: Data quality level
            tier: Tournament tier
            
        Returns:
            True if should be approved
        """
        if quality == "Missing Data":
            return False
        
        if tier not in TARGET_TIERS:
            return False
        
        return roi_score >= 70
    
    def copy_to_prematch_db(self, match: Dict, roi_score: int, 
                           player_a_data: Optional[Dict], player_b_data: Optional[Dict]) -> bool:
        """
        Copy approved match to Tennis Prematch DB with enrichment.
        
        Args:
            match: Match page dictionary from Raw Match Feed
            roi_score: Calculated ROI score
            player_a_data: Player A data from Player Cards
            player_b_data: Player B data from Player Cards
            
        Returns:
            True if successful
        """
        if not self.prematch_db:
            logger.error("❌ TENNIS_PREMATCH_DB_ID not set")
            return False
        
        props = match.get("properties", {})
        
        # Extract values
        match_id_elem = props.get("Match ID", {}).get("title", [])
        match_id = match_id_elem[0]["text"]["content"] if match_id_elem else ""
        
        player_a_elem = props.get("Player A Name", {}).get("rich_text", [])
        player_a = player_a_elem[0]["text"]["content"] if player_a_elem else ""
        
        player_b_elem = props.get("Player B Name", {}).get("rich_text", [])
        player_b = player_b_elem[0]["text"]["content"] if player_b_elem else ""
        
        tournament_elem = props.get("Tournament", {}).get("rich_text", [])
        tournament = tournament_elem[0]["text"]["content"] if tournament_elem else ""
        
        # Build properties for Tennis Prematch DB
        prematch_props = {}
        
        # Title (match name)
        prematch_props["Name"] = {
            "title": [{"text": {"content": f"{player_a} vs {player_b}"}}]
        }
        
        # Basic fields
        if player_a:
            prematch_props["Pelaaja A nimi"] = {
                "rich_text": [{"text": {"content": player_a}}]
            }
        
        if player_b:
            prematch_props["Pelaaja B nimi"] = {
                "rich_text": [{"text": {"content": player_b}}]
            }
        
        if tournament:
            prematch_props["Turnaus"] = {
                "rich_text": [{"text": {"content": tournament}}]
            }
        
        # Tournament tier
        tier = props.get("Tournament Tier", {}).get("select", {}).get("name")
        if tier:
            prematch_props["Tournament Tier"] = {
                "select": {"name": tier}
            }
        
        # Surface
        surface = props.get("Surface", {}).get("select", {}).get("name")
        if surface:
            prematch_props["Kenttä"] = {
                "select": {"name": surface}
            }
        
        # Round
        round_name = props.get("Round", {}).get("select", {}).get("name")
        if round_name:
            prematch_props["Round"] = {
                "select": {"name": round_name}
            }
        
        # Odds
        if props.get("Player A Odds", {}).get("number"):
            prematch_props["Best Odds P1"] = {
                "number": props["Player A Odds"]["number"]
            }
        
        if props.get("Player B Odds", {}).get("number"):
            prematch_props["Best Odds P2"] = {
                "number": props["Player B Odds"]["number"]
            }
        
        # Best odds (if available)
        if props.get("Best Odds A", {}).get("number"):
            prematch_props["Best Odds P1"] = {
                "number": props["Best Odds A"]["number"]
            }
        
        if props.get("Best Odds B", {}).get("number"):
            prematch_props["Best Odds P2"] = {
                "number": props["Best Odds B"]["number"]
            }
        
        # Bookmaker
        bookmaker = props.get("Bookmaker", {}).get("select", {}).get("name")
        if bookmaker:
            prematch_props["Bookmaker P1"] = {
                "select": {"name": bookmaker}
            }
        
        # Player data enrichment (ELO)
        if player_a_data and player_a_data.get("elo"):
            prematch_props["ELO A"] = {
                "number": player_a_data["elo"]
            }
        
        if player_b_data and player_b_data.get("elo"):
            prematch_props["ELO B"] = {
                "number": player_b_data["elo"]
            }
        
        # Match date
        match_date = props.get("Match Date", {}).get("date")
        if match_date:
            prematch_props["Päivämäärä"] = {
                "date": {"start": match_date.get("start")}
            }
        
        # Match status
        prematch_props["Match Status"] = {
            "select": {"name": "Upcoming"}
        }
        
        # Data source
        data_source = props.get("Data Source", {}).get("select", {}).get("name", "Unknown")
        prematch_props["Data Source"] = {
            "select": {"name": data_source}
        }
        
        # ROI Score (if field exists in Prematch DB)
        prematch_props["ROI Score"] = {
            "number": roi_score
        }
        
        try:
            # Check if already exists (simplified check)
            try:
                existing = self.notion.databases.query(
                    database_id=self.prematch_db,
                    filter={
                        "and": [
                            {
                                "property": "Pelaaja A nimi",
                                "rich_text": {"contains": player_a}
                            }
                        ]
                    },
                    page_size=1
                )
            except:
                # If query fails, skip duplicate check
                existing = {"results": []}
            
            if existing.get("results"):
                logger.debug(f"  ⚠️  Match already exists in Prematch DB: {player_a} vs {player_b}")
                return True  # Consider it success if already exists
            
            # Create page in Tennis Prematch DB
            self.notion.pages.create(
                parent={"database_id": self.prematch_db},
                properties=prematch_props
            )
            
            logger.info(f"  ✅ Copied to Prematch DB: {match_id} (ROI: {roi_score})")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Error copying to Prematch DB: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False
    
    def mark_processed(self, match_id: str, approved: bool, roi_score: int, notes: str, quality: str) -> bool:
        """
        Mark match as processed in Raw Match Feed.
        
        Args:
            match_id: Notion page ID
            approved: Whether match was approved
            roi_score: Calculated ROI score
            notes: Explanation/notes
            quality: Data quality level
            
        Returns:
            True if successful
        """
        if not self.raw_feed_db:
            return False
        
        try:
            update_props = {
                "AI Processed": {
                    "checkbox": True
                },
                "AI Approved": {
                    "checkbox": approved
                },
                "AI Score": {
                    "number": roi_score
                },
                "Raw Data Quality": {
                    "select": {"name": quality}
                }
            }
            
            # Add notes if field exists
            if notes:
                update_props["AI Notes"] = {
                    "rich_text": [{"text": {"content": notes}}]
                }
            
            self.notion.pages.update(
                page_id=match_id,
                properties=update_props
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error marking match as processed: {e}")
            return False
    
    def process_matches(self):
        """
        Main processing loop.
        """
        logger.info("🤖 Starting AI Match Filter...")
        logger.info(f"Timestamp: {datetime.now().isoformat()}\n")
        
        matches = self.get_unprocessed_matches()
        
        if not matches:
            logger.info("✅ No matches to process")
            return
        
        approved_count = 0
        rejected_count = 0
        
        for i, match in enumerate(matches, 1):
            props = match.get("properties", {})
            match_id_text = props.get("Match ID", {}).get("title", [{}])[0].get("text", {}).get("content", "Unknown")
            
            logger.info(f"\n[{i}/{len(matches)}] Processing: {match_id_text}")
            
            # 1. Check data quality
            quality, missing = self.check_data_quality(match)
            logger.info(f"  Quality: {quality}")
            if missing:
                logger.info(f"  Missing: {', '.join(missing)}")
            
            # 2. Get player data
            player_a_elem = props.get("Player A Name", {}).get("rich_text", [])
            player_a_name = player_a_elem[0]["text"]["content"] if player_a_elem else ""
            
            player_b_elem = props.get("Player B Name", {}).get("rich_text", [])
            player_b_name = player_b_elem[0]["text"]["content"] if player_b_elem else ""
            
            player_a_data = self.get_player_data(player_a_name) if player_a_name else None
            player_b_data = self.get_player_data(player_b_name) if player_b_name else None
            
            logger.info(f"  Player A: {'✓' if player_a_data else '✗'} {player_a_name}")
            logger.info(f"  Player B: {'✓' if player_b_data else '✗'} {player_b_name}")
            
            # 3. Calculate ROI score
            roi_score, explanation = self.calculate_roi_score(match, player_a_data, player_b_data, quality)
            logger.info(f"  ROI Score: {roi_score}/100")
            logger.info(f"  Breakdown: {explanation}")
            
            # 4. Decide approval
            tier = props.get("Tournament Tier", {}).get("select", {}).get("name", "")
            approved = self.should_approve(roi_score, quality, tier)
            
            if approved:
                logger.info(f"  ✅ APPROVED")
                approved_count += 1
                
                # Copy to Tennis Prematch DB
                try:
                    success = self.copy_to_prematch_db(match, roi_score, player_a_data, player_b_data)
                    if not success:
                        approved = False
                        explanation += " | Copy error"
                except Exception as e:
                    logger.error(f"  ❌ Error copying to Prematch DB: {str(e)}")
                    approved = False
                    explanation += f" | Copy error: {str(e)}"
            else:
                logger.info(f"  ❌ REJECTED")
                rejected_count += 1
            
            # 5. Mark as processed
            self.mark_processed(match["id"], approved, roi_score, explanation, quality)
            
            # Rate limiting (2.5 req/sec = 0.4s delay)
            time.sleep(0.4)
        
        logger.info(f"\n" + "="*50)
        logger.info(f"✅ Processing complete!")
        logger.info(f"Approved: {approved_count}")
        logger.info(f"Rejected: {rejected_count}")
        logger.info(f"Total: {len(matches)}")
        if len(matches) > 0:
            logger.info(f"Approval rate: {approved_count/len(matches)*100:.1f}%")


def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        filter = MatchFilter()
        filter.process_matches()
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


