# 📊 NOTION MCP - NOPEA KÄYTTÖÖNOTTO

## 🚀 5 MINUUTIN SETUP

### **1. Asenna Riippuvuudet**

```bash
pip install selenium notion-client beautifulsoup4
```

### **2. ChromeDriver Setup**

```bash
# macOS
brew install chromedriver

# TAI lataa manuaalisesti
# https://chromedriver.chromium.org/
```

### **3. Notion API Token (Valinnainen)**

```bash
# Rekisteröidy: https://www.notion.so/my-integrations
# Luo uusi integration ja kopioi token
export NOTION_TOKEN='your_notion_token'
```

### **4. Automaattinen Setup**

```bash
# Suorita setup-skripti
python setup_notion_mcp.py
```

---

## 🔐 KIRJAUTUMISVAIHTOEHDOT

### **Vaihtoehto 1: Browser Authentication (Automaattinen)**

```python
from src.notion_mcp_integration import NotionMCPIntegration

integration = NotionMCPIntegration()
success = integration.authenticate_via_browser(
    email="your_email@example.com",
    password="your_password"
)

if success:
    print("✅ Authenticated!")
```

### **Vaihtoehto 2: API Token**

```python
from src.notion_mcp_integration import NotionMCPIntegration

integration = NotionMCPIntegration()
integration.initialize_notion_client("your_notion_token")
```

---

## 📊 TIETOKANTOJEN LUONTI

### **Automaattinen (Python)**

```python
from src.notion_mcp_integration import NotionMCPIntegration

integration = NotionMCPIntegration()
integration.initialize_notion_client("your_token")

# Parent page ID (Notion-sivun ID)
parent_page_id = "your_page_id"

# Luo kaikki tietokannat
databases = integration.create_roi_database_structure(parent_page_id)

print(f"✅ Created {len(databases)} databases:")
# tennis, football, basketball, ice_hockey, roi_analysis
```

### **Manuaalinen (Notion AI)**

1. Avaa `NOTION_DATABASE_PROMPTS.md`
2. Kopioi haluamasi lajin prompt
3. Mene Notioniin
4. Luo uusi tietokanta
5. Liitä prompt Notion AI:hin tai luo kentät manuaalisesti

---

## 🔄 DATAN SYNKRONOINTI

### **Synkronoi Ottelu**

```python
# Match data
match_data = {
    'match_id': 'm1',
    'home_team': 'Manchester United',
    'away_team': 'Liverpool',
    'league': 'Premier League',
    'date': '2025-11-08',
    'odds': {'home': 2.50, 'draw': 3.20, 'away': 2.80},
    'edge': 0.08,
    'expected_value': 0.15,
    'roi': 0.20
}

# Sync to Notion
integration.sync_match_to_notion(match_data, sport='football')
```

### **Synkronoi ROI-Analyysi**

```python
roi_data = {
    'date': '2025-11-08',
    'sport': 'Football',
    'total_trades': 10,
    'winning_trades': 7,
    'losing_trades': 3,
    'win_rate': 0.70,
    'total_stake': 1000.0,
    'total_profit': 250.0,
    'total_loss': 150.0,
    'net_profit': 100.0,
    'roi': 0.10,
    'avg_edge': 0.08,
    'sharpe_ratio': 1.5,
    'max_drawdown': 0.05,
    'profit_factor': 1.67
}

integration.sync_roi_analysis(roi_data)
```

---

## 📋 TIETOKANTA-PROMPTIT

Kaikki promptit löytyvät `NOTION_DATABASE_PROMPTS.md`:

- 🎾 **Tennis Database** - Täydellinen tennis-tietokanta
- ⚽ **Football Database** - Jalkapallo-tietokanta
- 🏀 **Basketball Database** - Koripallo-tietokanta
- 🏒 **Ice Hockey Database** - Jääkiekko-tietokanta
- 💰 **ROI Analysis Database** - ROI-seuranta
- 📊 **Dashboard Prompt** - Yhteenveto-dashboard

---

## ✅ YHTEENVETO

✅ **Automaattinen kirjautuminen** - Browser-automaatio  
✅ **5 Tietokantaa** - Kaikki lajit + ROI  
✅ **Automaattinen synkronointi** - Python-integratio  
✅ **ROI-optimoitu** - Kaikki kentät ROI-laskentaan  
✅ **Dashboard** - Yhteenveto ja trendit  

**📊 Valmis käyttöön! 💰**

