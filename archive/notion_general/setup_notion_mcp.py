#!/usr/bin/env python3
"""
🚀 NOTION MCP SETUP - AUTOMAATTINEN KONFIGUROINTI
==================================================

Automaattinen setup-skripti Notion MCP -integraatiolle.

Author: TennisBot Advanced Analytics
Version: 1.0.0
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.notion_mcp_integration import NotionMCPIntegration


def main():
    """Main setup function"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║  📊 NOTION MCP SETUP                                         ║
║  ==========================================================  ║
║                                                              ║
║  Automaattinen Notion-tietokantojen luonti                  ║
║  High ROI -optimoitu rakenne                                 ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Initialize integration
    integration = NotionMCPIntegration()
    
    # Option 1: Browser authentication
    print("\n🔐 Authentication Options:")
    print("1. Browser authentication (automatic)")
    print("2. API token authentication")
    
    choice = input("\nSelect option (1 or 2): ").strip()
    
    if choice == "1":
        email = input("Enter Notion email: ").strip()
        password = input("Enter Notion password: ").strip()
        
        print("\n🌐 Authenticating via browser...")
        success = integration.authenticate_via_browser(email, password)
        
        if success:
            print("✅ Authentication successful!")
            
            # Try to get token from browser
            token = integration.get_notion_token_from_browser()
            if token:
                print(f"📝 Token extracted: {token[:20]}...")
                integration.initialize_notion_client(token)
        else:
            print("❌ Authentication failed")
            return
    
    elif choice == "2":
        token = input("Enter Notion API token: ").strip()
        integration.initialize_notion_client(token)
        print("✅ API token set")
    
    else:
        print("❌ Invalid option")
        return
    
    # Get parent page ID
    print("\n📄 Parent Page Setup:")
    print("Create a new page in Notion or use existing page ID")
    parent_page_id = input("Enter Notion page ID (or press Enter to skip): ").strip()
    
    if not parent_page_id:
        print("⚠️ Skipping database creation. Use prompts in NOTION_DATABASE_PROMPTS.md")
        return
    
    # Create databases
    print("\n🏗️ Creating databases...")
    databases = integration.create_roi_database_structure(parent_page_id)
    
    if databases:
        print(f"\n✅ Created {len(databases)} databases:")
        for sport, db_id in databases.items():
            print(f"   • {sport}: {db_id}")
        
        # Save database IDs
        config_file = Path('config/notion_databases.json')
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            import json
            json.dump(databases, f, indent=2)
        
        print(f"\n💾 Database IDs saved to {config_file}")
    else:
        print("❌ Failed to create databases")
    
    # Close browser
    integration.close_browser()
    
    print("\n✅ Setup complete!")
    print("\n📚 Next steps:")
    print("1. Review databases in Notion")
    print("2. Use sync functions to add data")
    print("3. Check NOTION_DATABASE_PROMPTS.md for manual setup")


if __name__ == "__main__":
    main()

