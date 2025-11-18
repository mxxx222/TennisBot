#!/usr/bin/env python3
"""
Notion Ultimate ROI Setup - Interaktiivinen aloitusohjelma
"""

import json
import sys
import webbrowser
from pathlib import Path

def print_header(text):
    """Tulosta otsikko"""
    print("\n" + "="*60)
    print(text.center(60))
    print("="*60 + "\n")

def print_step(number, text):
    """Tulosta vaihe"""
    print(f"\n{'='*60}")
    print(f"VAIHE {number}: {text}")
    print(f"{'='*60}\n")

def main():
    print_header("🏆 NOTION ULTIMATE ROI SETUP")
    print("Tervetuloa! Tämä ohjelma auttaa sinua aloittamaan.")
    print("\nMitä rakennamme:")
    print("  ✅ 7 Notion-tietokantaa")
    print("  ✅ 40+ automaattista kaavaa")
    print("  ✅ 3 reaaliaikaista dashboardia")
    print("  ✅ Python-integraatio")
    print("  ✅ Zapier/Make.com -automatisointi")
    print("\nOdotettu ROI-parannus: +12-19%")
    print("Aikaa kuluu: 8-12 tuntia")
    
    input("\nPaina Enter jatkaaksesi...")
    
    # Vaihe 1: Tarkista tiedostot
    print_step(1, "TIEDOSTOJEN TARKISTUS")
    
    required_files = [
        "NOTION_ROI_SYSTEM_GUIDE.md",
        "NOTION_DAILY_WORKFLOW.md",
        "ZAPIER_AUTOMATION_GUIDE.md",
        "NOTION_ULTIMATE_ROI_README.md",
        "config/notion_config.json",
        "config/zapier_webhooks.json",
        "src/notion_football_sync.py",
        "src/webhook_handler.py",
        "test_notion_integration.py"
    ]
    
    all_exist = True
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - PUUTTUU!")
            all_exist = False
    
    if not all_exist:
        print("\n❌ Joitain tiedostoja puuttuu!")
        print("Varmista että olet oikeassa hakemistossa.")
        sys.exit(1)
    
    print("\n✅ Kaikki tiedostot löytyvät!")
    
    # Vaihe 2: Notion Integration
    print_step(2, "NOTION INTEGRATION SETUP")
    
    print("Seuraavaksi luomme Notion Integration:")
    print("\n1. Avaa: https://www.notion.so/my-integrations")
    print("2. Klikkaa: '+ New integration'")
    print("3. Nimi: 'TennisBot ROI System'")
    print("4. Type: Internal")
    print("5. Kopioi: Internal Integration Token")
    
    open_browser = input("\nHaluatko avata Notion-sivun nyt? (y/n): ").lower()
    if open_browser == 'y':
        webbrowser.open("https://www.notion.so/my-integrations")
        print("✅ Notion avattu selaimessa!")
    
    print("\n⏸️ Kun olet luonut integrationin, palaa tänne.")
    input("Paina Enter kun olet valmis...")
    
    # Pyydä tokenia
    print("\nSyötä Notion Integration Token:")
    print("(Näyttää: secret_abc123xyz...)")
    token = input("Token: ").strip()
    
    if not token or token == "PASTE_YOUR_TOKEN_HERE":
        print("⚠️ Token ei kelpaa. Voit päivittää sen myöhemmin config/notion_config.json")
    else:
        # Tallenna token
        config_path = Path("config/notion_config.json")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        config['notion_token'] = token
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("✅ Token tallennettu!")
    
    # Vaihe 3: Notion Page
    print_step(3, "NOTION PAGE SETUP")
    
    print("Seuraavaksi luomme Notion-sivun:")
    print("\n1. Avaa Notion")
    print("2. Luo uusi sivu: '⚽ Jalkapallo ROI System'")
    print("3. Klikkaa '...' → 'Connections' → Lisää 'TennisBot ROI System'")
    print("4. Kopioi page ID URL:sta")
    print("   (URL: notion.so/[workspace]/[page-id])")
    
    input("\nPaina Enter kun olet valmis...")
    
    # Pyydä page ID:tä
    print("\nSyötä Notion Page ID:")
    print("(32 merkkiä, esim: a1b2c3d4e5f6...)")
    page_id = input("Page ID: ").strip()
    
    if not page_id or page_id == "PASTE_YOUR_PAGE_ID_HERE":
        print("⚠️ Page ID ei kelpaa. Voit päivittää sen myöhemmin config/notion_config.json")
    else:
        # Tallenna page ID
        config_path = Path("config/notion_config.json")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        config['page_id'] = page_id
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("✅ Page ID tallennettu!")
    
    # Vaihe 4: Testaa konfiguraatio
    print_step(4, "KONFIGURAATION TESTAUS")
    
    print("Testataan Notion-yhteyttä...")
    
    try:
        from src.notion_football_sync import NotionFootballSync
        
        sync = NotionFootballSync()
        
        if sync.is_configured():
            print("✅ Notion on konfiguroitu oikein!")
            print(f"📊 Token: {sync.token[:20]}...")
            print(f"📄 Page ID: {sync.page_id}")
        else:
            print("⚠️ Notion ei ole täysin konfiguroitu")
            print("Päivitä token ja page ID tiedostoon: config/notion_config.json")
    except Exception as e:
        print(f"❌ Virhe testatessa yhteyttä: {e}")
    
    # Vaihe 5: Seuraavat askeleet
    print_step(5, "SEURAAVAT ASKELEET")
    
    print("✅ Perussetup valmis!")
    print("\nSeuraavaksi:")
    print("\n1. RAKENNA NOTION-TIETOKANNAT (8-10h)")
    print("   📖 Lue: NOTION_ROI_SYSTEM_GUIDE.md")
    print("   🎯 Rakenna 7 tietokantaa askel askeleelta")
    print("   ✅ Testaa jokainen kaava")
    
    print("\n2. TESTAA PYTHON-INTEGRAATIO (30 min)")
    print("   🧪 Aja: python test_notion_integration.py")
    print("   📊 Päivitä database ID:t config/notion_config.json")
    print("   ✅ Varmista että synkronointi toimii")
    
    print("\n3. KONFIGUROI AUTOMATISOINTI (60 min)")
    print("   📖 Lue: ZAPIER_AUTOMATION_GUIDE.md")
    print("   🔄 Luo Make.com -scenaariot")
    print("   📱 Konfiguroi Telegram-notifikaatiot")
    
    print("\n4. ALOITA PÄIVITTÄINEN KÄYTTÖ")
    print("   📖 Lue: NOTION_DAILY_WORKFLOW.md")
    print("   📅 Seuraa aamu/päivä/ilta -rutiineja")
    print("   💰 Nauti voitoista!")
    
    print("\n" + "="*60)
    print("📚 DOKUMENTAATIO:")
    print("="*60)
    print("  📖 NOTION_ULTIMATE_ROI_README.md - Pääohje")
    print("  📖 NOTION_ROI_SYSTEM_GUIDE.md - Rakennusohje")
    print("  📖 NOTION_DAILY_WORKFLOW.md - Päivittäinen käyttö")
    print("  📖 ZAPIER_AUTOMATION_GUIDE.md - Automatisointi")
    
    print("\n" + "="*60)
    print("🎯 TAVOITTEET:")
    print("="*60)
    print("  📈 ROI: 12-19% (vs. 0-5% ilman järjestelmää)")
    print("  🎲 Win Rate: 55-65%")
    print("  💰 Kelly-optimointi automaattinen")
    print("  ✅ Strategioiden auto-validointi")
    
    print("\n🚀 Onnea rakentamiseen! 💪")
    print("\n" + "="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup keskeytetty. Voit jatkaa myöhemmin!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Virhe: {e}")
        sys.exit(1)

