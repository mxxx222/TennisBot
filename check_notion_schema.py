#!/usr/bin/env python3
"""
🔍 Check Notion Database Schema
Hakee Tennis Prematch -tietokannan kentät
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
    print("❌ notion-client not installed")
    sys.exit(1)

def check_database_schema():
    """Hae tietokannan schema"""
    token = os.getenv('NOTION_API_KEY') or os.getenv('NOTION_TOKEN')
    db_id = os.getenv('NOTION_TENNIS_PREMATCH_DB_ID')
    
    if not token:
        print("❌ Notion token not found")
        return
    
    if not db_id:
        print("❌ Database ID not found")
        return
    
    client = Client(auth=token)
    
    try:
        # Get database schema
        database = client.databases.retrieve(database_id=db_id)
        
        print("\n" + "="*80)
        print("📊 NOTION DATABASE SCHEMA")
        print("="*80)
        print(f"\nDatabase: {database.get('title', [{}])[0].get('plain_text', 'Unknown')}")
        print(f"ID: {db_id}")
        
        print("\n📋 Properties:")
        properties = database.get('properties', {})
        
        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get('type', 'unknown')
            print(f"\n  • {prop_name}")
            print(f"    Type: {prop_type}")
            
            # Show options for select/multi_select
            if prop_type in ['select', 'multi_select']:
                options = prop_data.get(prop_type, {}).get('options', [])
                if options:
                    print(f"    Options: {', '.join([opt.get('name', '') for opt in options])}")
            
            # Show format for date
            if prop_type == 'date':
                date_format = prop_data.get('date', {}).get('format', 'default')
                print(f"    Format: {date_format}")
        
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database_schema()

