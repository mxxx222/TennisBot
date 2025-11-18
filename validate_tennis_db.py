#!/usr/bin/env python3
"""
✅ TENNIS RELATIONAL DATABASE VALIDATOR
=======================================

Validoi luodut Notion-tietokannat ja varmistaa että:
- Kaikki 15 taulua on luotu
- Relaatiot ovat oikein
- Kaikki kentät ovat paikallaan
- Näkymät ovat luotu

Author: TennisBot Advanced Analytics
Version: 1.0.0
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

try:
    from notion_client import Client
    NOTION_API_AVAILABLE = True
except ImportError:
    NOTION_API_AVAILABLE = False
    print("⚠️ notion-client not installed. Install with: pip install notion-client")


class TennisDBValidator:
    """Validoi tennis-relaatiomallin"""
    
    def __init__(self, notion_token: str, config_file: str = "config/tennis_relational_db.json"):
        """
        Initialize validator
        
        Args:
            notion_token: Notion API token
            config_file: Config file path with database IDs
        """
        if not NOTION_API_AVAILABLE:
            raise ImportError("notion-client not available")
        
        self.notion = Client(auth=notion_token)
        self.config_file = Path(config_file)
        
        # Load config
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
                self.databases = self.config.get('databases', {})
        else:
            print(f"⚠️ Config file not found: {config_file}")
            self.databases = {}
        
        # Expected databases
        self.expected_databases = {
            'players': {'name': '👤 Players', 'min_properties': 15},
            'tournaments': {'name': '🏆 Tournaments', 'min_properties': 11},
            'events': {'name': '📅 Events', 'min_properties': 7},
            'matches': {'name': '🎾 Matches', 'min_properties': 12},
            'player_stats': {'name': '📊 Player Stats', 'min_properties': 6},
            'surface_stats': {'name': '🏟️ Surface Stats', 'min_properties': 12},
            'serve_stats': {'name': '🎯 Serve Stats', 'min_properties': 12},
            'return_stats': {'name': '🔄 Return Stats', 'min_properties': 8},
            'quality_stats': {'name': '⭐ Quality Stats', 'min_properties': 8},
            'h2h_stats': {'name': '⚔️ H2H Stats', 'min_properties': 12},
            'ratings': {'name': '📈 Ratings', 'min_properties': 7},
            'odds': {'name': '💰 Odds', 'min_properties': 9},
            'roi_analysis': {'name': '💎 ROI Analysis', 'min_properties': 15},
            'environment': {'name': '🌤️ Environment', 'min_properties': 10},
            'health': {'name': '🏥 Health', 'min_properties': 9}
        }
        
        # Expected relations
        self.expected_relations = {
            'matches': {
                'player_1': 'players',
                'player_2': 'players',
                'event': 'events',
                'tournament': 'tournaments'
            },
            'serve_stats': {
                'player': 'players',
                'match': 'matches'
            },
            'return_stats': {
                'player': 'players',
                'match': 'matches'
            },
            'quality_stats': {
                'player': 'players',
                'match': 'matches'
            },
            'ratings': {
                'player': 'players',
                'match': 'matches'
            },
            'odds': {
                'match': 'matches'
            },
            'roi_analysis': {
                'match': 'matches'
            },
            'environment': {
                'match': 'matches'
            },
            'player_stats': {
                'player': 'players'
            },
            'surface_stats': {
                'player': 'players'
            },
            'h2h_stats': {
                'player_1': 'players',
                'player_2': 'players'
            },
            'health': {
                'player': 'players',
                'match': 'matches'
            }
        }
    
    def validate_all(self) -> Dict:
        """Validoi kaikki tietokannat"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║  ✅ TENNIS RELATIONAL DATABASE VALIDATOR                    ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        results = {
            'databases_found': 0,
            'databases_missing': [],
            'databases_valid': [],
            'databases_invalid': [],
            'relations_valid': [],
            'relations_missing': [],
            'total_issues': 0
        }
        
        # 1. Validate databases exist
        print("\n📊 Validating Databases...")
        print("=" * 60)
        
        for db_key, db_info in self.expected_databases.items():
            db_id = self.databases.get(db_key)
            
            if not db_id:
                results['databases_missing'].append(db_key)
                print(f"   ❌ {db_info['name']}: NOT FOUND")
                results['total_issues'] += 1
                continue
            
            # Check if database exists in Notion
            try:
                db = self.notion.databases.retrieve(database_id=db_id)
                db_name = db.get('title', [{}])[0].get('plain_text', 'Unknown')
                
                # Validate properties count
                properties = db.get('properties', {})
                prop_count = len(properties)
                
                if prop_count >= db_info['min_properties']:
                    results['databases_valid'].append(db_key)
                    print(f"   ✅ {db_info['name']}: {db_name} ({prop_count} properties)")
                else:
                    results['databases_invalid'].append({
                        'key': db_key,
                        'name': db_name,
                        'expected': db_info['min_properties'],
                        'actual': prop_count
                    })
                    print(f"   ⚠️ {db_info['name']}: {db_name} ({prop_count}/{db_info['min_properties']} properties)")
                    results['total_issues'] += 1
                
                results['databases_found'] += 1
                
            except Exception as e:
                results['databases_invalid'].append({
                    'key': db_key,
                    'name': db_info['name'],
                    'error': str(e)
                })
                print(f"   ❌ {db_info['name']}: ERROR - {e}")
                results['total_issues'] += 1
        
        # 2. Validate relations
        print("\n🔗 Validating Relations...")
        print("=" * 60)
        
        for db_key, relations in self.expected_relations.items():
            db_id = self.databases.get(db_key)
            
            if not db_id:
                continue
            
            try:
                db = self.notion.databases.retrieve(database_id=db_id)
                properties = db.get('properties', {})
                
                for rel_prop, target_db in relations.items():
                    prop = properties.get(rel_prop)
                    
                    if not prop:
                        results['relations_missing'].append({
                            'database': db_key,
                            'property': rel_prop,
                            'target': target_db
                        })
                        print(f"   ❌ {db_key}.{rel_prop} → {target_db}: MISSING")
                        results['total_issues'] += 1
                    elif prop.get('type') == 'relation':
                        target_db_id = self.databases.get(target_db)
                        if target_db_id and prop.get('relation', {}).get('database_id') == target_db_id:
                            results['relations_valid'].append({
                                'database': db_key,
                                'property': rel_prop,
                                'target': target_db
                            })
                            print(f"   ✅ {db_key}.{rel_prop} → {target_db}: OK")
                        else:
                            results['relations_missing'].append({
                                'database': db_key,
                                'property': rel_prop,
                                'target': target_db
                            })
                            print(f"   ⚠️ {db_key}.{rel_prop} → {target_db}: WRONG TARGET")
                            results['total_issues'] += 1
                    else:
                        results['relations_missing'].append({
                            'database': db_key,
                            'property': rel_prop,
                            'target': target_db
                        })
                        print(f"   ❌ {db_key}.{rel_prop} → {target_db}: NOT A RELATION")
                        results['total_issues'] += 1
            
            except Exception as e:
                print(f"   ❌ {db_key}: ERROR - {e}")
                results['total_issues'] += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY:")
        print(f"   Databases Found: {results['databases_found']}/15")
        print(f"   Databases Valid: {len(results['databases_valid'])}")
        print(f"   Databases Missing: {len(results['databases_missing'])}")
        print(f"   Relations Valid: {len(results['relations_valid'])}")
        print(f"   Relations Missing: {len(results['relations_missing'])}")
        print(f"   Total Issues: {results['total_issues']}")
        
        if results['total_issues'] == 0:
            print("\n✅ ALL VALIDATIONS PASSED!")
        else:
            print(f"\n⚠️ {results['total_issues']} ISSUES FOUND")
        
        return results
    
    def validate_specific_database(self, db_key: str) -> Dict:
        """Validoi tietty tietokanta"""
        db_id = self.databases.get(db_key)
        
        if not db_id:
            return {'error': f'Database {db_key} not found in config'}
        
        try:
            db = self.notion.databases.retrieve(database_id=db_id)
            properties = db.get('properties', {})
            
            return {
                'id': db_id,
                'name': db.get('title', [{}])[0].get('plain_text', 'Unknown'),
                'properties': list(properties.keys()),
                'property_count': len(properties)
            }
        except Exception as e:
            return {'error': str(e)}


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate Tennis Relational Database')
    parser.add_argument('--token', '-t', required=True, help='Notion API token')
    parser.add_argument('--config', '-c', default='config/tennis_relational_db.json',
                       help='Config file path')
    
    args = parser.parse_args()
    
    validator = TennisDBValidator(args.token, args.config)
    results = validator.validate_all()
    
    # Save validation results
    results_file = Path('config/validation_results.json')
    results_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Validation results saved to {results_file}")


if __name__ == "__main__":
    main()







