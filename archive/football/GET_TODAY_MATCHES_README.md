# 📅 HAE PÄIVÄN OTTELUT - 24H SISÄLLÄ

## 🚀 NOPEA KÄYTTÖ

```bash
# Suorita skripti
python get_today_matches.py
```

## 📊 MITÄ SE TEKEE

Hakee **päivän ottelut 24h sisällä** seuraavista **5 lajista**:

1. 🎾 **Tennis** (ATP/WTA)
2. ⚽ **Jalkapallo** (Football - Premier League, La Liga, jne.)
3. 🏀 **Koripallo** (Basketball - NBA)
4. 🏒 **Jääkiekko** (Ice Hockey - NHL)
5. 🌍 **Jalkapallo** (Soccer - eri liigat: Champions League, Europa League, jne.)

## 📋 TULOSTEET

Skripti luo:

1. **Konsoli-yhteenveto** - Näyttää ottelut lajeittain
2. **JSON-tiedosto** - `data/today_matches/today_matches_YYYYMMDD_HHMMSS.json`
3. **CSV-tiedosto** - `data/today_matches/today_matches_YYYYMMDD_HHMMSS.csv`

## 📊 ESIMERKKI TULOSTE

```
╔══════════════════════════════════════════════════════════════╗
║  📅 PÄIVÄN OTTELUT - 24H SISÄLLÄ                            ║
╠══════════════════════════════════════════════════════════════╣

📊 YHTEENVETO:
   Kaikki ottelut: 45
   Lajeja: 5

📋 OTTELUT LAJITTAIN:

   Tennis: 12 ottelua
      • Djokovic vs Sinner - 14:30 (ATP Masters)
      • Swiatek vs Sabalenka - 16:00 (WTA Premier)
      ...

   Jalkapallo: 15 ottelua
      • Manchester United vs Liverpool - 18:00 (Premier League)
      • Real Madrid vs Barcelona - 20:00 (La Liga)
      ...

   Koripallo: 8 ottelua
      • Lakers vs Warriors - 01:00 (NBA)
      ...

   Jääkiekko: 6 ottelua
      • Bruins vs Maple Leafs - 00:30 (NHL)
      ...

   Jalkapallo (Soccer): 4 ottelua
      • Bayern vs PSG - 21:00 (Champions League)
      ...
```

## 🔧 KONFIGUROINTI

### **Käyttää automaattisesti:**

✅ **The Odds API** (jos saatavilla)  
✅ **Live Betting Scraper** (scraping)  
✅ **Multi-Sport Scraper** (scraping)  

**EI TARVITSE API-AVAIMIA** - toimii scraping-järjestelmillä!

### **Valinnainen: The Odds API**

Jos haluat käyttää The Odds API:a:

```bash
export ODDS_API_KEY='your_api_key'
```

**HUOM:** Järjestelmä toimii ilman API-avainta käyttäen scraping-järjestelmiä!

## 📁 TIEDOSTOT

### **JSON-muoto:**

```json
{
  "fetched_at": "2025-11-08T12:00:00",
  "total_matches": 45,
  "matches": [
    {
      "match_id": "tennis_12345",
      "sport": "tennis",
      "league": "ATP Masters",
      "home_team": "Djokovic",
      "away_team": "Sinner",
      "start_time": "2025-11-08T14:30:00",
      "status": "scheduled",
      "odds": {
        "home": 2.50,
        "away": 1.55
      },
      "source": "odds_api"
    }
  ]
}
```

### **CSV-muoto:**

| Sport | League | Home Team | Away Team | Start Time | Status | Home Odds | Away Odds | Source |
|-------|--------|-----------|-----------|------------|--------|-----------|-----------|--------|
| Tennis | ATP Masters | Djokovic | Sinner | 2025-11-08T14:30:00 | scheduled | 2.50 | 1.55 | odds_api |

## 🔄 AUTOMAATTINEN AJASTUS

Voit ajaa skriptin automaattisesti cron:lla:

```bash
# Päivittäin klo 08:00
0 8 * * * cd /path/to/TennisBot && python get_today_matches.py
```

## 🐍 PYTHON-KÄYTTÖ

Voit myös käyttää skriptiä Python-koodissa:

```python
from get_today_matches import TodayMatchesFetcher
import asyncio

async def main():
    fetcher = TodayMatchesFetcher()
    matches = await fetcher.fetch_all_matches()
    
    print(f"Found {len(matches)} matches")
    
    # Tallenna tiedostot
    fetcher.save_to_json()
    fetcher.save_to_csv()
    
    # Tulosta yhteenveto
    fetcher.print_summary()

asyncio.run(main())
```

## ✅ TROUBLESHOOTING

### **Problem: "No matches found"**

**Ratkaisu:**
- Tarkista että scrapers ovat asennettuna
- Varmista että internet-yhteys toimii
- Odds API on valinnainen - järjestelmä toimii ilman sitä

### **Problem: "Import errors"**

**Ratkaisu:**
```bash
pip install pandas aiohttp requests beautifulsoup4
```

### **Problem: "Rate limit exceeded"**

**Ratkaisu:**
- Odota hetki ja yritä uudelleen
- Järjestelmä käyttää automaattisesti rate limitingia

## 🎯 YHTEENVETO

✅ **Yksinkertainen käyttö** - `python get_today_matches.py`  
✅ **5 lajia** - Tennis, Jalkapallo, Koripallo, Jääkiekko, Soccer  
✅ **24h aikajänne** - Kaikki tulevat ottelut  
✅ **Automaattinen tallennus** - JSON ja CSV  
✅ **Ei API-avaimia tarvita** - Toimii scraping-järjestelmillä  

**🎾 Valmis käyttöön! 💰**

