# 🔗 NOTION INTEGRATION SETUP - TÄYDELLISET PROMPTIT

## 📋 VAIHE 1: INTEGRAATION LUOMINEN

### **Prompt Notion AI:lle:**

```
Luo uusi Notion-integration seuraavilla asetuksilla:

INTEGRATION SETTINGS:
- Nimi: "TennisBot ROI System" tai "Smart Value Detector"
- Työtila: [Valitse oma työtilasi]
- Tyyppi: "Internal" (sisäinen käyttö)
- Logo: [Valinnainen - voit lisätä logon myöhemmin]

INTEGRATION CAPABILITIES:
Tämä integration tarvitsee seuraavat oikeudet:
- Read content (Lue sisältö)
- Insert content (Lisää sisältö)
- Update content (Päivitä sisältö)
- Create databases (Luo tietokantoja)
- Update databases (Päivitä tietokantoja)

DESCRIPTION:
"AI-powered sports betting ROI analysis system that automatically syncs match data, 
calculates value bets, tracks ROI performance, and creates comprehensive databases 
for tennis, football, basketball, and ice hockey. Optimized for maximum ROI with 
Kelly Criterion stake optimization and statistical analysis."

Kun integration on luotu, kopioi "Internal Integration Token" ja tallenna se turvallisesti.
```

---

## 📋 VAIHE 2: INTEGRAATION LINKITTÄMINEN SIVUUN

### **Prompt Notion AI:lle:**

```
Linkitä juuri luomasi "TennisBot ROI System" -integration Notion-sivuun:

OHJEET:
1. Avaa Notion-sivu johon haluat lisätä tietokannat
2. Klikkaa oikealla yläkulmassa "..." (kolme pistettä)
3. Valitse "Connections" tai "Add connections"
4. Etsi "TennisBot ROI System" -integration
5. Klikkaa sitä lisätäksesi sen sivulle
6. Varmista että integration näkyy "Connected" -tilassa

TÄMÄN JÄLKEEN:
- Integration voi nyt luoda tietokantoja tälle sivulle
- Integration voi päivittää sisältöä tällä sivulla
- Integration voi synkronoida dataa automaattisesti

Tallenna sivun ID (URL:sta: notion.so/[workspace]/[page-id])
```

---

## 📋 VAIHE 3: AUTOMAATTINEN SETUP (Python)

### **Kun olet saanut tokenin ja linkittänyt integrationin:**

```python
from src.notion_mcp_integration import NotionMCPIntegration
import os

# 1. Aseta token
NOTION_TOKEN = "secret_abc123xyz..."  # Kopioi integrations-sivulta
PARENT_PAGE_ID = "your-page-id-here"  # Kopioi Notion-sivun URL:sta

# 2. Initialize integration
integration = NotionMCPIntegration()
integration.initialize_notion_client(NOTION_TOKEN)

# 3. Luo kaikki tietokannat
databases = integration.create_roi_database_structure(PARENT_PAGE_ID)

print(f"✅ Created {len(databases)} databases:")
for sport, db_id in databases.items():
    print(f"   • {sport}: {db_id}")

# 4. Tallenna database ID:t
import json
with open('config/notion_databases.json', 'w') as f:
    json.dump(databases, f, indent=2)

print("✅ Setup complete! Databases are ready in Notion.")
```

---

## 📋 VAIHE 4: TIETOKANTOJEN LUONTI (Manuaalinen vaihtoehto)

### **Jos haluat luoda tietokannat manuaalisesti Notion AI:lla:**

#### **Tennis Database Prompt:**

```
Luo Notion-tietokanta nimellä "🎾 Tennis Matches & ROI Analysis" seuraavilla kentillä:

Otsikko: Match (Title)
Teksti: Player 1, Player 2, Tournament
Valinta: Surface (Hard, Clay, Grass)
Valinta: Status (Scheduled, Live, Finished)
Valinta: Confidence (High, Medium, Low)
Valinta: Result (Win, Loss, Pending)
Numero: Odds Player 1, Odds Player 2
Numero: True Probability (%), Edge (%), Expected Value (%), ROI (%)
Numero: Recommended Stake (€), Profit/Loss (€)
Päivämäärä: Date

Lisää kaaviot:
- ROI % vs Päivämäärä
- Win Rate vs Confidence
- Profit/Loss vs Päivämäärä
```

#### **Football Database Prompt:**

```
Luo Notion-tietokanta nimellä "⚽ Football Matches & ROI Analysis" seuraavilla kentillä:

Otsikko: Match (Title)
Teksti: Home Team, Away Team, League, Score
Valinta: Status (Scheduled, Live, Finished)
Valinta: Confidence (High, Medium, Low)
Valinta: Result (Win, Loss, Draw, Pending)
Numero: Odds Home, Odds Draw, Odds Away
Numero: True Probability (%), Edge (%), Expected Value (%), ROI (%)
Numero: Recommended Stake (€), Profit/Loss (€)
Päivämäärä: Date

Lisää kaaviot:
- ROI % vs League
- Win Rate vs Confidence
- Profit/Loss vs Päivämäärä
```

#### **Basketball Database Prompt:**

```
Luo Notion-tietokanta nimellä "🏀 Basketball Matches & ROI Analysis" seuraavilla kentillä:

Otsikko: Match (Title)
Teksti: Home Team, Away Team, Score
Valinta: League (NBA, EuroLeague, NCAA)
Valinta: Status (Scheduled, Live, Finished)
Valinta: Confidence (High, Medium, Low)
Valinta: Result (Win, Loss, Pending)
Numero: Odds Home, Odds Away
Numero: True Probability (%), Edge (%), Expected Value (%), ROI (%)
Numero: Recommended Stake (€), Profit/Loss (€)
Päivämäärä: Date

Lisää kaaviot:
- ROI % vs League
- Win Rate vs Confidence
```

#### **Ice Hockey Database Prompt:**

```
Luo Notion-tietokanta nimellä "🏒 Ice Hockey Matches & ROI Analysis" seuraavilla kentillä:

Otsikko: Match (Title)
Teksti: Home Team, Away Team, Score
Valinta: League (NHL, KHL, SHL)
Valinta: Status (Scheduled, Live, Finished)
Valinta: Confidence (High, Medium, Low)
Valinta: Result (Win, Loss, Pending)
Numero: Odds Home, Odds Away
Numero: True Probability (%), Edge (%), Expected Value (%), ROI (%)
Numero: Recommended Stake (€), Profit/Loss (€)
Päivämäärä: Date

Lisää kaaviot:
- ROI % vs League
- Win Rate vs Confidence
```

#### **ROI Analysis Database Prompt:**

```
Luo Notion-tietokanta nimellä "💰 ROI Analysis & Performance" seuraavilla kentillä:

Otsikko: Date (Title)
Valinta: Sport (Tennis, Football, Basketball, Ice Hockey)
Valinta: Status (Excellent, Good, Needs Improvement)
Numero: Total Trades, Winning Trades, Losing Trades
Numero: Win Rate (%), Total Stake (€), Total Profit (€), Total Loss (€)
Numero: Net Profit (€), ROI (%), Average Edge (%)
Numero: Sharpe Ratio, Max Drawdown (%), Profit Factor

Lisää kaaviot:
- ROI % vs Päivämäärä (kaikki lajit)
- Net Profit vs Päivämäärä
- Win Rate % vs Laji
- Sharpe Ratio vs Päivämäärä
```

---

## 📋 VAIHE 5: DASHBOARD-LUONTI

### **Dashboard Prompt:**

```
Luo Notion-dashboard-sivu nimellä "📊 ROI Dashboard" joka näyttää:

1. YHTEENVETO-KORTTI:
   - KokonaisROI (%)
   - Netto-voitto (€)
   - Voittoprosentti (%)
   - Kaikki tradeja

2. LAJITTAIN-JAKAUTUMINEN:
   - Tennis ROI
   - Football ROI
   - Basketball ROI
   - Ice Hockey ROI

3. TRENDIT:
   - ROI % trendi (viimeiset 30 päivää)
   - Voittoprosentti trendi
   - Netto-voitto trendi

4. PARHAAT TRADEET:
   - Top 5 ROI %
   - Top 5 Voitto (€)
   - Top 5 Edge (%)

5. HUONOIMMAT TRADEET:
   - Bottom 5 Tappio (€)
   - Analyysi miksi meni pieleen

Linkitä kaikki tietokannat tähän dashboardiin käyttäen Notionin database views.
```

---

## 🔧 AUTOMAATTINEN SETUP-SKRIPTI

### **setup_notion_integration.py:**

```python
#!/usr/bin/env python3
"""
Automaattinen Notion-integration setup
"""

import os
import json
from pathlib import Path
from src.notion_mcp_integration import NotionMCPIntegration

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║  🔗 NOTION INTEGRATION SETUP                                ║
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
    
    token = input("\nLiitä token tähän: ").strip()
    
    if not token:
        print("❌ Token required!")
        return
    
    # 2. Hae parent page ID
    print("\n📋 VAIHE 2: Parent Page ID")
    print("=" * 50)
    print("1. Avaa Notion-sivu johon haluat lisätä tietokannat")
    print("2. Klikkaa '...' (kolme pistettä) oikealla yläkulmassa")
    print("3. Valitse 'Connections'")
    print("4. Lisää 'TennisBot ROI System' -integration")
    print("5. Kopioi sivun ID URL:sta (notion.so/[workspace]/[page-id])")
    
    page_id = input("\nLiitä page ID tähän: ").strip()
    
    if not page_id:
        print("❌ Page ID required!")
        return
    
    # 3. Initialize
    print("\n🔧 Initializing integration...")
    integration = NotionMCPIntegration()
    integration.initialize_notion_client(token)
    
    # 4. Create databases
    print("🏗️ Creating databases...")
    databases = integration.create_roi_database_structure(page_id)
    
    if databases:
        print(f"\n✅ Created {len(databases)} databases:")
        for sport, db_id in databases.items():
            print(f"   • {sport}: {db_id}")
        
        # Save config
        config_file = Path('config/notion_databases.json')
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump({
                'token': token,
                'parent_page_id': page_id,
                'databases': databases
            }, f, indent=2)
        
        print(f"\n💾 Config saved to {config_file}")
        print("\n✅ Setup complete!")
    else:
        print("❌ Failed to create databases")

if __name__ == "__main__":
    main()
```

---

## ✅ YHTEENVETO

### **Nopea Setup:**

1. **Luo Integration:**
   - Mene: https://www.notion.so/my-integrations
   - Klikkaa "+ New integration"
   - Nimi: "TennisBot ROI System"
   - Työtila: [Oma työtilasi]
   - Tyyppi: Internal
   - Kopioi token

2. **Linkitä Sivulle:**
   - Avaa Notion-sivu
   - Klikkaa "..." → "Connections"
   - Lisää "TennisBot ROI System"
   - Kopioi page ID

3. **Suorita Setup:**
   ```bash
   python setup_notion_integration.py
   ```

4. **Valmis!**
   - 5 tietokantaa luotu
   - Automaattinen synkronointi valmis
   - Dashboard-linkit luotu

---

## 🔒 TURVALLISUUS

⚠️ **TÄRKEÄÄ:**
- Älä jaa tokenia julkisesti
- Älä commitoi tokenia Git-repositorioon
- Käytä `.gitignore`-tiedostoa
- Tallenna token turvallisesti

---

**🔗 Integration luotu? Seuraavaksi: `python setup_notion_integration.py`**

