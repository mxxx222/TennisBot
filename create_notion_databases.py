#!/usr/bin/env python3
"""
🏗️ CREATE NOTION DATABASES - AUTOMAATTINEN LUONTI
==================================================

Luo kaikki Notion-tietokannat automaattisesti kun integraatio on linkitetty.

Käyttö:
    python create_notion_databases.py --token YOUR_TOKEN --page-id YOUR_PAGE_ID

Author: TennisBot Advanced Analytics
Version: 1.0.0
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.notion_mcp_integration import NotionMCPIntegration
except ImportError:
    print("❌ Error: Could not import NotionMCPIntegration")
    print("   Make sure src/notion_mcp_integration.py exists")
    sys.exit(1)


def create_all_databases(integration: NotionMCPIntegration, parent_page_id: str, integration_name: str = "TennisBot ROI System"):
    """
    Luo kaikki tietokannat automaattisesti
    
    Args:
        integration: NotionMCPIntegration instance
        parent_page_id: Notion parent page ID
        integration_name: Integration name for logging
    """
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  🏗️ CREATING NOTION DATABASES                               ║
║  ==========================================================  ║
║                                                              ║
║  Integration: {integration_name}
║  Parent Page: {parent_page_id[:20]}...
╚══════════════════════════════════════════════════════════════╝
    """)
    
    databases = {}
    
    print("\n📊 Creating databases...")
    print("=" * 50)
    
    # 1. Tennis Database
    print("\n🎾 Creating Tennis Database...")
    try:
        tennis_db = integration.create_tennis_database(parent_page_id)
        if tennis_db:
            databases['tennis'] = tennis_db
            print(f"   ✅ Created: {tennis_db}")
        else:
            print("   ❌ Failed to create")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 2. Football Database
    print("\n⚽ Creating Football Database...")
    try:
        football_db = integration.create_football_database(parent_page_id)
        if football_db:
            databases['football'] = football_db
            print(f"   ✅ Created: {football_db}")
        else:
            print("   ❌ Failed to create")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 3. Basketball Database
    print("\n🏀 Creating Basketball Database...")
    try:
        basketball_db = integration.create_basketball_database(parent_page_id)
        if basketball_db:
            databases['basketball'] = basketball_db
            print(f"   ✅ Created: {basketball_db}")
        else:
            print("   ❌ Failed to create")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 4. Ice Hockey Database
    print("\n🏒 Creating Ice Hockey Database...")
    try:
        ice_hockey_db = integration.create_ice_hockey_database(parent_page_id)
        if ice_hockey_db:
            databases['ice_hockey'] = ice_hockey_db
            print(f"   ✅ Created: {ice_hockey_db}")
        else:
            print("   ❌ Failed to create")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 5. ROI Analysis Database
    print("\n💰 Creating ROI Analysis Database...")
    try:
        roi_db = integration.create_roi_analysis_database(parent_page_id)
        if roi_db:
            databases['roi_analysis'] = roi_db
            print(f"   ✅ Created: {roi_db}")
        else:
            print("   ❌ Failed to create")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 SUMMARY:")
    print(f"   Created: {len(databases)}/{5} databases")
    
    if databases:
        print("\n✅ Successfully created databases:")
        for sport, db_id in databases.items():
            print(f"   • {sport}: {db_id}")
        
        # Save to config
        config_file = Path('config/notion_databases.json')
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        config_data = {
            'integration_name': integration_name,
            'parent_page_id': parent_page_id,
            'databases': databases,
            'created_at': datetime.now().isoformat()
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        print(f"\n💾 Config saved to {config_file}")
        print("\n📚 Next steps:")
        print("1. Check Notion - databases should be visible on your page")
        print("2. Use sync functions to add data:")
        print("   from src.notion_mcp_integration import NotionMCPIntegration")
        print("   integration = NotionMCPIntegration()")
        print("   integration.initialize_notion_client('your_token')")
        print("   integration.sync_match_to_notion(match_data, 'tennis')")
    else:
        print("\n❌ No databases were created")
        print("   Check that:")
        print("   - Token is correct and valid")
        print("   - Page ID is correct")
        print("   - Integration is connected to the page")
    
    return databases


def main():
    parser = argparse.ArgumentParser(
        description='Create Notion databases for ROI analysis system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # With token and page ID
  python create_notion_databases.py --token secret_abc123 --page-id abc123def456
  
  # Interactive mode
  python create_notion_databases.py
  
  # With custom integration name
  python create_notion_databases.py --token secret_abc123 --page-id abc123 --name "Smart Value Detector"
        """
    )
    
    parser.add_argument('--token', '-t', help='Notion API token')
    parser.add_argument('--page-id', '-p', help='Notion parent page ID')
    parser.add_argument('--name', '-n', default='TennisBot ROI System', 
                       help='Integration name (default: TennisBot ROI System)')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Interactive mode')
    
    args = parser.parse_args()
    
    # Interactive mode
    if args.interactive or not args.token or not args.page_id:
        print("""
╔══════════════════════════════════════════════════════════════╗
║  🏗️ CREATE NOTION DATABASES - INTERACTIVE MODE             ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        print("\n📋 VAIHE 1: Integration Token")
        print("=" * 50)
        print("1. Mene: https://www.notion.so/my-integrations")
        print("2. Klikkaa '+ New integration'")
        print("3. Täytä lomake:")
        print("   - Nimi: TennisBot ROI System")
        print("   - Työtila: [Valitse oma työtilasi]")
        print("   - Tyyppi: Internal")
        print("4. Kopioi 'Internal Integration Token'")
        
        token = input("\n📝 Liitä token tähän: ").strip()
        
        if not token:
            print("❌ Token required!")
            return
        
        print("\n📋 VAIHE 2: Parent Page ID")
        print("=" * 50)
        print("1. Avaa Notion-sivu johon haluat lisätä tietokannat")
        print("2. Klikkaa '...' → 'Connections'")
        print("3. Lisää 'TennisBot ROI System' -integration")
        print("4. Kopioi sivun ID URL:sta")
        
        page_id = input("\n📝 Liitä page ID tähän: ").strip()
        
        if not page_id:
            print("❌ Page ID required!")
            return
        
        # Clean page ID
        if '/' in page_id:
            page_id = page_id.split('/')[-1]
        if '?' in page_id:
            page_id = page_id.split('?')[0]
        
        integration_name = input("\n📝 Integration name (default: TennisBot ROI System): ").strip()
        if not integration_name:
            integration_name = "TennisBot ROI System"
    
    else:
        token = args.token
        page_id = args.page_id
        integration_name = args.name
        
        # Clean page ID
        if '/' in page_id:
            page_id = page_id.split('/')[-1]
        if '?' in page_id:
            page_id = page_id.split('?')[0]
    
    # Initialize integration
    print("\n🔧 Initializing integration...")
    try:
        integration = NotionMCPIntegration()
        integration.initialize_notion_client(token)
        print("✅ Integration initialized")
    except Exception as e:
        print(f"❌ Error initializing: {e}")
        print("\n💡 Troubleshooting:")
        print("   - Check that token is correct")
        print("   - Token should start with 'secret_'")
        print("   - Make sure integration exists in Notion")
        return
    
    # Create databases
    databases = create_all_databases(integration, page_id, integration_name)
    
    if databases:
        print("\n✅ Setup complete!")
        print("\n🎉 All databases are now available in Notion!")
        print("   You can start syncing data using the integration functions.")


if __name__ == "__main__":
    main()






