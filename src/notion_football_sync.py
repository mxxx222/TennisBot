#!/usr/bin/env python3
"""
Notion Football Sync - Synkronoi jalkapallodataa Notioniin
Integroituu highest_roi_system.py ja prematch_roi_system.py kanssa
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests
from pathlib import Path


class NotionFootballSync:
    """Synkronoi jalkapallo-ottelut, analytiikan ja vedot Notioniin"""
    
    def __init__(self, config_path: str = "config/notion_config.json"):
        """Alusta Notion-synkronointi"""
        self.config_path = config_path
        self.config = self._load_config()
        self.token = self.config.get("notion_token", "")
        self.page_id = self.config.get("page_id", "")
        self.databases = self.config.get("databases", {})
        
        # Notion API headers
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        # Validate config
        if not self.token or self.token == "PASTE_YOUR_TOKEN_HERE":
            print("⚠️ HUOM: Notion token ei ole asetettu!")
            print("📝 Aseta token tiedostoon: config/notion_config.json")
    
    def _load_config(self) -> Dict:
        """Lataa konfiguraatio"""
        config_file = Path(self.config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_config(self):
        """Tallenna konfiguraatio"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def is_configured(self) -> bool:
        """Tarkista onko Notion konfiguroitu"""
        return (
            self.token and 
            self.token != "PASTE_YOUR_TOKEN_HERE" and
            self.page_id and 
            self.page_id != "PASTE_YOUR_PAGE_ID_HERE"
        )
    
    def create_database(self, name: str, properties: Dict) -> Optional[str]:
        """Luo uusi tietokanta Notioniin"""
        if not self.is_configured():
            print("❌ Notion ei ole konfiguroitu!")
            return None
        
        url = "https://api.notion.com/v1/databases"
        
        data = {
            "parent": {"type": "page_id", "page_id": self.page_id},
            "title": [{"type": "text", "text": {"content": name}}],
            "properties": properties
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            db_data = response.json()
            db_id = db_data.get("id", "")
            
            print(f"✅ Tietokanta '{name}' luotu: {db_id}")
            return db_id
        except Exception as e:
            print(f"❌ Virhe luodessa tietokantaa '{name}': {e}")
            return None
    
    def sync_match(self, match_data: Dict) -> Optional[str]:
        """
        Synkronoi ottelu Notioniin
        
        Args:
            match_data: {
                'home_team': str,
                'away_team': str,
                'league': str,
                'date_time': str (ISO format),
                'status': str ('Scheduled', 'Live', 'Finished'),
                'home_goals': int (optional),
                'away_goals': int (optional),
                'home_xg': float (optional),
                'away_xg': float (optional)
            }
        """
        if not self.is_configured():
            print("⚠️ Notion ei ole konfiguroitu, skipataan synkronointi")
            return None
        
        db_id = self.databases.get("ottelut", "")
        if not db_id:
            print("⚠️ Ottelut-tietokanta ei ole konfiguroitu")
            return None
        
        url = "https://api.notion.com/v1/pages"
        
        properties = {
            "Date & Time": {
                "date": {
                    "start": match_data.get("date_time", datetime.now().isoformat())
                }
            },
            "Liiga": {
                "select": {"name": match_data.get("league", "Unknown")}
            },
            "Status": {
                "select": {"name": match_data.get("status", "Scheduled")}
            }
        }
        
        # Lisää maalit jos saatavilla
        if "home_goals" in match_data:
            properties["Koti maalit"] = {"number": match_data["home_goals"]}
        if "away_goals" in match_data:
            properties["Vieras maalit"] = {"number": match_data["away_goals"]}
        
        # Lisää xG jos saatavilla
        if "home_xg" in match_data:
            properties["Koti xG (pre)"] = {"number": round(match_data["home_xg"], 2)}
        if "away_xg" in match_data:
            properties["Vieras xG (pre)"] = {"number": round(match_data["away_xg"], 2)}
        
        data = {
            "parent": {"database_id": db_id},
            "properties": properties
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            page_data = response.json()
            page_id = page_data.get("id", "")
            
            print(f"✅ Ottelu synkronoitu: {match_data.get('home_team')} vs {match_data.get('away_team')}")
            return page_id
        except Exception as e:
            print(f"❌ Virhe synkronoidessa ottelua: {e}")
            return None
    
    def sync_analysis(self, analysis_data: Dict) -> Optional[str]:
        """
        Synkronoi analytiikka Notioniin
        
        Args:
            analysis_data: {
                'match_id': str (Notion page ID),
                'xg_edge_pct': float,
                'h2h_win_pct': float,
                'form_edge_pct': float,
                'injury_impact': int (0-10),
                'own_probability_pct': float,
                'market_probability_pct': float,
                'best_bet_type': str,
                'notes': str
            }
        """
        if not self.is_configured():
            print("⚠️ Notion ei ole konfiguroitu, skipataan synkronointi")
            return None
        
        db_id = self.databases.get("analytiikka", "")
        if not db_id:
            print("⚠️ Analytiikka-tietokanta ei ole konfiguroitu")
            return None
        
        url = "https://api.notion.com/v1/pages"
        
        properties = {
            "H2H voitto %": {"number": analysis_data.get("h2h_win_pct", 0)},
            "Form Edge %": {"number": analysis_data.get("form_edge_pct", 0)},
            "Injury Impact": {"number": analysis_data.get("injury_impact", 0)},
            "Oma probability %": {"number": analysis_data.get("own_probability_pct", 0)},
            "Markkina probability %": {"number": analysis_data.get("market_probability_pct", 0)},
            "Paras bet-tyyppi": {"select": {"name": analysis_data.get("best_bet_type", "1X2")}},
            "Pelaa?": {"select": {"name": "PLAY" if analysis_data.get("edge_pct", 0) > 4 else "WAIT"}}
        }
        
        # Lisää ottelu-linkki jos saatavilla
        if "match_id" in analysis_data:
            properties["Ottelu"] = {"relation": [{"id": analysis_data["match_id"]}]}
        
        data = {
            "parent": {"database_id": db_id},
            "properties": properties
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            page_data = response.json()
            page_id = page_data.get("id", "")
            
            print(f"✅ Analytiikka synkronoitu")
            return page_id
        except Exception as e:
            print(f"❌ Virhe synkronoidessa analytiikkaa: {e}")
            return None
    
    def sync_bet(self, bet_data: Dict) -> Optional[str]:
        """
        Synkronoi veto Notioniin
        
        Args:
            bet_data: {
                'analysis_id': str (Notion page ID),
                'strategy_id': str (Notion page ID),
                'bet_type': str,
                'own_probability_pct': float,
                'odds': float,
                'bankroll': float,
                'placed': bool,
                'bookmaker': str,
                'bet_slip_url': str (optional)
            }
        """
        if not self.is_configured():
            print("⚠️ Notion ei ole konfiguroitu, skipataan synkronointi")
            return None
        
        db_id = self.databases.get("vedot", "")
        if not db_id:
            print("⚠️ Vedot-tietokanta ei ole konfiguroitu")
            return None
        
        url = "https://api.notion.com/v1/pages"
        
        properties = {
            "Veto-tyyppi": {"select": {"name": bet_data.get("bet_type", "1X2")}},
            "Oma probability %": {"number": bet_data.get("own_probability_pct", 0)},
            "Kerroin (desimal)": {"number": bet_data.get("odds", 0)},
            "Bankroll nykyinen": {"number": bet_data.get("bankroll", 0)},
            "Sijoitettu?": {"checkbox": bet_data.get("placed", False)},
            "Kirjauspalvelu": {"select": {"name": bet_data.get("bookmaker", "Pinnacle")}},
            "Tulos": {"select": {"name": "Pending"}},
            "Päivämäärä sijoitettu": {"date": {"start": datetime.now().isoformat()}}
        }
        
        # Lisää analytiikka-linkki
        if "analysis_id" in bet_data:
            properties["Analytiikka"] = {"relation": [{"id": bet_data["analysis_id"]}]}
        
        # Lisää strategia-linkki
        if "strategy_id" in bet_data:
            properties["Strategia"] = {"relation": [{"id": bet_data["strategy_id"]}]}
        
        # Lisää bet slip URL jos saatavilla
        if "bet_slip_url" in bet_data:
            properties["Bet slip URL"] = {"url": bet_data["bet_slip_url"]}
        
        data = {
            "parent": {"database_id": db_id},
            "properties": properties
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            page_data = response.json()
            page_id = page_data.get("id", "")
            
            print(f"✅ Veto synkronoitu: {bet_data.get('bet_type')} @ {bet_data.get('odds')}")
            return page_id
        except Exception as e:
            print(f"❌ Virhe synkronoidessa vetoa: {e}")
            return None
    
    def update_bet_result(self, bet_id: str, result: str, profit_loss: float = None) -> bool:
        """
        Päivitä vedon tulos
        
        Args:
            bet_id: Notion page ID
            result: 'Won', 'Lost', 'Void', 'Cancelled'
            profit_loss: Voitto/tappio euroissa (optional)
        """
        if not self.is_configured():
            print("⚠️ Notion ei ole konfiguroitu, skipataan päivitys")
            return False
        
        url = f"https://api.notion.com/v1/pages/{bet_id}"
        
        properties = {
            "Tulos": {"select": {"name": result}}
        }
        
        if profit_loss is not None:
            properties["Toteutunut voitto/tappio (€)"] = {"number": profit_loss}
        
        data = {"properties": properties}
        
        try:
            response = requests.patch(url, headers=self.headers, json=data)
            response.raise_for_status()
            
            print(f"✅ Vedon tulos päivitetty: {result}")
            return True
        except Exception as e:
            print(f"❌ Virhe päivittäessä vedon tulosta: {e}")
            return False
    
    def get_database_id(self, db_name: str) -> Optional[str]:
        """Hae tietokannan ID"""
        return self.databases.get(db_name, "")
    
    def set_database_id(self, db_name: str, db_id: str):
        """Aseta tietokannan ID"""
        self.databases[db_name] = db_id
        self.config["databases"] = self.databases
        self._save_config()
        print(f"✅ Tietokannan '{db_name}' ID tallennettu: {db_id}")


# Käyttöesimerkki
if __name__ == "__main__":
    print("🔧 Notion Football Sync - Testaus\n")
    
    sync = NotionFootballSync()
    
    if not sync.is_configured():
        print("❌ Notion ei ole konfiguroitu!")
        print("\n📝 Konfiguroi Notion:")
        print("1. Avaa: https://www.notion.so/my-integrations")
        print("2. Luo uusi integration: 'TennisBot ROI System'")
        print("3. Kopioi token → config/notion_config.json")
        print("4. Luo Notion-sivu: 'Jalkapallo ROI System'")
        print("5. Linkitä integration sivulle (Connections)")
        print("6. Kopioi page ID → config/notion_config.json")
    else:
        print("✅ Notion on konfiguroitu!")
        print(f"📊 Token: {sync.token[:20]}...")
        print(f"📄 Page ID: {sync.page_id}")
        
        # Testaa yhteys
        print("\n🧪 Testataan yhteyttä...")
        
        # Esimerkki: Synkronoi ottelu
        match_data = {
            "home_team": "Manchester City",
            "away_team": "Liverpool",
            "league": "Premier League",
            "date_time": "2025-12-13T18:00:00",
            "status": "Scheduled",
            "home_xg": 2.8,
            "away_xg": 2.1
        }
        
        # match_id = sync.sync_match(match_data)
        # if match_id:
        #     print(f"✅ Testottelu luotu: {match_id}")

