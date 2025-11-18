# 🔗 SMART VALUE DETECTOR - API INTEGRAATIO

## ✅ **EI TARVITSE UUSIA API:ITA!**

Smart Value Detector käyttää **olemassa olevia** data-lähteitä projektissa:

---

## 📊 **KÄYTÖSSÄ OLEVAT DATA-LÄHTEET**

### **1. The Odds API** ✅
**Tiedosto:** `src/odds_api_integration.py`

**Mitä se tarjoaa:**
- Reaaliaikaiset kertoimet useista vedonvälittäjistä
- Tennis ATP/WTA ottelut
- Useita markkinoita (h2h, spreads, totals)

**Käyttö:**
```python
from src.odds_api_integration import OddsAPIIntegration

odds_api = OddsAPIIntegration()
odds_data = await odds_api.get_live_odds(
    sports=['tennis_atp', 'tennis_wta'],
    markets=['h2h']
)
```

**API Key:**
- Aseta environment variable: `ODDS_API_KEY`
- TAI käytä oletusarvoa koodissa (free tier)

---

### **2. Live Betting Scraper** ✅
**Tiedosto:** `src/scrapers/live_betting_scraper.py`

**Mitä se tarjoaa:**
- Live-ottelutiedot
- Tulevat ottelut
- Kertoimet scrapingista

**Käyttö:**
```python
from src.scrapers.live_betting_scraper import LiveBettingScraper

scraper = LiveBettingScraper()
live_matches = await scraper.scrape_live_matches()
upcoming = await scraper.scrape_upcoming_matches()
```

---

### **3. Multi-Sport Prematch Scraper** ✅
**Tiedosto:** `src/multi_sport_prematch_scraper.py`

**Mitä se tarjoaa:**
- Prematch-ottelutiedot
- Tilastot
- Useita urheilulajeja

**Käyttö:**
```python
from src.multi_sport_prematch_scraper import MultiSportPrematchScraper

scraper = MultiSportPrematchScraper()
matches = await scraper.scrape_tennis_matches()
```

---

### **4. Betfury Integration** ✅
**Tiedosto:** `src/betfury_integration.py`

**Mitä se tarjoaa:**
- Betfury.io linkit
- Kertoimet Betfury:sta

**Käyttö:**
```python
from src.betfury_integration import BetfuryIntegration

betfury = BetfuryIntegration()
links = await betfury.find_match_links(match_name)
```

---

## 🔗 **INTEGRAATIO SVD:ÄÄN**

**Tiedosto:** `src/svd_data_integration.py`

Tämä moduuli yhdistää kaikki data-lähteet SVD:ään:

```python
from src.svd_data_integration import SVDDataIntegration

integration = SVDDataIntegration()

# Hae kaikki tennis-ottelut kaikista lähteistä
matches = await integration.get_tennis_matches()

# Käytä SVD:ää
from src.smart_value_detector import SmartValueDetector

svd = SmartValueDetector(bankroll=1000.0)
trades = svd.find_value_trades(matches)
```

---

## ⚙️ **KONFIGURAATIO**

### **Environment Variables**

```bash
# The Odds API (valinnainen)
export ODDS_API_KEY='your_odds_api_key'

# Telegram Bot (valinnainen)
export TELEGRAM_BOT_TOKEN='your_bot_token'
export TELEGRAM_CHAT_ID='your_chat_id'
```

### **Ei Pakollisia API:ita**

SVD toimii **ilman** API-avaimia käyttäen scraping-järjestelmiä!

---

## 🚀 **KÄYTTÖÖNOTTO ILMAN API:ITA**

### **Vaihtoehto 1: Vain Scraping**

```python
from src.svd_data_integration import SVDDataIntegration
from src.smart_value_detector import SmartValueDetector

# Käytä vain scraping-järjestelmiä
integration = SVDDataIntegration()
integration.odds_api = None  # Ei käytä Odds API:a

matches = await integration.get_tennis_matches()
svd = SmartValueDetector(bankroll=1000.0)
trades = svd.find_value_trades(matches)
```

### **Vaihtoehto 2: Kaikki Lähteet**

```python
# Käytä kaikkia saatavilla olevia lähteitä
integration = SVDDataIntegration()
matches = await integration.get_tennis_matches()
```

---

## 📋 **TIETOLÄHTEIDEN VERTAILU**

| Lähte | Tyyppi | Kustannus | Laatu | Nopeus |
|-------|--------|-----------|-------|--------|
| **The Odds API** | API | Free tier | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Live Scraper** | Scraping | Ilmainen | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Multi-Sport Scraper** | Scraping | Ilmainen | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Betfury** | Scraping | Ilmainen | ⭐⭐⭐ | ⭐⭐⭐ |

---

## ✅ **YHTEENVETO**

**EI TARVITSE UUSIA API:ITA!**

✅ Käytä olemassa olevia data-lähteitä  
✅ Scraping-järjestelmät toimivat ilman API-avaimia  
✅ The Odds API on valinnainen (free tier saatavilla)  
✅ Kaikki integroituu automaattisesti SVD:ään  

**Järjestelmä toimii heti ilman lisäasetuksia!** 🎉

---

## 🔧 **TROUBLESHOOTING**

### **Problem: "No matches found"**

**Ratkaisu:**
```python
# Tarkista että scrapers ovat käytettävissä
from src.scrapers.live_betting_scraper import LiveBettingScraper
scraper = LiveBettingScraper()
matches = await scraper.scrape_live_matches()
print(f"Found {len(matches)} matches")
```

### **Problem: "Odds API error"**

**Ratkaisu:**
- Odds API on valinnainen
- Järjestelmä toimii ilman sitä käyttäen scraping-järjestelmiä
- Aseta `integration.odds_api = None` jos haluat poistaa sen

### **Problem: "No data sources available"**

**Ratkaisu:**
- Varmista että scrapers ovat asennettuna
- Tarkista että `src/scrapers/` hakemisto on olemassa
- Käytä `SVDDataIntegration` joka yhdistää kaikki lähteet automaattisesti

---

**🎾 Järjestelmä on valmis käyttöön ilman uusia API:ita! 💰**

