#!/usr/bin/env python3
"""
🧪 TEST NOTION MCP BET LOGGER
=============================
Testaa betin kirjausta Notioniin käyttäen MCP:ta
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from notion_mcp_integration import NotionMCPIntegration
    from notion_bet_logger import NotionBetLogger
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_mcp_bet_logging():
    """Testaa betin kirjaus MCP:lla"""
    print("\n" + "="*80)
    print("🧪 TEST NOTION MCP BET LOGGING")
    print("="*80 + "\n")
    
    # Initialize MCP
    print("1️⃣ Initializing NotionMCPIntegration...")
    mcp = NotionMCPIntegration()
    
    if not mcp.notion_token:
        print("⚠️ No token found in MCP")
        print("💡 MCP might use browser auth or token is set elsewhere")
        print("💡 Trying to initialize client anyway...")
    else:
        print(f"✅ Token found: {mcp.notion_token[:30]}...")
        mcp.initialize_notion_client(mcp.notion_token)
    
    # Try to use NotionBetLogger which uses MCP
    print("\n2️⃣ Initializing NotionBetLogger (uses MCP)...")
    logger = NotionBetLogger()
    
    if not logger.client:
        print("❌ Notion client not available")
        print("\n💡 Setup options:")
        print("   1. Set NOTION_TOKEN environment variable")
        print("   2. Add to telegram_secrets.env: NOTION_TOKEN=secret_xxxxx")
        print("   3. Add to config/notion_config.json: {\"notion_token\": \"secret_xxxxx\"}")
        return False
    
    print("✅ Notion client available!")
    
    if not logger.database_id:
        print("⚠️ Database ID not found")
        print("💡 Add NOTION_BETS_DATABASE_ID to config")
        print("💡 Or pass database_id to NotionBetLogger()")
        return False
    
    print(f"✅ Database ID: {logger.database_id[:20]}...")
    
    # Test bet from today's scan
    print("\n3️⃣ Logging test bet...")
    page_id = logger.log_bet(
        tournament="ITF W15 Sharm ElSheikh 20 Women",
        player1="Sciahbasi L.",
        player2="Durasovic V.",
        selected_player="Sciahbasi L.",
        odds=1.75,
        stake=10.00,
        player1_ranking=245,
        player2_ranking=312,
        surface="Hard",
        bookmaker="Bet365",
        notes=f"Test bet from automation - {datetime.now().strftime('%Y-%m-%d %H:%M')} - MCP integration test"
    )
    
    if page_id:
        print(f"\n✅ Test bet logged successfully!")
        print(f"📄 Page ID: {page_id}")
        print(f"🔗 View in Notion: https://www.notion.so/{page_id.replace('-', '')}")
        return True
    else:
        print("\n❌ Failed to log bet")
        return False

if __name__ == "__main__":
    success = test_mcp_bet_logging()
    sys.exit(0 if success else 1)

