#!/usr/bin/env python3
"""
🧪 Test Notion Connection
Testaa Notion API -yhteyttä tokenilla
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / 'telegram_secrets.env'
if env_path.exists():
    load_dotenv(env_path)

try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    print("❌ notion-client not installed. Install with: pip install notion-client")
    sys.exit(1)

def test_notion_connection():
    """Testaa Notion API -yhteyttä"""
    print("\n" + "="*80)
    print("🧪 TESTING NOTION CONNECTION")
    print("="*80)
    
    # Try to get token from multiple sources
    token = (
        os.getenv('NOTION_API_KEY') or
        os.getenv('NOTION_TOKEN') or
        None
    )
    
    if not token:
        print("❌ Notion token not found!")
        print("\n💡 Token sources checked:")
        print("   - NOTION_API_KEY environment variable")
        print("   - NOTION_TOKEN environment variable")
        print("   - telegram_secrets.env file")
        return False
    
    print(f"✅ Token found: {token[:20]}...{token[-10:]}")
    
    try:
        # Initialize client
        client = Client(auth=token)
        print("✅ Notion client initialized")
        
        # Test connection by listing databases
        print("\n📊 Testing API connection...")
        response = client.search(filter={"property": "object", "value": "database"})
        
        if response and 'results' in response:
            databases = response['results']
            print(f"✅ Connection successful! Found {len(databases)} accessible databases")
            
            if databases:
                print("\n📋 Accessible databases:")
                for i, db in enumerate(databases[:10], 1):  # Show first 10
                    db_id = db.get('id', 'N/A')
                    title = "Untitled"
                    if 'title' in db and db['title']:
                        if isinstance(db['title'], list) and len(db['title']) > 0:
                            title = db['title'][0].get('plain_text', 'Untitled')
                    
                    print(f"   {i}. {title}")
                    print(f"      ID: {db_id}")
                    print()
            
            if len(databases) > 10:
                print(f"   ... and {len(databases) - 10} more databases")
            
            return True
        else:
            print("⚠️ Connection successful but no databases found")
            print("💡 Make sure the integration has access to your databases")
            return True
            
    except Exception as e:
        print(f"❌ Error connecting to Notion API: {e}")
        print(f"\nError type: {type(e).__name__}")
        
        if "Unauthorized" in str(e) or "401" in str(e):
            print("\n💡 Token might be invalid or expired")
            print("   1. Check token in telegram_secrets.env")
            print("   2. Verify token at https://www.notion.so/my-integrations")
        elif "403" in str(e):
            print("\n💡 Token is valid but lacks permissions")
            print("   1. Go to your Notion pages/databases")
            print("   2. Click '...' → 'Connections'")
            print("   3. Add your integration to grant access")
        
        return False

if __name__ == "__main__":
    success = test_notion_connection()
    sys.exit(0 if success else 1)

