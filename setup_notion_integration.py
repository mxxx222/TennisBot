#!/usr/bin/env python3
"""
🔗 NOTION INTEGRATION SETUP - AUTOMAATTINEN
===========================================

Automaattinen Notion-integration setup-skripti.

Author: TennisBot Advanced Analytics
Version: 1.0.0
"""

import os
import json
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.notion_mcp_integration import NotionMCPIntegration
except ImportError:
    print("❌ Error: Could not import NotionMCPIntegration")
    print("   Make sure src/notion_mcp_integration.py exists")
    sys.exit(1)


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║  🔗 NOTION INTEGRATION SETUP                                ║
║  ==========================================================  ║
║                                                              ║
║  Automaattinen Notion-integration setup                     ║
║  High ROI -optimoitu rakenne                                 ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # 1. Hae token
    print("\n📋 VAIHE 1: Integration Token")
    print("=" * 50)
    print("1. Mene: https://www.notion.so/my-integrations")
    print("2. Klikkaa '+ New integration'")
    print("3. Täytä:")
    print("   - Nimi: TennisBot ROI System")
    print("   - Työtila: [Valitse oma työtilasi]")
    print("   - Tyyppi: Internal")
    print("4. Klikkaa 'Submit'")
    print("5. Kopioi 'Internal Integration Token'")
    print("\n💡 Token näyttää: secret_abc123xyz...")
    
    token = input("\n📝 Liitä token tähän: ").strip()
    
    if not token or not token.startswith('secret_'):
        print("⚠️ Warning: Token should start with 'secret_'")
        if input("Jatketaanko silti? (y/n): ").lower() != 'y':
            return
    
    # 2. Hae parent page ID
    print("\n📋 VAIHE 2: Parent Page ID")
    print("=" * 50)
    print("1. Avaa Notion-sivu johon haluat lisätä tietokannat")
    print("2. Klikkaa '...' (kolme pistettä) oikealla yläkulmassa")
    print("3. Valitse 'Connections' tai 'Add connections'")
    print("4. Lisää 'TennisBot ROI System' -integration")
    print("5. Kopioi sivun ID URL:sta")
    print("\n💡 URL-muoto: notion.so/[workspace]/[page-id]")
    print("   Kopioi vain [page-id] osa (32 merkkiä)")
    
    page_id = input("\n📝 Liitä page ID tähän: ").strip()
    
    if not page_id:
        print("❌ Page ID required!")
        return
    
    # Clean page ID (remove URL parts if included)
    if '/' in page_id:
        page_id = page_id.split('/')[-1]
    if '?' in page_id:
        page_id = page_id.split('?')[0]
    
    # 3. Initialize
    print("\n🔧 Initializing integration...")
    try:
        integration = NotionMCPIntegration()
        integration.initialize_notion_client(token)
        print("✅ Integration initialized")
    except Exception as e:
        print(f"❌ Error initializing: {e}")
        return
    
    # 4. Create databases
    print("\n🏗️ Creating databases...")
    print("   This may take a few moments...")
    print("   Creating 5 databases: Tennis, Football, Basketball, Ice Hockey, ROI Analysis...")
    
    try:
        databases = integration.create_roi_database_structure(page_id)
        
        if databases:
            print(f"\n✅ Created {len(databases)} databases:")
            for sport, db_id in databases.items():
                print(f"   • {sport}: {db_id}")
            
            # Save config
            config_file = Path('config/notion_databases.json')
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            config_data = {
                'token': token,
                'parent_page_id': page_id,
                'databases': databases,
                'created_at': str(Path(__file__).stat().st_mtime)
            }
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            print(f"\n💾 Config saved to {config_file}")
            print("\n✅ Setup complete!")
            print("\n📚 Next steps:")
            print("1. Check Notion - databases should be visible")
            print("2. Use sync functions to add data")
            print("3. Check NOTION_DATABASE_PROMPTS.md for manual setup")
        else:
            print("❌ Failed to create databases")
            print("   Check that:")
            print("   - Token is correct")
            print("   - Page ID is correct")
            print("   - Integration is connected to the page")
    
    except Exception as e:
        print(f"❌ Error creating databases: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

