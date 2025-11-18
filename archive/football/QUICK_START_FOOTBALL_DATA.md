# ⚽ FOOTBALL DATA COLLECTOR - NOPEA KÄYTTÖÖNOTTO

## 🚀 5 MINUUTIN SETUP

### **1. Asenna Riippuvuudet**

```bash
pip install beautifulsoup4 aiohttp requests pandas
```

### **2. Hae API-avaimet (Valinnainen)**

```bash
# Football-Data.org (Free: 10 req/min)
# Rekisteröidy: https://www.football-data.org/
export FOOTBALL_DATA_API_KEY='your_key'

# API-Football (Free: 100 req/day)
# Rekisteröidy: https://www.api-football.com/
export API_FOOTBALL_KEY='your_key'

# Sportmonks (Free: 500 req/month)
# Rekisteröidy: https://www.sportmonks.com/
export SPORTMONKS_KEY='your_key'
```

**HUOM:** Järjestelmä toimii ilman API-avaimia käyttäen scraping-järjestelmiä!

### **3. Käynnistä Data Collection**

```bash
# Suorita skripti
python src/football_data_collector.py
```

---

## 📊 MITÄ SE TEKEE

1. ✅ Hakee ottelut **Football-Data.org API:sta** (jos saatavilla)
2. ✅ Hakee ottelut **API-Football:sta** (jos saatavilla)
3. ✅ Scrapee **BBC Sport**, **ESPN**, **WhoScored**
4. ✅ Agregoi kaikki data
5. ✅ Poistaa duplikaatit
6. ✅ Tallentaa JSON ja CSV muodossa

---

## 📁 TULOSTEET

### **JSON-tiedosto**
`data/football/football_matches_YYYYMMDD_HHMMSS.json`

### **CSV-tiedosto**
`data/football/football_matches_YYYYMMDD_HHMMSS.csv`

---

## 🐍 PYTHON-KÄYTTÖ

```python
from src.football_data_collector import FootballDataCollector
import asyncio

async def main():
    # Initialize collector
    collector = FootballDataCollector()
    
    # Get today's matches
    matches = await collector.get_today_matches()
    
    print(f"✅ Found {len(matches)} matches")
    
    # Save to files
    collector.save_matches(matches)
    collector.save_to_csv(matches)
    
    # Print sample
    for match in matches[:5]:
        print(f"  • {match.home_team} vs {match.away_team} ({match.league})")

asyncio.run(main())
```

---

## 🔄 AUTOMAATTINEN PÄIVITYS

### **Cron Job**

```bash
# Päivittäin klo 08:00
0 8 * * * cd /path/to/TennisBot && python src/football_data_collector.py
```

### **Python Scheduler**

```python
import schedule
import time
import asyncio
from src.football_data_collector import FootballDataCollector

def update_data():
    collector = FootballDataCollector()
    matches = asyncio.run(collector.get_today_matches())
    collector.save_matches(matches)

schedule.every().day.at("08:00").do(update_data)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## ✅ YHTEENVETO

✅ **Ilmainen** - Free tier APIs + scraping  
✅ **Kattava** - Useita data-lähteitä  
✅ **Automaattinen** - Cron jobs & schedulers  
✅ **Ei API-avaimia pakollisia** - Toimii scraping-järjestelmillä  

**⚽ Valmis käyttöön! 📊**

