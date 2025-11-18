# 📊 Unified Data Fetching & Highest ROI Framework

Yhdistetty datan hakurakenne joka hakee automaattisesti kaiken tarvittavan datan ja tilastot useista API-lähteistä kaikille lajeille ja rakentaa korkeimman ROI:n analyysirakenteen.

## 🎯 Ominaisuudet

- **🔄 Automaattinen datan hakeminen** - Hakee pelit useista lähteistä (Odds API, API Football, Web Scraping, Notion)
- **📊 Tilastojen keräys** - Kerää 120+ eri tilastoa lajikohtaisesti
- **💰 ROI-analyysi** - Laskee korkeimman ROI:n käyttäen Smart Value Detector -menetelmää
- **💾 Notion-integraatio** - Hakee ja tallentaa pelit Notion-tietokantaan
- **📱 Telegram-ilmoitukset** - Lähettää ilmoitukset kannattavista ROI-mahdollisuuksista

## 📁 Komponentit

### 1. Unified Data Fetcher (`src/unified_data_fetcher.py`)
Yhdistetty datan hakurakenne joka hakee dataa useista lähteistä:
- Odds API (kertoimet)
- API Football (jalkapallo-tilastot)
- Multi-Sport Scraper (web scraping)
- Notion API (tallennetut pelit)

### 2. Notion Data Manager (`src/notion_data_manager.py`)
Laajennettu Notion-integraatio:
- Pelien hakeminen Notion-tietokannasta
- Pelien tallentaminen Notion-tietokantaan
- Automaattinen synkronointi

### 3. Highest ROI Analyzer (`src/highest_roi_analyzer.py`)
Korkeimman ROI:n analyysirakenne:
- Smart Value Detector (ELO, H2H, muoto)
- Edge-laskenta (todellinen vs markkinat)
- Kelly Criterion -panoksen optimointi
- Expected Value -laskenta
- Riskinhallinta

### 4. Multi-Sport Statistics Collector (`src/multi_sport_stats_collector.py`)
Lajikohtainen tilastojen keräys:
- Tennis (serve %, break points, ranking)
- Football (goals, possession, shots)
- Basketball (points, rebounds, assists)
- Ice Hockey (goals, saves, power play %)

### 5. Data Pipeline Orchestrator (`src/data_pipeline_orchestrator.py`)
Automaattinen datan hakeminen ja prosessointi:
- Automaattinen datan hakeminen
- Tilastojen keräys
- ROI-analyysi
- Notion-synkronointi
- Telegram-ilmoitukset

## 🚀 Käyttöönotto

### 1. Asenna riippuvuudet

```bash
pip install -r requirements.txt
```

### 2. Konfiguroi API-avaimet

Luo `.env`-tiedosto tai aseta ympäristömuuttujat:

```bash
export ODDS_API_KEY="your_odds_api_key"
export API_FOOTBALL_KEY="your_api_football_key"
export NOTION_TOKEN="your_notion_token"
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
export TELEGRAM_CHAT_ID="your_telegram_chat_id"
```

### 3. Konfiguroi järjestelmä

Muokkaa `config/unified_data_config.yaml`:

```yaml
# Ota käyttöön haluamasi lajit
sports:
  tennis:
    enabled: true
  football:
    enabled: true
  basketball:
    enabled: true
  ice_hockey:
    enabled: true

# ROI-kynnysarvot
roi_analysis:
  min_roi_threshold: 15.0  # Minimum 15% ROI
  min_confidence: 0.65     # Minimum 65% confidence
  min_edge: 5.0            # Minimum 5% edge
```

### 4. Käynnistä järjestelmä

```bash
python start_unified_data_pipeline.py
```

## 📊 Konfiguraatio

### ROI-Analyysi

```yaml
roi_analysis:
  min_roi_threshold: 15.0    # Minimum ROI %
  min_confidence: 0.65       # Minimum confidence (0-1)
  min_edge: 5.0              # Minimum edge %
  max_stake_pct: 10.0        # Maximum stake % of bankroll
  kelly_fraction: 0.25        # Conservative Kelly (25%)
  bankroll:
    initial: 10000.0          # Initial bankroll
    daily_max_risk: 3.0       # Max risk % per day
    monthly_target: 15.0       # Monthly ROI target %
```

### Pipeline

```yaml
pipeline:
  fetch_interval: 300         # Fetch data every 5 minutes
  analysis_interval: 600      # Analyze every 10 minutes
  sync_interval: 900          # Sync to Notion every 15 minutes
  max_matches_per_cycle: 100
  enable_telegram_notifications: true
```

## 🔄 Prosessi

1. **Datan hakeminen** - Hakee pelit useista lähteistä
2. **Tilastojen keräys** - Kerää tilastot jokaiselle pelille
3. **ROI-analyysi** - Laskee todellisen todennäköisyyden ja vertaa markkinakertoimiin
4. **Edge-laskenta** - Laskee edge-percentin
5. **Panoksen optimointi** - Käyttää Kelly Criterion -menetelmää
6. **Riskinarviointi** - Arvioi riskitason
7. **Notion-synkronointi** - Tallentaa kannattavat vedot Notioniin
8. **Telegram-ilmoitukset** - Lähettää ilmoitukset korkeista ROI-mahdollisuuksista

## 📈 ROI-Laskenta

### Todellinen todennäköisyys

Lasketaan käyttäen:
- ELO-rating
- Head-to-head historia
- Viimeisimmät tulokset (muoto)
- Kenttäspesifiset tilastot (tennis)

### Edge-laskenta

```
Edge = (Todellinen todennäköisyys - Implied todennäköisyys) / Implied todennäköisyys * 100
```

### Kelly Criterion

```
Kelly Stake = (Edge * Todellinen todennäköisyys) / (Markkinakertoimet - 1)
Conservative Stake = Kelly Stake * Kelly Fraction (25%)
```

### Expected Value

```
EV = (Todellinen todennäköisyys * (Markkinakertoimet - 1)) - (1 - Todellinen todennäköisyys)
```

## 🎯 Kynnysarvot

Järjestelmä suosittelee vetoa vain jos:
- ROI ≥ 15%
- Confidence ≥ 65%
- Edge ≥ 5%
- Riskitaso ≤ HIGH

## 📊 Tilastot

Järjestelmä seuraa:
- Haettujen ottelujen määrä
- Analysoitujen ottelujen määrä
- Löydettyjä ROI-mahdollisuuksia
- Notioniin synkronoituja otteluja
- Virheitä

## 🔧 Vianetsintä

### Notion-integraatio ei toimi

1. Tarkista että `NOTION_TOKEN` on asetettu
2. Varmista että Notion-integration on liitetty sivulle
3. Tarkista että tietokanta-ID:t ovat oikein `config/unified_data_config.yaml`

### Datan hakeminen ei toimi

1. Tarkista API-avaimet
2. Tarkista että API-lähteet ovat käytössä konfiguraatiossa
3. Tarkista rate limitit

### ROI-analyysi ei löydä mahdollisuuksia

1. Laske kynnysarvot konfiguraatiossa
2. Tarkista että dataa on saatavilla
3. Tarkista että tilastot kerätään oikein

## 📚 Lisätietoja

- [HIGHEST_ROI_PLAN.md](HIGHEST_ROI_PLAN.md) - Korkeimman ROI:n saavuttamisen suunnitelma
- [FOOTBALL_STATS_SUMMARY.md](FOOTBALL_STATS_SUMMARY.md) - Jalkapallo-tilastojen yhteenveto
- [QUICK_START_NOTION_MCP.md](QUICK_START_NOTION_MCP.md) - Notion-integraation nopea aloitus

## ✅ Yhteenveto

Tämä järjestelmä tarjoaa:
- ✅ Automaattisen datan hakemisen useista lähteistä
- ✅ Korkeimman ROI:n analyysirakenteen
- ✅ Notion-integraation pelien hakemiseen ja tallentamiseen
- ✅ Lajikohtaisen tilastojen keräyksen
- ✅ Automaattisen prosessoinnin ja synkronoinnin

**🎉 Valmis käyttöön! 💰**

