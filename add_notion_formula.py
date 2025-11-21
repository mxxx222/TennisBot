#!/usr/bin/env python3
"""
Attempt to add Odds Advantage % formula to Notion database
Note: Notion API doesn't support creating formula properties programmatically
This script will verify and provide instructions
"""

import os
from dotenv import load_dotenv
from notion_client import Client

# Load environment
load_dotenv('telegram_secrets.env')

token = os.getenv('NOTION_TOKEN') or os.getenv('NOTION_API_KEY')
db_id = os.getenv('NOTION_TENNIS_PREMATCH_DB_ID')

if not token or not db_id:
    print("❌ Missing NOTION_TOKEN or NOTION_TENNIS_PREMATCH_DB_ID")
    exit(1)

client = Client(auth=token)

try:
    # Get current database schema
    database = client.databases.retrieve(database_id=db_id)
    properties = database.get('properties', {})
    
    print(f"✅ Connected to database: {db_id[:8]}...")
    print(f"📊 Current properties: {len(properties)}")
    
    # Check if formula already exists
    if 'Odds Advantage %' in properties:
        print("✅ 'Odds Advantage %' formula already exists!")
        formula_prop = properties['Odds Advantage %']
        print(f"   Type: {formula_prop.get('type')}")
        if formula_prop.get('type') == 'formula':
            print(f"   Formula: {formula_prop.get('formula', {}).get('expression', 'N/A')}")
        exit(0)
    
    # Try to add formula property (this will fail - API limitation)
    print("\n⚠️ Attempting to add formula property via API...")
    print("   (This will fail - Notion API doesn't support creating formulas)")
    
    try:
        client.databases.update(
            database_id=db_id,
            properties={
                'Odds Advantage %': {
                    'formula': {
                        'expression': 'if(prop("Best Odds P1") > 0 and prop("Player A Odds") > 0, (prop("Best Odds P1") / prop("Player A Odds") - 1) * 100, 0)'
                    }
                }
            }
        )
        print("✅ Formula added successfully!")
    except Exception as e:
        print(f"❌ API Error (expected): {e}")
        print("\n" + "="*80)
        print("📝 MANUAL INSTRUCTIONS")
        print("="*80)
        print("\nNotion API doesn't support creating formula properties.")
        print("You must add it manually in the Notion UI:\n")
        print("1. Open your Tennis Prematch database:")
        print(f"   https://www.notion.so/{db_id.replace('-', '')}")
        print("\n2. Click the '+' button to add a new property")
        print("\n3. Name: Odds Advantage %")
        print("\n4. Type: Formula")
        print("\n5. Paste this formula:")
        print("\n" + "-"*80)
        print("if(")
        print("  prop(\"Best Odds P1\") > 0 and prop(\"Player A Odds\") > 0,")
        print("  (prop(\"Best Odds P1\") / prop(\"Player A Odds\") - 1) * 100,")
        print("  0")
        print(")")
        print("-"*80)
        print("\n6. Click 'Done' to save")
        print("\n✅ That's it! The formula will calculate automatically.")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

