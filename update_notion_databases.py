#!/usr/bin/env python3
"""
📊 Update Notion Database IDs
Päivittää Notion database ID:t konfiguraatioihin
"""

import os
import json
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

def get_all_databases():
    """Hae kaikki saatavilla olevat tietokannat"""
    token = os.getenv('NOTION_API_KEY') or os.getenv('NOTION_TOKEN')
    if not token:
        print("❌ Notion token not found")
        return {}
    
    client = Client(auth=token)
    response = client.search(filter={"property": "object", "value": "database"})
    
    databases = {}
    if response and 'results' in response:
        for db in response['results']:
            db_id = db.get('id', '').replace('-', '')
            title = "Untitled"
            if 'title' in db and db['title']:
                if isinstance(db['title'], list) and len(db['title']) > 0:
                    title = db['title'][0].get('plain_text', 'Untitled')
            
            databases[title] = db_id
    
    return databases

def update_config_file(databases):
    """Päivitä config/notion_config.json"""
    config_path = Path(__file__).parent / 'config' / 'notion_config.json'
    
    if not config_path.exists():
        print(f"⚠️ Config file not found: {config_path}")
        return
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Map database names to config keys
    name_mapping = {
        '🎾 TennisExplorer Live Feed': 'live_feed',
        '🎾 ITF Player Profiles': 'players',
        'Tennis Vihjeet': 'bets',
        '🎾 Tennis Prematch – Analyysi': 'tennis_prematch',
        'LiveTennis – Signaalit': 'signals',
        'Pelaajatilastot (Tennis)': 'analytics_base',
        '📊 Pelaajatilastot – Players': 'players',
    }
    
    updated = False
    for db_name, db_id in databases.items():
        config_key = name_mapping.get(db_name)
        if config_key and config_key in config.get('databases', {}):
            old_id = config['databases'][config_key]
            if old_id != db_id:
                config['databases'][config_key] = db_id
                updated = True
                print(f"✅ Updated {config_key}: {db_id[:20]}...")
    
    if updated:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"\n✅ Config file updated: {config_path}")
    else:
        print("\n⚠️ No updates needed")

def update_env_file(databases):
    """Päivitä telegram_secrets.env database ID:illä"""
    env_path = Path(__file__).parent / 'telegram_secrets.env'
    
    if not env_path.exists():
        print(f"⚠️ Env file not found: {env_path}")
        return
    
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Map database names to env variable names
    name_mapping = {
        '🎾 TennisExplorer Live Feed': 'NOTION_LIVE_FEED_DB_ID',
        '🎾 ITF Player Profiles': 'NOTION_PLAYERS_DB_ID',
        'Tennis Vihjeet': 'NOTION_BETS_DATABASE_ID',
        '🎾 Tennis Prematch – Analyysi': 'NOTION_TENNIS_PREMATCH_DB_ID',
        'LiveTennis – Signaalit': 'NOTION_SIGNALS_DB_ID',
    }
    
    # Check existing variables
    existing_vars = {}
    for i, line in enumerate(lines):
        if '=' in line and not line.strip().startswith('#'):
            key = line.split('=')[0].strip()
            existing_vars[key] = i
    
    updated_lines = lines.copy()
    added = False
    
    for db_name, db_id in databases.items():
        env_var = name_mapping.get(db_name)
        if env_var:
            db_id_formatted = db_id
            if env_var in existing_vars:
                # Update existing
                idx = existing_vars[env_var]
                updated_lines[idx] = f"{env_var}={db_id_formatted}\n"
                print(f"✅ Updated {env_var}: {db_id[:20]}...")
            else:
                # Add new
                updated_lines.append(f"{env_var}={db_id_formatted}\n")
                added = True
                print(f"✅ Added {env_var}: {db_id[:20]}...")
    
    if added or any(updated_lines[i] != lines[i] for i in existing_vars.values()):
        with open(env_path, 'w') as f:
            f.writelines(updated_lines)
        print(f"\n✅ Env file updated: {env_path}")
    else:
        print("\n⚠️ No updates needed")

def main():
    print("\n" + "="*80)
    print("📊 UPDATING NOTION DATABASE IDs")
    print("="*80)
    
    databases = get_all_databases()
    
    if not databases:
        print("❌ No databases found")
        return
    
    print(f"\n✅ Found {len(databases)} databases")
    print("\n📋 Available databases:")
    for name, db_id in list(databases.items())[:10]:
        print(f"   - {name}: {db_id[:20]}...")
    
    print("\n🔄 Updating configuration files...")
    update_config_file(databases)
    update_env_file(databases)
    
    print("\n✅ Done!")

if __name__ == "__main__":
    main()

